"""Optional external-process candidate. No shell execution or patch integration."""
from pathlib import Path
import subprocess,shutil,time,json
p=Path('/tmp/plugmlr-stretch-workbench');exe=shutil.which('rubberband')
if not exe:raise SystemExit('Rubber Band is optional and not installed; bundled vocoder test remains available.')
version=subprocess.run([exe,'--version'],capture_output=True,text=True,check=True)
start=time.time();t=time.monotonic()
r=subprocess.run([exe,'--fine','--time','2','--pitch','12',str(p/'source.wav'),str(p/'rubberband.wav')],capture_output=True,text=True,timeout=30)
(p/'worker.json').write_text(json.dumps(dict(executable=exe,version=(version.stdout+version.stderr).strip(),started_unix=start,elapsed_seconds=time.monotonic()-t,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr),indent=2)+'\n')
print(p/'worker.json');raise SystemExit(r.returncode)
