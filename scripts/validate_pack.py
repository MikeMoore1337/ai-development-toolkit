#!/usr/bin/env python3
"""Validate local pack metadata against the published Agent Skills format.

This is NOT the official skills-ref implementation, security audit, or client activation test.
Requires PyYAML >= 6.0. Upstream CLI can additionally validate each skill.
"""
from __future__ import annotations
import json, re, sys, unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ALLOWED={'name','description','license','compatibility','metadata','allowed-tools'}
try:
    import yaml
except ImportError:
    yaml=None


def _valid_name(value:str)->bool:
    if not isinstance(value,str) or not (1<=len(value)<=64):return False
    norm=unicodedata.normalize('NFKC',value)
    if value!=norm or value!=value.lower() or value.startswith('-') or value.endswith('-') or '--' in value:return False
    return all(c.isalnum() or c=='-' for c in value)


def parse_metadata(text:str):
    if yaml is None:raise RuntimeError('PyYAML required: python -m pip install -r requirements-dev.txt')
    m=re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)',text,re.S)
    if not m:raise ValueError('Missing or improperly closed YAML frontmatter')
    class Unique(yaml.SafeLoader):pass
    def unique(loader,node):
        d={}
        for a,b in node.value:
            k=loader.construct_object(a)
            if k in d:raise ValueError(f'Duplicate YAML key: {k}')
            d[k]=loader.construct_object(b)
        return d
    Unique.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,unique)
    doc=yaml.load(m.group(1),Loader=Unique)
    if not isinstance(doc,dict):raise ValueError('YAML frontmatter must be a map')
    return doc


def validate_skill(path:Path)->list[str]:
    errors=[]
    f=path/'SKILL.md'
    if not f.is_file():return [f'{path}: missing SKILL.md']
    try:header=parse_metadata(f.read_text(encoding='utf-8'))
    except Exception as ex:return [f'{f}: {type(ex).__name__}: {ex}']
    unknown=set(header)-ALLOWED
    if unknown:errors.append(f'{f}: unsupported top-level keys: {sorted(unknown)}')
    name=header.get('name')
    if not _valid_name(name) or name != path.name:errors.append(f'{f}: invalid name or mismatch to directory: {name!r}')
    desc=header.get('description')
    if not isinstance(desc,str) or not 1<=len(desc)<=1024 or not desc.strip():errors.append(f'{f}: invalid description')
    compatibility=header.get('compatibility')
    if compatibility is not None and (not isinstance(compatibility,str) or not 1<=len(compatibility)<=500):errors.append(f'{f}: invalid compatibility')
    for k in ('license','allowed-tools'):
        if k in header and not isinstance(header[k],str):errors.append(f'{f}: {k} must be string')
    meta=header.get('metadata')
    if meta is not None and (not isinstance(meta,dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in meta.items())):
        errors.append(f'{f}: metadata must map strings to strings')
    return errors


def _check_links(path:Path, limit_root:Path)->list[str]:
    issues=[]
    data=path.read_text(encoding='utf-8')
    if len(data.splitlines())>500:
        issues.append(f'Long SKILL.md, move details into references: {path}')
    for url in re.findall(r'\[[^\]\n]+\]\(([^)]+)\)',data):
        if url.startswith(('http:','https:','mailto:','#')):continue
        local=url.split('#',1)[0]
        if not local:continue
        dest=(path.parent/local).resolve()
        if not dest.is_relative_to(limit_root.resolve()) or not dest.exists():
            issues.append(f'{path}: broken/escaping link {url}')
    return issues


def inspect()->list[str]:
    issues=[]
    if yaml is None:return ['Missing PyYAML; run: python -m pip install -r requirements-dev.txt']
    manifest=json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf-8'))
    core=ROOT/'.agents/skills'
    names=sorted(p.name for p in core.iterdir() if p.is_dir())
    declared=manifest['core_skills']+manifest.get('extension_skills',[])
    if len(set(declared))!=len(declared) or names!=sorted(declared):issues.append('Core skills differ from MANIFEST.json')
    all_names=set(declared)
    for name in names:
        issues.extend(validate_skill(core/name))
        issues.extend(_check_links(core/name/'SKILL.md',core/name))
    extra=ROOT/'optional-original-skills'
    old=sorted(p for p in extra.iterdir() if p.is_dir())
    if len(old)!=manifest['original_skills_bundled_as_opt_in']:issues.append('Legacy inventory count mismatch')
    for path in old:issues.extend(validate_skill(path))
    for pack,cfg in manifest.get('extension_packs',{}).items():
        base=ROOT/cfg['skill_root']
        pack_names=sorted(p.name for p in base.iterdir() if p.is_dir()) if base.is_dir() else []
        if pack_names != sorted(cfg['skills']): issues.append(f'{pack}: skill manifest/inventory mismatch')
        for n in pack_names:
            if n in all_names: issues.append(f'{pack}: duplicate skill name {n}')
            all_names.add(n)
            issues.extend(validate_skill(base/n))
            issues.extend(_check_links(base/n/'SKILL.md',base/n))
        if 'role_root' in cfg:
            rb=ROOT/cfg['role_root']
            roles=sorted(p.stem for p in rb.glob('*.md'))
            if roles != sorted(cfg.get('roles',[])): issues.append(f'{pack}: role inventory mismatch')
    for profile,chosen in manifest['profiles'].items():
        if not chosen or len(set(chosen))!=len(chosen) or any(n not in all_names for n in chosen):issues.append(f'Invalid profile {profile}')
    roles=sorted(p.stem for p in (ROOT/'.agents/roles').glob('*.md'))
    if roles!=sorted(manifest['core_roles']):issues.append('Role inventory mismatch')
    return issues

if __name__=='__main__':
    issues=inspect()
    for i in issues:print('FAIL:',i)
    print(('PASS' if not issues else 'FAIL')+f": {len(list((ROOT/'.agents/skills').glob('*/SKILL.md')))} core + {sum(len(p['skills']) for p in json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf-8')).get('extension_packs',{}).values())} pack skills")
    sys.exit(bool(issues))
