from __future__ import annotations
import asyncio
import hashlib
import hmac
import html
import io
import json
import logging
import os
import random
import sqlite3
import urllib.parse
from contextlib import contextmanager
from datetime import datetime, timedelta
import pytz
import aiohttp
from aiohttp import web
from PIL import Image, ImageDraw, ImageFont

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    ChatMemberUpdated,
    BufferedInputFile
)
from aiogram.enums import ParseMode, ChatType, ChatMemberStatus
from aiogram.types.reaction_type_emoji import ReactionTypeEmoji
from aiogram.exceptions import TelegramConflictError

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8843755987:AAF4gGBSVa1SKr8oxq26kX__C3b8WSkTFz4")
DEFAULT_GROUP_ID = int(os.getenv("GROUP_CHAT_ID", "-1004349705982"))
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "6377617416"))
TIMEZONE_STR = "Asia/Tashkent"
DB_NAME = "5amclub.db"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ==================== STRICT TIME-WINDOW ENFORCEMENT ====================
def is_time_in_window(start_str: str, end_str: str) -> bool:
    """
    Checks if current Asia/Tashkent time falls strictly between start_str and end_str (HH:MM).
    Supports overnight windows safely. Fail closed.
    """
    try:
        tz = pytz.timezone(TIMEZONE_STR)
        now = datetime.now(tz)
        now_time = now.time()

        s_hour, s_min = map(int, start_str.strip().split(":"))
        e_hour, e_min = map(int, end_str.strip().split(":"))

        start_time = datetime.now(tz).replace(hour=s_hour, minute=s_min, second=0, microsecond=0).time()
        end_time = datetime.now(tz).replace(hour=e_hour, minute=e_min, second=59, microsecond=999999).time()

        if start_time <= end_time:
            return start_time <= now_time <= end_time
        else:
            return now_time >= start_time or now_time <= end_time
    except Exception as e:
        logging.error(f"Error checking time window ({start_str} - {end_str}): {e}")
        return False

# ==================== TELEGRAM initData HMAC-SHA256 VERIFICATION ====================
def verify_telegram_init_data(init_data: str, bot_token: str = BOT_TOKEN) -> tuple[bool, dict]:
    """
    Validates Telegram WebApp initData query string using HMAC-SHA256 according to official spec.
    """
    if not init_data:
        return False, {}
    try:
        parsed_data = urllib.parse.parse_qsl(init_data, keep_blank_values=True)
        data_dict = dict(parsed_data)
        received_hash = data_dict.pop("hash", None)
        if not received_hash:
            return False, {}

        data_check_list = [f"{k}={v}" for k, v in sorted(data_dict.items())]
        data_check_string = "\n".join(data_check_list)

        secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            return False, {}

        user_data = {}
        if "user" in data_dict:
            user_data = json.loads(data_dict["user"])

        return True, {
            "user": user_data,
            "auth_date": int(data_dict.get("auth_date", 0)),
            "query_id": data_dict.get("query_id", ""),
            "raw": data_dict
        }
    except Exception as e:
        logging.error(f"HMAC Verification exception: {e}")
        return False, {}

# ==================== SMART PHOTO VERIFICATION (PILLOW) ====================
def verify_image_quality(image_bytes: bytes, strictness: str = "medium") -> tuple[bool, str]:
    """
    Analyzes brightness & variance using Pillow based on strictness setting.
    """
    thresholds = {
        "low": (15, 5),
        "medium": (26, 10),
        "high": (35, 15)
    }
    min_bright, min_std = thresholds.get(strictness.lower(), (26, 10))
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        thumb = img.resize((100, 100))
        pixels = list(thumb.getdata())

        brightnesses = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in pixels]
        avg_brightness = sum(brightnesses) / len(brightnesses)

        variance = sum((b - avg_brightness) ** 2 for b in brightnesses) / len(brightnesses)
        std_dev = variance ** 0.5

        if avg_brightness < min_bright:
            return False, "dark"
        if std_dev < min_std:
            return False, "blank"

        return True, "ok"
    except Exception as e:
        logging.error(f"Photo verification exception: {e}")
        return True, "ok"

# ==================== INFINITE RANDOM PHOTO MISSIONS ====================
PHOTO_MISSIONS = {
    "uz": [
        "☕ **Topshiriq:** Bugungi tonggi kofe yoki choyingiz rasmini yuboring!",
        "🌅 **Topshiriq:** Derazangizdan tonggi osmon yoki quyosh nuri rasmini oling!",
        "💧 **Topshiriq:** Yuzingizni yuvib, bir stakan toza suv rasmini yuboring!",
        "📖 **Topshiriq:** Bugun o'qiydigan kitobingiz yoki daftaringiz rasmini oling!",
        "👟 **Topshiriq:** Tonggi badantarbiya yoki krossovkalaringiz rasmini yuboring!",
        "💻 **Topshiriq:** Bugungi ish stolingiz yoki noutbukingiz rasmini oling!",
        "⏰ **Topshiriq:** Budilnik ko'rsatayotgan soat yoki xonangiz soatini rasmga oling!",
        "🍎 **Topshiriq:** Tonggi foydali nonushtangiz yoki meva rasmini yuboring!",
        "📝 **Topshiriq:** Bugungi rejalaringiz yozilgan qog'oz rasmini oling!",
        "🌳 **Topshiriq:** Ko'chaga chiqib, toza havodagi daraxt yoki tabiat rasmini yuboring!"
    ],
    "ru": [
        "☕ **Задание:** Сделайте фото вашего утреннего кофе или чая!",
        "🌅 **Задание:** Сфотографируйте утреннее небо или рассвет из окна!",
        "💧 **Задание:** Умойтесь и сфотографируйте стакан свежей воды!",
        "📖 **Задание:** Сделайте фото книги или блокнота на сегодня!",
        "👟 **Задание:** Сфотографируйте кроссовки или место для утренней зарядки!",
        "💻 **Задание:** Сделайте фото вашего рабочего стола или ноутбука!",
        "⏰ **Задание:** Сфотографируйте часы с временем вашего подъема!",
        "🍎 **Задание:** Отправьте фото вашего полезного утреннего завтрака!",
        "📝 **Задание:** Сфотографируйте список ваших задач на сегодня!",
        "🌳 **Задание:** Выйдите на свежий воздух и сфотографируйте природу!"
    ],
    "en": [
        "☕ **Mission:** Send a photo of your morning coffee or tea!",
        "🌅 **Mission:** Snap a photo of the morning sky or sunrise from your window!",
        "💧 **Mission:** Wash your face and send a photo of a glass of fresh water!",
        "📖 **Mission:** Take a photo of the book or notebook you are reading today!",
        "👟 **Mission:** Send a photo of your sneakers or morning workout spot!",
        "💻 **Mission:** Take a photo of your organized morning workspace!",
        "⏰ **Mission:** Snap a photo of the alarm clock showing your wake-up time!",
        "🍎 **Mission:** Send a photo of your healthy morning breakfast!",
        "🌳 **Mission:** Step outside and send a photo of fresh morning nature!"
    ]
}

# ==================== PILLOW ANNOUNCEMENT BANNER GENERATOR ====================
def generate_announcement_banner(title: str, subtitle: str, badge_icon: str = "🏆", theme: str = "gold") -> bytes:
    """
    Generates a high-quality visual banner image (PNG) using Pillow for announcements.
    """
    width, height = 800, 420
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    colors = {
        "gold": ((15, 23, 42), (45, 25, 10), (245, 158, 11)),
        "marvel": ((20, 10, 30), (60, 15, 25), (239, 68, 68)),
        "cyberpunk": ((10, 25, 40), (20, 10, 50), (6, 182, 212)),
        "anime": ((30, 10, 40), (50, 20, 10), (249, 115, 22))
    }
    bg_start, bg_end, accent = colors.get(theme, colors["gold"])

    for y in range(height):
        r = int(bg_start[0] + (bg_end[0] - bg_start[0]) * (y / height))
        g = int(bg_start[1] + (bg_end[1] - bg_start[1]) * (y / height))
        b = int(bg_start[2] + (bg_end[2] - bg_start[2]) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Outer ornate borders
    draw.rectangle([15, 15, width - 15, height - 15], outline=accent, width=4)
    draw.rectangle([25, 25, width - 25, height - 25], outline=(255, 255, 255, 60), width=1)

    try:
        font_large = ImageFont.truetype("arial.ttf", 34)
        font_sub = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font_large = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    draw.text((width / 2, 110), f"{badge_icon} {title} {badge_icon}", fill=accent, font=font_large, anchor="mm")
    draw.text((width / 2, 210), subtitle, fill=(241, 245, 249), font=font_sub, anchor="mm")
    draw.text((width / 2, 340), "★ THE 5 AM CLUB OFFICIAL ANNOUNCEMENT ★", fill=(148, 163, 184), font=font_sub, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# ==================== THEMED INLINE REACTION ENGINE ====================
REACTIONS_STORE = {}

REALM_REACTION_EMOJIS = {
    "marvel": [("🦸", "Avenger"), ("⚡", "Power"), ("🛡️", "Vibranium")],
    "samurai": [("🗡️", "Katana"), ("⚔️", "Bushido"), ("🏯", "Shogun")],
    "feudal": [("🏰", "Castle"), ("⚔️", "Knight"), ("👑", "King")],
    "mafia": [("🎩", "Syndicate"), ("🔫", "Capo"), ("💼", "Don")],
    "olympus": [("⚡", "Zeus"), ("🏛️", "Olympus"), ("🔱", "Poseidon")],
    "cyberpunk": [("🚀", "Sci-Fi"), ("🦾", "Cyber"), ("🛸", "UFO")],
    "anime": [("🥷", "Ninja"), ("💥", "Saiyan"), ("🌀", "Chakra")],
    "standard": [("👍", "Like"), ("🔥", "Fire"), ("⚡", "Power")]
}

def get_reaction_inline_keyboard(chat_id: int, message_id: int, realm: str = "standard", lang: str = "uz") -> InlineKeyboardMarkup:
    key = f"{chat_id}_{message_id}"
    store = REACTIONS_STORE.get(key, {"0": 0, "1": 0, "2": 0, "users": {}})

    emojis = REALM_REACTION_EMOJIS.get(realm.lower(), REALM_REACTION_EMOJIS["standard"])

    btn1 = f"{emojis[0][0]} {store.get('0', 0)}"
    btn2 = f"{emojis[1][0]} {store.get('1', 0)}"
    btn3 = f"{emojis[2][0]} {store.get('2', 0)}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=btn1, callback_data=f"react_0_{realm}"),
            InlineKeyboardButton(text=btn2, callback_data=f"react_1_{realm}"),
            InlineKeyboardButton(text=btn3, callback_data=f"react_2_{realm}")
        ]
    ])

def get_random_photo_mission(lang: str = "uz") -> str:
    missions = PHOTO_MISSIONS.get(lang, PHOTO_MISSIONS["uz"])
    return random.choice(missions)

# ==================== 7 MULTIVERSE ROLEPLAY REALMS + STANDARD ====================
REALMS = {
    "marvel": {
        "name": "🦸 Marvel Avengers Universe",
        "emoji": "🦸",
        "titles": {
            "uz": ["🕷️ Odam-O'rgimchak (Spider-Man)", "🛡️ Kapitan Amerika", "⚡ Tor (Thor)", "🦾 Temir Odam (Iron Man)", "🔮 Doktori Strendj"],
            "ru": ["🕷️ Человек-Паук (Spider-Man)", "🛡️ Капитан Америка", "⚡ Тор (Thor)", "🦾 Железный Человек", "🔮 Доктор Стрэндж"],
            "en": ["🕷️ Spider-Man", "🛡️ Captain America", "⚡ Thor", "🦾 Iron Man", "🔮 Doctor Strange"]
        },
        "quips": {
            "uz": [
                "Avengers, Assemble! Jarvis tizimlari 05:00 da to'liq shay holatda! 🛡️⚡",
                "Spider-Man: 'Buyuk intizom — buyuk mas'uliyat demakdir!' 🕷️⚡",
                "Stark Tech ertalabki Arc Reaktorini 100% ga quvvatladi! Wakanda Forever! 🦾🔥",
                "Tor chaqmoqlari bilan tongni yoritdi: 'Asgard intizomi bilan hech kim bellasha olmaydi!' ⚡🔨",
                "Kapitan Amerika: 'Biz buni butun kun davomida bajara olamiz!' 🛡️🌟",
                "Doktor Strendj 14 million kelajakni ko'rdi, faqat 05:00 da uyg'onganlar g'alaba qozonmoqda! 🔮⏳",
                "Qora Pantera: 'Wakandada intizom — eng buyuk kuchdir!' 🐾👑"
            ],
            "ru": [
                "Мстители, общий сбор! Системы Джарвиса готовы к утреннему бою! 🛡️⚡",
                "Человек-Паук: «С большой дисциплиной приходит великая сила!» 🕷️⚡",
                "Технологии Старка зарядили ваш ядерный реактор на 100%! Ваканда Навеки! 🦾🔥",
                "Тор осветил рассвет молнией: «Ничто не сравнится с дисциплиной Асгарда!» ⚡🔨",
                "Капитан Америка: «Я могу делать это весь день!» 🛡️🌟",
                "Доктор Стрэндж посмотрел 14 миллионов исходов: побеждают только вставшие в 5 утра! 🔮⏳",
                "Черная Пантера: «В Ваканде дисциплина — это высшая сила!» 🐾👑"
            ],
            "en": [
                "Avengers, Assemble! Jarvis systems online and fully operational! 🛡️⚡",
                "Spider-Man: 'With great morning discipline comes great power!' 🕷️⚡",
                "Stark Tech initialized your morning Arc Reactor to 100%! Wakanda Forever! 🦾🔥",
                "Thor strikes the dawn with thunder: 'None can match the discipline of Asgard!' ⚡🔨",
                "Captain America: 'I can do this all day!' 🛡️🌟",
                "Doctor Strange saw 14 million futures: only 5 AM risers conquer them all! 🔮⏳",
                "Black Panther: 'In Wakanda, discipline is the ultimate power!' 🐾👑"
            ]
        },
        "wisdom_prefix": "🦸 **MARVEL HERO WISDOM:** "
    },
    "samurai": {
        "name": "🗡️ Medieval Samurai Bushido",
        "emoji": "🗡️",
        "titles": {
            "uz": ["⚔️ Ronin Shogird", "🌸 Katana Ustasi (Kenshin)", "🏯 Musashi Jangchisi", "⛩️ Dojo Sensei (Hattori)", "👑 Buyuk Shogun"],
            "ru": ["⚔️ Ученик Ронин", "🌸 Мастер Катаны (Кэнсин)", "🏯 Воин Мусаси", "⛩️ Сенсей Додзё (Хаттори)", "👑 Великий Сёгун"],
            "en": ["⚔️ Ronin Initiate", "🌸 Katana Master (Kenshin)", "🏯 Musashi Warrior", "⛩️ Dojo Sensei (Hattori)", "👑 Grand Shogun"]
        },
        "quips": {
            "uz": [
                "Katana birinchi quyosh nuri tushmasidan oldin qinidan chiqarildi! Musashi intizomiga tasanno! ⚔️🌸",
                "Bushido Qoidasi #1: Haqiqiy usta uyqu ustidan sukunatda g'alaba qozonadi! 🏯⚡",
                "Sensei sizga chuqur ta'zim qiladi. Ruhingiz charxlangan yapon po'latidek porlamoqda! 🌸🔥",
                "Ronin yo'li — bu tonggi 05:00 da o'z nafsini yengish san'atidir! 🗡️⛩️",
                "Gilos gullari to'kilguncha, siz allaqachon zafarga erishdingiz! 🌸✨",
                "Miyamoto Musashi: 'Barcha jangga kirishdan oldin tongni yeng!' ⚔️🥋",
                "Buyuk Syogun sizning temir irodangizni e'tirof etdi! 🏯👑"
            ],
            "ru": [
                "Катана обнажена до первого луча солнца! Слава твоей дисциплине, Ронин! ⚔️🌸",
                "Кодекс Бусидо №1: Настоящий мастер побеждает сон в абсолютной тишине! 🏯⚡",
                "Сенсей кланяется вам. Ваш дух сияет как закаленная сталь! 🌸🔥",
                "Путь Ронина — это искусство побеждать себя каждое утро в 05:00! 🗡️⛩️",
                "Сакура еще не осыпалась, а вы уже совершили утреннюю победу! 🌸✨",
                "Миямото Мусаси: «Прежде чем победить врага, победи свое утро!» ⚔️🥋",
                "Великий Сёгун признал вашу железную волю! 🏯👑"
            ],
            "en": [
                "The Katana is unsheathed before dawn! Honor to your discipline, Ronin! ⚔️🌸",
                "Bushido Code #1: A true master conquers sleep in quiet solitude! 🏯⚡",
                "The Sensei bows in deep respect. Your spirit shines like polished steel! 🌸🔥",
                "The Way of the Ronin: Master yourself every day at 5 AM sharp! 🗡️⛩️",
                "Before the cherry blossoms fall, your morning victory is secured! 🌸✨",
                "Miyamoto Musashi: 'Before conquering any battle, conquer the dawn!' ⚔️🥋",
                "The Grand Shogun salutes your unbreakable warrior willpower! 🏯👑"
            ]
        },
        "wisdom_prefix": "🗡️ **BUSHIDO CODE WISDOM:** "
    },
    "feudal": {
        "name": "🏰 Feudal Knights & Excalibur",
        "emoji": "🏰",
        "titles": {
            "uz": ["🏰 Qal'a Ritsari", "⚔️ Lanselot Jangchisi", "🛡️ Kamelot Paladini", "👑 Davra Stoli Ritsari", "👑 Qirol Artur (King Arthur)"],
            "ru": ["🏰 Рыцарь Замка", "⚔️ Воин Ланселот", "🛡️ Паладин Камелота", "👑 Рыцарь Круглого Стола", "👑 Король Артур (King Arthur)"],
            "en": ["🏰 Castle Knight", "⚔️ Sir Lancelot", "🛡️ Camelot Paladin", "👑 Round Table Champion", "👑 High King Arthur"]
        },
        "quips": {
            "uz": [
                "Ekskalibur qilichi tongda baland ko'tarildi! Qirol Artur sizning jasoratingizni ulug'laydi! 🏰⚔️",
                "Davra stoli ritsarlari buyrug'i bilan sizning tonggi zafaringiz oltin bilan bitildi! 🛡️✨",
                "Qal'amiz devorlari ritsarlarimiz hushyor turganda aslo qulamaydi! 🏰🔥",
                "Ser Lanselot: 'Haqiqiy ritsarlik — har tong o'z so'zida turishdir!' 🛡️👑",
                "Qal'a minorasida zafar karnaylari yangradi! 05:00 intizom qahramoniga salom! 🎺🏰",
                "Gral kosasi erta turgan sharafli jangchilarga nasib etadi! 🏆✨",
                "Qirol Artur ritsarlari safiga xush kelibsiz, tonggi jasorat sohibi! 👑⚔️"
            ],
            "ru": [
                "Меч Экскалибур поднят на рассвете! Король Артур чтит твою доблесть! 🏰⚔️",
                "По указу Рыцарей Круглого Стола твоя победа вписана золотом! 🛡️✨",
                "Стены нашего замка нерушимы, пока рыцари встречают рассвет на страже! 🏰🔥",
                "Сэр Ланселот: «Истинное рыцарство — это держать слово каждое утро!» 🛡️👑",
                "На башнях замка звучат фанфары победы! Честь герою 5 утра! 🎺🏰",
                "Чаша Грааля покоряется лишь тем, кто бодрствует на заре! 🏆✨",
                "Добро пожаловать в орден Круглого Стола, хранитель рассвета! 👑⚔️"
            ],
            "en": [
                "Excalibur is raised high at dawn! King Arthur honors your noble valor! 🏰⚔️",
                "By order of the Round Table, your morning victory is recorded in gold! 🛡️✨",
                "Our castle walls stand indestructible while our Knights guard the dawn! 🏰🔥",
                "Sir Lancelot: 'True chivalry is honoring your commitment every single dawn!' 🛡️👑",
                "Castle horns sound across Camelot in honor of your 5 AM victory! 🎺🏰",
                "The Holy Grail reveals itself only to those who conquer the early morning! 🏆✨",
                "Welcome to the Knights of the Round Table, Master of Dawn! 👑⚔️"
            ]
        },
        "wisdom_prefix": "🏰 **EXCALIBUR KNIGHT WISDOM:** "
    },
    "mafia": {
        "name": "🎩 Italian Mafia Syndicate",
        "emoji": "🎩",
        "titles": {
            "uz": ["🎩 Sindikat A'zosi", "💼 Soldato Enforcer", "🔪 Kaporedjime", "🍷 Konsilyeri Anderboss", "👑 Don Korleone (The Godfather)"],
            "ru": ["🎩 Участник Синдиката", "💼 Сольдато", "🔪 Капореджиме", "🍷 Консильери Андербосс", "👑 Дон Корлеоне (The Godfather)"],
            "en": ["🎩 Syndicate Associate", "💼 Soldato Enforcer", "🔪 Caporegime", "🍷 Consigliere Underboss", "👑 Don Corleone (The Godfather)"]
        },
        "quips": {
            "uz": [
                "Don Korleone o'z hurmatini yo'lladi. 05:00 da intizom ko'rsatganlarga oila yordam beradi! 🎩💼",
                "Omertà intizom qoidasi: Oila ishlayotganda hech kim uxlab qolmaydi! 💼🔥",
                "Ertalabki taklifdan voz kechib bo'lmaydi. 5 AM Oilasiga cheksiz sodiqlik! 🎩👑",
                "Konsilyeri bu tonggi g'alabangizni maxsus daftarga qayd etdi! 🍷📑",
                "Sindikatda faqat erta uyg'onib, reja tuzganlar shaharga hukmronlik qiladi! 💼🌆",
                "Hech qanday bahona yo'q: hurmat qoidalari 05:00 da boshlanadi! 🎩⚡",
                "Don siz bilan faxrlanadi. Ishlarimiz gullab-yashnamoqda! 🌹💼"
            ],
            "ru": [
                "Дон Корлеоне шлет личное уважение. Семья всегда поддерживает дисциплинированных! 🎩💼",
                "Омерта Дисциплины: Когда Семья работает, никто не спит! 💼🔥",
                "Предложение, от которого рассвет не мог отказаться. Преданность Семье! 🎩👑",
                "Консильери внес твой утренний успех в золотую книгу Семьи! 🍷📑",
                "В Синдикате правят те, кто просыпается на рассвете и строит планы! 💼🌆",
                "Никаких оправданий: уважение и дисциплина начинаются ровно в 5 утра! 🎩⚡",
                "Дон гордится вами. Наш Синдикат процветает! 🌹💼"
            ],
            "en": [
                "Don Corleone sends his personal respects. Respect is earned at 5 AM sharp! 🎩💼",
                "Omertà of Discipline: Never sleep when the Family is building its empire! 💼🔥",
                "An offer the morning could not refuse. Absolute loyalty to the 5 AM Family! 🎩👑",
                "The Consigliere has recorded your dawn victory in the Family ledger! 🍷📑",
                "In the Syndicate, only those who wake up early rule the city! 💼🌆",
                "No excuses accepted: the rules of power begin at 05:00 AM! 🎩⚡",
                "The Don is proud of you. Our empire grows stronger today! 🌹💼"
            ]
        },
        "wisdom_prefix": "🎩 **GODFATHER SYNDICATE WISDOM:** "
    },
    "olympus": {
        "name": "⚡ Greek Olympus & Gods",
        "emoji": "⚡",
        "titles": {
            "uz": ["🏛️ Oddiy Qahramon", "🗡️ Axilles (Achilles)", "🛡️ Gerkules (Hercules)", "⚡ Apollon Olimplari", "👑 Zevs Hukmdori (Zeus)"],
            "ru": ["🏛️ Смертный Герой", "🗡️ Ахиллес (Achilles)", "🛡️ Геркулес (Hercules)", "⚡ Аполлон Олимпиец", "👑 Владыка Зевс (Zeus)"],
            "en": ["🏛️ Mortal Hero", "🗡️ Achilles Demigod", "🛡️ Hercules Champion", "⚡ Olympian Apollo", "👑 Supreme Zeus"]
        },
        "quips": {
            "uz": [
                "Zevs shiddatli chaqmoq yubordi! Olimpdagi ambroziya va shon-sharaf sizni kutmoqda! ⚡🏛️",
                "Gerkules 13-jasoratini bajarib, Apollon aravasidan oldin uyg'ondi! 🏛️☀️",
                "Titanlar sizning yengilmas tonggi intizomingizga ta'zim qilmoqda! 🌩️🔥",
                "Afinalik donishmandlar sizning tonggi qaroringizni e'tirof etdilar! 🦉✨",
                "Poseydon to'lqinlari kabi shiddatli energiya vujudingizni qamrab oldi! 🔱🌊",
                "Olimp xudolari bugungi kuningizga cheksiz omad ato etadi! ⚡🏛️",
                "Axilles kabi yengilmas iroda: uyqu ustidan mutlaq g'alaba! 🛡️⚡"
            ],
            "ru": [
                "Зевс метнул молнию победы! Амброзия и слава ждут тебя на Олимпе! ⚡🏛️",
                "Геркулес совершил 13-й подвиг: проснулся раньше колесницы Аполлона! 🏛️☀️",
                "Титаны склоняются перед твоей несокрушимой утренней дисциплиной! 🌩️🔥",
                "Афина мудрости благословляет твой выбор вставать на рассвете! 🦉✨",
                "Энергия, подобная штормам Посейдона, наполняет твой день! 🔱🌊",
                "Боги Олимпа даруют тебе непобедимую силу духа! ⚡🏛️",
                "Неуязвимость Ахиллеса в твоей дисциплине: абсолютная победа! 🛡️⚡"
            ],
            "en": [
                "Zeus strikes the lightning bolt! Ambrosia and glory await on Mount Olympus! ⚡🏛️",
                "Hercules completed his 13th labor: Waking up before Apollo's sun chariot! 🏛️☀️",
                "The Titans bow to your invincible morning discipline! 🌩️🔥",
                "Athena blesses your wisdom and relentless morning determination! 🦉✨",
                "Poseidon's ocean power surges through your morning energy! 🔱🌊",
                "The Olympian Gods grant victory and favor to your day! ⚡🏛️",
                "Achilles-level willpower: total triumph over sleep and slumber! 🛡️⚡"
            ]
        },
        "wisdom_prefix": "⚡ **OLYMPIAN GODS WISDOM:** "
    },
    "cyberpunk": {
        "name": "🚀 Cyberpunk Sci-Fi 2077",
        "emoji": "🚀",
        "titles": {
            "uz": ["🤖 Chooh2 Yuguruvchi", "⚡ Kiber Samurai (Neo)", "🦾 Netranner Kapitan", "🌌 Galaktika Admirali", "👑 Night City Afsonasi"],
            "ru": ["🤖 Бегун Chooh2", "⚡ Кибер Самурай (Neo)", "🦾 Нетраннер Капитан", "🌌 Адмирал Галактики", "👑 Легенда Найт-Сити"],
            "en": ["🤖 Chooh2 Runner", "⚡ Cyber Samurai (Neo)", "🦾 Netrunner Captain", "🌌 Galactic Admiral", "👑 Night City Legend"]
        },
        "quips": {
            "uz": [
                "Neyron sinxronizatsiya bajarildi! Night City fikserlari 5 AM xrom energiyangizni tasdiqladi! 🦾⚡",
                "Varp dvigateli va uyqu kodi o'chirildi... Vitality Overdrive yoqildi! 🌃⚡",
                "Uyg'on Samurai, bugun galaktikani zabt etadigan kunimiz bor! 💥🦾",
                "Kiber-implantlar 100% yuklandi. Bugun siz tarmoqdagi eng tezkor Netrannersiz! 🌐⚡",
                "Chooh2 yoqilg'isi quyildi! Kiber-poygada siz birinchi o'rindasiz! 🏎️💨",
                "Matritsa xatosi tuzatildi: uyqu blokatori muvaffaqiyatli sindirildi! 🕶️🟩",
                "Night City afsonasi sizsiz! 05:00 da xrom iroda sinovi topshirildi! 🦾👑"
            ],
            "ru": [
                "Нейро-синхронизация завершена! Фиксеры Найт-Сити подтвердили ваш утренний буст! 🦾⚡",
                "Сон отключен... Включен овердрайв бодрости и варп-двигатели! 🌃⚡",
                "Проснись, Самурай, у нас есть город, который ждет нашего прорыва! 💥🦾",
                "Киберимпланты заряжены на 100%. Вы — самый быстрый Нетраннер в сети! 🌐⚡",
                "Топливо Chooh2 залито! В утренней кибер-гонке вы на первом месте! 🏎️💨",
                "Сбой Матрицы устранен: протокол сна успешно взломан! 🕶️🟩",
                "Вы — новая легенда Найт-Сити! Хромовая воля активирована в 5 утра! 🦾👑"
            ],
            "en": [
                "Neural sync complete! Night City fixers verified your 5 AM chrome boost! 🦾⚡",
                "Sleep subroutine terminated... Vitality Overdrive engaged! 🌃⚡",
                "Wake up Samurai, we have a city to take over today! 💥🦾",
                "Cyber implants at 100% efficiency. You are the apex Netrunner today! 🌐⚡",
                "Chooh2 fuel loaded! You're dominating the morning cyber-race! 🏎️💨",
                "Matrix glitch resolved: sleep firewall successfully bypassed! 🕶️🟩",
                "Night City Legend status confirmed! 5 AM chrome discipline unlocked! 🦾👑"
            ]
        },
        "wisdom_prefix": "🚀 **CYBERPUNK SCI-FI WISDOM:** "
    },
    "anime": {
        "name": "🥷 Anime Multiverse (Konoha & Saiyans)",
        "emoji": "🥷",
        "titles": {
            "uz": ["🥷 Konoha Ninjasi", "🏴‍☠️ Pirate Captain (Luffy)", "⚡ Hokage (Naruto)", "💥 Super Saiyan (Goku)", "👑 Saitama One-Punch"],
            "ru": ["🥷 Ниндзя Конохи", "🏴‍☠️ Капитан Пиратов (Луффи)", "⚡ Хокаге (Наруто)", "💥 Супер Сайян (Гоку)", "👑 Сайтама One-Punch"],
            "en": ["🥷 Leaf Ninja (Naruto)", "🏴‍☠️ Pirate Captain (Luffy)", "⚡ Shadow Hokage", "💥 Super Saiyan (Goku)", "👑 Saitama One-Punch"]
        },
        "quips": {
            "uz": [
                "Dattebayo! Nindo intizomingiz quyoshdan oldin portladi! 🥷⚡",
                "Kamehameha! Ertalabki energiyangiz 9000 dan oshdi! 💥🔥",
                "Bir zarbli uyg'onish! Saitama sizning irodangizga ta'zim qiladi! 👑🥊",
                "One Piece izlab yo'lga chiqqan qaroqchilar tongda dengizga chiqadi! 🏴‍☠️🌊",
                "Sharingan ko'zlari ochildi: barcha to'siqlar va uyqu yo'q qilindi! 👁️🔥",
                "Bankai! Ruhiy kuchingiz eng yuqori cho'qqiga yetdi! 🗡️✨",
                "Hokage unvoni faqat har tong o'z so'zida turganlarga beriladi! 🥷👑"
            ],
            "ru": [
                "Даттебайо! Твой путь ниндзя начался до восхода солнца! 🥷⚡",
                "Камехамеха! Утренняя энергия зашкаливает за 9000! 💥🔥",
                "Подъем с одного удара! Сайтама выражает глубокое уважение! 👑🥊",
                "Команда Ван Пис отправляется в плавание на рассвете! 🏴‍☠️🌊",
                "Шаринган активирован: сон и лень побеждены без шансов! 👁️🔥",
                "Банкай! Твоя духовная сила достигла абсолютного максимума! 🗡️✨",
                "Титул Хокаге принадлежит лишь тем, кто никогда не отступает от своего слова! 🥷👑"
            ],
            "en": [
                "Dattebayo! Your Ninja Way woke up before the sun! 🥷⚡",
                "Kamehameha! Your morning power level is over 9000! 💥🔥",
                "One-Punch Wakeup! Saitama respects your iron discipline! 👑🥊",
                "The Straw Hat crew sets sail at dawn! Adventure awaits! 🏴‍☠️🌊",
                "Sharingan awakened: laziness and fatigue completely erased! 👁️🔥",
                "Bankai! Your spiritual morning willpower has reached peak power! 🗡️✨",
                "The title of Hokage belongs to those who conquer every single dawn! 🥷👑"
            ]
        },
        "wisdom_prefix": "🥷 **ANIME NINJA WISDOM:** "
    },
    "standard": {
        "name": "⚡ The 5 AM Club Standard",
        "emoji": "⚡",
        "titles": {
            "uz": ["🌅 Tonggi Yangi A'zo", "⚡ Tonggi Jangchi", "🦅 Lochin Nigoh", "🦁 Tonggi Arslon", "👑 5 AM Afsonasi"],
            "ru": ["🌅 Новичок 5 AM", "⚡ Воин Рассвета", "🦅 Соколиный Взор", "🦁 Утренний Лев", "👑 Легенда 5 AM"],
            "en": ["🌅 5 AM Initiate", "⚡ Dawn Warrior", "🦅 Falcon Sight", "🦁 Morning Lion", "👑 5 AM Legend"]
        },
        "quips": {
            "uz": [
                "Qarang, kim erta uyg'ondi! Kofe siz bilan faxrlanadi! ☕🔥",
                "Quyoshdan oldin uyg'ondingiz-a! Haqiqiy arslon intizomi! 🦁⚡",
                "Krovat sizni tutqinlikda ushlab turmoqchi edi, lekin iroda g'olib chiqdi! ⚔️😎",
                "Ertalabki g'alaba bilan tabriklayman! Bugungi kun sizniki! 🚀",
                "Dunyo uxlayotganda g'oliblar o'z kelajagini quradi! 🌟💪",
                "5 AM intizomi — muvaffaqiyatning yagona va ishonchli kalitidir! 🔑✨",
                "Uyg'onish g'alabasi muborak! Bugun buyuk ishlarni amalga oshiramiz! 🌅🏆"
            ],
            "ru": [
                "Смотрите, кто проснулся раньше всех! Кофе гордится тобой! ☕🔥",
                "Проснулся раньше солнца! Настоящий режим льва! 🦁⚡",
                "Кровать пыталась удержать тебя, но железная дисциплина победила! ⚔️😎",
                "Поздравляем с утренней победой! Этот день полностью твой! 🚀",
                "Пока весь мир спит, чемпионы куют свое великое будущее! 🌟💪",
                "Дисциплина 5 утра — это главный ключ к успеху и величию! 🔑✨",
                "С победой над рассветом! Сегодня нас ждут великие дела! 🌅🏆"
            ],
            "en": [
                "Look who decided to rise and conquer! Coffee is proud! ☕🔥",
                "Woke up before the sun! Absolute beast mode activated! 🦁⚡",
                "The bed tried to hold you hostage, but iron discipline won! ⚔️😎",
                "Congrats on the morning victory! Today belongs to you! 🚀",
                "While the world sleeps, champions forge their empire! 🌟💪",
                "5 AM Club discipline: the golden key to extraordinary mastery! 🔑✨",
                "Morning victory unlocked! Today we conquer greatness together! 🌅🏆"
            ]
        },
        "wisdom_prefix": "⚡ **5 AM DISCIPLINE WISDOM:** "
    }
}

