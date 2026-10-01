import importlib.util
import io
import json
import os
import unittest
import urllib.error
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("parcel", Path(__file__).parents[1] / "scripts/parcel_api.py")
parcel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parcel)

class Response:
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return self.payload

class ParcelTests(unittest.TestCase):
    def test_private_inputs_never_enter_provider_errors(self):
        private = "private@example.test"
        cases = [urllib.error.HTTPError(parcel.API_BASE, 400, private, {}, io.BytesIO(private.encode())), Response(json.dumps({"success": False, "error_message": private}).encode()), Response(private.encode())]
        for response in cases:
            with self.subTest(response=type(response).__name__):
                if isinstance(response, urllib.error.HTTPError): self.addCleanup(response.close)
                kwargs = {"side_effect": response} if isinstance(response, Exception) else {"return_value": response}
                with patch.dict(os.environ, {"PARCEL_API_KEY": "test"}), patch.object(parcel.urllib.request, "urlopen", **kwargs), self.assertRaises(SystemExit) as error:
                    parcel.request_json("POST", "/add-delivery/", data={"email": private})
                self.assertNotIn(private, str(error.exception))

    def test_mixed_carrier_catalog(self):
        out = io.StringIO()
        with patch.object(parcel, "load_carriers", return_value={"ups": {"name": "UPS"}, "legacy": "Legacy", "invalid": {"name": None}}), redirect_stdout(out):
            parcel.command_carriers(parcel.build_parser().parse_args(["carriers", "--json"]))
        self.assertEqual(json.loads(out.getvalue()), {"ups": "UPS", "legacy": "Legacy"})

    def test_private_preview_and_confirmed_payload(self):
        args = parcel.build_parser().parse_args(["add", "--tracking", "synthetic", "--carrier", "pholder", "--description", "test", "--carrier-inputs-file", "-", "--no-duplicate-check"])
        out = io.StringIO()
        with patch.object(parcel, "request_json") as req, patch.object(parcel.sys, "stdin", io.StringIO(json.dumps({"email": "private@example.test", "postcode": "PRIVATE"}))), redirect_stdout(out):
            parcel.command_add(args)
            req.assert_not_called()
        self.assertNotIn("private@example.test", out.getvalue())
        self.assertNotIn("PRIVATE", out.getvalue())
        args.confirm = True
        out = io.StringIO()
        with patch.object(parcel, "request_json", return_value={"success": True, "echo": "private@example.test"}) as req, patch.object(parcel.sys, "stdin", io.StringIO(json.dumps({"email": "private@example.test", "postcode": "PRIVATE"}))), redirect_stdout(out):
            parcel.command_add(args)
        self.assertEqual(req.call_args.kwargs["data"]["email"], "private@example.test")
        self.assertEqual(req.call_args.kwargs["data"]["postcode"], "PRIVATE")
        self.assertNotIn("private@example.test", out.getvalue())

    def test_private_input_file_and_validation(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "inputs.json"
            source.write_text(json.dumps({"email": "private@example.test"}))
            self.assertEqual(parcel.load_carrier_inputs(str(source)), {"email": "private@example.test"})
            for value in [{"email": 1}, {"unknown": "private@example.test"}, ["private@example.test"]]:
                source.write_text(json.dumps(value))
                with self.assertRaises(SystemExit) as error:
                    parcel.load_carrier_inputs(str(source))
                self.assertNotIn("private@example.test", str(error.exception))
            source.write_text("private@example.test")
            with self.assertRaises(SystemExit) as error:
                parcel.load_carrier_inputs(str(source))
            self.assertNotIn("private@example.test", str(error.exception))
