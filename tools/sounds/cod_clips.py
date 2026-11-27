"""v1.111: cut the Call of Duty turn-button clips from myinstants uploads (fetched into SRC, one
<slug>.bin each) into sounds/ (5 s or less) and sounds/long/ (over 5 s), 10 s at most, -16 LUFS mono 64 kbps,
and add them to sounds/clips.json (group 'Call of Duty'). Run tools/sounds/make_list.py after.
Usage: python3 tools/sounds/cod_clips.py <dir with the .bin files>"""
import json, os, subprocess, sys
SRC = sys.argv[1]
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'sounds')
# name: (myinstants slug, title, quote or None, who, note)
CLIPS = {
 'cod-enemy-uav': ('enemy-uav-warzone-95907', 'Enemy UAV (Warzone)', 'Enemy UAV overhead!', 'Announcer', 'Warzone'),
 'cod-enemy-ac130': ('enemy-ac-130-above-51845', 'ENEMY AC-130 ABOVE!', 'Enemy AC-130 above!', 'Announcer', 'Modern Warfare'),
 'cod-enemy-cruise-missile': ('enemy-cruise-missile-coming-35382', 'enemy cruise missile coming', 'Enemy cruise missile incoming!', 'Announcer', 'Modern Warfare'),
 'cod-gulag': ('welcome-to-the-gulag-26587', 'Welcome to the gulag.', 'Welcome to the Gulag. If you survive, you earn your freedom.', 'Announcer', 'Warzone'),
 'cod-nuke-ready': ('mw2-tactical-nuke-ready-53823', 'MW2 Tactical Nuke Ready', 'Tactical nuke ready. Turn the key.', 'Announcer', 'Modern Warfare 2'),
 'cod-fallback': ('lets-go-fallback-now-cod-modern-warfare-99486', "LET'S GO! FALLBACK NOW! - CoD Modern Warfare", "Let's go! Fall back now!", 'Soldier', 'Modern Warfare'),
 'cod-no-prisoners': ('mw3-take-no-prisoners-99424', 'Mw3 take no prisoners', 'Take no prisoners!', 'Announcer', 'Modern Warfare 3'),
 'cod-be-advised': ('be-advised-your-teammate-got-their-arse-kicked-31004', 'Be advised your teammate got their arse kicked', 'Be advised, your teammate got their arse kicked.', 'Announcer', 'Modern Warfare'),
 'cod-find-ammo': ('i-need-to-find-some-ammunition-52468', 'I need to find some ammunition', 'I need to find some ammunition!', 'Soldier', 'Zombies'),
 'cod-lets-do-this': ('lets-do-this-cod', "Let's Do This Cod", "Let's do this.", 'Soldier', 'Call of Duty'),
 'cod-sam': ('cod-zombies-sam-78640', 'Cod Zombies Sam', 'Sam!', 'Richtofen', 'Zombies'),
 'cod-max-ammo-bo2': ('bo2-max-ammo-12408', 'bo2 max ammo', 'Max ammo!', 'Announcer', 'Black Ops 2 Zombies'),
 'cod-max-ammo-waw': ('cod-waw-zombies-max-ammo-sound-15387', 'COD Waw -Zombies- "Max Ammo" Sound', 'Max ammo!', 'Announcer', 'World at War Zombies'),
 'cod-zombies-nuke': ('cod-zombies-nuke', 'COD zombies nuke', None, None, 'Zombies: Nuke power-up'),
 'cod-kaboom': ('kaboom-zombies-cod-6061', 'Kaboom! Zombies Cod', None, None, 'Zombies'),
 'cod-insta-kill': ('cod-zombies-insta-kill-32630', 'Cod zombies insta kill', None, None, 'Zombies: Insta-Kill'),
 'cod-mystery-box': ('call-of-duty-mystery-box-11991', 'Call of duty mystery box', None, None, 'Zombies: the mystery box'),
 'cod-pack-a-punch': ('cod-zombies-pack-a-punch-59852', 'Cod Zombies Pack a Punch', None, None, 'Zombies: Pack-a-Punch'),
 'cod-round-start': ('cod-zombies-round-start-70658', 'Cod zombies round start', None, None, 'Zombies: a round begins'),
 'cod-round-end': ('call-of-duty-zombies-round-end', 'Call of Duty Zombies Round End', None, None, 'Zombies: a round ends'),
 'cod-new-round': ('call-of-duty-zombies-new-round-sound-945', 'Call of duty zombies new round sound', None, None, 'Zombies'),
 'cod-warzone-level-up': ('warzone-level-up-46714', 'Warzone level up', None, None, 'Warzone'),
 'cod-warzone-victory': ('warzone-victory-71898', 'Warzone Victory', None, None, 'Warzone'),
 'cod-rank-up': ('mw3-rank-up-sound-43373', 'mw3 rank up sound', None, None, 'Modern Warfare 3'),
 'cod-legendary': ('cod-warzone-legendary-sound-58718', 'COD Warzone Legendary Sound', None, None, 'Warzone'),
 'cod-nvg': ('mw2-nvg-intro-50221', 'mw2 nvg intro', None, None, 'Modern Warfare 2: night vision'),
 'cod-airstrike': ('warzone-airstrike-62763', 'WARZONE airstrike', None, None, 'Warzone'),
 'cod-warthog': ('a10-warthog-76372', 'A10 Warthog', None, None, 'A-10 gun run'),
}
data = json.load(open(os.path.join(ROOT, 'clips.json')))
have = {c['f'] for c in data}
for name, (slug, title, quote, who, note) in CLIPS.items():
    src = os.path.join(SRC, slug + '.bin')
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src], capture_output=True, text=True).stdout)
    d = min(dur, 10.0)
    sub = 'long/' if d > 5 else ''
    out = os.path.join(ROOT, sub + name + '.mp3')
    af = f'atrim=0:{d},loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=out:st={max(0, d - 0.2)}:d=0.2'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-ac', '1', '-ar', '44100', '-af', af, '-c:a', 'libmp3lame', '-b:a', '64k', out], check=True)
    key = sub + name
    if key in have: continue
    c = {'f': key, 'src': 'myinstants: ' + title, 'url': 'https://www.myinstants.com/en/instant/' + slug + '/', 'grp': 'Call of Duty',
         'kind': 'talk' if quote else 'sound', 'lic': 'Activision game audio', 'note': note}
    if quote: c.update(quote=quote, who=who)
    data.append(c)
json.dump(data, open(os.path.join(ROOT, 'clips.json'), 'w'), indent=0, ensure_ascii=False)
print(len(CLIPS), 'clips')
