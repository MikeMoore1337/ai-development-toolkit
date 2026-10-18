#!/usr/bin/env python3
"""Run the *installed upstream* skills-ref binary on every skill in this pack.
No download, installation, or fallback to a fake result.
"""
import argparse, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run(scope='all'):
    binary=shutil.which('skills-ref')
    if binary is None:
        print('NOT RUN: the upstream skills-ref CLI is not on PATH',file=sys.stderr)
        return 2
    groups=[ROOT/'.agents/skills']
    if scope=='all':groups.append(ROOT/'optional-original-skills')
    folders=sorted(p for group in groups for p in group.iterdir() if p.is_dir())
    failures=[]
    for folder in folders:
        proc=subprocess.run([binary,'validate',str(folder)],capture_output=True,text=True,timeout=30)
        if proc.returncode!=0:failures.append((folder.name,proc.stdout.strip(),proc.stderr.strip()))
    for name,out,err in failures:
        print('FAIL',name,out,err)
    print(f'UPSTREAM CHECKS: {len(folders)-len(failures)}/{len(folders)} passed')
    return int(bool(failures))

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--scope',choices=['core','all'],default='all')
    a=ap.parse_args()
    sys.exit(run(a.scope))
