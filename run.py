import os, sys, subprocess, webbrowser, time
from pathlib import Path
from urllib.request import urlopen
root=Path(__file__).resolve().parent
venv=root/".venv"/"Scripts"/"python.exe"
python=venv if venv.exists() else Path(sys.executable)
if venv.exists() and subprocess.run([str(venv),"-m","pip","--version"],capture_output=True).returncode:
    # An interrupted/unsupported venv should not prevent running from the host Python.
    python=Path(sys.executable)
check=subprocess.run([str(python),"-c","import fastapi,uvicorn"],capture_output=True)
if check.returncode:
    if not venv.exists():
        made=subprocess.run([sys.executable,"-m","venv",str(root/".venv")])
        if made.returncode: raise SystemExit("Could not create .venv; install requirements.txt with your Python installation.")
        python=venv
    installed=subprocess.run([str(python),"-m","pip","install","-r",str(root/"requirements.txt")])
    if installed.returncode: raise SystemExit("Dependency installation failed. Run python -m pip install -r requirements.txt and try again.")
url="http://127.0.0.1:8000"
process=subprocess.Popen([str(python),"-m","uvicorn","backend.main:app","--host","127.0.0.1","--port","8000"],cwd=root)
try:
    for _ in range(80):
        if process.poll() is not None: raise SystemExit(process.returncode)
        try:
            with urlopen(url,timeout=.5): break
        except Exception: time.sleep(.15)
    else:
        process.terminate()
        raise SystemExit("AquaAI did not become ready at http://127.0.0.1:8000")
    webbrowser.open(url)
    raise SystemExit(process.wait())
except KeyboardInterrupt:
    process.terminate()
