import math
import os
import random
import socket
import subprocess
import sys
import threading
import time
import json
from array import array
import pygame
from shared import *

SERVER_IP = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
NAME = sys.argv[2] if len(sys.argv) > 2 else "Player"
ROOM_CODE = sys.argv[3] if len(sys.argv) > 3 else ""
PORT = 50007

def app_dir():
    return os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))


def resolve_server_launcher():
    base = app_dir()
    candidates = [
        ([os.path.join(base, "REDONDOS_Server.exe")], base),
        ([os.path.join(base, "server.exe")], base),
        ([sys.executable, os.path.join(base, "server.py")], base),
    ]
    for cmd, cwd in candidates:
        target = cmd[0] if len(cmd) == 1 else cmd[1]
        if os.path.exists(target):
            return cmd, cwd
    return [sys.executable, os.path.join(base, "server.py")], base


CONFIG_PATH = os.path.join(app_dir(), "client_config.json")
LOCAL_SERVER_PID_PATH = os.path.join(app_dir(), "local_server.pid")

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
if pygame.mixer.get_init():
    pygame.mixer.set_num_channels(24)
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("REDONDOS - Cliente")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 20)
big = pygame.font.SysFont("arial", 42, bold=True)
small = pygame.font.SysFont("arial", 15)

state = None
state_lock = threading.Lock()
connected = False

sock = None
local_server = None
local_server_config = None
local_server_owned = False

CARD_RECTS = []
CARD_ACTION_RECTS = []
GAME_MENU_RECT = pygame.Rect(792, 14, 96, 38)
PARRY_BUTTON_RECT = pygame.Rect(WIDTH - 206, HEIGHT - 104, 176, 64)
SEEN_EFFECTS = set()
LAST_AUDIO_STATE = {"my_bullets": 0, "my_hp": None, "phase": None, "chosen": False, "hazard_count": 0, "arena_id": None}
SFX_ENABLED = True
AUDIO_VOLUMES = {"ui": 0.55, "combat": 0.65, "hazards": 0.55}
AMBIENT_CHANNEL = None


def load_client_config():
    default = {"sfx_enabled": True, "audio_ui": 0.55, "audio_combat": 0.65, "audio_hazards": 0.55}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        default.update({k: data[k] for k in default if k in data})
    except Exception:
        pass
    return default


def save_client_config():
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
            json.dump({"sfx_enabled": SFX_ENABLED, "audio_ui": AUDIO_VOLUMES["ui"], "audio_combat": AUDIO_VOLUMES["combat"], "audio_hazards": AUDIO_VOLUMES["hazards"]}, fh)
    except Exception:
        pass


def read_local_server_pid():
    try:
        with open(LOCAL_SERVER_PID_PATH, "r", encoding="utf-8") as fh:
            return int(fh.read().strip())
    except Exception:
        return None


def write_local_server_pid(pid):
    try:
        with open(LOCAL_SERVER_PID_PATH, "w", encoding="utf-8") as fh:
            fh.write(str(int(pid)))
    except Exception:
        pass


def clear_local_server_pid():
    try:
        if os.path.exists(LOCAL_SERVER_PID_PATH):
            os.remove(LOCAL_SERVER_PID_PATH)
    except Exception:
        pass


_cfg = load_client_config()
SFX_ENABLED = bool(_cfg["sfx_enabled"])
AUDIO_VOLUMES = {"ui": float(_cfg["audio_ui"]), "combat": float(_cfg["audio_combat"]), "hazards": float(_cfg["audio_hazards"])}


def build_wave(freq=440, duration=0.12, volume=0.35, wave="sine", slide=0.0, noise=0.0, decay=1.0):
    sample_rate = 44100
    total = max(1, int(sample_rate * duration))
    buf = array("h")
    for i in range(total):
        t = i / sample_rate
        prog = i / max(1, total - 1)
        current_freq = max(20.0, freq + slide * prog)
        phase = math.tau * current_freq * t
        if wave == "square":
            value = 1.0 if math.sin(phase) >= 0 else -1.0
        elif wave == "triangle":
            value = 2.0 * abs(2.0 * ((t * current_freq) % 1.0) - 1.0) - 1.0
        elif wave == "noise":
            value = random.uniform(-1.0, 1.0)
        else:
            value = math.sin(phase)
        if noise:
            value = value * (1.0 - noise) + random.uniform(-1.0, 1.0) * noise
        env = max(0.0, (1.0 - prog) ** decay)
        sample = int(max(-1.0, min(1.0, value * volume * env)) * 32767)
        buf.append(sample)
        buf.append(sample)
    return pygame.mixer.Sound(buffer=buf.tobytes())


def init_sound_bank():
    if not pygame.mixer.get_init():
        return {}
    return {
        "shoot": build_wave(760, 0.06, 0.22, wave="square", slide=-260, decay=1.8),
        "shoot_heavy": build_wave(420, 0.09, 0.26, wave="square", slide=-120, decay=1.4),
        "shoot_homing": build_wave(620, 0.10, 0.20, wave="sine", slide=140, decay=1.2),
        "shoot_buckshot": build_wave(210, 0.07, 0.24, wave="noise", noise=0.55, decay=1.9),
        "shoot_rail": build_wave(1180, 0.08, 0.20, wave="triangle", slide=-380, decay=0.9),
        "bounce": build_wave(980, 0.05, 0.18, wave="triangle", slide=-90, decay=1.3),
        "hit": build_wave(180, 0.08, 0.28, wave="noise", noise=0.65, decay=2.0),
        "hit_heavy": build_wave(90, 0.18, 0.32, wave="noise", noise=0.72, decay=1.4),
        "poison": build_wave(300, 0.14, 0.18, wave="sine", slide=-160, noise=0.25, decay=1.0),
        "card": build_wave(540, 0.12, 0.26, wave="triangle", slide=210, decay=1.4),
        "card_special": build_wave(860, 0.16, 0.22, wave="triangle", slide=320, decay=1.0),
        "card_fusion": build_wave(1180, 0.18, 0.20, wave="triangle", slide=420, decay=0.9),
        "freeze_card": build_wave(970, 0.12, 0.20, wave="triangle", slide=-220, decay=1.0),
        "burn_card": build_wave(200, 0.13, 0.24, wave="noise", noise=0.52, decay=1.3),
        "parry": build_wave(980, 0.09, 0.26, wave="triangle", slide=-180, decay=1.0),
        "active": build_wave(420, 0.18, 0.24, wave="sine", slide=180, decay=1.6),
        "portal": build_wave(640, 0.20, 0.18, wave="sine", slide=-260, noise=0.15, decay=0.9),
        "swarm": build_wave(780, 0.16, 0.18, wave="square", slide=180, decay=1.4),
        "remote": build_wave(170, 0.16, 0.20, wave="square", slide=-60, decay=1.0),
        "laser": build_wave(250, 0.24, 0.22, wave="square", slide=720, decay=0.8),
        "tornado": build_wave(140, 0.32, 0.20, wave="noise", noise=0.85, decay=0.9),
        "nuke": build_wave(70, 0.45, 0.32, wave="noise", noise=0.55, decay=0.7),
        "freeze": build_wave(1200, 0.18, 0.18, wave="triangle", slide=-650, decay=1.1),
        "quake": build_wave(80, 0.24, 0.26, wave="noise", noise=0.65, decay=0.9),
        "rift": build_wave(520, 0.22, 0.20, wave="sine", slide=-420, noise=0.20, decay=0.8),
        "wind": build_wave(160, 0.25, 0.16, wave="noise", noise=0.92, decay=0.7),
        "portal_storm": build_wave(430, 0.24, 0.22, wave="sine", slide=-320, noise=0.18, decay=0.9),
        "remote_detonator": build_wave(110, 0.22, 0.24, wave="square", slide=80, noise=0.12, decay=1.0),
        "omega_event_horizon": build_wave(55, 0.52, 0.28, wave="noise", noise=0.72, decay=0.65),
        "judgement_day": build_wave(90, 0.46, 0.30, wave="noise", noise=0.58, decay=0.75),
        "tempest_cataclysm": build_wave(180, 0.38, 0.24, wave="noise", noise=0.86, decay=0.8),
    }


SOUNDS = init_sound_bank()
SOUND_CATEGORY = {
    "shoot": "combat", "shoot_heavy": "combat", "shoot_homing": "combat", "shoot_buckshot": "combat", "shoot_rail": "combat",
    "bounce": "combat", "hit": "combat", "hit_heavy": "combat", "poison": "combat", "parry": "combat", "active": "combat",
    "portal": "combat", "swarm": "combat", "remote": "combat", "laser": "hazards", "tornado": "hazards", "nuke": "hazards",
    "freeze": "hazards", "quake": "hazards", "rift": "hazards", "wind": "hazards", "portal_storm": "combat",
    "remote_detonator": "combat", "omega_event_horizon": "hazards", "judgement_day": "hazards", "tempest_cataclysm": "hazards",
    "card": "ui", "card_special": "ui", "card_fusion": "ui", "freeze_card": "ui", "burn_card": "ui",
}


def build_ambient_sound(freqs, duration=2.4, volume=0.14, noise=0.08):
    sample_rate = 44100
    total = int(sample_rate * duration)
    buf = array("h")
    for i in range(total):
        t = i / sample_rate
        sample = 0.0
        for idx, freq in enumerate(freqs):
            sample += math.sin(math.tau * freq * t + idx * 0.7) * (0.6 / (idx + 1))
        sample += random.uniform(-1.0, 1.0) * noise
        sample *= 0.5 + 0.5 * math.sin(math.tau * 0.14 * t)
        sample = max(-1.0, min(1.0, sample * volume))
        pcm = int(sample * 32767)
        buf.append(pcm)
        buf.append(pcm)
    return pygame.mixer.Sound(buffer=buf.tobytes())


