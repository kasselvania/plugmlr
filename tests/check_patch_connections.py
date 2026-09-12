"""Check Pd canvas indexes after text edits; this does not load objects or test DSP.

Usage: python3 tests/check_patch_connections.py sample_player_rebuild.pd
External object availability, types and inlet/outlet counts require native Pd.
"""
import json
from pathlib import Path
import re
import sys


def check(path):
    canvases, stack, errors = [], [], []
    for line, text in enumerate(path.read_text().splitlines(), 1):
        if text.startswith('#N canvas'):
            canvas = {'objects': [], 'connections': []}
            canvases.append(canvas)
            stack.append(canvas)
        elif text.startswith('#X restore'):
            if len(stack) < 2:
                errors.append(f'{line}: unmatched restore')
                continue
            stack.pop()
            stack[-1]['objects'].append(text)
        elif text.startswith('#X connect'):
            match = re.match(r'#X connect (\d+) (\d+) (\d+) (\d+)', text)
            if not match or not stack:
                errors.append(f'{line}: invalid connection')
                continue
            edge = tuple(map(int, match.groups()))
            if max(edge[0], edge[2]) >= len(stack[-1]['objects']):
                errors.append(f'{line}: connection precedes object declaration')
            stack[-1]['connections'].append((line, *edge))
        elif stack and text.startswith('#X ') and not text.startswith(
                ('#X coords', '#X array', '#X f ')):
            stack[-1]['objects'].append(text)
    if len(stack) != 1:
        errors.append('unbalanced canvases')
    for canvas in canvases:
        objects = canvas['objects']
        for line, source, outlet, target, inlet in canvas['connections']:
            if source >= len(objects) or target >= len(objects):
                errors.append(f'{line}: object index outside canvas')
                continue
            if any(objects[i].startswith('#X text') for i in (source, target)):
                errors.append(f'{line}: connection to a text comment')
            for index, port, is_output in ((source, outlet, True),
                                            (target, inlet, False)):
                fields = objects[index].rstrip(';').split(', f ')[0].split()
                if fields[1] == 'obj' and fields[4] in ('t', 'trigger', 'unpack'):
                    count = len(fields[5:]) if is_output else 1
                    if port >= count:
                        errors.append(f'{line}: port outside {fields[4]}')
    return {'file': str(path), 'canvases': len(canvases),
            'objects': sum(len(c['objects']) for c in canvases),
            'connections': sum(len(c['connections']) for c in canvases),
            'errors': errors, 'native_load_or_audio_test': False}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    result = check(Path(sys.argv[1]))
    print(json.dumps(result, indent=2))
    sys.exit(bool(result['errors']))
