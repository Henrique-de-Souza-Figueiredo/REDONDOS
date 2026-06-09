import json

WIDTH = 1280
HEIGHT = 720
FPS = 60
PLAYER_RADIUS = 18
BULLET_RADIUS = 5
FLOOR_Y = 660
GRAVITY = 0.55
BULLET_GRAVITY = 0.32
PLAYER_COLORS = [
    (240, 72, 72),
    (72, 145, 240),
    (82, 210, 110),
    (235, 205, 80),
]
CARD_DEFS = {
    "speed": {
        "name": "Tralalero Tralala",
        "desc": "PASSIVA: +18% velocidade de movimento",
    },
    "damage": {
        "name": "Bombardiro Crocodilo",
        "desc": "PASSIVA: +20% dano dos tiros",
    },
    "jump": {
        "name": "Tung Tung Sahur",
        "desc": "PASSIVA: +18% forca do pulo",
    },
    "firerate": {
        "name": "6-7 Doot Doot",
        "desc": "PASSIVA: atira e recarrega mais rapido",
    },
    "multishot": {
        "name": "Brr Brr Patapim",
        "desc": "PASSIVA: dispara 3 balas em leque gastando 1 municao",
    },
    "shield": {
        "name": "Ballerina Cappuccina",
        "desc": "PASSIVA: +25 HP no comeco das rodadas",
    },
    "bullet_grav": {
        "name": "Trippi Troppi",
        "desc": "PASSIVA: menos queda de bala",
    },
    "bounce": {
        "name": "No La Polizia",
        "desc": "PASSIVA: balas quicam nas paredes, no chao e nas plataformas",
    },
    "bullet_speed": {
        "name": "Labubu Energy",
        "desc": "PASSIVA: +16% velocidade dos tiros",
    },
    "big_bullets": {
        "name": "Dubai Chocolate",
        "desc": "PASSIVA: balas maiores e mais faceis de acertar",
    },
    "armor": {
        "name": "But You Cannot Prove It",
        "desc": "PASSIVA: recebe menos dano",
    },
    "lifesteal": {
        "name": "Italian Brainrot",
        "desc": "PASSIVA: recupera vida ao acertar tiros",
    },
    "regen": {
        "name": "Pretty Little Baby",
        "desc": "PASSIVA: regenera vida aos poucos",
    },
    "air_jump": {
        "name": "Glorp Mode",
        "desc": "PASSIVA: ganha pulos extras no ar",
    },
    "bora_bill": {
        "name": "Bora Bill",
        "desc": "PASSIVA: +12% velocidade e arranque",
    },
    "receba": {
        "name": "Receba",
        "desc": "PASSIVA: chance de tiro critico",
    },
    "caneta_azul": {
        "name": "Caneta Azul",
        "desc": "PASSIVA: +1 municao e tiros duram mais tempo na arena",
    },
    "calma_calabreso": {
        "name": "Calma Calabreso",
        "desc": "PASSIVA: fica mais resistente com pouca vida",
    },
    "casca_de_bala": {
        "name": "Casca de Bala",
        "desc": "PASSIVA: tiros mais fortes e mais rapidos",
    },
    "luva_pedreiro": {
        "name": "Luva de Pedreiro",
        "desc": "PASSIVA: acertos empurram o inimigo",
    },
    "la_ele": {
        "name": "La Ele",
        "desc": "PASSIVA: chance de desviar de um tiro",
    },
    "xou_xuxa": {
        "name": "Que Xou da Xuxa",
        "desc": "PASSIVA: mais vida maxima por rodada",
    },
    "ratinho": {
        "name": "Rapaz",
        "desc": "PASSIVA: +10% dano e +10% tamanho da bala",
    },
    "faustao": {
        "name": "Errou",
        "desc": "PASSIVA: seus criticos ficam mais fortes",
    },
    "ney_malvadeza": {
        "name": "Neymar Caindo",
        "desc": "PASSIVA: mais esquiva e menos dano de queda",
    },
    "gemidao_zap": {
        "name": "Gemidao do Zap",
        "desc": "ATIVA: empurra todo mundo perto",
    },
    "pix_misterioso": {
        "name": "Pix Misterioso",
        "desc": "ATIVA: cura instantanea em voce",
    },
    "zap_do_meteoro": {
        "name": "Zap do Meteoro",
        "desc": "ATIVA: chuva de projeteis do alto",
    },
    "modo_turbo": {
        "name": "Modo Turbo",
        "desc": "ATIVA: dash brutal na mira",
    },
    "buraco_negro": {
        "name": "Buraco Negro do Zap",
        "desc": "ATIVA: puxa inimigos para voce",
    },
    "raio_trovao": {
        "name": "Raio do Trovão",
        "desc": "ATIVA: acerta os inimigos mais proximos",
    },
    "selo_anti_noob": {
        "name": "Selo Anti-Noob",
        "desc": "PASSIVA: revive uma vez por rodada",
    },
    "sigma_bahia": {
        "name": "Sigma da Bahia",
        "desc": "PASSIVA: quanto mais cartas, mais dano",
    },
    "xique_xique": {
        "name": "Xique-Xique Bahia",
        "desc": "PASSIVA: regenera mais e fica mais pesado",
    },
    "amostradinho": {
        "name": "Amostradinho",
        "desc": "PASSIVA: mais vida e mais critico",
    },
    "acorda_pedrinho": {
        "name": "Acorda Pedrinho",
        "desc": "PASSIVA: começa cada rodada acelerado",
    },
    "base_virginia": {
        "name": "Base da Virginia",
        "desc": "PASSIVA: reduz dano e brilho dos tiros",
    },
    "descer_bc": {
        "name": "Descer pra BC",
        "desc": "PASSIVA: mais velocidade horizontal",
    },
    "so_fe": {
        "name": "So Fe",
        "desc": "PASSIVA: chance absurda de sobreviver com 1 HP",
    },
    "ta_ok": {
        "name": "Ta Ok",
        "desc": "PASSIVA: atira e recarrega um pouco mais rapido",
    },
    "faz_o_l": {
        "name": "Faz o L",
        "desc": "PASSIVA: ganha vida ao vencer rodada",
    },
    "faz_o_m": {
        "name": "Faz o M",
        "desc": "PASSIVA: ganha dano ao perder rodada",
    },
    "free_fire": {
        "name": "Capa no Free Fire",
        "desc": "PASSIVA: critico alto em alvos com pouca vida",
    },
    "blox_fruits": {
        "name": "Blox Fruits",
        "desc": "ATIVA: rajada circular de balas ao redor",
    },
    "roblox_obby": {
        "name": "Roblox Obby",
        "desc": "PASSIVA: mais pulos no ar e menos gravidade",
    },
    "skibidi": {
        "name": "Skibidi Toilet",
        "desc": "ATIVA: desacelera inimigos e empilha controle",
    },
    "ohio_final_boss": {
        "name": "Ohio Final Boss",
        "desc": "PASSIVA: fica enorme, tanque e lento",
    },
    "rizz": {
        "name": "Rizz Supremo",
        "desc": "ATIVA: rouba vida de inimigos proximos",
    },
    "gyatt": {
        "name": "Gyatt Armor",
        "desc": "PASSIVA: mais armadura e knockback",
    },
    "npc_streamer": {
        "name": "NPC Streamer",
        "desc": "PASSIVA: cada acerto reduz cooldown ativo",
    },
    "delulu": {
        "name": "Delulu Mode",
        "desc": "PASSIVA: chance de ignorar dano fatal",
    },
    "grimace_shake": {
        "name": "Grimace Shake",
        "desc": "ATIVA: envenena todos os inimigos",
    },
    "ankha_zone": {
        "name": "Ankha Zone",
        "desc": "PASSIVA: balas quicam mais e duram mais",
    },
    "among_us": {
        "name": "Sus Impostor",
        "desc": "ATIVA: teleporta curto na direcao da mira",
    },
    "doge": {
        "name": "Doge Muito Uau",
        "desc": "PASSIVA: pequenos bonus em tudo",
    },
    "pepe": {
        "name": "Pepe Rare",
        "desc": "PASSIVA: sorte em critico, esquiva e cartas",
    },
    "rickroll": {
        "name": "Rickroll",
        "desc": "ATIVA: silencia os inimigos por um instante",
    },
    "galvao": {
        "name": "Fala Tino",
        "desc": "PASSIVA: logs criticos e dano extra em lideres",
    },
    "irineu": {
        "name": "Voce Nao Sabe Nem Eu",
        "desc": "PASSIVA: efeito aleatorio extra a cada rodada",
    },
    "marilene": {
        "name": "Oi Marilene",
        "desc": "ATIVA: cura voce e empurra inimigos proximos",
    },
    "vou_nada": {
        "name": "Vou Nada",
        "desc": "PASSIVA: resistir a empurroes e quedas",
    },
    "tata_foda": {
        "name": "O Tata e Foda",
        "desc": "PASSIVA: multishot extra ocasional",
    },
    "bluezao": {
        "name": "Azul Caneta",
        "desc": "ATIVA: dispara bala gigante; stacks soltam varias",
    },
    "nyan_cat": {
        "name": "Nyan Cat",
        "desc": "ATIVA: arco-iris de balas caoticas",
    },
    "keyboard_cat": {
        "name": "Keyboard Cat",
        "desc": "ATIVA: silencia geral e joga caos na arena",
    },
    "trollface": {
        "name": "Trollface",
        "desc": "PASSIVA: chance de inverter dano recebido",
    },
    "wojak": {
        "name": "Wojak",
        "desc": "PASSIVA: fica mais forte quando esta perdendo",
    },
    "stonks": {
        "name": "Stonks",
        "desc": "PASSIVA: cada carta aumenta todos os status",
    },
    "galaxy_brain": {
        "name": "Galaxy Brain",
        "desc": "PASSIVA: +1 municao, recarga melhor, cooldown ativo menor e critico maior",
    },
    "glock_lisa": {
        "name": "Glock Lisa",
        "desc": "PASSIVA: +1 municao maxima",
    },
    "reload_chad": {
        "name": "Reload Chad",
        "desc": "PASSIVA: recarga bem mais rapida",
    },
    "one_tap": {
        "name": "One Tap Clip",
        "desc": "PASSIVA: a ultima bala do pente bate bem mais forte",
    },
    "scavenger_hunt": {
        "name": "Scavenger Hunt",
        "desc": "PASSIVA: abates com tiro devolvem municao para o pente",
    },
    "panic_pocket": {
        "name": "Panic Pocket",
        "desc": "PASSIVA: terminar recarga da um pico curto de ritmo",
    },
    "golden_mag": {
        "name": "Golden Mag",
        "desc": "PASSIVA: a primeira bala depois da recarga sai mais forte e mais veloz",
    },
    "bottomless_meme": {
        "name": "Bottomless Meme",
        "desc": "PASSIVA: alguns disparos saem de graca sem gastar municao",
    },
    "this_is_fine": {
        "name": "This Is Fine",
        "desc": "ATIVA: espalha incendio e caos pela arena inteira",
    },
    "distracted_boyfriend": {
        "name": "Distracted Boyfriend",
        "desc": "ATIVA: inimigos miram para o lado errado",
    },
    "hide_pain_harold": {
        "name": "Hide the Pain Harold",
        "desc": "PASSIVA: converte parte do dano em cura lenta",
    },
    "salt_bae": {
        "name": "Salt Bae",
        "desc": "ATIVA: chuva de sal explosivo cai do ceu",
    },
    "john_cena": {
        "name": "John Cena",
        "desc": "ATIVA: ganha dash e fica intangivel por um tempo",
    },
    "giga_chad": {
        "name": "GigaChad",
        "desc": "PASSIVA: muito dano, vida e knockback",
    },
    "morbin_time": {
        "name": "Morbin Time",
        "desc": "ATIVA: rouba muita vida em area",
    },
    "big_chungus": {
        "name": "Big Chungus",
        "desc": "PASSIVA: vira tanque gigante com bala enorme",
    },
    "loss_meme": {
        "name": "Loss",
        "desc": "PASSIVA: perder rodada aumenta muito os buffs",
    },
    "press_f": {
        "name": "Press F",
        "desc": "PASSIVA: ao morrer explode em homenagem",
    },
    "surprised_pikachu": {
        "name": "Surprised Pikachu",
        "desc": "PASSIVA: chance de refletir criticos",
    },
    "kermit_tea": {
        "name": "Kermit Tea",
        "desc": "PASSIVA: regenera quando nao esta atirando",
    },
    "evil_kermit": {
        "name": "Evil Kermit",
        "desc": "ATIVA: empilha tiros duplicados por alguns segundos",
    },
    "coffin_dance": {
        "name": "Coffin Dance",
        "desc": "ATIVA: executa inimigos com pouca vida",
    },
    "el_risitas": {
        "name": "El Risitas",
        "desc": "PASSIVA: risada critica encadeia dano",
    },
    "corn_kid": {
        "name": "Corn Kid",
        "desc": "PASSIVA: balas deixam milho explosivo",
    },
    "wednesday_dance": {
        "name": "Wednesday Dance",
        "desc": "ATIVA: arremessa inimigos para o alto",
    },
    "pedro_pedro": {
        "name": "Pedro Pedro",
        "desc": "ATIVA: gira e dispara em espiral",
    },
    "harlem_shake": {
        "name": "Harlem Shake",
        "desc": "ATIVA: troca posicoes aleatorias",
    },
    "gangnam_style": {
        "name": "Gangnam Style",
        "desc": "PASSIVA: movimento lateral insano",
    },
    "yeet": {
        "name": "Yeet",
        "desc": "PASSIVA: knockback ridiculo nos acertos",
    },
    "fanum_tax": {
        "name": "Fanum Tax",
        "desc": "ATIVA: rouba vida e atrasa o cooldown ativo dos inimigos",
    },
    "backrooms": {
        "name": "Backrooms",
        "desc": "ATIVA: joga inimigos para pontos aleatorios da arena",
    },
    "liminal_space": {
        "name": "Liminal Space",
        "desc": "PASSIVA: fica intangivel por instantes ao tomar dano",
    },
    "corecore": {
        "name": "Corecore",
        "desc": "PASSIVA: quanto mais caos na sala, mais forte",
    },
    "moye_moye": {
        "name": "Moye Moye",
        "desc": "PASSIVA: dano sobe quando sua vida cai",
    },
    "quandale_dingle": {
        "name": "Quandale Dingle",
        "desc": "ATIVA: balas aleatorias em angulos impossiveis",
    },
    "ugandan_knuckles": {
        "name": "Ugandan Knuckles",
        "desc": "PASSIVA: segue o caminho: mais mira e velocidade",
    },
    "do_you_know_da_wae": {
        "name": "Do You Know Da Wae",
        "desc": "ATIVA: empurra inimigos na direcao da sua mira",
    },
    "dat_boi": {
        "name": "Dat Boi",
        "desc": "PASSIVA: acelera infinitamente a cada rodada",
    },
    "area_51": {
        "name": "Area 51 Raid",
        "desc": "ATIVA: invoca chuva lateral de projeteis alienigenas",
    },
    "shrek": {
        "name": "Shrek Is Love",
        "desc": "PASSIVA: tanque verde com cura forte",
    },
    "all_your_base": {
        "name": "All Your Base",
        "desc": "ATIVA: captura a arena com explosoes",
    },
    "bad_luck_brian": {
        "name": "Bad Luck Brian",
        "desc": "PASSIVA: azar vira dano extra depois",
    },
    "success_kid": {
        "name": "Success Kid",
        "desc": "PASSIVA: sorte absurda em tudo",
    },
    "side_eye_chloe": {
        "name": "Side Eye Chloe",
        "desc": "PASSIVA: esquiva melhor quando inimigo mira em voce",
    },
    "numa_numa": {
        "name": "Numa Numa",
        "desc": "ATIVA: acelera tiro e movimento por um tempo",
    },
    "ice_bucket": {
        "name": "Ice Bucket Challenge",
        "desc": "ATIVA: desacelera e derruba inimigos",
    },
    "tide_pod": {
        "name": "Tide Pod",
        "desc": "ATIVA: aplica veneno pesado nos inimigos",
    },
    "planking": {
        "name": "Planking",
        "desc": "PASSIVA: deitado toma menos dano",
    },
    "one_does_not": {
        "name": "One Does Not Simply",
        "desc": "PASSIVA: resistencia contra execucoes",
    },
    "woman_yelling": {
        "name": "Woman Yelling",
        "desc": "ATIVA: grito que empurra e silencia inimigos",
    },
    "baby_shark": {
        "name": "Baby Shark",
        "desc": "ATIVA: enxame de mini projeteis em volta de voce",
    },
    "let_him_cook": {
        "name": "Let Him Cook",
        "desc": "PASSIVA: ficar sem atirar carrega super tiro",
    },
    "npc_wojak": {
        "name": "NPC Wojak",
        "desc": "PASSIVA: automatiza pequenas rajadas extras",
    },
    "based": {
        "name": "Based",
        "desc": "PASSIVA: bonus enorme se tiver poucas cartas repetidas",
    },
    "ratio": {
        "name": "Ratio",
        "desc": "PASSIVA: dano extra contra quem tem mais vitorias",
    },
    "touch_grass": {
        "name": "Touch Grass",
        "desc": "PASSIVA: cura forte quando toca o chao",
    },
    "no_bitches": {
        "name": "No Maidens",
        "desc": "PASSIVA: sozinho fica muito mais forte",
    },
    "obama_prism": {
        "name": "Obama Prism",
        "desc": "ATIVA: rajada de lasers atravessa a arena",
    },
    "me_and_the_boys": {
        "name": "Me and the Boys",
        "desc": "ATIVA: rajada sincronizada de tiros fantasmas",
    },
    "ultra_instinct": {
        "name": "Ultra Instinct Shaggy",
        "desc": "PASSIVA: esquiva, velocidade e revive absurdo",
    },
    "uno_reverse": {
        "name": "UNO Reverse Card",
        "desc": "PASSIVA: parry dura mais e tiros refletidos batem mais forte",
    },
    "no_u": {
        "name": "No U",
        "desc": "PASSIVA: parry recarrega mais rapido e reflete mais veloz",
    },
    "omae_wa": {
        "name": "Omae Wa Mou Shindeiru",
        "desc": "PASSIVA: parry bem-sucedido silencia e desacelera o atacante",
    },
    "mans_not_hot": {
        "name": "Man's Not Hot",
        "desc": "PASSIVA: parry bem-sucedido cura e acelera voce por instantes",
    },
    "call_an_ambulance": {
        "name": "Call An Ambulance",
        "desc": "PASSIVA: parry bem-sucedido deixa seu proximo disparo muito mais forte",
    },
    "spiderman_pointing": {
        "name": "Spider-Man Pointing",
        "desc": "PASSIVA: tiros refletidos ganham mais quique e mais knockback",
    },
    "is_this_pigeon": {
        "name": "Is This a Pigeon?",
        "desc": "PASSIVA: parry fica mais largo e mais facil de acertar",
    },
    "bonk": {
        "name": "Bonk",
        "desc": "PASSIVA: tiros refletidos atordoam no impacto com empurrao extra",
    },
    "leeroy_jenkins": {
        "name": "Leeroy Jenkins",
        "desc": "PASSIVA: corre e atira mais rapido, mas fica menos resistente",
    },
    "disaster_girl": {
        "name": "Disaster Girl",
        "desc": "PASSIVA: seus acertos espalham incendio curto no alvo",
    },
    "dramatic_chipmunk": {
        "name": "Dramatic Chipmunk",
        "desc": "PASSIVA: criticos e cooldown ativo ficam melhores",
    },
    "crying_jordan": {
        "name": "Crying Jordan",
        "desc": "PASSIVA: quando a vida cai, sua cura e armadura sobem",
    },
    "charlie_bit_my_finger": {
        "name": "Charlie Bit My Finger",
        "desc": "PASSIVA: roubavida e dano extra em alvos proximos",
    },
    "keyboard_smash": {
        "name": "ASDF Movie Panic",
        "desc": "PASSIVA: tiros saem mais rapido e com mais caos",
    },
    "reverse_overdrive": {
        "name": "Reverse Overdrive",
        "desc": "FUSAO: parry colossal, reflect brutal e quase sem cooldown",
        "fusion_only": True,
    },
    "final_notice": {
        "name": "Final Notice",
        "desc": "FUSAO: parry refletido fica brutal, silencia, desacelera e amplifica a pressão",
        "fusion_only": True,
    },
    "chaos_engine": {
        "name": "Chaos Engine",
        "desc": "FUSAO: acelera a build, reforça criticos e empilha caos em tudo",
        "fusion_only": True,
    },
    "berserker_prime": {
        "name": "Berserker Prime",
        "desc": "FUSAO: rush extremo com sustain, dano e resistencia em clutch",
        "fusion_only": True,
    },
    "tsar_bomba": {
        "name": "Tsar Bomba",
        "desc": "ATIVA: explosao nuclear colossal no centro da arena",
        "special": True,
    },
    "mini_black_hole": {
        "name": "Mini Black Hole",
        "desc": "ATIVA: puxa inimigos para voce; com stacks o campo fica mais opressivo",
        "special": True,
    },
    "brainrot_tornado": {
        "name": "Brainrot Tornado",
        "desc": "ATIVA: cria um tornado que ergue, gira e bagunca inimigos",
        "special": True,
    },
    "meteor_swarm": {
        "name": "Meteor Swarm",
        "desc": "ATIVA: bombardeio massivo de meteoros em toda a arena",
        "special": True,
    },
    "orbital_laser": {
        "name": "Orbital Laser",
        "desc": "ATIVA: feixe orbital corta a arena; stacks criam varios lasers",
        "special": True,
    },
    "world_freeze": {
        "name": "World Freeze",
        "desc": "ATIVA: congela, desacelera e derruba todos os inimigos",
        "special": True,
    },
    "void_rift": {
        "name": "Void Rift",
        "desc": "ATIVA: rasgo do vazio teleporta e estoura inimigos proximos",
        "special": True,
    },
    "apocalypse_rain": {
        "name": "Apocalypse Rain",
        "desc": "ATIVA: chuva apocaliptica de tiros e fogo do ceu",
        "special": True,
    },
    "supernova": {
        "name": "Supernova",
        "desc": "ATIVA: implosao seguida de explosao gigante ao seu redor",
        "special": True,
    },
    "quake_slam": {
        "name": "Quake Slam",
        "desc": "ATIVA: impacto sismico derruba e arremessa geral",
        "special": True,
    },
    "homing_rounds": {
        "name": "Homing For The Weak",
        "desc": "PASSIVA: tiros ganham rastreio; mais stacks curvam mais forte",
    },
    "ricochet_roulette": {
        "name": "Ricochet Roulette",
        "desc": "PASSIVA: tiros quicam mais e perseguem melhor depois do ricochete",
    },
    "cluster_pop": {
        "name": "Cluster Pop",
        "desc": "PASSIVA: tiros se dividem ao expirar ou impactar",
    },
    "toxic_payload": {
        "name": "Toxic Payload",
        "desc": "PASSIVA: impactos criam splash venenoso; stacks ampliam a praga",
    },
    "railgun_charge": {
        "name": "Railgun Charge",
        "desc": "PASSIVA: projeteis perfuram e voam muito mais rapido, mas a recarga fica um pouco mais lenta",
    },
    "boomerang_rounds": {
        "name": "Boomerang Rounds",
        "desc": "PASSIVA: tiros voltam como bumerangue; stacks fazem voltar mais cedo",
    },
    "drone_guidance": {
        "name": "Drone Guidance",
        "desc": "PASSIVA: tiros aceleram no ar e reforcam o tracking",
    },
    "guided_swarm": {
        "name": "Guided Swarm",
        "desc": "ATIVA: libera um enxame de mini tiros teleguiados; stacks soltam mais enxame",
    },
    "buckshot_mayhem": {
        "name": "Buckshot Mayhem",
        "desc": "PASSIVA: cada disparo vira uma rajada de pellets curtos gastando 1 municao; stacka com multishot",
    },
    "ghost_rounds": {
        "name": "Ghost Rounds",
        "desc": "PASSIVA: cada tiro atravessa a primeira parede, teto ou plataforma",
    },
    "parasite_rounds": {
        "name": "Parasite Rounds",
        "desc": "PASSIVA: impactos envenenam e drenam cooldown ativo do alvo",
    },
    "bounce_house": {
        "name": "Bounce House",
        "desc": "PASSIVA: cada ricochete acelera e fortalece ainda mais o tiro",
    },
    "remote_detonator": {
        "name": "Remote Detonator",
        "desc": "ATIVA: detona todas as suas balas; stacks aumentam raio e dano da explosao",
    },
    "magnet_trigger": {
        "name": "Magnet Trigger",
        "desc": "ATIVA: todas as suas balas em campo ganham homing e aceleracao extra",
    },
    "portal_storm": {
        "name": "Portal Storm",
        "desc": "ATIVA: abre portais nas laterais; stacks disparam ainda mais balas",
    },
    "glass_cannon_tv": {
        "name": "Glass Cannon TV",
        "desc": "PASSIVA: muito dano e velocidade de tiro, mas bem menos vida maxima",
    },
    "omega_event_horizon": {
        "name": "Omega Event Horizon",
        "desc": "FUSAO: buraco negro, veneno e detonação apocaliptica no mesmo cast",
        "fusion_only": True,
    },
    "judgement_day": {
        "name": "Judgement Day",
        "desc": "FUSAO: nuke, laser orbital e chuva final do ceu no mesmo ataque",
        "fusion_only": True,
    },
    "tempest_cataclysm": {
        "name": "Tempest Cataclysm",
        "desc": "FUSAO: tornado, freeze e quake empilhados num unico cast",
        "fusion_only": True,
    },
}

def send_json(sock, payload):
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8") + b"\n"
    sock.sendall(data)

class LineBuffer:
    def __init__(self):
        self.buf = b""

    def feed(self, data):
        self.buf += data
        lines = []
        while b"\n" in self.buf:
            line, self.buf = self.buf.split(b"\n", 1)
            if line.strip():
                lines.append(json.loads(line.decode("utf-8")))
        return lines
