"""Remake the announcer lines (sounds/tts-*.mp3 and sounds/long/tts-*.mp3) from their words in clips.json.

Voices: Kokoro (82M, Apache 2.0), female, af_heart and af_bella taking alternate lines. Kokoro sounds far more
like a person than Piper did (the user asked for female voices that sound more human), so there is no pitch
shift or echo any more: only trimmed silence, a gentle high-pass and loudness matched to -16 LUFS like the rest.

Setup (not preinstalled): pip install kokoro-onnx soundfile, then put kokoro-v1.0.onnx and voices-v1.0.bin from
github.com/thewh1teagle/kokoro-onnx/releases (model-files-v1.0) in KOKORO_DIR (default ~/.cache/kokoro).
Run: python3 tools/sounds/make_tts.py [name ...], then python3 tools/sounds/make_list.py for lengths and pools.
"""
import json, os, subprocess, sys, tempfile
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
SPEED = float(os.environ.get('TTS_SPEED', '0.82'))  # v1.71: slower, the user found 1.0 hard to understand
VOICES = ['af_heart', 'af_bella']
# Spellings Kokoro says right (it read mana as "Mona"); the words shown in the app stay as written.
SAY = {'mana': 'manna', 'Mana': 'Manna'}
kdir = os.environ.get('KOKORO_DIR', os.path.expanduser('~/.cache/kokoro'))
k = Kokoro(os.path.join(kdir, 'kokoro-v1.0.onnx'), os.path.join(kdir, 'voices-v1.0.bin'))
clips = [c for c in json.load(open(os.path.join(ROOT, 'sounds/clips.json'))) if c['f'].split('/')[-1].startswith('tts-')]
only = set(sys.argv[1:])
for i, c in enumerate(sorted(clips, key=lambda c: c['f'])):
    if only and c['f'].split('/')[-1] not in only:
        continue
    voice = VOICES[i % len(VOICES)]
    text = c['quote']
    for a, b in SAY.items():
        text = text.replace(a, b)
    audio, sr = k.create(text, voice=voice, speed=SPEED, lang='en-us')
    with tempfile.NamedTemporaryFile(suffix='.wav') as w:
        sf.write(w.name, audio, sr)
        trim = 'silenceremove=start_periods=1:start_threshold=-50dB'
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', w.name, '-af',
                        f'{trim},areverse,{trim},areverse,highpass=f=80,apad=pad_dur=0.15,loudnorm=I=-16:TP=-1.5:LRA=11',
                        '-ar', '44100', '-ac', '1', '-b:a', '64k', os.path.join(ROOT, 'sounds', c['f'] + '.mp3')], check=True)
    print(voice, c['f'], '|', c['quote'])