# ==================== MULTI-LANGUAGE DICTIONARY ====================
TEXTS = {
    "uz": {
        "welcome": """👋 **"The 5 AM Club" botiga xush kelibsiz, {name}!**\n\n“Ertalabki vaqtingizga egalik qiling. Hayotingizni yuksaltiring.”\n\n⚙️ 4 ta asosiy katalog bo'limlaridan foydalaning:""",
        "hub_solo": """🌅 Solo Rejim""",
        "hub_multiverse": """🎭 Multiverse Roleplay""",
        "hub_arena": """🎮 Interaktiv Arena""",
        "hub_settings": """⚙️ Sozlamalar & Yordam""",
        "hub_quote": """💡 Kun Hikmati""",
        "btn_admin": """👑 Owner Admin Panel""",
        "checkin_btn_inline": """⚡ CHECK-IN QILISH (MEN UYG'ONDIM)""",
        "already_checked_in": """⚠️ Siz bugun allaqachon check-in qildingiz! Ertagacha! 🌅""",
        "not_in_window": """⚠️ Hozir check-in vaqti emas! Uyg'onish vaqti: {start} - {end} 🌅""",
        "photo_too_dark": """❌ Rasm qorong'u yoki talabga javob bermaydi! Yorug'roq va aniq rasm yuboring! 📸""",
        "solo_menu_title": """⚡ **SOLO CHECK-IN & SHAXSIY REJIM**\n\nIntizomingizni boshqarish uchun bo'limni tanlang:""",
        "multiverse_menu_title": """🎭 **MULTIVERSE ROLEPLAY PARK**\n\nO'zingizga yoqqan koinot (realm) atmosfarasini tanlang. Roleplay yoqilganda barcha xabarlar va unvonlar koinot ruhiga kiradi!""",
        "arena_menu_title": """🎮 **INTERAKTIV ARENA & DUYELLAR**\n\nBoshqa o'yinchilar bilan bellashing, duo sherik biriktiring va haftalik turnirda g'olib bo'ling!""",
        "settings_menu_title": """⚙️ **SOZLAMALAR & BOSHGARUV**\n\nVaqt, eslatma, foto strictness va til sozlamalarini boshqaring:""",
        "group_checkin_popup": """⚡ CHECK-IN MUVAFFAQIYATLI!\n🔥 Streak: {streak} kun | 🪙 +{coins} Tanga | 🌟 +{xp} XP""",
        "checkin_success": """⚡ **CHECK-IN MUVAFFAQIYATLI!**\n\n{quip}\n\n🔥 Streak: `{streak} kun` (Koeffitsiyent: `{multiplier}X`)\n🎯 Maqsad: `{streak}/{goal} kun`\n🪙 Tangalar: `+{coins_earned}` (Jami: `{coins}`)\n🌟 XP: `+{xp_earned}` (Jami: `{xp}` XP | Level `{level}`)\n⚡ Stamina: `100/100 🟢`\n🏅 Unvon: {rank}""",
        "photo_mission_prompt": """📸 **KUNLIK FOTO TOPSHIRIQ:**\n\n{mission}\n\n📌 **Shart:** Rasm yuboring! Bot **VERIFIED STAMP** muhrini bosadi! 🚀""",
        "photo_success": """📸 **FOTO CHECK-IN VERIFIED! (+{coins_earned} COIN, +{xp_earned} XP)**\n\n{quip}\n\n🔥 Streak: `{streak} kun` (Koeffitsiyent: `{multiplier}X`)\n🎯 Maqsad: `{streak}/{goal} kun`\n🪙 Tangalar: `+{coins_earned}` (Jami: `{coins}`)\n🌟 XP: `+{xp_earned}` (Jami: `{xp}` XP | Level `{level}`)\n⚡ Stamina: `100/100 🟢`\n🏅 Unvon: {rank}""",
        "profile_title": """👤 **FOYDALANUVCHI PROFILI & RPG STATS**\n\n🏷 Ism: {name}\n🛡 Level: `{level}` — **{level_title}**\n🌟 XP: `{xp} / {next_level_xp} XP` ({progress_pct}%)\n⚡ Stamina: `{stamina}/100` {stamina_badge}\n🔥 Streak: `{streak} Kun` | 🎯 Maqsad: `{streak}/{goal} Kun`\n🪙 Tangalar: `{coins}`\n⚔️ Turnir Ballari: `{tourney_pts} pts`\n👥 Taklif qilinganlar: `{ref_count} kishi`\n🛡 Streak Freeze: `{freeze_count} ta`\n🎭 Multiverse: `{universe_name}` (RP: `{rp_status}`)\n🌐 Til: `{lang_str}`\n⏰ Shaxsiy vaqt: `{start}` — `{end}`\n\n🏆 **TROPHY CABINET (NISHONLAR):**\n{badges}\n\n📈 **XP PROGRESSI:**\n{xp_bar}\n\n📈 **UNVON PROGRESSI:**\n{progress_bar}""",
        "ref_text": """👥 **DO'STLARNI TAKLIF QILISH**\n\nSizning shaxsiy havolangiz:\n`{ref_link}`\n\n📌 Har bir taklif qilgan do'stingiz uchun sizga ham, do'stingizga ham **+100 tanga** beriladi!\nJami taklif qilinganlar: `{ref_count} kishi`""",
        "leaderboard_title": """🏆 **THE 5 AM CLUB REYTING JADVALI** 🏆\n\n""",
        "leaderboard_empty": """🏆 Reyting jadvali hozircha bo'sh.""",
        "quote_title": """💡 **KUN HIKMATI**\n\n{quote}""",
        "help_text": """📖 **THE 5 AM CLUB — QOIDALAR**\n\n1. **Ertalabki Check-In**: Uyg'onish vaqti oralig'ida check-in qiling.\n2. **🎭 Multiverse Roleplay**: 7 ta koinotdan birini tanlab, motivatsiya muhitiga kiring.\n3. **⚡ RPG XP & Leveling**: Har bir uyg'onish XP beradi va yangi darajalarni ochadi.\n4. **🌙 21:30 Uyqu Protokoli**: Har kuni 21:30 da uxlashga yotib +20 XP va 100% Stamina oling.\n5. **⚔️ Haftalik Turnir**: Top-3 sohiblariga 1000 coin sovrin jamg'armasi!\n6. **🏆 Kunlik Maqsad Maraton**: 21, 30, 100 yoki 365 kunlik maqsadingizga erishing!""",
        "lang_select": """🌐 **Iltimos, tilni tanlang:**""",
        "lang_updated": """✅ **Bot tili O'zbek tiliga o'zgartirildi!**""",
        "shop_main": """🛒 **THE 5 AM CLUB MARKETPLACE**\n\nSizning tangalaringiz: 🪙 `{coins} tanga`\n\n1. 🛡 **Streak Freeze (Qalqon)** — `100 tanga`\n*(Uxlab qolganda Streakni saqlaydi)*""",
        "shop_buy_freeze_ok": """🎉 **Muvaffaqiyatli sotib olindi!** Sizda 1 ta 🛡 **Streak Freeze** bor!""",
        "shop_no_coins": """❌ **Tangalaringiz yetarli emas!** Sizda `{coins}` tanga bor.""",
        "games_main": """🎮 **O'YINLAR VA ARENA KATALOGI**\n\n⚔️ **1v1 Uyg'onish Dueli** — 50 coin tikib bellashish (-20 Stamina)\n🤝 **Duo Combo** — Sherik bilan birga uyg'onib bonus olish\n🎲 **Random Matchmaking** — Avtomatik begona sherik topish""",
        "matchmaking_searching": """🎲 **RANDOM SHERIK QIDIRILMOQDA...**\n\nTizim sizga mos begona o'yinchini qidirmoqda...""",
        "matchmaking_found": """🎉 **SHERIK TOPILDI!**\n\nSizning yangi Duo sherigingiz: `{partner_name}`!\nEndi erta uyg'onsangiz +50 bonus tanga olasiz! 🚀""",
        "duo_title": """🤝 **DUO COMBO SHERIKLIK TIZIMI**""",
        "duo_invite_prompt": """📌 Sherik biriktirish uchun: `/duo <sherik_id>` buyrug'ini yuboring!\nBirgalikda erta uyg'onib, har kuni **+50 bonus tanga** yuting! 🚀""",
        "setup_group": """⚙️ **Guruh uyg'onish vaqti oralig'ini tanlang:**""",
        "setup_user": """⚙️ **Shaxsiy uyg'onish vaqtingizni sozlang:**\nHozirgi vaqt: `{start}` — `{end}`""",
        "setup_updated": """✅ **Uyg'onish vaqti yangilandi:** `{start}` — `{end}` 🌅""",
        "cert_congrats": """🏆 **TABRIKLAYMIZ! MARATON YUKSAK ZAFARI!**\n\nSiz 21 kun uzluksiz soat 05:00 da uyg'onib, maratonni yakunladingiz!\nSizga rasmiy **21-Day Discipline Certificate** va **👑 Elite 21** nishoni berildi!""",
        "bedtime_btn": """😴 Men Uxlashga Yotdim (+20 XP)""",
        "bedtime_reminder": """🌙 **THE 5 AM CLUB: UXLASH PROTOKOLI (21:30)**\n\n🛌 *“Ertalabki vaqtingizga egalik qilish uchun uyqungizni asrang!”* – Robin Sharma\n\n✨ Ekranlarni o'chiring va 7.5 soatlik shifobaxsh uyquga tayyorlaning.\n\n👇 *Uxlashdan oldin quyidagi tugmani bosib +20 XP va 100% Stamina oling:*""",
        "bedtime_success": """😴 **XAYRLI TUN, CHAMPION! (+20 XP)**\n\n⚡ Staminangiz 100% tiklanmoqda. Ertalab soat 05:00 da kutamiz!""",
        "tournament_head": """⚔️ **5 AM HAFTALIK TOURNAMENT (SEZON #{season})** 🏆\n\n⏳ Tugash vaqti: `{end_date}` (Yakshanba 23:59)\n💰 Mukofot jamg'armasi: `1,000 Coin + 👑 Champion Badges`\n\n""",
        "tournament_empty": """⚔️ Turnirda hali qatnashchilar yo'q.""",
        "spin_btn": """🎰 Omad g'ildiragini aylantirish""",
        "spin_already": """⚠️ Siz bugun omad g'ildiragini aylantirib bo'ldingiz! Ertagacha! 🎰""",
        "spin_success": """🎰 **OMAD G'ILDIRAGI NATIV NESHONA!**\n\n🎉 Siz yutib oldingiz: **{reward_label}**!\nIntizomingiz sari davom eting! 🚀""",
        "squad_main": """🛡️ **5 AM DISCIPLINE SQUAD (KLAN)**\n\nSizning klainingiz: **{name}** `[{tag}]` (ID: `{squad_id}`)\n👑 Klan yetakchisi: `{leader_id}`\n👥 A'zolar soni: `{member_count}` ta\n🔥 Jami klan streaki: `{total_streak} kun`\n🌟 Jami XP: `{total_xp} XP`""",
        "squad_not_in": """🛡️ **Siz hali hech qanday klanga a'zo emassiz.**\n\nYangi klan yaratish uchun: `/squad_create <nomi> <tag>`\nKlanga qo'shilish uchun: `/squad_join <squad_id>`""",
        "squad_already": """⚠️ Siz allaqachon klanga a'zosiz! Dastlab joriy klandan chiqing.""",
        "squad_created": """🎉 **Klan muvaffaqiyatli yaratildi!**\n\n🛡️ Klan: **{name}** `[{tag}]` (ID: `{squad_id}`)\nEndi do'stlaringizni taklif qiling!""",
        "squad_joined": """🎉 **Klanga muvaffaqiyatli qo'shildingiz!**\n\n🛡️ Siz endi **{name}** `[{tag}]` klanining a'zosiz!""",
        "squad_not_found": """❌ Bunday ID ga ega klan topilmadi!""",
        "squad_leaderboard_title": """🛡️ **TOP-10 KLANLAR REYTINGI (5 AM CLANS)** 🛡️\n\n""",
        "badge_unlocked": """🎖️ **YANGI NISHON OCHILDI!**\n\nSiz **{badge_name}** nishonini qo'lga kiritdingiz! ({badge_desc}) 🚀""",
        "grp_awake_title": """🌅 **UYG'ONGAN A'ZOLAR RO'YXATI:**""",
        "grp_graveyard_title": """😴 **UXLAB QOLGANLAR QABRISTONI:**""",
        "grp_register_btn": """✋ Guruhda Registratsiyadan O'tish""",
        "grp_registered_pm": """Siz **{group}** guruhida 5 AM Club uchun omadli ro'yxatdan o'tdingiz :)""",
        "grp_to_group_btn": """Guruhga o'tish ↗"""
    },
    "ru": {
        "welcome": """👋 **Добро пожаловать в бот "The 5 AM Club", {name}!**\n\n«Владейте своим утром. Поднимите свою жизнь.»\n\n⚙️ Используйте 4 главных каталога ниже:""",
        "hub_solo": """🌅 Соло Режим""",
        "hub_multiverse": """🎭 Мультивселенная""",
        "hub_arena": """🎮 Интерактивная Арена""",
        "hub_settings": """⚙️ Настройки и Помощь""",
        "hub_quote": """💡 Мудрость Дня""",
        "btn_admin": """👑 Owner Admin Panel""",
        "checkin_btn_inline": """⚡ СДЕЛАТЬ CHECK-IN (Я ПРОСНУЛСЯ)""",
        "already_checked_in": """⚠️ Вы уже отметились сегодня! До завтра! 🌅""",
        "not_in_window": """⚠️ Сейчас не время для check-in! Время подъема: {start} - {end} 🌅""",
        "photo_too_dark": """❌ Фото слишком темное! Отправьте более четкое фото! 📸""",
        "solo_menu_title": """⚡ **СОЛО CHECK-IN И ЛИЧНЫЙ РЕЖИМ**\n\nВыберите действие для управления вашей дисциплиной:""",
        "multiverse_menu_title": """🎭 **ПАРК МУЛЬТИВСЕЛЕННЫХ ROLEPLAY**\n\nВыберите атмосферу вселенной. При включенном Roleplay все сообщения принимают дух выбранного мира!""",
        "arena_menu_title": """🎮 **ИНТЕРАКТИВНАЯ АРЕНА И ДУЭЛИ**\n\nСоревнуйтесь с другими игроками, привязывайте напарников и выигрывайте турниры!""",
        "settings_menu_title": """⚙️ **НАСТРОЙКИ И УПРАВЛЕНИЕ**\n\nУправляйте временем, напоминаниями, строгостью фото и языком:""",
        "group_checkin_popup": """⚡ CHECK-IN УСПЕШЕН!\n🔥 Стрик: {streak} дн. | 🪙 +{coins} Монет | 🌟 +{xp} XP""",
        "checkin_success": """⚡ **CHECK-IN УСПЕШЕН!**\n\n{quip}\n\n🔥 Стрик: `{streak} дней` (Множитель: `{multiplier}X`)\n🎯 Цель: `{streak}/{goal} дней`\n🪙 Монеты: `+{coins_earned}` (Всего: `{coins}`)\n🌟 XP: `+{xp_earned}` (Всего: `{xp}` XP | Level `{level}`)\n⚡ Энергия: `100/100 🟢`\n🏅 Ранг: {rank}""",
        "photo_mission_prompt": """📸 **ЕЖЕДНЕВНОЕ ФОТО-ЗАДАНИЕ:**\n\n{mission}\n\n📌 **Условие:** Отправьте фото! Бот поставит печать **VERIFIED STAMP**! 🚀""",
        "photo_success": """📸 **ФОТО CHECK-IN ПОДТВЕРЖДЕН! (+{coins_earned} МОНЕТ, +{xp_earned} XP)**\n\n{quip}\n\n🔥 Стрик: `{streak} дней` (Множитель: `{multiplier}X`)\n🎯 Цель: `{streak}/{goal} дней`\n🪙 Монеты: `+{coins_earned}` (Всего: `{coins}`)\n🌟 XP: `+{xp_earned}` (Всего: `{xp}` XP | Level `{level}`)\n⚡ Энергия: `100/100 🟢`\n🏅 Ранг: {rank}""",
        "profile_title": """👤 **ПРОФИЛЬ УЧАСТНИКА & RPG СТАТИСТИКА**\n\n🏷 Имя: {name}\n🛡 Уровень: `{level}` — **{level_title}**\n🌟 XP: `{xp} / {next_level_xp} XP` ({progress_pct}%)\n⚡ Энергия: `{stamina}/100` {stamina_badge}\n🔥 Стрик: `{streak} Дней` | 🎯 Цель: `{streak}/{goal} Дней`\n🪙 Монеты: `{coins}`\n⚔️ Турнирные Очки: `{tourney_pts} pts`\n👥 Приглашено: `{ref_count} чел`\n🛡 Защита Стрика: `{freeze_count} шт`\n🎭 Вселенная: `{universe_name}` (RP: `{rp_status}`)\n🌐 Язык: `{lang_str}`\n⏰ Время: `{start}` — `{end}`\n\n🏆 **ВИТРИНА НАГРАД:**\n{badges}\n\n📈 **ПРОГРЕСС УРОВНЯ:**\n{xp_bar}\n\n📈 **ПРОГРЕСС РАНГА:**\n{progress_bar}""",
        "ref_text": """👥 **ПРИГЛАШАЙТЕ ДРУЗЕЙ**\n\nВаша ссылка:\n`{ref_link}`\n\n📌 За каждого друга вам и другу начисляется **+100 монет**!\nПриглашено: `{ref_count} чел`""",
        "leaderboard_title": """🏆 **ТАБЛИЦА ЛИДЕРОВ THE 5 AM CLUB** 🏆\n\n""",
        "leaderboard_empty": """🏆 Таблица лидеров пока пуста.""",
        "quote_title": """💡 **МУДРОСТЬ ДНЯ**\n\n{quote}""",
        "help_text": """📖 **THE 5 AM CLUB — ПРАВИЛА**\n\n1. **Утренний Check-In**: Отмечайтесь строго в заданное время.\n2. **🎭 Roleplay**: Выберите одну из 7 вселенных.\n3. **⚡ RPG XP & Уровни**: Каждый подъем дает опыт!\n4. **🌙 21:30 Протокол Сна**: Ложитесь вовремя и получайте +20 XP.\n5. **⚔️ Недельный Турнир**: Еженедельный призовой фонд 1000 монет!\n6. **🏆 Цель**: Достигните 21, 30, 100 или 365 дней!""",
        "lang_select": """🌐 **Выберите удобный язык:**""",
        "lang_updated": """✅ **Язык бота изменен на Русский!**""",
        "shop_main": """🛒 **МАГАЗИН THE 5 AM CLUB**\n\nВаши монеты: 🪙 `{coins} монет`\n\n1. 🛡 **Streak Freeze** — `100 монет`\n*(Сохраняет Стрик при пропуске 1 дня)*""",
        "shop_buy_freeze_ok": """🎉 **Успешно куплено!** У вас есть 1 🛡 **Streak Freeze**!""",
        "shop_no_coins": """❌ **Недостаточно монет!** У вас `{coins}` монет.""",
        "games_main": """🎮 **ИГРЫ И АРЕНА THE 5 AM CLUB**\n\n⚔️ **Дуэль 1v1** — Ставка 50 монет (-20 Stamina)\n🤝 **Парный Комбо** — Совместный подъем для бонуса\n🎲 **Случайный подбор** — Автоматический поиск партнера""",
        "matchmaking_searching": """🎲 **ПОИСК СЛУЧАЙНОГО ПАРТНЕРА...**""",
        "matchmaking_found": """🎉 **ПАРТНЕР НАЙДЕН!**\n\nВаш партнер: `{partner_name}`!\nПросыпайтесь вместе и получайте +50 монет! 🚀""",
        "duo_title": """🤝 **ПАРНЫЙ РЕЖИМ DUO COMBO**""",
        "duo_invite_prompt": """📌 Отправьте `/duo <id_партнера>`!\nПросыпайтесь вместе и получайте **+50 монет** ежедневно! 🚀""",
        "setup_group": """⚙️ **Выберите временное окно подъема для группы:**""",
        "setup_user": """⚙️ **Настройте персональное время подъема:**\nТекущее время: `{start}` — `{end}`""",
        "setup_updated": """✅ **Время подъема обновлено:** `{start}` — `{end}` 🌅""",
        "cert_congrats": """🏆 **ПОЗДРАВЛЯЕМ С ПОБЕДОЙ В МАРАФОНЕ!**\n\nВы просыпались 21 день подряд в 5:00 утра!\nВам вручен **21-Day Discipline Certificate** и знак **👑 Elite 21**!""",
        "bedtime_btn": """😴 Я Ложусь Спать (+20 XP)""",
        "bedtime_reminder": """🌙 **THE 5 AM CLUB: ПРОТОКОЛ СНА (21:30)**\n\n🛌 *«Чтобы владеть своим утром, защищайте свой сон!»* – Робин Шарма\n\n👇 *Нажмите кнопку перед сном для +20 XP и 100% энергии:*""",
        "bedtime_success": """😴 **СПОКОЙНОЙ НОЧИ, ЧЕМПИОН! (+20 XP)**\n\n⚡ Энергия восстанавливается на 100% for завтрашнего утра.""",
        "tournament_head": """⚔️ **5 AM ЕЖЕНЕДЕЛЬНЫЙ ТУРНИР (СЕЗОН #{season})** 🏆\n\n⏳ Финал: `{end_date}`\n💰 Призовой фонд: `1,000 Монет + 👑 Значки Чемпиона`\n\n""",
        "tournament_empty": """⚔️ В турнире пока нет участников.""",
        "spin_btn": """🎰 Крутить Колесо Удачи""",
        "spin_already": """⚠️ Вы уже вращали колесо удачи сегодня! До завтра! 🎰""",
        "spin_success": """🎰 **ВРАЩЕНИЕ КОЛЕСА УДАЧИ!**\n\n🎉 Вы выиграли: **{reward_label}**!\nПродолжайте путь к дисциплине! 🚀""",
        "squad_main": """🛡️ **5 AM КЛАН ДИСЦИПЛИНЫ (SQUAD)**\n\nВаш клан: **{name}** `[{tag}]` (ID: `{squad_id}`)\n👑 Лидер клана: `{leader_id}`\n👥 Участников: `{member_count}` чел\n🔥 Общий стрик клана: `{total_streak} дней`\n🌟 Всего XP: `{total_xp} XP`""",
        "squad_not_in": """🛡️ **Вы пока не состоите ни в одном клане.**\n\nСоздать клан: `/squad_create <название> <тег>`\nВступить в клан: `/squad_join <squad_id>`""",
        "squad_already": """⚠️ Вы уже состоите в клане! Сначала покиньте текущий клан.""",
        "squad_created": """🎉 **Клан успешно создан!**\n\n🛡️ Клан: **{name}** `[{tag}]` (ID: `{squad_id}`)\nПриглашайте соратников!""",
        "squad_joined": """🎉 **Вы успешно вступили в клан!**\n\n🛡️ Теперь вы участник клана **{name}** `[{tag}]` !""",
        "squad_not_found": """❌ Клан с таким ID не найден!""",
        "squad_leaderboard_title": """🛡️ **ТОП-10 КЛАНОВ ДИСЦИПЛИНЫ (5 AM CLANS)** 🛡️\n\n""",
        "badge_unlocked": """🎖️ **НОВЫЙ ЗНАЧОК РАЗБЛОКИРОВАН!**\n\nВы получили значок **{badge_name}**! ({badge_desc}) 🚀""",
        "grp_awake_title": """🌅 **СПИСОК ПРОСНУВШИХСЯ УЧАСТНИКОВ:**""",
        "grp_graveyard_title": """😴 **КЛАДБИЩЕ СОНИ:**""",
        "grp_register_btn": """✋ Зарегистрироваться в Группе""",
        "grp_registered_pm": """Вы успешно зарегистрировались в группе **{group}** for 5 AM Club :)""",
        "grp_to_group_btn": """Перейти в группу ↗"""
    },
    "en": {
        "welcome": """👋 **Welcome to The 5 AM Club, {name}!**\n\n“Own your morning. Elevate your life.”\n\n⚙️ Use the 4 main catalog hubs below:""",
        "hub_solo": """🌅 Solo Mode""",
        "hub_multiverse": """🎭 Multiverse Roleplay""",
        "hub_arena": """🎮 Interactive Arena""",
        "hub_settings": """⚙️ Settings & Help""",
        "hub_quote": """💡 Daily Wisdom""",
        "btn_admin": """👑 Owner Admin Panel""",
        "checkin_btn_inline": """⚡ CHECK-IN NOW (I'M AWAKE)""",
        "already_checked_in": """⚠️ You already checked in today! See you tomorrow! 🌅""",
        "not_in_window": """⚠️ It's not check-in time right now! Wake-up window: {start} - {end} 🌅""",
        "photo_too_dark": """❌ Image is too dark! Send a brighter photo! 📸""",
        "solo_menu_title": """⚡ **SOLO CHECK-IN & PERSONAL MODE**\n\nSelect an option to manage your morning discipline:""",
        "multiverse_menu_title": """🎭 **MULTIVERSE ROLEPLAY PARK**\n\nSelect your favorite universe realm. When Roleplay is enabled, all quips and titles match the active universe!""",
        "arena_menu_title": """🎮 **INTERACTIVE ARENA & DUELS**\n\nChallenge other players, pair up with a duo partner, and win weekly tournaments!""",
        "settings_menu_title": """⚙️ **SETTINGS & CONTROL PANEL**\n\nManage wake-up window, reminders, photo strictness, and language:""",
        "group_checkin_popup": """⚡ CHECK-IN SUCCESSFUL!\n🔥 Streak: {streak} days | 🪙 +{coins} Coins | 🌟 +{xp} XP""",
        "checkin_success": """⚡ **CHECK-IN SUCCESSFUL!**\n\n{quip}\n\n🔥 Streak: `{streak} days` (Multiplier: `{multiplier}X`)\n🎯 Target: `{streak}/{goal} days`\n🪙 Coins: `+{coins_earned}` (Total: `{coins}`)\n🌟 XP: `+{xp_earned}` (Total: `{xp}` XP | Level `{level}`)\n⚡ Stamina: `100/100 🟢`\n🏅 Rank: {rank}""",
        "photo_mission_prompt": """📸 **DAILY PHOTO MISSION:**\n\n{mission}\n\n📌 **Condition:** Send a photo! The bot will apply an official **VERIFIED STAMP**! 🚀""",
        "photo_success": """📸 **PHOTO CHECK-IN VERIFIED! (+{coins_earned} COINS, +{xp_earned} XP)**\n\n{quip}\n\n🔥 Streak: `{streak} days` (Multiplier: `{multiplier}X`)\n🎯 Target: `{streak}/{goal} days`\n🪙 Coins: `+{coins_earned}` (Total: `{coins}`)\n🌟 XP: `+{xp_earned}` (Total: `{xp}` XP | Level `{level}`)\n⚡ Stamina: `100/100 🟢`\n🏅 Rank: {rank}""",
        "profile_title": """👤 **MEMBER PROFILE & RPG STATS**\n\n🏷 Name: {name}\n🛡 Level: `{level}` — **{level_title}**\n🌟 XP: `{xp} / {next_level_xp} XP` ({progress_pct}%)\n⚡ Stamina: `{stamina}/100` {stamina_badge}\n🔥 Streak: `{streak} Days` | 🎯 Target: `{streak}/{goal} Days`\n🪙 Coins: `{coins}`\n⚔️ Tournament Points: `{tourney_pts} pts`\n👥 Invited Friends: `{ref_count}`\n🛡 Streak Freezes: `{freeze_count}`\n🎭 Multiverse: `{universe_name}` (RP: `{rp_status}`)\n🌐 Language: `{lang_str}`\n⏰ Window: `{start}` — `{end}`\n\n🏆 **TROPHY CABINET:**\n{badges}\n\n📈 **XP PROGRESSION:**\n{xp_bar}\n\n📈 **RANK PROGRESSION:**\n{progress_bar}""",
        "ref_text": """👥 **INVITE FRIENDS & EARN COINS**\n\nYour referral link:\n`{ref_link}`\n\n📌 Earn **+100 coins** for both you and your friend for every invite!\nTotal Invited: `{ref_count}` friends""",
        "leaderboard_title": """🏆 **THE 5 AM CLUB LEADERBOARD** 🏆\n\n""",
        "leaderboard_empty": """🏆 Leaderboard is currently empty.""",
        "quote_title": """💡 **DAILY MORNING WISDOM**\n\n{quote}""",
        "help_text": """📖 **THE 5 AM CLUB — RULES & GUIDELINES**\n\n1. **Morning Check-In**: Check in strictly within your window.\n2. **🎭 Multiverse Roleplay**: Choose 1 of 7 universe realms.\n3. **⚡ RPG XP & Leveling**: Gain XP on wakeups and level up!\n4. **🌙 21:30 Bedtime Protocol**: Protect your sleep for +20 XP.\n5. **⚔️ Weekly Tournament**: Compete for 1,000 coin prize pool!\n6. **🏆 Target Goal**: Master 21, 30, 100, or 365 days!""",
        "lang_select": """🌐 **Please select your language:**""",
        "lang_updated": """✅ **Bot language updated to English!**""",
        "shop_main": """🛒 **THE 5 AM CLUB MARKETPLACE**\n\nYour Balance: 🪙 `{coins} coins`\n\n1. 🛡 **Streak Freeze Shield** — `100 coins`\n*(Protects streak if you miss 1 day)*""",
        "shop_buy_freeze_ok": """🎉 **Purchase Successful!** You have 1 🛡 **Streak Freeze** shield!""",
        "shop_no_coins": """❌ **Insufficient coins!** You have `{coins}` coins.""",
        "games_main": """🎮 **THE 5 AM CLUB GAMES & ARENA**\n\n⚔️ **1v1 Wake-Up Duel** — Bet 50 coins (-20 Stamina)\n🤝 **Duo Combo** — Team up for daily bonus coins\n🎲 **Random Matchmaking** — Find a random player instantly""",
        "matchmaking_searching": """🎲 **SEARCHING FOR RANDOM PARTNER...**""",
        "matchmaking_found": """🎉 **PARTNER FOUND!**\n\nYour new Duo Partner: `{partner_name}`!\nWake up early together for +50 bonus coins! 🚀""",
        "duo_title": """🤝 **DUO COMBO PARTNER SYSTEM**""",
        "duo_invite_prompt": """📌 Send `/duo <partner_id>` command!\nWake up early together and earn **+50 bonus coins** every single day! 🚀""",
        "setup_group": """⚙️ **Select the check-in time window for the group:**""",
        "setup_user": """⚙️ **Customize your personal wake-up window:**\nCurrent window: `{start}` — `{end}`""",
        "setup_updated": """✅ **Morning check-in window updated:** `{start}` — `{end}` 🌅""",
        "cert_congrats": """🏆 **CONGRATULATIONS ON YOUR MARATHON VICTORY!**\n\nYou woke up at 5:00 AM for 21 consecutive days!\nAwarded official **21-Day Discipline Certificate** and **👑 Elite 21** badge!""",
        "bedtime_btn": """😴 I'm Going to Sleep (+20 XP)""",
        "bedtime_reminder": """🌙 **THE 5 AM CLUB: BEDTIME PROTOCOL (21:30)**\n\n🛌 *“To own your morning, protect your sleep!”* – Robin Sharma\n\n👇 *Tap below before sleeping to claim +20 XP and 100% Stamina boost:*""",
        "bedtime_success": """😴 **GOOD NIGHT, CHAMPION! (+20 XP)**\n\n⚡ Your stamina is recharging to 100% for tomorrow morning.""",
        "tournament_head": """⚔️ **5 AM WEEKLY TOURNAMENT (SEASON #{season})** 🏆\n\n⏳ Ends on: `{end_date}`\n💰 Prize Pool: `1,000 Coins + 👑 Champion Badges`\n\n""",
        "tournament_empty": """⚔️ No participants in current weekly tournament yet.""",
        "spin_btn": """🎰 Spin Daily Wheel of Fortune""",
        "spin_already": """⚠️ You have already spun the wheel of fortune today! See you tomorrow! 🎰""",
        "spin_success": """🎰 **WHEEL OF FORTUNE SPIN RESULT!**\n\n🎉 You won: **{reward_label}**!\nKeep elevating your discipline! 🚀""",
        "squad_main": """🛡️ **5 AM DISCIPLINE SQUAD (CLAN)**\n\nYour squad: **{name}** `[{tag}]` (ID: `{squad_id}`)\n👑 Leader: `{leader_id}`\n👥 Members: `{member_count}`\n🔥 Total Squad Streak: `{total_streak} days`\n🌟 Total Squad XP: `{total_xp} XP`""",
        "squad_not_in": """🛡️ **You are not currently in any squad.**\n\nCreate a squad: `/squad_create <name> <tag>`\nJoin a squad: `/squad_join <squad_id>`""",
        "squad_already": """⚠️ You are already in a squad! Leave your current squad first.""",
        "squad_created": """🎉 **Squad successfully created!**\n\n🛡️ Squad: **{name}** `[{tag}]` (ID: `{squad_id}`)\nNow invite your fellow warriors!""",
        "squad_joined": """🎉 **Successfully joined squad!**\n\n🛡️ You are now a member of **{name}** `[{tag}]` !""",
        "squad_not_found": """❌ No squad found with that ID!""",
        "squad_leaderboard_title": """🛡️ **TOP-10 DISCIPLINE SQUADS (5 AM CLANS)** 🛡️\n\n""",
        "badge_unlocked": """🎖️ **NEW BADGE UNLOCKED!**\n\nYou earned the **{badge_name}** badge! ({badge_desc}) 🚀""",
        "grp_awake_title": """🌅 **LIST OF AWAKE MEMBERS:**""",
        "grp_graveyard_title": """😴 **SLEEPYHEADS GRAVEYARD:**""",
        "grp_register_btn": """✋ Register in Group""",
        "grp_registered_pm": """You have successfully registered for The 5 AM Club in **{group}** :)""",
        "grp_to_group_btn": """Go to Group ↗"""
    }
}

