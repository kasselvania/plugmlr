"""Read actual Pd feedback messages. Open grid-feedback-check.pd with MLR closed."""
import socket,json,time
from pathlib import Path
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.bind(('127.0.0.1',17931));s.settimeout(.08)
def clear(row):return f'/monome/grid/led/row 0 {row} 0 0'
def marker(row,col):return [clear(row),f'/monome/grid/led/level/set {col} {row} 12']
cases=[('position 0',[]),('ready 1',[]),('playing 1',[]),
 ('connected 1',marker(1,0)+[clear(2)]),('position 0.5',marker(1,8)),
 ('position 1',marker(1,15)),('position 0.9999',[]),('position 0.25',marker(1,4)),
 ('paused 1',[clear(1)]),('position 0.75',[]),('paused 0',marker(1,12)),
 ('playing 0',[clear(1)]),('playing 1',marker(1,12)),('switching 1',[clear(1)]),
 ('position 0.5',[]),('switching 0',marker(1,8)),('ready 0',[clear(1)]),
 ('ready 1',marker(1,8)),('ready_b 1',[]),('playing_b 1',marker(2,0)),
 ('position_b 0.5',marker(2,8)),('position 0.1',marker(1,1)),
 ('connected 0',[]),('position 0.5',[]),('connected 1',marker(1,8)+marker(2,8)),
 ('position -0.1',[clear(1)]),('position 1.1',[]),('position 1',marker(1,15)),('connected 0',[])]
results=[]
for cmd,expected in cases:
 s.sendto((cmd+';\n').encode(),('127.0.0.1',17930));observed=[]
 while True:
  try:observed += [p.strip() for p in s.recv(4096).decode().split(';') if p.strip()]
  except socket.timeout:break
 # On connection, two independent renderers may receive in either order.
 ok=observed==expected if not cmd.startswith('connected 1') else sorted(observed)==sorted(expected)
 results.append(dict(command=cmd,expected=expected,observed=observed,passed=ok))
p=Path('docs/evidence/grid-feedback');p.mkdir(parents=True,exist_ok=True)
(p/'native-message-checks.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(r['passed'] for r in results),[r for r in results if not r['passed']]
print(f'PASS: {len(results)} actual Pd command sequences')
