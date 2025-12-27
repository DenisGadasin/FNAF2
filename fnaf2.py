import pygame
import os
import ctypes
import random
from PIL import Image, ImageSequence
import webbrowser
import json
import requests
import time
import importlib.util
import sys
import subprocess
import platform

try:
    ctypes.windll.user32.SetProcessDPIAware()
except:
    pass

pygame.init()
pygame.mixer.quit()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

info = pygame.display.Info()
WIN_W, WIN_H = info.current_w, info.current_h
screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.FULLSCREEN)
pygame.display.set_caption("Five Nights at Freddy's 2")

base_path = os.path.dirname(os.path.abspath(__file__))
images_path = os.path.join(base_path, "images")
sounds_path = os.path.join(base_path, "sounds")

OFFICE_SCALE = 1.25
office_size = (int(WIN_W * OFFICE_SCALE), WIN_H)

os.makedirs(images_path, exist_ok=True)
os.makedirs(sounds_path, exist_ok=True)

font_clock = pygame.font.SysFont("OCR A Extended", 40)
font_dev = pygame.font.SysFont("Consolas", 18)
font_main = pygame.font.SysFont("Arial", 100, bold=True)
font_title = pygame.font.SysFont("Arial", 50, bold=True)
font_button = pygame.font.SysFont("Arial", 30, bold=True)
font_bug_report = pygame.font.SysFont("Arial", 20)
font_bug_input = pygame.font.SysFont("Arial", 18)
font_mods = pygame.font.SysFont("Arial", 24)
font_mods_warning = pygame.font.SysFont("Arial", 16, bold=True)

# Mods system setup
appdata_path = os.getenv('APPDATA')
if not appdata_path:
    appdata_path = os.path.expanduser('~')
    if os.name == 'nt':
        appdata_path = os.path.join(appdata_path, 'AppData', 'Roaming')

save_dir = os.path.join(appdata_path, 'FNAF2')
mods_dir = os.path.join(save_dir, 'Mods')

try:
    os.makedirs(mods_dir, exist_ok=True)
except:
    pass

save_file = os.path.join(save_dir, "save.json")

available_mods = []
installed_mod = None
active_mod = None
mods_scroll_offset = 0

def scan_mods():
    """Сканирует папку модов и возвращает список доступных модов"""
    global available_mods
    available_mods = []
    
    if not os.path.exists(mods_dir):
        try:
            os.makedirs(mods_dir, exist_ok=True)
        except:
            pass
        return available_mods
    
    try:
        for filename in os.listdir(mods_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                mod_name = filename[:-3]  # Убираем .py
                mod_path = os.path.join(mods_dir, filename)
                available_mods.append({
                    'name': mod_name,
                    'filename': filename,
                    'path': mod_path,
                    'installed': False
                })
    except Exception as e:
        print(f"Error scanning mods: {e}")
    
    return available_mods

def install_mod(mod_info):
    """Устанавливает мод"""
    global installed_mod
    installed_mod = mod_info
    mod_info['installed'] = True

def uninstall_mod():
    """Удаляет установленный мод"""
    global installed_mod, active_mod
    if installed_mod:
        installed_mod['installed'] = False
        installed_mod = None
    active_mod = None

def launch_mod(mod_info):
    """Запускает мод"""
    global active_mod
    try:
        # Загружаем модуль мода
        spec = importlib.util.spec_from_file_location(mod_info['name'], mod_info['path'])
        mod_module = importlib.util.module_from_spec(spec)
        sys.modules[mod_info['name']] = mod_module
        spec.loader.exec_module(mod_module)
        
        active_mod = mod_info
        
        # Вызываем функцию инициализации мода, если она есть
        if hasattr(mod_module, 'init_mod'):
            mod_module.init_mod()
        
        return True
    except Exception as e:
        print(f"Error launching mod: {e}")
        return False

def open_mods_folder():
    """Открывает папку с модами в проводнике"""
    try:
        # Создаем папку если её нет
        if not os.path.exists(mods_dir):
            os.makedirs(mods_dir, exist_ok=True)
        
        # Открываем папку в зависимости от ОС
        if platform.system() == 'Windows':
            os.startfile(mods_dir)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.Popen(['open', mods_dir])
        else:  # Linux
            subprocess.Popen(['xdg-open', mods_dir])
    except Exception as e:
        print(f"Error opening mods folder: {e}")

def load_img(name, target_size=(WIN_W, WIN_H)):
    path = os.path.join(images_path, name)
    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, target_size)
        return img
    except:
        surf = pygame.Surface(target_size, pygame.SRCALPHA)
        surf.fill((30, 30, 30))
        return surf

def load_gif_frames(filename, target_size=(WIN_W, WIN_H), make_transparent=False):
    path = os.path.join(images_path, filename)
    frames = []
    if not os.path.exists(path):
        return None
    try:
        pil_image = Image.open(path)
        for frame in ImageSequence.Iterator(pil_image):
            frame = frame.convert("RGBA")
            
            # Делаем черный фон прозрачным если требуется
            if make_transparent:
                datas = frame.getdata()
                newData = []
                for item in datas:
                    # Заменяем черный (или почти черный) на прозрачный
                    if item[0] < 10 and item[1] < 10 and item[2] < 10:
                        newData.append((255, 255, 255, 0))
                    else:
                        newData.append(item)
                frame.putdata(newData)
            
            pygame_surface = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode).convert_alpha()
            pygame_surface = pygame.transform.scale(pygame_surface, target_size)
            frames.append((pygame_surface, frame.info.get('duration', 33)))
        return frames
    except:
        return None

def load_sound(filename):
    path = os.path.join(sounds_path, filename)
    if not os.path.exists(path):
        return None
    try:
        sound = pygame.mixer.Sound(path)
        return sound
    except:
        return None

