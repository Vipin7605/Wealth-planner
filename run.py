"""Local launcher: isolated environment, dependencies, model, then web server."""
from pathlib import Path
import argparse,hashlib,json,os,socket,subprocess,sys,time,venv,webbrowser
ROOT=Path(__file__).resolve().parent
def main():
    if not (3,11)<=sys.version_info[:2]<=(3,13):raise SystemExit('Please install Python 3.11, 3.12 or 3.13, then run this file again.')
    parser=argparse.ArgumentParser(description='Start the local AI Wealth Growth Planner')
    parser.add_argument('--no-browser',action='store_true');parser.add_argument('--port',type=int,default=8000);args=parser.parse_args()
    if not 1024<=args.port<=65535:raise SystemExit('Choose a port between 1024 and 65535.')
    with socket.socket() as sock:
        try:sock.bind(('127.0.0.1',args.port))
        except OSError:raise SystemExit(f'Port {args.port} is busy. Close the other app or use --port 8001.')
    envdir=ROOT/'.venv';python=envdir/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not python.exists():
        print('Creating a project-only Python environment…',flush=True);venv.create(envdir,with_pip=True)
    stamp=envdir/'.requirements-sha256';digest=hashlib.sha256((ROOT/'requirements.txt').read_bytes()).hexdigest()
    if not stamp.exists() or stamp.read_text()!=digest:
        print('Installing project dependencies. Internet is required on first start…',flush=True)
        subprocess.run([str(python),'-m','pip','install','-r',str(ROOT/'requirements.txt')],cwd=ROOT,check=True)
        print('Training the synthetic-data model for this environment…',flush=True)
        subprocess.run([str(python),'ml/train.py'],cwd=ROOT,check=True);stamp.write_text(digest)
    elif not (ROOT/'ml'/'model.joblib').exists():subprocess.run([str(python),'ml/train.py'],cwd=ROOT,check=True)
    if not (ROOT/'frontend'/'dist'/'index.html').exists():raise SystemExit('Frontend build is missing. Run npm ci and npm run build inside frontend/.')
    env=os.environ.copy()
    # Optional .env settings stay on the backend. Environment variables take precedence.
    dot=ROOT/'.env'
    if dot.exists():
        for raw in dot.read_text().splitlines():
            line=raw.strip()
            if line and not line.startswith('#') and '=' in line:
                k,v=line.split('=',1);env.setdefault(k.strip(),v.strip().strip('"').strip("'"))
    env.setdefault('ALLOWED_ORIGINS',f'http://127.0.0.1:{args.port},http://localhost:{args.port}')
    url=f'http://127.0.0.1:{args.port}'
    process=subprocess.Popen([str(python),'-m','uvicorn','backend.main:app','--host','127.0.0.1','--port',str(args.port)],cwd=ROOT,env=env)
    try:
        import urllib.request
        for _ in range(60):
            if process.poll() is not None:raise SystemExit('The server did not start. See the error above.')
            try:
                with urllib.request.urlopen(url+'/api/health',timeout=1) as res:
                    if json.loads(res.read())['status']=='ok':break
            except Exception:time.sleep(.5)
        else:raise SystemExit('Server startup timed out.')
        print(f'\nWealthwise is ready: {url}\nKeep this terminal open. Press Ctrl+C to stop.\n',flush=True)
        if not args.no_browser:webbrowser.open(url)
        process.wait()
    except KeyboardInterrupt:print('\nStopping Wealthwise…')
    finally:
        if process.poll() is None:
            process.terminate()
            try:process.wait(timeout=8)
            except subprocess.TimeoutExpired:process.kill()
if __name__=='__main__':
    try:main()
    except subprocess.CalledProcessError as exc:raise SystemExit(f'Setup failed (exit {exc.returncode}). Check the connection and error above, then rerun. Your saved data is unchanged.')