AMBIENT_SOUNDS = {
    "classic": build_ambient_sound([110, 220], volume=0.08),
    "sawmill": build_ambient_sound([92, 138], volume=0.10, noise=0.10),
    "neon": build_ambient_sound([180, 360, 540], volume=0.07),
    "wind": build_ambient_sound([130, 195], volume=0.09, noise=0.14),
    "factory": build_ambient_sound([84, 126, 252], volume=0.10, noise=0.12),
    "volcano": build_ambient_sound([70, 105], volume=0.11, noise=0.12),
    "glacier": build_ambient_sound([210, 315], volume=0.07, noise=0.05),
    "void": build_ambient_sound([66, 99, 198], volume=0.09, noise=0.10),
} if pygame.mixer.get_init() else {}


def apply_sound_volume():
    if pygame.mixer.get_init():
        global AMBIENT_CHANNEL
        if AMBIENT_CHANNEL is None:
            AMBIENT_CHANNEL = pygame.mixer.Channel(23)
    for name, snd in SOUNDS.items():
        category = SOUND_CATEGORY.get(name, "combat")
        snd.set_volume((AUDIO_VOLUMES.get(category, 0.5) if SFX_ENABLED else 0.0))
    for snd in AMBIENT_SOUNDS.values():
        snd.set_volume((AUDIO_VOLUMES.get("hazards", 0.5) * 0.45) if SFX_ENABLED else 0.0)


apply_sound_volume()


def play_sound(name):
    if not SFX_ENABLED:
        return
    snd = SOUNDS.get(name)
    if snd:
        snd.play()


def play_sound_positional(name, x, y, st, base_volume=1.0):
    if not SFX_ENABLED:
        return
    snd = SOUNDS.get(name)
    if not snd or not pygame.mixer.get_init():
        return
    me = get_me(st) if st else None
    if not me:
        snd.play()
        return
    dx = float(x) - float(me.get("x", WIDTH / 2))
    dy = float(y) - float(me.get("y", HEIGHT / 2))
    dist = math.hypot(dx, dy)
    max_dist = math.hypot(WIDTH, HEIGHT) * 0.75
    attenuation = max(0.12, 1.0 - dist / max_dist)
    pan = max(-1.0, min(1.0, dx / (WIDTH * 0.45)))
    category_volume = AUDIO_VOLUMES.get(SOUND_CATEGORY.get(name, "combat"), 0.5)
    left = category_volume * base_volume * attenuation * (1.0 - max(0.0, pan))
    right = category_volume * base_volume * attenuation * (1.0 + min(0.0, pan))
    channel = pygame.mixer.find_channel(True)
    if channel:
        channel.set_volume(max(0.0, min(1.0, left)), max(0.0, min(1.0, right)))
        channel.play(snd)


def update_ambience(st):
    arena_id = ((st or {}).get("arena") or {}).get("id")
    if not pygame.mixer.get_init() or AMBIENT_CHANNEL is None:
        return
    if not SFX_ENABLED or not arena_id:
        AMBIENT_CHANNEL.stop()
        return
    if LAST_AUDIO_STATE.get("arena_id") == arena_id and AMBIENT_CHANNEL.get_busy():
        return
    snd = AMBIENT_SOUNDS.get(arena_id)
    if snd:
        AMBIENT_CHANNEL.play(snd, loops=-1)
    LAST_AUDIO_STATE["arena_id"] = arena_id


def choose_shot_sound(me):
    buffs = (me or {}).get("buffs", {})
    if buffs.get("portal_storm"):
        return "portal_storm"
    if buffs.get("guided_swarm"):
        return "swarm"
    if buffs.get("remote_detonator"):
        return "remote_detonator"
    if buffs.get("railgun_charge") or buffs.get("glass_cannon_tv"):
        return "shoot_rail"
    if buffs.get("buckshot_mayhem"):
        return "shoot_buckshot"
    if buffs.get("homing_rounds") or buffs.get("drone_guidance") or buffs.get("guided_swarm"):
        return "shoot_homing"
    if buffs.get("bluezao") or buffs.get("tsar_bomba"):
        return "shoot_heavy"
    return "shoot"


def play_effect_sound(effect):
    hint = effect.get("sound")
    if hint in SOUNDS:
        return ("positional", hint)
    etype = effect.get("type")
    radius = float(effect.get("radius", 0))
    if etype == "parry_burst":
        return ("positional", "parry")
    if etype == "orbital_laser":
        return ("positional", "laser")
    if etype == "tornado":
        return ("positional", "tornado")
    if etype == "freeze_wave":
        return ("positional", "freeze")
    if etype == "quake":
        return ("positional", "quake")
    if etype == "void_rift":
        return ("positional", "rift")
    if etype == "sky_rain":
        return ("positional", "swarm")
    if etype == "black_hole":
        return ("positional", "nuke" if radius > 300 else "active")
    if etype == "nuke":
        return ("positional", "nuke")
    if etype == "active_flash":
        if effect.get("color") == "ember":
            return ("positional", "remote")
        if effect.get("color") == "toxic":
            return ("positional", "poison")
        return ("positional", "active")
    return None


def update_audio(st):
    if not st:
        return
    update_ambience(st)
    me = get_me(st)
    my_id = st.get("your_id")
    my_bullets = sum(1 for b in st.get("bullets", []) if b.get("owner") == my_id)
    if my_bullets > LAST_AUDIO_STATE["my_bullets"]:
        if me:
            play_sound_positional(choose_shot_sound(me), me.get("x", WIDTH / 2), me.get("y", HEIGHT / 2), st, base_volume=0.85)
        else:
            play_sound(choose_shot_sound(me))
    LAST_AUDIO_STATE["my_bullets"] = my_bullets

    if me:
        hp = float(me.get("hp", 0))
        if LAST_AUDIO_STATE["my_hp"] is not None and hp < LAST_AUDIO_STATE["my_hp"]:
            play_sound("hit_heavy" if LAST_AUDIO_STATE["my_hp"] - hp >= 18 else "hit")
        LAST_AUDIO_STATE["my_hp"] = hp
        chosen = bool(me.get("chosen"))
        if chosen and not LAST_AUDIO_STATE["chosen"]:
            if me.get("last_picked_fusion"):
                play_sound("card_fusion")
            elif me.get("last_picked_special"):
                play_sound("card_special")
            else:
                play_sound("card")
        LAST_AUDIO_STATE["chosen"] = chosen

    phase = st.get("phase")
    if phase == "cards" and LAST_AUDIO_STATE["phase"] != "cards":
        play_sound("card")
    LAST_AUDIO_STATE["phase"] = phase

    current_keys = set()
    for effect in st.get("effects", []):
        key = (effect.get("type"), round(float(effect.get("x", 0)), 1), round(float(effect.get("y", 0)), 1), round(float(effect.get("until", 0)), 2))
        current_keys.add(key)
        if key in SEEN_EFFECTS:
            continue
        sound_event = play_effect_sound(effect)
        if sound_event and sound_event[0] == "positional":
            play_sound_positional(sound_event[1], effect.get("x", WIDTH / 2), effect.get("y", HEIGHT / 2), st)
        SEEN_EFFECTS.add(key)
    stale = [key for key in SEEN_EFFECTS if key not in current_keys]
    for key in stale:
        SEEN_EFFECTS.discard(key)

    hazards = st.get("hazards", [])
    active_hazards = sum(1 for hazard in hazards if hazard.get("active"))
    if active_hazards > LAST_AUDIO_STATE["hazard_count"]:
        if any(h.get("type") == "laser" and h.get("active") for h in hazards):
            hz = next(h for h in hazards if h.get("type") == "laser" and h.get("active"))
            play_sound_positional("laser", hz.get("x", (hz.get("x1", 0) + hz.get("x2", WIDTH)) / 2), hz.get("y", (hz.get("y1", 0) + hz.get("y2", HEIGHT)) / 2), st, base_volume=0.75)
        elif any(h.get("type") == "wind" and h.get("active") for h in hazards):
            hz = next(h for h in hazards if h.get("type") == "wind" and h.get("active"))
            play_sound_positional("wind", hz.get("x", WIDTH / 2) + hz.get("w", 0) / 2, hz.get("y", HEIGHT / 2) + hz.get("h", 0) / 2, st, base_volume=0.65)
        elif any(h.get("type") == "pulse" and h.get("active") for h in hazards):
            hz = next(h for h in hazards if h.get("type") == "pulse" and h.get("active"))
            play_sound_positional("quake", hz.get("x", WIDTH / 2), hz.get("y", HEIGHT / 2), st, base_volume=0.75)
    LAST_AUDIO_STATE["hazard_count"] = active_hazards


def recommend_synergy(card_id, me, st):
    buffs = (me or {}).get("buffs", {})
    recipes = st.get("fusion_recipes", {})
    if card_id in recipes:
        owned = sum(1 for part in recipes[card_id] if buffs.get(part))
        return f"Fusao pronta: {owned}/{len(recipes[card_id])} pecas"
    suggestions = {
        "homing_rounds": [("ricochet_roulette", "com ricochete"), ("drone_guidance", "com guidance"), ("guided_swarm", "para enxame")],
        "ricochet_roulette": [("homing_rounds", "para retarget"), ("bounce_house", "para quique forte")],
        "cluster_pop": [("toxic_payload", "para splash toxico"), ("buckshot_mayhem", "para caos puro")],
        "railgun_charge": [("glass_cannon_tv", "para burst"), ("parasite_rounds", "para perfurar e drenar")],
        "glock_lisa": [("reload_chad", "para spam seguro"), ("one_tap", "mais balas fortes no pente")],
        "reload_chad": [("glock_lisa", "mais valor por pente"), ("buckshot_mayhem", "para ciclo rapido")],
        "one_tap": [("railgun_charge", "ultimo tiro brutal"), ("glass_cannon_tv", "para burst final")],
        "scavenger_hunt": [("buckshot_mayhem", "para roubar municao em snowball"), ("guided_swarm", "para resetar pente em limpeza")],
        "panic_pocket": [("reload_chad", "para recarga-agressao"), ("glock_lisa", "para manter o giro")],
        "golden_mag": [("railgun_charge", "primeira bala devastadora"), ("one_tap", "primeira e ultima bala fortes")],
        "bottomless_meme": [("buckshot_mayhem", "para rajada gratuita"), ("multishot", "para leques gratis")],
        "guided_swarm": [("homing_rounds", "stack de busca"), ("drone_guidance", "mais tracking")],
        "portal_storm": [("remote_detonator", "para detonar tudo"), ("magnet_trigger", "para virar enxame")],
        "ghost_rounds": [("railgun_charge", "para linha reta"), ("boomerang_rounds", "para trajetoria estranha")],
        "buckshot_mayhem": [("cluster_pop", "mais fragmentos"), ("toxic_payload", "mais area")],
    }
    for other, text in suggestions.get(card_id, []):
        if buffs.get(other):
            return f"Sinergia: {text}"
    near_fusions = []
    for result, parts in recipes.items():
        if card_id in parts:
            owned = sum(1 for part in parts if buffs.get(part))
            near_fusions.append((owned, len(parts), result))
    if near_fusions:
        owned, total, result = max(near_fusions)
        if owned >= total - 1:
            return f"Quase funde: {st['card_defs'][result]['name']}"
    return ""


