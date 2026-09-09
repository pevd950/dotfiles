#!/usr/bin/env python3
"""Validate tracked skill YAML and relative Markdown links; never scan private files.

Requires PyYAML (CI installs python3-yaml). This checks structure, not semantics
or runtime activation. Code examples, external URLs and fragments are excluded.
"""
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

import yaml


class UniqueKeysLoader(yaml.SafeLoader):
    """Reject duplicate mapping keys instead of silently retaining the last one."""


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in result:
            raise ValueError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node)
    return result


UniqueKeysLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping
)


def metadata(text):
    lines = text.splitlines()
    if not lines or lines[0] != '---':
        raise ValueError('missing frontmatter')
    try:
        end = lines.index('---', 1)
    except ValueError as exc:
        raise ValueError('unterminated frontmatter') from exc
    data = yaml.load('\n'.join(lines[1:end]) + '\n', Loader=UniqueKeysLoader)
    if not isinstance(data, dict):
        raise ValueError('frontmatter must be a mapping')
    for key in ('name', 'description'):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f'{key} must be a nonempty string')
    return data


def local_links(text):
    # Ignore fenced and inline code: examples are not document dependencies.
    prose = []
    fence = None
    for line in text.splitlines():
        match = re.match(r'^\s*(`{3,}|~{3,})', line)
        if match:
            marker = match[1]
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            continue
        if fence is None:
            prose.append(re.sub(r'`+[^`]*`+', '', line))
    text = '\n'.join(prose)
    targets = re.findall(r'\]\((<[^>]+>|[^\s)]+)(?:\s+"[^"]*")?\)', text)
    targets += re.findall(r'^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)', text, re.M)
    for target in targets:
        target = target.strip('<>')
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        yield unquote(parsed.path)


def validate(root, paths, tracked_paths=None):
    errors = []
    names = {}
    tracked = {p.resolve() for p in (paths if tracked_paths is None else tracked_paths)}
    for path in paths:
        if path.name == 'SKILL.md':
            try:
                data = metadata(path.read_text())
                name = data['name']
                if name in names:
                    errors.append(f'{path.relative_to(root)}: duplicate skill name {name} ({names[name]})')
                names[name] = path.relative_to(root)
            except (ValueError, TypeError, yaml.YAMLError) as exc:
                errors.append(f'{path.relative_to(root)}: {exc}')
        if path.name == 'openai.yaml' and path.parent.name == 'agents':
            try:
                data = yaml.load(path.read_text(), Loader=UniqueKeysLoader)
                if not isinstance(data, dict):
                    raise ValueError('skill UI metadata must be a mapping')
                policy = data.get('policy', {})
                if not isinstance(policy, dict):
                    raise ValueError('policy must be a mapping')
                if 'allow_implicit_invocation' in policy and not isinstance(policy['allow_implicit_invocation'], bool):
                    raise ValueError('allow_implicit_invocation must be boolean')
            except (ValueError, TypeError, yaml.YAMLError) as exc:
                errors.append(f'{path.relative_to(root)}: {exc}')
        if path.suffix != '.md':
            continue
        for target in local_links(path.read_text()):
            resolved = (path.parent / target).resolve()
            # Directory references are valid when they contain tracked files.
            if resolved not in tracked and not any(resolved in p.parents for p in tracked):
                errors.append(f'{path.relative_to(root)}: untracked or missing link target {target}')
    return errors


def main():
    root = Path(__file__).resolve().parents[1]
    tracked = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z']).decode().split('\0')
    paths = [root / p for p in tracked if p and (
        p.startswith('.agents/skills/') or p in ('AGENTS.md', '.codex/AGENTS.md', 'superassistant/AGENTS.md')
    )]
    errors = validate(root, paths, [root / p for p in tracked if p])
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'Instruction checks passed ({sum(p.name == "SKILL.md" for p in paths)} tracked skills).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
