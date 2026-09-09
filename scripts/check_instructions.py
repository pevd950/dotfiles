#!/usr/bin/env python3
"""Validate tracked skill YAML and relative Markdown links; never scan private files.

Run scripts/setup-checks.sh to install the declared validation dependencies. This checks structure, not semantics
or runtime activation. Code examples, external URLs and fragments are excluded.
"""
from pathlib import Path
import os
import subprocess
import sys
from urllib.parse import unquote, urlsplit

import yaml
from markdown_it import MarkdownIt


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
    """Extract CommonMark destinations, excluding code, external URLs and fragments."""
    env = {}
    tokens = MarkdownIt('commonmark').parse(text, env)
    targets = [ref['href'] for ref in env.get('references', {}).values()]
    pending = list(tokens)
    while pending:
        token = pending.pop(0)
        if token.type in ('link_open', 'image'):
            targets.append(token.attrGet('href' if token.type == 'link_open' else 'src'))
        pending[0:0] = token.children or []
    for target in dict.fromkeys(targets):
        parsed = urlsplit(target)
        if not parsed.scheme and not parsed.netloc and parsed.path:
            yield unquote(parsed.path)


def validate(root, paths, tracked_paths=None):
    errors = []
    names = {}
    tracked = {p.resolve() for p in (paths if tracked_paths is None else tracked_paths)}
    for path in paths:
        try:
            path.resolve(strict=True).relative_to(root.resolve())
            text = path.read_text() if path.suffix in ('.md', '.yaml') else ''
        except (ValueError, OSError, RuntimeError) as exc:
            errors.append(f'{path.relative_to(root)}: unavailable or outside checkout ({type(exc).__name__})')
            continue
        if path.name == 'SKILL.md':
            try:
                data = metadata(text)
                name = data['name']
                if name in names:
                    errors.append(f'{path.relative_to(root)}: duplicate skill name {name} ({names[name]})')
                names.setdefault(name, path.relative_to(root))
            except (ValueError, TypeError, yaml.YAMLError) as exc:
                errors.append(f'{path.relative_to(root)}: {exc}')
        if path.name == 'openai.yaml' and path.parent.name == 'agents':
            try:
                data = yaml.load(text, Loader=UniqueKeysLoader)
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
        for target in local_links(text):
            resolved = (path.parent / target).resolve()
            # Directory references are valid when they contain tracked files.
            if not resolved.is_relative_to(root.resolve()) or not resolved.exists() or (resolved not in tracked and not any(resolved in p.parents for p in tracked)):
                errors.append(f'{path.relative_to(root)}: untracked or missing link target {target}')
    return errors


def tracked_files(root):
    """Read the exact clone or yadm index without invoking yadm auto-alt writes."""
    if (root / '.git').exists():
        command = ['git', '-C', str(root)]
    else:
        env = os.environ.copy()
        count = int(env.get('GIT_CONFIG_COUNT', '0'))
        env.update({'GIT_CONFIG_COUNT': str(count + 1),
                    f'GIT_CONFIG_KEY_{count}': 'yadm.auto-alt',
                    f'GIT_CONFIG_VALUE_{count}': 'false'})
        repo = subprocess.check_output(['yadm', 'introspect', 'repo'], env=env, text=True).strip()
        command = ['git', '--git-dir=' + repo]
        worktree = subprocess.check_output(command + ['config', 'core.worktree'], text=True).strip()
        if Path(worktree).resolve() != root.resolve():
            raise ValueError('yadm worktree does not match instruction root')
    return subprocess.check_output(command + ['ls-files', '-z']).decode().split('\0')


def main():
    root = Path(__file__).resolve().parents[1]
    tracked = tracked_files(root)
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
