"""Editor worker: crop stereo WAV, run Rubber Band outside Pd, publish a new file.

Only the launcher/status protocol is shared with Pd. No application arrays or
transport controls are accessed here. Requires the optional Rubber Band CLI.
"""
import fcntl
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import uuid


def status(base, state, message, output=''):
    tmp = Path(str(base) + '.status.tmp')
    tmp.write_text(f'{state}\n{message}\n{output}\n')
    tmp.replace(str(base) + '.status')


def wav_region(source, dest, first, end, expected_rate):
    """Copy frames, retaining PCM/float encoding; no resampling or normalization."""
    before = source.stat()
    with source.open('rb') as f:
        header = f.read(12)
        if header[:4] != b'RIFF' or header[8:] != b'WAVE':
            raise ValueError('This experiment needs a stereo WAV source')
        fmt = data = None
        while chunk := f.read(8):
            if len(chunk) != 8:
                raise ValueError('Incomplete WAV chunk')
            tag, size = struct.unpack('<4sI', chunk)
            offset = f.tell()
            if offset + size > before.st_size:
                raise ValueError('Incomplete WAV data')
            if tag == b'fmt ':
                if size > 4096:
                    raise ValueError('Unsupported WAV format header')
                fmt = f.read(size)
            elif tag == b'data':
                data = (offset, size)
            f.seek(offset + size + (size & 1))
        if fmt is None or len(fmt) < 16 or data is None:
            raise ValueError('WAV needs format and audio data')
        encoding, channels, rate, _, align, bits = struct.unpack('<HHIIHH', fmt[:16])
        if encoding == 0xFFFE and len(fmt) >= 40:
            encoding = struct.unpack('<I', fmt[24:28])[0]
        if channels != 2 or encoding not in (1, 3) or bits not in (16, 24, 32, 64) or align != channels * bits // 8:
            raise ValueError('Use stereo PCM or float WAV for this experiment')
        if rate != expected_rate or first < 0 or end - first < 4 or end > data[1] // align:
            raise ValueError('Source file no longer matches the selected frames/rate')
        count = (end - first) * align
        with dest.open('xb') as out:
            out.write(b'RIFF' + struct.pack('<I', 4 + 8 + len(fmt) + (len(fmt) & 1) + 8 + count) + b'WAVE')
            out.write(b'fmt ' + struct.pack('<I', len(fmt)) + fmt + b'\0' * (len(fmt) & 1))
            out.write(b'data' + struct.pack('<I', count))
            f.seek(data[0] + first * align)
            remaining = count
            while remaining:
                block = f.read(min(remaining, 1024 * 1024))
                if not block:
                    raise ValueError('Source changed while reading')
                out.write(block)
                remaining -= len(block)
    after = source.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError('Source changed while reading; render again')
    return {'path': str(source), 'size': before.st_size, 'mtime_ns': before.st_mtime_ns,
            'rate': rate, 'first': first, 'end': end, 'channels': channels}


def render(base, source, first, end, rate, ratio, pitch, output_dir):
    if not all(math.isfinite(x) for x in (rate, ratio, pitch)) or rate <= 0 or not .25 <= ratio <= 4 or not -24 <= pitch <= 24:
        raise ValueError('Duration must be 0.25–4x; pitch must be -24–24 semitones')
    if (end - first) / rate * ratio > 600:
        raise ValueError('Rendered copy is limited to 600 seconds')
    exe = next((p for p in [shutil.which('rubberband'), '/opt/homebrew/bin/rubberband', '/usr/local/bin/rubberband'] if p and os.access(p, os.X_OK)), None)
    if not exe:
        raise ValueError('Rubber Band is not installed')
    os.nice(10)
    # One worker across editor instances. Never queue a stale command.
    with open(Path(tempfile.gettempdir()) / 'plugmlr-rubberband.lock', 'a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Another editor is rendering; try again when finished')
        cancel = Path(str(base) + '.cancel')
        with tempfile.TemporaryDirectory(prefix='plugmlr-render-') as temp:
            temp = Path(temp)
            identity = wav_region(source, temp / 'selection.wav', first, end, rate)
            if cancel.exists():
                status(base, 'cancelled', 'Render cancelled');return
            status(base, 'running', 'Rendering copy; playback continues')
            command = [exe, '--fine', '--time', str(ratio), '--pitch', str(pitch), str(temp / 'selection.wav'), str(temp / 'render.wav')]
            started = time.monotonic()
            with (temp / 'worker.log').open('w+') as log:
                child = subprocess.Popen(command, stdout=log, stderr=log)
                try:
                    while child.poll() is None:
                        if cancel.exists():
                            child.terminate();child.wait(timeout=3)
                            status(base, 'cancelled', 'Render cancelled');return
                        if time.monotonic() - started > 120:
                            raise TimeoutError('Render timed out after 120 seconds')
                        time.sleep(.1)
                finally:
                    if child.poll() is None:
                        child.kill();child.wait()
                log.seek(0);diagnostic = log.read()
            if child.returncode:
                raise ValueError('Rubber Band failed: ' + diagnostic.strip().split('\n')[-1][:120])
            if cancel.exists():
                status(base, 'cancelled', 'Render cancelled');return
            output_dir.mkdir(parents=True, exist_ok=True)
            result = output_dir / (source.stem[:60] + '-stretch-' + uuid.uuid4().hex[:12] + '.wav')
            shutil.move(temp / 'render.wav', result)
            version = subprocess.run([exe, '--version'], capture_output=True, text=True, timeout=5)
            result.with_suffix('.json').write_text(json.dumps(dict(source=identity, duration_multiplier=ratio, pitch_semitones=pitch,
                executable=exe, version=(version.stdout + version.stderr).strip(), elapsed_seconds=time.monotonic()-started, log=diagnostic), indent=2))
            status(base, 'ready', 'Copy ready — Load copy, then Audition loop', str(result))


def main():
    base = Path(sys.argv[1])
    try:
        render(base, Path(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7]), Path(sys.argv[8]))
    except Exception as error:
        status(base, 'error', str(error).replace('\n', ' ')[:180])
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