map_size = (WIN_W // 2, WIN_H)

imgs = {
    "main": load_img("office_main.png", office_size),
    "hall_clear": load_img("office_center_clear.png", office_size),
    "hall_foxy": load_img("WitheredFoxyStage.png", office_size),
    "vent_l_clear": load_img("FNaF_2_Office_Left_Vent_Light.png", office_size),
    "vent_l_chica": load_img("FNaF_2_Office_Left_Vent_Toy_Chica.png", office_size),
    "vent_r_clear": load_img("FNaF_2_Office_Right_Vent_Light.png", office_size),
    "vent_r_bonnie": load_img("FNaF_2_Office_Right_Vent_Toy_Bonnie.png", office_size),
    "mask": load_img("Mask.png"),
    "puppet_awake_light": load_img("PuppetAwakeLight.png"),
    "puppet_in_box_light": load_img("PuppetInBoxLight.png"),
    "puppet_box_no_light": load_img("PuppetBoxNoLight.png"),
    "map8": load_img("Cam8.png", map_size),
    "map9": load_img("cam9.png", map_size),
    "map11": load_img("Cam11.png", map_size),
    "stage_full": load_img("StageFull.png"),
    "stage_full_light": load_img("StageLightFull.png"),
    "stage_freddy_chica": load_img("StageFreddyChicka.png"),
    "stage_freddy_chica_light": load_img("StageFreddyChickaLight.png"),
    "stage_freddy_bonnie": load_img("StageFreddyBonnie.png"),
    "stage_freddy_bonnie_light": load_img("StageFreddyBonnieLight.png"),
    "stage_freddy": load_img("StageFreddy.png"),
    "stage_freddy_light": load_img("StageFreddyLight.png"),
    "stage_bonnie_freddy": load_img("ToyBonnieToyFreddyStage.png"),
    "stage_bonnie_freddy_light": load_img("ToyBonnieToyFreddyStageLight.png"),
    "cam8_view": load_img("Cam8View.png"),
    "menu": load_img("menuTest.png"),
    "toy_chica_face": load_img("ToyChikaFace.png", (150, 150)),
    "toy_chica_face2": load_img("ToyChickaFace2.png", (150, 150)),
    "toy_chica_face3": load_img("ToyChickaFace3.png", (150, 150)),
    "toy_bonnie_face": load_img("ToyBonnyFace.png", (150, 150)),
    "toy_bonnie_face2": load_img("BonnieFace2.png", (150, 150)),
    "toy_bonnie_face3": load_img("BonnieFace3.png", (150, 150)),
    "withered_foxy_face": load_img("WitheredFoxyFace.png", (150, 150)),
    "withered_foxy_face2": load_img("FoxyFace2.png", (150, 150)),
    "withered_foxy_face3": load_img("FoxyFace3.png", (150, 150)),
    "puppet_face": load_img("PuppetFace.png", (150, 150)),
    "main_hall_clear": load_img("MainHallClear.png"),
    "main_hall_toy_chica": load_img("MainHallToyChicka.png"),
    "main_hall_clear_light": load_img("MainHalLClearLight.png"),
    "main_hall_toy_chica_light": load_img("MainHallToyChickaLight.png"),
    "party_room2_toy_bonnie": load_img("PartyRoom2ToyBonnie.png"),
    "party_room2_toy_bonnie_light": load_img("PartyRoom2ToyBonnieLight.png"),
    "party_room2_clear": load_img("PartyRoom2Clear.png"),
    "party_room2_clear_light": load_img("PartyRoomClearLight.png"),
    "bb_face": load_img("BBFace.png", (150, 150)),
    "bb_face2": load_img("BBFace2.png", (150, 150)),
    "bb_face3": load_img("BBFace3.png", (150, 150)),
    "bb_face4": load_img("BBFace4.png", (150, 150)),
    "parts_service_lo_light": load_img("PartsServiceLoLight.png"),
    "parts_service_all_light": load_img("PartsServiceAllLight.png"),
    "parts_service_without_foxy": load_img("PartsServiceWithoutFoxy.png"),
    "game_area_bb": load_img("GameAreaBB.png"),
    "game_area_bb_light": load_img("GameAreBBLight.png"),
    "game_area_clear": load_img("GameAreaClear.png"),
    "game_area_clear_light": load_img("GameAreClearLight.png"),
    "left_vent": load_img("LeftVent.png"),
    "left_vent_bb_light": load_img("LeftVentBBLight.png"),
    "left_vent_toy_chicka": load_img("LeftVentToyChicka.png"),
    "office_bb_vent": load_img("OfficeBBVent.png", office_size),
    "office_bb": load_img("OfficeBB.png", office_size),
    "tg_icon": load_img("TGIcon.png", (50, 50)),
    "tiktok_icon": load_img("TikTokIcon.png", (50, 50)),
    "bug_icon": load_img("BugIcon.png", (50, 50)),
    "monitor_button": load_img("MonitorButton.png", (650, 40)),
    "mask_button": load_img("MaskButton.png", (650, 40))
}

imgs["mask"].set_colorkey((255, 255, 255))

jumpscares = {
    "Toy Bonnie": load_gif_frames("FNaF_2_Toy_Bonnie_Jumpscare.gif"),
    "Toy Chica": load_gif_frames("FNaF_2_Toy_Chica_Jumpscare.gif"),
    "Withered Foxy": load_gif_frames("FNaF_2_Withered_Foxy_Jumpscare.gif"),
    "Puppet": load_gif_frames("PuppetJumpScare.gif")
}

checks = {
    "Toy Bonnie_fail": load_gif_frames("ToyBonnieShake.gif", office_size),
    "Toy Chica_fail": load_gif_frames("ToyChicaShake.gif", office_size)
}

puppet_dance_frames = load_gif_frames("PuppetDance.gif")
# Загружаем анимации
monitor_up_frames = load_gif_frames("MonitorUp.gif")
monitor_down_frames = load_gif_frames("MonitorDown.gif")
mask_equip_frames = load_gif_frames("MaskEquip.gif")
mask_unequip_frames = load_gif_frames("MaskUnequip.gif")
pomexi_frames = load_gif_frames("Pomexi.gif")
orange_alert_frames = load_gif_frames("Orange_Alert.gif", (100, 100))
red_alert_frames = load_gif_frames("Red_Alert.gif", (100, 100))
# FIX 2: Загружаем анимацию 6AM
six_am_frames = load_gif_frames("6AM.gif")

jumpscare_sound = load_sound("JumpScare1.mp3")
foxy_line1_sound = load_sound("FoxyLine1.mp3")
vent_light_sound = load_sound("VentLight.mp3")
hall_sound = load_sound("Hall.mp3")
vent_crawl_sound = load_sound("VentCrawl.mp3")
mask_equip_sound = load_sound("MaskEquip.mp3")
mask_unequip_sound = load_sound("MaskUnequip.mp3")
mask_breathing_sound = load_sound("MaskBreathing.mp3")
music_box_song = load_sound("MusicBoxSong.mp3")
music_box_charge = load_sound("MusicBoxCharge.mp3")
check_sound = load_sound("CheckSound.mp3")
menu_music = load_sound("MenuTheme.mp3")
bb_hi = load_sound("BBHi.mp3")
bb_hello = load_sound("BBHello.mp3")
bb_laugh = load_sound("BBLaugh.mp3")
bb_laught = load_sound("BBLaught.mp3")
flash_error = load_sound("FlashLightError.mp3")
# FIX 2: Загружаем звук 6AM
six_am_theme = load_sound("6AMTheme.mp3")

def play_sound(sound, loops=0):
    if sound:
        try:
            sound.play(loops)
        except:
            pass

def stop_sound(sound):
    if sound:
        try:
            sound.stop()
        except:
            pass

def stop_all_sounds():
    stop_sound(jumpscare_sound)
    stop_sound(foxy_line1_sound)
    stop_sound(vent_light_sound)
    stop_sound(hall_sound)
    stop_sound(vent_crawl_sound)
    stop_sound(mask_equip_sound)
    stop_sound(mask_unequip_sound)
    stop_sound(mask_breathing_sound)
    stop_sound(music_box_song)
    stop_sound(music_box_charge)
    stop_sound(check_sound)
    stop_sound(menu_music)
    stop_sound(bb_hi)
    stop_sound(bb_hello)
    stop_sound(bb_laugh)
    stop_sound(bb_laught)
    stop_sound(flash_error)
    stop_sound(six_am_theme)

class SimpleBeatDetector:
    def __init__(self):
        self.shake_intensity = 0
        self.shake_decay = 0.85
        self.beat_pattern = [
            (0.0, 8), (0.5, 3), (1.0, 8), (1.5, 3),
            (2.0, 8), (2.5, 3), (3.0, 8), (3.5, 3),
            (4.0, 10), (4.5, 4), (5.0, 10), (5.5, 4),
            (6.0, 10), (6.5, 4), (7.0, 10), (7.5, 4),
            (8.0, 12), (8.25, 5), (8.5, 8), (8.75, 5),
            (9.0, 12), (9.25, 5), (9.5, 8), (9.75, 5),
        ]
        self.pattern_duration = 10.0
        self.last_beat_time = -1
   
    def update(self, music_position_sec):
        self.shake_intensity *= self.shake_decay
       
        loop_position = music_position_sec % self.pattern_duration
       
        for beat_time, strength in self.beat_pattern:
            if abs(loop_position - beat_time) < 0.05:
                if abs(music_position_sec - self.last_beat_time) > 0.1:
                    self.shake_intensity = strength
                    self.last_beat_time = music_position_sec
                    break
   
    def get_shake_offset(self):
        if self.shake_intensity > 0.5:
            shake_x = random.uniform(-self.shake_intensity, self.shake_intensity)
            shake_y = random.uniform(-self.shake_intensity, self.shake_intensity)
            return int(shake_x), int(shake_y)
        return 0, 0
   
    def reset(self):
        self.shake_intensity = 0
        self.last_beat_time = -1

bug_report_text = ""
bug_report_category = ""
last_bug_report_time = 0
BUG_REPORT_COOLDOWN = 600

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1453443649680703639/Sae4YeT500kDNZoR_M7an7Fqle1Fo-Mx7lo_yvZWyIJo2RBQIaerxAkygXeTnYXcR9Ms"

bug_categories = [
    "Слабый (не мешающий игровому процессу)",
    "Средний (немного мешает игре)",
    "Сильный (очень мешает игре)"
]

def send_bug_report_to_discord(text, category):
    try:
        data = {
            "content": f"**Новый баг!**\n\n**Текст:**\n{text}\n\n**Категория:** {category}"
        }
        response = requests.post(DISCORD_WEBHOOK, json=data, timeout=5)
        return response.status_code == 204
    except Exception as e:
        return False

def can_submit_bug_report():
    current_time = time.time()
    return (current_time - last_bug_report_time) >= BUG_REPORT_COOLDOWN

def get_time_until_next_report():
    current_time = time.time()
    time_passed = current_time - last_bug_report_time
    time_remaining = max(0, BUG_REPORT_COOLDOWN - time_passed)
    minutes = int(time_remaining // 60)
    seconds = int(time_remaining % 60)
    return minutes, seconds

class Animatronic:
    def __init__(self, name, start_pos, target_pos, ai_level, interval=5000):
        self.name = name
        self.start_pos = start_pos
        self.pos = start_pos
        self.target_name = target_pos
        self.ai_level = ai_level
        self.interval = interval
        self.last_think = pygame.time.get_ticks()
        self.think_interval = interval
       
        self.foxy_unwatched_time = 0
        self.foxy_watched_time = 0
        self.vent_arrival_time = 0
        self.status_msg = "Waiting"
        self.charge = 100.0 if name == "Puppet" else None
        self.last_discharge = pygame.time.get_ticks()
        self.discharge_time = 0

    def reset(self):
        self.pos = self.start_pos
        self.last_think = pygame.time.get_ticks()
        self.think_interval = self.interval
        self.foxy_unwatched_time = 0
        self.foxy_watched_time = 0
        self.vent_arrival_time = 0
        self.status_msg = "Waiting"
        self.last_discharge = pygame.time.get_ticks()
        self.discharge_time = 0
        if self.name == "Puppet":
            self.charge = 100.0

    def update(self, is_watching_hall, dt):
        now = pygame.time.get_ticks()
       
        if self.ai_level == 0:
            return
       
        if self.name == "Puppet":
            if self.pos == "Box" and self.charge > 0:
                interval = 1000
                amount = 6
                if now - self.last_discharge >= interval:
                    self.charge -= amount
                    self.last_discharge = now
                    if self.charge <= 0:
                        self.charge = 0
                        self.discharge_time = now
                        self.pos = "Awake"
            elif self.pos == "Awake":
                if now - self.discharge_time >= 3000:
                    self.pos = "Office"
            return
       
        if self.name == "Withered Foxy":
            if self.pos == "Parts Service":
                if now - self.last_think > self.think_interval:
                    self.last_think = now
                    if random.randint(1, 20) <= self.ai_level:
                        if not any(b.pos == self.target_name for b in bots if b != self):
                            self.pos = self.target_name
                            self.vent_arrival_time = now
                            self.status_msg = "ENTERING HALL"
                        else:
                            self.status_msg = "Hall occupied"
                    else:
                        self.status_msg = "Idle in Parts Service"
            elif self.pos == self.target_name:
                if not is_watching_hall:
                    self.foxy_unwatched_time += dt
                    self.status_msg = f"Attack in: {7.5 - self.foxy_unwatched_time/1000:.1f}s"
                    if self.foxy_unwatched_time >= 7500: 
                        self.pos = "Office"
                else:
                    self.foxy_watched_time += dt
                    self.foxy_unwatched_time = max(0, self.foxy_unwatched_time - dt)
                    self.status_msg = f"Blinding: {6.0 - self.foxy_watched_time/1000:.1f}s"
                    if self.foxy_watched_time >= 6000:
                        self.pos = self.start_pos
                        self.foxy_watched_time = 0
            return

        if now - self.last_think > self.think_interval:
            self.last_think = now
           
            if self.name == "Toy Chica":
                if self.pos == "Stage":
                    if random.randint(1, 20) <= self.ai_level:
                        next_pos = "Main Hall"
                        if not any(b.pos == next_pos for b in bots if b != self):
                            self.pos = next_pos
                            self.status_msg = "MOVING TO MAIN HALL"
                        else:
                            self.status_msg = "Main Hall occupied"
                    else:
                        self.status_msg = "Idle on Stage"
                    return
                elif self.pos == "Main Hall":
                    if random.randint(1, 20) <= self.ai_level:
                        next_pos = "Left Air Vent"
                        if not any(b.pos == next_pos for b in bots if b != self):
                            self.pos = next_pos
                            self.vent_arrival_time = now
                            play_sound(vent_crawl_sound)
                            self.status_msg = "ENTERING LEFT AIR VENT"
                        else:
                            self.status_msg = "Left Air Vent occupied"
                    else:
                        self.status_msg = "Idle in Main Hall"
                    return
                elif self.pos == "Left Air Vent":
                    if random.randint(1, 20) <= self.ai_level:
                        next_pos = "Office Vent Left"
                        if not any(b.pos == next_pos for b in bots if b != self):
                            self.pos = next_pos
                            self.vent_arrival_time = now
                            play_sound(vent_crawl_sound)
                            self.status_msg = "ENTERING OFFICE VENT LEFT"
                        else:
                            self.status_msg = "Office Vent Left occupied"
                    else:
                        self.status_msg = "Idle in Left Air Vent"
                    return
           
            if self.name == "Toy Bonnie":
                if self.pos == "Stage":
                    if random.randint(1, 20) <= self.ai_level:
                        next_pos = "Party Room2"
                        if not any(b.pos == next_pos for b in bots if b != self):
                            self.pos = next_pos
                            self.status_msg = "MOVING TO PARTY ROOM2"
                        else:
                            self.status_msg = "Party Room2 occupied"
                    else:
                        self.status_msg = "Idle on Stage"
                    return
                elif self.pos == "Party Room2":
                    if random.randint(1, 20) <= self.ai_level:
                        next_pos = "Office Vent Right"
                        if not any(b.pos == next_pos for b in bots if b != self):
                            self.pos = next_pos
                            self.vent_arrival_time = now
                            play_sound(vent_crawl_sound)
                            self.status_msg = "ENTERING OFFICE VENT RIGHT"
                        else:
                            self.status_msg = "Office Vent Right occupied"
                    else:
                        self.status_msg = "Idle in Party Room2"
                    return
           
            if self.name == "Balloon Boy":
                if self.pos == "Left Air Vent":
                    if random.randint(1, 20) <= self.ai_level:
                        next_pos = "Office Vent Left"
                        if not any(b.pos == next_pos for b in bots if b != self):
                            self.pos = next_pos
                            self.vent_arrival_time = now
                            self.status_msg = "ENTERING OFFICE VENT LEFT"
                        else:
                            self.status_msg = "Office Vent Left occupied"
                    else:
                        self.status_msg = "Idle in Left Air Vent"
                return
           
            if self.pos == "Office Vent Left" or self.pos == "Office Vent Right":
                if now - self.vent_arrival_time < 3000:
                    self.status_msg = f"Preparing: {3.0 - (now - self.vent_arrival_time)/1000:.1f}s"
                else:
                    roll = random.randint(1, 20)
                    if roll <= 5:
                        self.pos = "Office"
                        self.status_msg = "ATTACKING!"
                    else:
                        self.status_msg = f"Vent Wait (Roll {roll}>5)"

bots = [
    Animatronic("Toy Bonnie", "Stage", "Office Vent Right", ai_level=2, interval=5000),
    Animatronic("Toy Chica", "Stage", "Main Hall", ai_level=1, interval=6000),
    Animatronic("Withered Foxy", "Parts Service", "Hall", ai_level=0, interval=8000),
    Animatronic("Puppet", "Box", "Office", ai_level=1, interval=10000),
    Animatronic("Balloon Boy", "Game Area", "Left Air Vent", ai_level=0, interval=5000)
]

custom_levels = {
    "Toy Bonnie": 2,
    "Toy Chica": 1,
    "Withered Foxy": 0,
    "Puppet": 1,
    "Balloon Boy": 0
}

nights_ai = {
    1: {"Toy Bonnie":2, "Toy Chica":1, "Withered Foxy":0, "Puppet":2, "Balloon Boy":0},
    2: {"Toy Bonnie":3, "Toy Chica":3, "Withered Foxy":2, "Puppet":3, "Balloon Boy":3},
    3: {"Toy Bonnie":6, "Toy Chica":4, "Withered Foxy":4, "Puppet":6, "Balloon Boy":5},
    4: {"Toy Bonnie":8, "Toy Chica":7, "Withered Foxy":7, "Puppet":8, "Balloon Boy":7},
    5: {"Toy Bonnie":15, "Toy Chica":14, "Withered Foxy":8, "Puppet":11, "Balloon Boy":7},
    6: {"Toy Bonnie":15, "Toy Chica":14, "Withered Foxy":11, "Puppet":11, "Balloon Boy":11},
}

game_time_ms = 0
hour = 12
HOUR_DURATION = 60000

office_x = 0
mask_on = False
mask_on_start = 0
is_breathing_playing = False
dev_mode_active = False
running = True
game_state = "MENU"
active_js_bot = None
checking_bot = None
check_type = ""
check_start = 0
success_start = 0
js_frame_index = 0
js_frame_index_alert = 0
is_vent_light_playing = False
is_hall_sound_playing = False
camera_mode = False
light_on = False
charging = False
last_charge = 0
charge_button_rect = pygame.Rect(WIN_W // 2 - 50, WIN_H - 100, 100, 50)
music_box_playing = False
current_cam = '11'
clock = pygame.time.Clock()
is_custom_night = False
bb_sound_count = 0
bb_move_time = 0
bb_mask_start = 0
bb_in_office = False
bb_laugh_playing = False
bb_last_speak_time = 0
bb_idle_start = 0
bb_return_idle = False
flash_error_playing = False
monitor_animation_start = 0
pomexi_frame = 0
monitor_button_hovered = False
mask_button_hovered = False
current_night = 1
is_custom_unlocked = False

# Новые переменные для анимации маски
mask_animation_state = None  # None, "equipping", "equipped", "unequipping"
mask_animation_start = 0
mask_animation_frame = 0

# FIX 2: Новые переменные для анимации 6AM
six_am_animation_start = 0
six_am_frame_index = 0
six_am_sound_playing = False

def load_save():
    global current_night, is_custom_unlocked, last_bug_report_time, installed_mod
    if os.path.exists(save_file):
        try:
            with open(save_file, 'r') as f:
                data = json.load(f)
                current_night = data.get('current_night', 1)
                is_custom_unlocked = data.get('custom_unlocked', False)
                last_bug_report_time = data.get('last_bug_report_time', 0)
                
                # Загружаем информацию об установленном моде
                saved_mod = data.get('installed_mod', None)
                if saved_mod:
                    # Проверяем, существует ли еще файл мода
                    if os.path.exists(saved_mod.get('path', '')):
                        installed_mod = saved_mod
        except:
            current_night = 1
            is_custom_unlocked = False
            last_bug_report_time = 0
            installed_mod = None
    else:
        current_night = 1
        is_custom_unlocked = False
        last_bug_report_time = 0
        installed_mod = None

def save_progress():
    data = {
        'current_night': current_night,
        'custom_unlocked': is_custom_unlocked,
        'last_bug_report_time': last_bug_report_time,
        'installed_mod': installed_mod
    }
    try:
        os.makedirs(save_dir, exist_ok=True)
        with open(save_file, 'w') as f:
            json.dump(data, f, indent=2)
    except:
        pass

load_save()
save_progress()

# Сканируем моды при запуске
scan_mods()

puppet = next(b for b in bots if b.name == "Puppet")
foxy = next(b for b in bots if b.name == "Withered Foxy")

map_pos = (WIN_W // 2, 0)

cam_buttons = {
    '1': {'rect': pygame.Rect(50, 100, 100, 60), 'label': 'CAM 01'},
    '2': {'rect': pygame.Rect(170, 120, 100, 60), 'label': 'CAM 02'},
    '3': {'rect': pygame.Rect(290, 100, 100, 60), 'label': 'CAM 03'},
    '4': {'rect': pygame.Rect(50, 200, 100, 60), 'label': 'CAM 04'},
    '5': {'rect': pygame.Rect(170, 220, 100, 60), 'label': 'CAM 05'},
    '6': {'rect': pygame.Rect(290, 200, 100, 60), 'label': 'CAM 06'},
    '7': {'rect': pygame.Rect(50, 300, 100, 60), 'label': 'CAM 07'},
    '8': {'rect': pygame.Rect(170, 320, 100, 60), 'label': 'CAM 08'},
    '9': {'rect': pygame.Rect(290, 300, 100, 60), 'label': 'CAM 09'},
    '10': {'rect': pygame.Rect(50, 400, 100, 60), 'label': 'CAM 10'},
    '11': {'rect': pygame.Rect(170, 420, 100, 60), 'label': 'CAM 11'},
    '12': {'rect': pygame.Rect(290, 400, 100, 60), 'label': 'CAM 12'}
}

custom_pos_y = 200
custom_spacing = 200
custom_characters = ["Toy Bonnie", "Toy Chica", "Withered Foxy", "Puppet", "Balloon Boy"]

custom_rects_left = {}
custom_rects_right = {}
custom_level_rects = {}

char_positions = [
    (WIN_W//5, custom_pos_y),
    (2*WIN_W//5, custom_pos_y),
    (3*WIN_W//5, custom_pos_y),
    (4*WIN_W//5, custom_pos_y),
    (WIN_W//2, custom_pos_y + 250)
]

for i, name in enumerate(custom_characters):
    x, y = char_positions[i]
    custom_rects_left[name] = pygame.Rect(x - 80, y + 100, 40, 40)
    custom_rects_right[name] = pygame.Rect(x + 40, y + 100, 40, 40)
    custom_level_rects[name] = pygame.Rect(x - 40, y + 100, 80, 40)
   
rect_start_custom = pygame.Rect(WIN_W//2 - 100, custom_pos_y + 500, 200, 50)

foxy_sequence_start = 0
black_screen_alpha = 0
foxy_sound_played = False
foxy_sound_end = 0

rect_bug = pygame.Rect(WIN_W - 170, 10, 50, 50)
rect_tg = pygame.Rect(WIN_W - 110, 10, 50, 50)
rect_tiktok = pygame.Rect(WIN_W - 50, 10, 50, 50)

button_width_monitor = 650
button_width_mask = 650
button_height = 40

monitor_button_rect = pygame.Rect(WIN_W // 2 + 50, WIN_H - 60, button_width_monitor, button_height)
mask_button_rect = pygame.Rect(WIN_W // 2 - 700, WIN_H - 60, button_width_mask, button_height)

menu_buttons = [
    {"text": "ИГРАТЬ", "action": "new_game"},
    {"text": "ПРОДОЛЖИТЬ", "action": "continue"},
    {"text": "КАСТОМ НАЙТ", "action": "custom"},
    {"text": "МОДЫ", "action": "mods"}
]

menu_font = pygame.font.SysFont("Arial", 60, bold=True)
menu_button_y_start = WIN_H // 2 - 100
menu_button_spacing = 80
menu_selected = -1
menu_button_rects = []

# Создаем прямоугольники для всех кнопок
for i, btn in enumerate(menu_buttons):
    text_surf = menu_font.render(btn["text"], True, (255, 255, 255))
    x = 200
    # Учитываем, что КАСТОМ НАЙТ может быть скрыт
    if i <= 2:  # ИГРАТЬ, ПРОДОЛЖИТЬ, КАСТОМ НАЙТ
        y = menu_button_y_start + i * menu_button_spacing
    else:  # МОДЫ - всегда под КАСТОМ НАЙТ
        y = menu_button_y_start + 3 * menu_button_spacing
    rect = pygame.Rect(x, y, text_surf.get_width(), text_surf.get_height())
    menu_button_rects.append(rect)

beat_detector = SimpleBeatDetector()
menu_music_start_time = 0

def set_ai_levels():
    if is_custom_night:
        for bot in bots:
            if bot.name in custom_levels:
                bot.ai_level = custom_levels[bot.name]
    else:
        ai_dict = nights_ai.get(current_night, nights_ai[1])
        for bot in bots:
            bot.ai_level = ai_dict.get(bot.name, 0)
        if current_night == 1:
            foxy.ai_level = 0

def reset_game():
    global game_time_ms, hour, office_x, mask_on, mask_on_start, is_breathing_playing, active_js_bot, checking_bot, check_type, check_start, success_start, js_frame_index, js_frame_index_alert, is_vent_light_playing, is_hall_sound_playing, camera_mode, light_on, charging, last_charge, music_box_playing, current_cam, foxy_sequence_start, black_screen_alpha, foxy_sound_played, foxy_sound_end, bb_sound_count, bb_move_time, bb_mask_start, bb_in_office, bb_laugh_playing, bb_last_speak_time, bb_idle_start, bb_return_idle, flash_error_playing, monitor_animation_start, pomexi_frame, monitor_button_hovered, mask_button_hovered, mask_animation_state, mask_animation_start, mask_animation_frame
    
    for bot in bots:
        bot.reset()
    
    set_ai_levels()
    
    game_time_ms = 0
    hour = 12
    office_x = 0
    mask_on = False
    mask_on_start = 0
    is_breathing_playing = False
    active_js_bot = None
    checking_bot = None
    check_type = ""
    check_start = 0
    success_start = 0
    js_frame_index = 0
    js_frame_index_alert = 0
    is_vent_light_playing = False
    is_hall_sound_playing = False
    camera_mode = False
    light_on = False
    charging = False
    last_charge = 0
    music_box_playing = False
    current_cam = '11'
    foxy_sequence_start = 0
    black_screen_alpha = 0
    foxy_sound_played = False
    foxy_sound_end = 0
    bb_sound_count = 0
    bb_move_time = 0
    bb_mask_start = 0
    bb_in_office = False
    bb_laugh_playing = False
    bb_last_speak_time = 0
    bb_idle_start = pygame.time.get_ticks()
    bb_return_idle = False
    flash_error_playing = False
    monitor_animation_start = 0
    pomexi_frame = 0
    monitor_button_hovered = False
    mask_button_hovered = False
    mask_animation_state = None
    mask_animation_start = 0
    mask_animation_frame = 0

play_sound(menu_music, -1)
menu_music_start_time = pygame.time.get_ticks()

while running:
    dt = clock.tick(30)
   
    js_frame_index_alert += 1
    pomexi_frame += 1
   
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
       
        if game_state == "BUG_REPORT" and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                bug_report_text = bug_report_text[:-1]
            elif event.key == pygame.K_ESCAPE:
                game_state = "MENU"
                bug_report_text = ""
                bug_report_category = ""
            elif event.key not in [pygame.K_RETURN, pygame.K_TAB] and len(bug_report_text) < 500:
                bug_report_text += event.unicode
       
        if event.type == pygame.KEYDOWN:
            if game_state in ["PLAY", "CHECKING"]:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LCTRL] and keys[pygame.K_h] and keys[pygame.K_g] and keys[pygame.K_f]:
                    dev_mode_active = not dev_mode_active
                
                if bb_in_office and event.key in [pygame.K_x, pygame.K_c, pygame.K_z] and not flash_error_playing:
                    play_sound(flash_error)
                    flash_error_playing = True
            
            if game_state == "MENU":
                if event.key == pygame.K_UP:
                    if menu_selected == -1:
                        menu_selected = 0
                    else:
                        menu_selected = max(0, menu_selected - 1)
                        # Пропускаем КАСТОМ НАЙТ если он заблокирован
                        if menu_selected == 2 and not is_custom_unlocked:
                            menu_selected = max(0, menu_selected - 1)
                elif event.key == pygame.K_DOWN:
                    if menu_selected == -1:
                        menu_selected = 0
                    else:
                        menu_selected = min(3, menu_selected + 1)
                        # Пропускаем КАСТОМ НАЙТ если он заблокирован
                        if menu_selected == 2 and not is_custom_unlocked:
                            menu_selected = 3
                elif event.key in [pygame.K_RETURN, pygame.K_SPACE] and menu_selected != -1:
                    action = menu_buttons[menu_selected]["action"]
                    if menu_selected == 2 and not is_custom_unlocked:
                        continue
                    
                    if action == "new_game":
                        current_night = 1
                        save_progress()
                        is_custom_night = False
                        reset_game()
                        game_state = "PLAY"
                        stop_sound(menu_music)
                        beat_detector.reset()
                    elif action == "continue":
                        is_custom_night = False
                        reset_game()
                        game_state = "PLAY"
                        stop_sound(menu_music)
                        beat_detector.reset()
                    elif action == "custom":
                        game_state = "CUSTOM"
                    elif action == "mods":
                        scan_mods()  # Обновляем список модов
                        game_state = "MODS"
            
            # FIX 2: Обработка нажатия клавиши на экране 6AM
            if game_state == "SIX_AM_ANIMATION":
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    # Пропускаем анимацию
                    stop_sound(six_am_theme)
                    if not is_custom_night:
                        current_night += 1
                        if current_night > 6:
                            current_night = 6
                            is_custom_unlocked = True
                        save_progress()
                    game_state = "MENU"
                    play_sound(menu_music, -1)
                    menu_music_start_time = pygame.time.get_ticks()
                    beat_detector.reset()
            
            if game_state in ["GAMEOVER"]:
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    game_state = "MENU"
                    play_sound(menu_music, -1)
                    menu_music_start_time = pygame.time.get_ticks()
                    beat_detector.reset()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_state in ["PLAY", "CHECKING"]:
                if camera_mode:
                    mouse_pos = pygame.mouse.get_pos()
                    for cam_id, cam_data in cam_buttons.items():
                        adjusted_rect = cam_data['rect'].copy()
                        adjusted_rect.move_ip(map_pos)
                        if adjusted_rect.collidepoint(mouse_pos):
                            current_cam = cam_id
                            break
                    
                    if current_cam == '11' and puppet.charge > 0 and puppet.pos == "Box":
                        if charge_button_rect.collidepoint(mouse_pos):
                            charging = True
                            last_charge = pygame.time.get_ticks()
                            play_sound(music_box_charge, -1)
            
            if game_state == "BUG_REPORT":
                mouse_pos = pygame.mouse.get_pos()
               
                close_btn = pygame.Rect(WIN_W // 2 + 350, WIN_H // 2 - 250, 40, 40)
                if close_btn.collidepoint(mouse_pos):
                    game_state = "MENU"
                    bug_report_text = ""
                    bug_report_category = ""
               
                for i, cat in enumerate(bug_categories):
                    cat_rect = pygame.Rect(WIN_W // 2 - 300, WIN_H // 2 - 50 + i * 60, 30, 30)
                    if cat_rect.collidepoint(mouse_pos):
                        bug_report_category = cat
               
                submit_btn = pygame.Rect(WIN_W // 2 - 100, WIN_H // 2 + 200, 200, 50)
                can_submit = len(bug_report_text.strip()) > 0 and bug_report_category != ""
                if submit_btn.collidepoint(mouse_pos) and can_submit:
                    if can_submit_bug_report():
                        if send_bug_report_to_discord(bug_report_text, bug_report_category):
                            last_bug_report_time = time.time()
                            save_progress()
                            bug_report_text = ""
                            bug_report_category = ""
                            game_state = "MENU"
            
            if game_state == "MODS":
                mouse_pos = pygame.mouse.get_pos()
                
                # Кнопка закрыть
                close_btn = pygame.Rect(WIN_W // 2 + 350, WIN_H // 2 - 300, 40, 40)
                if close_btn.collidepoint(mouse_pos):
                    game_state = "MENU"
                
                # Кнопка "Папка с модами"
                open_folder_btn = pygame.Rect(WIN_W // 2 - 100, WIN_H // 2 + 230, 200, 50)
                if open_folder_btn.collidepoint(mouse_pos):
                    open_mods_folder()
                
                # Обработка кликов по модам
                mods_window_y = WIN_H // 2 - 250
                for i, mod in enumerate(available_mods):
                    mod_y = mods_window_y + 50 + i * 80
                    
                    # Проверяем, установлен ли этот мод
                    is_this_mod_installed = installed_mod and installed_mod['name'] == mod['name']
                    
                    if is_this_mod_installed:
                        # Кнопка "Запустить"
                        launch_btn = pygame.Rect(WIN_W // 2 + 100, mod_y + 10, 150, 40)
                        if launch_btn.collidepoint(mouse_pos):
                            if launch_mod(mod):
                                # Мод успешно запущен
                                pass
                        
                        # Кнопка "Удалить"
                        uninstall_btn = pygame.Rect(WIN_W // 2 + 260, mod_y + 10, 80, 40)
                        if uninstall_btn.collidepoint(mouse_pos):
                            uninstall_mod()
                            save_progress()
                    else:
                        # Кнопка "Установить"
                        install_btn = pygame.Rect(WIN_W // 2 + 100, mod_y + 10, 150, 40)
                        if install_btn.collidepoint(mouse_pos):
                            # Сначала удаляем предыдущий мод, если есть
                            if installed_mod:
                                uninstall_mod()
                            install_mod(mod)
                            save_progress()
            
            if game_state == "MENU":
                mouse_pos = pygame.mouse.get_pos()
               
                if rect_bug.collidepoint(mouse_pos):
                    game_state = "BUG_REPORT"
                    bug_report_text = ""
                    bug_report_category = ""
               
                for i, rect in enumerate(menu_button_rects):
                    if i == 2 and not is_custom_unlocked:
                        continue
                    if rect.collidepoint(mouse_pos):
                        action = menu_buttons[i]["action"]
                        if action == "new_game":
                            current_night = 1
                            save_progress()
                            is_custom_night = False
                            reset_game()
                            game_state = "PLAY"
                            stop_sound(menu_music)
                            beat_detector.reset()
                        elif action == "continue":
                            is_custom_night = False
                            reset_game()
                            game_state = "PLAY"
                            stop_sound(menu_music)
                            beat_detector.reset()
                        elif action == "custom":
                            game_state = "CUSTOM"
                        elif action == "mods":
                            scan_mods()  # Обновляем список модов
                            game_state = "MODS"
                
                if rect_tg.collidepoint(mouse_pos):
                    webbrowser.open("https://t.me/sh4destudio")
                if rect_tiktok.collidepoint(mouse_pos):
                    webbrowser.open("https://www.tiktok.com/@sh4de_o")
            
            if game_state == "CUSTOM":
                mouse_pos = pygame.mouse.get_pos()
                for name in custom_characters:
                    if custom_rects_left[name].collidepoint(mouse_pos):
                        custom_levels[name] = max(0, custom_levels[name] - 1)
                    if custom_rects_right[name].collidepoint(mouse_pos):
                        custom_levels[name] = min(20, custom_levels[name] + 1)
                
                if rect_start_custom.collidepoint(mouse_pos):
                    is_custom_night = True
                    for bot in bots:
                        if bot.name in custom_levels:
                            bot.ai_level = custom_levels[bot.name]
                    reset_game()
                    game_state = "PLAY"
                    stop_sound(menu_music)
                    beat_detector.reset()
            
            # FIX 2: Обработка клика на экране 6AM
            if game_state == "SIX_AM_ANIMATION":
                stop_sound(six_am_theme)
                if not is_custom_night:
                    current_night += 1
                    if current_night > 6:
                        current_night = 6
                        is_custom_unlocked = True
                    save_progress()
                game_state = "MENU"
                play_sound(menu_music, -1)
                menu_music_start_time = pygame.time.get_ticks()
                beat_detector.reset()
            
            if game_state in ["GAMEOVER"]:
                game_state = "MENU"
                play_sound(menu_music, -1)
                menu_music_start_time = pygame.time.get_ticks()
                beat_detector.reset()
        
        if event.type == pygame.MOUSEBUTTONUP:
            if game_state in ["PLAY", "CHECKING"]:
                if charging:
                    charging = False
                    stop_sound(music_box_charge)
        
        if event.type == pygame.MOUSEMOTION and game_state == "MENU":
            mouse_pos = pygame.mouse.get_pos()
            menu_selected = -1
            for i, rect in enumerate(menu_button_rects):
                # Пропускаем КАСТОМ НАЙТ если не разблокирован
                if i == 2 and not is_custom_unlocked:
                    continue
                if rect.collidepoint(mouse_pos):
                    menu_selected = i
                    break
    
    if game_state in ["PLAY", "CHECKING"]:
        mouse_pos = pygame.mouse.get_pos()
       
        current_monitor_hover = monitor_button_rect.collidepoint(mouse_pos)
        if current_monitor_hover and not monitor_button_hovered:
            # FIX 3: Остановить звук зарядки при наведении на кнопку камеры
            if charging:
                charging = False
                stop_sound(music_box_charge)
            
            if not camera_mode and mask_animation_state != "equipping" and mask_animation_state != "equipped":
                game_state = "MONITOR_OPENING"
                monitor_animation_start = pygame.time.get_ticks()
            elif camera_mode:
                game_state = "MONITOR_CLOSING"
                monitor_animation_start = pygame.time.get_ticks()
                if music_box_playing:
                    stop_sound(music_box_song)
                music_box_playing = False
        monitor_button_hovered = current_monitor_hover
       
        current_mask_hover = mask_button_rect.collidepoint(mouse_pos)
        if current_mask_hover and not mask_button_hovered:
            if mask_animation_state is None and not camera_mode:
                # Начинаем анимацию надевания маски
                mask_animation_state = "equipping"
                mask_animation_start = pygame.time.get_ticks()
                mask_animation_frame = 0
                play_sound(mask_equip_sound)
            elif mask_animation_state == "equipped":
                # Начинаем анимацию снятия маски
                mask_animation_state = "unequipping"
                mask_animation_start = pygame.time.get_ticks()
                mask_animation_frame = 0
                play_sound(mask_unequip_sound)
                if is_breathing_playing:
                    stop_sound(mask_breathing_sound)
                    is_breathing_playing = False
        mask_button_hovered = current_mask_hover
    
    # Обновление анимации маски
    if mask_animation_state == "equipping":
        if mask_equip_frames:
            now = pygame.time.get_ticks()
            elapsed = now - mask_animation_start
            cum_time = 0
            finished = True
            
            for i, (surf, dur) in enumerate(mask_equip_frames):
                if elapsed < cum_time + dur:
                    mask_animation_frame = i
                    finished = False
                    break
                cum_time += dur
            
            if finished:
                # Анимация закончилась, теперь маска надета
                mask_animation_state = "equipped"
                mask_on = True
                mask_on_start = pygame.time.get_ticks()
    
    elif mask_animation_state == "unequipping":
        if mask_unequip_frames:
            now = pygame.time.get_ticks()
            elapsed = now - mask_animation_start
            cum_time = 0
            finished = True
            
            for i, (surf, dur) in enumerate(mask_unequip_frames):
                if elapsed < cum_time + dur:
                    mask_animation_frame = i
                    finished = False
                    break
                cum_time += dur
            
            if finished:
                # Анимация закончилась, маска снята
                mask_animation_state = None
                mask_on = False
    
    if game_state in ["PLAY", "CHECKING"]:
        game_time_ms += dt
        if game_time_ms >= HOUR_DURATION:
            game_time_ms = 0
            hour = 1 if hour == 12 else hour + 1
            # Изменяем AI только в обычном режиме, не в кастом найт
            if not is_custom_night and hour == 3 and current_night == 1:
                foxy.ai_level = 1
            if hour == 6:
                # FIX 2: Переходим к анимации 6AM вместо экрана WIN
                for bot in bots:
                    bot.ai_level = 0
                stop_all_sounds()
                is_breathing_playing = False
                is_vent_light_playing = False
                is_hall_sound_playing = False
                music_box_playing = False
                charging = False
                bb_laugh_playing = False
                flash_error_playing = False
                game_state = "SIX_AM_ANIMATION"
                six_am_animation_start = pygame.time.get_ticks()
                six_am_frame_index = 0
                six_am_sound_playing = False
        
        keys = pygame.key.get_pressed()
        show_hall = keys[pygame.K_z] and mask_animation_state != "equipping" and mask_animation_state != "equipped" and not camera_mode and not bb_in_office
        show_vent_l = keys[pygame.K_x] and mask_animation_state != "equipping" and mask_animation_state != "equipped" and not camera_mode and not bb_in_office
        show_vent_r = keys[pygame.K_c] and mask_animation_state != "equipping" and mask_animation_state != "equipped" and not camera_mode and not bb_in_office
        light_on = keys[pygame.K_LCTRL] and camera_mode
        
        for bot in bots:
            bot.update(show_hall, dt)
        
        if camera_mode and current_cam == '11' and puppet.charge > 0:
            if not music_box_playing:
                play_sound(music_box_song, -1)
                music_box_playing = True
        else:
            if music_box_playing:
                stop_sound(music_box_song)
                music_box_playing = False
        
        now = pygame.time.get_ticks()
        bb_bot = next((b for b in bots if b.name == "Balloon Boy"), None)
        
        if bb_bot and bb_bot.ai_level > 2 and bb_bot.pos == "Game Area":
            if now - bb_idle_start < 15000:
                pass
            else:
                if bb_bot.ai_level <= 6:
                    interval = 12000
                elif bb_bot.ai_level <= 12:
                    interval = 8000
                else:
                    interval = random.choice([5000, 6000, 7000, 7500])
                
                if now - bb_last_speak_time >= interval:
                    bb_last_speak_time = now
                    sound = random.choice([bb_hi, bb_hello])
                    play_sound(sound)
                    bb_sound_count += 1
                    if bb_sound_count == 4:
                        bb_move_time = now + 1000
        
        if bb_bot and bb_bot.pos == "Game Area" and bb_move_time > 0 and now >= bb_move_time:
            if not any(b.pos == "Left Air Vent" for b in bots if b != bb_bot):
                bb_bot.pos = "Left Air Vent"
                bb_sound_count = 0
                bb_move_time = 0
                bb_bot.status_msg = "MOVING TO LEFT AIR VENT"
        
        if bb_bot and bb_bot.pos == "Office Vent Left":
            if mask_on:
                if bb_mask_start == 0:
                    bb_mask_start = now
                elif now - bb_mask_start >= 5000:
                    bb_bot.pos = "Game Area"
                    bb_mask_start = 0
                    bb_bot.status_msg = "RETURNING TO GAME AREA"
                    bb_idle_start = now
                    bb_return_idle = True
            else:
                bb_mask_start = 0
            
            if now - bb_bot.vent_arrival_time >= 10000:
                bb_bot.pos = "Office"
                bb_in_office = True
                bb_bot.status_msg = "IN OFFICE"
        
        if bb_in_office and not bb_laugh_playing:
            play_sound(bb_laught, -1)
            bb_laugh_playing = True
        
        if not bb_in_office and bb_laugh_playing:
            stop_sound(bb_laught)
            bb_laugh_playing = False
        
        if flash_error and flash_error.get_num_channels() == 0:
            flash_error_playing = False
        
        if game_state == "PLAY":
            for bot in bots:
                if bot.pos == "Office":
                    if bot.name == "Puppet":
                        if camera_mode:
                            camera_mode = False
                            if music_box_playing:
                                stop_sound(music_box_song)
                            music_box_playing = False
                        active_js_bot = bot.name
                        game_state = "JUMPSCARE"
                        js_frame_index = 0
                        stop_all_sounds()
                        play_sound(jumpscare_sound)
                    elif bot.name == "Withered Foxy":
                        if camera_mode:
                            camera_mode = False
                            if music_box_playing:
                                stop_sound(music_box_song)
                            music_box_playing = False
                        active_js_bot = bot.name
                        game_state = "JUMPSCARE"
                        js_frame_index = 0
                        stop_all_sounds()
                        play_sound(jumpscare_sound)
                    elif bot.name != "Balloon Boy":
                        if camera_mode:
                            camera_mode = False
                            if music_box_playing:
                                stop_sound(music_box_song)
                            music_box_playing = False
                            active_js_bot = bot.name
                            game_state = "JUMPSCARE"
                            js_frame_index = 0
                            stop_all_sounds()
                            play_sound(jumpscare_sound)
                        else:
                            checking_bot = bot
                            check_start = pygame.time.get_ticks()
                            check_type = "fail"
                            game_state = "CHECKING"
                            js_frame_index = 0
                            bot.status_msg = "Checking office..."
                            play_sound(check_sound, -1)
        
        if (show_vent_l or show_vent_r) and not is_vent_light_playing:
            play_sound(vent_light_sound, -1)
            is_vent_light_playing = True
        elif not (show_vent_l or show_vent_r) and is_vent_light_playing:
            stop_sound(vent_light_sound)
            is_vent_light_playing = False
        
        foxy_bot = next((b for b in bots if b.name == "Withered Foxy"), None)
        if foxy_bot:
            if foxy_bot.pos == "Hall" and not is_hall_sound_playing:
                play_sound(hall_sound, -1)
                is_hall_sound_playing = True
            elif foxy_bot.pos != "Hall" and is_hall_sound_playing:
                stop_sound(hall_sound)
                is_hall_sound_playing = False
        
        if mask_on and mask_animation_state == "equipped":
            now = pygame.time.get_ticks()
            if now - mask_on_start >= 2000 and not is_breathing_playing:
                play_sound(mask_breathing_sound, -1)
                is_breathing_playing = True
        
        if charging and camera_mode and current_cam == '11' and puppet.charge > 0 and puppet.pos == "Box":
            now = pygame.time.get_ticks()
            if music_box_charge:
                charge_time = music_box_charge.get_length() * 1000
                if now - last_charge >= charge_time:
                    puppet.charge = min(100, puppet.charge + 20)
                    last_charge = now
        
        screen.fill((0, 0, 0))
        
        if camera_mode:
            current_img = None
            if current_cam == '11':
                if light_on:
                    if puppet.charge > 0 and puppet.pos == "Box":
                        current_img = imgs["puppet_in_box_light"]
                    else:
                        if random.random() < 0.08:
                            game_state = "PUPPET_DANCE"
                            js_frame_index = 0
                            continue
                        else:
                            current_img = imgs["puppet_awake_light"]
                else:
                    current_img = imgs["puppet_box_no_light"]
                
                screen.blit(current_img, (0, 0))
               
                if puppet.charge > 0 and puppet.pos == "Box":
                    pygame.draw.rect(screen, (255, 255, 255), charge_button_rect)
                    charge_text = font_dev.render("Charge", True, (0, 0, 0))
                    screen.blit(charge_text, (charge_button_rect.x + 10, charge_button_rect.y + 10))
                   
                    charge_circle_center = (charge_button_rect.x - 100, charge_button_rect.y + 25)
                    radius = 20
                    pygame.draw.circle(screen, (0, 0, 0), charge_circle_center, radius, 2)
                    angle = 360 * (puppet.charge / 100)
                    rect = (charge_circle_center[0] - radius, charge_circle_center[1] - radius, radius * 2, radius * 2)
                    pygame.draw.arc(screen, (0, 255, 0), rect, 0, angle * (3.14159 / 180), 2)
            
            elif current_cam == '9':
                toy_bonnie = next(b for b in bots if b.name == "Toy Bonnie")
                toy_chica = next(b for b in bots if b.name == "Toy Chica")
                
                if light_on:
                    if toy_bonnie.pos == "Stage" and toy_chica.pos == "Stage":
                        current_img = imgs["stage_full_light"]
                    elif toy_bonnie.pos != "Stage" and toy_chica.pos == "Stage":
                        current_img = imgs["stage_freddy_chica_light"]
                    elif toy_bonnie.pos == "Stage" and toy_chica.pos != "Stage":
                        current_img = imgs["stage_bonnie_freddy_light"]
                    else:
                        current_img = imgs["stage_freddy_light"]
                else:
                    if toy_bonnie.pos == "Stage" and toy_chica.pos == "Stage":
                        current_img = imgs["stage_full"]
                    elif toy_bonnie.pos != "Stage" and toy_chica.pos == "Stage":
                        current_img = imgs["stage_freddy_chica"]
                    elif toy_bonnie.pos == "Stage" and toy_chica.pos != "Stage":
                        current_img = imgs["stage_bonnie_freddy"]
                    else:
                        current_img = imgs["stage_freddy"]
                
                screen.blit(current_img, (0, 0))
            
            elif current_cam == '4':
                toy_chica = next(b for b in bots if b.name == "Toy Chica")
                is_chica_there = toy_chica.pos == "Main Hall"
                
                if light_on:
                    if is_chica_there:
                        current_img = imgs["main_hall_toy_chica_light"]
                    else:
                        current_img = imgs["main_hall_clear_light"]
                else:
                    if is_chica_there:
                        current_img = imgs["main_hall_toy_chica"]
                    else:
                        current_img = imgs["main_hall_clear"]
                
                screen.blit(current_img, (0, 0))
            
            elif current_cam == '7':
                foxy_there = foxy_bot.pos == "Parts Service" if foxy_bot else False
                
                if light_on:
                    if foxy_there:
                        current_img = imgs["parts_service_all_light"]
                    else:
                        current_img = imgs["parts_service_without_foxy"]
                else:
                    current_img = imgs["parts_service_lo_light"]
                
                screen.blit(current_img, (0, 0))
            
            elif current_cam == '3':
                bb_there = bb_bot.pos == "Game Area" if bb_bot else False
                
                if light_on:
                    if bb_there:
                        current_img = imgs["game_area_bb_light"]
                    else:
                        current_img = imgs["game_area_clear_light"]
                else:
                    if bb_there:
                        current_img = imgs["game_area_bb"]
                    else:
                        current_img = imgs["game_area_clear"]
                
                screen.blit(current_img, (0, 0))
            
            elif current_cam == '5':
                toy_chica = next((b for b in bots if b.name == "Toy Chica"), None)
                bb_there = bb_bot.pos == "Left Air Vent" if bb_bot else False
                chica_there = toy_chica.pos == "Left Air Vent" if toy_chica else False
                
                if light_on:
                    if bb_there:
                        current_img = imgs["left_vent_bb_light"]
                    elif chica_there:
                        current_img = imgs["left_vent_toy_chicka"]
                    else:
                        current_img = imgs["left_vent"]
                else:
                    current_img = imgs["left_vent"]
                
                screen.blit(current_img, (0, 0))
            
            elif current_cam == '2':
                toy_bonnie = next(b for b in bots if b.name == "Toy Bonnie")
                is_bonnie_there = toy_bonnie.pos == "Party Room2"
                
                if light_on:
                    if is_bonnie_there:
                        current_img = imgs["party_room2_toy_bonnie_light"]
                    else:
                        current_img = imgs["party_room2_clear_light"]
                else:
                    if is_bonnie_there:
                        current_img = imgs["party_room2_toy_bonnie"]
                    else:
                        current_img = imgs["party_room2_clear"]
                
                screen.blit(current_img, (0, 0))
            
            elif current_cam == '8':
                current_img = imgs["cam8_view"]
                screen.blit(current_img, (0, 0))
            
            if pomexi_frames:
                pomexi_overlay = pomexi_frames[pomexi_frame % len(pomexi_frames)][0].copy()
                pomexi_overlay.set_alpha(89)
                screen.blit(pomexi_overlay, (0, 0))
            
            map_bg = pygame.Surface(map_size, pygame.SRCALPHA)
            map_bg.fill((20, 20, 20, 200))
            screen.blit(map_bg, map_pos)
           
            font_cam = pygame.font.SysFont("Arial", 16, bold=True)
            for cam_id, cam_data in cam_buttons.items():
                btn_rect = cam_data['rect'].copy()
                btn_rect.move_ip(map_pos)
               
                if cam_id == current_cam:
                    color = (50, 200, 50)
                else:
                    color = (60, 60, 60)
               
                pygame.draw.rect(screen, color, btn_rect)
                pygame.draw.rect(screen, (200, 200, 200), btn_rect, 2)
               
                cam_text = font_cam.render(cam_data['label'], True, (255, 255, 255))
                text_x = btn_rect.x + (btn_rect.width - cam_text.get_width()) // 2
                text_y = btn_rect.y + (btn_rect.height - cam_text.get_height()) // 2
                screen.blit(cam_text, (text_x, text_y))
        else:
            mouse_x, _ = pygame.mouse.get_pos()
            target_x = -(mouse_x / WIN_W) * (imgs["main"].get_width() - WIN_W)
            office_x += (target_x - office_x) * 0.1
            
            current_img = imgs["main"]
            
            if show_hall:
                current_img = imgs["hall_foxy"] if foxy_bot and foxy_bot.pos == "Hall" else imgs["hall_clear"]
            elif show_vent_l:
                if bb_bot and bb_bot.pos == "Office Vent Left":
                    current_img = imgs["office_bb_vent"]
                else:
                    chica_bot = next(b for b in bots if b.name == "Toy Chica")
                    current_img = imgs["vent_l_chica"] if chica_bot.pos == "Office Vent Left" else imgs["vent_l_clear"]
            elif show_vent_r:
                bonnie_bot = next(b for b in bots if b.name == "Toy Bonnie")
                current_img = imgs["vent_r_bonnie"] if bonnie_bot.pos == "Office Vent Right" else imgs["vent_r_clear"]
            
            screen.blit(current_img, (office_x, 0))
            
            if bb_in_office:
                screen.blit(imgs["office_bb"], (office_x, 0))
        
        if game_state == "CHECKING":
            now = pygame.time.get_ticks()
            
            if mask_on and check_type == "fail":
                check_type = "success"
                success_start = now
            
            if check_type == "fail" and now - check_start > 1300:
                active_js_bot = checking_bot.name
                game_state = "JUMPSCARE"
                js_frame_index = 0
                stop_all_sounds()
                play_sound(jumpscare_sound)
                
                if checking_bot.name == "Toy Chica" and random.random() < 0.05:
                    pass
            
            key = checking_bot.name + "_fail"
            frames = checks.get(key)
            if frames:
                frame_idx = js_frame_index % len(frames)
                screen.blit(frames[frame_idx][0], (office_x, 0))
                js_frame_index += 1
            
            if check_type == "success":
                if not mask_on:
                    active_js_bot = checking_bot.name
                    game_state = "JUMPSCARE"
                    js_frame_index = 0
                    stop_all_sounds()
                    play_sound(jumpscare_sound)
                elif now - success_start > 3000:
                    checking_bot.pos = checking_bot.start_pos if checking_bot.name == "Toy Bonnie" else "Stage"
                    checking_bot.last_think = pygame.time.get_ticks() + 3000
                    checking_bot.status_msg = "Waiting"
                    game_state = "PLAY"
                    stop_sound(check_sound)
        
        # Отрисовка анимации маски
        if mask_animation_state == "equipping" and mask_equip_frames:
            screen.blit(mask_equip_frames[mask_animation_frame][0], (0, 0))
        elif mask_animation_state == "equipped":
            screen.blit(imgs["mask"], (0, 0))
        elif mask_animation_state == "unequipping" and mask_unequip_frames:
            screen.blit(mask_unequip_frames[mask_animation_frame][0], (0, 0))
        
        if game_state in ["PLAY", "CHECKING"]:
            mouse_pos = pygame.mouse.get_pos()
            monitor_hover = monitor_button_rect.collidepoint(mouse_pos)
            mask_hover = mask_button_rect.collidepoint(mouse_pos)
           
            if mask_animation_state == "equipped":
                screen.blit(imgs["mask_button"], mask_button_rect)
            elif camera_mode:
                screen.blit(imgs["monitor_button"], monitor_button_rect)
            else:
                if mask_hover and mask_animation_state is None:
                    screen.blit(imgs["mask_button"], mask_button_rect)
                elif monitor_hover:
                    screen.blit(imgs["monitor_button"], monitor_button_rect)
                else:
                    screen.blit(imgs["monitor_button"], monitor_button_rect)
                    screen.blit(imgs["mask_button"], mask_button_rect)
       
        if puppet.charge < 50 and puppet.charge > 0:
            alert_frames = orange_alert_frames
            if puppet.charge < 20:
                alert_frames = red_alert_frames
            
            if alert_frames:
                frame_idx = js_frame_index_alert % len(alert_frames)
                alert_w, alert_h = alert_frames[0][0].get_size()
                screen.blit(alert_frames[frame_idx][0], (WIN_W - alert_w - 10, WIN_H - alert_h - 10))
        
        time_text = font_clock.render(f"{hour} AM", True, (255, 255, 255))
        screen.blit(time_text, (WIN_W - 150, 30))
        
        if dev_mode_active:
            dev_panel = pygame.Surface((420, 130), pygame.SRCALPHA)
            dev_panel.fill((0, 0, 0, 180))
            screen.blit(dev_panel, (10, 10))
            
            for i, bot in enumerate(bots):
                color = (0, 255, 0) if bot.pos == "Stage" else (255, 255, 0) if bot.pos == "Target" else (255, 0, 0)
                dev_txt = font_dev.render(f"{bot.name}: {bot.pos} | {bot.status_msg}", True, color)
                screen.blit(dev_txt, (15, 15 + i*30))
   
    elif game_state == "MONITOR_OPENING":
        if monitor_up_frames:
            now = pygame.time.get_ticks()
            elapsed = now - monitor_animation_start
            cum_time = 0
            current_surf = None
            
            for surf, dur in monitor_up_frames:
                if elapsed < cum_time + dur:
                    current_surf = surf
                    break
                cum_time += dur
            
            if current_surf:
                mouse_x, _ = pygame.mouse.get_pos()
                target_x = -(mouse_x / WIN_W) * (imgs["main"].get_width() - WIN_W)
                office_x += (target_x - office_x) * 0.1
                screen.blit(imgs["main"], (office_x, 0))
               
                if bb_in_office:
                    screen.blit(imgs["office_bb"], (office_x, 0))
               
                screen.blit(current_surf, (0, 0))
               
                screen.blit(imgs["monitor_button"], monitor_button_rect)
            else:
                camera_mode = True
                game_state = "PLAY"
        else:
            camera_mode = True
            game_state = "PLAY"
   
    elif game_state == "MONITOR_CLOSING":
        if monitor_down_frames:
            now = pygame.time.get_ticks()
            elapsed = now - monitor_animation_start
            cum_time = 0
            current_surf = None
            
            for surf, dur in monitor_down_frames:
                if elapsed < cum_time + dur:
                    current_surf = surf
                    break
                cum_time += dur
            
            if current_surf:
                screen.fill((0, 0, 0))
               
                screen.blit(current_surf, (0, 0))
               
                screen.blit(imgs["monitor_button"], monitor_button_rect)
            else:
                camera_mode = False
                game_state = "PLAY"
        else:
            camera_mode = False
            game_state = "PLAY"
    
    elif game_state == "MENU":
        current_time = pygame.time.get_ticks()
        elapsed_sec = (current_time - menu_music_start_time) / 1000.0
        beat_detector.update(elapsed_sec)
        shake_x, shake_y = beat_detector.get_shake_offset()
       
        screen.fill((0, 0, 0))
        screen.blit(imgs["menu"], (shake_x, shake_y))
        
        for i, btn in enumerate(menu_buttons):
            # Пропускаем КАСТОМ НАЙТ если не разблокирован
            if i == 2 and not is_custom_unlocked:
                continue
            
            text_surf = menu_font.render(btn["text"], True, (255, 255, 255))
            x = 200 + shake_x
            
            # Правильное позиционирование
            if i <= 2:
                y = menu_button_y_start + i * menu_button_spacing + shake_y
            else:  # МОДЫ всегда под КАСТОМ НАЙТ
                y = menu_button_y_start + 3 * menu_button_spacing + shake_y
            
            screen.blit(text_surf, (x, y))
           
            if i == menu_selected:
                arrow_surf = menu_font.render(">>", True, (255, 255, 255))
                screen.blit(arrow_surf, (x - arrow_surf.get_width() - 20, y))
                
                if btn["action"] == "continue":
                    night_text = menu_font.render(f"НОЧЬ {current_night}", True, (255, 255, 255))
                    screen.blit(night_text, (x, y + text_surf.get_height() + 10))
        
        screen.blit(imgs["bug_icon"], (rect_bug.x + shake_x, rect_bug.y + shake_y))
        screen.blit(imgs["tg_icon"], (rect_tg.x + shake_x, rect_tg.y + shake_y))
        screen.blit(imgs["tiktok_icon"], (rect_tiktok.x + shake_x, rect_tiktok.y + shake_y))
    
    elif game_state == "BUG_REPORT":
        screen.fill((0, 0, 0))
       
        window_rect = pygame.Rect(WIN_W // 2 - 400, WIN_H // 2 - 250, 800, 500)
        pygame.draw.rect(screen, (40, 40, 40), window_rect)
        pygame.draw.rect(screen, (200, 200, 200), window_rect, 3)
       
        title = font_title.render("Сообщить о баге", True, (255, 255, 255))
        screen.blit(title, (WIN_W // 2 - title.get_width() // 2, WIN_H // 2 - 230))
       
        close_btn = pygame.Rect(WIN_W // 2 + 350, WIN_H // 2 - 250, 40, 40)
        pygame.draw.rect(screen, (150, 50, 50), close_btn)
        pygame.draw.rect(screen, (255, 255, 255), close_btn, 2)
        close_text = font_button.render("X", True, (255, 255, 255))
        screen.blit(close_text, (close_btn.x + 8, close_btn.y + 2))
       
        text_label = font_bug_report.render("Опишите баг:", True, (255, 255, 255))
        screen.blit(text_label, (WIN_W // 2 - 350, WIN_H // 2 - 180))
       
        text_box = pygame.Rect(WIN_W // 2 - 350, WIN_H // 2 - 150, 700, 100)
        pygame.draw.rect(screen, (60, 60, 60), text_box)
        pygame.draw.rect(screen, (200, 200, 200), text_box, 2)
       
        words = bug_report_text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if font_bug_input.size(test_line)[0] < 680:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)
       
        y_offset = 0
        for line in lines[-4:]:
            text_surf = font_bug_input.render(line, True, (255, 255, 255))
            screen.blit(text_surf, (text_box.x + 10, text_box.y + 10 + y_offset))
            y_offset += 25
       
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = text_box.x + 10 + font_bug_input.size(lines[-1] if lines else "")[0]
            cursor_y = text_box.y + 10 + (len(lines[-4:]) - 1) * 25
            pygame.draw.line(screen, (255, 255, 255), (cursor_x, cursor_y), (cursor_x, cursor_y + 20), 2)
       
        cat_label = font_bug_report.render("Категория:", True, (255, 255, 255))
        screen.blit(cat_label, (WIN_W // 2 - 350, WIN_H // 2 - 30))
       
        for i, cat in enumerate(bug_categories):
            y_pos = WIN_H // 2 - 50 + i * 60
           
            radio_rect = pygame.Rect(WIN_W // 2 - 300, y_pos, 30, 30)
            pygame.draw.circle(screen, (200, 200, 200), radio_rect.center, 15, 2)
           
            if bug_report_category == cat:
                pygame.draw.circle(screen, (50, 200, 50), radio_rect.center, 10)
           
            cat_text = font_bug_input.render(cat, True, (255, 255, 255))
            screen.blit(cat_text, (WIN_W // 2 - 260, y_pos + 5))
       
        submit_btn = pygame.Rect(WIN_W // 2 - 100, WIN_H // 2 + 200, 200, 50)
        can_submit = len(bug_report_text.strip()) > 0 and bug_report_category != ""
       
        if can_submit and can_submit_bug_report():
            btn_color = (50, 150, 50)
        else:
            btn_color = (100, 100, 100)
       
        pygame.draw.rect(screen, btn_color, submit_btn)
        pygame.draw.rect(screen, (200, 200, 200), submit_btn, 3)
        submit_text = font_button.render("Отправить", True, (255, 255, 255))
        screen.blit(submit_text, (submit_btn.x + (submit_btn.width - submit_text.get_width())//2, submit_btn.y + 10))
       
        if not can_submit_bug_report():
            minutes, seconds = get_time_until_next_report()
            cooldown_text = font_bug_input.render(f"Подождите {minutes}:{seconds:02d} до следующего отчета", True, (255, 100, 100))
            screen.blit(cooldown_text, (WIN_W // 2 - cooldown_text.get_width() // 2, WIN_H // 2 + 170))
    
    elif game_state == "MODS":
        screen.fill((0, 0, 0))
        
        # Окно модов
        window_width = 800
        window_height = 600
        window_x = WIN_W // 2 - window_width // 2
        window_y = WIN_H // 2 - window_height // 2
        
        window_rect = pygame.Rect(window_x, window_y, window_width, window_height)
        pygame.draw.rect(screen, (40, 40, 40), window_rect)
        pygame.draw.rect(screen, (200, 200, 200), window_rect, 3)
        
        # Заголовок
        title = font_title.render("Моды", True, (255, 255, 255))
        screen.blit(title, (WIN_W // 2 - title.get_width() // 2, window_y + 20))
        
        # Кнопка закрыть
        close_btn = pygame.Rect(WIN_W // 2 + 350, WIN_H // 2 - 300, 40, 40)
        pygame.draw.rect(screen, (150, 50, 50), close_btn)
        pygame.draw.rect(screen, (255, 255, 255), close_btn, 2)
        close_text = font_button.render("X", True, (255, 255, 255))
        screen.blit(close_text, (close_btn.x + 8, close_btn.y + 2))
        
        # Список модов
        mods_list_y = window_y + 80
        
        if len(available_mods) == 0:
            no_mods_text = font_mods.render("Модов пока нет. Добавьте .py файлы в папку с модами", True, (200, 200, 200))
            screen.blit(no_mods_text, (WIN_W // 2 - no_mods_text.get_width() // 2, mods_list_y + 50))
        else:
            for i, mod in enumerate(available_mods):
                mod_y = mods_list_y + i * 80
                
                # Имя мода
                mod_name_text = font_mods.render(mod['name'], True, (255, 255, 255))
                screen.blit(mod_name_text, (window_x + 30, mod_y))
                
                # Проверяем, установлен ли этот мод
                is_this_mod_installed = installed_mod and installed_mod['name'] == mod['name']
                
                if is_this_mod_installed:
                    # Кнопка "Запустить"
                    launch_btn = pygame.Rect(WIN_W // 2 + 100, mod_y + 10, 150, 40)
                    pygame.draw.rect(screen, (50, 150, 50), launch_btn)
                    pygame.draw.rect(screen, (200, 200, 200), launch_btn, 2)
                    launch_text = font_bug_report.render("Запустить", True, (255, 255, 255))
                    screen.blit(launch_text, (launch_btn.x + (launch_btn.width - launch_text.get_width())//2, launch_btn.y + 10))
                    
                    # Кнопка "Удалить"
                    uninstall_btn = pygame.Rect(WIN_W // 2 + 260, mod_y + 10, 80, 40)
                    pygame.draw.rect(screen, (150, 50, 50), uninstall_btn)
                    pygame.draw.rect(screen, (200, 200, 200), uninstall_btn, 2)
                    uninstall_text = font_bug_report.render("X", True, (255, 255, 255))
                    screen.blit(uninstall_text, (uninstall_btn.x + (uninstall_btn.width - uninstall_text.get_width())//2, uninstall_btn.y + 10))
                    
                    # Метка "Установлен"
                    installed_label = font_bug_input.render("(Установлен)", True, (50, 255, 50))
                    screen.blit(installed_label, (window_x + 30 + mod_name_text.get_width() + 10, mod_y + 5))
                else:
                    # Кнопка "Установить"
                    install_btn = pygame.Rect(WIN_W // 2 + 100, mod_y + 10, 150, 40)
                    pygame.draw.rect(screen, (100, 100, 150), install_btn)
                    pygame.draw.rect(screen, (200, 200, 200), install_btn, 2)
                    install_text = font_bug_report.render("Установить", True, (255, 255, 255))
                    screen.blit(install_text, (install_btn.x + (install_btn.width - install_text.get_width())//2, install_btn.y + 10))
        
        # Кнопка "Папка с модами" с закругленными углами
        open_folder_btn = pygame.Rect(WIN_W // 2 - 100, WIN_H // 2 + 230, 200, 50)
        
        # Рисуем закругленную кнопку
        pygame.draw.rect(screen, (70, 130, 180), open_folder_btn, border_radius=15)
        pygame.draw.rect(screen, (200, 200, 200), open_folder_btn, 3, border_radius=15)
        
        folder_btn_text = font_button.render("Папка с модами", True, (255, 255, 255))
        screen.blit(folder_btn_text, (open_folder_btn.x + (open_folder_btn.width - folder_btn_text.get_width())//2, open_folder_btn.y + 10))
        
        # FIX 1: Предупреждение теперь ПОД окном модов
        warning_y = window_y + window_height + 20  # Размещаем под окном с отступом
        warning_text1 = font_mods_warning.render("Внимание! Моды являются модификацией игрового кода.", True, (255, 50, 50))
        warning_text2 = font_mods_warning.render("Перед их скачиванием проверяйте мод на вирусы!", True, (255, 50, 50))
        
        screen.blit(warning_text1, (WIN_W // 2 - warning_text1.get_width() // 2, warning_y))
        screen.blit(warning_text2, (WIN_W // 2 - warning_text2.get_width() // 2, warning_y + 25))
    
    elif game_state == "CUSTOM":
        screen.fill((0, 0, 0))
        
        custom_title = font_title.render("Custom Night", True, (255, 255, 255))
        screen.blit(custom_title, (WIN_W//2 - custom_title.get_width()//2, 50))
       
        for i, name in enumerate(custom_characters):
            x, y = char_positions[i]
           
            level = custom_levels[name]
            
            if name == "Toy Bonnie":
                if 0 <= level <= 2:
                    face_key = "toy_bonnie_face"
                elif 3 <= level <= 6:
                    face_key = "toy_bonnie_face2"
                elif 7 <= level <= 20:
                    face_key = "toy_bonnie_face3"
                else:
                    face_key = "toy_bonnie_face"
            elif name == "Toy Chica":
                if 0 <= level <= 2:
                    face_key = "toy_chica_face"
                elif 3 <= level <= 6:
                    face_key = "toy_chica_face2"
                elif 7 <= level <= 20:
                    face_key = "toy_chica_face3"
                else:
                    face_key = "toy_chica_face"
            elif name == "Withered Foxy":
                if 0 <= level <= 2:
                    face_key = "withered_foxy_face"
                elif 3 <= level <= 6:
                    face_key = "withered_foxy_face2"
                elif 7 <= level <= 20:
                    face_key = "withered_foxy_face3"
                else:
                    face_key = "withered_foxy_face"
            elif name == "Puppet":
                face_key = "puppet_face"
            elif name == "Balloon Boy":
                if 0 <= level <= 2:
                    face_key = "bb_face"
                elif 3 <= level <= 6:
                    face_key = "bb_face2"
                elif 7 <= level <= 12:
                    face_key = "bb_face3"
                elif 13 <= level <= 20:
                    face_key = "bb_face4"
                else:
                    face_key = "bb_face"
           
            if face_key and face_key in imgs:
                face_img = imgs[face_key]
                face_x = x - face_img.get_width() // 2
                face_y = y - face_img.get_height() // 2 - 30
                screen.blit(face_img, (face_x, face_y))
           
            name_text = font_button.render(name, True, (255, 255, 255))
            name_x = x - name_text.get_width() // 2
            screen.blit(name_text, (name_x, y + 60))
           
            pygame.draw.rect(screen, (100, 100, 100), custom_rects_left[name])
            pygame.draw.rect(screen, (200, 200, 200), custom_rects_left[name], 2)
            left_arrow = font_button.render("<", True, (255, 255, 255))
            screen.blit(left_arrow, (custom_rects_left[name].x + 8, custom_rects_left[name].y + 5))
           
            level_rect = custom_level_rects[name]
            level_text = pygame.font.SysFont("Arial", 28, bold=True).render(str(custom_levels[name]), True, (255, 255, 0))
            level_x = level_rect.x + (level_rect.width - level_text.get_width()) // 2
            level_y = level_rect.y + (level_rect.height - level_text.get_height()) // 2
            screen.blit(level_text, (level_x, level_y))
           
            pygame.draw.rect(screen, (100, 100, 100), custom_rects_right[name])
            pygame.draw.rect(screen, (200, 200, 200), custom_rects_right[name], 2)
            right_arrow = font_button.render(">", True, (255, 255, 255))
            screen.blit(right_arrow, (custom_rects_right[name].x + 8, custom_rects_right[name].y + 5))
       
        pygame.draw.rect(screen, (50, 150, 50), rect_start_custom)
        pygame.draw.rect(screen, (200, 200, 200), rect_start_custom, 3)
        start_text = font_button.render("START", True, (255, 255, 255))
        screen.blit(start_text, (rect_start_custom.x + (rect_start_custom.width - start_text.get_width())//2, rect_start_custom.y + 10))
    
    elif game_state == "JUMPSCARE":
        screen.fill((0, 0, 0))
        frames = jumpscares.get(active_js_bot)
        
        if frames and js_frame_index < len(frames):
            screen.blit(frames[js_frame_index][0], (0, 0))
            js_frame_index += 1
        else:
            if active_js_bot == "Withered Foxy":
                game_state = "FOXY_SEQUENCE"
                foxy_sequence_start = pygame.time.get_ticks()
                black_screen_alpha = 0
                foxy_sound_played = False
                foxy_sound_end = 0
            else:
                game_state = "GAMEOVER"
    
    elif game_state == "FOXY_SEQUENCE":
        screen.fill((0, 0, 0))
        now = pygame.time.get_ticks()
        elapsed = now - foxy_sequence_start
        
        if elapsed < 600:
            black_screen_alpha = (elapsed / 600.0) * 255
        else:
            black_screen_alpha = 255
            if not foxy_sound_played:
                if elapsed >= 600 + 1000:
                    play_sound(foxy_line1_sound)
                    foxy_sound_played = True
                    if foxy_line1_sound:
                        foxy_sound_end = now + int(foxy_line1_sound.get_length() * 1000) + 300
                    else:
                        foxy_sound_end = now + 300
        
        if foxy_sound_played and now >= foxy_sound_end:
            fade_out_elapsed = now - foxy_sound_end
            if fade_out_elapsed < 600:
                black_screen_alpha = 255 - (fade_out_elapsed / 600.0) * 255
            else:
                game_state = "MENU"
                play_sound(menu_music, -1)
                menu_music_start_time = pygame.time.get_ticks()
                beat_detector.reset()
        
        black_surf = pygame.Surface((WIN_W, WIN_H))
        black_surf.fill((0, 0, 0))
        black_surf.set_alpha(int(black_screen_alpha))
        screen.blit(black_surf, (0, 0))
    
    elif game_state == "PUPPET_DANCE":
        screen.fill((0, 0, 0))
        
        if puppet_dance_frames and js_frame_index < len(puppet_dance_frames):
            screen.blit(puppet_dance_frames[js_frame_index][0], (0, 0))
            js_frame_index += 1
        else:
            active_js_bot = "Puppet"
            game_state = "JUMPSCARE"
            js_frame_index = 0
            stop_all_sounds()
            play_sound(jumpscare_sound)
    
    # FIX 2: Новое состояние для анимации 6AM
    elif game_state == "SIX_AM_ANIMATION":
        screen.fill((0, 0, 0))
        
        # Воспроизводим звук 6AM только один раз
        if not six_am_sound_playing:
            play_sound(six_am_theme)
            six_am_sound_playing = True
        
        # Показываем анимацию 6AM
        if six_am_frames and six_am_frame_index < len(six_am_frames):
            now = pygame.time.get_ticks()
            elapsed = now - six_am_animation_start
            cum_time = 0
            
            for i, (surf, dur) in enumerate(six_am_frames):
                if elapsed < cum_time + dur:
                    six_am_frame_index = i
                    screen.blit(surf, (0, 0))
                    break
                cum_time += dur
            else:
                # Анимация закончилась
                stop_sound(six_am_theme)
                if not is_custom_night:
                    current_night += 1
                    if current_night > 6:
                        current_night = 6
                        is_custom_unlocked = True
                    save_progress()
                game_state = "MENU"
                play_sound(menu_music, -1)
                menu_music_start_time = pygame.time.get_ticks()
                beat_detector.reset()
                six_am_sound_playing = False
        else:
            # Если гифка не загружена, показываем текст
            txt = font_main.render("6 AM", True, (255, 255, 255))
            screen.blit(txt, (WIN_W//2 - txt.get_width()//2, WIN_H//2 - 50))
            
            # Через 3 секунды переходим в меню
            now = pygame.time.get_ticks()
            if now - six_am_animation_start >= 3000:
                stop_sound(six_am_theme)
                if not is_custom_night:
                    current_night += 1
                    if current_night > 6:
                        current_night = 6
                        is_custom_unlocked = True
                    save_progress()
                game_state = "MENU"
                play_sound(menu_music, -1)
                menu_music_start_time = pygame.time.get_ticks()
                beat_detector.reset()
                six_am_sound_playing = False
    
    elif game_state == "GAMEOVER":
        screen.fill((0, 0, 0))
        
        msg = "ВЫ УМЕРЛИ"
        color = (255, 0, 0)
        txt = font_main.render(msg, True, color)
        screen.blit(txt, (WIN_W//2 - txt.get_width()//2, WIN_H//2 - 50))
       
        press_text = font_button.render("Нажмите любую кнопку для продолжения", True, (255, 255, 255))
        screen.blit(press_text, (WIN_W//2 - press_text.get_width()//2, WIN_H//2 + 50))
    
    pygame.display.flip()

save_progress()
pygame.quit()