def net_reader():
    global state, connected
    lb = LineBuffer()
    try:
        while connected:
            data = sock.recv(65536)
            if not data:
                break
            for msg in lb.feed(data):
                if msg.get("type") == "state":
                    with state_lock:
                        state = msg
                elif msg.get("type") == "full":
                    print(msg.get("msg", "Sala cheia"))
                    connected = False
                    return
                elif msg.get("type") == "reject":
                    print(msg.get("msg", "Entrada recusada"))
                    connected = False
                    return
    except Exception as e:
        print("Conexão encerrada:", e)
    connected = False

def draw_text(txt, x, y, f=font, color=(235, 235, 235), center=False):
    surf = f.render(str(txt), True, color)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)
    return rect


def draw_button(rect, label, hovered=False, primary=False):
    if primary:
        fill = (245, 184, 70) if hovered else (226, 146, 46)
        text = (28, 24, 20)
        border = (255, 225, 145)
    else:
        fill = (49, 58, 74) if hovered else (37, 43, 56)
        text = (230, 236, 244)
        border = (105, 120, 142)
    pygame.draw.rect(screen, fill, rect, border_radius=8)
    pygame.draw.rect(screen, border, rect, 2, border_radius=8)
    draw_text(label, rect.centerx, rect.centery, font, text, center=True)


def draw_input(rect, label, value, active=False):
    pygame.draw.rect(screen, (21, 25, 34), rect, border_radius=8)
    border = (245, 184, 70) if active else (78, 89, 108)
    pygame.draw.rect(screen, border, rect, 2, border_radius=8)
    draw_text(label, rect.x, rect.y - 24, small, (190, 199, 213))
    shown = value if value else ""
    draw_text(shown, rect.x + 14, rect.y + 13, font, (245, 247, 250))
    if active and int(time.time() * 2) % 2 == 0:
        cursor_x = rect.x + 15 + font.size(shown)[0]
        pygame.draw.line(screen, (245, 225, 150), (cursor_x, rect.y + 12), (cursor_x, rect.y + rect.height - 12), 2)


def draw_panel(rect, title, active=False):
    pygame.draw.rect(screen, (27, 33, 45), rect, border_radius=8)
    border = (235, 172, 70) if active else (66, 79, 99)
    pygame.draw.rect(screen, border, rect, 2, border_radius=8)
    draw_text(title, rect.x + 24, rect.y + 22, font, (246, 232, 195) if active else (216, 224, 235))


def draw_slider(rect, value, label):
    pygame.draw.rect(screen, (21, 25, 34), rect, border_radius=8)
    pygame.draw.rect(screen, (78, 89, 108), rect, 2, border_radius=8)
    fill_w = int((rect.width - 8) * max(0.0, min(1.0, value)))
    pygame.draw.rect(screen, (226, 146, 46), (rect.x + 4, rect.y + 4, fill_w, rect.height - 8), border_radius=6)
    draw_text(f"{label}: {int(value * 100)}%", rect.centerx, rect.centery, small, (240, 244, 250), center=True)


