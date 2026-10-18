#!/usr/bin/env python3
"""Selective install with dry-run by default and no overwrites of existing skills."""
from __future__ import annotations
from pathlib import Path
import argparse
import json
import os
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def skill_sources(manifest: dict) -> dict[str, Path]:
    sources: dict[str, Path] = {}
    for name in manifest['core_skills'] + manifest.get('extension_skills', []):
        if name in sources:
            raise ValueError(f'Duplicate core skill: {name}')
        sources[name] = ROOT / '.agents' / 'skills' / name
    for pack, cfg in manifest.get('extension_packs', {}).items():
        root = ROOT / cfg['skill_root']
        for name in cfg['skills']:
            if name in sources:
                raise ValueError(f'Conflicting skill name ({pack}): {name}')
            sources[name] = root / name
    return sources


def _ensure_no_symlink_chain(path: Path):
    """Reject symbolic links *and* Windows junctions along a destination path.

    A junction is a directory reparse point that can redirect writes outside
    the target tree, but Path.is_symlink() does not necessarily detect it.
    """
    for component in (path, *path.parents):
        if component.is_symlink() or component.is_junction():
            raise ValueError(f'Linked destination blocked: {component}')


def install(target, names, apply, layout='codex', skills_dir=None):
    """Install named skills; no writes on dry-run and never overwrite existing files."""
    manifest = json.loads((ROOT / 'MANIFEST.json').read_text(encoding='utf-8'))
    sources = skill_sources(manifest)
    if not names:
        raise ValueError('Provide at least one skill')
    if len(set(names)) != len(names):
        raise ValueError('Duplicate skill names in selection')
    unknown = sorted(set(names) - set(sources))
    if unknown:
        raise ValueError(f'Unknown skill(s): {unknown}')
    for name in names:
        if not sources[name].is_dir() or not (sources[name] / 'SKILL.md').is_file():
            raise FileNotFoundError(f'Source skill missing: {sources[name]}')
    repo = Path(target).expanduser().absolute()
    if not repo.is_dir():
        raise ValueError('Target must be an existing directory')
    _ensure_no_symlink_chain(repo)
    if skills_dir:
        destroot = Path(skills_dir).expanduser().absolute()
    else:
        if layout not in ('codex', 'claude'):
            raise ValueError(f'Unsupported layout: {layout}')
        destroot = repo / ('.agents' if layout == 'codex' else '.claude') / 'skills'
    _ensure_no_symlink_chain(destroot)
    for name in names:
        dest = destroot / name
        if dest.exists() or dest.is_symlink():
            raise FileExistsError(f'Refusing to overwrite: {dest}')
    for name in names:
        print(('INSTALL' if apply else 'DRY-RUN'), ':', name, '->', destroot / name)
    if not apply:
        return
    destroot.mkdir(parents=True, exist_ok=True)
    installed: list[Path] = []
    try:
        for name in names:
            with tempfile.TemporaryDirectory(prefix='.toolkit-staging-', dir=destroot) as temp:
                staged = Path(temp) / name
                shutil.copytree(sources[name], staged, symlinks=False)
                target_skill = destroot / name
                if target_skill.exists() or target_skill.is_symlink():
                    raise FileExistsError(f'Race detected: {target_skill}')
                os.rename(staged, target_skill)
                installed.append(target_skill)
    except Exception:
        for dst in reversed(installed):
            if dst.is_dir():
                shutil.rmtree(dst)
        raise


def main():
    p = argparse.ArgumentParser(description='Install portable skills (dry-run by default)')
    p.add_argument('--target', help='Existing target repository directory')
    select = p.add_mutually_exclusive_group()
    select.add_argument('--skills', help='Comma-separated skill names')
    select.add_argument('--profile', help='Named curated skill profile')
    p.add_argument('--list-profiles', action='store_true')
    p.add_argument('--apply', action='store_true')
    p.add_argument('--layout', choices=['codex','claude'], default='codex')
    p.add_argument('--skills-dir', help='Explicit target skill folder for custom clients')
    args = p.parse_args()
    try:
        manifest = json.loads((ROOT / 'MANIFEST.json').read_text(encoding='utf-8'))
        if args.list_profiles:
            for name, names in sorted(manifest['profiles'].items()):
                print(f'{name}: {", ".join(names)}')
            return
        if not args.target or not (args.skills or args.profile):
            p.error('--target and either --profile or --skills are required')
        if args.profile:
            if args.profile not in manifest['profiles']:
                raise ValueError(f'Unknown profile: {args.profile}')
            names = manifest['profiles'][args.profile]
        else:
            names = [s.strip() for s in args.skills.split(',') if s.strip()]
        install(args.target, names, args.apply, args.layout, args.skills_dir)
    except (ValueError, FileNotFoundError, FileExistsError, OSError) as exc:
        print('ERROR:', exc, file=sys.stderr)
        sys.exit(2)

if __name__ == '__main__':
    main()
