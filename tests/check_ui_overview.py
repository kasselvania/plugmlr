"""Protect the UI-only boundary against the pre-UI PR36 source.

Checks actual current sources, original nested engine wiring, and display-only
adapters. Native rendering and audio remain separate tests.
"""
from pathlib import Path
import json
import re
import subprocess
from check_patch_connections import check
ROOT = Path(__file__).resolve().parents[1]
BASE = '95a2d612fbb8c799c309850fc53d106d8211ff44'
UI = {'mlr.pd','player-panel.pd','buffer-panel.pd','slice-panel.pd',
      'slice-mode-control.pd','record-take-row.pd','record-takes-panel.pd'}
NEW = {'track-overview-row.pd','player-overview-bridge.pd','sample-bank-panel.pd',
       'sample-bank-row.pd','ui-open-view.pd'}
def old(name):
    return subprocess.check_output(['git','show',f'{BASE}:{name}'],cwd=ROOT,text=True)

def subpatches(source):
    result, stack = {}, []
    for line in source.splitlines():
        if line.startswith('#N canvas'):
            stack.append([line])
        elif line.startswith('#X restore'):
            child = stack.pop()
            name = line.split(' pd ')[-1].rstrip(';')
            result[name] = child
            stack[-1].extend(child + [line])
        elif stack:
            stack[-1].append(line)
    return result

