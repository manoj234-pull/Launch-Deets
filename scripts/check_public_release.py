"""Check files Git would publish. Never print credential values or matching lines."""
from pathlib import Path
import argparse
import json
import os
import re
import subprocess
import tempfile


def git_files(root):
    existing = subprocess.run(['git', '-C', str(root), 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
    if existing.returncode == 0:
        if Path(existing.stdout.strip()).resolve() != root:
            raise RuntimeError('The Git root is not the application folder. Do not publish the parent workspace.')
        result = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], capture_output=True, check=True)
        return sorted(set(result.stdout.decode().split('\0')) - {''}), True
    with tempfile.TemporaryDirectory(prefix='launch-deets-release-') as temporary:
        subprocess.run(['git', 'init', '--quiet', temporary], check=True)
        env = dict(os.environ, GIT_DIR=str(Path(temporary)/'.git'), GIT_WORK_TREE=str(root))
        result = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root, env=env, capture_output=True, check=True)
        return sorted(set(result.stdout.decode().split('\0')) - {''}), False


def audit(root):
    names, repository_exists = git_files(root)
    issues = []
    patterns = {
        'credential token': re.compile(r'(?:sk-[A-Za-z0-9_-]{20,}|lsv2_[A-Za-z0-9_-]{15,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{15,})'),
        'private key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
        'personal filesystem path': re.compile(r'(?:[A-Za-z]:[\\/]+Users[\\/]+|/Users/|/home/)[A-Za-z0-9._ -]+[\\/]'),
        'credential URL': re.compile(r'https?://[^\s/:]+:[^\s/@]+@'),
    }
    # Compare local credentials in memory when configured; report only file and field name.
    known = {}
    configured = os.getenv('LAUNCH_DEETS_ENV_FILE')
    for p in [root/'.env', *([Path(configured)] if configured else [])]:
        if p.is_file():
            for line in p.read_text(encoding='utf-8').splitlines():
                if '=' not in line or line.lstrip().startswith('#'): continue
                key, value = line.split('=',1)
                value=value.strip().strip('"\'')
                if re.search(r'(KEY|TOKEN|PASSWORD|SECRET|NEO4J_URI)',key) and len(value)>=8: known[key.strip()]=value
    for name in names:
        p=root/name
        parts=set(p.relative_to(root).parts)
        if (p.name.startswith('.env') and p.name!='.env.example') or parts & {'.venv','.private','project_archive','__pycache__'} or p.suffix in {'.pem','.key','.pfx','.p12'}:
            issues.append({'file':name,'issue':'private file selected for publication'})
        if not p.is_file(): continue
        content=p.read_bytes()
        for key,value in known.items():
            if value.encode() in content: issues.append({'file':name,'issue':'contains configured '+key})
        try: text=content.decode('utf-8')
        except UnicodeDecodeError: continue
        for label,pattern in patterns.items():
            if pattern.search(text): issues.append({'file':name,'issue':label})
        if p.suffix=='.ipynb':
            notebook=json.loads(text)
            if any(c.get('outputs') or c.get('execution_count') is not None for c in notebook['cells'] if c['cell_type']=='code'):
                issues.append({'file':name,'issue':'saved notebook output or execution count'})
        if p.name=='.env.example':
            for line in text.splitlines():
                if '=' in line and not line.startswith('#'):
                    key,value=line.split('=',1)
                    if re.search(r'(API_KEY|PASSWORD|TOKEN|SECRET|NEO4J_URI)',key) and value.strip():
                        issues.append({'file':name,'issue':'populated credential placeholder'})
    return {'candidate_files':len(names),'git_repository_exists':repository_exists,'issues':issues}, names


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args()
    result,_=audit(args.root.resolve())
    print(json.dumps(result,indent=2))
    raise SystemExit(bool(result['issues']))
