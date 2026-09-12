"""Check actual native event readback, not a simulated buffer state machine."""
from pathlib import Path
import json, shlex, sys

def analyze(path):
    rows=[shlex.split(line.rstrip(';')) for line in (path/'events.txt').read_text().splitlines()]
    replies={(int(float(r[0])),int(r[4])):(int(r[5]),int(r[8]),r[-1])
             for r in rows if len(r)>9 and r[1:4]==['clear-route-reply','info','live']}
    checks={}
    for t in (400,550,650):
        for slot in (3,4):
            checks[f'live_{slot}_preserved_at_{t}ms']=replies.get((t,slot))==(1,4800,'Unsaved')
    checks['armed_clear_keeps_live_3']=replies.get((760,3))==(1,4800,'Unsaved')
    checks['deliberate_discard_clears_live_3']=replies.get((850,3))==(0,0,'Empty')
    checks['live_4_unaffected_by_deliberate_discard']=replies.get((850,4))==(1,4800,'Unsaved')
    checks['repeat_discard_stays_empty']=replies.get((950,3))==(0,0,'Empty')
    checks['no_actions_forwarded_during_switch']=not any(
        r[1] in ('3_l_b_delete_buffer','4_l_b_delete_buffer') and 500<=float(r[0])<620 for r in rows)
    checks['settled_actions_forwarded']=all(any(float(r[0])==t and r[1]=='3_l_b_delete_buffer' for r in rows) for t in (750,800,900))
    return {'checks':checks,'passed':sum(checks.values()),'total':len(checks),
            'pass':all(checks.values()),'evidence':'Native Pd timestamped control and content metadata. Not a listening or button-hit test.'}
if __name__=='__main__':
    result=analyze(Path(sys.argv[1]));print(json.dumps(result,indent=2));sys.exit(0 if result['pass'] else 1)
