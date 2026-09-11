"""Check the replacement native capture; keep the rejected capture as a failure.
Usage: python3 tests/analyze_beat_reset_listening.py docs/evidence/beat-reset
"""
import json, sys
from pathlib import Path
import numpy as np
from analyze_cut_handoff import jumps
from analyze_beat_reset import events, span

p = Path(sys.argv[1])
x = np.load(p/'musical-long-player-mixer-48.npz')['samples']
r = np.load(p/'musical-long-readers-48.npz')['samples']
windows = [(0.1,1.0),(2.5,3.95),(5.5,6.25)]
rms = [float(np.sqrt(np.mean(span(x,a,b)[:,4:6]**2))) for a,b in windows]
checks = {
 'finite_bounded_capture': bool(335000 < len(x) <= 336064 and len(x)==len(r) and np.isfinite(x).all() and np.isfinite(r).all()),
 'audible_forward_and_both_reverse_passes': all(v > .01 for v in rms),
 'clock_reset_at_two_bars': events(p,'musical-long','1-reset-fired') == [(4050,['128'])],
 'reverse_reset_enters_file_end': bool(abs(span(r,4.05,4.065)[:,2]-631881).min() < 1.1),
 'reverse_motion_before_and_after_reset': all(abs((float(span(r,a,b)[-1,2])-float(span(r,a,b)[0,2]))/(len(span(r,a,b))-1) + .459375)<.02 for a,b in [(3.8,4.0),(4.1,4.3)]),
 'no_nonzero_gain_reader_teleports': not jumps(r),
 'active_mixer_gain_preserved': bool(abs(span(x,.1,6.25)[:,4:6]-.411*span(x,.1,6.25)[:,2:4]).max()<2e-6),
 'automatic_stop_silence': bool(np.all(x[-12000:,2:6]==0)),
 'source_tail_explains_quiet_sections': all(bool(np.max(abs(span(x,a,b)[:,2:6]))<1e-6 and np.min(span(r,a,b)[:,2])>606983) for a,b in [(1.2,2.0),(4.2,5.0)]),
}
result={'checks':checks,'passed':all(checks.values()),'audible_windows_seconds':windows,'post_master_rms':rms,'maximum_adjacent_steps_player_mixer':abs(np.diff(x[:,2:6],axis=0)).max(0).tolist(),'limits':['Human listening is recorded separately in STATUS and manifest','Source silent tail remains audible as gaps; no trimming','48 kHz host only','No universal click-free claim','Earlier musical capture remains rejected']}
print(json.dumps(result,indent=2));sys.exit(0 if result['passed'] else 1)