def draw_menu(values, mode, active_field, error_msg="", audio_open=False):
    screen.fill((13, 18, 27))
    for x in range(-100, WIDTH + 100, 92):
        pygame.draw.line(screen, (24, 33, 47), (x, 0), (x + 260, HEIGHT), 2)
    pygame.draw.rect(screen, (33, 46, 63), (0, HEIGHT - 150, WIDTH, 150))
    pygame.draw.rect(screen, (86, 74, 54), (0, HEIGHT - 78, WIDTH, 78))

    pygame.draw.circle(screen, (226, 146, 46), (180, HEIGHT - 120), 54)
    pygame.draw.circle(screen, (67, 163, 124), (1110, 110), 70)
    pygame.draw.circle(screen, (43, 68, 96), (1020, 188), 32)

    draw_text("REDONDOS", WIDTH // 2, 72, big, (255, 226, 158), center=True)
    draw_text("Crie uma sala local ou entre com IP e codigo.", WIDTH // 2, 118, font, (205, 215, 229), center=True)

    create_panel = pygame.Rect(150, 170, 470, 470)
    join_panel = pygame.Rect(660, 170, 470, 430)
    audio_button = pygame.Rect(WIDTH // 2 - 70, 138, 140, 34)
    mouse = pygame.mouse.get_pos()

    draw_panel(create_panel, "Criar sala", mode == "create")
    draw_panel(join_panel, "Entrar na sala", mode == "join")
    draw_button(audio_button, "Audio", audio_button.collidepoint(mouse), audio_open)

    name_rect = pygame.Rect(190, 248, 380, 48)
    create_code_rect = pygame.Rect(190, 338, 220, 48)
    random_rect = pygame.Rect(424, 338, 146, 48)
    infinite_rect = pygame.Rect(190, 418, 380, 42)
    mutators_rect = pygame.Rect(190, 468, 380, 42)
    more_cards_rect = pygame.Rect(190, 518, 380, 42)
    create_rect = pygame.Rect(190, 578, 380, 56)

    join_name_rect = pygame.Rect(700, 242, 380, 48)
    ip_rect = pygame.Rect(700, 332, 380, 48)
    join_code_rect = pygame.Rect(700, 422, 220, 48)
    join_rect = pygame.Rect(700, 512, 180, 52)
    quit_rect = pygame.Rect(900, 512, 180, 52)

    draw_input(name_rect, "Seu nome", values["name"], active_field == "name")
    draw_input(create_code_rect, "Codigo da sala", values["create_code"], active_field == "create_code")
    draw_button(random_rect, "Gerar", random_rect.collidepoint(mouse))
    draw_button(infinite_rect, f"Infinito: {'Ligado' if values['infinite'] else 'Desligado'}", infinite_rect.collidepoint(mouse), values["infinite"])
    draw_button(mutators_rect, f"Mutadores: {'Ligado' if values['mutators'] else 'Desligado'}", mutators_rect.collidepoint(mouse), values["mutators"])
    draw_button(more_cards_rect, f"Mais cartas: {'Ligado' if values['more_cards'] else 'Desligado'}", more_cards_rect.collidepoint(mouse), values["more_cards"])
    draw_text("Servidor local com teste solo. Passe IP e codigo aos amigos.", 190, 556, small, (178, 190, 207))
    draw_button(create_rect, "Criar e entrar", create_rect.collidepoint(mouse), primary=True)

    draw_input(join_name_rect, "Seu nome", values["name"], active_field == "name")
    draw_input(ip_rect, "IP do host", values["join_ip"], active_field == "join_ip")
    draw_input(join_code_rect, "Codigo", values["join_code"], active_field == "join_code")
    draw_button(join_rect, "Entrar", join_rect.collidepoint(mouse), primary=True)
    draw_button(quit_rect, "Sair", quit_rect.collidepoint(mouse))

    audio_panel = None
    audio_rects = {}
    if audio_open:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))
        audio_panel = pygame.Rect(WIDTH // 2 - 250, 190, 500, 320)
        pygame.draw.rect(screen, (24, 31, 43), audio_panel, border_radius=12)
        pygame.draw.rect(screen, (240, 178, 76), audio_panel, 2, border_radius=12)
        draw_text("Audio", audio_panel.centerx, audio_panel.y + 36, font, (255, 226, 158), center=True)
        audio_toggle = pygame.Rect(audio_panel.x + 40, audio_panel.y + 72, 420, 42)
        draw_button(audio_toggle, f"SFX Master: {'Ligado' if values['sfx_enabled'] else 'Desligado'}", audio_toggle.collidepoint(mouse), values["sfx_enabled"])
        ui_slider = pygame.Rect(audio_panel.x + 40, audio_panel.y + 136, 420, 34)
        combat_slider = pygame.Rect(audio_panel.x + 40, audio_panel.y + 192, 420, 34)
        hazard_slider = pygame.Rect(audio_panel.x + 40, audio_panel.y + 248, 420, 34)
        draw_slider(ui_slider, values["audio_ui"], "UI")
        draw_slider(combat_slider, values["audio_combat"], "Combate")
        draw_slider(hazard_slider, values["audio_hazards"], "Hazards")
        audio_rects = {"audio_toggle": audio_toggle, "audio_ui": ui_slider, "audio_combat": combat_slider, "audio_hazards": hazard_slider}

    if error_msg:
        draw_text(error_msg, WIDTH // 2, 640, small, (255, 130, 118), center=True)
    return {
        "name": name_rect,
        "create_code": create_code_rect,
        "random": random_rect,
        "infinite": infinite_rect,
        "mutators": mutators_rect,
        "more_cards": more_cards_rect,
        "create": create_rect,
        "audio_button": audio_button,
        "audio_panel": audio_panel,
        "join_name": join_name_rect,
        "join_ip": ip_rect,
        "join_code": join_code_rect,
        "join": join_rect,
        "quit": quit_rect,
        "create_panel": create_panel,
        "join_panel": join_panel,
        **audio_rects,
    }


def generate_room_code():
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(alphabet) for _ in range(5))


def sanitize_room_code(value):
    filtered = "".join(ch for ch in str(value).upper() if ch.isalnum())
    return filtered[:8]


def start_local_server(room_code, infinite_mode=False, mutators_enabled=False, more_cards_enabled=False):
    global local_server, local_server_config, local_server_owned
    room_code = sanitize_room_code(room_code) or generate_room_code()
    requested = {
        "room_code": room_code,
        "allow_solo": True,
        "infinite": bool(infinite_mode),
        "mutators": bool(mutators_enabled),
        "more_cards": bool(more_cards_enabled),
    }
    if local_server and local_server.poll() is None:
        if local_server_config == requested:
            return ""
        stop_local_server()
    else:
        stop_orphan_local_servers()

    cmd, launch_cwd = resolve_server_launcher()
    cmd = list(cmd) + ["--room-code", room_code, "--allow-solo"]
    if infinite_mode:
        cmd.append("--infinite")
    if mutators_enabled:
        cmd.append("--mutators")
    if more_cards_enabled:
        cmd.append("--more-cards")
    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = subprocess.CREATE_NO_WINDOW
    try:
        local_server = subprocess.Popen(
            cmd,
            cwd=launch_cwd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            startupinfo=startupinfo,
            creationflags=creationflags,
        )
        time.sleep(0.6)
        if local_server.poll() is not None:
            local_server = None
            local_server_config = None
            local_server_owned = False
            clear_local_server_pid()
            return "Nao foi possivel iniciar o servidor. A porta 50007 pode estar em uso."
        local_server_config = requested
        local_server_owned = True
        write_local_server_pid(local_server.pid)
        return ""
    except Exception as e:
        local_server = None
        local_server_config = None
        local_server_owned = False
        clear_local_server_pid()
        return f"Nao foi possivel iniciar o servidor ({e})"


def stop_local_server():
    global local_server, local_server_config, local_server_owned
    if local_server and local_server.poll() is None:
        local_server.terminate()
        try:
            local_server.wait(timeout=1)
        except Exception:
            local_server.kill()
    local_server = None
    local_server_config = None
    local_server_owned = False
    clear_local_server_pid()


def stop_orphan_local_servers():
    tracked_pid = read_local_server_pid()
    current_pid = local_server.pid if local_server and local_server.poll() is None else None
    targets = set()
    if tracked_pid and tracked_pid != current_pid:
        targets.add(tracked_pid)
    if os.name == "nt":
        cmd = (
            "Get-CimInstance Win32_Process | "
            "Where-Object { (($_.Name -match 'python' -and $_.CommandLine -match 'server.py') -or $_.Name -match 'REDONDOS_Server.exe|server.exe') } | "
            "ForEach-Object { $_.ProcessId }"
        )
        try:
            output = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", cmd],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            for line in output.splitlines():
                line = line.strip()
                if line.isdigit():
                    pid = int(line)
                    if pid != current_pid:
                        targets.add(pid)
        except Exception:
            pass
    for pid in sorted(targets):
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            else:
                os.kill(pid, 15)
        except Exception:
            pass
    if targets:
        clear_local_server_pid()


def close_connection(stop_host=False):
    global sock, connected, state, SEEN_EFFECTS, LAST_AUDIO_STATE
    connected = False
    with state_lock:
        state = None
    SEEN_EFFECTS = set()
    LAST_AUDIO_STATE = {"my_bullets": 0, "my_hp": None, "phase": None, "chosen": False, "hazard_count": 0, "arena_id": None}
    if AMBIENT_CHANNEL:
        AMBIENT_CHANNEL.stop()
    try:
        if sock:
            sock.close()
    except Exception:
        pass
    sock = None
    if stop_host and local_server_owned:
        stop_local_server()


def start_connection(server_ip, player_name, room_code):
    global sock, connected, state, SERVER_IP, NAME, ROOM_CODE
    SERVER_IP = server_ip.strip() or "127.0.0.1"
    NAME = player_name.strip() or "Player"
    ROOM_CODE = sanitize_room_code(room_code)
    with state_lock:
        state = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((SERVER_IP, PORT))
        send_json(sock, {"type": "hello", "name": NAME, "code": ROOM_CODE})
        sock.settimeout(3.0)
        lb = LineBuffer()
        initial_state = None
        try:
            deadline = time.time() + 3.0
            while time.time() < deadline:
                data = sock.recv(65536)
                if not data:
                    break
                for msg in lb.feed(data):
                    if msg.get("type") in ("reject", "full"):
                        sock.close()
                        sock = None
                        return msg.get("msg", "Entrada recusada")
                    if msg.get("type") == "state":
                        initial_state = msg
                        break
                if initial_state:
                    break
        except socket.timeout:
            pass
        if not initial_state:
            sock.close()
            sock = None
            return f"Nao foi possivel entrar na sala {ROOM_CODE or '(sem codigo)'}. O servidor nao respondeu com o estado inicial."
        with state_lock:
            state = initial_state
        sock.settimeout(None)
        connected = True
        threading.Thread(target=net_reader, daemon=True).start()
        return ""
    except Exception as e:
        connected = False
        try:
            if sock:
                sock.close()
        except Exception:
            pass
        sock = None
        return f"Nao foi possivel conectar em {SERVER_IP}:{PORT} ({e})"


def connect_local_room(player_name, room_code, attempts=8, delay=0.35):
    last_error = ""
    for _ in range(attempts):
        last_error = start_connection("127.0.0.1", player_name, room_code)
        if not last_error or "Nao foi possivel conectar" not in last_error:
            return last_error
        time.sleep(delay)
    return last_error


def host_local_room(player_name, room_code, infinite_mode=False, mutators_enabled=False, more_cards_enabled=False):
    global local_server
    room_code = sanitize_room_code(room_code) or generate_room_code()
    error = start_local_server(room_code, infinite_mode, mutators_enabled, more_cards_enabled)
    if error:
        return room_code, error
    error = connect_local_room(player_name, room_code)
    if error == "Codigo da sala invalido":
        if local_server and local_server.poll() is None:
            stop_local_server()
            error = start_local_server(room_code, infinite_mode, mutators_enabled, more_cards_enabled)
            if error:
                return room_code, error
            error = connect_local_room(player_name, room_code)
        else:
            error = "Ja existe outro servidor em 127.0.0.1:50007 com outro codigo. Feche-o antes de criar uma nova sala."
    return room_code, error


def run_menu():
    global SFX_ENABLED, AUDIO_VOLUMES
    values = {
        "name": NAME,
        "join_ip": SERVER_IP,
        "join_code": ROOM_CODE,
        "create_code": ROOM_CODE or generate_room_code(),
        "infinite": True,
        "mutators": True,
        "more_cards": False,
        "sfx_enabled": SFX_ENABLED,
        "audio_ui": AUDIO_VOLUMES["ui"],
        "audio_combat": AUDIO_VOLUMES["combat"],
        "audio_hazards": AUDIO_VOLUMES["hazards"],
    }
    mode = "create"
    audio_open = False
    active_field = "name"
    error_msg = ""
    fields = ["name", "create_code", "join_ip", "join_code"]

    while True:
        clock.tick(FPS)
        rects = draw_menu(values, mode, active_field, error_msg, audio_open)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if rects["audio_button"].collidepoint(event.pos):
                    audio_open = not audio_open
                    continue
                if audio_open:
                    if not (rects.get("audio_panel") and rects["audio_panel"].collidepoint(event.pos)):
                        audio_open = False
                        continue
                    if rects.get("audio_toggle") and rects["audio_toggle"].collidepoint(event.pos):
                        values["sfx_enabled"] = not values["sfx_enabled"]
                        SFX_ENABLED = values["sfx_enabled"]
                        apply_sound_volume()
                        save_client_config()
                        play_sound("card")
                        continue
                    if rects.get("audio_ui") and rects["audio_ui"].collidepoint(event.pos):
                        values["audio_ui"] = max(0.0, min(1.0, (event.pos[0] - rects["audio_ui"].x) / rects["audio_ui"].width))
                        AUDIO_VOLUMES["ui"] = values["audio_ui"]
                        apply_sound_volume()
                        save_client_config()
                        play_sound("card")
                        continue
                    if rects.get("audio_combat") and rects["audio_combat"].collidepoint(event.pos):
                        values["audio_combat"] = max(0.0, min(1.0, (event.pos[0] - rects["audio_combat"].x) / rects["audio_combat"].width))
                        AUDIO_VOLUMES["combat"] = values["audio_combat"]
                        apply_sound_volume()
                        save_client_config()
                        play_sound("active")
                        continue
                    if rects.get("audio_hazards") and rects["audio_hazards"].collidepoint(event.pos):
                        values["audio_hazards"] = max(0.0, min(1.0, (event.pos[0] - rects["audio_hazards"].x) / rects["audio_hazards"].width))
                        AUDIO_VOLUMES["hazards"] = values["audio_hazards"]
                        apply_sound_volume()
                        save_client_config()
                        play_sound("quake")
                        continue
                    continue
                if rects["create_panel"].collidepoint(event.pos):
                    mode = "create"
                elif rects["join_panel"].collidepoint(event.pos):
                    mode = "join"
                if rects["name"].collidepoint(event.pos) or rects["join_name"].collidepoint(event.pos):
                    active_field = "name"
                elif rects["create_code"].collidepoint(event.pos):
                    active_field = "create_code"
                elif rects["join_ip"].collidepoint(event.pos):
                    active_field = "join_ip"
                elif rects["join_code"].collidepoint(event.pos):
                    active_field = "join_code"
                elif rects["random"].collidepoint(event.pos):
                    values["create_code"] = generate_room_code()
                    active_field = "create_code"
                elif rects["infinite"].collidepoint(event.pos):
                    values["infinite"] = not values["infinite"]
                elif rects["mutators"].collidepoint(event.pos):
                    values["mutators"] = not values["mutators"]
                elif rects["more_cards"].collidepoint(event.pos):
                    values["more_cards"] = not values["more_cards"]
                elif rects["create"].collidepoint(event.pos):
                    audio_open = False
                    values["create_code"], error_msg = host_local_room(values["name"], values["create_code"], values["infinite"], values["mutators"], values["more_cards"])
                    if not error_msg:
                        return True
                elif rects["join"].collidepoint(event.pos):
                    audio_open = False
                    values["join_code"] = sanitize_room_code(values["join_code"])
                    error_msg = start_connection(values["join_ip"], values["name"], values["join_code"])
                    if not error_msg:
                        return True
                elif rects["quit"].collidepoint(event.pos):
                    return False
            elif event.type == pygame.KEYDOWN:
                if audio_open:
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        audio_open = False
                    continue
                if event.key == pygame.K_TAB:
                    idx = fields.index(active_field) if active_field in fields else 0
                    active_field = fields[(idx + 1) % len(fields)]
                elif event.key == pygame.K_RETURN:
                    if mode == "create":
                        audio_open = False
                        values["create_code"], error_msg = host_local_room(values["name"], values["create_code"], values["infinite"], values["mutators"], values["more_cards"])
                    else:
                        audio_open = False
                        values["join_code"] = sanitize_room_code(values["join_code"])
                        error_msg = start_connection(values["join_ip"], values["name"], values["join_code"])
                    if not error_msg:
                        return True
                elif event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_BACKSPACE:
                    if active_field in values:
                        values[active_field] = values[active_field][:-1]
                elif event.unicode and event.unicode.isprintable():
                    if active_field == "name" and len(values["name"]) < 18:
                        values["name"] += event.unicode
                    elif active_field == "join_ip" and len(values["join_ip"]) < 32:
                        values["join_ip"] += event.unicode
                    elif active_field in ("join_code", "create_code") and len(values[active_field]) < 8:
                        values[active_field] += event.unicode.upper()


def draw_bar(x, y, w, h, value, max_value):
    pygame.draw.rect(screen, (24, 29, 39), (x, y, w, h), border_radius=4)
    ratio = 0 if max_value <= 0 else max(0, min(1, value / max_value))
    fill = (220, 66, 75) if ratio < 0.35 else (72, 204, 132)
    pygame.draw.rect(screen, fill, (x, y, int(w * ratio), h), border_radius=4)
    pygame.draw.rect(screen, (230, 235, 242), (x, y, w, h), 1, border_radius=4)


def draw_game_background(st=None):
    colors = (st or {}).get("arena", {}).get("colors", {})
    top = tuple(colors.get("sky_top", (12, 17, 26)))
    bottom = tuple(colors.get("sky_bottom", (44, 66, 82)))
    accent = tuple(colors.get("accent", (92, 73, 45)))
    screen.fill(top)
    for y in range(HEIGHT):
        blend = y / max(1, HEIGHT - 1)
        color = (
            int(top[0] + (bottom[0] - top[0]) * blend),
            int(top[1] + (bottom[1] - top[1]) * blend),
            int(top[2] + (bottom[2] - top[2]) * blend),
        )
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))
    for x in range(-160, WIDTH + 160, 120):
        pygame.draw.line(screen, (28, 43, 61), (x, 0), (x + 260, HEIGHT), 2)
    for y in range(80, HEIGHT, 80):
        pygame.draw.line(screen, (21, 31, 45), (0, y), (WIDTH, y), 1)
    pygame.draw.circle(screen, (56, 86, 104), (170, 135), 72)
    pygame.draw.circle(screen, accent, (1120, 590), 140)


