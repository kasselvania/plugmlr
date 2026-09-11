import socket,json
from pathlib import Path
rx=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);rx.bind(('127.0.0.1',17935));rx.settimeout(.08)
tx=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);results=[]
def check(cmd,expected):
 tx.sendto((cmd+';\n').encode(),('127.0.0.1',17934));actual=[]
 while True:
  try:actual.extend(s.strip() for s in rx.recv(4096).decode().split(';') if s.strip())
  except socket.timeout:break
 results.append(dict(command=cmd,expected=expected,actual=actual,passed=actual==expected))
for c in ['first 44100','last 485100','rate 44.1']:check(c,[])
check('cells 0 16',['cancel','region keep 1 11'])
check('cells 2 6',['cancel','region keep 2.25 4.75'])
check('cells 15 16',['cancel','region keep 10.375 11'])
for c in ['cells -1 3','cells 4 4','cells 6 2','cells 0 17','cells 1.5 4','cells 2 x','cells x 4','cells 2','cells 2 4 6']:check(c,[])
check('stop bang',['gesture_cancel 91'])
check('paused 1',['gesture_cancel 91'])
check('paused 1',[]) # unchanged paused state must not cancel a fresh paused edit
check('paused 0',[])
check('switching 1',['gesture_cancel 91'])
p=Path('docs/evidence/grid-loop/continuity');p.mkdir(exist_ok=True,parents=True);(p/'native-regions.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(r['passed'] for r in results),[r for r in results if not r['passed']]
print(f'PASS: {len(results)} native conversion/cancellation cases')
