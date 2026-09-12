"""Build a bounded native UI/mixer check from the current complete mlr.pd.

Close other MLR patches first. Open /tmp/plugmlr-ui-check/check.pd in plugdata,
then send `ui-check-run bang` in its console. Seven seconds, eight-second backup.
Only the copied DAC is replaced by an unconnected signal join: no speaker output.
Original players, buffers, mixer gain/envelopes and all view controls are retained.
"""
from pathlib import Path
import hashlib
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = Path('/tmp/plugmlr-ui-check')
OUT.mkdir(exist_ok=True)
for path in ROOT.iterdir():
    if path.suffix in ('.pd', '.pd_lua', '.lua') or path.name == 'dependencies':
        link = OUT / path.name
        if not link.exists():
            link.symlink_to(path)
        assert link.resolve() == path.resolve()
shutil.copyfile(ROOT / 'DrumLoop.wav', OUT / 'input.wav')

class Patch:
    def __init__(self, offset=0):
        self.objects, self.connections, self.offset = [], [], offset
    def add(self, body):
        index = self.offset + len(self.objects)
        self.objects.append('#X ' + body + ';')
        return index
    def wire(self, a, b, outlet=0, inlet=0):
        self.connections.append(f'#X connect {a} {outlet} {b} {inlet};')
    def text(self):
        return '\n'.join(self.objects + self.connections) + '\n'

def count_root(source):
    count, depth = 0, 0
    for line in source.splitlines():
        if line.startswith('#N canvas'): depth += 1
        elif line.startswith('#X restore'):
            depth -= 1
            if depth == 1: count += 1
        elif depth == 1 and line.startswith(('#X obj ', '#X msg ', '#X text ', '#X floatatom ', '#X symbolatom ', '#X listbox ')):
            count += 1
    return count

source = (ROOT / 'mlr.pd').read_text()
start = source.index('#N canvas', source.index('#N canvas') + 1)
end = source.index('#X restore', start)
mixer = source[start:end]
assert ' mixer 0;' in mixer.splitlines()[0]
assert mixer.count('dac~;') == 1
mixer = mixer.replace('dac~;', 'snake~ in 2;')
p = Patch(count_root(mixer))
# Existing post-master multipliers. Require the production source/wiring shape.
assert '#X connect 20 0 3 0;' in mixer and '#X connect 21 0 3 1;' in mixer
for channel, original in [('L', 20), ('R', 21)]:
    tap = p.add(f'obj 900 1100 s~ \\$0-ui-master-{channel}')
    p.wire(original, tap)
source = source[:start] + mixer + p.text() + source[end:]
p = Patch(count_root(source)); o, c = p.add, p.wire
cap = o('obj 30 1350 writesf~ 6')
for i, channel in enumerate(['L', 'R']):
    r = o(f'obj {30+i*250} 1260 r~ \\$0-ui-master-{channel}'); c(r, cap, 0, i)
for track in (1, 2):
    r = o(f'obj {550+(track-1)*250} 1260 r~ {track}-voice_audio')
    split = o(f'obj {550+(track-1)*250} 1300 snake~ out 2')
    c(r, split); c(split, cap, 0, track*2); c(split, cap, 1, track*2+1)
# Relays only resolve the original root's private view/master destinations.
for j, name in enumerate(['sample-bank-open', 'record-takes-open', 'master-level']):
    r = o(f'obj {30+j*300} 1420 r ui-check-{name}')
    s = o(f'obj {30+j*300} 1460 s \\$0-{name}'); c(r, s)
