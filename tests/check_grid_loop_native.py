"""Exercise actual pd-lua gestures in the silent native fixture; no audio/device."""
import socket, json
from pathlib import Path
rx=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);rx.bind(('127.0.0.1',17933));rx.settimeout(.08)
tx=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
results=[]
def check(command, expected):
    tx.sendto((command+';\n').encode(),('127.0.0.1',17932))
    actual=[]
    while True:
        try: actual.extend(s.strip() for s in rx.recv(8192).decode().split(';') if s.strip())
        except socket.timeout: break
    results.append(dict(command=command, expected=expected, actual=actual, passed=actual==expected))
check('key 0 1 1',[])
check('connected 1',['led /monome/grid/led/row 0 0 0 0','led /monome/grid/led/level/set 1 0 8','led /monome/grid/led/level/set 15 0 4'])
check('key 3 1 1',['focus 1','slice 3 1 1'])
check('key 3 1 1',[])
check('key 15 0 1',['led /monome/grid/led/level/set 15 0 15'])
check('key 3 1 0',[])
check('key 3 1 1',['play 1'])
check('key 3 1 1',[])
check('key 15 0 0',['led /monome/grid/led/level/set 15 0 4'])
check('key 3 1 0',[])
check('key 3 1 1',['slice 3 1 1'])
check('key 3 1 0',[])
check('key 15 0 1',['led /monome/grid/led/level/set 15 0 15'])
check('key 7 2 1',['focus 2','play 2'])
check('key 7 2 0',[])
check('key 7 2 1',['play 2'])
check('connected 0',[])
check('key 8 1 1',[])
check('connected 1',['led /monome/grid/led/row 0 0 0 0','led /monome/grid/led/level/set 1 0 8','led /monome/grid/led/level/set 15 0 4'])
check('key 7 2 1',['slice 7 2 1'])
check('key 7 2 0',[])
check('key 1 0 1',[])
check('key 0 7 1',[])
for c in ['key -1 1 1','key 16 1 1','key 0 8 1','key 0 1 2','key 0.5 1 1','key x 1 1','key 1 1','key 1 1 1 1']:
    check(c,[])
for row in range(3,7):
    check(f'key 0 {row} 1',[f'focus {row}',f'slice 0 {row} 1'])
# Clear all held keys and ALT, retain focus (6).
check('connected 0',[])
check('connected 1',['led /monome/grid/led/row 0 0 0 0','led /monome/grid/led/level/set 1 0 8','led /monome/grid/led/level/set 15 0 4'])
check('key 2 1 1',['focus 1','slice 2 1 1'])
check('key 5 1 1',[])
check('key 2 1 0',['loop 1 2 6'])
check('key 5 1 0',[])
# reverse press/release ordering, inclusive outer cells
check('key 15 1 1',['slice 15 1 1'])
check('key 0 1 1',[])
check('key 0 1 0',['loop 1 0 16'])
check('key 15 1 0',[])
# three-key cancellation
check('key 1 1 1',['slice 1 1 1'])
check('key 4 1 1',[])
check('key 8 1 1',[])
for x in [1,4,8]: check(f'key {x} 1 0',[])
# cancellation from player Stop/Pause/selection
check('key 2 1 1',['slice 2 1 1'])
check('key 7 1 1',[])
check('cancel 1',[])
check('key 2 1 0',[])
check('key 7 1 0',[])
# ALT cancels pair, transport release cannot become loop
check('key 2 1 1',['slice 2 1 1'])
check('key 7 1 1',[])
check('key 15 0 1',['led /monome/grid/led/level/set 15 0 15'])
check('key 2 1 0',[])
check('key 7 1 0',[])
check('key 4 1 1',['play 1'])
check('key 15 0 0',['led /monome/grid/led/level/set 15 0 4'])
check('key 4 1 0',[])
# independent pairs across rows
check('key 1 1 1',['slice 1 1 1'])
check('key 3 2 1',['focus 2','slice 3 2 1'])
check('key 6 1 1',['focus 1'])
check('key 9 2 1',['focus 2'])
check('key 6 1 0',['loop 1 1 7'])
check('key 3 2 0',['loop 2 3 10'])
check('key 1 1 0',[])
check('key 9 2 0',[])
# detached pair releases do not commit
check('key 0 2 1',['slice 0 2 1'])
check('key 1 2 1',[])
check('connected 0',[])
check('key 0 2 0',[])
check('connected 1',['led /monome/grid/led/row 0 0 0 0','led /monome/grid/led/level/set 1 0 8','led /monome/grid/led/level/set 15 0 4'])
check('key 1 2 0',[])
p=Path('docs/evidence/grid-loop');p.mkdir(parents=True,exist_ok=True)
(p/'native-keys.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(r['passed'] for r in results), [r for r in results if not r['passed']]
print(f'PASS: {len(results)} native gesture sequences')
