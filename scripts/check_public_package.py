#!/usr/bin/env python3
"""Basic publication safeguards, not a full secrets scan."""
import re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BAD_EXACT={'LICENSE.personal.txt','make-feature-0.3.0.tar.gz','make-feature-0.3.0.tar(1).gz'}
BAD_SUFFIXES={'.exe','.dll','.pem','.p12','.pfx','.zip','.tgz'}
PATTERNS=[r'(?i)your[- ]fitness[- ]coach',r'(?i)second[- ]brain',r'(?i)\byfc\b',r'(?i)github\.com/MikeMoore1337/(?!ai-development-toolkit)',r'(?i)mikhail\.murzaev@']
errors=[]
for p in ROOT.rglob('*'):
 if not p.is_file() or '.git' in p.parts or '__pycache__' in p.parts:continue
 if p.name in BAD_EXACT or p.suffix.lower() in BAD_SUFFIXES:errors.append(f'Forbidden binary/personal file: {p.relative_to(ROOT)}')
 if p.name.startswith('.env') and p.name!='.env.example':errors.append(f'Environment file: {p.relative_to(ROOT)}')
 if p.suffix.lower() not in ('.md','.txt','.json','.yaml','.yml','.py','.ps1','.toml','.sh','.gitignore','.cfg'):continue
 try:content=p.read_text('utf8')
 except UnicodeDecodeError:continue
 for pattern in PATTERNS:
  if re.search(pattern,content):errors.append(f'Sensitive project/license reference: {p.relative_to(ROOT)} / {pattern}')
for e in errors:print('FAIL:',e)
print('PASS: publication hygiene checks' if not errors else f'FAIL: {len(errors)} publication issues')
sys.exit(bool(errors))
