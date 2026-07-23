#!/usr/bin/env python3
import http.server
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import sys
import tempfile
import threading
from typing import Optional
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
CRAFT_API_HELPER = (
    REPO_ROOT / ".agents/skills/productivity/craft-api/scripts/craft_api.py"
)
TEST_CREDENTIAL = "unit-test-credential"


class RecordingHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.server.requests.append(
            {
                "path": self.path,
                "authorization": self.headers.get("Authorization"),
                "x_craft_api_key": self.headers.get("x-craft-api-key"),
            }
        )
        if self.path == "/api/v1/start" and self.server.redirect_to:
            self.send_response(302)
            self.send_header("Location", self.server.redirect_to)
            self.end_headers()
            return

        payload = b'{"ok":true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, _format: str, *_args: object) -> None:
        pass


class CraftApiTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        openssl = shutil.which("openssl")
        if openssl is None:
            raise RuntimeError("openssl is required for Craft API transport tests")

        cls.temp_dir = tempfile.TemporaryDirectory()
        temp_path = Path(cls.temp_dir.name)
        cls.cert_path = temp_path / "cert.pem"
        cls.key_path = temp_path / "key.pem"
        openssl_config = temp_path / "openssl.cnf"
        openssl_config.write_text(
            """
[req]
distinguished_name = subject
x509_extensions = extensions
prompt = no

[subject]
CN = localhost

[extensions]
subjectAltName = DNS:localhost
basicConstraints = critical,CA:TRUE
keyUsage = critical,digitalSignature,keyEncipherment,keyCertSign
extendedKeyUsage = serverAuth
""".strip()
            + "\n",
            encoding="utf-8",
        )
        subprocess.run(
            [
                openssl,
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-days",
                "1",
                "-config",
                str(openssl_config),
                "-keyout",
                str(cls.key_path),
                "-out",
                str(cls.cert_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()

    def start_server(
        self, *, use_tls: bool, redirect_to: Optional[str] = None
    ) -> http.server.ThreadingHTTPServer:
        server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), RecordingHandler
        )
        server.requests = []
        server.redirect_to = redirect_to
        if use_tls:
            tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            tls_context.load_cert_chain(self.cert_path, self.key_path)
            server.socket = tls_context.wrap_socket(server.socket, server_side=True)

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        return server

    def run_helper(
        self, base_url: str, *, auth: str = "bearer"
    ) -> subprocess.CompletedProcess[str]:
        environment = {
            "CRAFT_API_BASE_URL": base_url,
            "CRAFT_API_KEY": TEST_CREDENTIAL,
            "PATH": os.environ.get("PATH", ""),
            "SSL_CERT_FILE": str(self.cert_path),
        }
        return subprocess.run(
            [
                sys.executable,
                str(CRAFT_API_HELPER),
                "GET",
                "/start",
                "--auth",
                auth,
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )

    def test_rejects_cleartext_base_url_before_sending_credentials(self) -> None:
        server = self.start_server(use_tls=False)

        result = self.run_helper(
            f"http://localhost:{server.server_port}/api/v1"
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("must use HTTPS", result.stderr)
        self.assertEqual(server.requests, [])
        self.assertNotIn(TEST_CREDENTIAL, result.stdout)
        self.assertNotIn(TEST_CREDENTIAL, result.stderr)

    def test_rejects_base_url_userinfo_before_sending_credentials(self) -> None:
        server = self.start_server(use_tls=True)

        result = self.run_helper(
            f"https://user:password@localhost:{server.server_port}/api/v1"
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("must not include userinfo", result.stderr)
        self.assertEqual(server.requests, [])
        self.assertNotIn(TEST_CREDENTIAL, result.stdout)
        self.assertNotIn(TEST_CREDENTIAL, result.stderr)

    def test_blocks_cross_origin_redirect_before_forwarding_credentials(self) -> None:
        auth_modes = {
            "bearer": ("authorization", f"Bearer {TEST_CREDENTIAL}"),
            "x-craft-api-key": ("x_craft_api_key", TEST_CREDENTIAL),
        }
        for auth_mode, (header_name, expected_value) in auth_modes.items():
            with self.subTest(auth_mode=auth_mode):
                redirected_server = self.start_server(use_tls=True)
                redirect_target = (
                    f"https://localhost:{redirected_server.server_port}/api/v1/final"
                )
                initial_server = self.start_server(
                    use_tls=True, redirect_to=redirect_target
                )

                result = self.run_helper(
                    f"https://localhost:{initial_server.server_port}/api/v1",
                    auth=auth_mode,
                )

                self.assertEqual(len(initial_server.requests), 1)
                self.assertEqual(
                    initial_server.requests[0][header_name], expected_value
                )
                self.assertEqual(redirected_server.requests, [])
                self.assertEqual(result.returncode, 1)
                self.assertIn("blocked unsafe redirect", result.stderr)
                self.assertNotIn(TEST_CREDENTIAL, result.stdout)
                self.assertNotIn(TEST_CREDENTIAL, result.stderr)

    def test_blocks_https_to_http_redirect_before_forwarding_credentials(self) -> None:
        redirected_server = self.start_server(use_tls=False)
        initial_server = self.start_server(
            use_tls=True,
            redirect_to=(
                f"http://localhost:{redirected_server.server_port}/api/v1/final"
            ),
        )

        result = self.run_helper(
            f"https://localhost:{initial_server.server_port}/api/v1"
        )

        self.assertEqual(len(initial_server.requests), 1)
        self.assertEqual(redirected_server.requests, [])
        self.assertEqual(result.returncode, 1)
        self.assertIn("blocked unsafe redirect", result.stderr)
        self.assertNotIn(TEST_CREDENTIAL, result.stdout)
        self.assertNotIn(TEST_CREDENTIAL, result.stderr)

    def test_blocks_redirect_userinfo_before_forwarding_credentials(self) -> None:
        server = self.start_server(use_tls=True)
        server.redirect_to = (
            f"https://user:password@localhost:{server.server_port}/api/v1/final"
        )

        result = self.run_helper(
            f"https://localhost:{server.server_port}/api/v1"
        )

        self.assertEqual(len(server.requests), 1)
        self.assertEqual(result.returncode, 1)
        self.assertIn("blocked unsafe redirect", result.stderr)
        self.assertNotIn(TEST_CREDENTIAL, result.stdout)
        self.assertNotIn(TEST_CREDENTIAL, result.stderr)

    def test_allows_same_origin_https_redirect_with_credentials(self) -> None:
        auth_modes = {
            "bearer": ("authorization", f"Bearer {TEST_CREDENTIAL}"),
            "x-craft-api-key": ("x_craft_api_key", TEST_CREDENTIAL),
        }
        for auth_mode, (header_name, expected_value) in auth_modes.items():
            with self.subTest(auth_mode=auth_mode):
                server = self.start_server(use_tls=True)
                server.redirect_to = (
                    f"https://localhost:{server.server_port}/api/v1/final"
                )

                result = self.run_helper(
                    f"https://localhost:{server.server_port}/api/v1",
                    auth=auth_mode,
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, '{"ok":true}')
                self.assertEqual(len(server.requests), 2)
                self.assertEqual(
                    server.requests[0][header_name], expected_value
                )
                self.assertEqual(
                    server.requests[1][header_name], expected_value
                )


if __name__ == "__main__":
    unittest.main()
