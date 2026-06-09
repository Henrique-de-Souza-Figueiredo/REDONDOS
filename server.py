import math
import random
import socket
import argparse
import threading
import time
from shared import *

HOST = "0.0.0.0"
PORT = 50007
MAX_PLAYERS = 4
ROUND_WAIT_SECONDS = 18

DEFAULT_SPAWNS = [(130, FLOOR_Y - 40), (1150, FLOOR_Y - 40), (310, 180), (970, 180)]
DEFAULT_PLATFORMS = [
    (0, FLOOR_Y, WIDTH, HEIGHT - FLOOR_Y),
    (175, 500, 270, 25),
    (835, 500, 270, 25),
    (480, 385, 320, 25),
    (135, 260, 245, 25),
    (900, 260, 245, 25),
]
ARENAS = [
    {
        "id": "classic",
        "name": "Classic Chaos",
        "colors": {"sky_top": (16, 24, 38), "sky_bottom": (44, 66, 82), "accent": (230, 180, 90)},
        "platforms": DEFAULT_PLATFORMS,
        "spawns": DEFAULT_SPAWNS,
        "hazards": [],
    },
    {
        "id": "sawmill",
        "name": "Sawmill Panic",
        "colors": {"sky_top": (26, 19, 16), "sky_bottom": (87, 54, 32), "accent": (255, 146, 92)},
        "platforms": [
            (0, FLOOR_Y, WIDTH, HEIGHT - FLOOR_Y),
            (150, 535, 220, 24),
            (910, 535, 220, 24),
            (455, 450, 370, 24),
            (250, 310, 180, 22),
            (850, 310, 180, 22),
        ],
        "spawns": [(120, 610), (1160, 610), (335, 260), (945, 260)],
        "hazards": [
            {"type": "saw", "x1": 190, "y1": 420, "x2": 1090, "y2": 420, "speed": 0.75, "radius": 24, "damage": 14, "cooldown": 0.45},
            {"type": "saw", "x1": 320, "y1": 210, "x2": 960, "y2": 210, "speed": 1.1, "radius": 18, "damage": 11, "cooldown": 0.35, "phase": 0.35},
        ],
    },
    {
        "id": "neon",
        "name": "Neon Grid",
        "colors": {"sky_top": (8, 18, 32), "sky_bottom": (21, 54, 68), "accent": (96, 236, 255)},
        "platforms": [
            (0, FLOOR_Y, WIDTH, HEIGHT - FLOOR_Y),
            (130, 520, 210, 22),
            (470, 520, 340, 22),
            (940, 520, 210, 22),
            (285, 350, 240, 22),
            (755, 350, 240, 22),
            (540, 215, 200, 20),
        ],
        "spawns": [(100, 610), (1180, 610), (395, 300), (885, 300)],
        "hazards": [
            {"type": "laser", "axis": "vertical", "x": 395, "y1": 90, "y2": FLOOR_Y, "thickness": 16, "cycle": 3.2, "on_time": 1.35, "damage": 18, "cooldown": 0.22},
            {"type": "laser", "axis": "vertical", "x": 885, "y1": 90, "y2": FLOOR_Y, "thickness": 16, "cycle": 3.2, "on_time": 1.35, "damage": 18, "cooldown": 0.22, "phase": 1.6},
            {"type": "laser", "axis": "horizontal", "y": 282, "x1": 180, "x2": 1100, "thickness": 12, "cycle": 4.4, "on_time": 1.1, "damage": 15, "cooldown": 0.22, "phase": 0.8},
        ],
    },
    {
        "id": "wind",
        "name": "Sky Temple",
        "colors": {"sky_top": (24, 36, 52), "sky_bottom": (114, 150, 164), "accent": (205, 238, 160)},
        "platforms": [
            (0, FLOOR_Y, WIDTH, HEIGHT - FLOOR_Y),
            (120, 560, 170, 22),
            (990, 560, 170, 22),
            (320, 470, 220, 22),
            (740, 470, 220, 22),
            (535, 360, 210, 20),
            (220, 250, 180, 20),
            (880, 250, 180, 20),
        ],
        "spawns": [(105, 610), (1175, 610), (310, 205), (970, 205)],
        "hazards": [
            {"type": "wind", "x": 0, "y": 180, "w": 220, "h": 380, "vx": 1.8, "vy": -0.15, "cycle": 4.2, "on_time": 2.2, "phase": 0.3},
            {"type": "wind", "x": WIDTH - 220, "y": 180, "w": 220, "h": 380, "vx": -1.8, "vy": -0.15, "cycle": 4.2, "on_time": 2.2, "phase": 2.1},
            {"type": "pulse", "x": WIDTH // 2, "y": 520, "radius": 180, "cycle": 5.4, "on_time": 0.7, "damage": 12, "force": 18, "cooldown": 0.5, "phase": 1.2},
        ],
    },
    {
        "id": "factory",
        "name": "Factory Overload",
        "colors": {"sky_top": (22, 20, 25), "sky_bottom": (82, 71, 59), "accent": (255, 90, 90)},
        "platforms": [
            (0, FLOOR_Y, WIDTH, HEIGHT - FLOOR_Y),
            (90, 520, 220, 22),
            (970, 520, 220, 22),
            (375, 500, 180, 20),
            (725, 500, 180, 20),
            (520, 380, 240, 22),
            (180, 270, 220, 20),
            (880, 270, 220, 20),
        ],
        "spawns": [(110, 610), (1170, 610), (280, 220), (1000, 220)],
        "hazards": [
            {"type": "laser", "axis": "horizontal", "y": 590, "x1": 70, "x2": 1210, "thickness": 14, "cycle": 5.1, "on_time": 1.1, "damage": 20, "cooldown": 0.22},
            {"type": "saw", "x1": 120, "y1": 330, "x2": 1160, "y2": 330, "speed": 0.55, "radius": 22, "damage": 13, "cooldown": 0.4, "phase": 0.6},
            {"type": "wind", "x": 500, "y": 120, "w": 280, "h": 170, "vx": 0.0, "vy": -0.95, "cycle": 3.7, "on_time": 1.5, "phase": 1.0},
        ],
    },
    {
        "id": "volcano",
        "name": "Volcano Rush",
        "colors": {"sky_top": (38, 16, 12), "sky_bottom": (142, 66, 28), "accent": (255, 178, 84)},
        "platforms": [
            (0, FLOOR_Y, WIDTH, HEIGHT - FLOOR_Y),
            (80, 560, 180, 20),
            (1020, 560, 180, 20),
            (310, 470, 220, 22),
            (750, 470, 220, 22),
            (515, 340, 250, 20),
            (190, 245, 180, 18),
            (910, 245, 180, 18),
        ],
        "spawns": [(110, 612), (1170, 612), (295, 205), (985, 205)],
        "hazards": [
            {"type": "pulse", "x": WIDTH // 2, "y": 640, "radius": 250, "cycle": 4.8, "on_time": 0.8, "damage": 15, "force": 22},
            {"type": "laser", "axis": "horizontal", "y": 430, "x1": 220, "x2": 1060, "thickness": 10, "cycle": 5.0, "on_time": 0.9, "damage": 18, "cooldown": 0.2, "phase": 0.6},
        ],
    },
    {
        "id": "glacier",
        "name": "Glacier Drift",
        "colors": {"sky_top": (18, 34, 52), "sky_bottom": (140, 188, 210), "accent": (210, 245, 255)},
        "platforms": [
            (0, FLOOR_Y, WIDTH, HEIGHT - FLOOR_Y),
            (150, 540, 220, 20),
            (910, 540, 220, 20),
            (440, 510, 400, 20),
            (240, 360, 220, 18),
            (820, 360, 220, 18),
            (535, 235, 210, 18),
        ],
        "spawns": [(130, 612), (1150, 612), (320, 315), (960, 315)],
        "hazards": [
            {"type": "wind", "x": 0, "y": 300, "w": WIDTH, "h": 160, "vx": 0.95, "vy": 0.0, "cycle": 5.8, "on_time": 2.1},
            {"type": "laser", "axis": "vertical", "x": 640, "y1": 110, "y2": FLOOR_Y, "thickness": 12, "cycle": 4.2, "on_time": 1.0, "damage": 16, "cooldown": 0.22, "phase": 2.0},
        ],
    },
    {
        "id": "void",
        "name": "Void Relay",
        "colors": {"sky_top": (12, 10, 28), "sky_bottom": (58, 42, 84), "accent": (170, 120, 255)},
        "platforms": [
            (0, FLOOR_Y, WIDTH, HEIGHT - FLOOR_Y),
            (110, 535, 180, 20),
            (990, 535, 180, 20),
            (340, 450, 180, 18),
            (760, 450, 180, 18),
            (520, 365, 240, 18),
            (250, 250, 170, 18),
            (860, 250, 170, 18),
        ],
        "spawns": [(105, 610), (1175, 610), (300, 205), (980, 205)],
        "hazards": [
            {"type": "saw", "x1": 180, "y1": 145, "x2": 1100, "y2": 145, "speed": 0.95, "radius": 20, "damage": 12, "cooldown": 0.32},
            {"type": "pulse", "x": WIDTH // 2, "y": 365, "radius": 150, "cycle": 4.0, "on_time": 0.65, "damage": 14, "force": 20, "phase": 1.5},
            {"type": "laser", "axis": "horizontal", "y": 590, "x1": 90, "x2": 1190, "thickness": 12, "cycle": 5.5, "on_time": 0.95, "damage": 20, "cooldown": 0.2, "phase": 0.9},
        ],
    },
]
FUSION_RECIPES = [
    {"result": "reverse_overdrive", "parts": ("uno_reverse", "no_u", "spiderman_pointing")},
    {"result": "final_notice", "parts": ("omae_wa", "call_an_ambulance", "bonk")},
    {"result": "chaos_engine", "parts": ("keyboard_smash", "dramatic_chipmunk", "disaster_girl")},
    {"result": "berserker_prime", "parts": ("leeroy_jenkins", "charlie_bit_my_finger", "crying_jordan")},
    {"result": "omega_event_horizon", "parts": ("mini_black_hole", "supernova", "void_rift")},
    {"result": "judgement_day", "parts": ("tsar_bomba", "orbital_laser", "apocalypse_rain")},
    {"result": "tempest_cataclysm", "parts": ("brainrot_tornado", "world_freeze", "quake_slam")},
]
GLOBAL_MUTATORS = [
    {"id": "low_gravity", "name": "Low Gravity"},
    {"id": "bullet_hell", "name": "Bullet Hell"},
    {"id": "parry_mania", "name": "Parry Mania"},
    {"id": "speed_freaks", "name": "Speed Freaks"},
    {"id": "sudden_death", "name": "Sudden Death"},
    {"id": "hazard_party", "name": "Hazard Party"},
]
SPECIAL_CARDS = {key for key, info in CARD_DEFS.items() if info.get("special")}

CARD_KEYS = [key for key, info in CARD_DEFS.items() if not info.get("fusion_only")]
ACTIVE_CARDS = (
    "gemidao_zap", "pix_misterioso", "zap_do_meteoro", "modo_turbo", "buraco_negro", "raio_trovao", "blox_fruits",
    "skibidi", "rizz", "grimace_shake", "among_us", "rickroll", "marilene", "bluezao", "nyan_cat", "keyboard_cat",
    "this_is_fine", "distracted_boyfriend", "salt_bae", "john_cena", "morbin_time", "coffin_dance", "wednesday_dance",
    "pedro_pedro", "harlem_shake", "fanum_tax", "backrooms", "quandale_dingle", "do_you_know_da_wae", "area_51",
    "all_your_base", "numa_numa", "ice_bucket", "tide_pod", "woman_yelling", "baby_shark", "obama_prism",
    "tsar_bomba", "mini_black_hole", "brainrot_tornado", "meteor_swarm", "orbital_laser", "world_freeze",
    "void_rift", "apocalypse_rain", "supernova", "quake_slam", "guided_swarm", "remote_detonator", "magnet_trigger", "portal_storm",
    "omega_event_horizon", "judgement_day", "tempest_cataclysm",
    "me_and_the_boys", "evil_kermit",
)
TANK_CARDS = ("big_chungus", "shrek", "giga_chad", "planking", "berserker_prime")
SPEED_CARDS = ("gangnam_style", "dat_boi", "ugandan_knuckles", "ultra_instinct", "leeroy_jenkins", "chaos_engine", "berserker_prime", "glass_cannon_tv")
DAMAGE_CARDS = ("giga_chad", "bad_luck_brian", "ratio", "stonks", "corecore", "keyboard_smash", "charlie_bit_my_finger", "final_notice", "chaos_engine", "berserker_prime", "judgement_day", "railgun_charge", "glass_cannon_tv")
LUCK_CARDS = ("success_kid", "surprised_pikachu", "trollface", "based", "dramatic_chipmunk", "chaos_engine", "omega_event_horizon")
BULLET_CARDS = ("nyan_cat", "corn_kid", "ankha_zone", "baby_shark", "me_and_the_boys", "homing_rounds", "cluster_pop", "ricochet_roulette")
PARRY_CARDS = ("uno_reverse", "no_u", "omae_wa", "mans_not_hot", "call_an_ambulance", "spiderman_pointing", "is_this_pigeon", "bonk", "reverse_overdrive", "final_notice")

class Player:
    def __init__(self, pid, name):
        self.id = pid
        self.name = name or f"Player {pid + 1}"
        self.color = PLAYER_COLORS[pid]
        self.wins = 0
        self.total_buffs = {k: 0 for k in CARD_DEFS}
        self.input = {"left": False, "right": False, "jump": False, "shoot": False, "active": False, "parry": False, "reload": False, "aim": 0.0}
        self.card_offer = []
        self.chosen_decks = set()
        self.frozen_cards = []
        self.last_offer_frozen = set()
        self.burned_cards = set()
        self.draft_points = 0
        self.last_picked_special = False
        self.last_picked_fusion = False
        self.chosen_this_phase = False
        self.was_jumping = False
        self.was_active = False
        self.active_ready_at = 0.0
        self.reload_until = 0.0
        self.reload_started_at = 0.0
        self.shots_since_reload = 0
        self.slow_until = 0.0
        self.silenced_until = 0.0
        self.poison_until = 0.0
        self.poison_damage = 0
        self.double_shot_until = 0.0
        self.rhythm_until = 0.0
        self.intangible_until = 0.0
        self.parry_until = 0.0
        self.parry_ready_at = 0.0
        self.parry_empower_until = 0.0
        self.last_ground_heal = 0.0
        self.revive_used = False
        self.reset_for_round()

    def count(self, *keys):
        return sum(self.total_buffs.get(k, 0) for k in keys)

    def card_count(self):
        return sum(self.total_buffs.values())

    def max_hp(self):
        return int(100 + 25 * self.total_buffs["shield"] + 15 * self.total_buffs["xou_xuxa"] + 18 * self.count("amostradinho", "ohio_final_boss") + 5 * self.total_buffs["doge"] + 22 * self.count(*TANK_CARDS) + 8 * self.total_buffs["stonks"] - 22 * self.total_buffs["glass_cannon_tv"])

    def speed(self):
        value = 4.2 * (1.18 ** self.total_buffs["speed"]) * (1.12 ** self.total_buffs["bora_bill"]) * (1.14 ** self.total_buffs["descer_bc"]) * (1.03 ** self.total_buffs["doge"])
        value *= 1.10 ** self.count(*SPEED_CARDS)
        value *= 1.05 ** self.total_buffs["stonks"]
        value *= 1.08 ** self.total_buffs["keyboard_smash"]
        value *= 1.14 ** self.total_buffs["berserker_prime"]
        value *= 0.84 ** self.total_buffs["ohio_final_boss"]
        value *= 0.90 ** self.count(*TANK_CARDS)
        if time.time() < self.rhythm_until:
            value *= 1.45
        if time.time() < self.slow_until:
            value *= 0.55
        return value

    def jump_power(self):
        return 12.5 * (1.18 ** self.total_buffs["jump"]) * (1.08 ** self.total_buffs["roblox_obby"]) * (1.06 ** self.total_buffs["wednesday_dance"]) * (1.02 ** self.total_buffs["doge"])

    def damage(self):
        scaling = 1 + 0.014 * self.card_count() * self.total_buffs["sigma_bahia"]
        chaos = 1 + 0.009 * self.card_count() * self.total_buffs["corecore"]
        lonely = 1.0 + 0.08 * self.total_buffs["no_bitches"]
        return int(18 * (1.18 ** self.total_buffs["damage"]) * (1.07 ** self.total_buffs["casca_de_bala"]) * (1.09 ** self.total_buffs["ratinho"]) * (1.07 ** self.total_buffs["faz_o_m"]) * (1.06 ** self.count(*DAMAGE_CARDS)) * (1.03 ** self.total_buffs["doge"]) * (1.14 ** self.total_buffs["final_notice"]) * (1.09 ** self.total_buffs["chaos_engine"]) * (1.15 ** self.total_buffs["glass_cannon_tv"]) * scaling * chaos * lonely)

    def fire_cooldown(self):
        value = 0.42 * (0.82 ** self.total_buffs["firerate"]) * (0.88 ** self.total_buffs["ta_ok"]) * (0.95 ** self.total_buffs["galaxy_brain"]) * (0.97 ** self.total_buffs["doge"])
        value *= 0.90 ** self.total_buffs["leeroy_jenkins"]
        value *= 0.88 ** self.total_buffs["keyboard_smash"]
        value *= 0.88 ** self.total_buffs["chaos_engine"]
        value *= 0.92 ** self.total_buffs["buckshot_mayhem"]
        if time.time() < self.rhythm_until:
            value *= 0.55
        return max(0.075, value)

    def max_ammo(self):
        return max(1, 3 + self.total_buffs["caneta_azul"] + self.total_buffs["galaxy_brain"] + self.total_buffs["glock_lisa"])

    def reload_duration(self):
        value = 1.55
        value *= 0.90 ** self.total_buffs["firerate"]
        value *= 0.92 ** self.total_buffs["ta_ok"]
        value *= 0.94 ** self.total_buffs["keyboard_smash"]
        value *= 0.93 ** self.total_buffs["galaxy_brain"]
        value *= 0.82 ** self.total_buffs["reload_chad"]
        value *= 1.08 ** self.total_buffs["railgun_charge"]
        return max(0.48, value)

    def bullet_gravity(self):
        return BULLET_GRAVITY * (0.72 ** self.total_buffs["bullet_grav"]) * (0.86 ** self.total_buffs["roblox_obby"])

    def reset_for_round(self, spawn=None):
        x, y = spawn if spawn else DEFAULT_SPAWNS[self.id]
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.hp = self.max_hp() if hasattr(self, "total_buffs") else 100
        self.alive = True
        self.on_ground = False
        self.air_jumps_used = 0
        self.last_regen = time.time()
        self.last_shot = 0.0
        self.ammo = self.max_ammo()
        self.reload_until = 0.0
        self.reload_started_at = 0.0
        self.shots_since_reload = 0
        self.aim = 0.0
        self.was_jumping = False
        self.was_active = False
        self.slow_until = 0.0
        self.silenced_until = 0.0
        self.poison_until = 0.0
        self.poison_damage = 0
        self.double_shot_until = 0.0
        self.rhythm_until = 0.0
        self.intangible_until = 0.0
        self.parry_until = 0.0
        self.parry_ready_at = 0.0
        self.parry_empower_until = 0.0
        self.revive_used = False
        self.chosen_decks = set()

    def bullet_speed(self):
        return 15.0 * (1.16 ** self.total_buffs["bullet_speed"]) * (1.10 ** self.total_buffs["casca_de_bala"]) * (1.06 ** self.count(*BULLET_CARDS)) * (1.03 ** self.total_buffs["doge"]) * (1.10 ** self.total_buffs["chaos_engine"]) * (1.18 ** self.total_buffs["glass_cannon_tv"])

    def bullet_radius(self):
        return BULLET_RADIUS + 2 * self.total_buffs["big_bullets"] + self.total_buffs["ratinho"] + 2 * self.total_buffs["ohio_final_boss"] + self.count("big_chungus", "shrek", "obama_prism")

    def armor_multiplier(self):
        multiplier = (0.86 ** self.total_buffs["armor"]) * (0.88 ** self.total_buffs["base_virginia"]) * (0.84 ** self.total_buffs["gyatt"]) * (0.82 ** self.total_buffs["ohio_final_boss"]) * (0.97 ** self.total_buffs["doge"])
        multiplier *= 0.88 ** self.count(*TANK_CARDS)
        multiplier *= 1.08 ** self.total_buffs["leeroy_jenkins"]
        multiplier *= 0.88 ** self.total_buffs["berserker_prime"]
        if self.hp <= self.max_hp() * 0.4:
            multiplier *= 0.78 ** (self.total_buffs["calma_calabreso"] + self.total_buffs["wojak"] + self.total_buffs["moye_moye"])
            multiplier *= 0.84 ** self.total_buffs["crying_jordan"]
        return multiplier

    def lifesteal_ratio(self):
        return min(0.55, 0.16 * self.total_buffs["lifesteal"] + 0.07 * self.total_buffs["rizz"] + 0.08 * self.total_buffs["morbin_time"] + 0.07 * self.total_buffs["charlie_bit_my_finger"])

    def regen_amount(self):
        base = self.total_buffs["regen"] + 2 * self.total_buffs["xique_xique"] + 3 * self.total_buffs["shrek"] + self.total_buffs["hide_pain_harold"] + self.total_buffs["doge"]
        if self.hp <= self.max_hp() * 0.45:
            base += 2 * self.total_buffs["crying_jordan"]
        return base

    def bullet_life(self):
        return 3.0 + 0.55 * self.total_buffs["caneta_azul"] + 0.5 * self.total_buffs["ankha_zone"] + 0.35 * self.count(*BULLET_CARDS)

    def crit_chance(self):
        return min(0.72, 0.12 * self.total_buffs["receba"] + 0.10 * self.total_buffs["amostradinho"] + 0.08 * self.total_buffs["pepe"] + 0.06 * self.total_buffs["galaxy_brain"] + 0.05 * self.count(*LUCK_CARDS) + 0.04 * self.total_buffs["doge"] + 0.07 * self.total_buffs["chaos_engine"])

    def crit_multiplier(self):
        return 1.7 + 0.35 * self.total_buffs["faustao"] + 0.22 * self.total_buffs["el_risitas"] + 0.16 * self.total_buffs["dramatic_chipmunk"]

    def dodge_chance(self):
        return min(0.78, 0.10 * self.total_buffs["la_ele"] + 0.08 * self.total_buffs["ney_malvadeza"] + 0.06 * self.total_buffs["pepe"] + 0.08 * self.total_buffs["ultra_instinct"] + 0.05 * self.total_buffs["side_eye_chloe"])

    def knockback_strength(self):
        return 8.5 * self.total_buffs["luva_pedreiro"] + 4.0 * self.total_buffs["gyatt"] + 7.0 * self.total_buffs["yeet"] + 4.0 * self.total_buffs["giga_chad"]

    def bounces(self):
        return self.total_buffs["bounce"] + self.total_buffs["ankha_zone"] + self.total_buffs["nyan_cat"] + self.total_buffs["ricochet_roulette"]

    def homing_strength(self):
        return 0.0 + 0.12 * self.total_buffs["homing_rounds"] + 0.08 * self.total_buffs["drone_guidance"] + 0.10 * self.total_buffs["guided_swarm"]

    def split_shots(self):
        return self.total_buffs["cluster_pop"]

    def explosion_radius(self):
        return 0 + 26 * self.total_buffs["toxic_payload"]

    def pierce_count(self):
        return self.total_buffs["railgun_charge"]

    def boomerang_delay(self):
        stacks = self.total_buffs["boomerang_rounds"]
        if not stacks:
            return 0.0
        return max(0.18, 0.7 - 0.12 * (stacks - 1))

    def active_power(self):
        return self.count(*ACTIVE_CARDS)

    def active_cooldown(self):
        return max(1.8, 9.8 - 0.20 * self.active_power() - 0.30 * self.total_buffs["npc_streamer"] - 0.35 * self.total_buffs["galaxy_brain"] - 0.24 * self.total_buffs["dramatic_chipmunk"])

    def parry_duration(self):
        return 0.5 + 0.18 * self.total_buffs["uno_reverse"] + 0.08 * self.total_buffs["omae_wa"] + 0.20 * self.total_buffs["reverse_overdrive"] + 0.08 * self.total_buffs["final_notice"]

    def parry_cooldown(self):
        return max(1.1, 3.8 - 0.55 * self.total_buffs["no_u"] - 0.25 * self.total_buffs["uno_reverse"] - 0.15 * self.total_buffs["galaxy_brain"] - 0.60 * self.total_buffs["reverse_overdrive"])

    def parry_damage_multiplier(self):
        return 1.0 + 0.35 * self.total_buffs["uno_reverse"] + 0.12 * self.total_buffs["mans_not_hot"] + 0.20 * self.total_buffs["call_an_ambulance"] + 0.45 * self.total_buffs["reverse_overdrive"] + 0.35 * self.total_buffs["final_notice"]

    def parry_speed_multiplier(self):
        return 1.12 + 0.12 * self.total_buffs["no_u"] + 0.06 * self.count(*PARRY_CARDS) + 0.16 * self.total_buffs["reverse_overdrive"]

    def parry_guard_radius(self):
        return PLAYER_RADIUS + 10 + 5 * self.total_buffs["is_this_pigeon"] + 2 * self.count(*PARRY_CARDS) + 10 * self.total_buffs["reverse_overdrive"]

class Bullet:
    def __init__(self, owner, x, y, vx, vy, damage, grav, bounces, radius, life, knockback, homing=0.0, split=0, explode_radius=0, pierce=0, boomerang_delay=0.0, accelerate=0.0, ghost_passes=0, bounce_scale=0):
        self.owner = owner
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.grav = grav
        self.bounces = bounces
        self.radius = radius
        self.life = life
        self.max_life = life
        self.knockback = knockback
        self.homing = homing
        self.split = split
        self.explode_radius = explode_radius
        self.pierce = pierce
        self.boomerang_delay = boomerang_delay
        self.accelerate = accelerate
        self.ghost_passes = ghost_passes
        self.bounce_scale = bounce_scale
        self.reflected = False
        self.exploded = False
        self.created_at = time.time()

class GameServer:
    def __init__(self, room_code="", allow_solo=False, infinite_mode=False, mutators_enabled=False, more_cards_enabled=False):
        self.lock = threading.RLock()
        self.clients = {}
        self.players = {}
        self.next_pid = 0
        self.bullets = []
        self.phase = "lobby"
        self.phase_until = 0
        self.round_winner = None
        self.round = 1
        self.log = ["Servidor iniciado. Lobby aberto."]
        self.running = True
        self.room_code = room_code.strip().upper()
        self.allow_solo = allow_solo
        self.infinite_mode = infinite_mode
        self.mutators_enabled = mutators_enabled
        self.more_cards_enabled = more_cards_enabled
        self.min_players = 1 if allow_solo else 2
        self.host_id = None
        self.current_arena = ARENAS[0]
        self.round_started_at = time.time()
        self.hazard_hits = {}
        self.active_mutators = []
        self.effects = []
        self.offer_nonce = 0

    def required_players_to_start(self):
        return 1 if self.allow_solo else 2

    def can_start_game(self):
        return len(self.players) >= self.required_players_to_start()

    def ensure_host(self):
        if self.host_id in self.players:
            return
        self.host_id = min(self.players) if self.players else None

    def reset_to_lobby(self, msg=None):
        self.phase = "lobby"
        self.phase_until = 0
        self.round_winner = None
        self.bullets.clear()
        self.effects.clear()
        self.hazard_hits.clear()
        if msg:
            self.log_msg(msg)

    def draft_deck_count(self):
        return 3 if self.more_cards_enabled else 1

    def draft_point_gain(self):
        return 2 if self.more_cards_enabled else 1

    def next_offer_id(self, deck, card):
        self.offer_nonce += 1
        return f"d{deck}_{self.offer_nonce}_{card}"

    def make_offer_entry(self, card, deck, frozen=False):
        return {"offer_id": self.next_offer_id(deck, card), "card": card, "deck": deck, "frozen": frozen}

    def active_offer_cards(self, p, deck=None):
        cards = []
        for entry in p.card_offer:
            if deck is not None and entry["deck"] != deck:
                continue
            cards.append(entry["card"])
        return cards

    def build_offer_pool(self, p, excluded_cards):
        pool = []
        for card in CARD_KEYS:
            if card in p.burned_cards or card in excluded_cards:
                continue
            if card in SPECIAL_CARDS and random.random() > 0.16:
                continue
            pool.append(card)
        random.shuffle(pool)
        return pool

    def find_offer_entry(self, p, offer_id):
        return next((entry for entry in p.card_offer if entry["offer_id"] == offer_id), None)

    def log_msg(self, msg):
        print(msg, flush=True)
        self.log.append(msg)
        self.log = self.log[-7:]

    def extend_timer(self, current_until, duration):
        now = time.time()
        return max(current_until, now) + duration

    def stack_slow(self, player, duration, intensity=0):
        player.slow_until = self.extend_timer(player.slow_until, duration)
        if intensity:
            player.vx *= max(0.2, 1.0 - 0.04 * intensity)

    def stack_silence(self, player, duration):
        player.silenced_until = self.extend_timer(player.silenced_until, duration)

    def stack_poison(self, player, duration, damage):
        player.poison_until = self.extend_timer(player.poison_until, duration)
        player.poison_damage += max(1, damage)

    def stack_rhythm(self, player, duration):
        player.rhythm_until = self.extend_timer(player.rhythm_until, duration)

    def stack_intangible(self, player, duration):
        player.intangible_until = self.extend_timer(player.intangible_until, duration)

    def stack_double_shot(self, player, duration):
        player.double_shot_until = self.extend_timer(player.double_shot_until, duration)

    def stack_parry_empower(self, player, duration):
        player.parry_empower_until = self.extend_timer(player.parry_empower_until, duration)

    def spawn_effect(self, effect_type, x, y, duration=0.9, **extra):
        payload = {"type": effect_type, "x": float(x), "y": float(y), "until": time.time() + duration}
        payload.update(extra)
        self.effects.append(payload)

    def current_platforms(self):
        return self.current_arena.get("platforms", DEFAULT_PLATFORMS)

    def current_spawns(self):
        return self.current_arena.get("spawns", DEFAULT_SPAWNS)

    def select_next_arena(self):
        options = [arena for arena in ARENAS if arena["id"] != self.current_arena["id"]]
        if not options:
            options = ARENAS[:]
        self.current_arena = random.choice(options)
        self.log_msg(f"Novo mapa: {self.current_arena['name']}")

    def has_mutator(self, mutator_id):
        return mutator_id in self.active_mutators

    def roll_mutators(self):
        if not self.mutators_enabled:
            self.active_mutators = []
            return
        count = 2 if random.random() < 0.35 else 1
        self.active_mutators = [m["id"] for m in random.sample(GLOBAL_MUTATORS, count)]
        names = [m["name"] for m in GLOBAL_MUTATORS if m["id"] in self.active_mutators]
        self.log_msg("Mutadores: " + ", ".join(names))

    def get_fusion_recipe(self, result):
        return next((recipe for recipe in FUSION_RECIPES if recipe["result"] == result), None)

    def fusion_ready(self, p, recipe):
        return p.total_buffs.get(recipe["result"], 0) <= 0 and all(p.total_buffs.get(part, 0) > 0 for part in recipe["parts"])

    def build_card_offer(self, p):
        frozen = []
        seen = set()
        for card in p.frozen_cards:
            if card in p.burned_cards or card in seen:
                continue
            frozen.append(card)
            seen.add(card)
        p.last_offer_frozen = set()
        offer = []
        excluded = set()
        frozen_idx = 0
        ready_fusions = [recipe["result"] for recipe in FUSION_RECIPES if self.fusion_ready(p, recipe)]
        fusion_queue = [card for card in ready_fusions if card not in excluded]
        for deck in range(self.draft_deck_count()):
            deck_cards = []
            while frozen_idx < len(frozen) and len(deck_cards) < 4:
                card = frozen[frozen_idx]
                frozen_idx += 1
                if card in excluded:
                    continue
                deck_cards.append(self.make_offer_entry(card, deck, frozen=True))
                p.last_offer_frozen.add(card)
                excluded.add(card)
            for card in list(fusion_queue):
                if len(deck_cards) >= 4:
                    break
                if card in excluded:
                    continue
                deck_cards.append(self.make_offer_entry(card, deck))
                excluded.add(card)
                fusion_queue.remove(card)
            pool = self.build_offer_pool(p, excluded)
            while len(deck_cards) < 4 and pool:
                card = pool.pop()
                deck_cards.append(self.make_offer_entry(card, deck))
                excluded.add(card)
            offer.extend(deck_cards)
        p.frozen_cards = frozen[frozen_idx:]
        return offer

    def refill_offer_slot(self, p, deck):
        if deck in p.chosen_decks:
            return
        excluded = set(self.active_offer_cards(p))
        deck_entries = [entry for entry in p.card_offer if entry["deck"] == deck]
        ready_fusions = [recipe["result"] for recipe in FUSION_RECIPES if self.fusion_ready(p, recipe) and recipe["result"] not in excluded]
        while len(deck_entries) < 4:
            card = None
            for fusion in ready_fusions:
                if fusion not in excluded:
                    card = fusion
                    ready_fusions.remove(fusion)
                    break
            if not card:
                pool = self.build_offer_pool(p, excluded)
                if not pool:
                    break
                card = pool.pop()
            entry = self.make_offer_entry(card, deck)
            p.card_offer.append(entry)
            deck_entries.append(entry)
            excluded.add(card)

    def choose_card_for_player(self, p, offer_id, announce=True):
        entry = self.find_offer_entry(p, offer_id)
        if not entry:
            return False
        deck = entry["deck"]
        if deck in p.chosen_decks:
            return False
        card = entry["card"]
        recipe = self.get_fusion_recipe(card)
        if recipe:
            if not self.fusion_ready(p, recipe):
                return False
            for part in recipe["parts"]:
                p.total_buffs[part] -= 1
            p.total_buffs[card] += 1
            p.last_picked_special = bool(CARD_DEFS.get(card, {}).get("special"))
            p.last_picked_fusion = True
            if announce:
                self.log_msg(f"{p.name} fundiu {CARD_DEFS[card]['name']}")
        else:
            p.total_buffs[card] += 1
            p.last_picked_special = bool(CARD_DEFS.get(card, {}).get("special"))
            p.last_picked_fusion = False
            if announce:
                self.log_msg(f"{p.name} escolheu {CARD_DEFS[card]['name']}")
        if card in p.frozen_cards:
            p.frozen_cards = [f for f in p.frozen_cards if f != card]
        p.card_offer = [offer for offer in p.card_offer if offer["deck"] != deck]
        p.chosen_decks.add(deck)
        p.chosen_this_phase = len(p.chosen_decks) >= self.draft_deck_count()
        return True

    def auto_choose_missing_cards(self, p):
        picked = False
        for deck in range(self.draft_deck_count()):
            if deck in p.chosen_decks:
                continue
            deck_entries = [entry for entry in p.card_offer if entry["deck"] == deck]
            if not deck_entries:
                continue
            choice = random.choice(deck_entries)
            if self.choose_card_for_player(p, choice["offer_id"], announce=False):
                self.log_msg(f"{p.name} recebeu aleatoriamente {CARD_DEFS[choice['card']]['name']}")
                picked = True
        return picked

    def start_socket(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            srv.bind((HOST, PORT))
        except Exception as e:
            self.log_msg(f"Erro ao abrir servidor em {HOST}:{PORT}: {e}")
            self.running = False
            return
        srv.listen()
        self.log_msg(f"Servidor ouvindo em {HOST}:{PORT}")
        if self.room_code:
            self.log_msg(f"Codigo da sala: {self.room_code}")
        if self.allow_solo:
            self.log_msg("Modo teste solo ativado")
        if self.infinite_mode:
            self.log_msg("Modo infinito ativado: rodadas e cartas sem limite")
        if self.more_cards_enabled:
            self.log_msg("Modo Mais Cartas ativado: 3 decks por rodada")
        while self.running:
            conn, addr = srv.accept()
            hello = self.read_hello(conn)
            if not hello:
                conn.close()
                continue
            if self.room_code and str(hello.get("code", "")).strip().upper() != self.room_code:
                send_json(conn, {"type": "reject", "msg": "Codigo da sala invalido"})
                conn.close()
                continue
            with self.lock:
                if len(self.players) >= MAX_PLAYERS:
                    send_json(conn, {"type": "full", "msg": "Sala cheia"})
                    conn.close()
                    continue
                pid = next(i for i in range(MAX_PLAYERS) if i not in self.players)
                name = str(hello.get("name", "")).strip()[:18]
                player = Player(pid, name or f"Player {pid + 1}")
                self.players[pid] = player
                self.clients[pid] = conn
                if self.host_id is None:
                    self.host_id = pid
                self.log_msg(f"{player.name} conectado de {addr[0]}")
            threading.Thread(target=self.client_reader, args=(pid, conn), daemon=True).start()

    def read_hello(self, conn):
        lb = LineBuffer()
        conn.settimeout(5)
        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    return None
                for msg in lb.feed(data):
                    if msg.get("type") == "hello":
                        conn.settimeout(None)
                        return msg
        except Exception:
            return None

    def client_reader(self, pid, conn):
        lb = LineBuffer()
        try:
            while self.running:
                data = conn.recv(4096)
                if not data:
                    break
                for msg in lb.feed(data):
                    self.handle_message(pid, msg)
        except Exception as e:
            self.log_msg(f"Player {pid + 1} saiu: {e}")
        finally:
            with self.lock:
                self.clients.pop(pid, None)
                if pid in self.players:
                    name = self.players[pid].name
                    self.players.pop(pid, None)
                    self.log_msg(f"{name} desconectou")
                self.ensure_host()
                if len(self.players) < self.required_players_to_start() and self.phase in ("playing", "cards"):
                    self.reset_to_lobby("Jogadores insuficientes. Voltando ao lobby.")
            try:
                conn.close()
            except Exception:
                pass

    def handle_message(self, pid, msg):
        with self.lock:
            p = self.players.get(pid)
            if not p:
                return
            if msg.get("type") == "hello":
                name = str(msg.get("name", ""))[:18].strip()
                if name:
                    p.name = name
            elif msg.get("type") == "input":
                p.input.update({
                    "left": bool(msg.get("left")),
                    "right": bool(msg.get("right")),
                    "jump": bool(msg.get("jump")),
                    "shoot": bool(msg.get("shoot")),
                    "active": bool(msg.get("active")),
                    "parry": bool(msg.get("parry")),
                    "reload": bool(msg.get("reload")),
                    "aim": float(msg.get("aim", p.aim)),
                })
            elif msg.get("type") == "choose_card" and self.phase == "cards":
                offer_id = msg.get("card")
                if not p.chosen_this_phase and p.alive is False:
                    self.choose_card_for_player(p, offer_id)
            elif msg.get("type") == "draft_action" and self.phase == "cards" and p.alive is False:
                offer_id = msg.get("card")
                action = msg.get("action")
                entry = self.find_offer_entry(p, offer_id)
                if not entry or p.draft_points <= 0 or p.chosen_this_phase or entry["deck"] in p.chosen_decks:
                    return
                card = entry["card"]
                if action == "burn" and not CARD_DEFS.get(card, {}).get("fusion_only"):
                    p.burned_cards.add(card)
                    p.frozen_cards = [f for f in p.frozen_cards if f != card]
                    p.draft_points -= 1
                    p.card_offer = [c for c in p.card_offer if c["offer_id"] != offer_id]
                    self.refill_offer_slot(p, entry["deck"])
                    self.log_msg(f"{p.name} queimou {CARD_DEFS[card]['name']}")
                elif action == "freeze":
                    if card in p.frozen_cards:
                        return
                    p.frozen_cards.append(card)
                    p.draft_points -= 1
                    self.log_msg(f"{p.name} congelou {CARD_DEFS[card]['name']}")
            elif msg.get("type") == "start_game":
                if pid != self.host_id:
                    return
                if self.phase != "lobby":
                    return
                if not self.can_start_game():
                    self.log_msg("Nao ha jogadores suficientes para iniciar")
                    return
                self.log_msg(f"{p.name} iniciou a partida")
                self.start_round()

    def start_round(self):
        self.phase = "playing"
        self.phase_until = 0
        self.round_winner = None
        self.bullets.clear()
        self.effects.clear()
        self.select_next_arena()
        self.roll_mutators()
        self.round_started_at = time.time()
        self.hazard_hits.clear()
        spawns = self.current_spawns()
        for p in self.players.values():
            p.reset_for_round(spawns[p.id])
            if self.has_mutator("speed_freaks"):
                p.rhythm_until = max(p.rhythm_until, time.time() + 999)
            if self.has_mutator("sudden_death"):
                p.hp = max(35, int(p.max_hp() * 0.55))
            if p.total_buffs["acorda_pedrinho"]:
                p.vx += random.choice([-1, 1]) * 5 * p.total_buffs["acorda_pedrinho"]
            if p.total_buffs["irineu"]:
                bonus = random.choice(CARD_KEYS)
                p.total_buffs[bonus] += 1
                self.log_msg(f"Irineu deu {CARD_DEFS[bonus]['name']} temporario para {p.name}")
            p.card_offer = []
            p.chosen_decks = set()
            p.chosen_this_phase = False
        self.log_msg(f"Rodada {self.round} come?ou em {self.current_arena['name']}!")

    def end_round(self, winner_pid):
        self.phase = "cards"
        self.phase_until = time.time() + ROUND_WAIT_SECONDS
        self.round_winner = winner_pid
        if winner_pid in self.players:
            self.players[winner_pid].wins += 1
            if self.players[winner_pid].total_buffs["faz_o_l"]:
                self.players[winner_pid].hp = min(self.players[winner_pid].max_hp(), self.players[winner_pid].hp + 20 * self.players[winner_pid].total_buffs["faz_o_l"])
            self.log_msg(f"{self.players[winner_pid].name} venceu a rodada {self.round}!")
        for p in self.players.values():
            if self.infinite_mode or p.id != winner_pid:
                p.card_offer = self.build_card_offer(p)
                p.chosen_this_phase = False
                p.chosen_decks = set()
            else:
                p.card_offer = []
                p.chosen_decks = set()
                p.chosen_this_phase = True
            if self.round % 5 == 0:
                p.draft_points += self.draft_point_gain()
        self.round += 1

    def rect_collision(self, x, y, radius, rect):
        rx, ry, rw, rh = rect
        nearest_x = max(rx, min(x, rx + rw))
        nearest_y = max(ry, min(y, ry + rh))
        return (x - nearest_x) ** 2 + (y - nearest_y) ** 2 <= radius ** 2

    def hazard_elapsed(self):
        return max(0.0, time.time() - self.round_started_at)

    def hazard_active(self, hazard):
        cycle = hazard.get("cycle")
        on_time = hazard.get("on_time")
        if not cycle or not on_time:
            return True
        uptime_scale = 1.0 if self.has_mutator("hazard_party") else 0.74
        return ((self.hazard_elapsed() + hazard.get("phase", 0.0)) % cycle) < (on_time * uptime_scale)

    def saw_position(self, hazard):
        travel = (math.sin((self.hazard_elapsed() + hazard.get("phase", 0.0)) * hazard.get("speed", 1.0)) + 1.0) / 2.0
        return (
            hazard["x1"] + (hazard["x2"] - hazard["x1"]) * travel,
            hazard["y1"] + (hazard["y2"] - hazard["y1"]) * travel,
        )

    def hazard_snapshot(self):
        snapshot = []
        for index, hazard in enumerate(self.current_arena.get("hazards", [])):
            data = {"id": index, "type": hazard["type"], "active": self.hazard_active(hazard)}
            if hazard["type"] == "saw":
                data.update({"x": round(self.saw_position(hazard)[0], 2), "y": round(self.saw_position(hazard)[1], 2), "radius": hazard["radius"]})
            elif hazard["type"] == "laser":
                data.update(hazard)
            elif hazard["type"] == "wind":
                data.update(hazard)
            elif hazard["type"] == "pulse":
                data.update(hazard)
            snapshot.append(data)
        return snapshot

    def hazard_tick_damage(self, pid, hazard_id, damage, cooldown):
        now = time.time()
        key = (pid, hazard_id)
        if now - self.hazard_hits.get(key, 0.0) < cooldown:
            return False
        self.hazard_hits[key] = now
        player = self.players.get(pid)
        if player and player.alive:
            player.hp -= damage
            if player.hp <= 0:
                player.hp = 0
                player.alive = False
                self.log_msg(f"{player.name} caiu no hazard")
        return True

    def steer_bullet(self, b, dt):
        owner = self.players.get(b.owner)
        if b.homing > 0:
            enemies = [p for p in self.players.values() if p.id != b.owner and p.alive]
            if enemies:
                target = min(enemies, key=lambda p: (p.x - b.x) ** 2 + (p.y - b.y) ** 2)
                desired = math.atan2(target.y - b.y, target.x - b.x)
                current = math.atan2(b.vy, b.vx)
                delta = (desired - current + math.pi) % (math.tau) - math.pi
                current += max(-b.homing * dt * 8, min(b.homing * dt * 8, delta))
                speed = max(0.1, math.hypot(b.vx, b.vy))
                b.vx = math.cos(current) * speed
                b.vy = math.sin(current) * speed
        if b.accelerate:
            b.vx *= 1.0 + b.accelerate * dt
            b.vy *= 1.0 + b.accelerate * dt
        if b.boomerang_delay and b.life < b.max_life - b.boomerang_delay:
            current = math.atan2(b.vy, b.vx)
            desired = math.atan2(b.start_y - b.y, b.start_x - b.x)
            delta = (desired - current + math.pi) % (math.tau) - math.pi
            current += max(-0.9 * dt * 8, min(0.9 * dt * 8, delta))
            speed = max(0.1, math.hypot(b.vx, b.vy))
            b.vx = math.cos(current) * speed
            b.vy = math.sin(current) * speed
        if owner and owner.total_buffs["ricochet_roulette"] and b.bounces > 0:
            b.homing = max(b.homing, 0.10 + 0.06 * owner.total_buffs["ricochet_roulette"])

    def bullet_explosion(self, b):
        if b.explode_radius <= 0:
            return
        owner = self.players.get(b.owner)
        self.spawn_effect("active_flash", b.x, b.y, duration=0.28, radius=b.explode_radius, color="toxic")
        for p in self.players.values():
            if not p.alive:
                continue
            dist = math.hypot(p.x - b.x, p.y - b.y)
            if dist <= b.explode_radius:
                splash = max(4, int(b.damage * (1 - dist / max(1, b.explode_radius)) * 0.45))
                p.hp -= splash
                self.stack_poison(p, 2.2, 3 + (owner.total_buffs["toxic_payload"] if owner else 1))
                if p.hp <= 0:
                    p.hp = 0
                    p.alive = False

    def split_bullet(self, b):
        if b.split <= 0:
            return
        if len(self.bullets) >= 220:
            return
        owner = self.players.get(b.owner)
        if not owner:
            return
        base = math.atan2(b.vy, b.vx)
        amount = min(4, 2 + b.split)
        amount = min(amount, max(0, 220 - len(self.bullets)))
        for i in range(amount):
            angle = base + (-0.38 + 0.76 * i / max(1, amount - 1))
            self.bullets.append(Bullet(
                b.owner,
                b.x,
                b.y,
                math.cos(angle) * max(7, math.hypot(b.vx, b.vy) * 0.82),
                math.sin(angle) * max(7, math.hypot(b.vx, b.vy) * 0.82),
                max(4, int(b.damage * 0.45)),
                owner.bullet_gravity(),
                max(0, b.bounces - 1),
                max(3, b.radius - 1),
                1.1,
                max(0, b.knockback * 0.4),
                homing=max(0.0, b.homing * 0.7),
                split=0,
                explode_radius=max(0, int(b.explode_radius * 0.55)),
                pierce=0,
                boomerang_delay=0.0,
                accelerate=0.0,
            ))

    def update_hazards(self, dt):
        damage_scale = 1.35 if self.has_mutator("hazard_party") else 1.0
        for hazard_id, hazard in enumerate(self.current_arena.get("hazards", [])):
            if not self.hazard_active(hazard):
                continue
            if hazard["type"] == "saw":
                hx, hy = self.saw_position(hazard)
                for p in self.players.values():
                    if not p.alive:
                        continue
                    if (p.x - hx) ** 2 + (p.y - hy) ** 2 <= (PLAYER_RADIUS + hazard["radius"]) ** 2:
                        if self.hazard_tick_damage(p.id, hazard_id, int(hazard["damage"] * damage_scale), hazard.get("cooldown", 0.4)):
                            dx = p.x - hx
                            dy = p.y - hy
                            dist = max(1.0, math.hypot(dx, dy))
                            p.x += dx / dist * 22
                            p.y += dy / dist * 14
            elif hazard["type"] == "laser":
                for p in self.players.values():
                    if not p.alive:
                        continue
                    if hazard["axis"] == "vertical":
                        inside = abs(p.x - hazard["x"]) <= hazard["thickness"] + PLAYER_RADIUS and hazard["y1"] <= p.y <= hazard["y2"]
                    else:
                        inside = abs(p.y - hazard["y"]) <= hazard["thickness"] + PLAYER_RADIUS and hazard["x1"] <= p.x <= hazard["x2"]
                    if inside:
                        self.hazard_tick_damage(p.id, hazard_id, int(hazard["damage"] * damage_scale), hazard.get("cooldown", 0.25))
            elif hazard["type"] == "wind":
                zone = (hazard["x"], hazard["y"], hazard["w"], hazard["h"])
                for p in self.players.values():
                    if p.alive and self.rect_collision(p.x, p.y, PLAYER_RADIUS, zone):
                        p.x += hazard.get("vx", 0.0)
                        p.y += hazard.get("vy", 0.0)
                        p.x = max(PLAYER_RADIUS, min(WIDTH - PLAYER_RADIUS, p.x))
                if self.has_mutator("hazard_party"):
                    for p in self.players.values():
                        if p.alive and self.rect_collision(p.x, p.y, PLAYER_RADIUS, zone):
                            p.vy += hazard.get("vy", 0.0) * 0.6
            elif hazard["type"] == "pulse":
                for p in self.players.values():
                    if not p.alive:
                        continue
                    dx = p.x - hazard["x"]
                    dy = p.y - hazard["y"]
                    dist = math.hypot(dx, dy)
                    if dist <= hazard["radius"]:
                        if self.hazard_tick_damage(p.id, hazard_id, int(hazard["damage"] * damage_scale), hazard.get("cooldown", 0.5)):
                            force = hazard.get("force", 12)
                            p.x += (dx / max(1.0, dist)) * force
                            p.y += (dy / max(1.0, dist)) * force * 0.6

    def resolve_player_world(self, p, previous=None):
        if not p.alive:
            return
        p.x = max(PLAYER_RADIUS, min(WIDTH - PLAYER_RADIUS, p.x))
        floor_y = FLOOR_Y - PLAYER_RADIUS
        if p.y >= floor_y:
            p.y = floor_y
            if p.vy > 0:
                p.vy = 0
            p.on_ground = True
            p.air_jumps_used = 0
        for rect in self.current_platforms():
            rx, ry, rw, rh = rect
            if not self.rect_collision(p.x, p.y, PLAYER_RADIUS, rect):
                continue
            handled = False
            if previous is not None:
                old_x, old_y = previous
                if old_y + PLAYER_RADIUS <= ry and p.vy >= 0:
                    p.y = ry - PLAYER_RADIUS
                    if p.vy > 0:
                        p.vy = 0
                    p.on_ground = True
                    p.air_jumps_used = 0
                    handled = True
                elif old_y - PLAYER_RADIUS >= ry + rh and p.vy < 0:
                    p.y = ry + rh + PLAYER_RADIUS
                    if p.vy < 0:
                        p.vy = 0
                    handled = True
                elif old_x < rx:
                    p.x = rx - PLAYER_RADIUS
                    handled = True
                elif old_x > rx + rw:
                    p.x = rx + rw + PLAYER_RADIUS
                    handled = True
            if handled:
                continue
            overlaps = {
                "left": abs((p.x + PLAYER_RADIUS) - rx),
                "right": abs((rx + rw) - (p.x - PLAYER_RADIUS)),
                "top": abs((p.y + PLAYER_RADIUS) - ry),
                "bottom": abs((ry + rh) - (p.y - PLAYER_RADIUS)),
            }
            side = min(overlaps, key=overlaps.get)
            if side == "top":
                p.y = ry - PLAYER_RADIUS
                if p.vy > 0:
                    p.vy = 0
                p.on_ground = True
                p.air_jumps_used = 0
            elif side == "bottom":
                p.y = ry + rh + PLAYER_RADIUS
                if p.vy < 0:
                    p.vy = 0
            elif side == "left":
                p.x = rx - PLAYER_RADIUS
            else:
                p.x = rx + rw + PLAYER_RADIUS

    def update_reload(self, p):
        now = time.time()
        if p.reload_until and now >= p.reload_until:
            p.ammo = p.max_ammo()
            p.reload_until = 0.0
            p.reload_started_at = 0.0
            p.shots_since_reload = 0
            if p.total_buffs["panic_pocket"]:
                self.stack_rhythm(p, 0.9 + 0.45 * p.total_buffs["panic_pocket"])

    def start_reload(self, p, force=False):
        if p.reload_until and not force:
            return
        if p.ammo >= p.max_ammo() and not force:
            return
        p.reload_started_at = time.time()
        p.reload_until = time.time() + p.reload_duration()

    def update_player(self, p, dt):
        if not p.alive:
            return
        inp = p.input
        self.update_reload(p)
        gravity_scale = 0.72 if self.has_mutator("low_gravity") else 1.0
        if time.time() < p.poison_until and p.poison_damage:
            p.hp -= p.poison_damage * dt
            if p.hp <= 0:
                p.hp = 0
                p.alive = False
                self.log_msg(f"{p.name} caiu no veneno")
        if p.regen_amount() and time.time() - p.last_regen >= 1.0:
            p.hp = min(p.max_hp(), p.hp + p.regen_amount())
            p.last_regen = time.time()
        if p.on_ground and p.total_buffs["touch_grass"] and time.time() - p.last_ground_heal >= 1.4:
            p.hp = min(p.max_hp(), p.hp + 4 * p.total_buffs["touch_grass"])
            p.last_ground_heal = time.time()
        p.aim = inp.get("aim", p.aim)
        target_vx = 0
        if inp.get("left"):
            target_vx -= p.speed()
        if inp.get("right"):
            target_vx += p.speed()
        p.vx = target_vx
        jump_pressed = inp.get("jump") and not p.was_jumping
        if jump_pressed:
            if p.on_ground:
                p.vy = -p.jump_power()
                p.on_ground = False
                p.air_jumps_used = 0
            elif p.air_jumps_used < p.total_buffs["air_jump"]:
                p.vy = -p.jump_power() * 0.92
                p.air_jumps_used += 1
        p.was_jumping = inp.get("jump")
        active_pressed = inp.get("active") and not p.was_active
        if active_pressed:
            self.try_active(p)
        p.was_active = inp.get("active")
        if inp.get("parry"):
            self.try_parry(p)
        if inp.get("reload"):
            self.start_reload(p)
        p.vy += GRAVITY * gravity_scale
        old_x, old_y = p.x, p.y
        p.x += p.vx
        p.y += p.vy
        p.on_ground = False
        self.resolve_player_world(p, previous=(old_x, old_y))
        if p.y > HEIGHT + 80:
            fall_resist = p.total_buffs["ney_malvadeza"] + p.total_buffs["vou_nada"]
            if fall_resist and random.random() < min(0.7, 0.18 * fall_resist):
                p.x, p.y = self.current_spawns()[p.id]
                p.vx = p.vy = 0
                p.hp = max(1, p.hp // 2)
            else:
                p.hp = 0
                p.alive = False
        if inp.get("shoot"):
            self.try_shoot(p)

    def spawn_bullet(self, owner, x, y, angle, speed, damage=None, radius=None, life=None, bounces=None, knockback=None):
        if self.has_mutator("bullet_hell"):
            speed *= 1.16
            life = (life if life is not None else owner.bullet_life()) * 1.15
            radius = (radius if radius is not None else owner.bullet_radius()) + 1
        life_value = life if life is not None else owner.bullet_life()
        radius_value = radius if radius is not None else owner.bullet_radius()
        damage_value = damage if damage is not None else owner.damage()
        bounces_value = bounces if bounces is not None else owner.bounces()
        knockback_value = knockback if knockback is not None else owner.knockback_strength()
        self.bullets.append(Bullet(
            owner.id,
            x,
            y,
            math.cos(angle) * speed,
            math.sin(angle) * speed,
            damage_value,
            owner.bullet_gravity(),
            bounces_value,
            radius_value,
            life_value,
            knockback_value,
            homing=owner.homing_strength(),
            split=owner.split_shots(),
            explode_radius=owner.explosion_radius(),
            pierce=owner.pierce_count(),
            boomerang_delay=owner.boomerang_delay(),
            accelerate=0.22 * owner.total_buffs["drone_guidance"],
            ghost_passes=owner.total_buffs["ghost_rounds"],
            bounce_scale=owner.total_buffs["bounce_house"],
        ))

    def try_active(self, p):
        now = time.time()
        if p.active_power() <= 0 or now < p.active_ready_at or not p.alive:
            return
        p.active_ready_at = now + p.active_cooldown()
        used = []

        if p.total_buffs["pix_misterioso"]:
            p.hp = min(p.max_hp(), p.hp + 24 * p.total_buffs["pix_misterioso"])
            used.append("Pix")
        if p.total_buffs["modo_turbo"]:
            force = 120 + 35 * p.total_buffs["modo_turbo"]
            p.x += math.cos(p.aim) * force
            p.y += math.sin(p.aim) * force * 0.65
            p.x = max(PLAYER_RADIUS, min(WIDTH - PLAYER_RADIUS, p.x))
            p.y = max(PLAYER_RADIUS, min(HEIGHT - PLAYER_RADIUS - 60, p.y))
            used.append("Turbo")
        if p.total_buffs["among_us"]:
            force = 90 + 45 * p.total_buffs["among_us"]
            p.x += math.cos(p.aim) * force
            p.y += math.sin(p.aim) * force
            p.x = max(PLAYER_RADIUS, min(WIDTH - PLAYER_RADIUS, p.x))
            p.y = max(PLAYER_RADIUS, min(HEIGHT - PLAYER_RADIUS - 60, p.y))
            used.append("Sus")
        if p.total_buffs["gemidao_zap"] or p.total_buffs["marilene"]:
            power = 20 * p.total_buffs["gemidao_zap"] + 16 * p.total_buffs["marilene"]
            for enemy in self.players.values():
                if enemy.id == p.id or not enemy.alive:
                    continue
                dx, dy = enemy.x - p.x, enemy.y - p.y
                dist = max(1, math.hypot(dx, dy))
                if dist < 310:
                    enemy.x += dx / dist * power
                    enemy.y += dy / dist * power * 0.35
            if p.total_buffs["marilene"]:
                p.hp = min(p.max_hp(), p.hp + 18 * p.total_buffs["marilene"])
            used.append("Onda")
        if p.total_buffs["buraco_negro"]:
            power = 26 * p.total_buffs["buraco_negro"]
            for enemy in self.players.values():
                if enemy.id != p.id and enemy.alive:
                    dx, dy = p.x - enemy.x, p.y - enemy.y
                    dist = max(1, math.hypot(dx, dy))
                    if dist < 420:
                        enemy.x += dx / dist * power
                        enemy.y += dy / dist * power * 0.45
            used.append("Buraco")
        if p.total_buffs["raio_trovao"]:
            enemies = [e for e in self.players.values() if e.id != p.id and e.alive]
            if enemies:
                strikes = min(len(enemies), p.total_buffs["raio_trovao"])
                targets = sorted(enemies, key=lambda e: (e.x - p.x) ** 2 + (e.y - p.y) ** 2)[:strikes]
                for target in targets:
                    target.hp -= 22 * p.total_buffs["raio_trovao"]
                    if target.hp <= 0:
                        target.hp = 0
                        target.alive = False
                used.append("Raio")
        if p.total_buffs["rizz"]:
            for enemy in self.players.values():
                if enemy.id != p.id and enemy.alive and (enemy.x - p.x) ** 2 + (enemy.y - p.y) ** 2 < 260 ** 2:
                    drain = 12 * p.total_buffs["rizz"]
                    enemy.hp -= drain
                    p.hp = min(p.max_hp(), p.hp + drain)
                    if enemy.hp <= 0:
                        enemy.hp = 0
                        enemy.alive = False
            used.append("Rizz")
        if p.total_buffs["skibidi"] or p.total_buffs["rickroll"] or p.total_buffs["grimace_shake"]:
            for enemy in self.players.values():
                if enemy.id == p.id or not enemy.alive:
                    continue
                if p.total_buffs["skibidi"]:
                    self.stack_slow(enemy, 1.8 + 0.7 * p.total_buffs["skibidi"], p.total_buffs["skibidi"])
                if p.total_buffs["rickroll"]:
                    self.stack_silence(enemy, 1.2 + 0.5 * p.total_buffs["rickroll"])
                if p.total_buffs["grimace_shake"]:
                    self.stack_poison(enemy, 2.2 + 0.6 * p.total_buffs["grimace_shake"], 3 * p.total_buffs["grimace_shake"])
            used.append("Debuff")
        if p.total_buffs["blox_fruits"]:
            amount = 8 + 4 * p.total_buffs["blox_fruits"]
            for i in range(amount):
                angle = (math.tau / amount) * i
                self.spawn_bullet(p, p.x, p.y, angle, 11.0, damage=max(6, p.damage() // 2), life=1.8)
            used.append("Blox")
        if p.total_buffs["zap_do_meteoro"]:
            for _ in range(5 + 2 * p.total_buffs["zap_do_meteoro"]):
                x = random.randint(80, WIDTH - 80)
                y = random.randint(-260, -40)
                self.bullets.append(Bullet(p.id, x, y, 0, 13 + random.random() * 5, p.damage(), 0.12, 0, p.bullet_radius() + 2, 2.5, p.knockback_strength()))
            used.append("Meteoro")
        if p.total_buffs["bluezao"]:
            amount = min(3, p.total_buffs["bluezao"])
            for i in range(amount):
                angle = p.aim + (i - (amount - 1) / 2) * 0.06
                self.spawn_bullet(p, p.x, p.y, angle, 8.5, damage=int(p.damage() * 1.6), radius=p.bullet_radius() + 14 + 3 * p.total_buffs["bluezao"], life=2.9, knockback=p.knockback_strength() + 16)
            used.append("Azul")
        if p.total_buffs["evil_kermit"]:
            self.stack_double_shot(p, 2.0 + 1.0 * p.total_buffs["evil_kermit"])
            used.append("Kermit")
        if p.total_buffs["numa_numa"]:
            self.stack_rhythm(p, 2.0 + 1.1 * p.total_buffs["numa_numa"])
            used.append("Numa")
        if p.total_buffs["john_cena"]:
            self.stack_intangible(p, 1.2 + 0.7 * p.total_buffs["john_cena"])
            p.x += math.cos(p.aim) * (100 + 35 * p.total_buffs["john_cena"])
            p.y += math.sin(p.aim) * (70 + 20 * p.total_buffs["john_cena"])
            p.x = max(PLAYER_RADIUS, min(WIDTH - PLAYER_RADIUS, p.x))
            p.y = max(PLAYER_RADIUS, min(HEIGHT - PLAYER_RADIUS - 60, p.y))
            used.append("Cena")
        if p.total_buffs["coffin_dance"]:
            threshold = 0.22 + 0.06 * p.total_buffs["coffin_dance"]
            for enemy in self.players.values():
                if enemy.id != p.id and enemy.alive and enemy.hp <= enemy.max_hp() * threshold:
                    enemy.hp = 0
                    enemy.alive = False
                    self.log_msg(f"{enemy.name} foi levado pelo Coffin Dance")
            used.append("Coffin")
        if p.total_buffs["wednesday_dance"]:
            for enemy in self.players.values():
                if enemy.id != p.id and enemy.alive:
                    enemy.vy = -10 - 2 * p.total_buffs["wednesday_dance"]
                    enemy.on_ground = False
            used.append("Dance")
        if p.total_buffs["harlem_shake"] and len(self.players) > 1:
            alive = [e for e in self.players.values() if e.alive]
            positions = [(e.x, e.y) for e in alive]
            random.shuffle(positions)
            for enemy, pos in zip(alive, positions):
                enemy.x, enemy.y = pos
            used.append("Shake")
        if p.total_buffs["backrooms"]:
            for enemy in self.players.values():
                if enemy.id != p.id and enemy.alive:
                    enemy.x = random.choice([80, WIDTH - 80])
                    enemy.y = random.randint(120, HEIGHT - 140)
            used.append("Backrooms")
        if p.total_buffs["do_you_know_da_wae"]:
            for enemy in self.players.values():
                if enemy.id != p.id and enemy.alive:
                    enemy.x += math.cos(p.aim) * 55 * p.total_buffs["do_you_know_da_wae"]
                    enemy.y += math.sin(p.aim) * 35 * p.total_buffs["do_you_know_da_wae"]
            used.append("Wae")
        if p.total_buffs["fanum_tax"]:
            for enemy in self.players.values():
                if enemy.id != p.id and enemy.alive:
                    tax = 8 * p.total_buffs["fanum_tax"]
                    enemy.hp -= tax
                    p.hp = min(p.max_hp(), p.hp + tax)
                    if enemy.active_ready_at > now:
                        enemy.active_ready_at += 1.5
                    if enemy.hp <= 0:
                        enemy.alive = False
            used.append("Tax")
        if p.total_buffs["ice_bucket"] or p.total_buffs["tide_pod"] or p.total_buffs["this_is_fine"]:
            for enemy in self.players.values():
                if enemy.id == p.id or not enemy.alive:
                    continue
                if p.total_buffs["ice_bucket"]:
                    self.stack_slow(enemy, 2.4 + 0.8 * p.total_buffs["ice_bucket"], p.total_buffs["ice_bucket"])
                    enemy.vy += 8
                if p.total_buffs["tide_pod"]:
                    self.stack_poison(enemy, 3.0 + 0.8 * p.total_buffs["tide_pod"], 5 * p.total_buffs["tide_pod"])
                if p.total_buffs["this_is_fine"]:
                    self.stack_poison(enemy, 1.8 + 0.5 * p.total_buffs["this_is_fine"], 4 * p.total_buffs["this_is_fine"])
            used.append("Caos")
        if p.total_buffs["keyboard_cat"] or p.total_buffs["woman_yelling"] or p.total_buffs["distracted_boyfriend"]:
            for enemy in self.players.values():
                if enemy.id == p.id or not enemy.alive:
                    continue
                self.stack_silence(enemy, 1.4 + 0.7 * p.total_buffs["keyboard_cat"] + 0.6 * p.total_buffs["woman_yelling"])
                if p.total_buffs["distracted_boyfriend"]:
                    enemy.aim += math.pi
                if p.total_buffs["woman_yelling"]:
                    enemy.x += random.choice([-1, 1]) * 55 * p.total_buffs["woman_yelling"]
            used.append("Grito")
        if p.total_buffs["nyan_cat"] or p.total_buffs["quandale_dingle"] or p.total_buffs["pedro_pedro"] or p.total_buffs["baby_shark"] or p.total_buffs["me_and_the_boys"]:
            amount = 4 * p.total_buffs["nyan_cat"] + 5 * p.total_buffs["quandale_dingle"] + 8 * p.total_buffs["pedro_pedro"] + 10 * p.total_buffs["baby_shark"] + 4 * p.total_buffs["me_and_the_boys"]
            amount = min(48, max(6, amount))
            for i in range(amount):
                angle = p.aim + (math.tau * i / amount if p.total_buffs["pedro_pedro"] or p.total_buffs["baby_shark"] else random.uniform(-1.2, 1.2))
                self.spawn_bullet(p, p.x, p.y, angle, 9 + random.random() * 7, damage=max(5, p.damage() // 2), radius=max(3, p.bullet_radius() - 1), life=2.2)
            used.append("Rajada")
        if p.total_buffs["salt_bae"] or p.total_buffs["area_51"] or p.total_buffs["all_your_base"]:
            amount = 5 * p.total_buffs["salt_bae"] + 8 * p.total_buffs["area_51"] + 10 * p.total_buffs["all_your_base"]
            for _ in range(min(45, amount)):
                x = random.randint(50, WIDTH - 50)
                y = random.randint(-300, -30)
                vx = random.uniform(-2, 2) + 3 * p.total_buffs["area_51"]
                self.bullets.append(Bullet(p.id, x, y, vx, 12 + random.random() * 6, p.damage(), 0.16, 0, p.bullet_radius() + 1, 2.7, p.knockback_strength()))
            used.append("Chuva")
        if p.total_buffs["obama_prism"]:
            beams = 3 + p.total_buffs["obama_prism"]
            for i in range(beams):
                angle = p.aim + (i - beams // 2) * 0.08
                self.spawn_bullet(p, p.x, p.y, angle, 24, damage=p.damage() + 8, radius=p.bullet_radius() + 4, life=1.1, bounces=0, knockback=p.knockback_strength() + 6)
            used.append("Prism")
        if p.total_buffs["mini_black_hole"] or p.total_buffs["supernova"]:
            pull_radius = 240 + 80 * p.total_buffs["mini_black_hole"] + 110 * p.total_buffs["supernova"]
            pull_strength = 28 * p.total_buffs["mini_black_hole"] + 38 * p.total_buffs["supernova"]
            self.spawn_effect("black_hole", p.x, p.y, duration=1.15, radius=pull_radius, color="void")
            for enemy in self.players.values():
                if not enemy.alive:
                    continue
                dx, dy = p.x - enemy.x, p.y - enemy.y
                dist = max(1, math.hypot(dx, dy))
                if dist <= pull_radius:
                    enemy.x += dx / dist * pull_strength
                    enemy.y += dy / dist * pull_strength * 0.55
                    if p.total_buffs["supernova"]:
                        blast = int((p.damage() * 0.9 + 12 * p.total_buffs["supernova"]) * (1 - dist / pull_radius * 0.55))
                        enemy.hp -= max(8, blast)
                        if enemy.hp <= 0:
                            enemy.hp = 0
                            enemy.alive = False
            used.append("Void")
        if p.total_buffs["brainrot_tornado"]:
            self.spawn_effect("tornado", p.x, p.y, duration=1.4, radius=320, color="storm")
            for enemy in self.players.values():
                if enemy.id == p.id or not enemy.alive:
                    continue
                dx, dy = enemy.x - p.x, enemy.y - p.y
                dist = max(1, math.hypot(dx, dy))
                if dist < 320:
                    swirl = 24 * p.total_buffs["brainrot_tornado"]
                    enemy.x += (-dy / dist) * swirl
                    enemy.y += (dx / dist) * swirl * 0.35 - 16
                    enemy.vy = min(enemy.vy, -10 - 2 * p.total_buffs["brainrot_tornado"])
                    self.stack_slow(enemy, 2.0 + 0.7 * p.total_buffs["brainrot_tornado"], p.total_buffs["brainrot_tornado"])
            used.append("Tornado")
        if p.total_buffs["tsar_bomba"]:
            cx, cy = WIDTH // 2, FLOOR_Y - 40
            self.spawn_effect("nuke", cx, cy, duration=1.25, radius=470, color="fire")
            for enemy in self.players.values():
                if not enemy.alive:
                    continue
                dist = max(1, math.hypot(enemy.x - cx, enemy.y - cy))
                if dist < 460:
                    damage = int((p.damage() * 1.2 + 26 * p.total_buffs["tsar_bomba"]) * (1 - min(0.7, dist / 540)))
                    enemy.hp -= max(10, damage)
                    enemy.x += (enemy.x - cx) / dist * (34 + 10 * p.total_buffs["tsar_bomba"])
                    enemy.y += (enemy.y - cy) / dist * (18 + 5 * p.total_buffs["tsar_bomba"])
                    if enemy.hp <= 0:
                        enemy.hp = 0
                        enemy.alive = False
            used.append("Nuke")
        if p.total_buffs["meteor_swarm"] or p.total_buffs["apocalypse_rain"]:
            amount = 10 * p.total_buffs["meteor_swarm"] + 16 * p.total_buffs["apocalypse_rain"]
            self.spawn_effect("sky_rain", WIDTH // 2, 70, duration=1.4, radius=WIDTH // 2, color="ember")
            for _ in range(min(70, amount)):
                x = random.randint(40, WIDTH - 40)
                y = random.randint(-360, -30)
                vx = random.uniform(-4, 4)
                vy = 13 + random.random() * 8
                damage = p.damage() + (8 if p.total_buffs["apocalypse_rain"] else 0)
                bullet = Bullet(p.id, x, y, vx, vy, damage, 0.10, 0, p.bullet_radius() + 3, 2.9, p.knockback_strength() + 3)
                self.bullets.append(bullet)
            used.append("Meteoro")
        if p.total_buffs["orbital_laser"]:
            thickness = 34 + 7 * p.total_buffs["orbital_laser"]
            beam_count = min(3, p.total_buffs["orbital_laser"])
            beam_angles = [p.aim + (i - (beam_count - 1) / 2) * 0.16 for i in range(beam_count)]
            for beam_angle in beam_angles:
                self.spawn_effect("orbital_laser", p.x, p.y, duration=0.8, angle=beam_angle, thickness=thickness, color="cyan")
                for enemy in self.players.values():
                    if not enemy.alive:
                        continue
                    dx = enemy.x - p.x
                    dy = enemy.y - p.y
                    line_dist = abs(dx * math.sin(beam_angle) - dy * math.cos(beam_angle))
                    along = dx * math.cos(beam_angle) + dy * math.sin(beam_angle)
                    if line_dist <= thickness and along > -40:
                        enemy.hp -= int(p.damage() * 0.82) + 12 * p.total_buffs["orbital_laser"]
                        self.stack_silence(enemy, 1.2)
                        if enemy.hp <= 0:
                            enemy.hp = 0
                            enemy.alive = False
            used.append("Laser")
        if p.total_buffs["world_freeze"]:
            self.spawn_effect("freeze_wave", WIDTH // 2, HEIGHT // 2, duration=1.0, radius=WIDTH // 2, color="ice")
            for enemy in self.players.values():
                if not enemy.alive:
                    continue
                self.stack_slow(enemy, 3.0 + 1.0 * p.total_buffs["world_freeze"], p.total_buffs["world_freeze"])
                enemy.vy += 10 + 2 * p.total_buffs["world_freeze"]
                self.stack_poison(enemy, 1.3 + 0.4 * p.total_buffs["world_freeze"], 2 * p.total_buffs["world_freeze"])
            used.append("Freeze")
        if p.total_buffs["void_rift"]:
            self.spawn_effect("void_rift", p.x, p.y, duration=1.0, radius=290, color="violet")
            for enemy in self.players.values():
                if not enemy.alive:
                    continue
                if (enemy.x - p.x) ** 2 + (enemy.y - p.y) ** 2 < 290 ** 2:
                    enemy.x = WIDTH - enemy.x
                    enemy.y = max(100, min(FLOOR_Y - 80, enemy.y + random.randint(-90, 90)))
                    enemy.hp -= 18 * p.total_buffs["void_rift"] + p.damage() // 2
                    if enemy.hp <= 0:
                        enemy.hp = 0
                        enemy.alive = False
            used.append("Rift")
        if p.total_buffs["quake_slam"]:
            self.spawn_effect("quake", p.x, p.y, duration=0.9, radius=340, color="earth")
            for enemy in self.players.values():
                if not enemy.alive:
                    continue
                dx, dy = enemy.x - p.x, enemy.y - p.y
                dist = max(1, math.hypot(dx, dy))
                if dist < 340:
                    enemy.vy = -14 - 2 * p.total_buffs["quake_slam"]
                    enemy.x += dx / dist * (28 + 8 * p.total_buffs["quake_slam"])
                    enemy.hp -= 10 + 10 * p.total_buffs["quake_slam"]
                    if enemy.hp <= 0:
                        enemy.hp = 0
                        enemy.alive = False
            used.append("Quake")
        if p.total_buffs["guided_swarm"]:
            self.spawn_effect("active_flash", p.x, p.y, duration=0.5, radius=120, color="cyan", sound="swarm")
            for i in range(6 + 2 * p.total_buffs["guided_swarm"]):
                angle = p.aim + random.uniform(-0.8, 0.8)
                speed = 9 + random.random() * 4
                bullet = Bullet(
                    p.id,
                    p.x,
                    p.y,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    max(6, p.damage() // 2),
                    p.bullet_gravity(),
                    p.bounces(),
                    max(3, p.bullet_radius() - 2),
                    2.6,
                    max(1, p.knockback_strength() * 0.45),
                    homing=0.38 + 0.10 * p.total_buffs["guided_swarm"],
                    split=0,
                    explode_radius=0,
                    pierce=0,
                    boomerang_delay=0.0,
                    accelerate=0.18,
                )
                self.bullets.append(bullet)
            used.append("Swarm")
        if p.total_buffs["remote_detonator"]:
            detonated = 0
            for bullet in self.bullets:
                if bullet.owner == p.id:
                    bullet.life = 0
                    bullet.explode_radius += 36 + 18 * p.total_buffs["remote_detonator"]
                    bullet.damage = int(bullet.damage * (1.0 + 0.12 * p.total_buffs["remote_detonator"]))
                    detonated += 1
            if detonated:
                self.spawn_effect("active_flash", p.x, p.y, duration=0.5, radius=140, color="ember", sound="remote_detonator")
                used.append("Remote")
        if p.total_buffs["magnet_trigger"]:
            for bullet in self.bullets:
                if bullet.owner == p.id:
                    bullet.homing += 0.18 + 0.10 * p.total_buffs["magnet_trigger"]
                    bullet.accelerate += 0.08 + 0.04 * p.total_buffs["magnet_trigger"]
            self.spawn_effect("orbital_laser", p.x, p.y, duration=0.35, angle=p.aim, thickness=18, color="cyan", sound="active")
            used.append("Magnet")
        if p.total_buffs["portal_storm"]:
            amount = 3 + 2 * p.total_buffs["portal_storm"]
            for i in range(amount):
                y = random.randint(120, FLOOR_Y - 80)
                self.spawn_bullet(p, 20, y, 0.0, 14, damage=max(6, p.damage() // 2), life=1.9)
                self.spawn_bullet(p, WIDTH - 20, y, math.pi, 14, damage=max(6, p.damage() // 2), life=1.9)
            self.spawn_effect("void_rift", WIDTH // 2, FLOOR_Y // 2, duration=0.7, radius=WIDTH // 2, color="violet", sound="portal_storm")
            used.append("Portal")
        if p.total_buffs["omega_event_horizon"]:
            radius = 420
            self.spawn_effect("black_hole", p.x, p.y, duration=1.5, radius=radius, color="violet", sound="omega_event_horizon")
            self.spawn_effect("nuke", p.x, p.y, duration=1.1, radius=radius, color="void")
            for enemy in self.players.values():
                if not enemy.alive:
                    continue
                dx, dy = p.x - enemy.x, p.y - enemy.y
                dist = max(1, math.hypot(dx, dy))
                if dist < radius:
                    enemy.x += dx / dist * 52
                    enemy.y += dy / dist * 28
                    enemy.hp -= p.damage() + 28
                    self.stack_poison(enemy, 2.8, 6)
                    if enemy.hp <= 0:
                        enemy.hp = 0
                        enemy.alive = False
            used.append("Omega")
        if p.total_buffs["judgement_day"]:
            self.spawn_effect("nuke", WIDTH // 2, FLOOR_Y - 40, duration=1.2, radius=520, color="fire", sound="judgement_day")
            self.spawn_effect("orbital_laser", p.x, p.y, duration=1.0, angle=p.aim, thickness=56, color="gold")
            self.spawn_effect("sky_rain", WIDTH // 2, 60, duration=1.8, radius=WIDTH // 2, color="ember")
            for _ in range(28):
                x = random.randint(40, WIDTH - 40)
                y = random.randint(-380, -20)
                self.bullets.append(Bullet(p.id, x, y, random.uniform(-4, 4), 15 + random.random() * 7, p.damage() + 12, 0.08, 0, p.bullet_radius() + 4, 3.2, p.knockback_strength() + 4))
            for enemy in self.players.values():
                if not enemy.alive:
                    continue
                enemy.hp -= 20
                if enemy.hp <= 0:
                    enemy.hp = 0
                    enemy.alive = False
            used.append("Judge")
        if p.total_buffs["tempest_cataclysm"]:
            self.spawn_effect("tornado", p.x, p.y, duration=1.6, radius=360, color="ice", sound="tempest_cataclysm")
            self.spawn_effect("freeze_wave", p.x, p.y, duration=1.0, radius=360, color="ice")
            self.spawn_effect("quake", p.x, p.y, duration=1.0, radius=360, color="earth")
            for enemy in self.players.values():
                if not enemy.alive:
                    continue
                dx, dy = enemy.x - p.x, enemy.y - p.y
                dist = max(1, math.hypot(dx, dy))
                if dist < 360:
                    self.stack_slow(enemy, 4.5, 3 + p.total_buffs["tempest_cataclysm"])
                    enemy.vy = -18
                    enemy.x += (-dy / dist) * 36
                    enemy.y += (dx / dist) * 10
                    enemy.hp -= 18 + p.damage() // 2
                    if enemy.hp <= 0:
                        enemy.hp = 0
                        enemy.alive = False
            used.append("Tempest")

        if used:
            self.spawn_effect("active_flash", p.x, p.y, duration=0.45, radius=90 + 12 * len(used), color="white")
            self.log_msg(f"{p.name} usou ativa: {'+'.join(used[:3])}")

    def try_parry(self, p):
        now = time.time()
        if not p.alive or now < p.parry_ready_at:
            return
        p.parry_until = now + p.parry_duration()
        p.parry_ready_at = now + p.parry_cooldown() * (0.45 if self.has_mutator("parry_mania") else 1.0)

    def reflect_bullet(self, p, b, owner):
        now = time.time()
        speed = max(8.0, math.hypot(b.vx, b.vy) * p.parry_speed_multiplier())
        angle = p.aim
        b.owner = p.id
        b.x = p.x + math.cos(angle) * (PLAYER_RADIUS + b.radius + 4)
        b.y = p.y + math.sin(angle) * (PLAYER_RADIUS + b.radius + 4)
        b.vx = math.cos(angle) * speed
        b.vy = math.sin(angle) * speed
        b.damage = max(1, int(b.damage * p.parry_damage_multiplier()))
        b.life = max(b.life, 0.55)
        b.bounces += p.total_buffs["spiderman_pointing"]
        b.knockback += 6 * p.total_buffs["spiderman_pointing"] + 8 * p.total_buffs["bonk"]
        b.reflected = True
        if p.total_buffs["call_an_ambulance"]:
            self.stack_parry_empower(p, 2.5 + 1.0 * p.total_buffs["call_an_ambulance"])
        if p.total_buffs["mans_not_hot"]:
            p.hp = min(p.max_hp(), p.hp + 6 * p.total_buffs["mans_not_hot"])
            self.stack_rhythm(p, 1.2 + 0.5 * p.total_buffs["mans_not_hot"])
        if owner and owner.alive and p.total_buffs["omae_wa"]:
            self.stack_silence(owner, 0.8 + 0.35 * p.total_buffs["omae_wa"])
            self.stack_slow(owner, 1.1 + 0.45 * p.total_buffs["omae_wa"], p.total_buffs["omae_wa"])
        self.spawn_effect("parry_burst", p.x, p.y, duration=0.35, radius=p.parry_guard_radius() + 10, color="gold")
        self.log_msg(f"{p.name} refletiu um tiro")

    def try_shoot(self, p):
        now = time.time()
        if now < p.silenced_until:
            return
        self.update_reload(p)
        if p.reload_until:
            return
        if p.ammo <= 0:
            self.start_reload(p)
            return
        if now - p.last_shot < p.fire_cooldown():
            return
        cooked = p.total_buffs["let_him_cook"] and now - p.last_shot > 2.0
        first_round = p.shots_since_reload == 0
        last_round = p.ammo == 1
        free_shot = p.total_buffs["bottomless_meme"] and random.random() < min(0.6, 0.14 * p.total_buffs["bottomless_meme"])
        p.last_shot = now
        if not free_shot:
            p.ammo = max(0, p.ammo - 1)
        p.shots_since_reload += 1
        base = p.aim
        angles = [base]
        if self.has_mutator("bullet_hell"):
            angles += [base - 0.08, base + 0.08]
        extra_angles = []
        if p.total_buffs["buckshot_mayhem"]:
            pellets = 2 + 2 * p.total_buffs["buckshot_mayhem"]
            spread = 0.22 + 0.03 * p.total_buffs["buckshot_mayhem"]
            extra_angles += [base + random.uniform(-spread, spread) for _ in range(pellets)]
        if p.total_buffs["multishot"] > 0:
            spread = 0.13
            extra_angles += [base - spread, base, base + spread]
        if time.time() < p.double_shot_until:
            extra_angles += [a + 0.07 for a in (extra_angles or angles)]
        if p.total_buffs["tata_foda"] and random.random() < min(0.65, 0.18 * p.total_buffs["tata_foda"]):
            extra_angles += [base - 0.26, base + 0.26]
        if p.total_buffs["keyboard_smash"]:
            spread = min(0.35, 0.04 * p.total_buffs["keyboard_smash"])
            extra_angles += [base + random.uniform(-spread, spread)]
        if extra_angles:
            angles = extra_angles
        for a in angles:
            speed = p.bullet_speed()
            sx = p.x + math.cos(a) * 25
            sy = p.y + math.sin(a) * 25
            damage = p.damage()
            if first_round and p.total_buffs["golden_mag"]:
                speed *= 1.10 + 0.06 * p.total_buffs["golden_mag"]
                damage = int(damage * (1.22 + 0.10 * p.total_buffs["golden_mag"]))
            if last_round and p.total_buffs["one_tap"]:
                damage = int(damage * (1.35 + 0.16 * p.total_buffs["one_tap"]))
            if cooked:
                damage = int(damage * (1.7 + 0.25 * p.total_buffs["let_him_cook"]))
            if time.time() < p.parry_empower_until:
                damage = int(damage * (1.45 + 0.20 * p.total_buffs["call_an_ambulance"]))
                p.parry_empower_until = 0.0
            bullet_life = None
            bullet_radius = None
            if p.total_buffs["buckshot_mayhem"]:
                damage = max(4, int(damage * 0.42))
                speed *= 0.92
                bullet_life = p.bullet_life() * 0.6
                bullet_radius = max(3, p.bullet_radius() - 1)
            self.spawn_bullet(p, sx, sy, a, speed, damage=damage, life=bullet_life, radius=bullet_radius)
        if p.ammo <= 0:
            self.start_reload(p, force=True)

    def update_bullets(self, dt):
        keep = []
        for b in self.bullets:
            old_x, old_y = b.x, b.y
            b.life -= dt
            self.steer_bullet(b, dt)
            b.vy += b.grav
            b.x += b.vx
            b.y += b.vy
            hit = False
            bounced = False
            if b.x < 0 or b.x > WIDTH:
                if b.ghost_passes > 0:
                    b.ghost_passes -= 1
                    b.x = max(1, min(WIDTH - 1, b.x))
                elif b.bounces > 0:
                    b.bounces -= 1
                    b.vx *= -0.75
                    b.x = max(0, min(WIDTH, b.x))
                    bounced = True
                else:
                    hit = True
            if b.y > HEIGHT:
                if b.bounces > 0:
                    if b.ghost_passes > 0:
                        b.ghost_passes -= 1
                        b.y = max(1, min(HEIGHT - 1, b.y))
                    elif b.y > 0:
                        b.bounces -= 1
                        b.vy *= -0.72
                        b.y = min(HEIGHT, b.y)
                        bounced = True
                    else:
                        hit = True
                elif b.ghost_passes > 0:
                    b.ghost_passes -= 1
                    b.y = max(1, min(HEIGHT - 1, b.y))
                else:
                    hit = True
            for rect in self.current_platforms():
                if self.rect_collision(b.x, b.y, b.radius, rect):
                    if b.ghost_passes > 0:
                        b.ghost_passes -= 1
                        break
                    if b.bounces > 0:
                        b.bounces -= 1
                        rx, ry, rw, rh = rect
                        from_above = old_y + b.radius <= ry and b.vy >= 0
                        from_below = old_y - b.radius >= ry + rh and b.vy <= 0
                        from_left = old_x + b.radius <= rx and b.vx >= 0
                        from_right = old_x - b.radius >= rx + rw and b.vx <= 0
                        if from_above:
                            b.y = ry - b.radius - 1
                            b.vy = -abs(b.vy) * 0.72
                            b.vx *= 0.90
                        elif from_below:
                            b.y = ry + rh + b.radius + 1
                            b.vy = abs(b.vy) * 0.72
                            b.vx *= 0.90
                        elif from_left:
                            b.x = rx - b.radius - 1
                            b.vx = -abs(b.vx) * 0.75
                            b.vy *= 0.92
                        elif from_right:
                            b.x = rx + rw + b.radius + 1
                            b.vx = abs(b.vx) * 0.75
                            b.vy *= 0.92
                        else:
                            overlap_x = min(abs((b.x + b.radius) - rx), abs((rx + rw) - (b.x - b.radius)))
                            overlap_y = min(abs((b.y + b.radius) - ry), abs((ry + rh) - (b.y - b.radius)))
                            if overlap_y <= overlap_x:
                                if old_y <= ry:
                                    b.y = ry - b.radius - 1
                                    b.vy = -abs(b.vy) * 0.72
                                else:
                                    b.y = ry + rh + b.radius + 1
                                    b.vy = abs(b.vy) * 0.72
                                b.vx *= 0.90
                            else:
                                if old_x <= rx:
                                    b.x = rx - b.radius - 1
                                    b.vx = -abs(b.vx) * 0.75
                                else:
                                    b.x = rx + rw + b.radius + 1
                                    b.vx = abs(b.vx) * 0.75
                                b.vy *= 0.92
                        if b.bounce_scale:
                            b.damage = int(b.damage * (1.10 + 0.05 * b.bounce_scale))
                            b.vx *= 1.03 + 0.02 * b.bounce_scale
                            b.vy *= 1.03 + 0.02 * b.bounce_scale
                        bounced = True
                    else:
                        hit = True
                    break
            if bounced:
                self.spawn_effect("active_flash", b.x, b.y, duration=0.12, radius=24 + b.radius * 2, color="cyan")
            if not hit:
                for p in self.players.values():
                    if not p.alive:
                        continue
                    if p.id == b.owner and time.time() - b.created_at < 0.12:
                        continue
                    guard_radius = p.parry_guard_radius() if time.time() < p.parry_until else PLAYER_RADIUS
                    if (p.x - b.x) ** 2 + (p.y - b.y) ** 2 <= (guard_radius + b.radius) ** 2:
                        owner = self.players.get(b.owner)
                        if time.time() < p.parry_until:
                            self.reflect_bullet(p, b, owner)
                            break
                        if time.time() < p.intangible_until:
                            hit = True
                            break
                        if p.total_buffs["liminal_space"] and random.random() < min(0.45, 0.12 * p.total_buffs["liminal_space"]):
                            self.stack_intangible(p, 1.2)
                            self.log_msg(f"{p.name} entrou no Liminal Space")
                            hit = True
                            break
                        if p.dodge_chance() and random.random() < p.dodge_chance():
                            self.log_msg(f"{p.name} desviou do tiro")
                            hit = True
                            break
                        damage = max(1, int(b.damage * p.armor_multiplier()))
                        if p.total_buffs["trollface"] and owner and random.random() < min(0.40, 0.10 * p.total_buffs["trollface"]):
                            owner.hp -= damage
                            self.log_msg(f"{p.name} devolveu dano no Trollface")
                            hit = True
                            break
                        if p.total_buffs["surprised_pikachu"] and owner and random.random() < min(0.35, 0.09 * p.total_buffs["surprised_pikachu"]):
                            owner.hp -= max(1, damage // 2)
                        if owner and owner.crit_chance() and random.random() < owner.crit_chance():
                            damage = int(damage * owner.crit_multiplier())
                            self.log_msg(f"{owner.name} acertou critico!")
                        if owner and owner.total_buffs["free_fire"] and p.hp <= p.max_hp() * 0.35:
                            damage = int(damage * (1.35 + 0.12 * owner.total_buffs["free_fire"]))
                        if owner and owner.total_buffs["galvao"] and p.wins >= owner.wins:
                            damage = int(damage * (1.10 + 0.08 * owner.total_buffs["galvao"]))
                        if owner and owner.total_buffs["charlie_bit_my_finger"] and (owner.x - p.x) ** 2 + (owner.y - p.y) ** 2 < 220 ** 2:
                            damage = int(damage * (1.12 + 0.06 * owner.total_buffs["charlie_bit_my_finger"]))
                        p.hp -= damage
                        self.spawn_effect("active_flash", b.x, b.y, duration=0.14, radius=18 + b.radius * 2, color="white")
                        if b.knockback:
                            dist = max(1, math.hypot(p.x - b.x, p.y - b.y))
                            p.x += ((p.x - b.x) / dist) * b.knockback
                            p.y += ((p.y - b.y) / dist) * b.knockback * 0.45
                            p.x = max(PLAYER_RADIUS, min(WIDTH - PLAYER_RADIUS, p.x))
                        if owner and owner.total_buffs["disaster_girl"]:
                            self.stack_poison(p, 1.6 + 0.5 * owner.total_buffs["disaster_girl"], 3 * owner.total_buffs["disaster_girl"])
                        if owner and owner.total_buffs["parasite_rounds"]:
                            self.stack_poison(p, 2.5, 2 + owner.total_buffs["parasite_rounds"])
                            owner.active_ready_at = max(time.time(), owner.active_ready_at - 0.55 * owner.total_buffs["parasite_rounds"])
                        if b.reflected and owner and owner.total_buffs["bonk"]:
                            self.stack_slow(p, 0.7 + 0.4 * owner.total_buffs["bonk"], owner.total_buffs["bonk"])
                        if owner and owner.alive and owner.lifesteal_ratio():
                            owner.hp = min(owner.max_hp(), owner.hp + int(damage * owner.lifesteal_ratio()))
                        if owner and owner.total_buffs["npc_streamer"]:
                            owner.active_ready_at = max(time.time(), owner.active_ready_at - 0.45 * owner.total_buffs["npc_streamer"])
                        if not b.exploded:
                            self.bullet_explosion(b)
                            b.exploded = True
                        if p.hp <= 0:
                            save_chance = min(0.85, 0.18 * p.total_buffs["so_fe"] + 0.16 * p.total_buffs["delulu"] + 0.10 * p.total_buffs["one_does_not"] + 0.12 * p.total_buffs["ultra_instinct"])
                            if p.total_buffs["selo_anti_noob"] and not p.revive_used:
                                p.revive_used = True
                                p.hp = max(1, p.max_hp() // 3)
                                self.log_msg(f"{p.name} reviveu no Selo Anti-Noob")
                            elif save_chance and random.random() < save_chance:
                                p.hp = 1
                                self.log_msg(f"{p.name} sobreviveu no absurdo")
                            else:
                                if owner and owner.alive and owner.total_buffs["scavenger_hunt"]:
                                    owner.ammo = min(owner.max_ammo(), owner.ammo + owner.total_buffs["scavenger_hunt"])
                                if p.total_buffs["press_f"]:
                                    amount = min(24, 6 + 3 * p.total_buffs["press_f"])
                                    for i in range(amount):
                                        self.spawn_bullet(p, p.x, p.y, math.tau * i / amount, 10, damage=max(5, p.damage() // 2), life=1.6)
                                p.hp = 0
                                p.alive = False
                                self.log_msg(f"{p.name} foi eliminado")
                        if b.pierce > 0:
                            b.pierce -= 1
                            b.damage = max(1, int(b.damage * 0.72))
                            continue
                        hit = True
                        break
            if hit or b.life <= 0:
                if not b.exploded:
                    self.bullet_explosion(b)
                    b.exploded = True
                self.split_bullet(b)
            if b.life > 0 and not hit:
                keep.append(b)
        self.bullets = keep

    def maybe_finish_round(self):
        alive = [p for p in self.players.values() if p.alive]
        if self.phase == "playing" and len(self.players) >= self.min_players:
            solo_test_running = self.allow_solo and len(self.players) == 1 and len(alive) == 1
            winner = alive[0].id if alive else None
            if winner is not None and not solo_test_running and len(alive) <= 1:
                self.end_round(winner)
            else:
                if not alive:
                    if self.allow_solo and len(self.players) == 1:
                        self.end_round(None)
                    else:
                        self.start_round()
        if self.phase == "cards":
            pending_players = [p for p in self.players.values() if p.card_offer]
            all_chosen = all(p.chosen_this_phase for p in pending_players)
            if time.time() >= self.phase_until:
                for p in pending_players:
                    if not p.chosen_this_phase:
                        self.auto_choose_missing_cards(p)
                all_chosen = all(p.chosen_this_phase for p in pending_players)
            if time.time() >= self.phase_until or all_chosen:
                self.start_round()

    def tick(self, dt):
        with self.lock:
            now = time.time()
            self.effects = [effect for effect in self.effects if effect.get("until", now) > now]
            if self.phase == "playing":
                for p in list(self.players.values()):
                    self.update_player(p, dt)
                self.update_hazards(dt)
                self.update_bullets(dt)
                for p in self.players.values():
                    if p.alive:
                        self.resolve_player_world(p)
            self.maybe_finish_round()
            self.broadcast()

    def state_for(self, pid):
        players = []
        for p in self.players.values():
            players.append({
                "id": p.id,
                "name": p.name,
                "x": round(p.x, 2),
                "y": round(p.y, 2),
                "hp": p.hp,
                "max_hp": p.max_hp(),
                "alive": p.alive,
                "wins": p.wins,
                "color": p.color,
                "aim": p.aim,
                "buffs": {k: v for k, v in p.total_buffs.items() if v},
                "chosen": p.chosen_this_phase,
                "last_picked_special": p.last_picked_special,
                "last_picked_fusion": p.last_picked_fusion,
                "active_ready_at": p.active_ready_at,
                "ammo": p.ammo,
                "max_ammo": p.max_ammo(),
                "reload_until": p.reload_until,
                "reload_started_at": p.reload_started_at,
                "parry_ready_at": p.parry_ready_at,
                "parry_until": p.parry_until,
            })
        me = self.players.get(pid)
        fusion_map = {recipe["result"]: list(recipe["parts"]) for recipe in FUSION_RECIPES}
        cards = []
        if me:
            for card in me.card_offer:
                cards.append({
                    "id": card["card"],
                    "offer_id": card["offer_id"],
                    "deck": card["deck"],
                    "frozen": card["card"] in me.last_offer_frozen,
                    "fusion": card["card"] in fusion_map,
                    "parts": fusion_map.get(card["card"], []),
                    "special": card["card"] in SPECIAL_CARDS,
                })
        return {
            "type": "state",
            "your_id": pid,
            "host_id": self.host_id,
            "can_start": self.can_start_game(),
            "required_players": self.required_players_to_start(),
            "room_code": self.room_code,
            "phase": self.phase,
            "round": self.round,
            "phase_until": self.phase_until,
            "winner": self.round_winner,
            "infinite": self.infinite_mode,
            "mutators_enabled": self.mutators_enabled,
            "more_cards_enabled": self.more_cards_enabled,
            "mutators": [m["name"] for m in GLOBAL_MUTATORS if m["id"] in self.active_mutators],
            "players": players,
            "bullets": [{"x": round(b.x, 2), "y": round(b.y, 2), "owner": b.owner, "radius": b.radius} for b in self.bullets],
            "effects": self.effects,
            "platforms": self.current_platforms(),
            "arena": {"id": self.current_arena["id"], "name": self.current_arena["name"], "colors": self.current_arena.get("colors", {})},
            "hazards": self.hazard_snapshot(),
            "cards": cards,
            "draft_points": me.draft_points if me else 0,
            "draft_deck_count": self.draft_deck_count(),
            "chosen_decks": sorted(me.chosen_decks) if me else [],
            "card_defs": CARD_DEFS,
            "fusion_recipes": fusion_map,
            "log": self.log,
        }

    def broadcast(self):
        dead = []
        for pid, conn in list(self.clients.items()):
            try:
                send_json(conn, self.state_for(pid))
            except Exception:
                dead.append(pid)
        for pid in dead:
            self.clients.pop(pid, None)
            if pid in self.players:
                self.players[pid].alive = False

    def loop(self):
        last = time.time()
        while self.running:
            now = time.time()
            dt = min(0.05, now - last)
            last = now
            self.tick(dt)
            time.sleep(1 / FPS)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--room-code", default="")
    parser.add_argument("--allow-solo", action="store_true")
    parser.add_argument("--infinite", action="store_true")
    parser.add_argument("--mutators", action="store_true")
    parser.add_argument("--more-cards", action="store_true")
    args = parser.parse_args()
    game = GameServer(args.room_code, args.allow_solo, args.infinite, args.mutators, args.more_cards)
    threading.Thread(target=game.start_socket, daemon=True).start()
    game.loop()