# ==================== AUTHENTIC MOTIVATIONAL QUOTES ====================
MOTIVATIONAL_QUOTES = [
    {"id": 1, "body": {"uz": "Ertalabki vaqtingizga egalik qiling. Hayotingizni yuksaltiring.", "ru": "Владейте своим утром. Поднимите свою жизнь.", "en": "Own your morning. Elevate your life."}, "author": "Robin Sharma"},
    {"id": 2, "body": {"uz": "G'alabalar tong otmasdan, sukunat va intizomda yaratiladi.", "ru": "Победы куются до рассвета, в тишине железной дисциплины.", "en": "Victories are created before dawn, in the quiet solitude of discipline."}, "author": "Robin Sharma"},
    {"id": 3, "body": {"uz": "Daqiqalarga e'tibor bering, soatlar o'z-o'zidan tartibga tushadi.", "ru": "Позаботьтесь о минутах, и часы позаботятся о себе сами.", "en": "Take care of the minutes and the hours will take care of themselves."}, "author": "Lord Chesterfield"},
    {"id": 4, "body": {"uz": "Oldinga siljishning siri — boshlashdir.", "ru": "Секрет того, чтобы вырваться вперед — это начать.", "en": "The secret of getting ahead is getting started."}, "author": "Mark Twain"},
    {"id": 5, "body": {"uz": "Intizom — bu hozir xohlagan narsangiz bilan eng ko'p xohlagan narsangiz o'rtasidagi tanlovdir.", "ru": "Дисциплина — это выбор между тем, чего вы хотите сейчас, и тем, чего вы хотите больше всего.", "en": "Discipline is choosing between what you want now and what you want most."}, "author": "Abraham Lincoln"},
    {"id": 6, "body": {"uz": "Kichik kunlik o'sishlar vaqt o'tishi bilan aql bovar qilmas natijalarga olib keladi.", "ru": "Маленькие ежедневные улучшения со временем приводят к потрясающим результатам.", "en": "Small daily improvements over time lead to stunning results."}, "author": "Robin Sharma"},
    {"id": 7, "body": {"uz": "Biz har kuni takrorlaydigan narsamizning mahsulimiz. Muvaffaqiyat — bu harakat emas, odatdir.", "ru": "Мы то, что мы делаем постоянно. Совершенство — это не действие, а привычка.", "en": "We are what we repeatedly do. Excellence, then, is not an act, but a habit."}, "author": "Aristotle"},
    {"id": 8, "body": {"uz": "Intizom azobi pushaymonlik azobidan ming marotaba yengilroqdir.", "ru": "Боль дисциплины весит граммы, а боль сожаления — тонны.", "en": "Discipline weighs ounces, regret weighs tons."}, "author": "Jim Rohn"},
    {"id": 9, "body": {"uz": "G'oliblar oddiy odamlar qilmoqchi bo'lmagan narsalarni har kuni qiladilar.", "ru": "Победители делают то, что обычные люди делать не хотят.", "en": "Winners do what ordinary people are unwilling to do daily."}, "author": "Kobe Bryant"},
    {"id": 10, "body": {"uz": "Charchaganingizda emas, ishni tugatganingizda to'xtang!", "ru": "Останавливайтесь не тогда, когда устали, а когда закончили!", "en": "Don't stop when you're tired. Stop when you're done!"}, "author": "Dwayne Johnson"},
    {"id": 11, "body": {"uz": "Vaqtingiz chegaralangan, uni boshqa birovning hayotini yashashga sarflamang.", "ru": "Ваше время ограничено, не тратьте его, живя чужой жизнью.", "en": "Your time is limited, don't waste it living someone else's life."}, "author": "Steve Jobs"},
    {"id": 12, "body": {"uz": "Ertalab soat 5:00 da uyg'onish — bu butun dunyoga berilgan intizomiy chaqiriqdir.", "ru": "Подъем в 5:00 утра — это вызов всему миру и проявление силы воли.", "en": "Rising at 5 AM is a statement of intent to the entire world."}, "author": "Robin Sharma"},
    {"id": 13, "body": {"uz": "Intizom — bu maqsadlar va muvaffaqiyat o'rtasidagi ko'prikdir.", "ru": "Дисциплина — это мост между целями и достижениями.", "en": "Discipline is the bridge between goals and accomplishment."}, "author": "Jim Rohn"},
    {"id": 14, "body": {"uz": "Agarda siz o'z orzularingiz uchun kurashmasangiz, birov sizni o'z orzusi uchun yollaydi.", "ru": "Если вы не построите свою мечту, кто-то наймет вас для постройки своей.", "en": "If you don't build your dream, someone will hire you to build theirs."}, "author": "Robert Kiyosaki"},
    {"id": 15, "body": {"uz": "O'zingizga bo'lgan ishonch har kuni soat 5:00 da boshlanadi.", "ru": "Уверенность в себе начинается каждое утро в 5:00.", "en": "Self-confidence begins every single morning at 5 AM."}, "author": "Robin Sharma"},
    {"id": 16, "body": {"uz": "Kuch jismoniy imkoniyatdan emas, yengilmas irodadan kelib chiqadi.", "ru": "Сила происходит не от физических возможностей, а от несокрушимой воли.", "en": "Strength does not come from physical capacity. It comes from an indomitable will."}, "author": "Mahatma Gandhi"},
    {"id": 17, "body": {"uz": "Ertalabki sukunatda aqlingiz eng tiniq va kuchli holatda bo'ladi.", "ru": "В утренней тишине ваш разум находится в самой сильной концентрации.", "en": "In the morning silence, your mind reaches peak clarity."}, "author": "Robin Sharma"},
    {"id": 18, "body": {"uz": "Kelajak bugun nima qilayotganingizga bog'liq, ertaga emas.", "ru": "Будущее зависит от того, что вы делаете сегодня, а не завтра.", "en": "The future depends on what you do today."}, "author": "Mahatma Gandhi"},
    {"id": 19, "body": {"uz": "O'z ongini va vaqtini boshqargan inson butun dunyoni boshqaradi.", "ru": "Кто управляет своим разумом и временем, тот управляет миром.", "en": "He who controls his mind and time controls the world."}, "author": "Seneca"},
    {"id": 20, "body": {"uz": "Yo'lingizda g'ovlar bo'lmaydi, yo'lingizning o'zi g'ovlardan iboratdir.", "ru": "Препятствие на пути становится самим путем.", "en": "The obstacle is the way."}, "author": "Marcus Aurelius"},
    {"id": 21, "body": {"uz": "Ming chaqirimlik yo'l birinchi qadamdan boshlanadi.", "ru": "Путь в тысячу миль начинается с первого шага.", "en": "A journey of a thousand miles begins with a single step."}, "author": "Lao Tzu"},
    {"id": 22, "body": {"uz": "Qiyinchiliklar sizni sindirish uchun emas, charxlash uchun keladi.", "ru": "Трудности приходят не для того чтобы сломать вас, а чтобы закалить.", "en": "Difficulties come to sharpen you, not to break you."}, "author": "Epictetus"},
    {"id": 23, "body": {"uz": "Xatolardan qo'rqmang, harakat qilmaslikdan qo'rqing.", "ru": "Не бойтесь ошибок, бойтесь inaction.", "en": "Do not fear failure, fear lack of effort."}, "author": "Bruce Lee"},
    {"id": 24, "body": {"uz": "O'z ustida g'alaba qozonish — eng buyuk g'alabadir.", "ru": "Победа над собой — величайшая из побед.", "en": "To conquer oneself is the greatest victory."}, "author": "Plato"},
    {"id": 25, "body": {"uz": "Har kuni ozgina rivojlanish — yil oxirida ulkan zafardir.", "ru": "Маленький прогресс каждый день дает невероятный результат через год.", "en": "Daily progress compounds into extraordinary transformation."}, "author": "Robin Sharma"}
]

async def fetch_motivational_quote(user_id: int = 0, lang: str = "uz", active_universe: str = None) -> str:
    """
    Delivers a clean motivational quote formatted strictly with Telegram's native blockquote Markdown syntax (> quote).
    Guarantees zero duplicate quotes per user.
    """
    if user_id == 0:
        chosen = random.choice(MOTIVATIONAL_QUOTES)
    else:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT quote_id FROM user_quote_history WHERE user_id = ?", (user_id,))
            seen_ids = set(row[0] for row in cursor.fetchall())

            available = [q for q in MOTIVATIONAL_QUOTES if q["id"] not in seen_ids]

            if not available:
                cursor.execute("DELETE FROM user_quote_history WHERE user_id = ?", (user_id,))
                available = list(MOTIVATIONAL_QUOTES)

            chosen = random.choice(available)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT OR IGNORE INTO user_quote_history (user_id, quote_id, delivered_at) VALUES (?, ?, ?)",
                           (user_id, chosen["id"], now_str))

    q_body = chosen["body"].get(lang, chosen["body"]["uz"])
    q_author = chosen.get("author", "Robin Sharma")

    return f"> “{q_body}”\n> \n> — *{q_author}*"

# ==================== DYNAMIC QUIPS & ROLEPLAY TITLES ====================
async def fetch_dynamic_quip(streak: int, name: str, lang: str = "uz", roleplay_enabled: int = 0, active_universe: str = "marvel") -> str:
    target_realm = active_universe if (roleplay_enabled and active_universe in REALMS) else "standard"
    realm = REALMS.get(target_realm, REALMS["standard"])
    quips_list = realm["quips"].get(lang, realm["quips"]["uz"])
    return random.choice(quips_list)

# ==================== ASYNC PILLOW PHOTO STAMPING & CERTIFICATES ====================
def _sync_stamp_photo(image_bytes: bytes, name: str, streak: int, rank: str) -> bytes:
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        width, height = img.size

        banner_height = max(60, int(height * 0.12))
        banner = Image.new("RGBA", (width, banner_height), (15, 23, 42, 220))
        img.paste(banner, (0, height - banner_height), banner)

        draw = ImageDraw.Draw(img)
        tz = pytz.timezone(TIMEZONE_STR)
        time_str = datetime.now(tz).strftime("%Y-%m-%d %I:%M:%S %p")

        text1 = f"✅ VERIFIED 5 AM CLUB | {time_str}"
        text2 = f"👤 {name} | 🔥 Streak: {streak} Days | 🏅 {rank}"

        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        draw.text((20, height - banner_height + 10), text1, fill=(250, 204, 21), font=font)
        draw.text((20, height - banner_height + 32), text2, fill=(255, 255, 255), font=font)

        out_io = io.BytesIO()
        img.save(out_io, format="JPEG", quality=90)
        return out_io.getvalue()
    except Exception as e:
        logging.error(f"Error stamping photo: {e}")
        return image_bytes

async def stamp_photo_with_watermark(image_bytes: bytes, name: str, streak: int, rank: str) -> bytes:
    return await asyncio.to_thread(_sync_stamp_photo, image_bytes, name, streak, rank)

def _sync_generate_certificate(name: str) -> bytes:
    try:
        img = Image.new("RGB", (1000, 600), (15, 23, 42))
        draw = ImageDraw.Draw(img)

        draw.rectangle([20, 20, 980, 580], outline=(250, 204, 21), width=6)
        draw.rectangle([30, 30, 970, 570], outline=(255, 255, 255), width=2)

        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        tz = pytz.timezone(TIMEZONE_STR)
        today_str = datetime.now(tz).strftime("%Y-%m-%d")

        draw.text((220, 80), "🏆 THE 5 AM CLUB DISCIPLINE CERTIFICATE 🏆", fill=(250, 204, 21), font=font)
        draw.text((380, 160), "PROUDLY PRESENTED TO", fill=(255, 255, 255), font=font)
        draw.text((350, 220), f"★ {name.upper()} ★", fill=(250, 204, 21), font=font)
        draw.text((180, 310), "For completing 21 Consecutive Days of 5 AM Morning Discipline!", fill=(255, 255, 255), font=font)
        draw.text((320, 370), "“Own Your Morning. Elevate Your Life.”", fill=(148, 163, 184), font=font)
        draw.text((350, 480), f"Issued on: {today_str} | Verified Official", fill=(250, 204, 21), font=font)

        out_io = io.BytesIO()
        img.save(out_io, format="JPEG", quality=95)
        return out_io.getvalue()
    except Exception as e:
        logging.error(f"Error generating certificate: {e}")
        return b""

async def generate_21day_certificate(name: str) -> bytes:
    return await asyncio.to_thread(_sync_generate_certificate, name)

# ==================== RPG XP, LEVELING & STAMINA SYSTEM ====================
RPG_LEVEL_TITLES = {
    "uz": [
        (1, "🌅 Tonggi Shogird"),
        (5, "⚡ Quyosh Quluvchisi"),
        (10, "⚔️ Temir Intizom Ritsari"),
        (20, "👑 Tonggi Master"),
        (35, "🌌 Koinot Buyuk Ustasi")
    ],
    "ru": [
        (1, "🌅 Новичок Рассвета"),
        (5, "⚡ Искатель Солнца"),
        (10, "⚔️ Рыцарь Дисциплины"),
        (20, "👑 Мастер Рассвета"),
        (35, "🌌 Грандмастер 5 AM")
    ],
    "en": [
        (1, "🌅 Dawn Initiate"),
        (5, "⚡ Sun Chaser"),
        (10, "⚔️ Iron Discipline Knight"),
        (20, "👑 Dawn Master"),
        (35, "🌌 Grandmaster of 5 AM Dawn")
    ]
}

def calculate_rpg_level(xp: int, lang: str = "uz") -> dict:
    level = 1
    while True:
        next_req = int(50 * level * (level + 1))
        if xp < next_req:
            break
        level += 1

    curr_floor = int(50 * (level - 1) * level)
    next_ceil = int(50 * level * (level + 1))
    xp_in_level = max(0, xp - curr_floor)
    xp_needed_level = max(1, next_ceil - curr_floor)
    progress_pct = round((xp_in_level / xp_needed_level) * 100, 1)

    titles = RPG_LEVEL_TITLES.get(lang, RPG_LEVEL_TITLES["uz"])
    title = titles[0][1]
    for min_lvl, t_name in titles:
        if level >= min_lvl:
            title = t_name

    return {
        "level": level,
        "total_xp": xp,
        "xp_in_level": xp_in_level,
        "xp_needed_level": xp_needed_level,
        "next_level_total_xp": next_ceil,
        "progress_pct": progress_pct,
        "title": title
    }

def get_streak_multiplier(streak: int) -> float:
    if streak >= 30: return 2.0
    elif streak >= 15: return 1.5
    elif streak >= 7: return 1.2
    else: return 1.0


# ==================== 12 BADGES VAULT SYSTEM ====================
BADGES_VAULT = {
    "streak_7": {
        "icon": "⚡",
        "key": "streak_7",
        "name": {"uz": "⚡ Early Bird", "ru": "⚡ Ранняя Пташка", "en": "⚡ Early Bird"},
        "desc": {"uz": "7 kunlik uzluksiz streak", "ru": "7 дней подряд check-in", "en": "7-day check-in streak"}
    },
    "streak_21": {
        "icon": "👑",
        "key": "streak_21",
        "name": {"uz": "👑 Elite 21", "ru": "👑 Элита 21", "en": "👑 Elite 21"},
        "desc": {"uz": "21 kunlik intizom maratoni", "ru": "21 день утреннего марафона", "en": "21-day discipline streak"}
    },
    "streak_66": {
        "icon": "🛡️",
        "key": "streak_66",
        "name": {"uz": "🛡️ Odat Ustasi", "ru": "🛡️ Мастер Привычки", "en": "🛡️ Habit Master"},
        "desc": {"uz": "66 kunlik shakllangan odat", "ru": "66 дней сформированной привычки", "en": "66-day habit lock"}
    },
    "streak_100": {
        "icon": "💎",
        "key": "streak_100",
        "name": {"uz": "💎 Asr Afsonasi", "ru": "💎 Легенда Века", "en": "💎 Century Legend"},
        "desc": {"uz": "100 kunlik buyuk afsonaviy streak", "ru": "100 дней легендарного стрика", "en": "100-day legendary streak"}
    },
    "coins_500": {
        "icon": "💰",
        "key": "coins_500",
        "name": {"uz": "💰 Tanga Yig'uvchi", "ru": "💰 Собиратель Монет", "en": "💰 Coin Collector"},
        "desc": {"uz": "500 coin jamg'arish", "ru": "Накопить 500 монет", "en": "Accumulate 500 coins"}
    },
    "coins_2000": {
        "icon": "🏦",
        "key": "coins_2000",
        "name": {"uz": "🏦 Xazina Ustasi", "ru": "🏦 Мастер Сокровищница", "en": "🏦 Vault Master"},
        "desc": {"uz": "2000 coin jamg'arish", "ru": "Накопить 2000 монет", "en": "Accumulate 2000 coins"}
    },
    "duels_1": {
        "icon": "⚔️",
        "key": "duels_1",
        "name": {"uz": "⚔️ Birinchi Qon", "ru": "⚔️ Первая Кровь", "en": "⚔️ First Blood"},
        "desc": {"uz": "1-duelda g'alaba qozonish", "ru": "Победа в 1 дуэли", "en": "Win 1 duel"}
    },
    "duels_5": {
        "icon": "🗡️",
        "key": "duels_5",
        "name": {"uz": "🗡️ Arena Gladiator", "ru": "🗡️ Гладиатор Арены", "en": "🗡️ Arena Gladiator"},
        "desc": {"uz": "5 ta duel g'alabasi", "ru": "5 побед на арене", "en": "Win 5 duels"}
    },
    "bedtime_7": {
        "icon": "🌙",
        "key": "bedtime_7",
        "name": {"uz": "🌙 Uyqu Himoyachisi", "ru": "🌙 Хранитель Сна", "en": "🌙 Sleep Guardian"},
        "desc": {"uz": "7 marta 21:30 uyqu protokoli", "ru": "7 раз протокол сна 21:30", "en": "7 bedtime protocol check-ins"}
    },
    "bedtime_21": {
        "icon": "🛌",
        "key": "bedtime_21",
        "name": {"uz": "🛌 Tinch Titan", "ru": "🛌 Отдохнувший Титан", "en": "🛌 Rested Titan"},
        "desc": {"uz": "21 marta 21:30 uyqu protokoli", "ru": "21 раз протокол сна", "en": "21 bedtime protocol check-ins"}
    },
    "ref_3": {
        "icon": "👥",
        "key": "ref_3",
        "name": {"uz": "👥 Jamiyat Yetakchisi", "ru": "👥 Лидер Сообщества", "en": "👥 Community Leader"},
        "desc": {"uz": "3 ta do'stni taklif qilish", "ru": "Пригласить 3 друзей", "en": "Invite 3 friends"}
    },
    "ref_10": {
        "icon": "🌐",
        "key": "ref_10",
        "name": {"uz": "🌐 Imperiya Bunyodkori", "ru": "🌐 Строитель Империи", "en": "🌐 Empire Builder"},
        "desc": {"uz": "10 ta do'stni taklif qilish", "ru": "Пригласить 10 друзей", "en": "Invite 10 friends"}
    }
}