r = o('obj 30 1520 r ui-check-run'); trig = o('obj 30 1560 t b b b b b'); c(r, trig)
watch = o('obj 650 1640 delay 8000'); c(trig, watch, 4)
clock = o('obj 1050 1600 timer'); c(trig, clock, 3)
events = o('obj 1050 1840 text define \\$0-ui-events')
clear = o('msg 460 1600 clear'); c(trig, clear, 2); c(clear, events)
open_capture = o(f'msg 250 1600 open -bytes 4 {OUT}/capture.wav \\, start'); c(trig, open_capture, 1); c(open_capture, cap)
qlist = o('obj 30 1680 qlist')
score = o(f'msg 30 1600 read {OUT}/score.txt \\, bang'); c(trig, score); c(score, qlist)
r = o('obj 650 1520 r ui-check-stop'); finish = o('obj 650 1560 t b b b b'); c(r, finish); c(watch, finish)
stop = o('msg 950 1680 stop'); c(finish, stop, 3); c(stop, cap); c(stop, watch)
rewind = o('msg 850 1680 rewind'); c(finish, rewind, 2); c(rewind, qlist)
allstop = o('msg 650 1720 \\; 1-ui-stop bang \\; 2-ui-stop bang \\; global-transport 0 \\; mlr-close-views bang'); c(finish, allstop, 1)
save = o(f'msg 650 1780 write {OUT}/events.txt'); c(finish, save); c(save, events)
printdone = o('obj 650 1840 print ui-check-capture-stopped'); c(finish, printdone)
r = o('obj 1050 1520 r \\$0-ui-log'); order = o('obj 1050 1560 t l b'); c(r, order); c(order, clock, 1, 1)
prepend = o('obj 1050 1680 list prepend'); c(clock, prepend, 0, 1); c(order, prepend)
insert = o('obj 1050 1760 text insert \\$0-ui-events 1e+09'); c(prepend, insert)
receivers = ['1-grid-playing', '2-grid-playing', '1-grid-paused', '2-grid-paused',
             '1-grid-position', '2-grid-position', 'audio-1-out', 'audio-2-out',
             '\\$0-master-level', '1-ui-transport', '2-ui-transport',
             '1-ui-slot', '2-ui-slot', 's_b_buffer_states', 'mlr-close-views',
             '1-open-player-view', '16-open-player-view', '\\$0-record-finish',
             'ppq', 'clock-bpm-ui', 'clock-run-ui']
for j, recv in enumerate(receivers):
    x, y = 30+(j%4)*300, 1960+(j//4)*140
    r = o(f'obj {x} {y} r {recv}')
    tag = o(f'obj {x} {y+40} list prepend {recv.replace(chr(92)+"$0-", "")}')
    s = o(f'obj {x} {y+80} s \\$0-ui-log'); c(r, tag); c(tag, s)
(OUT / 'check.pd').write_text(source + '\n' + p.text())
score = [
    (0, '1-sample-path', f'symbol {OUT}/input.wav'),
    (100, '1-buffer-select', 'sample 1'), (100, '2-buffer-select', 'sample 1'),
    (150, '1-clock_mode_enabled', '0'), (150, '2-clock_mode_enabled', '0'),
    (150, 'global-transport', '1'),
    (150, 'audio-1-out', '0.4'), (150, 'audio-2-out', '0.3'),
    (300, '1-press_play', 'bang'), (300, '2-press_play', 'bang'),
    (1000, 'internal-bpm', '120'),
    (1500, '1-press_play', 'bang'), (1800, '1-press_play', 'bang'),
    (2300, '1-ui-stop', 'bang'), (2600, '1-press_play', 'bang'),
    (3000, 'audio-1-out', '0.2'), (3500, 'audio-1-out', '0.4'),
    (4000, 'ui-check-master-level', '0.5'), (4500, 'ui-check-master-level', '0.75'),
    (5000, '1-open-player-view', 'bang'), (5200, 'ui-check-sample-bank-open', 'bang'),
    (5400, '16-open-player-view', 'bang'), (5600, 'ui-check-record-takes-open', 'bang'),
    (5800, 'mlr-close-views', 'bang'),
    (6000, 'global-transport', '0'),
    (6300, '1-ui-stop', 'bang'), (6500, '2-ui-stop', 'bang'),
    (7000, 'ui-check-stop', 'bang'),
]
last = 0; lines = []
for ms, recv, msg in score:
    lines.append(f'{ms-last} {recv} {msg};'); last = ms
(OUT/'score.txt').write_text('\n'.join(lines)+'\n')
sys.path.insert(0, str(ROOT/'tests'))
from check_patch_connections import check
result = check(OUT/'check.pd'); assert not result['errors'], result
hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.pd')}
(OUT/'source.json').write_text(json.dumps({'production_sha256': hashes, 'fixture_sha256': hashlib.sha256((OUT/'check.pd').read_bytes()).hexdigest(), 'score': score, 'changes': 'Only copied DAC replaced; passive audio/message taps and bounded control score appended.'}, indent=2)+'\n')
print(json.dumps(result, indent=2))