def run():
    protected = []
    tracked = subprocess.check_output(['git','ls-tree','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    for name in tracked:
        if name.endswith('.pd') and name not in UI:
            current = (ROOT/name).read_text()
            # Subsequent waveform slice: diagnostic sinks may be gated, and
            # buffer views append receive-only metadata observers. Original
            # objects/connections still match this checkpoint exactly.
            current = current.replace('debug-print ', 'print ')
            if name == 'loop-region-control.pd':
                extension = '\n#X obj 1500 1050 loop-window-control \\$1 \\$2;\n'
                assert current.endswith(extension), 'Unexpected live loop control attachment'
                current = current[:-len(extension)]
            if name == 'sample_player_rebuild.pd':
                gate = '\n#X obj 2700 125 r \\$0-stop-direction-reset;\n#X connect 545 0 509 1;\n'
                assert current.endswith(gate), 'Unexpected direction preservation gate'
                current = current[:-len(gate)]
                stop_extension = '#X obj 900 60 route preserve;\n#X obj 900 100 t b b;\n#X obj 1020 100 t b b;\n#X msg 950 145 0;\n#X msg 1070 145 1;\n#X obj 900 580 f 1;\n#X obj 25 620 t b b b;\n#X obj 900 660 s \\$0-stop-direction-reset;\n#X msg 900 700 1;\n#X text 600 430 Buffer changes stop through the same fade but retain direction.;\n#X connect 0 0 31 0;\n#X connect 31 0 32 0;\n#X connect 31 1 33 0;\n#X connect 32 1 34 0;\n#X connect 33 1 35 0;\n#X connect 34 0 36 1;\n#X connect 35 0 36 1;\n#X connect 32 0 4 0;\n#X connect 33 0 4 0;\n#X connect 18 2 37 0;\n#X connect 37 2 36 0;\n#X connect 36 0 38 0;\n#X connect 37 1 2 0;\n#X connect 37 0 39 0;\n#X connect 39 0 38 0;\n'
                assert current.count(stop_extension) == 1
                current = current.replace(stop_extension, '')
                # Restore only the two replaced edges in pd stop_transition.
                begin = current.index('#N canvas 100 80 1100 900 stop_transition')
                end = current.index('#X restore', begin)
                stop = current[begin:end]
                stop = stop.replace('rechecking the buffer and starting again.;\n\n', 'rechecking the buffer and starting again.;\n#X connect 0 0 4 0;\n')
                stop = stop.replace('#X connect 17 0 18 0;\n\n', '#X connect 17 0 18 0;\n#X connect 18 2 2 0;\n')
                current = current[:begin]+stop+current[end:]
            if name == 'buffer-selection.pd':
                preserve = '\n#X obj 900 1080 s \\$1-stop_button;\n#X connect 76 0 99 0;\n'
                assert current.endswith(preserve)
                current = current[:-len(preserve)].replace('#X msg 900 1030 preserve;', '#X obj 900 1030 s \\$1-stop_button;')
            if name == 'sample-data.pd':
                trim = '\n#X obj 600 400 sample-trim \\$1;\n#X connect 29 0 52 0;\n#X connect 52 0 18 0;\n'
                assert current.endswith(trim), 'Unexpected trim-owner wiring'
                current = current[:-len(trim)].replace('#X connect 28 3 30 0;\n\n', '#X connect 28 3 30 0;\n#X connect 29 0 18 0;\n')
            if name == 'sample_player_rebuild.pd':
                offset = '\n#X obj 2400 165 +;\n#X obj 2500 125 r \\$0-first_index;\n#X text 2400 205 Slice coordinates include the usable sample start.;\n#X connect 84 0 542 0;\n#X connect 543 0 542 1;\n#X connect 542 0 466 0;\n'
                assert current.endswith(offset), 'Unexpected slice offset wiring'
                current = current[:-len(offset)].replace('#X connect 83 0 81 0;\n\n', '#X connect 83 0 81 0;\n#X connect 84 0 466 0;\n')
            # Take protection inserts a gate before the unchanged Clear path.
            if name == 'sample_player_rebuild.pd':
                initialization = '#X obj 900 390 loadbang;\n#X text 900 430 No slice is pending at load. Allow the first natural wrap.;\n#X connect 31 0 16 0;\n'
                assert current.count(initialization) == 1, 'Missing first-wrap initialization'
                current = current.replace(initialization, '')
            if name == 'live_buffer.pd':
                current = current.replace('#X obj 1806 18 take-clear-control \\$1;',
                                          '#X obj 1806 18 r \\$1_l_b_delete_buffer, f 21;')
            if name == 'buffer-selection.pd':
                switch_guard = '\n#X obj 1140 940 spigot 1;\n#X obj 1370 865 r \\$1-buffer-switching;\n#X obj 1370 900 == 0;\n#X text 1080 1040 Ignore Clear/Discard until selection has installed the new target.;\n#X connect 95 0 80 0;\n#X connect 96 0 97 0;\n#X connect 97 0 95 1;\n#X connect 79 0 95 0;\n'
                assert current.endswith(switch_guard), 'Missing Clear switch guard'
                current = current[:-len(switch_guard)]
                # Restore the removed old edge at any point after its objects.
                current = current.replace('#X connect 78 0 79 0;', '#X connect 78 0 79 0;\n#X connect 79 0 80 0;')
                suffix = '\n#X obj 25 1100 s mlr-cancel-clear;\n#X connect 24 0 94 0;\n'
                assert current.endswith(suffix), 'Unexpected discard-cancellation wiring'
                current = current[:-len(suffix)]
            if name in ('sample-data.pd', 'live_buffer.pd'):
                suffix = current[len(old(name)):]
                expected = {'sample-data.pd': '\n#X obj 355 355 buffer-view-data sample \\$1;\n#X connect 40 1 51 0;\n',
                            'live_buffer.pd': '\n#X obj 35 630 buffer-view-data live \\$1;\n'}
                assert suffix == expected[name], f'Unexpected buffer-view wiring: {name}'
                current = current[:len(old(name))]
            assert current == old(name), f'Unexpected engine/source edit: {name}'
            protected.append(name)
    before, after = subpatches(old('mlr.pd')), subpatches((ROOT/'mlr.pd').read_text())
    for name in ('arrays-samples','clock-system','grid-input-output'):
        assert before[name][1:] == after[name][1:], name
    # Only Master moved: preserve every other nested mixer object and all wires.
    old_mixer, new_mixer = before['mixer'], after['mixer']
    assert len(old_mixer) == len(new_mixer)
    changes = [(a,b) for a,b in zip(old_mixer,new_mixer) if a!=b]
    assert len(changes)==1 and 'knob 50 0 1 0 0.75' in changes[0][0]
    assert changes[0][1] == '#X obj 180 921 r \\$0-master-level;'
    moved = next(l for l in (ROOT/'mlr.pd').read_text().splitlines() if 'knob 50 0 1 0 0.75' in l)
    normalize = lambda s: re.sub(r'\\\$0-master-(?:level|show)', 'empty', ' '.join(s.split()[4:]))
    assert normalize(moved) == normalize(changes[0][0]), 'Master parameters changed'
    # Existing public musical send/receive symbols remain in focused views.
    for name in ('player-panel.pd','buffer-panel.pd','slice-panel.pd','slice-mode-control.pd','record-take-row.pd'):
        symbols = lambda s: set(re.findall(r'\\\$[12]-[A-Za-z0-9_-]+',s))
        assert symbols(old(name)) <= symbols((ROOT/name).read_text()), name
    for name in NEW:
        for line in (ROOT/name).read_text().splitlines():
            if line.startswith('#X obj '):
                assert '~' not in line.split()[4], f'Audio object in view {name}: {line}'
    layouts = [('mlr.pd',r'#X obj (\d+) (\d+) track-overview-row (\d+);',28),
               ('sample-bank-panel.pd',r'#X obj (\d+) (\d+) sample-bank-row (\d+);',32),
               ('record-takes-panel.pd',r'#X obj (\d+) (\d+) record-take-row \\\$1 (\d+);',30)]
    for name, pattern, height in layouts:
        rows = [tuple(map(int,m)) for m in re.findall(pattern,(ROOT/name).read_text())]
        assert [r[2] for r in rows] == list(range(1,17)), name
        assert all(b[1]-a[1]>=height for a,b in zip(rows,rows[1:])), f'Overlapping rows: {name}'
    structures = [check(ROOT/name) for name in sorted(UI|NEW)]
    assert all(not s['errors'] for s in structures)
    return {'base':BASE,'protected_engine_files':protected,'allowed_changes':'Routine print gates, buffer preview observers, Clear gate and selection cancellation; first-wrap initialization; original DSP connections preserved','original_nested_engines_preserved':True,
            'only_nested_mixer_change':'Master widget replaced by its named receiver; original connections unchanged',
            'all_16_rows_distinct_and_nonoverlapping':True,'structures':structures,
            'native_or_listening_acceptance':False}

if __name__ == '__main__': print(json.dumps(run(),indent=2))