def db_check_and_unlock_badges(user_id: int) -> list:
    newly_unlocked = []
    user = db_get_user(user_id)
    if not user:
        return newly_unlocked

    u_dict = dict(user)
    streak = u_dict.get("streak") or 0
    coins = u_dict.get("coins") or 0
    duels_won = u_dict.get("duels_won") or 0
    bedtime_count = u_dict.get("bedtime_count") or 0
    ref_count = u_dict.get("referral_count") or 0

    eligible = []
    if streak >= 7: eligible.append("streak_7")
    if streak >= 21: eligible.append("streak_21")
    if streak >= 66: eligible.append("streak_66")
    if streak >= 100: eligible.append("streak_100")

    if coins >= 500: eligible.append("coins_500")
    if coins >= 2000: eligible.append("coins_2000")

    if duels_won >= 1: eligible.append("duels_1")
    if duels_won >= 5: eligible.append("duels_5")

    if bedtime_count >= 7: eligible.append("bedtime_7")
    if bedtime_count >= 21: eligible.append("bedtime_21")

    if ref_count >= 3: eligible.append("ref_3")
    if ref_count >= 10: eligible.append("ref_10")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT badge_key FROM user_badges WHERE user_id = ?", (user_id,))
        existing_keys = set(row[0] for row in cursor.fetchall())

        for b_key in eligible:
            if b_key not in existing_keys and b_key in BADGES_VAULT:
                cursor.execute("INSERT OR IGNORE INTO user_badges (user_id, badge_key, unlocked_at) VALUES (?, ?, ?)",
                               (user_id, b_key, now_str))
                newly_unlocked.append(BADGES_VAULT[b_key])

    return newly_unlocked

def db_get_user_badges(user_id: int, lang: str = "uz") -> list:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT badge_key FROM user_badges WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            b_key = r["badge_key"]
            if b_key in BADGES_VAULT:
                b_data = BADGES_VAULT[b_key]
                result.append(f"{b_data['icon']} {b_data['name'].get(lang, b_data['name']['uz'])}")
        return result

# ==================== SAFE DATABASE CONNECTION MANAGER ====================
@contextmanager
def get_db(row_factory: bool = True):
    conn = sqlite3.connect(DB_NAME, timeout=20.0, check_same_thread=False)
    if row_factory:
        conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f"Database transaction error: {e}")
        raise
    finally:
        conn.close()