def draw_hud_panel(rect):
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    panel.fill((15, 20, 30, 205))
    screen.blit(panel, rect.topleft)
    pygame.draw.rect(screen, (82, 99, 122), rect, 2, border_radius=8)


def card_initials(name):
    words = [part for part in str(name).replace("-", " ").split() if part]
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()
    if words:
        token = words[0][:2]
        return token.upper()
    return "??"


def draw_tooltip(lines, anchor_x, anchor_y):
    text_lines = [str(line) for line in lines if line]
    if not text_lines:
        return
    widths = [small.size(line)[0] for line in text_lines]
    box_w = max(widths) + 18
    box_h = 10 + len(text_lines) * 18
    x = min(WIDTH - box_w - 12, anchor_x + 16)
    y = max(12, min(HEIGHT - box_h - 12, anchor_y + 16))
    panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    panel.fill((12, 15, 22, 228))
    screen.blit(panel, (x, y))
    pygame.draw.rect(screen, (245, 184, 70), (x, y, box_w, box_h), 2, border_radius=8)
    for idx, line in enumerate(text_lines):
        draw_text(line, x + 9, y + 6 + idx * 18, small, (238, 242, 248))


def draw_ammo_pips(player):
    max_ammo = max(1, int(player.get("max_ammo", 3)))
    ammo = max(0, min(max_ammo, int(player.get("ammo", max_ammo))))
    aim = float(player.get("aim", 0.0))
    base_x = float(player.get("x")) + math.cos(aim) * 28
    base_y = float(player.get("y")) + math.sin(aim) * 28
    perp_x = -math.sin(aim)
    perp_y = math.cos(aim)
    radius = max(2, int(6 - 0.45 * max(0, max_ammo - 3)))
    spacing = radius * 2 + 2
    total_width = max_ammo * spacing - 2
    start = -total_width / 2
    reloading = time.time() < float(player.get("reload_until", 0))
    reload_progress = 0.0
    if reloading:
        started = float(player.get("reload_started_at", 0))
        ends = float(player.get("reload_until", 0))
        if ends > started:
            reload_progress = max(0.0, min(1.0, 1.0 - ((ends - time.time()) / (ends - started))))
    fill_color = (245, 229, 177) if not reloading else (255, 196, 120)
    empty_color = (62, 72, 86)
    border_color = (22, 28, 36)
    for idx in range(max_ammo):
        offset = start + idx * spacing
        cx = int(base_x + perp_x * 14 + math.cos(aim) * offset)
        cy = int(base_y + perp_y * 14 + math.sin(aim) * offset)
        color = fill_color if idx < ammo else empty_color
        pygame.draw.circle(screen, border_color, (cx, cy), radius + 2)
        pygame.draw.circle(screen, color, (cx, cy), radius)
        if reloading and idx >= ammo:
            pygame.draw.circle(screen, (255, 238, 170), (cx, cy), max(1, radius - 2), 1)
            if idx / max(1, max_ammo) < reload_progress:
                pygame.draw.circle(screen, (255, 244, 196), (cx, cy), max(1, radius - 3))
    if reloading:
        arc_rect = pygame.Rect(int(base_x - 14), int(base_y - 14), 28, 28)
        pygame.draw.arc(screen, (255, 220, 140), arc_rect, -math.pi / 2, -math.pi / 2 + math.tau * reload_progress, 3)


def draw_card_badges(st, me):
    buffs = (me or {}).get("buffs", {})
    if not buffs:
        return
    items = []
    for key, amount in sorted(buffs.items(), key=lambda item: st.get("card_defs", {}).get(item[0], {}).get("name", item[0])):
        info = st.get("card_defs", {}).get(key, {})
        items.append((key, info.get("name", key), info.get("desc", ""), int(amount)))
    cols = 6
    size = 30
    gap = 6
    rows = (len(items) + cols - 1) // cols
    panel = pygame.Rect(14, 96, cols * size + (cols - 1) * gap + 20, rows * size + (rows - 1) * gap + 20)
    draw_hud_panel(panel)
    draw_text("Cartas", panel.x + 12, panel.y + 8, small, (178, 190, 207))
    mouse = pygame.mouse.get_pos()
    hovered = None
    for idx, (key, name, desc, amount) in enumerate(items):
        info = st.get("card_defs", {}).get(key, {})
        is_fusion = bool(info.get("fusion_only"))
        is_special = bool(info.get("special"))
        is_active = str(desc).startswith("ATIVA:")
        col = idx % cols
        row = idx // cols
        x = panel.x + 10 + col * (size + gap)
        y = panel.y + 28 + row * (size + gap)
        rect = pygame.Rect(x, y, size, size)
        is_hover = rect.collidepoint(mouse)
        base_fill = (36, 43, 58)
        base_border = (98, 110, 132)
        text_color = (236, 240, 246)
        if is_fusion:
            base_fill = (70, 42, 38)
            base_border = (255, 166, 120)
        elif is_special:
            base_fill = (68, 56, 30)
            base_border = (255, 206, 120)
        elif is_active:
            base_fill = (32, 58, 58)
            base_border = (120, 232, 255)
        else:
            base_fill = (40, 48, 66)
            base_border = (150, 176, 215)
        fill = (245, 184, 70) if is_hover else base_fill
        border = (255, 226, 158) if is_hover else base_border
        pygame.draw.rect(screen, fill, rect, border_radius=6)
        pygame.draw.rect(screen, border, rect, 2, border_radius=6)
        draw_text(card_initials(name), rect.centerx, rect.centery - 1, small, (18, 22, 28) if is_hover else text_color, center=True)
        if amount > 1:
            pygame.draw.circle(screen, (86, 214, 156), (rect.right - 6, rect.bottom - 6), 8)
            draw_text(str(amount), rect.right - 6, rect.bottom - 12, small, (16, 22, 24), center=True)
        if is_hover:
            tag = "Fusao" if is_fusion else ("Especial" if is_special else ("Ativa" if is_active else "Passiva"))
            hovered = (name, desc, amount, tag)
    if hovered:
        name, desc, amount, tag = hovered
        draw_tooltip([f"{name} x{amount}", tag, desc], mouse[0], mouse[1])