# ==================== DATABASE INITIALIZATION & MIGRATIONS ====================
def init_sqlite_db():
    with get_db(row_factory=False) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                streak INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                stamina INTEGER DEFAULT 100,
                max_stamina INTEGER DEFAULT 100,
                last_stamina_update TEXT,
                last_bedtime_date TEXT,
                freeze_count INTEGER DEFAULT 0,
                photo_count INTEGER DEFAULT 0,
                duo_partner_id INTEGER DEFAULT 0,
                in_matchmaking INTEGER DEFAULT 0,
                referred_by INTEGER DEFAULT 0,
                referral_count INTEGER DEFAULT 0,
                cert_issued INTEGER DEFAULT 0,
                checkin_start TEXT DEFAULT '04:30',
                checkin_end TEXT DEFAULT '06:00',
                lang TEXT DEFAULT 'uz',
                last_checkin_date TEXT,
                status TEXT DEFAULT 'snoozed',
                target_goal INTEGER DEFAULT 21,
                roleplay_enabled INTEGER DEFAULT 0,
                active_universe TEXT DEFAULT 'marvel',
                interactive_enabled INTEGER DEFAULT 1,
                pm_reminder_enabled INTEGER DEFAULT 1,
                photo_strictness TEXT DEFAULT 'medium',
                created_at TEXT
            )
        """)

        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        if "lang" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN lang TEXT DEFAULT 'uz'")
        if "last_spin_date" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN last_spin_date TEXT")
        if "duels_won" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN duels_won INTEGER DEFAULT 0")
        if "bedtime_count" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN bedtime_count INTEGER DEFAULT 0")
        if "photo_count" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN photo_count INTEGER DEFAULT 0")
        if "freeze_count" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN freeze_count INTEGER DEFAULT 0")
        if "duo_partner_id" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN duo_partner_id INTEGER DEFAULT 0")
        if "in_matchmaking" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN in_matchmaking INTEGER DEFAULT 0")
        if "referred_by" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER DEFAULT 0")
        if "referral_count" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN referral_count INTEGER DEFAULT 0")
        if "cert_issued" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN cert_issued INTEGER DEFAULT 0")
        if "checkin_start" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN checkin_start TEXT DEFAULT '04:30'")
        if "checkin_end" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN checkin_end TEXT DEFAULT '06:00'")
        if "xp" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN xp INTEGER DEFAULT 0")
        if "level" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN level INTEGER DEFAULT 1")
        if "stamina" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN stamina INTEGER DEFAULT 100")
        if "max_stamina" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN max_stamina INTEGER DEFAULT 100")
        if "last_stamina_update" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN last_stamina_update TEXT")
        if "last_bedtime_date" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN last_bedtime_date TEXT")
        if "target_goal" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN target_goal INTEGER DEFAULT 21")
        if "roleplay_enabled" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN roleplay_enabled INTEGER DEFAULT 0")
        if "active_universe" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN active_universe TEXT DEFAULT 'marvel'")
        if "interactive_enabled" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN interactive_enabled INTEGER DEFAULT 1")
        if "pm_reminder_enabled" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN pm_reminder_enabled INTEGER DEFAULT 1")
        if "photo_strictness" not in columns: cursor.execute("ALTER TABLE users ADD COLUMN photo_strictness TEXT DEFAULT 'medium'")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                title TEXT,
                checkin_start TEXT DEFAULT '04:30',
                checkin_end TEXT DEFAULT '06:00',
                normal_coins INTEGER DEFAULT 10,
                photo_coins INTEGER DEFAULT 25,
                timezone TEXT DEFAULT 'Asia/Tashkent',
                is_active INTEGER DEFAULT 1,
                target_goal INTEGER DEFAULT 21,
                roleplay_enabled INTEGER DEFAULT 0,
                active_universe TEXT DEFAULT 'marvel',
                interactive_enabled INTEGER DEFAULT 1,
                pm_reminder_enabled INTEGER DEFAULT 1,
                photo_strictness TEXT DEFAULT 'medium',
                opt_in_mode TEXT DEFAULT 'auto',
                lang TEXT DEFAULT 'uz'
            )
        """)

        cursor.execute("PRAGMA table_info(groups)")
        g_columns = [col[1] for col in cursor.fetchall()]
        if "target_goal" not in g_columns: cursor.execute("ALTER TABLE groups ADD COLUMN target_goal INTEGER DEFAULT 21")
        if "roleplay_enabled" not in g_columns: cursor.execute("ALTER TABLE groups ADD COLUMN roleplay_enabled INTEGER DEFAULT 0")
        if "active_universe" not in g_columns: cursor.execute("ALTER TABLE groups ADD COLUMN active_universe TEXT DEFAULT 'marvel'")
        if "interactive_enabled" not in g_columns: cursor.execute("ALTER TABLE groups ADD COLUMN interactive_enabled INTEGER DEFAULT 1")
        if "pm_reminder_enabled" not in g_columns: cursor.execute("ALTER TABLE groups ADD COLUMN pm_reminder_enabled INTEGER DEFAULT 1")
        if "photo_strictness" not in g_columns: cursor.execute("ALTER TABLE groups ADD COLUMN photo_strictness TEXT DEFAULT 'medium'")
        if "opt_in_mode" not in g_columns: cursor.execute("ALTER TABLE groups ADD COLUMN opt_in_mode TEXT DEFAULT 'auto'")
        if "lang" not in g_columns: cursor.execute("ALTER TABLE groups ADD COLUMN lang TEXT DEFAULT 'uz'")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_quote_history (
                user_id INTEGER,
                quote_id INTEGER,
                delivered_at TEXT,
                PRIMARY KEY (user_id, quote_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_members (
                group_id INTEGER,
                user_id INTEGER,
                status TEXT DEFAULT 'snoozed',
                last_checkin_time TEXT,
                streak INTEGER DEFAULT 0,
                PRIMARY KEY (group_id, user_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS squads (
                squad_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                tag TEXT,
                leader_id INTEGER,
                created_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS squad_members (
                squad_id INTEGER,
                user_id INTEGER PRIMARY KEY,
                joined_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_badges (
                user_id INTEGER,
                badge_key TEXT,
                unlocked_at TEXT,
                PRIMARY KEY (user_id, badge_key)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                group_id INTEGER,
                checkin_timestamp TEXT,
                checkin_date TEXT,
                coins_earned INTEGER
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tournament_seasons (
                season_id INTEGER PRIMARY KEY AUTOINCREMENT,
                season_number INTEGER,
                start_date TEXT,
                end_date TEXT,
                is_active INTEGER DEFAULT 1,
                winner_id INTEGER DEFAULT 0,
                winner_name TEXT DEFAULT '',
                winner_points INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tournament_participants (
                season_id INTEGER,
                user_id INTEGER,
                first_name TEXT,
                username TEXT,
                points INTEGER DEFAULT 0,
                checkins_count INTEGER DEFAULT 0,
                photos_count INTEGER DEFAULT 0,
                rank_tier TEXT DEFAULT 'Bronze',
                PRIMARY KEY (season_id, user_id)
            )
        """)

# ==================== DB HELPER OPERATIONS ====================
def db_register_user(user_id: int, username: str, first_name: str, ref_by: int = 0):
    with get_db() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        existing = cursor.fetchone()

        if not existing:
            initial_coins = 100 if ref_by and ref_by != user_id else 0
            cursor.execute("""
                INSERT INTO users (user_id, username, first_name, coins, xp, level, stamina, max_stamina, last_stamina_update, referred_by, created_at, target_goal, roleplay_enabled, active_universe, interactive_enabled, pm_reminder_enabled, photo_strictness)
                VALUES (?, ?, ?, ?, 0, 1, 100, 100, ?, ?, ?, 21, 0, 'marvel', 1, 1, 'medium')
            """, (user_id, username or "", first_name or "Member", initial_coins, now_str, ref_by, now_str))

            if ref_by and ref_by != user_id:
                cursor.execute("UPDATE users SET coins = coins + 100, referral_count = referral_count + 1 WHERE user_id = ?", (ref_by,))
        else:
            cursor.execute("""
                UPDATE users SET username = ?, first_name = ? WHERE user_id = ?
            """, (username or "", first_name or "Member", user_id))

def db_register_group(group_id: int, title: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO groups (group_id, title)
            VALUES (?, ?)
            ON CONFLICT(group_id) DO UPDATE SET title = excluded.title
        """, (group_id, title or "5 AM Club Group"))

def db_link_group_member(group_id: int, user_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO group_members (group_id, user_id)
            VALUES (?, ?)
            ON CONFLICT(group_id, user_id) DO NOTHING
        """, (group_id, user_id))

def db_get_user(user_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()

def db_get_group(group_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM groups WHERE group_id = ?", (group_id,))
        return cursor.fetchone()

def db_get_all_users():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        return cursor.fetchall()

def db_get_active_groups():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM groups WHERE is_active = 1")
        return cursor.fetchall()

def db_update_user_setting(user_id: int, field: str, value):
    valid_fields = ["target_goal", "roleplay_enabled", "active_universe", "interactive_enabled", "pm_reminder_enabled", "photo_strictness", "lang", "checkin_start", "checkin_end"]
    if field not in valid_fields:
        return
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))

def db_update_group_setting(group_id: int, field: str, value):
    valid_fields = ["target_goal", "roleplay_enabled", "active_universe", "interactive_enabled", "pm_reminder_enabled", "photo_strictness", "opt_in_mode", "checkin_start", "checkin_end"]
    if field not in valid_fields:
        return
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE groups SET {field} = ? WHERE group_id = ?", (value, group_id))

def db_update_user_lang(user_id: int, lang: str):
    db_update_user_setting(user_id, "lang", lang)

def db_update_user_times(user_id: int, start_time: str, end_time: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET checkin_start = ?, checkin_end = ? WHERE user_id = ?", (start_time, end_time, user_id))

def db_update_group_times(group_id: int, start_time: str, end_time: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE groups SET checkin_start = ?, checkin_end = ? WHERE group_id = ?", (start_time, end_time, group_id))

def db_update_group_coins(group_id: int, normal_coins: int, photo_coins: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE groups SET normal_coins = ?, photo_coins = ? WHERE group_id = ?", (normal_coins, photo_coins, group_id))

def db_update_user_coins(user_id: int, coins_to_add: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (coins_to_add, user_id))

def db_update_user_streak(user_id: int, new_streak: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET streak = ? WHERE user_id = ?", (new_streak, user_id))

def db_buy_streak_freeze(user_id: int) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT coins, freeze_count FROM users WHERE user_id = ?", (user_id,))
        u = cursor.fetchone()
        if not u or u["coins"] < 100:
            return False
        cursor.execute("UPDATE users SET coins = coins - 100, freeze_count = freeze_count + 1 WHERE user_id = ?", (user_id,))
        return True

def db_set_duo_partner(user_id: int, partner_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET duo_partner_id = ?, in_matchmaking = 0 WHERE user_id = ?", (partner_id, user_id))
        cursor.execute("UPDATE users SET duo_partner_id = ?, in_matchmaking = 0 WHERE user_id = ?", (user_id, partner_id))

def db_matchmaking_find_or_enqueue(user_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, first_name FROM users WHERE in_matchmaking = 1 AND user_id != ?", (user_id,))
        waiting_user = cursor.fetchone()

        if waiting_user:
            partner_id = waiting_user["user_id"]
            partner_name = waiting_user["first_name"]

            cursor.execute("UPDATE users SET duo_partner_id = ?, in_matchmaking = 0 WHERE user_id = ?", (partner_id, user_id))
            cursor.execute("UPDATE users SET duo_partner_id = ?, in_matchmaking = 0 WHERE user_id = ?", (user_id, partner_id))
            return partner_id, partner_name
        else:
            cursor.execute("UPDATE users SET in_matchmaking = 1 WHERE user_id = ?", (user_id,))
            return None, None

def db_set_cert_issued(user_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET cert_issued = 1 WHERE user_id = ?", (user_id,))


# ==================== DAILY SPIN & SQUADS DB OPERATIONS ====================
def db_process_spin(user_id: int) -> dict:
    tz = pytz.timezone(TIMEZONE_STR)
    today_str = datetime.now(tz).strftime("%Y-%m-%d")

    user = db_get_user(user_id)
    if not user:
        return {"status": "error", "message": "User not found"}

    if user["last_spin_date"] == today_str:
        return {"status": "already", "message": "Already spun today"}

    rewards = [
        {"type": "coins", "val": 10, "label": "🪙 +10 Coins", "weight": 25},
        {"type": "coins", "val": 25, "label": "🪙 +25 Coins", "weight": 20},
        {"type": "coins", "val": 50, "label": "🪙 +50 Coins", "weight": 15},
        {"type": "coins", "val": 100, "label": "🪙 +100 Coins", "weight": 5},
        {"type": "xp", "val": 20, "label": "🌟 +20 XP", "weight": 15},
        {"type": "xp", "val": 50, "label": "🌟 +50 XP", "weight": 10},
        {"type": "xp", "val": 100, "label": "🌟 +100 XP", "weight": 5},
        {"type": "freeze", "val": 1, "label": "🛡️ +1 Streak Freeze Shield", "weight": 5},
    ]

    weights = [r["weight"] for r in rewards]
    chosen = random.choices(rewards, weights=weights, k=1)[0]

    with get_db() as conn:
        cursor = conn.cursor()
        coins_add = chosen["val"] if chosen["type"] == "coins" else 0
        xp_add = chosen["val"] if chosen["type"] == "xp" else 0
        freeze_add = chosen["val"] if chosen["type"] == "freeze" else 0

        new_coins = user["coins"] + coins_add
        new_xp = (user["xp"] or 0) + xp_add
        new_freeze = (user["freeze_count"] or 0) + freeze_add
        rpg_data = calculate_rpg_level(new_xp, user["lang"] or "uz")
        new_level = rpg_data["level"]

        cursor.execute("""
            UPDATE users
            SET last_spin_date = ?, coins = ?, xp = ?, level = ?, freeze_count = ?
            WHERE user_id = ?
        """, (today_str, new_coins, new_xp, new_level, new_freeze, user_id))

    if xp_add > 0:
        db_add_tournament_points(user_id, user["first_name"], user["username"], xp_add // 2)

    db_check_and_unlock_badges(user_id)

    return {
        "status": "ok",
        "reward": chosen,
        "coins": new_coins,
        "xp": new_xp,
        "level": new_level,
        "freeze_count": new_freeze
    }

def db_create_squad(leader_id: int, name: str, tag: str) -> tuple:
    name = name.strip()
    tag = tag.strip().upper()
    if not name or not tag:
        return False, "invalid_input", 0

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT squad_id FROM squad_members WHERE user_id = ?", (leader_id,))
        if cursor.fetchone():
            return False, "already_in_squad", 0

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cursor.execute("""
                INSERT INTO squads (name, tag, leader_id, created_at)
                VALUES (?, ?, ?, ?)
            """, (name, tag, leader_id, now_str))
            squad_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO squad_members (squad_id, user_id, joined_at)
                VALUES (?, ?, ?)
            """, (squad_id, leader_id, now_str))
            return True, "created", squad_id
        except sqlite3.IntegrityError:
            return False, "name_taken", 0

def db_join_squad(user_id: int, squad_id: int) -> tuple:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT squad_id FROM squads WHERE squad_id = ?", (squad_id,))
        if not cursor.fetchone():
            return False, "not_found"

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO squad_members (squad_id, user_id, joined_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                squad_id = excluded.squad_id,
                joined_at = excluded.joined_at
        """, (squad_id, user_id, now_str))
        return True, "joined"

def db_get_user_squad(user_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.squad_id, s.name, s.tag, s.leader_id, s.created_at
            FROM squad_members sm
            JOIN squads s ON sm.squad_id = s.squad_id
            WHERE sm.user_id = ?
        """, (user_id,))
        return cursor.fetchone()

def db_get_squad_info(squad_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM squads WHERE squad_id = ?", (squad_id,))
        squad = cursor.fetchone()
        if not squad:
            return None

        cursor.execute("""
            SELECT u.user_id, u.first_name, u.username, u.streak, u.coins, u.xp
            FROM squad_members sm
            JOIN users u ON sm.user_id = u.user_id
            WHERE sm.squad_id = ?
            ORDER BY u.streak DESC
        """, (squad_id,))
        members = cursor.fetchall()
        total_streak = sum(m["streak"] for m in members) if members else 0
        total_xp = sum((m["xp"] or 0) for m in members) if members else 0

        return {
            "squad": squad,
            "members": members,
            "member_count": len(members),
            "total_streak": total_streak,
            "total_xp": total_xp
        }

def db_get_squad_leaderboard(limit: int = 10):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.squad_id, s.name, s.tag, s.leader_id,
                   COUNT(sm.user_id) as member_count,
                   COALESCE(SUM(u.streak), 0) as total_streak,
                   COALESCE(SUM(u.xp), 0) as total_xp
            FROM squads s
            LEFT JOIN squad_members sm ON s.squad_id = sm.squad_id
            LEFT JOIN users u ON sm.user_id = u.user_id
            GROUP BY s.squad_id
            ORDER BY total_streak DESC, total_xp DESC
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()

# ==================== TOURNAMENT ENGINE ====================
def db_get_or_create_active_season():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tournament_seasons WHERE is_active = 1 ORDER BY season_id DESC LIMIT 1")
        season = cursor.fetchone()
        if season:
            return dict(season)

        tz = pytz.timezone(TIMEZONE_STR)
        now = datetime.now(tz)
        start_of_week = now - timedelta(days=now.weekday())
        start_str = start_of_week.strftime("%Y-%m-%d 00:00:00")
        end_of_week = start_of_week + timedelta(days=6)
        end_str = end_of_week.strftime("%Y-%m-%d 23:59:59")

        cursor.execute("SELECT COUNT(*) as cnt FROM tournament_seasons")
        cnt_row = cursor.fetchone()
        season_num = (cnt_row["cnt"] if cnt_row else 0) + 1

        cursor.execute("""
            INSERT INTO tournament_seasons (season_number, start_date, end_date, is_active)
            VALUES (?, ?, ?, 1)
        """, (season_num, start_str, end_str))
        season_id = cursor.lastrowid
        return {
            "season_id": season_id,
            "season_number": season_num,
            "start_date": start_str,
            "end_date": end_str,
            "is_active": 1
        }

def db_add_tournament_points(user_id: int, first_name: str, username: str, points: int, is_photo: bool = False):
    season = db_get_or_create_active_season()
    season_id = season["season_id"]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tournament_participants (season_id, user_id, first_name, username, points, checkins_count, photos_count)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            ON CONFLICT(season_id, user_id) DO UPDATE SET
                points = points + excluded.points,
                checkins_count = checkins_count + 1,
                photos_count = photos_count + excluded.photos_count,
                first_name = excluded.first_name,
                username = excluded.username
        """, (season_id, user_id, first_name, username or "", points, 1 if is_photo else 0))

def db_get_tournament_leaderboard(limit: int = 10):
    season = db_get_or_create_active_season()
    season_id = season["season_id"]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, first_name, username, points, checkins_count, photos_count
            FROM tournament_participants
            WHERE season_id = ?
            ORDER BY points DESC, checkins_count DESC
            LIMIT ?
        """, (season_id, limit))
        return cursor.fetchall(), season

def db_get_user_tournament_points(user_id: int) -> int:
    season = db_get_or_create_active_season()
    season_id = season["season_id"]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT points FROM tournament_participants WHERE season_id = ? AND user_id = ?
        """, (season_id, user_id))
        row = cursor.fetchone()
        return row["points"] if row else 0

# ==================== BEDTIME & STAMINA OPERATIONS ====================
def db_calculate_and_update_stamina(user: dict) -> int:
    current_stamina = user["stamina"] if "stamina" in user.keys() and user["stamina"] is not None else 100
    last_update_str = user["last_stamina_update"] if "last_stamina_update" in user.keys() and user["last_stamina_update"] else None
    
    if not last_update_str:
        return current_stamina

    try:
        last_dt = datetime.strptime(last_update_str, "%Y-%m-%d %H:%M:%S")
        hours_passed = (datetime.now() - last_dt).total_seconds() / 3600.0
        regen = int(hours_passed * 5)
        new_stamina = min(100, current_stamina + regen)
        if new_stamina != current_stamina:
            with get_db() as conn:
                conn.cursor().execute("UPDATE users SET stamina = ?, last_stamina_update = ? WHERE user_id = ?",
                                      (new_stamina, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user["user_id"]))
        return new_stamina
    except Exception:
        return current_stamina

def db_record_bedtime(user_id: int) -> tuple[bool, str]:
    tz = pytz.timezone(TIMEZONE_STR)
    now = datetime.now(tz)
    today_str = now.strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    user = db_get_user(user_id)
    if not user:
        return False, "not_found"

    if user["last_bedtime_date"] == today_str:
        return False, "already_recorded"

    with get_db() as conn:
        cursor = conn.cursor()
        new_xp = (user["xp"] or 0) + 20
        rpg_data = calculate_rpg_level(new_xp, user["lang"] or "uz")
        new_level = rpg_data["level"]

        cursor.execute("""
            UPDATE users
            SET xp = ?, level = ?, stamina = 100, last_stamina_update = ?, last_bedtime_date = ?, bedtime_count = bedtime_count + 1
            WHERE user_id = ?
        """, (new_xp, new_level, now_str, today_str, user_id))

    db_add_tournament_points(user_id, user["first_name"], user["username"], 25, is_photo=False)
    db_check_and_unlock_badges(user_id)
    return True, "ok"

# ==================== MAIN CHECKIN PIPELINE ====================
def db_process_checkin(user_id: int, group_id: int = 0, is_photo: bool = False):
    with get_db() as conn:
        cursor = conn.cursor()

        tz = pytz.timezone(TIMEZONE_STR)
        now = datetime.now(tz)
        today_str = now.strftime("%Y-%m-%d")
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        time_str = now.strftime("%H:%M:%S")

        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return None

        last_date = user["last_checkin_date"]
        current_streak = user["streak"]

        if last_date == today_str:
            return "already"

        yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        if last_date == yesterday_str:
            new_streak = current_streak + 1
        else:
            if user["freeze_count"] > 0:
                new_streak = current_streak + 1
                cursor.execute("UPDATE users SET freeze_count = freeze_count - 1 WHERE user_id = ?", (user_id,))
            else:
                new_streak = 1

        normal_reward, photo_reward = 10, 25
        if group_id != 0:
            cursor.execute("SELECT normal_coins, photo_coins FROM groups WHERE group_id = ?", (group_id,))
            g_row = cursor.fetchone()
            if g_row:
                normal_reward = g_row["normal_coins"] if g_row["normal_coins"] else 10
                photo_reward = g_row["photo_coins"] if g_row["photo_coins"] else 25

        base_coins = photo_reward if is_photo else normal_reward
        multiplier = get_streak_multiplier(new_streak)
        coins_earned = int(round(base_coins * multiplier))

        xp_earned = 100 if is_photo else 50
        tourney_pts = 100 if is_photo else 50

        partner_id = user["duo_partner_id"]
        if partner_id and partner_id != 0:
            cursor.execute("SELECT last_checkin_date FROM users WHERE user_id = ?", (partner_id,))
            p_row = cursor.fetchone()
            if p_row and p_row["last_checkin_date"] == today_str:
                coins_earned += 50
                xp_earned += 25
                tourney_pts += 25

        new_coins = user["coins"] + coins_earned
        new_xp = (user["xp"] if "xp" in user.keys() and user["xp"] else 0) + xp_earned
        rpg_data = calculate_rpg_level(new_xp, user["lang"] or "uz")
        new_level = rpg_data["level"]
        new_photo_count = user["photo_count"] + (1 if is_photo else 0)

        cursor.execute("""
            UPDATE users 
            SET streak = ?, coins = ?, xp = ?, level = ?, stamina = 100, last_stamina_update = ?, photo_count = ?, last_checkin_date = ?, status = 'awake'
            WHERE user_id = ?
        """, (new_streak, new_coins, new_xp, new_level, now_str, new_photo_count, today_str, user_id))

        if group_id != 0:
            cursor.execute("""
                INSERT INTO group_members (group_id, user_id, status, last_checkin_time, streak)
                VALUES (?, ?, 'awake', ?, ?)
                ON CONFLICT(group_id, user_id) DO UPDATE SET
                    status = 'awake',
                    last_checkin_time = excluded.last_checkin_time,
                    streak = excluded.streak
            """, (group_id, user_id, time_str, new_streak))

        cursor.execute("""
            INSERT INTO checkins (user_id, group_id, checkin_timestamp, checkin_date, coins_earned)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, group_id, now_str, today_str, coins_earned))

    db_add_tournament_points(user_id, user["first_name"], user["username"], tourney_pts, is_photo=is_photo)

    target_goal = user["target_goal"] if "target_goal" in user.keys() and user["target_goal"] else 21
    roleplay_enabled = user["roleplay_enabled"] if "roleplay_enabled" in user.keys() else 0
    active_universe = user["active_universe"] if "active_universe" in user.keys() and user["active_universe"] else "marvel"

    db_check_and_unlock_badges(user_id)
    return {
        "streak": new_streak,
        "goal": target_goal,
        "multiplier": multiplier,
        "coins": new_coins,
        "xp": new_xp,
        "level": new_level,
        "level_title": rpg_data["title"],
        "xp_earned": xp_earned,
        "photo_count": new_photo_count,
        "coins_earned": coins_earned,
        "checkin_time": time_str,
        "roleplay_enabled": roleplay_enabled,
        "active_universe": active_universe
    }

def db_reset_group_snoozed(group_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE group_members SET status = 'snoozed' WHERE group_id = ?", (group_id,))

def db_get_group_attendance_report(group_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.first_name, u.username, gm.status, gm.last_checkin_time, u.streak
            FROM group_members gm
            JOIN users u ON gm.user_id = u.user_id
            WHERE gm.group_id = ?
        """, (group_id,))
        return cursor.fetchall()

def db_get_global_leaderboard(limit: int = 10):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, username, streak, coins, level, xp FROM users ORDER BY streak DESC, coins DESC LIMIT ?", (limit,))
        return cursor.fetchall()

# ==================== GAMIFICATION HELPERS ====================
def get_user_rank(streak: int, lang: str = "uz") -> str:
    ranks = {
        "uz": ("👑 5 AM Afsonasi", "🏆 Ertalabki Usta", "⚔️ Intizom Jangchisi", "⚡ Porlayotgan Qaqnus", "🌅 Tonggi Yangi A'zo"),
        "ru": ("👑 Легенда 5 AM", "🏆 Мастер Утра", "⚔️ Воин Дисциплины", "⚡ Восходящий Феникс", "🌅 Рассветный Новичок"),
        "en": ("👑 5 AM Legend", "🏆 Morning Master", "⚔️ Discipline Warrior", "⚡ Rising Phoenix", "🌅 Dawn Novice")
    }
    r = ranks.get(lang, ranks["uz"])
    if streak >= 30: return r[0]
    elif streak >= 15: return r[1]
    elif streak >= 8: return r[2]
    elif streak >= 4: return r[3]
    else: return r[4]

def generate_progress_bar(streak: int, lang: str = "uz") -> str:
    ranks_next = {
        "uz": ("Porlayotgan Qaqnus ⚡", "Intizom Jangchisi ⚔️", "Ertalabki Usta 🏆", "5 AM Afsonasi 👑"),
        "ru": ("Восходящий Феникс ⚡", "Воин Дисциплины ⚔️", "Мастер Утра 🏆", "Легенда 5 AM 👑"),
        "en": ("Rising Phoenix ⚡", "Discipline Warrior ⚔️", "Morning Master 🏆", "5 AM Legend 👑")
    }
    rn = ranks_next.get(lang, ranks_next["uz"])

    if streak < 4: target, prev, next_rank = 4, 0, rn[0]
    elif streak < 8: target, prev, next_rank = 8, 4, rn[1]
    elif streak < 15: target, prev, next_rank = 15, 8, rn[2]
    elif streak < 30: target, prev, next_rank = 30, 15, rn[3]
    else:
        max_str = {"uz": "👑 **Maksimal Unvon: 5 AM Afsonasi!**", "ru": "👑 **Макс. Ранг: Легенда 5 AM!**", "en": "👑 **Max Rank: 5 AM Legend!**"}
        return max_str.get(lang, max_str["uz"])

    progress = max(0.0, min(1.0, (streak - prev) / (target - prev)))
    filled_length = int(round(10 * progress))
    bar = '█' * filled_length + '░' * (10 - filled_length)
    pct = int(progress * 100)
    days_left = target - streak

    labels = {
        "uz": f"Progress: [{bar}] {pct}%\nKeyingi unvonga **{days_left} kun** qoldi ({next_rank})",
        "ru": f"Прогресс: [{bar}] {pct}%\nДо след. ранга **{days_left} дн.** ({next_rank})",
        "en": f"Progress: [{bar}] {pct}%\nNext Rank: **{next_rank}** in {days_left} day(s)"
    }
    return labels.get(lang, labels["uz"])

def generate_xp_progress_bar(xp: int, lang: str = "uz") -> str:
    rpg = calculate_rpg_level(xp, lang)
    pct = int(rpg["progress_pct"])
    filled = int(round(10 * (pct / 100)))
    bar = '█' * filled + '░' * (10 - filled)
    return f"Level {rpg['level']} [{bar}] {pct}% ({rpg['xp_in_level']}/{rpg['xp_needed_level']} XP)"

def get_user_language(user_id: int) -> str:
    user = db_get_user(user_id)
    if user and "lang" in user.keys() and user["lang"]:
        return user["lang"]
    return "uz"

# ==================== CATALOG HUB REPLIES & KEYBOARDS ====================
def get_main_reply_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    buttons = [
        [KeyboardButton(text=t["hub_solo"]), KeyboardButton(text=t["hub_multiverse"])],
        [KeyboardButton(text=t["hub_arena"]), KeyboardButton(text=t["hub_settings"])],
        [KeyboardButton(text=t["hub_quote"])]
    ]
    if user_id == SUPER_ADMIN_ID:
        buttons.append([KeyboardButton(text=t["btn_admin"])])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_solo_hub_inline_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    labels = {
        "uz": {
            "do_checkin": "⚡ Hozir Check-In Qilish",
            "photo": "📸 Foto Check-In Yuborish",
            "stats": "📊 Shaxsiy Statistika & Maqsad",
            "goal": "🎯 Kunlik Maqsadni Sozlash (21/30/100/365)",
            "bedtime": "🌙 21:30 Uyqu Protokoli",
            "cert": "📜 21 Kunlik Sertifikat"
        },
        "ru": {
            "do_checkin": "⚡ Сделать Check-In Сейчас",
            "photo": "📸 Отправить Фото Check-In",
            "stats": "📊 Личная Статистика & Цель",
            "goal": "🎯 Настройка Цели (21/30/100/365)",
            "bedtime": "🌙 21:30 Протокол Сна",
            "cert": "📜 21-Дневный Сертификат"
        },
        "en": {
            "do_checkin": "⚡ Check-In Now",
            "photo": "📸 Send Photo Check-In",
            "stats": "📊 Personal Stats & Goal",
            "goal": "🎯 Set Daily Target (21/30/100/365)",
            "bedtime": "🌙 21:30 Bedtime Protocol",
            "cert": "📜 21-Day Certificate"
        }
    }
    l = labels.get(lang, labels["uz"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=l["do_checkin"], callback_data="solo_do_checkin")],
        [InlineKeyboardButton(text=l["photo"], callback_data="solo_photo_checkin")],
        [InlineKeyboardButton(text=l["stats"], callback_data="solo_my_stats")],
        [InlineKeyboardButton(text=l["goal"], callback_data="solo_target_goal_menu")],
        [InlineKeyboardButton(text=l["bedtime"], callback_data="solo_bedtime")],
        [InlineKeyboardButton(text=l["cert"], callback_data="solo_cert")]
    ])

def get_multiverse_hub_inline_keyboard(user_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    u = db_get_user(user_id)
    rp_on = u["roleplay_enabled"] if u and "roleplay_enabled" in u.keys() else 0

    rp_toggle_labels = {
        "uz": ("🎭 Roleplay: [ ✅ YOQILGAN ]", "🎭 Roleplay: [ ❌ O'CHIRILGAN ]", "👁️ Realm Atmosferasini Ko'rish"),
        "ru": ("🎭 Roleplay: [ ✅ ВКЛЮЧЕН ]", "🎭 Roleplay: [ ❌ ВЫКЛЮЧЕН ]", "👁️ Просмотр Атмосферы Мира"),
        "en": ("🎭 Roleplay: [ ✅ ENABLED ]", "🎭 Roleplay: [ ❌ DISABLED ]", "👁️ Preview Realm Atmosphere")
    }
    t_on, t_off, t_prev = rp_toggle_labels.get(lang, rp_toggle_labels["uz"])
    rp_toggle_text = t_on if rp_on else t_off

    buttons = [
        [InlineKeyboardButton(text=rp_toggle_text, callback_data="rp_toggle")],
        [InlineKeyboardButton(text="🦸 Marvel Avengers", callback_data="rp_realm_marvel"), InlineKeyboardButton(text="🗡️ Samurai Bushido", callback_data="rp_realm_samurai")],
        [InlineKeyboardButton(text="🏰 Feudal Knights", callback_data="rp_realm_feudal"), InlineKeyboardButton(text="🎩 Mafia Syndicate", callback_data="rp_realm_mafia")],
        [InlineKeyboardButton(text="⚡ Greek Olympus", callback_data="rp_realm_olympus"), InlineKeyboardButton(text="🚀 Cyberpunk 2077", callback_data="rp_realm_cyberpunk")],
        [InlineKeyboardButton(text="🥷 Anime Multiverse", callback_data="rp_realm_anime")],
        [InlineKeyboardButton(text=t_prev, callback_data="rp_preview")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_arena_hub_inline_keyboard(user_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    u = db_get_user(user_id)
    arena_on = u["interactive_enabled"] if u and "interactive_enabled" in u.keys() else 1

    labels = {
        "uz": {
            "toggle_on": "🎮 Interaktiv Rejim: [ ✅ YOQILGAN ]",
            "toggle_off": "🎮 Interaktiv Rejim: [ ❌ O'CHIRILGAN ]",
            "shop": "🛒 Marketplace & Do'kon",
            "squad": "🛡️ Klan / Squad Info",
            "wheel": "🎡 Daily Wheel of Fortune",
            "duel": "⚔️ 1v1 Uyg'onish Dueli (-20 Stamina)",
            "duo": "🤝 Duo Combo Sheriklik",
            "match": "🎲 Random Matchmaking Sherik",
            "tourney": "🏆 Haftalik Turnir Reytingi",
            "lead": "📊 Global Reyting Jadvali"
        },
        "ru": {
            "toggle_on": "🎮 Интерактивный Режим: [ ✅ ВКЛЮЧЕН ]",
            "toggle_off": "🎮 Интерактивный Режим: [ ❌ ВЫКЛЮЧЕН ]",
            "shop": "🛒 Магазин и Маркет",
            "squad": "🛡️ Информация о Кланах",
            "wheel": "🎡 Колесо Удачи",
            "duel": "⚔️ Дуэль 1v1 (-20 Stamina)",
            "duo": "🤝 Парный Режим Duo Combo",
            "match": "🎲 Случайный Подбор Партнера",
            "tourney": "🏆 Турнирный Рейтинг",
            "lead": "📊 Глобальная Таблица Лидеров"
        },
        "en": {
            "toggle_on": "🎮 Interactive Mode: [ ✅ ENABLED ]",
            "toggle_off": "🎮 Interactive Mode: [ ❌ DISABLED ]",
            "shop": "🛒 Marketplace & Shop",
            "squad": "🛡️ Squad & Clan Info",
            "wheel": "🎡 Daily Wheel of Fortune",
            "duel": "⚔️ 1v1 Wake-up Duel (-20 Stamina)",
            "duo": "🤝 Duo Combo Partner",
            "match": "🎲 Random Matchmaking",
            "tourney": "🏆 Weekly Tournament",
            "lead": "📊 Global Leaderboard"
        }
    }
    l = labels.get(lang, labels["uz"])
    arena_toggle_text = l["toggle_on"] if arena_on else l["toggle_off"]

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=arena_toggle_text, callback_data="arena_toggle")],
        [InlineKeyboardButton(text=l["shop"], callback_data="shop_menu")],
        [InlineKeyboardButton(text=l["squad"], callback_data="squad_info_cb")],
        [InlineKeyboardButton(text=l["wheel"], callback_data="spin_wheel")],
        [InlineKeyboardButton(text=l["duel"], callback_data="game_1v1_info")],
        [InlineKeyboardButton(text=l["duo"], callback_data="game_duo_info")],
        [InlineKeyboardButton(text=l["match"], callback_data="game_matchmaking")],
        [InlineKeyboardButton(text=l["tourney"], callback_data="arena_tournament")],
        [InlineKeyboardButton(text=l["lead"], callback_data="arena_leaderboard")]
    ])

def get_settings_hub_inline_keyboard(user_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    u = db_get_user(user_id)
    pm_on = u["pm_reminder_enabled"] if u and "pm_reminder_enabled" in u.keys() else 1
    strictness = u["photo_strictness"] if u and "photo_strictness" in u.keys() and u["photo_strictness"] else "medium"

    labels = {
        "uz": {
            "time": "⏰ Uyg'onish Vaqtini Sozlash",
            "pm_on": "🔔 PM Eslatmalar: [ ✅ YOQILGAN ]",
            "pm_off": "🔔 PM Eslatmalar: [ ❌ O'CHIRILGAN ]",
            "strict": f"📸 Foto Strictness: [ {strictness.upper()} ]",
            "lang": "🌐 Tilni Tanlash / Language",
            "ref": "👥 Taklif Qilish (+100 Coin)",
            "help": "📖 Qoidalar va Qo'llanma"
        },
        "ru": {
            "time": "⏰ Настройка Времени Подъема",
            "pm_on": "🔔 PM Напоминания: [ ✅ ВКЛЮЧЕНЫ ]",
            "pm_off": "🔔 PM Напоминания: [ ❌ ВЫКЛЮЧЕНЫ ]",
            "strict": f"📸 Строгость Фото: [ {strictness.upper()} ]",
            "lang": "🌐 Выбор Языка / Language",
            "ref": "👥 Пригласить Друзей (+100 Монет)",
            "help": "📖 Правила и Справка"
        },
        "en": {
            "time": "⏰ Set Wake-up Window",
            "pm_on": "🔔 PM Reminders: [ ✅ ENABLED ]",
            "pm_off": "🔔 PM Reminders: [ ❌ DISABLED ]",
            "strict": f"📸 Photo Strictness: [ {strictness.upper()} ]",
            "lang": "🌐 Choose Language",
            "ref": "👥 Invite Friends (+100 Coins)",
            "help": "📖 Rules & Guidelines"
        }
    }
    l = labels.get(lang, labels["uz"])
    pm_text = l["pm_on"] if pm_on else l["pm_off"]

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=l["time"], callback_data="set_time_menu")],
        [InlineKeyboardButton(text=pm_text, callback_data="toggle_pm_reminder")],
        [InlineKeyboardButton(text=l["strict"], callback_data="strictness_menu")],
        [InlineKeyboardButton(text=l["lang"], callback_data="lang_menu")],
        [InlineKeyboardButton(text=l["ref"], callback_data="ref_menu")],
        [InlineKeyboardButton(text=l["help"], callback_data="help_menu")]
    ])

def get_checkin_inline_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["uz"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["checkin_btn_inline"], callback_data="do_checkin")]
    ])

def get_bedtime_inline_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["uz"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["bedtime_btn"], callback_data="bedtime_sleep_now")]
    ])

def get_language_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="set_lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en")
        ]
    ])

def get_start_language_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="start_lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="start_lang_ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="start_lang_en")
        ]
    ])

# ==================== STEP-BY-STEP ONBOARDING WIZARDS ====================
# --- PRIVATE SOLO ONBOARDING WIZARD ---
def get_solo_wizard_step1_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Boshlash (1/4) ->", callback_data="sw_step_2")]
    ])

def get_solo_wizard_step2_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏰ 04:30 - 06:00 (Standard 5 AM)", callback_data="sw_time_04:30_06:00")],
        [InlineKeyboardButton(text="⏰ 05:00 - 06:30 (Early Bird)", callback_data="sw_time_05:00_06:30")],
        [InlineKeyboardButton(text="⏰ 05:30 - 07:00 (Morning Power)", callback_data="sw_time_05:30_07:00")],
        [InlineKeyboardButton(text="⏰ 06:00 - 07:30 (Flex Dawn)", callback_data="sw_time_06:00_07:30")]
    ])

def get_solo_wizard_step3_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏃 21 Kun (Sprint Odat)", callback_data="sw_goal_21")],
        [InlineKeyboardButton(text="🔥 30 Kun (Chidamli Odat)", callback_data="sw_goal_30")],
        [InlineKeyboardButton(text="⚔️ 100 Kun (Master Intizom)", callback_data="sw_goal_100")],
        [InlineKeyboardButton(text="👑 365 Kun (Afsonaviy Maraton)", callback_data="sw_goal_365")],
        [InlineKeyboardButton(text="♾️ Cheksiz Goal", callback_data="sw_goal_0")]
    ])

def get_solo_wizard_step4_kb(user_id: int) -> InlineKeyboardMarkup:
    u = db_get_user(user_id)
    rp_on = u["roleplay_enabled"] if u and "roleplay_enabled" in u.keys() else 0
    arena_on = u["interactive_enabled"] if u and "interactive_enabled" in u.keys() else 1
    pm_on = u["pm_reminder_enabled"] if u and "pm_reminder_enabled" in u.keys() else 1

    rp_status = "✅ ON" if rp_on else "❌ OFF"
    arena_status = "✅ ON" if arena_on else "❌ OFF"
    pm_status = "✅ ON" if pm_on else "❌ OFF"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🎭 Multiverse Roleplay: [{rp_status}]", callback_data="sw_toggle_rp")],
        [InlineKeyboardButton(text=f"🎮 Interaktiv Arena: [{arena_status}]", callback_data="sw_toggle_arena")],
        [InlineKeyboardButton(text=f"🔔 PM Eslatmalari: [{pm_status}]", callback_data="sw_toggle_pm")],
        [InlineKeyboardButton(text="🚀 SOZLASHNI YAKUNLASH & BOSHLASH", callback_data="sw_finish")]
    ])

# --- GROUP ONBOARDING WIZARD ---
def get_group_wizard_step1_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Guruh Sozlashni Boshlash ->", callback_data="gw_step_2")]
    ])

def get_group_wizard_step2_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Avtomatik Opt-In (Barcha A'zolar)", callback_data="gw_opt_auto")],
        [InlineKeyboardButton(text="✋ Qo'lda Opt-In (Tugma orqali a'zo bo'lish)", callback_data="gw_opt_manual")]
    ])

def get_group_wizard_step3_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏰ 04:30 - 06:00", callback_data="gw_time_04:30_06:00")],
        [InlineKeyboardButton(text="⏰ 05:00 - 06:30", callback_data="gw_time_05:00_06:30")],
        [InlineKeyboardButton(text="⏰ 05:30 - 07:00", callback_data="gw_time_05:30_07:00")]
    ])

def get_group_wizard_step4_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛡️ Marvel Avengers", callback_data="gw_realm_marvel"), InlineKeyboardButton(text="⚔️ Medieval Samurai", callback_data="gw_realm_samurai")],
        [InlineKeyboardButton(text="🏰 Feudal Knights", callback_data="gw_realm_feudal"), InlineKeyboardButton(text="🎩 Italian Mafia", callback_data="gw_realm_mafia")],
        [InlineKeyboardButton(text="⚡ Greek Olympus", callback_data="gw_realm_olympus"), InlineKeyboardButton(text="🚀 Cyberpunk 2077", callback_data="gw_realm_cyberpunk")],
        [InlineKeyboardButton(text="🥷 Anime Multiverse", callback_data="gw_realm_anime")],
        [InlineKeyboardButton(text="🚀 GURUHNI FAOL LASHTIRISH (FINISH)", callback_data="gw_finish")]
    ])

# ==================== HANDLERS ====================
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    args = message.text.split()

    ref_by = 0
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            ref_by = int(args[1].replace("ref_", ""))
        except Exception:
            pass

    db_register_user(user.id, user.username, user.first_name, ref_by=ref_by)

    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        db_register_group(message.chat.id, message.chat.title)
        db_link_group_member(message.chat.id, user.id)
        msg = (
            "🌅 **THE 5 AM CLUB GURUH ONBOARDING**\n\n"
            "Guruh a'zolarining intizomini oshirish uchun sozlashni boshlang!"
        )
        await message.reply(msg, reply_markup=get_group_wizard_step1_kb(), parse_mode=ParseMode.MARKDOWN)
    else:
        lang_msg = (
            f"👋 **\"The 5 AM Club\" botiga xush kelibsiz, {html.escape(user.first_name)}!**\n\n"
            "🌐 **1-QADAM: Muloqot tilini tanlang / Choose language / Выберите язык:**"
        )
        await message.answer(lang_msg, reply_markup=get_start_language_inline_keyboard(), parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data.startswith("start_lang_"))
async def start_lang_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = callback.data.replace("start_lang_", "")
    db_update_user_lang(user_id, lang)
    await callback.answer()

    t = TEXTS.get(lang, TEXTS["uz"])
    await callback.message.answer(t["lang_updated"], reply_markup=get_main_reply_keyboard(user_id), parse_mode=ParseMode.MARKDOWN)

    user_name = html.escape(callback.from_user.first_name or "Champion")
    welcome_str = t.get('welcome', '👋').format(name=user_name)
    wiz_msg = (
        f"{welcome_str}\n\n"
        "📌 **4 Bosqichli Solo Onboarding Wizard (2/4):**\n"
        "Keling, ertalabki uyg'onish vaqtingiz, kunlik intizomiy maqsad hamda Multiverse rejimlarini sozlaymiz!"
    )
    await callback.message.answer(wiz_msg, reply_markup=get_solo_wizard_step1_kb(), parse_mode=ParseMode.MARKDOWN)

# --- SOLO ONBOARDING WIZARD CALLBACKS ---
@router.callback_query(F.data == "sw_step_2")
async def sw_step_2_cb(callback: CallbackQuery):
    await callback.answer()
    msg = (
        "⏰ **1-QADAM: Uyg'onish Vaqti Oralig'ini Tanlang:**\n\n"
        "Har kuni ertalab qaysi vaqt oraliqlarida check-in qilasiz?"
    )
    await callback.message.edit_text(msg, reply_markup=get_solo_wizard_step2_kb(), parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data.startswith("sw_time_"))
async def sw_time_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    parts = callback.data.split("_")
    s_t, e_t = parts[2], parts[3]
    db_update_user_times(user_id, s_t, e_t)
    await callback.answer("✅ Vaqt saqlandi!")

    msg = (
        f"✅ **Vaqt oralig'i soat `{s_t}` - `{e_t}` qilib belgilandi!**\n\n"
        "🎯 **2-QADAM: Intizomiy Maqsadingizni Tanlang:**\n"
        "Necha kunlik uzluksiz 5 AM uyg'onish maratonida qatnashasiz?"
    )
    await callback.message.edit_text(msg, reply_markup=get_solo_wizard_step3_kb(), parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data.startswith("sw_goal_"))
async def sw_goal_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    goal_val = int(callback.data.split("_")[2])
    db_update_user_setting(user_id, "target_goal", goal_val)
    await callback.answer("✅ Maqsad saqlandi!")

    goal_str = "Cheksiz (Infinite)" if goal_val == 0 else f"{goal_val} kun"
    msg = (
        f"✅ **Maqsadingiz: `{goal_str}` kilib belgilandi!**\n\n"
        "🎭 **3-QADAM: Rejimlar va Eslatmalarni Sozlang:**\n"
        "Multiverse Roleplay va Arena imkoniyatlarini yoqing yoki o'chiring:"
    )
    await callback.message.edit_text(msg, reply_markup=get_solo_wizard_step4_kb(user_id), parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data == "sw_toggle_rp")
async def sw_toggle_rp_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    u = db_get_user(user_id)
    curr = u["roleplay_enabled"] if u and "roleplay_enabled" in u.keys() else 0
    new_val = 0 if curr == 1 else 1
    db_update_user_setting(user_id, "roleplay_enabled", new_val)
    await callback.answer("✅ Roleplay rejim yangilandi!")
    await callback.message.edit_reply_markup(reply_markup=get_solo_wizard_step4_kb(user_id))

@router.callback_query(F.data == "sw_toggle_arena")
async def sw_toggle_arena_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    u = db_get_user(user_id)
    curr = u["interactive_enabled"] if u and "interactive_enabled" in u.keys() else 1
    new_val = 0 if curr == 1 else 1
    db_update_user_setting(user_id, "interactive_enabled", new_val)
    await callback.answer("✅ Arena rejim yangilandi!")
    await callback.message.edit_reply_markup(reply_markup=get_solo_wizard_step4_kb(user_id))

@router.callback_query(F.data == "sw_toggle_pm")
async def sw_toggle_pm_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    u = db_get_user(user_id)
    curr = u["pm_reminder_enabled"] if u and "pm_reminder_enabled" in u.keys() else 1
    new_val = 0 if curr == 1 else 1
    db_update_user_setting(user_id, "pm_reminder_enabled", new_val)
    await callback.answer("✅ PM Eslatmalari yangilandi!")
    await callback.message.edit_reply_markup(reply_markup=get_solo_wizard_step4_kb(user_id))

@router.callback_query(F.data == "sw_finish")
async def sw_finish_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.answer("🚀 Solo Onboarding Yakunlandi!", show_alert=True)
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    welcome_text = (
        "🎉 **SOLO ONBOARDING MUVAFFAQIYATLI YAKUNLANDI!**\n\n"
        "“Sizning har bir ertalabki intizomingiz buyuk kelajagingiz tamal tashidir!”\n\n"
        "👇 Quydagi 4 ta asosiy katalog menyusidan foydalanishingiz mumkin:"
    )
    await callback.message.answer(welcome_text, reply_markup=get_main_reply_keyboard(user_id), parse_mode=ParseMode.MARKDOWN)

# --- GROUP ONBOARDING WIZARD CALLBACKS ---
@router.callback_query(F.data == "gw_step_2")
async def gw_step_2_cb(callback: CallbackQuery):
    member = await callback.bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR] and callback.from_user.id != SUPER_ADMIN_ID:
        await callback.answer("⛔ Bu amaldan faqat guruh adminlari foydalana oladi!", show_alert=True)
        return
    await callback.answer()
    msg = "👥 **1-QADAM: Guruh A'zolarini Opt-In Qilish Rejimi:**"
    await callback.message.edit_text(msg, reply_markup=get_group_wizard_step2_kb(), parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data.startswith("gw_opt_"))
async def gw_opt_cb(callback: CallbackQuery):
    group_id = callback.message.chat.id
    mode = "auto" if callback.data == "gw_opt_auto" else "manual"
    db_update_group_setting(group_id, "opt_in_mode", mode)
    await callback.answer("✅ Opt-In mode saqlandi!")

    msg = "⏰ **2-QADAM: Guruh Uyg'onish Vaqti Oralig'ini Tanlang:**"
    await callback.message.edit_text(msg, reply_markup=get_group_wizard_step3_kb(), parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data.startswith("gw_time_"))
async def gw_time_cb(callback: CallbackQuery):
    group_id = callback.message.chat.id
    parts = callback.data.split("_")
    s_t, e_t = parts[2], parts[3]
    db_update_group_times(group_id, s_t, e_t)
    await callback.answer("✅ Guruh vaqti saqlandi!")

    msg = "🎭 **3-QADAM: Guruh Multiverse Realm Koinotini Tanlang:**"
    await callback.message.edit_text(msg, reply_markup=get_group_wizard_step4_kb(), parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data.startswith("gw_realm_"))
async def gw_realm_cb(callback: CallbackQuery):
    group_id = callback.message.chat.id
    realm_key = callback.data.replace("gw_realm_", "")
    db_update_group_setting(group_id, "active_universe", realm_key)
    db_update_group_setting(group_id, "roleplay_enabled", 1)
    await callback.answer(f"✅ Realm '{realm_key.upper()}' guruhga biriktirildi!")

@router.callback_query(F.data == "gw_finish")
async def gw_finish_cb(callback: CallbackQuery):
    await callback.answer("🚀 Guruh Sozlamalari Muvaffaqiyatli Saqlandi!", show_alert=True)
    msg = (
        "🎉 **THE 5 AM CLUB GURUH ONBOARDING YAKUNLANDI!**\n\n"
        "Guruh bot vaqtlari va Multiverse koinoti tayyor! Har kuni ertalab 5 AM check-in o'ynasi ochiladi!"
    )
    await callback.message.edit_text(msg, parse_mode=ParseMode.MARKDOWN)

# --- 4 MAIN CATALOG HUB HANDLERS ---
@router.message(F.text.in_(["🌅 Solo Rejim", "🌅 Соло Режим", "🌅 Solo Mode"]))
@router.message(Command("solo"))
async def handle_hub_solo(message: Message):
    user_id = message.from_user.id
    db_register_user(user_id, message.from_user.username, message.from_user.first_name)
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    await message.answer(t["solo_menu_title"], reply_markup=get_solo_hub_inline_keyboard(lang), parse_mode=ParseMode.MARKDOWN)

@router.message(F.text.in_(["🎭 Multiverse Roleplay", "🎭 Мультивселенная"]))
@router.message(Command("roleplay"))
async def handle_hub_multiverse(message: Message):
    user_id = message.from_user.id
    db_register_user(user_id, message.from_user.username, message.from_user.first_name)
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    await message.answer(t["multiverse_menu_title"], reply_markup=get_multiverse_hub_inline_keyboard(user_id, lang), parse_mode=ParseMode.MARKDOWN)

@router.message(F.text.in_(["🎮 Interaktiv Arena", "🎮 Интерактивная Арена", "🎮 Interactive Arena"]))
@router.message(Command("arena"))
async def handle_hub_arena(message: Message):
    user_id = message.from_user.id
    db_register_user(user_id, message.from_user.username, message.from_user.first_name)
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    await message.answer(t["arena_menu_title"], reply_markup=get_arena_hub_inline_keyboard(user_id, lang), parse_mode=ParseMode.MARKDOWN)

@router.message(F.text.in_(["⚙️ Sozlamalar & Yordam", "⚙️ Настройки и Помощь", "⚙️ Settings & Help"]))
async def handle_hub_settings(message: Message):
    user_id = message.from_user.id
    db_register_user(user_id, message.from_user.username, message.from_user.first_name)
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    await message.answer(t["settings_menu_title"], reply_markup=get_settings_hub_inline_keyboard(user_id, lang), parse_mode=ParseMode.MARKDOWN)

@router.message(F.text.in_(["💡 Kun Hikmati", "💡 Мудрость Дня", "💡 Daily Wisdom"]))
@router.message(Command("quote"))
async def handle_hub_quote(message: Message):
    user_id = message.from_user.id
    db_register_user(user_id, message.from_user.username, message.from_user.first_name)
    lang = get_user_language(user_id)
    quote = await fetch_motivational_quote(user_id, lang)
    await message.answer(quote, parse_mode=ParseMode.MARKDOWN)

# --- HUB SUBMENU CALLBACKS ---
@router.callback_query(F.data == "rp_toggle")
async def handle_rp_toggle_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    u = db_get_user(user_id)
    curr = u["roleplay_enabled"] if u and "roleplay_enabled" in u.keys() else 0
    new_val = 0 if curr == 1 else 1
    db_update_user_setting(user_id, "roleplay_enabled", new_val)
    status_str = "yoqildi" if new_val == 1 else "o'chirildi"
    await callback.answer(f"✅ Multiverse Roleplay {status_str}!")
    lang = get_user_language(user_id)
    await callback.message.edit_reply_markup(reply_markup=get_multiverse_hub_inline_keyboard(user_id, lang))

@router.callback_query(F.data.startswith("rp_realm_"))
async def handle_rp_realm_select_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    realm_key = callback.data.replace("rp_realm_", "")
    if realm_key in REALMS:
        db_update_user_setting(user_id, "active_universe", realm_key)
        db_update_user_setting(user_id, "roleplay_enabled", 1)
        r_name = REALMS[realm_key]["name"]
        await callback.answer(f"🎉 Active Realm '{r_name}' tanlandi!")
        lang = get_user_language(user_id)
        await callback.message.edit_reply_markup(reply_markup=get_multiverse_hub_inline_keyboard(user_id, lang))

@router.callback_query(F.data == "rp_preview")
async def handle_rp_preview_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    u = db_get_user(user_id)
    curr_realm = u["active_universe"] if u and "active_universe" in u.keys() and u["active_universe"] else "marvel"
    realm = REALMS.get(curr_realm, REALMS["marvel"])
    lang = get_user_language(user_id)

    quips = realm["quips"].get(lang, realm["quips"]["uz"])
    titles = realm["titles"].get(lang, realm["titles"]["uz"])

    msg = (
        f"{realm['emoji']} **REALM PREVIEW: {realm['name']}**\n\n"
        f"👑 **Unvonlar Tizimi:** {', '.join(titles)}\n\n"
        f"💬 **Namuna Quip:**\n_{random.choice(quips)}_\n\n"
        f"💡 **Wisdom Prefix:** `{realm['wisdom_prefix']}`"
    )
    await callback.answer()
    await callback.message.answer(msg, parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data == "arena_toggle")
async def handle_arena_toggle_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    u = db_get_user(user_id)
    curr = u["interactive_enabled"] if u and "interactive_enabled" in u.keys() else 1
    new_val = 0 if curr == 1 else 1
    db_update_user_setting(user_id, "interactive_enabled", new_val)
    status_str = "yoqildi" if new_val == 1 else "o'chirildi"
    await callback.answer(f"✅ Interaktiv Arena {status_str}!")
    lang = get_user_language(user_id)
    await callback.message.edit_reply_markup(reply_markup=get_arena_hub_inline_keyboard(user_id, lang))

@router.callback_query(F.data == "toggle_pm_reminder")
async def handle_toggle_pm_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    u = db_get_user(user_id)
    curr = u["pm_reminder_enabled"] if u and "pm_reminder_enabled" in u.keys() else 1
    new_val = 0 if curr == 1 else 1
    db_update_user_setting(user_id, "pm_reminder_enabled", new_val)
    status_str = "yoqildi" if new_val == 1 else "o'chirildi"
    await callback.answer(f"✅ PM Eslatmalar {status_str}!")
    lang = get_user_language(user_id)
    await callback.message.edit_reply_markup(reply_markup=get_settings_hub_inline_keyboard(user_id, lang))

@router.callback_query(F.data == "strictness_menu")
async def handle_strictness_menu_cb(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Yengil (Low Strictness)", callback_data="set_strictness_low")],
        [InlineKeyboardButton(text="🟡 O'rtacha (Medium Strictness)", callback_data="set_strictness_medium")],
        [InlineKeyboardButton(text="🔴 Qattiq (High Strictness)", callback_data="set_strictness_high")]
    ])
    await callback.answer()
    await callback.message.answer("📸 **Foto Strictness darajasini tanlang:**", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data.startswith("set_strictness_"))
async def handle_set_strictness_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    val = callback.data.replace("set_strictness_", "")
    db_update_user_setting(user_id, "photo_strictness", val)
    await callback.answer(f"✅ Foto strictness '{val.upper()}' deb belgilandi!", show_alert=True)

@router.callback_query(F.data.in_(["solo_random_quote", "get_random_quote"]))
async def handle_solo_random_quote_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_language(user_id)
    u = db_get_user(user_id)
    active_universe = u["active_universe"] if u and "active_universe" in u.keys() and u["active_universe"] else "marvel"
    quote_text = await fetch_motivational_quote(user_id=user_id, lang=lang, active_universe=active_universe)
    await callback.answer("💡 Yangi Kun Hikmati!")
    await callback.message.answer(f"💡 **KUN HIKMATI:**\n\n{quote_text}", parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data == "solo_bedtime")
async def handle_solo_bedtime_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])
    await callback.answer()
    await callback.message.answer(
        t["bedtime_reminder"],
        reply_markup=get_bedtime_inline_keyboard(lang),
        parse_mode=ParseMode.MARKDOWN
    )

@router.callback_query(F.data == "solo_target_goal_menu")
async def handle_target_goal_menu_cb(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("🎯 **Intizomiy maqsadingizni tanlang:**", reply_markup=get_solo_wizard_step3_kb(), parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data == "solo_cert")
async def handle_solo_cert_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    u = db_get_user(user_id)
    if u and u["streak"] >= 21:
        cert_bytes = await generate_21day_certificate(u["first_name"])
        if cert_bytes:
            cert_file = BufferedInputFile(cert_bytes, filename="21day_certificate.jpg")
            await callback.message.answer_photo(photo=cert_file, caption="📜 **Sizning 21 Kunlik Oltin Sertifikatingiz!**", parse_mode=ParseMode.MARKDOWN)
            return
    await callback.answer("⚠️ Oltin sertifikat olish uchun kamida 21 kunlik streak kerak!", show_alert=True)

@router.callback_query(F.data == "solo_do_checkin")
async def handle_solo_do_checkin_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    db_register_user(user_id, callback.from_user.username, callback.from_user.first_name)
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    u = db_get_user(user_id)
    start_t = u["checkin_start"] if u and "checkin_start" in u.keys() and u["checkin_start"] else "04:30"
    end_t = u["checkin_end"] if u and "checkin_end" in u.keys() and u["checkin_end"] else "06:00"

    if not is_time_in_window(start_t, end_t):
        warning_msg = t["not_in_window"].format(start=start_t, end=end_t)
        await callback.answer(warning_msg, show_alert=True)
        return

    res = db_process_checkin(user_id, group_id=0, is_photo=False)

    if res == "already":
        await callback.answer(t["already_checked_in"], show_alert=True)
    elif res:
        await callback.answer("⚡ Check-in Muvaffaqiyatli!", show_alert=False)
        try:
            chosen_emoji = random.choice(["🔥", "⚡", "🦅", "🏆", "🎉", "💪", "👍"])
            await callback.message.react(reaction=[ReactionTypeEmoji(emoji=chosen_emoji)])
        except Exception:
            pass

        quip = await fetch_dynamic_quip(res["streak"], callback.from_user.first_name, lang=lang, roleplay_enabled=res["roleplay_enabled"], active_universe=res["active_universe"])
        rank = get_user_rank(res["streak"], lang=lang)
        msg_text = t["checkin_success"].format(
            quip=quip,
            streak=res["streak"],
            goal=res["goal"],
            multiplier=res["multiplier"],
            coins_earned=res["coins_earned"],
            coins=res["coins"],
            xp_earned=res["xp_earned"],
            xp=res["xp"],
            level=res["level"],
            rank=rank
        )
        await callback.message.answer(msg_text, parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data == "solo_photo_checkin")
async def handle_solo_photo_checkin_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])
    mission = get_random_photo_mission(lang)

    prompt = t["photo_mission_prompt"].format(mission=mission)
    await callback.answer()
    await callback.message.answer(prompt, parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data == "solo_my_stats")
async def handle_solo_my_stats_callback(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    user = db_get_user(user_id)
    if not user:
        db_register_user(user_id, callback.from_user.username, callback.from_user.first_name)
        user = db_get_user(user_id)

    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    streak = user["streak"]
    coins = user["coins"]
    xp = user["xp"] if "xp" in user.keys() and user["xp"] else 0
    rpg = calculate_rpg_level(xp, lang=lang)
    stamina = db_calculate_and_update_stamina(dict(user))
    stamina_badge = "🟢 (Vitality Surge!)" if stamina >= 80 else "🟡 (Normal)"
    photo_count = user["photo_count"] if "photo_count" in user.keys() else 0
    freeze_count = user["freeze_count"] if "freeze_count" in user.keys() else 0
    ref_count = user["referral_count"] if "referral_count" in user.keys() else 0
    tourney_pts = db_get_user_tournament_points(user_id)
    rank = get_user_rank(streak, lang=lang)
    progress_bar = generate_progress_bar(streak, lang=lang)
    xp_bar = generate_xp_progress_bar(xp, lang=lang)
    lang_names = {"uz": "🇺🇿 O'zbekcha", "ru": "🇷🇺 Русский", "en": "🇬🇧 English"}
    start_t = user["checkin_start"] if "checkin_start" in user.keys() and user["checkin_start"] else "04:30"
    end_t = user["checkin_end"] if "checkin_end" in user.keys() and user["checkin_end"] else "06:00"
    goal_val = user["target_goal"] if "target_goal" in user.keys() and user["target_goal"] else 21
    rp_val = user["roleplay_enabled"] if "roleplay_enabled" in user.keys() else 0
    universe_val = user["active_universe"] if "active_universe" in user.keys() and user["active_universe"] else "marvel"
    universe_name = REALMS.get(universe_val, REALMS["marvel"])["name"]

    user_badges_list = db_get_user_badges(user_id, lang=lang)
    badges_str = " | ".join(user_badges_list) if user_badges_list else "Boshlang'ich nishonlar"

    profile_text = t["profile_title"].format(
        name=html.escape(user['first_name']),
        level=rpg["level"],
        level_title=rpg["title"],
        xp=xp,
        next_level_xp=rpg["next_level_total_xp"],
        progress_pct=rpg["progress_pct"],
        stamina=stamina,
        stamina_badge=stamina_badge,
        streak=streak,
        goal=goal_val,
        multiplier=get_streak_multiplier(streak),
        coins=coins,
        tourney_pts=tourney_pts,
        ref_count=ref_count,
        freeze_count=freeze_count,
        universe_name=universe_name,
        rp_status="YOQILGAN" if rp_val else "O'CHIRILGAN",
        rank=rank,
        start=start_t,
        end=end_t,
        badges=badges_str,
        lang_str=lang_names.get(lang, "🇺🇿 O'zbekcha"),
        xp_bar=xp_bar,
        progress_bar=progress_bar
    )
    await callback.message.answer(profile_text, parse_mode=ParseMode.MARKDOWN)

# --- GROUP & COMMON CHECK-IN CALLBACK ---
@router.callback_query(F.data == "do_checkin")
async def handle_callback_checkin(callback: CallbackQuery):
    try:
        user = callback.from_user
        db_register_user(user.id, user.username, user.first_name)
        lang = get_user_language(user.id)
        t = TEXTS.get(lang, TEXTS["uz"])

        chat_type = callback.message.chat.type if callback.message and callback.message.chat else None
        is_group = chat_type in [ChatType.GROUP, ChatType.SUPERGROUP]
        group_id = callback.message.chat.id if is_group else 0

        if group_id != 0:
            db_link_group_member(group_id, user.id)
            g = db_get_group(group_id)
            start_t = g["checkin_start"] if g and "checkin_start" in g.keys() and g["checkin_start"] else "04:30"
            end_t = g["checkin_end"] if g and "checkin_end" in g.keys() and g["checkin_end"] else "06:00"
        else:
            u = db_get_user(user.id)
            start_t = u["checkin_start"] if u and "checkin_start" in u.keys() and u["checkin_start"] else "04:30"
            end_t = u["checkin_end"] if u and "checkin_end" in u.keys() and u["checkin_end"] else "06:00"

        if not is_time_in_window(start_t, end_t):
            warning_msg = t["not_in_window"].format(start=start_t, end=end_t)
            await callback.answer(warning_msg, show_alert=True)
            return

        res = db_process_checkin(user.id, group_id=group_id, is_photo=False)

        if res == "already":
            await callback.answer(t["already_checked_in"], show_alert=True)
        elif res:
            popup_text = t["group_checkin_popup"].format(streak=res['streak'], coins=res['coins_earned'], xp=res['xp_earned'])
            await callback.answer(popup_text, show_alert=True)

            try:
                chosen_emoji = random.choice(["🔥", "⚡", "🦅", "🏆", "🎉", "💪", "👍"])
                await callback.message.react(reaction=[ReactionTypeEmoji(emoji=chosen_emoji)])
            except Exception:
                pass

            if group_id == 0:
                quip = await fetch_dynamic_quip(res["streak"], user.first_name, lang=lang, roleplay_enabled=res["roleplay_enabled"], active_universe=res["active_universe"])
                rank = get_user_rank(res["streak"], lang=lang)
                msg_text = t["checkin_success"].format(
                    quip=quip,
                    streak=res["streak"],
                    goal=res["goal"],
                    multiplier=res["multiplier"],
                    coins_earned=res["coins_earned"],
                    coins=res["coins"],
                    xp_earned=res["xp_earned"],
                    xp=res["xp"],
                    level=res["level"],
                    rank=rank
                )
                await callback.message.answer(msg_text, parse_mode=ParseMode.MARKDOWN)
            else:
                g = db_get_group(group_id)
                g_dict = dict(g) if g else {}
                g_lang = g_dict.get("lang") or lang
                realm = g_dict.get("active_universe", "standard") if g_dict.get("roleplay_enabled") else (res.get("active_universe", "standard") if res.get("roleplay_enabled") else "standard")

                quip_text = await fetch_dynamic_quip(res["streak"], user.first_name, lang=g_lang, roleplay_enabled=1 if realm != "standard" else 0, active_universe=realm)
                raw_name = html.escape(user.first_name or "Champion").replace("[", "").replace("]", "").replace("*", "").replace("_", "").replace("`", "")
                mention = f"[{raw_name}](https://t.me/{user.username})" if user.username else f"[{raw_name}](tg://user?id={user.id})"

                group_celebration = f"⚡ **CHECK-IN MUVAFFAQIYATLI!**\n\n⚡ {mention}: {quip_text}"
                try:
                    sent_reply = await callback.message.answer(
                        group_celebration,
                        reply_markup=get_reaction_inline_keyboard(group_id, 0, realm, g_lang),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    REACTIONS_STORE[f"{group_id}_{sent_reply.message_id}"] = {"0": 0, "1": 0, "2": 0, "users": {}}
                    await callback.bot.edit_message_reply_markup(
                        chat_id=group_id,
                        message_id=sent_reply.message_id,
                        reply_markup=get_reaction_inline_keyboard(group_id, sent_reply.message_id, realm, g_lang)
                    )
                except Exception as ex:
                    logging.error(f"Error sending group checkin celebration: {ex}")
        else:
            await callback.answer("⚡ Check-in bajarildi!", show_alert=True)
    except Exception as e:
        logging.error(f"Group checkin callback exception: {e}")
        try:
            await callback.answer("⚡ Check-in bajarildi!", show_alert=True)
        except Exception:
            pass

# --- BEDTIME PROTOCOL HANDLER ---
@router.callback_query(F.data.in_(["bedtime_sleep_now", "bedtime_sleep"]))
async def handle_bedtime_sleep_callback(callback: CallbackQuery):
    try:
        user_id = callback.from_user.id
        db_register_user(user_id, callback.from_user.username, callback.from_user.first_name)
        lang = get_user_language(user_id)
        t = TEXTS.get(lang, TEXTS["uz"])

        success, reason = db_record_bedtime(user_id)
        if success:
            await callback.answer(t.get("bedtime_success", "😴 Xayrli tun! +20 XP va 100% Stamina berildi!"), show_alert=True)
            if callback.message and callback.message.chat and callback.message.chat.type == ChatType.PRIVATE:
                await callback.message.answer(t["bedtime_success"], parse_mode=ParseMode.MARKDOWN)
        elif reason == "already_recorded":
            await callback.answer("⚠️ Bugun uxlash protokoli allaqachon qayd etilgan! Xayrli tun! 😴", show_alert=True)
        else:
            await callback.answer("😴 Xayrli tun!", show_alert=True)
    except Exception as e:
        logging.error(f"Bedtime callback exception: {e}")
        try: await callback.answer("😴 Xayrli tun!", show_alert=True)
        except Exception: pass

# --- THEMED REACTION CALLBACK HANDLER ---
@router.callback_query(F.data.startswith("react_"))
async def handle_reaction_cb(callback: CallbackQuery):
    try:
        if not callback.message or not callback.message.chat:
            await callback.answer()
            return
        parts = callback.data.split("_")
        idx = parts[1]
        realm = parts[2] if len(parts) > 2 else "standard"
        chat_id = callback.message.chat.id
        msg_id = callback.message.message_id
        user_id = callback.from_user.id

        key = f"{chat_id}_{msg_id}"
        if key not in REACTIONS_STORE:
            REACTIONS_STORE[key] = {"0": 0, "1": 0, "2": 0, "users": {}}

        store = REACTIONS_STORE[key]
        user_prev = store["users"].get(user_id)

        if user_prev == idx:
            store[idx] = max(0, store.get(idx, 0) - 1)
            del store["users"][user_id]
            await callback.answer("Reaksiya olib tashlandi!", show_alert=False)
        else:
            if user_prev is not None:
                store[user_prev] = max(0, store.get(user_prev, 0) - 1)
            store[idx] = store.get(idx, 0) + 1
            store["users"][user_id] = idx
            await callback.answer("✅ Reaksiya bildirildi!", show_alert=False)

        g = db_get_group(chat_id)
        lang = dict(g).get("lang") if g else get_user_language(user_id)
        try:
            await callback.message.edit_reply_markup(reply_markup=get_reaction_inline_keyboard(chat_id, msg_id, realm, lang or "uz"))
        except Exception:
            pass
    except Exception as e:
        logging.error(f"Reaction handler exception: {e}")
        try: await callback.answer()
        except Exception: pass

# --- GROUP MEMBER REGISTRATION HANDLER ---
@router.callback_query(F.data == "group_join_member")
async def handle_group_join_member_cb(callback: CallbackQuery):
    try:
        if not callback.message or not callback.message.chat:
            await callback.answer("✅ Ro'yxatdan o'tildi!", show_alert=True)
            return
        user = callback.from_user
        group = callback.message.chat
        db_register_user(user.id, user.username, user.first_name)
        db_link_group_member(group.id, user.id)

        await callback.answer("🎉 Guruhda omadli ro'yxatdan o'tdingiz!", show_alert=True)

        lang = get_user_language(user.id)
        t = TEXTS.get(lang, TEXTS["uz"])

        group_title = html.escape(group.title or "5 AM Club Group")
        group_url = f"https://t.me/{group.username}" if getattr(group, "username", None) else f"https://t.me/c/{str(group.id).replace('-100', '')}"

        pm_text = t.get("grp_registered_pm", "Siz {group} guruhida 5 AM Club uchun omadli ro'yxatdan o'tdingiz :)").format(group=group_title)
        btn_label = t.get("grp_to_group_btn", "Guruhga o'tish ↗")

        pm_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=btn_label, url=group_url)]
        ])

        try:
            await callback.bot.send_message(user.id, pm_text, reply_markup=pm_kb, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logging.warning(f"Could not send PM registration note to user {user.id}: {e}")
    except Exception as e:
        logging.error(f"Group join member exception: {e}")
        try: await callback.answer("✅ Ro'yxatdan o'tildi!", show_alert=True)
        except Exception: pass

@router.message(Command("bedtime"))
async def cmd_bedtime(message: Message):
    lang = get_user_language(message.from_user.id)
    t = TEXTS.get(lang, TEXTS["uz"])
    await message.reply(t["bedtime_reminder"], reply_markup=get_bedtime_inline_keyboard(lang), parse_mode=ParseMode.MARKDOWN)

# --- REFERRAL HANDLER ---
@router.callback_query(F.data == "ref_menu")
@router.message(Command("ref"))
async def handle_referral_btn(event):
    user_id = event.from_user.id
    user = db_get_user(user_id)
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    bot_info = await event.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    ref_count = user["referral_count"] if user and "referral_count" in user.keys() else 0

    msg = t["ref_text"].format(ref_link=ref_link, ref_count=ref_count)
    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.answer(msg, parse_mode=ParseMode.MARKDOWN)
    else:
        await event.answer(msg, parse_mode=ParseMode.MARKDOWN)

# --- TOURNAMENT HANDLER ---
@router.callback_query(F.data == "arena_tournament")
@router.message(Command("tournament"))
async def handle_tournament(event):
    lang = get_user_language(event.from_user.id)
    t = TEXTS.get(lang, TEXTS["uz"])

    participants, season = db_get_tournament_leaderboard(10)
    text = t["tournament_head"].format(season=season["season_number"], end_date=season["end_date"])

    if not participants:
        text += t["tournament_empty"]
    else:
        for idx, row in enumerate(participants, 1):
            medal = "👑 🥇" if idx == 1 else ("🥈" if idx == 2 else ("🥉" if idx == 3 else f"#{idx}"))
            text += f"`{medal}` **{html.escape(row['first_name'])}** — `{row['points']} pts` | 🔥 `{row['checkins_count']} check-in` | 📸 `{row['photos_count']} foto`\n"

    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.answer(text, parse_mode=ParseMode.MARKDOWN)
    else:
        await event.reply(text, parse_mode=ParseMode.MARKDOWN)

# --- ARENA CALLBACKS & HANDLERS ---
@router.callback_query(F.data == "game_matchmaking")
async def handle_matchmaking_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    partner_id, partner_name = db_matchmaking_find_or_enqueue(user_id)
    if partner_id:
        await callback.message.edit_text(t["matchmaking_found"].format(partner_name=html.escape(partner_name)), parse_mode=ParseMode.MARKDOWN)
        try:
            await callback.bot.send_message(partner_id, t["matchmaking_found"].format(partner_name=html.escape(callback.from_user.first_name)), parse_mode=ParseMode.MARKDOWN)
        except Exception:
            pass
    else:
        await callback.message.edit_text(t["matchmaking_searching"], parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data == "game_duo_info")
async def handle_duo_info_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = db_get_user(user_id)
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    partner_id = user["duo_partner_id"] if user and "duo_partner_id" in user.keys() else 0
    partner_str = f"`{partner_id}`" if partner_id else "None"

    msg = t["duo_title"] + f"\n\n🤝 **Sherigingiz / Partner:** {partner_str}\n\n" + t["duo_invite_prompt"]
    await callback.message.edit_text(msg, parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data == "game_1v1_info")
async def handle_1v1_info_cb(callback: CallbackQuery):
    msg = (
        "⚔️ **1v1 UYG'ONISH DUELI (CHALLENGE MODE)**\n\n"
        "Do'stingiz bilan 50 tanga tikib bellashing! (-20 Stamina)\n"
        "Kim ertalab birinchi foto check-in qilsa, **100 tangalik bank** va **+75 Turnir Balli**ni yutib oladi!\n\n"
        "📌 **Chaqirish uchun:** `/duel <do'stingizning_user_id>` yuboring!"
    )
    await callback.message.edit_text(msg, parse_mode=ParseMode.MARKDOWN)

# --- GROUP CONFIG CATALOG (/gconfig) & GAMES CATALOG (/games) ---
def get_group_config_inline_keyboard(group_id: int) -> InlineKeyboardMarkup:
    g = db_get_group(group_id)
    rp_on = g["roleplay_enabled"] if g and "roleplay_enabled" in g.keys() else 1
    arena_on = g["interactive_enabled"] if g and "interactive_enabled" in g.keys() else 1
    curr_realm = g["active_universe"] if g and "active_universe" in g.keys() and g["active_universe"] else "marvel"
    opt_mode = g["opt_in_mode"] if g and "opt_in_mode" in g.keys() and g["opt_in_mode"] else "auto"

    rp_btn_text = "🎭 Multiverse Roleplay: [ ✅ YOQILGAN ]" if rp_on else "🎭 Multiverse Roleplay: [ ❌ O'CHIRILGAN ]"
    arena_btn_text = "🎮 Interaktiv Rejim: [ ✅ YOQILGAN ]" if arena_on else "🎮 Interaktiv Rejim: [ ❌ O'CHIRILGAN ]"
    opt_btn_text = f"👥 Opt-In Rejimi: [ {opt_mode.upper()} ]"
    realm_btn_text = f"🌌 Realm: [{curr_realm.upper()}]"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=rp_btn_text, callback_data="gcfg_toggle_rp")],
        [InlineKeyboardButton(text=arena_btn_text, callback_data="gcfg_toggle_arena")],
        [InlineKeyboardButton(text=opt_btn_text, callback_data="gcfg_toggle_opt")],
        [InlineKeyboardButton(text=realm_btn_text, callback_data="gcfg_realm_menu")],
        [InlineKeyboardButton(text="⏰ Uyg'onish Vaqtini Sozlash", callback_data="gcfg_time_menu")],
        [InlineKeyboardButton(text="🔄 Yangilash / Status Check", callback_data="gcfg_refresh")]
    ])

def get_group_realm_select_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛡️ Marvel Avengers", callback_data="gcfg_setrealm_marvel"), InlineKeyboardButton(text="⚔️ Medieval Samurai", callback_data="gcfg_setrealm_samurai")],
        [InlineKeyboardButton(text="🏰 Feudal Knights", callback_data="gcfg_setrealm_feudal"), InlineKeyboardButton(text="🎩 Italian Mafia", callback_data="gcfg_setrealm_mafia")],
        [InlineKeyboardButton(text="⚡ Greek Olympus", callback_data="gcfg_setrealm_olympus"), InlineKeyboardButton(text="🚀 Cyberpunk 2077", callback_data="gcfg_setrealm_cyberpunk")],
        [InlineKeyboardButton(text="🥷 Anime Multiverse", callback_data="gcfg_setrealm_anime")]
    ])

def get_group_games_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ 1v1 Uyg'onish Dueli", callback_data="ggame_1v1_info")],
        [InlineKeyboardButton(text="🤝 Duo Combo Sheriklik", callback_data="ggame_duo_info")],
        [InlineKeyboardButton(text="🎲 Random Matchmaking Sherik", callback_data="game_matchmaking")],
        [InlineKeyboardButton(text="🏆 Haftalik Turnir Reytingi", callback_data="arena_tournament")],
        [InlineKeyboardButton(text="📊 Global Reyting Jadvali", callback_data="arena_leaderboard")]
    ])

@router.message(Command("gconfig"))
async def cmd_gconfig(message: Message):
    group_id = message.chat.id
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("ℹ️ Ushbu buyruq faqat guruhlar ichida ishlaydi!")
        return

    g = db_get_group(group_id)
    g_dict = dict(g) if g else {}
    start_t = g_dict.get("checkin_start", "04:30")
    end_t = g_dict.get("checkin_end", "06:00")
    rp_on = "✅ YOQILGAN" if g_dict.get("roleplay_enabled") else "❌ O'CHIRILGAN"
    arena_on = "✅ YOQILGAN" if g_dict.get("interactive_enabled") else "❌ O'CHIRILGAN"
    realm = g_dict.get("active_universe", "marvel").upper()
    opt = g_dict.get("opt_in_mode", "auto").upper()

    text = (
        "⚙️ **THE 5 AM CLUB GURUH BOSH QARUV KATALOGI**\n\n"
        f"⏰ **Uyg'onish vaqti:** `{start_t}` - `{end_t}`\n"
        f"🎭 **Roleplay Rejimi:** `{rp_on}`\n"
        f"🌌 **Faol Realm:** `{realm}`\n"
        f"🎮 **Interaktiv Rejim:** `{arena_on}`\n"
        f"👥 **Opt-In Rejimi:** `{opt}`\n\n"
        "👇 *Tugmalar orqali guruh sozlamalarini darhol o'zgartirishingiz mumkin:*"
    )
    await message.reply(text, reply_markup=get_group_config_inline_keyboard(group_id), parse_mode=ParseMode.MARKDOWN)

@router.message(Command("games"))
async def cmd_group_games(message: Message):
    text = (
        "🎮 **GURUH INTERAKTIV O'YINLAR VA DUELLAR KATALOGI**\n\n"
        "Guruh a'zolari bilan duellarda bellashing, juftlik hosil qiling va haftalik turnirda ball to'plang!\n\n"
        "👇 *Quyidagi o'yin va rejimni tanlang:*"
    )
    await message.reply(text, reply_markup=get_group_games_inline_keyboard(), parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data == "gcfg_toggle_rp")
async def gcfg_toggle_rp_cb(callback: CallbackQuery):
    group_id = callback.message.chat.id
    member = await callback.bot.get_chat_member(group_id, callback.from_user.id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR] and callback.from_user.id != SUPER_ADMIN_ID:
        await callback.answer("⛔ Bu amaldan faqat guruh adminlari foydalana oladi!", show_alert=True)
        return
    g = db_get_group(group_id)
    curr = g["roleplay_enabled"] if g and "roleplay_enabled" in g.keys() else 1
    new_val = 0 if curr == 1 else 1
    db_update_group_setting(group_id, "roleplay_enabled", new_val)
    status_str = "YOQILDI" if new_val == 1 else "O'CHIRILDI"
    await callback.answer(f"✅ Guruh Roleplay rejimi {status_str}!", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=get_group_config_inline_keyboard(group_id))

@router.callback_query(F.data == "gcfg_toggle_arena")
async def gcfg_toggle_arena_cb(callback: CallbackQuery):
    group_id = callback.message.chat.id
    member = await callback.bot.get_chat_member(group_id, callback.from_user.id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR] and callback.from_user.id != SUPER_ADMIN_ID:
        await callback.answer("⛔ Bu amaldan faqat guruh adminlari foydalana oladi!", show_alert=True)
        return
    g = db_get_group(group_id)
    curr = g["interactive_enabled"] if g and "interactive_enabled" in g.keys() else 1
    new_val = 0 if curr == 1 else 1
    db_update_group_setting(group_id, "interactive_enabled", new_val)
    status_str = "YOQILDI" if new_val == 1 else "O'CHIRILDI"
    await callback.answer(f"✅ Guruh Interaktiv rejimi {status_str}!", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=get_group_config_inline_keyboard(group_id))

@router.callback_query(F.data == "gcfg_toggle_opt")
async def gcfg_toggle_opt_cb(callback: CallbackQuery):
    group_id = callback.message.chat.id
    member = await callback.bot.get_chat_member(group_id, callback.from_user.id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR] and callback.from_user.id != SUPER_ADMIN_ID:
        await callback.answer("⛔ Bu amaldan faqat guruh adminlari foydalana oladi!", show_alert=True)
        return
    g = db_get_group(group_id)
    curr = g["opt_in_mode"] if g and "opt_in_mode" in g.keys() else "auto"
    new_val = "manual" if curr == "auto" else "auto"
    db_update_group_setting(group_id, "opt_in_mode", new_val)
    await callback.answer(f"✅ Guruh Opt-In rejimi '{new_val.upper()}' qilindi!", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=get_group_config_inline_keyboard(group_id))

@router.callback_query(F.data == "gcfg_realm_menu")
async def gcfg_realm_menu_cb(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("🌌 **Guruh uchun Multiverse Realm tanlang:**", reply_markup=get_group_realm_select_inline_keyboard(), parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data.startswith("gcfg_setrealm_"))
async def gcfg_setrealm_cb(callback: CallbackQuery):
    group_id = callback.message.chat.id
    member = await callback.bot.get_chat_member(group_id, callback.from_user.id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR] and callback.from_user.id != SUPER_ADMIN_ID:
        await callback.answer("⛔ Bu amaldan faqat guruh adminlari foydalana oladi!", show_alert=True)
        return
    realm_key = callback.data.replace("gcfg_setrealm_", "")
    db_update_group_setting(group_id, "active_universe", realm_key)
    db_update_group_setting(group_id, "roleplay_enabled", 1)
    await callback.answer(f"🎉 Guruh uchun Realm '{realm_key.upper()}' saqlandi!", show_alert=True)

@router.callback_query(F.data == "gcfg_time_menu")
async def gcfg_time_menu_cb(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("⏰ **Guruh uyg'onish vaqti oralig'ini tanlang:**", reply_markup=get_group_wizard_step3_kb(), parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data == "gcfg_refresh")
async def gcfg_refresh_cb(callback: CallbackQuery):
    group_id = callback.message.chat.id
    await callback.answer("🔄 Yangilandi!")
    await callback.message.edit_reply_markup(reply_markup=get_group_config_inline_keyboard(group_id))

@router.callback_query(F.data == "ggame_1v1_info")
async def ggame_1v1_info_cb(callback: CallbackQuery):
    await callback.answer()
    msg = (
        "⚔️ **GURUH 1v1 UYG'ONISH DUELI**\n\n"
        "Har qanday guruh a'zosiga duel e'lon qilishingiz mumkin! (-20 Stamina)\n"
        "Kim ertalab birinchi foto check-in qilsa, **100 tangalik bank** va **+75 Turnir Balli**ni yutadi!\n\n"
        "📌 **Boshlash uchun:** guruhda `/duel @username` yoki `/duel <user_id>` yozing!"
    )
    await callback.message.answer(msg, parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data == "ggame_duo_info")
async def ggame_duo_info_cb(callback: CallbackQuery):
    await callback.answer()
    msg = (
        "🤝 **GURUH DUO COMBO SHERIKLIK**\n\n"
        "Guruhdoshingiz bilan birgalikda uyg'onish va **+50 Bonus Tanga** hamda **+25 XP** olish uchun sherik biriktiring!\n\n"
        "📌 **Birlashish uchun:** guruhda `/duo <sherigingiz_user_id>` yuboring!"
    )
    await callback.message.answer(msg, parse_mode=ParseMode.MARKDOWN)

@router.message(Command("duo"))
async def cmd_set_duo_partner(message: Message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) != 2:
        await message.reply("ℹ️ **Foydalanish:** `/duo <sherik_user_id>`\n*Misol:* `/duo 6377617416`", parse_mode=ParseMode.MARKDOWN)
        return

    try:
        partner_id = int(args[1])
        db_set_duo_partner(user_id, partner_id)
        await message.reply(f"🤝 **Juftlik biriktirildi!** Endi `{user_id}` va `{partner_id}` har kuni birga uyg'onsa **+50 bonus tanga** oladi!", parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await message.reply("❌ Noto'g'ri user ID kiritildi.")

# --- SHOP & MARKET HANDLERS ---
@router.callback_query(F.data == "shop_menu")
@router.message(Command("shop"))
async def handle_shop_main(event):
    user_id = event.from_user.id
    user = db_get_user(user_id)
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])
    coins = user["coins"] if user else 0

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛡 Streak Freeze Olish (100 Coin)", callback_data="buy_freeze")]
    ])

    msg = t["shop_main"].format(coins=coins)
    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.answer(msg, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    else:
        await event.answer(msg, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data == "buy_freeze")
async def handle_buy_freeze_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    success = db_buy_streak_freeze(user_id)
    if success:
        await callback.answer("🎉 Muvaffaqiyatli!", show_alert=True)
        await callback.message.answer(t["shop_buy_freeze_ok"], parse_mode=ParseMode.MARKDOWN)
    else:
        user = db_get_user(user_id)
        coins = user["coins"] if user else 0
        await callback.answer(t["shop_no_coins"].format(coins=coins), show_alert=True)

# --- GROUP & USER TIME SETUP HANDLERS ---
@router.callback_query(F.data == "set_time_menu")
@router.message(Command("setup"))
async def cmd_setup(event):
    user_id = event.from_user.id
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    chat_type = event.message.chat.type if isinstance(event, CallbackQuery) else event.chat.type

    if chat_type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        member = await event.bot.get_chat_member(event.message.chat.id if isinstance(event, CallbackQuery) else event.chat.id, user_id)
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR] and user_id != SUPER_ADMIN_ID:
            msg = "⛔ Kechirasiz, bu buyruq faqat guruh adminlari uchun."
            if isinstance(event, CallbackQuery): await event.answer(msg, show_alert=True)
            else: await event.reply(msg)
            return

        kb = get_group_wizard_step3_kb()
        if isinstance(event, CallbackQuery):
            await event.answer()
            await event.message.answer(t["setup_group"], reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        else:
            await event.reply(t["setup_group"], reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    else:
        u = db_get_user(user_id)
        start_t = u["checkin_start"] if u and "checkin_start" in u.keys() else "04:30"
        end_t = u["checkin_end"] if u and "checkin_end" in u.keys() else "06:00"
        kb = get_solo_wizard_step2_kb()
        if isinstance(event, CallbackQuery):
            await event.answer()
            await event.message.answer(t["setup_user"].format(start=start_t, end=end_t), reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        else:
            await event.answer(t["setup_user"].format(start=start_t, end=end_t), reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

# --- PHOTO CHECK-IN & PILLOW VERIFICATION HANDLERS ---
@router.message(F.photo)
async def handle_user_photo(message: Message):
    user = message.from_user
    db_register_user(user.id, user.username, user.first_name)
    lang = get_user_language(user.id)
    t = TEXTS.get(lang, TEXTS["uz"])

    u = db_get_user(user.id)
    strictness = u["photo_strictness"] if u and "photo_strictness" in u.keys() and u["photo_strictness"] else "medium"

    group_id = message.chat.id if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] else 0
    if group_id != 0:
        db_link_group_member(group_id, user.id)
        g = db_get_group(group_id)
        start_t = g["checkin_start"] if g and "checkin_start" in g.keys() and g["checkin_start"] else "04:30"
        end_t = g["checkin_end"] if g and "checkin_end" in g.keys() and g["checkin_end"] else "06:00"
    else:
        start_t = u["checkin_start"] if u and "checkin_start" in u.keys() and u["checkin_start"] else "04:30"
        end_t = u["checkin_end"] if u and "checkin_end" in u.keys() and u["checkin_end"] else "06:00"

    if not is_time_in_window(start_t, end_t):
        await message.reply(t["not_in_window"].format(start=start_t, end=end_t), parse_mode=ParseMode.MARKDOWN)
        return

    photo_file = message.photo[-1]
    file_info = await message.bot.get_file(photo_file.file_id)
    photo_bytes_io = await message.bot.download_file(file_info.file_path)
    photo_bytes = photo_bytes_io.read()

    is_valid_img, _ = verify_image_quality(photo_bytes, strictness=strictness)
    if not is_valid_img:
        await message.reply(t["photo_too_dark"], parse_mode=ParseMode.MARKDOWN)
        return

    res = db_process_checkin(user.id, group_id=group_id, is_photo=True)

    if res == "already":
        await message.reply(t["already_checked_in"], parse_mode=ParseMode.MARKDOWN)
        return

    rank = get_user_rank(res["streak"], lang=lang)

    stamped_bytes = await stamp_photo_with_watermark(photo_bytes, user.first_name, res["streak"], rank)
    input_file = BufferedInputFile(stamped_bytes, filename="verified_stamp.jpg")

    quip = await fetch_dynamic_quip(res["streak"], user.first_name, lang=lang, roleplay_enabled=res["roleplay_enabled"], active_universe=res["active_universe"])
    caption_text = t["photo_success"].format(
        quip=quip,
        streak=res["streak"],
        goal=res["goal"],
        multiplier=res["multiplier"],
        coins_earned=res["coins_earned"],
        coins=res["coins"],
        xp_earned=res["xp_earned"],
        xp=res["xp"],
        level=res["level"],
        rank=rank
    )

    try:
        chosen_emoji = random.choice(["🔥", "⚡", "🦅", "🏆", "🎉", "💪", "👍"])
        await message.react(reaction=[ReactionTypeEmoji(emoji=chosen_emoji)])
    except Exception:
        pass

    share_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📲 Story'ga Joylash (Instagram/Telegram)", callback_data="story_share_tip")]
    ])

    await message.answer_photo(photo=input_file, caption=caption_text, reply_markup=share_keyboard, parse_mode=ParseMode.MARKDOWN)

    if res["streak"] >= 21:
        u_info = db_get_user(user.id)
        if u_info and ("cert_issued" not in u_info.keys() or u_info["cert_issued"] == 0):
            cert_bytes = await generate_21day_certificate(user.first_name)
            if cert_bytes:
                cert_file = BufferedInputFile(cert_bytes, filename="21day_certificate.jpg")
                cert_caption = t["cert_congrats"]
                await message.answer_photo(photo=cert_file, caption=cert_caption, parse_mode=ParseMode.MARKDOWN)
                db_set_cert_issued(user.id)

@router.callback_query(F.data == "story_share_tip")
async def handle_story_share_tip(callback: CallbackQuery):
    msg = (
        "📲 **STORY'GA JOYLASH VA DO'STLARNI HAYRATDA QOLDIRISH:**\n\n"
        "1. Yuqoridagi **VERIFIED STAMP** urilgan rasmni saqlab oling.\n"
        "2. Telegram yoki Instagram Story'ingizga joylang!\n"
        "3. Do'stlaringizga intizomingizni ko'rsating! 🚀"
    )
    await callback.answer()
    await callback.message.answer(msg, parse_mode=ParseMode.MARKDOWN)

# --- LANGUAGE SETUP ---
@router.callback_query(F.data == "lang_menu")
@router.message(Command("lang"))
async def cmd_language(event):
    lang = get_user_language(event.from_user.id)
    t = TEXTS.get(lang, TEXTS["uz"])
    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.answer(t["lang_select"], reply_markup=get_language_inline_keyboard(), parse_mode=ParseMode.MARKDOWN)
    else:
        await event.answer(t["lang_select"], reply_markup=get_language_inline_keyboard(), parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data.startswith("set_lang_"))
async def handle_set_language_callback(callback: CallbackQuery):
    selected_lang = callback.data.split("_")[2]
    user_id = callback.from_user.id
    db_register_user(user_id, callback.from_user.username, callback.from_user.first_name)
    db_update_user_lang(user_id, selected_lang)

    t = TEXTS.get(selected_lang, TEXTS["uz"])
    await callback.answer(t["lang_updated"], show_alert=False)
    await callback.message.answer(t["lang_updated"], reply_markup=get_main_reply_keyboard(user_id), parse_mode=ParseMode.MARKDOWN)

# --- SUPER ADMIN PANEL HANDLERS ---
@router.message(F.text.in_(["👑 Owner Admin Panel", "👑 Панель Владельца"]))
@router.message(Command("admin"))
async def cmd_admin_panel(message: Message):
    if message.from_user.id != SUPER_ADMIN_ID:
        await message.reply("⛔ Bu bo'lim faqat Katta Admin (Owner) uchun!")
        return

    users = db_get_all_users()
    groups = db_get_active_groups()

    admin_text = (
        f"👑 **KATTA ADMIN (OWNER) PANELI**\n\n"
        f"👤 ID: `{SUPER_ADMIN_ID}`\n"
        f"📊 **Boshqaruv va Statistika:**\n"
        f"👤 Jami foydalanuvchilar: `{len(users)} ta`\n"
        f"👥 Faol guruhlar: `{len(groups)} ta`\n\n"
        f"🛠 **Admin Buyruqlari:**\n"
        f"• `/broadcast <matn>` — Barcha foydalanuvchilarga xabar yuborish\n"
        f"• `/addcoins <user_id> <tanga>` — Tangalar qo'shish\n"
        f"• `/setstreak <user_id> <kun>` — Streak o'zgartirish\n"
    )
    await message.answer(admin_text, parse_mode=ParseMode.MARKDOWN)

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.reply("⚠️ **Foydalanish:** `/broadcast Sizning xabaringiz`", parse_mode=ParseMode.MARKDOWN)
        return

    users = db_get_all_users()
    success, fail = 0, 0
    for u in users:
        try:
            await message.bot.send_message(u["user_id"], f"📢 **ADMIN XABARI:**\n\n{text}", parse_mode=ParseMode.MARKDOWN)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail += 1

    await message.reply(f"✅ Xabar yuborildi!\nMuvaffaqiyatli: `{success}` | Muvaffaqiyatsiz: `{fail}`", parse_mode=ParseMode.MARKDOWN)

@router.message(Command("addcoins"))
async def cmd_add_coins(message: Message):
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    args = message.text.split()
    if len(args) != 3:
        await message.reply("⚠️ **Foydalanish:** `/addcoins <user_id> <tanga_soni>`", parse_mode=ParseMode.MARKDOWN)
        return
    try:
        target_id, amount = int(args[1]), int(args[2])
        db_update_user_coins(target_id, amount)
        await message.reply(f"✅ User `{target_id}` ga `+{amount}` tanga berildi!", parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await message.reply("❌ Noto'g'ri parametrlar kiritildi.")

@router.message(Command("setstreak"))
async def cmd_set_streak(message: Message):
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    args = message.text.split()
    if len(args) != 3:
        await message.reply("⚠️ **Foydalanish:** `/setstreak <user_id> <streak_kuni>`", parse_mode=ParseMode.MARKDOWN)
        return
    try:
        target_id, streak_days = int(args[1]), int(args[2])
        db_update_user_streak(target_id, streak_days)
        await message.reply(f"✅ User `{target_id}` ning streak kuni `{streak_days}` ga o'zgartirildi!", parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await message.reply("❌ Noto'g'ri parametrlar kiritildi.")


# ==================== SPIN & SQUAD TELEGRAM HANDLERS ====================
@router.callback_query(F.data == "spin_wheel")
@router.message(Command("spin"))
@router.message(Command("luck"))
@router.message(Command("wheel"))
async def handle_spin_command(event):
    user_id = event.from_user.id
    db_register_user(user_id, event.from_user.username, event.from_user.first_name)
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    res = db_process_spin(user_id)

    if res["status"] == "already":
        msg = t["spin_already"]
        if isinstance(event, CallbackQuery):
            await event.answer(msg, show_alert=True)
        else:
            await event.reply(msg, parse_mode=ParseMode.MARKDOWN)
    elif res["status"] == "ok":
        reward = res["reward"]
        msg = t["spin_success"].format(reward_label=reward["label"])
        if isinstance(event, CallbackQuery):
            await event.answer("🎰 Spin!", show_alert=False)
            await event.message.answer(msg, parse_mode=ParseMode.MARKDOWN)
        else:
            await event.reply(msg, parse_mode=ParseMode.MARKDOWN)
    else:
        err_msg = "❌ Error processing spin."
        if isinstance(event, CallbackQuery): await event.answer(err_msg, show_alert=True)
        else: await event.reply(err_msg)

@router.callback_query(F.data == "squad_info_cb")
@router.message(Command("squad"))
@router.message(Command("squad_info"))
async def handle_squad_info_cmd(event):
    user_id = event.from_user.id
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    sq = db_get_user_squad(user_id)
    if not sq:
        msg = t["squad_not_in"]
        if isinstance(event, CallbackQuery):
            await event.answer()
            await event.message.answer(msg, parse_mode=ParseMode.MARKDOWN)
        else:
            await event.reply(msg, parse_mode=ParseMode.MARKDOWN)
        return

    info = db_get_squad_info(sq["squad_id"])
    msg = t["squad_main"].format(
        name=info["squad"]["name"],
        tag=info["squad"]["tag"],
        squad_id=info["squad"]["squad_id"],
        leader_id=info["squad"]["leader_id"],
        member_count=info["member_count"],
        total_streak=info["total_streak"],
        total_xp=info["total_xp"]
    )
    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.answer(msg, parse_mode=ParseMode.MARKDOWN)
    else:
        await event.reply(msg, parse_mode=ParseMode.MARKDOWN)

@router.message(Command("squad_create"))
async def handle_squad_create_cmd(message: Message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])
    args = message.text.split(maxsplit=2)

    if len(args) < 3:
        await message.reply("ℹ️ **Foydalanish:** `/squad_create <squad_nomi> <TAG>`\n*Misol:* `/squad_create Lions 5AM`", parse_mode=ParseMode.MARKDOWN)
        return

    s_name, s_tag = args[1], args[2]
    ok, status, squad_id = db_create_squad(user_id, s_name, s_tag)
    if ok:
        await message.reply(t["squad_created"].format(name=s_name, tag=s_tag.upper(), squad_id=squad_id), parse_mode=ParseMode.MARKDOWN)
    elif status == "already_in_squad":
        await message.reply(t["squad_already"], parse_mode=ParseMode.MARKDOWN)
    elif status == "name_taken":
        await message.reply("❌ Bu klan nomi allaqachon band! Boshqa nom tanlang.", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply("❌ Noto'g'ri parametrlar kiritildi.", parse_mode=ParseMode.MARKDOWN)

@router.message(Command("squad_join"))
async def handle_squad_join_cmd(message: Message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])
    args = message.text.split()

    if len(args) < 2:
        await message.reply("ℹ️ **Foydalanish:** `/squad_join <squad_id>`\n*Misol:* `/squad_join 1`", parse_mode=ParseMode.MARKDOWN)
        return

    try:
        sq_id = int(args[1])
        ok, status = db_join_squad(user_id, sq_id)
        if ok:
            sq_info = db_get_squad_info(sq_id)
            name = sq_info["squad"]["name"] if sq_info else ""
            tag = sq_info["squad"]["tag"] if sq_info else ""
            await message.reply(t["squad_joined"].format(name=name, tag=tag), parse_mode=ParseMode.MARKDOWN)
        else:
            await message.reply(t["squad_not_found"], parse_mode=ParseMode.MARKDOWN)
    except ValueError:
        await message.reply("❌ Squad ID raqam bo'lishi kerak.")

@router.message(Command("squad_leaderboard"))
async def handle_squad_leaderboard_cmd(message: Message):
    lang = get_user_language(message.from_user.id)
    t = TEXTS.get(lang, TEXTS["uz"])

    top_squads = db_get_squad_leaderboard(10)
    text = t["squad_leaderboard_title"]

    if not top_squads:
        text += "🛡️ Hozircha klanlar yaratilmagan."
    else:
        for idx, sq in enumerate(top_squads, 1):
            medal = "👑 🥇" if idx == 1 else ("🥈" if idx == 2 else ("🥉" if idx == 3 else f"#{idx}"))
            text += f"`{medal}` **{html.escape(sq['name'])}** `[{sq['tag']}]` (ID: `{sq['squad_id']}`) — 🔥 `{sq['total_streak']}d` | 👥 `{sq['member_count']} a'zo` | 🌟 `{sq['total_xp']} XP`\n"

    await message.reply(text, parse_mode=ParseMode.MARKDOWN)

# --- PROFILE & LEADERBOARD & QUOTE & HELP HANDLERS ---
@router.message(Command("profile"))
@router.message(Command("myprofile"))
async def handle_my_profile(message: Message):
    user_id = message.from_user.id
    user = db_get_user(user_id)
    if not user:
        db_register_user(user_id, message.from_user.username, message.from_user.first_name)
        user = db_get_user(user_id)

    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    streak = user["streak"]
    coins = user["coins"]
    xp = user["xp"] if "xp" in user.keys() and user["xp"] else 0
    rpg = calculate_rpg_level(xp, lang=lang)
    stamina = db_calculate_and_update_stamina(dict(user))
    stamina_badge = "🟢 (Vitality Surge!)" if stamina >= 80 else "🟡 (Normal)"
    photo_count = user["photo_count"] if "photo_count" in user.keys() else 0
    freeze_count = user["freeze_count"] if "freeze_count" in user.keys() else 0
    ref_count = user["referral_count"] if "referral_count" in user.keys() else 0
    tourney_pts = db_get_user_tournament_points(user_id)
    rank = get_user_rank(streak, lang=lang)
    progress_bar = generate_progress_bar(streak, lang=lang)
    xp_bar = generate_xp_progress_bar(xp, lang=lang)
    lang_names = {"uz": "🇺🇿 O'zbekcha", "ru": "🇷🇺 Русский", "en": "🇬🇧 English"}
    start_t = user["checkin_start"] if "checkin_start" in user.keys() and user["checkin_start"] else "04:30"
    end_t = user["checkin_end"] if "checkin_end" in user.keys() and user["checkin_end"] else "06:00"
    goal_val = user["target_goal"] if "target_goal" in user.keys() and user["target_goal"] else 21
    rp_val = user["roleplay_enabled"] if "roleplay_enabled" in user.keys() else 0
    universe_val = user["active_universe"] if "active_universe" in user.keys() and user["active_universe"] else "marvel"
    universe_name = REALMS.get(universe_val, REALMS["marvel"])["name"]

    user_badges_list = db_get_user_badges(user_id, lang=lang)
    badges_str = " | ".join(user_badges_list) if user_badges_list else "Boshlang'ich nishonlar"

    profile_text = t["profile_title"].format(
        name=html.escape(user['first_name']),
        level=rpg["level"],
        level_title=rpg["title"],
        xp=xp,
        next_level_xp=rpg["next_level_total_xp"],
        progress_pct=rpg["progress_pct"],
        stamina=stamina,
        stamina_badge=stamina_badge,
        streak=streak,
        goal=goal_val,
        multiplier=get_streak_multiplier(streak),
        coins=coins,
        tourney_pts=tourney_pts,
        ref_count=ref_count,
        freeze_count=freeze_count,
        universe_name=universe_name,
        rp_status="YOQILGAN" if rp_val else "O'CHIRILGAN",
        rank=rank,
        start=start_t,
        end=end_t,
        badges=badges_str,
        lang_str=lang_names.get(lang, "🇺🇿 O'zbekcha"),
        xp_bar=xp_bar,
        progress_bar=progress_bar
    )
    await message.reply(profile_text, parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data == "arena_leaderboard")
@router.message(Command("leaderboard"))
async def handle_leaderboard(event):
    lang = get_user_language(event.from_user.id)
    t = TEXTS.get(lang, TEXTS["uz"])

    lb = db_get_global_leaderboard(10)
    if not lb:
        if isinstance(event, CallbackQuery): await event.answer(t["leaderboard_empty"])
        else: await event.reply(t["leaderboard_empty"])
        return

    text = t["leaderboard_title"]
    for idx, row in enumerate(lb, 1):
        r_title = get_user_rank(row['streak'], lang=lang)
        lvl = row['level'] if 'level' in row.keys() and row['level'] else 1
        text += f"`#{idx}` **{html.escape(row['first_name'])}** (Lvl {lvl}) — `{row['streak']}d` | `{row['coins']} coins` | {r_title}\n"
    
    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.answer(text, parse_mode=ParseMode.MARKDOWN)
    else:
        await event.reply(text, parse_mode=ParseMode.MARKDOWN)

@router.message(Command("quote"))
async def handle_quote(message: Message):
    user_id = message.from_user.id
    u = db_get_user(user_id)
    lang = get_user_language(user_id)
    active_universe = u["active_universe"] if u and u["roleplay_enabled"] else None
    t = TEXTS.get(lang, TEXTS["uz"])
    quote = await fetch_motivational_quote(user_id, lang=lang, active_universe=active_universe)
    await message.answer(t["quote_title"].format(quote=quote), parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data == "help_menu")
@router.message(Command("help"))
async def handle_help(event):
    lang = get_user_language(event.from_user.id)
    t = TEXTS.get(lang, TEXTS["uz"])
    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.answer(t["help_text"], parse_mode=ParseMode.MARKDOWN)
    else:
        await event.answer(t["help_text"], parse_mode=ParseMode.MARKDOWN)

# --- GROUP AUTO-CAPTURE & CHAT MEMBER EVENTS ---
@router.message(F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]))
async def handle_group_auto_capture(message: Message):
    if message.from_user and not message.from_user.is_bot:
        db_register_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        db_register_group(message.chat.id, message.chat.title)
        db_link_group_member(message.chat.id, message.from_user.id)

@router.chat_member()
async def handle_chat_member_updated(event: ChatMemberUpdated):
    if event.new_chat_member and not event.new_chat_member.user.is_bot:
        u = event.new_chat_member.user
        db_register_user(u.id, u.username, u.first_name)
        db_register_group(event.chat.id, event.chat.title)
        db_link_group_member(event.chat.id, u.id)

# ==================== SCHEDULER & BEDTIME PROTOCOL ====================
async def check_weekly_tournament_reset(bot: Bot):
    try:
        tz = pytz.timezone(TIMEZONE_STR)
        now = datetime.now(tz)
        season = db_get_or_create_active_season()
        end_dt = datetime.strptime(season["end_date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)

        if now >= end_dt:
            participants, _ = db_get_tournament_leaderboard(limit=3)
            with get_db() as conn:
                cursor = conn.cursor()
                w_id, w_name, w_pts = 0, "No Winner", 0
                w2_name, w3_name = "", ""
                if participants:
                    w1 = participants[0]
                    w_id = w1["user_id"]
                    w_name = f"[{html.escape(w1['first_name'])}](tg://user?id={w1['user_id']})"
                    w_pts = w1["points"]
                    cursor.execute("UPDATE users SET coins = coins + 500, freeze_count = freeze_count + 2 WHERE user_id = ?", (w_id,))
                    if len(participants) > 1:
                        w2 = participants[1]
                        w2_name = f"[{html.escape(w2['first_name'])}](tg://user?id={w2['user_id']})"
                        cursor.execute("UPDATE users SET coins = coins + 300, freeze_count = freeze_count + 1 WHERE user_id = ?", (w2["user_id"],))
                    if len(participants) > 2:
                        w3 = participants[2]
                        w3_name = f"[{html.escape(w3['first_name'])}](tg://user?id={w3['user_id']})"
                        cursor.execute("UPDATE users SET coins = coins + 150 WHERE user_id = ?", (w3["user_id"],))

                cursor.execute("""
                    UPDATE tournament_seasons
                    SET is_active = 0, winner_id = ?, winner_name = ?, winner_points = ?
                    WHERE season_id = ?
                """, (w_id, w_name, w_pts, season["season_id"]))

            groups = db_get_active_groups()
            broadcast_msg = (
                f"🏆 **HAFTALIK TOURNAMENT #{season['season_number']} G'OLIBLARI E'LON QILINDI!** 🏆\n\n"
                f"🥇 **1-o'rin (Chempion):** {w_name} (`{w_pts} pts`)\n"
                f"🎁 *Mukofot:* `+500 Tanga, 2x Streak Freeze & 👑 Haftalik Chempion Nishoni!`\n\n"
            )
            if w2_name:
                broadcast_msg += f"🥈 **2-o'rin:** {w2_name} — `+300 Tanga, 1x Streak Freeze`\n"
            if w3_name:
                broadcast_msg += f"🥉 **3-o'rin:** {w3_name} — `+150 Tanga`\n"

            broadcast_msg += (
                f"\n🚀 **Yangi #{season['season_number'] + 1}-mavsum boshlandi!**\n"
                f"Barcha ballar yangilandi. Tonggi intizom bellashuvi davom etadi! Har kuni 5 AM da g'alabaga erishing! 💪"
            )

            banner_bytes = generate_announcement_banner(f"TOURNAMENT #{season['season_number']} WINNERS", "Congratulations to our Champions!", "🏆", "gold")

            for g in groups:
                try:
                    await bot.send_photo(g["group_id"], photo=BufferedInputFile(banner_bytes, filename="tourney.png"), caption=broadcast_msg, parse_mode=ParseMode.MARKDOWN)
                    await asyncio.sleep(0.05)
                except Exception:
                    try:
                        await bot.send_message(g["group_id"], broadcast_msg, parse_mode=ParseMode.MARKDOWN)
                    except Exception:
                        pass

            db_get_or_create_active_season()
    except Exception as e:
        logging.error(f"Error checking weekly tournament reset: {e}")

async def scheduler_loop(bot: Bot):
    sent_start, sent_end, sent_bedtime = {}, {}, {}
    sent_bedtime_grp_msgs = {}
    while True:
        try:
            tz = pytz.timezone(TIMEZONE_STR)
            now = datetime.now(tz)
            today_str = now.strftime("%Y-%m-%d")
            hhmm = now.strftime("%H:%M")
            groups = db_get_active_groups()

            if not groups:
                db_register_group(DEFAULT_GROUP_ID, "5 AM Club Group")
                groups = db_get_active_groups()

            # 1. EVENING BEDTIME PROTOCOL AT 21:30 PM
            if hhmm == "21:30":
                if sent_bedtime.get(f"grp_bedtime_{today_str}") != True:
                    sent_bedtime[f"grp_bedtime_{today_str}"] = True
                    for g in groups:
                        try:
                            g_dict = dict(g)
                            g_lang = g_dict.get("lang") or "uz"
                            t_grp_bed = TEXTS.get(g_lang, TEXTS["uz"])
                            b_msg = await bot.send_message(
                                g["group_id"],
                                t_grp_bed["bedtime_reminder"],
                                reply_markup=get_bedtime_inline_keyboard(g_lang),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            sent_bedtime_grp_msgs[f"{g['group_id']}_{today_str}"] = b_msg.message_id
                            await asyncio.sleep(0.05)
                        except Exception:
                            pass

                users = db_get_all_users()
                for u in users:
                    uid = u["user_id"]
                    pm_on = u["pm_reminder_enabled"] if "pm_reminder_enabled" in u.keys() else 1
                    if sent_bedtime.get(f"usr_{uid}_{today_str}") != True and u["streak"] > 0 and pm_on == 1:
                        sent_bedtime[f"usr_{uid}_{today_str}"] = True
                        u_lang = u["lang"] if "lang" in u.keys() and u["lang"] else "uz"
                        t = TEXTS.get(u_lang, TEXTS["uz"])
                        try:
                            await bot.send_message(
                                uid,
                                t["bedtime_reminder"],
                                reply_markup=get_bedtime_inline_keyboard(u_lang),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            await asyncio.sleep(0.05)
                        except Exception:
                            pass

            # AUTO-DELETE BEDTIME MESSAGES AFTER WINDOW ENDS (23:00 PM)
            if hhmm == "23:00":
                for key, msg_id in list(sent_bedtime_grp_msgs.items()):
                    try:
                        g_id = int(key.split("_")[0])
                        await bot.delete_message(chat_id=g_id, message_id=msg_id)
                        del sent_bedtime_grp_msgs[key]
                    except Exception:
                        pass

            # 2. PM MORNING CHECK-IN REMINDERS
            all_users = db_get_all_users()
            for u in all_users:
                uid = u["user_id"]
                pm_on = u["pm_reminder_enabled"] if "pm_reminder_enabled" in u.keys() else 1
                s_t = u["checkin_start"] if "checkin_start" in u.keys() and u["checkin_start"] else "04:30"
                e_t = u["checkin_end"] if "checkin_end" in u.keys() and u["checkin_end"] else "06:00"
                u_lang = u["lang"] if "lang" in u.keys() and u["lang"] else "uz"

                if hhmm == s_t and pm_on == 1 and sent_start.get(f"pm_start_{uid}_{today_str}") != True:
                    sent_start[f"pm_start_{uid}_{today_str}"] = True
                    try:
                        msg_text = (
                            f"🌅 **THE 5 AM CLUB: UYG'ONISH VAQTI BO'LDI!**\n\n"
                            f"⏰ Uyg'onish oyna chegarasi: `{s_t}` — `{e_t}`\n"
                            f"⚡ Hozir check-in qiling yoki foto topshiriq yuboring!"
                        )
                        await bot.send_message(uid, msg_text, reply_markup=get_checkin_inline_keyboard(u_lang), parse_mode=ParseMode.MARKDOWN)
                        await asyncio.sleep(0.05)
                    except Exception:
                        pass

            # 3. MORNING CHECK-IN OPEN / CLOSE FOR GROUPS
            for g in groups:
                gid = g["group_id"]
                g_dict = dict(g)
                s_t, e_t = g_dict.get("checkin_start", "04:30"), g_dict.get("checkin_end", "06:00")
                g_lang = g_dict.get("lang") or "uz"
                t_grp = TEXTS.get(g_lang, TEXTS["uz"])
                realm = g_dict.get("active_universe", "standard") if g_dict.get("roleplay_enabled") else "standard"

                if hhmm == s_t and sent_start.get(f"{gid}_{today_str}") != True:
                    sent_start[f"{gid}_{today_str}"] = True
                    db_reset_group_snoozed(gid)

                    if g_lang == "uz":
                        open_msg = (
                            f"🌅 **THE 5 AM CLUB: TONGGI CHECK-IN OCHILDI!**\n\n"
                            f"⏰ **Uyg'onish vaqti:** `{s_t}` — `{e_t}`\n"
                            f"⚡ *“Ertalabki vaqtingizga egalik qiling. Hayotingizni yuksaltiring!”*\n\n"
                            f"👇 Uyg'ongan bo'lsangiz, quyidagi tugmani bosing:"
                        )
                    elif g_lang == "ru":
                        open_msg = (
                            f"🌅 **THE 5 AM CLUB: УТРЕННИЙ CHECK-IN ОТКРЫТ!**\n\n"
                            f"⏰ **Время подъема:** `{s_t}` — `{e_t}`\n"
                            f"⚡ *«Владейте своим утром. Поднимите свою жизнь!»*\n\n"
                            f"👇 Если вы проснулись, нажмите кнопку ниже:"
                        )
                    else:
                        open_msg = (
                            f"🌅 **THE 5 AM CLUB: MORNING CHECK-IN IS OPEN!**\n\n"
                            f"⏰ **Wake-up Window:** `{s_t}` — `{e_t}`\n"
                            f"⚡ *“Own your morning. Elevate your life.”*\n\n"
                            f"👇 If you are awake, tap the button below:"
                        )

                    try:
                        banner = generate_announcement_banner("5 AM CLUB CHECK-IN OPEN", f"Window: {s_t} - {e_t}", "🌅", realm)
                        await bot.send_photo(gid, photo=BufferedInputFile(banner, filename="checkin.png"), caption=open_msg, reply_markup=get_checkin_inline_keyboard(g_lang), parse_mode=ParseMode.MARKDOWN)
                    except Exception:
                        await bot.send_message(gid, open_msg, reply_markup=get_checkin_inline_keyboard(g_lang), parse_mode=ParseMode.MARKDOWN)

                if hhmm == e_t and sent_end.get(f"{gid}_{today_str}") != True:
                    sent_end[f"{gid}_{today_str}"] = True
                    report = db_get_group_attendance_report(gid)
                    awake, sleepers = [], []
                    for m in report:
                        raw_first_name = m.get('first_name') or 'Member'
                        first_name = html.escape(raw_first_name).replace("[", "").replace("]", "").replace("*", "").replace("_", "").replace("`", "")
                        user_id = m['user_id']
                        username = m.get('username')
                        if username:
                            mention = f"[{first_name}](https://t.me/{username})"
                        else:
                            mention = f"[{first_name}](tg://user?id={user_id})"

                        if m["status"] == "awake":
                            awake.append(f"• {mention} (`{m['last_checkin_time']}`) — 🔥 `{m['streak']}d`")
                        else:
                            sleepers.append(f"• {mention} 😴")

                    quote = await fetch_motivational_quote(0, g_lang, realm)
                    awake_title = t_grp.get("grp_awake_title", "🌅 AWAKE MEMBERS:")
                    graveyard_title = t_grp.get("grp_graveyard_title", "😴 GRAVEYARD OF SLEEPERS:")

                    if g_lang == "uz":
                        rep_msg = (
                            f"🔒 **THE 5 AM CLUB: CHECK-IN YOPILDI ({e_t})**\n\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"{awake_title}\n" + ("\n".join(awake) if awake else "• *Hech kim uyg'onmadi* 😞") + "\n\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"{graveyard_title}\n" + ("\n".join(sleepers) if sleepers else "• *Hamma vaqtida uyg'ondi!* 🎉") + "\n\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"💡 **KUN HIKMATI:**\n{quote}"
                        )
                    elif g_lang == "ru":
                        rep_msg = (
                            f"🔒 **THE 5 AM CLUB: CHECK-IN ЗАКРЫТ ({e_t})**\n\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"{awake_title}\n" + ("\n".join(awake) if awake else "• *Никто не проснулся* 😞") + "\n\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"{graveyard_title}\n" + ("\n".join(sleepers) if sleepers else "• *Все проснулись вовремя!* 🎉") + "\n\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"💡 **МУДРОСТЬ ДНЯ:**\n{quote}"
                        )
                    else:
                        rep_msg = (
                            f"🔒 **THE 5 AM CLUB: CHECK-IN CLOSED ({e_t})**\n\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"{awake_title}\n" + ("\n".join(awake) if awake else "• *No one checked in* 😞") + "\n\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"{graveyard_title}\n" + ("\n".join(sleepers) if sleepers else "• *Everyone is awake!* 🎉") + "\n\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"💡 **QUOTE OF THE DAY:**\n{quote}"
                        )
                    await bot.send_message(gid, rep_msg, parse_mode=ParseMode.MARKDOWN)

            # 4. SATURDAY WEEKLY INTERACTIVE EVENT & MULTIVERSE REALM ROTATION
            if now.weekday() == 5 and hhmm == "10:00":
                if sent_start.get(f"saturday_evt_{today_str}") != True:
                    sent_start[f"saturday_evt_{today_str}"] = True
                    realms_list = list(REALMS.keys())
                    for u in all_users:
                        u_dict = dict(u)
                        if u_dict.get("roleplay_enabled") == 1:
                            new_realm = random.choice(realms_list)
                            db_update_user_setting(u["user_id"], "active_universe", new_realm)
                            try:
                                await bot.send_message(
                                    u["user_id"],
                                    f"🌌 **SHANBA MULTIVERSE ROTATSASI!**\n\n"
                                    f"Sizning koinotingiz haftalik avto-rotatsiyadan o'tdi va **{REALMS[new_realm]['name']}** koinotiga o'tkazildi! 🚀",
                                    parse_mode=ParseMode.MARKDOWN
                                )
                            except Exception:
                                pass

            # 5. WEEKLY TOURNAMENT RESET CHECK
            await check_weekly_tournament_reset(bot)

        except Exception as e:
            logging.error(f"Scheduler error: {e}")
        await asyncio.sleep(25)

# ==================== RENDER WEBAPP SERVER & HMAC AUTH REST API ====================
async def serve_index(req):
    if os.path.exists("index.html"):
        return web.FileResponse("index.html")
    return web.Response(text="The 5 AM Club WebApp is loading...")

async def serve_styles(req):
    if os.path.exists("styles.css"):
        return web.FileResponse("styles.css")
    return web.Response(text="/* styles */", content_type="text/css")

async def serve_app_js(req):
    if os.path.exists("app.js"):
        return web.FileResponse("app.js")
    return web.Response(text="// app.js", content_type="application/javascript")

async def web_ping(req):
    return web.Response(text="Bot is active 24/7!", content_type="text/plain")

async def api_auth_validate(req):
    try:
        body = await req.json()
        init_data = body.get("initData", "")
        valid, auth_result = verify_telegram_init_data(init_data)

        if valid and auth_result:
            user_data = auth_result.get("user", {})
            user_id = user_data.get("id")
            if user_id:
                db_user = db_get_user(user_id)
                if not db_user:
                    db_register_user(user_id, user_data.get("username", ""), user_data.get("first_name", ""))

                if "active_universe" in body:
                    db_update_user_setting(user_id, "active_universe", body["active_universe"])
                if "roleplay_enabled" in body:
                    db_update_user_setting(user_id, "roleplay_enabled", 1 if body["roleplay_enabled"] else 0)
                if "interactive_enabled" in body:
                    db_update_user_setting(user_id, "interactive_enabled", 1 if body["interactive_enabled"] else 0)
                if "target_goal" in body:
                    db_update_user_setting(user_id, "target_goal", int(body["target_goal"]))

                db_user = db_get_user(user_id)
                db_user_dict = dict(db_user)
                stamina = db_calculate_and_update_stamina(db_user_dict)
                xp = db_user_dict.get("xp") or 0
                rpg = calculate_rpg_level(xp, db_user_dict.get("lang") or "uz")
                tourney_pts = db_get_user_tournament_points(user_id)

                return web.json_response({
                    "status": "ok",
                    "verified": True,
                    "user": {
                        "id": db_user_dict["user_id"],
                        "name": db_user_dict["first_name"],
                        "username": db_user_dict["username"],
                        "streak": db_user_dict["streak"],
                        "coins": db_user_dict["coins"],
                        "xp": xp,
                        "level": rpg["level"],
                        "level_title": rpg["title"],
                        "xp_in_level": rpg["xp_in_level"],
                        "xp_needed_level": rpg["xp_needed_level"],
                        "next_level_total_xp": rpg["next_level_total_xp"],
                        "progress_pct": rpg["progress_pct"],
                        "stamina": stamina,
                        "max_stamina": 100,
                        "tournament_points": tourney_pts,
                        "photo_count": db_user_dict["photo_count"],
                        "freeze_count": db_user_dict["freeze_count"],
                        "ref_count": db_user_dict["referral_count"],
                        "lang": db_user_dict["lang"],
                        "checkin_start": db_user_dict["checkin_start"],
                        "checkin_end": db_user_dict["checkin_end"],
                        "target_goal": db_user_dict.get("target_goal", 21),
                        "roleplay_enabled": db_user_dict.get("roleplay_enabled", 0),
                        "active_universe": db_user_dict.get("active_universe", "marvel"),
                        "interactive_enabled": db_user_dict.get("interactive_enabled", 1),
                        "pm_reminder_enabled": db_user_dict.get("pm_reminder_enabled", 1),
                        "photo_strictness": db_user_dict.get("photo_strictness", "medium")
                    }
                })
    except Exception as e:
        logging.error(f"API Auth validate error: {e}")
    return web.json_response({"status": "error", "verified": False, "message": "Invalid initData signature"}, status=401)

async def api_user_stats(req):
    user_id_str = req.match_info.get("user_id", "")
    try:
        user_id = int(user_id_str)
        user = db_get_user(user_id)
        if user:
            user_dict = dict(user)
            stamina = db_calculate_and_update_stamina(user_dict)
            xp = user_dict.get("xp") or 0
            rpg = calculate_rpg_level(xp, user_dict.get("lang") or "uz")
            tourney_pts = db_get_user_tournament_points(user_id)

            return web.json_response({
                "status": "ok",
                "user": {
                    "id": user_dict["user_id"],
                    "name": user_dict["first_name"],
                    "username": user_dict["username"],
                    "streak": user_dict["streak"],
                    "coins": user_dict["coins"],
                    "xp": xp,
                    "level": rpg["level"],
                    "level_title": rpg["title"],
                    "xp_in_level": rpg["xp_in_level"],
                    "xp_needed_level": rpg["xp_needed_level"],
                    "progress_pct": rpg["progress_pct"],
                    "stamina": stamina,
                    "max_stamina": 100,
                    "tournament_points": tourney_pts,
                    "photo_count": user_dict["photo_count"],
                    "freeze_count": user_dict["freeze_count"],
                    "ref_count": user_dict["referral_count"],
                    "lang": user_dict["lang"],
                    "target_goal": user_dict.get("target_goal", 21),
                    "roleplay_enabled": user_dict.get("roleplay_enabled", 0),
                    "active_universe": user_dict.get("active_universe", "marvel"),
                    "interactive_enabled": user_dict.get("interactive_enabled", 1),
                    "pm_reminder_enabled": user_dict.get("pm_reminder_enabled", 1),
                    "photo_strictness": user_dict.get("photo_strictness", "medium")
                }
            })
    except Exception as e:
        logging.error(f"API user error: {e}")
    return web.json_response({"status": "error", "message": "User not found"}, status=404)

async def api_action_bedtime(req):
    try:
        body = await req.json()
        init_data = body.get("initData", "")
        valid, auth_result = verify_telegram_init_data(init_data)
        if not valid or not auth_result:
            return web.json_response({"status": "error", "message": "Unauthorized"}, status=401)

        user_id = auth_result.get("user", {}).get("id")

        # Check bedtime time window (21:00 - 04:00)
        if not is_time_in_window("21:00", "04:00"):
            return web.json_response({
                "status": "not_in_window",
                "message": "Hozir uyqu vaqti emas! Uyqu protokoli soat 21:00 - 23:00 oralig'ida ochiladi 🌙"
            }, status=400)

        success, reason = db_record_bedtime(user_id)
        if success:
            user = db_get_user(user_id)
            user_dict = dict(user)
            rpg = calculate_rpg_level(user_dict["xp"] or 0, user_dict["lang"] or "uz")
            return web.json_response({
                "status": "ok",
                "message": "Bedtime protocol recorded (+20 XP, 100% Stamina)",
                "xp": user_dict["xp"],
                "level": rpg["level"],
                "stamina": 100
            })
        else:
            return web.json_response({"status": "already", "message": "Already recorded bedtime today"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def api_tournament(req):
    try:
        participants, season = db_get_tournament_leaderboard(20)
        data = [{
            "rank": idx + 1,
            "name": r["first_name"],
            "username": r["username"],
            "points": r["points"],
            "checkins": r["checkins_count"],
            "photos": r["photos_count"]
        } for idx, r in enumerate(participants)]

        return web.json_response({
            "status": "ok",
            "season": {
                "number": season["season_number"],
                "start_date": season["start_date"],
                "end_date": season["end_date"]
            },
            "leaderboard": data
        })
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def api_leaderboard(req):
    try:
        lb = db_get_global_leaderboard(10)
        data = [{
            "name": r["first_name"],
            "username": r["username"],
            "streak": r["streak"],
            "coins": r["coins"],
            "level": r["level"] if "level" in r.keys() and r["level"] else 1,
            "xp": r["xp"] if "xp" in r.keys() and r["xp"] else 0
        } for r in lb]
        return web.json_response({"status": "ok", "leaderboard": data})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def api_action_spin(req):
    try:
        body = await req.json()
        init_data = body.get("initData", "")
        valid, auth_result = verify_telegram_init_data(init_data)
        if not valid or not auth_result:
            return web.json_response({"status": "error", "message": "Unauthorized"}, status=401)

        user_id = auth_result.get("user", {}).get("id")
        res = db_process_spin(user_id)
        if res["status"] == "already":
            return web.json_response({"status": "already", "message": "Already spun today"})
        elif res["status"] == "ok":
            return web.json_response({
                "status": "ok",
                "reward": res["reward"],
                "user": {
                    "coins": res["coins"],
                    "xp": res["xp"],
                    "level": res["level"],
                    "freeze_count": res["freeze_count"]
                }
            })
        else:
            return web.json_response({"status": "error", "message": res.get("message", "Spin failed")}, status=400)
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def api_squads(req):
    try:
        top_squads = db_get_squad_leaderboard(20)
        data = [{
            "rank": idx + 1,
            "squad_id": sq["squad_id"],
            "name": sq["name"],
            "tag": sq["tag"],
            "leader_id": sq["leader_id"],
            "member_count": sq["member_count"],
            "total_streak": sq["total_streak"],
            "total_xp": sq["total_xp"]
        } for idx, sq in enumerate(top_squads)]

        return web.json_response({"status": "ok", "squads": data})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def api_action_squad_join(req):
    try:
        body = await req.json()
        init_data = body.get("initData", "")
        valid, auth_result = verify_telegram_init_data(init_data)
        if not valid or not auth_result:
            return web.json_response({"status": "error", "message": "Unauthorized"}, status=401)

        user_id = auth_result.get("user", {}).get("id")
        squad_id = body.get("squad_id")
        if not squad_id:
            return web.json_response({"status": "error", "message": "squad_id is required"}, status=400)

        ok, status = db_join_squad(user_id, int(squad_id))
        if ok:
            return web.json_response({"status": "ok", "message": "Joined squad successfully", "squad_id": int(squad_id)})
        else:
            return web.json_response({"status": "error", "message": "Squad not found"}, status=404)
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def api_action_checkin(req):
    try:
        body = await req.json()
        init_data = body.get("initData", "")
        valid, auth_result = verify_telegram_init_data(init_data)
        if not valid or not auth_result:
            return web.json_response({"status": "error", "message": "Unauthorized"}, status=401)

        user_id = auth_result.get("user", {}).get("id")
        user = db_get_user(user_id)
        if not user:
            return web.json_response({"status": "error", "message": "User not found"}, status=404)

        start_t = user["checkin_start"] if "checkin_start" in user.keys() and user["checkin_start"] else "04:30"
        end_t = user["checkin_end"] if "checkin_end" in user.keys() and user["checkin_end"] else "06:00"

        if not is_time_in_window(start_t, end_t):
            return web.json_response({
                "status": "not_in_window",
                "message": f"Hozir check-in vaqti emas! Uyg'onish vaqti: {start_t} - {end_t}"
            }, status=400)

        res = db_process_checkin(user_id, group_id=0, is_photo=False)
        if res == "already":
            return web.json_response({"status": "already", "message": "Siz bugun allaqachon check-in qildingiz!"})
        elif res:
            return web.json_response({
                "status": "ok",
                "user": {
                    "streak": res["streak"],
                    "coins": res["coins"],
                    "xp": res["xp"],
                    "level": res["level"],
                    "multiplier": res["multiplier"],
                    "coins_earned": res["coins_earned"],
                    "xp_earned": res["xp_earned"]
                }
            })
        else:
            return web.json_response({"status": "error", "message": "Check-in failed"}, status=400)
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def start_dummy_web_server():
    app = web.Application()
    app.router.add_get('/', serve_index)
    app.router.add_get('/index.html', serve_index)
    app.router.add_get('/styles.css', serve_styles)
    app.router.add_get('/app.js', serve_app_js)
    app.router.add_get('/health', web_ping)
    app.router.add_post('/api/auth/validate', api_auth_validate)
    app.router.add_post('/api/action/checkin', api_action_checkin)
    app.router.add_post('/api/action/bedtime', api_action_bedtime)
    app.router.add_get('/api/user/{user_id}', api_user_stats)
    app.router.add_get('/api/tournament', api_tournament)
    app.router.add_get('/api/leaderboard', api_leaderboard)
    app.router.add_post('/api/action/spin', api_action_spin)
    app.router.add_get('/api/squads', api_squads)
    app.router.add_post('/api/action/squad/join', api_action_squad_join)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000)))
    await site.start()

# ==================== MAIN ENTRY POINT ====================
async def set_bot_commands(bot: Bot):
    group_commands = [
        BotCommand(command="gconfig", description="⚙️ Guruh Sozlamalari & Multiverse Katalogi"),
        BotCommand(command="games", description="🎮 Interaktiv O'yinlar (1v1 Duellar & Duo)"),
        BotCommand(command="setup", description="🛠️ Guruhni O'rnatish Wizard (Admin)"),
        BotCommand(command="tournament", description="🏆 Haftalik Turnir & Reyting"),
        BotCommand(command="profile", description="📊 Shaxsiy va Guruh Stats"),
        BotCommand(command="help", description="📖 Guruh Qo'llanmasi"),
    ]
    private_commands = [
        BotCommand(command="start", description="🚀 Botni boshlash / Wizard"),
        BotCommand(command="solo", description="🌅 Solo check-in catalog hub"),
        BotCommand(command="roleplay", description="🎭 Multiverse roleplay hub"),
        BotCommand(command="arena", description="🎮 Interaktiv arena hub"),
        BotCommand(command="tournament", description="⚔️ Haftalik turnir reytingi"),
        BotCommand(command="bedtime", description="🌙 21:30 Uxlash protokoli (+20 XP)"),
        BotCommand(command="profile", description="📊 Profilim va RPG stats"),
        BotCommand(command="leaderboard", description="🏆 Reyting jadvali"),
        BotCommand(command="shop", description="🛒 Do'kon va bozor"),
        BotCommand(command="setup", description="⚙️ Uyg'onish vaqtini sozlash"),
        BotCommand(command="ref", description="👥 Do'stlarni taklif qilish"),
        BotCommand(command="duo", description="🤝 Sherik biriktirish"),
        BotCommand(command="spin", description="🎰 Omad g'ildiragini aylantirish"),
        BotCommand(command="squad", description="🛡️ Klan / Squad ma'lumotlari"),
        BotCommand(command="squad_create", description="🛡️ Yangi klan yaratish (/squad_create <nom> <tag>)"),
        BotCommand(command="squad_join", description="🛡️ Klanga qo'shilish (/squad_join <squad_id>)"),
        BotCommand(command="squad_leaderboard", description="🛡️ Klanlar reyting jadvali"),
        BotCommand(command="lang", description="🌐 Tilni tanlash / Language"),
        BotCommand(command="help", description="📖 Bot qoidalari"),
    ]
    try:
        await bot.set_my_commands(group_commands, scope=BotCommandScopeAllGroupChats())
        await bot.set_my_commands(private_commands, scope=BotCommandScopeAllPrivateChats())
        await bot.set_my_commands(private_commands)
    except Exception as e:
        logging.error(f"Failed to set bot commands: {e}")

async def main():
    init_sqlite_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await set_bot_commands(bot)
    await start_dummy_web_server()
    asyncio.create_task(scheduler_loop(bot))

    await bot.delete_webhook(drop_pending_updates=True)
    while True:
        try:
            await dp.start_polling(bot)
            break
        except TelegramConflictError:
            logging.warning("Telegram conflict detected (another instance running). Waiting 5 seconds before retrying...")
            await asyncio.sleep(5)
        except Exception as e:
            if "Conflict" in str(e):
                logging.warning("Telegram conflict detected. Waiting 5 seconds before retrying...")
                await asyncio.sleep(5)
            else:
                logging.error(f"Polling error: {e}")
                await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())