def draw_hazard(hazard):
    if hazard.get("type") == "saw":
        pos = (int(hazard["x"]), int(hazard["y"]))
        radius = int(hazard.get("radius", 18))
        pygame.draw.circle(screen, (60, 60, 65), pos, radius + 5)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            inner = (int(pos[0] + math.cos(rad) * (radius - 4)), int(pos[1] + math.sin(rad) * (radius - 4)))
            outer = (int(pos[0] + math.cos(rad) * (radius + 7)), int(pos[1] + math.sin(rad) * (radius + 7)))
            pygame.draw.line(screen, (225, 225, 225), inner, outer, 3)
        pygame.draw.circle(screen, (200, 120, 84), pos, radius, 2)
    elif hazard.get("type") == "laser":
        if not hazard.get("active"):
            return
        color = (255, 92, 92) if hazard.get("axis") == "horizontal" else (84, 244, 255)
        thickness = int(hazard.get("thickness", 10) * 2)
        if hazard.get("axis") == "vertical":
            pygame.draw.line(screen, color, (int(hazard["x"]), int(hazard["y1"])), (int(hazard["x"]), int(hazard["y2"])), thickness)
        else:
            pygame.draw.line(screen, color, (int(hazard["x1"]), int(hazard["y"])), (int(hazard["x2"]), int(hazard["y"])), thickness)
    elif hazard.get("type") == "wind":
        if not hazard.get("active"):
            return
        rect = pygame.Rect(int(hazard["x"]), int(hazard["y"]), int(hazard["w"]), int(hazard["h"]))
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((140, 220, 170, 45))
        screen.blit(overlay, rect.topleft)
        for i in range(4):
            yy = rect.y + 18 + i * max(20, rect.height // 5)
            pygame.draw.arc(screen, (190, 255, 220), (rect.x + 14, yy, rect.width - 28, 26), 0.2, 2.9, 2)
    elif hazard.get("type") == "pulse":
        if not hazard.get("active"):
            return
        pygame.draw.circle(screen, (255, 220, 120), (int(hazard["x"]), int(hazard["y"])), int(hazard["radius"]), 2)
        pygame.draw.circle(screen, (255, 245, 190), (int(hazard["x"]), int(hazard["y"])), 24)


def draw_effect(effect):
    now = time.time()
    ttl = max(0.01, float(effect.get("until", now)) - now)
    pulse = 0.5 + 0.5 * math.sin(now * 10)
    etype = effect.get("type")
    x = int(effect.get("x", 0))
    y = int(effect.get("y", 0))
    radius = int(effect.get("radius", 120))
    if etype in ("nuke", "active_flash", "freeze_wave", "quake", "parry_burst", "void_rift"):
        color_map = {
            "nuke": (255, 180, 110, 70),
            "active_flash": (255, 255, 255, 55),
            "freeze_wave": (150, 235, 255, 60),
            "quake": (220, 180, 120, 50),
            "parry_burst": (255, 235, 150, 65),
            "void_rift": (180, 120, 255, 55),
        }
        col = color_map.get(etype, (255, 255, 255, 45))
        surf = pygame.Surface((radius * 2 + 40, radius * 2 + 40), pygame.SRCALPHA)
        center = (surf.get_width() // 2, surf.get_height() // 2)
        pygame.draw.circle(surf, col, center, int(radius * (0.75 + pulse * 0.25)))
        pygame.draw.circle(surf, col[:3] + (min(200, col[3] + 30),), center, int(radius * 0.45), 4)
        screen.blit(surf, (x - center[0], y - center[1]))
    elif etype == "black_hole":
        surf = pygame.Surface((radius * 2 + 60, radius * 2 + 60), pygame.SRCALPHA)
        center = (surf.get_width() // 2, surf.get_height() // 2)
        pygame.draw.circle(surf, (22, 10, 40, 160), center, int(radius * 0.26))
        pygame.draw.circle(surf, (125, 80, 240, 55), center, int(radius * (0.55 + 0.15 * pulse)), 6)
        pygame.draw.circle(surf, (210, 180, 255, 35), center, int(radius * (0.85 + 0.08 * pulse)), 3)
        screen.blit(surf, (x - center[0], y - center[1]))
    elif etype == "tornado":
        for i in range(6):
            rr = 34 + i * 22
            rect = pygame.Rect(x - rr, y - radius // 2 + i * 18, rr * 2, 30)
            pygame.draw.arc(screen, (205, 240, 255), rect, 0.2, 3.4, 2)
    elif etype == "orbital_laser":
        angle = float(effect.get("angle", 0.0))
        thickness = int(effect.get("thickness", 40))
        end = (int(x + math.cos(angle) * 1600), int(y + math.sin(angle) * 1600))
        pygame.draw.line(screen, (255, 248, 210), (x, y), end, thickness + 10)
        pygame.draw.line(screen, (120, 240, 255), (x, y), end, thickness)
    elif etype == "sky_rain":
        for i in range(18):
            xx = int((i + 0.5) * WIDTH / 18)
            pygame.draw.line(screen, (255, 170, 120), (xx, 0), (xx - 18, 120), 2)


def get_me(st):
    for p in st.get("players", []):
        if p["id"] == st.get("your_id"):
            return p
    return None


def summarize_build(me):
    buffs = (me or {}).get("buffs", {})

    def score(keys):
        return sum(int(buffs.get(key, 0)) for key in keys)

    def label(value):
        if value >= 8:
            return "Insano"
        if value >= 5:
            return "Alto"
        if value >= 3:
            return "Medio"
        if value >= 1:
            return "Baixo"
        return "Base"

    shooting = score([
        "damage", "firerate", "multishot", "bullet_speed", "big_bullets", "railgun_charge",
        "homing_rounds", "ricochet_roulette", "cluster_pop", "drone_guidance", "guided_swarm",
        "buckshot_mayhem", "ghost_rounds", "parasite_rounds", "bounce_house", "glass_cannon_tv",
    ])
    parry = score([
        "uno_reverse", "no_u", "omae_wa", "mans_not_hot", "call_an_ambulance",
        "spiderman_pointing", "is_this_pigeon", "bonk", "reverse_overdrive", "final_notice",
    ])
    mobility = score([
        "speed", "jump", "air_jump", "bora_bill", "descer_bc", "gangnam_style", "dat_boi",
        "ugandan_knuckles", "ultra_instinct", "leeroy_jenkins", "modo_turbo", "among_us", "john_cena",
    ])
    chaos = score([
        "tsar_bomba", "mini_black_hole", "brainrot_tornado", "meteor_swarm", "orbital_laser",
        "world_freeze", "void_rift", "apocalypse_rain", "supernova", "quake_slam", "remote_detonator",
        "magnet_trigger", "portal_storm", "omega_event_horizon", "judgement_day", "tempest_cataclysm",
        "this_is_fine", "salt_bae", "harlem_shake", "all_your_base", "area_51",
    ])
    return {
        "Tiro": label(shooting),
        "Parry": label(parry),
        "Mobilidade": label(mobility),
        "Caos": label(chaos),
    }


def send_input(st):
    keys = pygame.key.get_pressed()
    me = get_me(st) if st else None
    mx, my = pygame.mouse.get_pos()
    left_pressed = pygame.mouse.get_pressed()[0]
    parry_click = bool(st and PARRY_BUTTON_RECT.collidepoint(mx, my) and left_pressed)
    aim = 0.0
    if me:
        aim = math.atan2(my - me["y"], mx - me["x"])
    payload = {
        "type": "input",
        "left": keys[pygame.K_a] or keys[pygame.K_LEFT],
        "right": keys[pygame.K_d] or keys[pygame.K_RIGHT],
        "jump": keys[pygame.K_w] or keys[pygame.K_SPACE] or keys[pygame.K_UP],
        "shoot": left_pressed and not parry_click,
        "active": keys[pygame.K_e] or pygame.mouse.get_pressed()[2],
        "parry": keys[pygame.K_q] or parry_click,
        "reload": keys[pygame.K_r],
        "aim": aim,
    }
    try:
        send_json(sock, payload)
    except Exception:
        pass


def send_neutral_input():
    try:
        send_json(sock, {"type": "input", "left": False, "right": False, "jump": False, "shoot": False, "active": False, "parry": False, "reload": False, "aim": 0.0})
    except Exception:
        pass


def send_start_game():
    try:
        send_json(sock, {"type": "start_game"})
        play_sound("card")
    except Exception:
        pass


def draw_lobby(st):
    screen.fill((13, 18, 27))
    for x in range(-100, WIDTH + 100, 92):
        pygame.draw.line(screen, (24, 33, 47), (x, 0), (x + 260, HEIGHT), 2)
    pygame.draw.rect(screen, (33, 46, 63), (0, HEIGHT - 150, WIDTH, 150))
    pygame.draw.rect(screen, (86, 74, 54), (0, HEIGHT - 78, WIDTH, 78))
    pygame.draw.circle(screen, (226, 146, 46), (180, HEIGHT - 120), 54)
    pygame.draw.circle(screen, (67, 163, 124), (1110, 110), 70)
    pygame.draw.circle(screen, (43, 68, 96), (1020, 188), 32)

    panel = pygame.Rect(WIDTH // 2 - 420, 120, 840, 520)
    pygame.draw.rect(screen, (24, 31, 43), panel, border_radius=14)
    pygame.draw.rect(screen, (240, 178, 76), panel, 2, border_radius=14)

    my_id = st.get("your_id")
    host_id = st.get("host_id")
    is_host = my_id == host_id
    can_start = st.get("can_start", False)
    room_code = st.get("room_code", ROOM_CODE)
    required_players = max(1, int(st.get("required_players", 2)))

    draw_text("Lobby da sala", panel.centerx, panel.y + 42, big, (255, 226, 158), center=True)
    draw_text(f"Codigo: {room_code}", panel.centerx, panel.y + 82, font, (205, 215, 229), center=True)
    players = sorted(st.get("players", []), key=lambda p: p["id"])
    needed = max(0, required_players - len(players))
    if can_start:
        subtitle = "Todos conectados. O host decide quando iniciar."
    elif needed > 0:
        subtitle = f"Aguardando mais {needed} jogador(es) para liberar o inicio."
    else:
        subtitle = "Aguardando jogadores para liberar o inicio."
    draw_text(subtitle, panel.centerx, panel.y + 116, small, (178, 190, 207), center=True)

    list_panel = pygame.Rect(panel.x + 42, panel.y + 150, panel.width - 84, 250)
    pygame.draw.rect(screen, (18, 24, 34), list_panel, border_radius=12)
    pygame.draw.rect(screen, (84, 98, 118), list_panel, 2, border_radius=12)
    draw_text("Jogadores conectados", list_panel.x + 22, list_panel.y + 18, font, (240, 244, 250))

    for index, player in enumerate(players):
        row = pygame.Rect(list_panel.x + 18, list_panel.y + 56 + index * 46, list_panel.width - 36, 36)
        pygame.draw.rect(screen, (31, 38, 51), row, border_radius=8)
        marker = "HOST" if player["id"] == host_id else f"P{player['id'] + 1}"
        color = tuple(player.get("color", (230, 230, 230)))
        draw_text(marker, row.x + 12, row.y + 8, small, (255, 226, 158) if player["id"] == host_id else (170, 184, 202))
        draw_text(player["name"], row.x + 84, row.y + 7, font, color)
        draw_text(f"{player['wins']}v", row.right - 54, row.y + 8, small, (205, 215, 229), center=True)

    status_panel = pygame.Rect(panel.x + 42, panel.y + 424, panel.width - 84, 72)
    pygame.draw.rect(screen, (18, 24, 34), status_panel, border_radius=12)
    pygame.draw.rect(screen, (84, 98, 118), status_panel, 2, border_radius=12)
    if is_host:
        status_text = "Voce e o host desta sala."
    elif host_id is not None:
        host_name = next((p["name"] for p in players if p["id"] == host_id), "Host")
        status_text = f"Aguardando {host_name} iniciar a partida."
    else:
        status_text = "Aguardando definicao do host."
    draw_text(status_text, status_panel.x + 22, status_panel.y + 14, font, (240, 244, 250))
    draw_text("Quando a partida iniciar, todos entram juntos na arena.", status_panel.x + 22, status_panel.y + 40, small, (178, 190, 207))

    start_rect = pygame.Rect(panel.centerx - 170, panel.y + 448, 340, 56)
    leave_rect = pygame.Rect(panel.centerx - 170, panel.y + 520, 340, 48)
    hovered = pygame.mouse.get_pos()
    if is_host:
        draw_button(start_rect, "Iniciar partida", start_rect.collidepoint(hovered), primary=can_start)
    else:
        draw_button(start_rect, "Somente o host inicia", start_rect.collidepoint(hovered))
    draw_button(leave_rect, "Voltar ao menu", leave_rect.collidepoint(hovered))
    return {"start": start_rect, "leave": leave_rect, "is_host": is_host, "can_start": can_start}


def draw_pause_menu():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((4, 7, 12, 185))
    screen.blit(overlay, (0, 0))

    panel = pygame.Rect(WIDTH // 2 - 210, HEIGHT // 2 - 170, 420, 340)
    pygame.draw.rect(screen, (24, 31, 43), panel, border_radius=10)
    pygame.draw.rect(screen, (240, 178, 76), panel, 2, border_radius=10)
    draw_text("Menu da partida", panel.centerx, panel.y + 48, big, (255, 226, 158), center=True)

    mouse = pygame.mouse.get_pos()
    resume = pygame.Rect(panel.x + 60, panel.y + 110, 300, 54)
    leave = pygame.Rect(panel.x + 60, panel.y + 180, 300, 54)
    quit_game = pygame.Rect(panel.x + 60, panel.y + 250, 300, 54)
    draw_button(resume, "Continuar", resume.collidepoint(mouse), primary=True)
    draw_button(leave, "Sair da partida", leave.collidepoint(mouse))
    draw_button(quit_game, "Sair do jogo", quit_game.collidepoint(mouse))
    return {"resume": resume, "leave": leave, "quit": quit_game}


def draw_game(st):
    draw_game_background(st)

    for rect in st.get("platforms", []):
        r = pygame.Rect(rect)
        pygame.draw.rect(screen, (13, 16, 23), r.move(0, 7), border_radius=7)
        pygame.draw.rect(screen, (79, 91, 105), r, border_radius=7)
        pygame.draw.rect(screen, (132, 151, 162), (r.x, r.y, r.w, 7), border_radius=7)
        pygame.draw.rect(screen, (34, 42, 52), r, 2, border_radius=7)

    for hazard in st.get("hazards", []):
        draw_hazard(hazard)

    for effect in st.get("effects", []):
        draw_effect(effect)

    for b in st.get("bullets", []):
        radius = int(b.get("radius", BULLET_RADIUS))
        pos = (int(b["x"]), int(b["y"]))
        owner = next((p for p in st.get("players", []) if p["id"] == b.get("owner")), None)
        glow = tuple(owner.get("color", (255, 224, 128))) if owner else (255, 224, 128)
        pygame.draw.circle(screen, glow, pos, radius + 6)
        pygame.draw.circle(screen, (255, 221, 98), pos, radius + 3)
        pygame.draw.circle(screen, glow, pos, radius)
        pygame.draw.circle(screen, (255, 250, 210), pos, max(2, radius // 2))

    for p in st.get("players", []):
        color = tuple(p.get("color", (200, 200, 200)))
        pos = (int(p["x"]), int(p["y"]))
        if p["alive"]:
            pygame.draw.circle(screen, (9, 12, 18), (pos[0], pos[1] + 5), PLAYER_RADIUS + 6)
            pygame.draw.circle(screen, color, pos, PLAYER_RADIUS + 8, 2)
            pygame.draw.circle(screen, (240, 245, 250), pos, PLAYER_RADIUS + 4)
            pygame.draw.circle(screen, color, pos, PLAYER_RADIUS)
            if time.time() < float(p.get("parry_until", 0)):
                pygame.draw.circle(screen, (255, 228, 140), pos, PLAYER_RADIUS + 12, 3)
                pygame.draw.circle(screen, (255, 248, 210), pos, PLAYER_RADIUS + 18, 2)
            end = (int(p["x"] + math.cos(p["aim"]) * 34), int(p["y"] + math.sin(p["aim"]) * 34))
            pygame.draw.line(screen, (18, 22, 30), pos, end, 8)
            pygame.draw.line(screen, (245, 245, 245), pos, end, 4)
            draw_ammo_pips(p)
        else:
            pygame.draw.circle(screen, (80, 80, 88), pos, PLAYER_RADIUS)
            draw_text("X", p["x"] - 7, p["y"] - 13, font, (230, 70, 70))
        draw_text(p["name"], p["x"], p["y"] - 52, small, color, center=True)
        draw_bar(p["x"] - 32, p["y"] - 32, 64, 7, p["hp"], p["max_hp"])

    draw_hud_panel(pygame.Rect(14, 12, 232, 76))
    draw_text(f"Rodada {st.get('round', 1)}", 28, 24, font, (255, 226, 158))
    if st.get("infinite"):
        draw_text("Modo infinito", 128, 26, small, (88, 214, 156))
    arena_name = st.get("arena", {}).get("name", "Arena")
    draw_text(arena_name, 28, 46, small, (172, 231, 255))
    y = 62
    for p in sorted(st.get("players", []), key=lambda q: q["id"]):
        color = tuple(p.get("color", (230, 230, 230)))
        draw_text(f"{p['name']}: {p['wins']}v", 132 if p["id"] % 2 else 28, y, small, color)
        if p["id"] % 2:
            y += 16
    me = get_me(st)
    if me:
        draw_card_badges(st, me)
        draw_hud_panel(pygame.Rect(14, HEIGHT - 86, 430, 62))
        cooldown = max(0, float(me.get("active_ready_at", 0)) - time.time())
        active_text = "Ativa pronta" if cooldown <= 0 else f"Ativa {cooldown:.1f}s"
        parry_cooldown = max(0, float(me.get("parry_ready_at", 0)) - time.time())
        parry_active = time.time() < float(me.get("parry_until", 0))
        parry_text = "Parry ativo" if parry_active else ("Parry pronto" if parry_cooldown <= 0 else f"Parry {parry_cooldown:.1f}s")
        ammo = int(me.get("ammo", 0))
        max_ammo = int(me.get("max_ammo", 0))
        reload_left = max(0, float(me.get("reload_until", 0)) - time.time())
        ammo_text = f"Ammo {ammo}/{max_ammo} [R]" if reload_left <= 0 else f"Recarregando {reload_left:.1f}s [R]"
        build_summary = summarize_build(me)
        draw_text(active_text, 28, HEIGHT - 72, small, (255, 226, 158))
        draw_text(parry_text, 150, HEIGHT - 72, small, (170, 224, 255))
        summary_text = " ".join(f"{k}:{v}" for k, v in build_summary.items())
        draw_text(summary_text, 28, HEIGHT - 50, small, (180, 232, 196))
        draw_text(ammo_text, 250, HEIGHT - 72, small, (196, 232, 255))
        parry_hover = PARRY_BUTTON_RECT.collidepoint(pygame.mouse.get_pos())
        draw_button(PARRY_BUTTON_RECT, "Parry [Q]", parry_hover, parry_active or parry_cooldown <= 0)
    draw_button(GAME_MENU_RECT, "Menu", GAME_MENU_RECT.collidepoint(pygame.mouse.get_pos()))
    draw_hud_panel(pygame.Rect(942, 12, 318, 112))
    for i, line in enumerate(st.get("log", [])[-4:]):
        draw_text(line, 958, 24 + i * 18, small, (210, 218, 228))
    hazards = st.get("hazards", [])
    hazard_names = []
    for hazard in hazards:
        if hazard.get("type") == "saw":
            hazard_names.append("Serra")
        elif hazard.get("type") == "laser":
            hazard_names.append("Laser")
        elif hazard.get("type") == "wind":
            hazard_names.append("Vento")
        elif hazard.get("type") == "pulse":
            hazard_names.append("Pulso")
    if hazard_names:
        draw_text("Eventos: " + ", ".join(hazard_names[:3]), 958, 98, small, (255, 226, 158))
    else:
        draw_text("Eventos: arena limpa", 958, 98, small, (166, 214, 170))
    mutators = st.get("mutators", [])
    if mutators:
        draw_text("Mutadores: " + ", ".join(mutators[:2]), 958, 116, small, (155, 236, 255))
    elif st.get("mutators_enabled"):
        draw_text("Mutadores: aguardando rolagem", 958, 116, small, (155, 236, 255))

    if st.get("phase") == "waiting":
        draw_text("Aguardando pelo menos 2 jogadores...", WIDTH // 2, 90, big, center=True)
    elif st.get("phase") == "cards":
        draw_cards(st)


def draw_cards(st):
    global CARD_RECTS, CARD_ACTION_RECTS
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))
    winner = next((p for p in st.get("players", []) if p["id"] == st.get("winner")), None)
    title = f"{winner['name']} ganhou a rodada!" if winner else "Fim da rodada!"
    draw_text(title, WIDTH // 2, 95, big, (255, 235, 150), center=True)

    me = get_me(st)
    CARD_RECTS = []
    CARD_ACTION_RECTS = []
    cards = st.get("cards", [])
    draft_points = st.get("draft_points", 0)
    deck_count = max(1, int(st.get("draft_deck_count", 1)))
    chosen_decks = set(st.get("chosen_decks", []))
    if not cards:
        draw_text("Voce ganhou ou esta aguardando os perdedores escolherem cartas.", WIDTH // 2, 170, font, center=True)
    elif me and me.get("chosen"):
        draw_text("Carta escolhida. A proxima rodada comeca ja ja.", WIDTH // 2, 170, font, center=True)
    else:
        prompt = "Escolha uma carta para tentar virar o jogo:"
        if deck_count > 1:
            prompt = "Escolha 1 carta em cada deck desta rodada:"
        draw_text(prompt, WIDTH // 2, 160, font, center=True)
        remaining = max(0, deck_count - len(chosen_decks))
        draw_text(f"Escolhas restantes: {remaining}", WIDTH // 2, 174, small, (255, 226, 158), center=True)
        points_text = f"Pontos de draft: {draft_points} | Congelar/Queimar custa 1"
        if st.get("more_cards_enabled"):
            points_text += " | Modo Mais Cartas: +2 pontos a cada 5 rodadas"
        draw_text(points_text, WIDTH // 2, 192, small, (180, 224, 255), center=True)
        palette = [(226, 146, 46), (67, 163, 124), (82, 145, 210), (220, 84, 98)]
        if deck_count <= 1:
            deck_groups = [cards]
        else:
            deck_groups = [[entry for entry in cards if entry.get("deck", 0) == deck] for deck in range(deck_count)]
        for deck_index, deck_cards in enumerate(deck_groups):
            if not deck_cards and deck_count > 1 and deck_index not in chosen_decks:
                continue
            deck_y = 220 + deck_index * 156 if deck_count > 1 else 220
            if deck_count > 1:
                status = "ESCOLHIDO" if deck_index in chosen_decks else f"DECK {deck_index + 1}"
                status_color = (118, 226, 154) if deck_index in chosen_decks else (255, 226, 158)
                draw_text(status, 118, deck_y + 58, font, status_color)
            card_w = 220 if deck_count > 1 else (255 if len(deck_cards) >= 4 else 290)
            card_h = 138 if deck_count > 1 else 230
            gap = 14 if deck_count > 1 else (18 if len(deck_cards) >= 4 else 24)
            total_w = len(deck_cards) * card_w + max(0, len(deck_cards) - 1) * gap
            start_x = WIDTH // 2 - total_w // 2
            for idx, entry in enumerate(deck_cards):
                card = entry["id"]
                offer_id = entry.get("offer_id", card)
                x = start_x + idx * (card_w + gap)
                y = deck_y
                rect = pygame.Rect(x, y, card_w, card_h)
                CARD_RECTS.append((rect, offer_id, entry.get("deck", 0)))
                accent = palette[idx % len(palette)]
                pygame.draw.rect(screen, (16, 20, 30), rect.move(0, 8), border_radius=10)
                pygame.draw.rect(screen, (28, 35, 48), rect, border_radius=10)
                pygame.draw.rect(screen, accent, (x, y, card_w, 8), border_radius=10)
                if entry.get("special"):
                    pygame.draw.rect(screen, (255, 184, 90), (x + 12, y + 12, card_w - 24, rect.height - 24), 2, border_radius=10)
                pygame.draw.rect(screen, (220, 230, 240), rect, 2, border_radius=10)
                info = st["card_defs"][card]
                pygame.draw.circle(screen, accent, (x + card_w - 34, y + 34), 18 if deck_count > 1 else 24)
                draw_text(str(idx + 1), x + card_w - 34, y + 34, small if deck_count > 1 else font, (18, 22, 28), center=True)
                draw_text(info["name"], x + 14, y + 22, small if deck_count > 1 else font, (255, 235, 150))
                if entry.get("fusion"):
                    draw_text("FUSAO", x + 14, y + 46, small, (255, 166, 120))
                elif entry.get("special"):
                    draw_text("ESPECIAL", x + 14, y + 46, small, (255, 206, 120))
                words = info["desc"].split()
                line = ""
                yy = y + (66 if deck_count > 1 else 82)
                limit = 22 if deck_count > 1 else (24 if len(deck_cards) >= 4 else 28)
                max_lines = 2 if deck_count > 1 else 4
                lines_drawn = 0
                for w in words:
                    if len(line + " " + w) > limit:
                        draw_text(line, x + 14, yy, small, (230, 230, 235))
                        yy += 20
                        lines_drawn += 1
                        line = w
                        if lines_drawn >= max_lines:
                            break
                    else:
                        line = (line + " " + w).strip()
                if line and lines_drawn < max_lines:
                    draw_text(line, x + 14, yy, small, (230, 230, 235))
                    yy += 20
                footer_y = y + card_h - 36
                if entry.get("fusion") and entry.get("parts"):
                    req = " + ".join(st["card_defs"][part]["name"] for part in entry["parts"])
                    draw_text(req[:26 if deck_count > 1 else 31], x + 14, footer_y - 18, small, (255, 205, 170))
                elif entry.get("special"):
                    draw_text("Raridade baixa", x + 14, footer_y - 18, small, (255, 205, 170))
                synergy = recommend_synergy(card, me, st)
                if synergy and deck_count <= 1:
                    draw_text(synergy[:31], x + 18, y + 172, small, (170, 235, 190))
                elif synergy and deck_count > 1:
                    draw_text(synergy[:22], x + 14, footer_y - 2, small, (170, 235, 190))
                if deck_count <= 1:
                    draw_text(f"Clique para escolher [{idx+1}]", x + 18, y + 188, small, (190, 225, 255))
                freeze_rect = pygame.Rect(x + 12, y + card_h - 28, 88, 22)
                burn_rect = pygame.Rect(x + card_w - 100, y + card_h - 28, 88, 22)
                if draft_points > 0 and deck_index not in chosen_decks:
                    draw_button(freeze_rect, "Congelar", freeze_rect.collidepoint(pygame.mouse.get_pos()))
                    CARD_ACTION_RECTS.append((freeze_rect, offer_id, "freeze"))
                    if not info.get("fusion_only"):
                        draw_button(burn_rect, "Queimar", burn_rect.collidepoint(pygame.mouse.get_pos()))
                        CARD_ACTION_RECTS.append((burn_rect, offer_id, "burn"))
                if entry.get("frozen"):
                    draw_text("Congelada", x + card_w - 60, y + 14, small, (170, 240, 255), center=True)
    left = max(0, int(st.get("phase_until", 0) - time.time()))
    draw_text(f"Proxima rodada em ate {left}s", WIDTH // 2, 690 if deck_count > 1 else 500, font, center=True)


def choose_card(offer_id):
    try:
        send_json(sock, {"type": "choose_card", "card": offer_id})
        play_sound("card")
    except Exception:
        pass


def draft_action(offer_id, action):
    try:
        send_json(sock, {"type": "draft_action", "card": offer_id, "action": action})
        play_sound("freeze_card" if action == "freeze" else "burn_card")
    except Exception:
        pass

def run_game():
    paused = False
    sent_pause_stop = False
    while connected:
        clock.tick(FPS)
        with state_lock:
            st = state.copy() if isinstance(state, dict) else None

        pause_rects = None
        lobby_rects = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close_connection(stop_host=True)
                return "quit"
            if st and st.get("phase") == "lobby":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    close_connection(stop_host=True)
                    return "menu"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    lobby_rects = draw_lobby(st)
                    if lobby_rects["leave"].collidepoint(event.pos):
                        close_connection(stop_host=True)
                        return "menu"
                    if lobby_rects["is_host"] and lobby_rects["can_start"] and lobby_rects["start"].collidepoint(event.pos):
                        send_start_game()
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                paused = not paused
                sent_pause_stop = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if paused:
                    pause_rects = draw_pause_menu()
                    if pause_rects["resume"].collidepoint(event.pos):
                        paused = False
                        sent_pause_stop = False
                    elif pause_rects["leave"].collidepoint(event.pos):
                        close_connection(stop_host=True)
                        return "menu"
                    elif pause_rects["quit"].collidepoint(event.pos):
                        close_connection(stop_host=True)
                        return "quit"
                elif GAME_MENU_RECT.collidepoint(event.pos):
                    paused = True
                    sent_pause_stop = False
                elif st and st.get("phase") == "cards":
                    handled_action = False
                    for rect, offer_id, action in CARD_ACTION_RECTS:
                        if rect.collidepoint(event.pos):
                            draft_action(offer_id, action)
                            handled_action = True
                            break
                    if handled_action:
                        continue
                    for rect, offer_id, deck in CARD_RECTS:
                        if rect.collidepoint(event.pos):
                            choose_card(offer_id)
            elif not paused and event.type == pygame.KEYDOWN and st and st.get("phase") == "cards":
                cards = st.get("cards", [])
                if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    idx = event.key - pygame.K_1
                    if st.get("draft_deck_count", 1) <= 1:
                        if 0 <= idx < len(cards):
                            choose_card(cards[idx].get("offer_id", cards[idx]["id"]))
                    else:
                        chosen_decks = set(st.get("chosen_decks", []))
                        target_deck = next((deck for deck in range(int(st.get("draft_deck_count", 1))) if deck not in chosen_decks), None)
                        deck_cards = [entry for entry in cards if entry.get("deck", 0) == target_deck]
                        if target_deck is not None and 0 <= idx < len(deck_cards):
                            choose_card(deck_cards[idx].get("offer_id", deck_cards[idx]["id"]))

        if st:
            update_audio(st)
            if st.get("phase") == "lobby":
                send_neutral_input()
                draw_lobby(st)
            elif paused:
                if not sent_pause_stop:
                    send_neutral_input()
                    sent_pause_stop = True
                draw_game(st)
                draw_pause_menu()
            else:
                send_input(st)
                draw_game(st)
        else:
            screen.fill((12, 17, 26))
            draw_text("Conectando ao servidor...", WIDTH // 2, HEIGHT // 2, big, center=True)
        pygame.display.flip()
    close_connection(stop_host=True)
    return "menu"


app_running = True
while app_running:
    if not run_menu():
        break
    result = run_game()
    if result == "quit":
        break

close_connection(stop_host=True)
pygame.quit()
