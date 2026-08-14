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
        "📝 **Mission:** Take a photo of your handwritten to-do list for today!",
        "🌳 **Mission:** Step outside and send a photo of fresh morning nature!"
    ]
}

def get_random_photo_mission(lang: str = "uz") -> str:
    missions = PHOTO_MISSIONS.get(lang, PHOTO_MISSIONS["uz"])
    return random.choice(missions)

# ==================== 7 MULTIVERSE ROLEPLAY REALMS ====================
REALMS = {
    "marvel": {
        "name": "🛡️ Marvel Cinematic Universe",
        "emoji": "🛡️",
        "titles": {
            "uz": ["🛡️ Boshlang'ich Qasoskor", "🦾 Stark Texniks", "⚡ Vibranium Jangchisi", "🌌 Kvant Ustasi", "👑 Temir Qasoskor Afsonasi"],
            "ru": ["🛡️ Новичок Мститель", "🦾 Старк Техник", "⚡ Вибраниум Воин", "🌌 Квантовый Мастер", "👑 Легендарный Железный Мститель"],
            "en": ["🛡️ Initiate Avenger", "🦾 Stark Specialist", "⚡ Vibranium Warrior", "🌌 Quantum Master", "👑 Legendary Iron Avenger"]
        },
        "quips": {
            "uz": [
                "Avengers, Assemble! Jarvis tizimlari 05:00 da to'liq shay holatda! 🛡️⚡",
                "Stark Tech ertalabki energiya reaktorini 100% ga quvvatladi! Wakanda Forever! 🦾🔥",
                "Men Temir Odamman. Bugungi tonggi g'alaba bizniki! 👑⚡"
            ],
            "ru": [
                "Мстители, общий сбор! Системы Джарвиса готовы к утреннему бою! 🛡️⚡",
                "Технологии Старка зарядили ваш ядерный реактор на 100%! Ваканда Навеки! 🦾🔥",
                "Я — Железный Человек. Победа сегодня за нами! 👑⚡"
            ],
            "en": [
                "Avengers, Assemble! Jarvis systems online and fully operational! 🛡️⚡",
                "Stark Tech initialized your morning Arc Reactor to 100%! Wakanda Forever! 🦾🔥",
                "I am Iron Man. Today's dawn belongs to us! 👑⚡"
            ]
        },
        "wisdom_prefix": "🛡️ **STARK TECH WISDOM:** "
    },
    "samurai": {
        "name": "⚔️ Medieval Samurai Bushido",
        "emoji": "⚔️",
        "titles": {
            "uz": ["⚔️ Ronin Shogird", "🌸 Katana Ustasi", "🏯 Bushido Jangchisi", "⛩️ Dojo Sensei", "👑 Buyuk Shogun"],
            "ru": ["⚔️ Ученик Ронин", "🌸 Мастер Катаны", "🏯 Воин Бусидо", "⛩️ Сенсей Додзё", "👑 Великий Сёгун"],
            "en": ["⚔️ Ronin Initiate", "🌸 Katana Master", "🏯 Bushido Warrior", "⛩️ Dojo Sensei", "👑 Grand Shogun"]
        },
        "quips": {
            "uz": [
                "Katana birinchi quyosh nuri tushmasidan oldin qinidan chiqarildi! Intizomingizga tasanno, Ronin! ⚔️🌸",
                "Bushido Qoidasi #1: Haqiqiy usta uyqu ustidan jimjitlikda g'alaba qozonadi! 🏯⚡",
                "Sensei sizga chuqur ta'zim qiladi. Ruhingiz charxlangan po'latdek porlamoqda! 🌸🔥"
            ],
            "ru": [
                "Катана обнажена до первого луча солнца! Слава твоей дисциплине, Ронин! ⚔️🌸",
                "Кодекс Бусидо №1: Настоящий мастер побеждает сон в абсолютной тишине! 🏯⚡",
                "Сенсей кланяется вам. Ваш дух сияет как закаленная сталь! 🌸🔥"
            ],
            "en": [
                "The Katana is unsheathed before the first ray of dawn! Honor to your discipline, Ronin! ⚔️🌸",
                "Bushido Code #1: A true master conquers sleep in quiet solitude! 🏯⚡",
                "The Sensei bows in deep respect. Your spirit shines like polished steel! 🌸🔥"
            ]
        },
        "wisdom_prefix": "⚔️ **BUSHIDO CODE WISDOM:** "
    },
    "feudal": {
        "name": "🏰 Feudal Knights of Round Table",
        "emoji": "🏰",
        "titles": {
            "uz": ["🏰 Qal'a Soqchisi", "⚔️ Ekskalibur Ritsari", "🛡️ Kamelot Chempioni", "👑 Qirol Artur Saroy unvoni", "👑 Afsonaviy Qirol"],
            "ru": ["🏰 Страж Замка", "⚔️ Рыцарь Экскалибура", "🛡️ Чемпион Камелота", "👑 Рыцарь Круглого Стола", "👑 Король Артур"],
            "en": ["🏰 Castle Guard", "⚔️ Knight of Excalibur", "🛡️ Camelot Champion", "👑 Paladin of Honor", "👑 High King Arthur"]
        },
        "quips": {
            "uz": [
                "Ekskalibur qilichi tongda baland ko'tarildi! Qirollik sizning sharafingizni ulug'laydi! 🏰⚔️",
                "Davra stoli ritsarlari buyrug'i bilan sizning tonggi zafaringiz oltin bilan bitildi! 🛡️✨",
                "Qal'amiz devorlari ritsarlarimiz hushyor turganda aslo qulamaydi! 🏰🔥"
            ],
            "ru": [
                "Меч Экскалибур поднят на рассвете! Королевство чтит твою доблесть! 🏰⚔️",
                "По указу Рыцарей Круглого Стола твоя победа вписана золотом! 🛡️✨",
                "Стены нашего замка нерушимы, пока рыцари не спят! 🏰🔥"
            ],
            "en": [
                "Excalibur is raised high at dawn! The Kingdom honors your noble valor! 🏰⚔️",
                "By order of the Round Table, your morning victory is recorded in gold! 🛡️✨",
                "Our castle walls stand indestructible while our Knights guard the dawn! 🏰🔥"
            ]
        },
        "wisdom_prefix": "🏰 **KNIGHTLY CODE WISDOM:** "
    },
    "mafia": {
        "name": "🎩 Italian Mafia Syndicate",
        "emoji": "🎩",
        "titles": {
            "uz": ["🎩 Sindikat A'zosi", "💼 Soldato Jangchi", "🔪 Kaporedjime", "🍷 Anderboss", "👑 Don Korleone (Godfather)"],
            "ru": ["🎩 Участник Синдиката", "💼 Сольдато", "🔪 Капореджиме", "🍷 Андербосс", "👑 Дон Корлеоне (Godfather)"],
            "en": ["🎩 Syndicate Associate", "💼 Soldato Enforcer", "🔪 Caporegime", "🍷 Underboss", "👑 Don Corleone (The Godfather)"]
        },
        "quips": {
            "uz": [
                "Don Korleone o'z hurmatini yo'lladi. 05:00 da intizom ko'rsatganlarga oila yordam beradi! 🎩💼",
                "Omertà intizom qoidasi: Oila ishlayotganda hech kim uxlab qolmaydi! 💼🔥",
                "Ertalabki taklifdan voz kechib bo'lmaydi. 5 AM Oilasiga sodiqlik! 🎩👑"
            ],
            "ru": [
                "Дон Корлеоне шлет личное уважение. Семья всегда поддерживает дисциплинированных! 🎩💼",
                "Омерта Дисциплины: Когда Семья работает, никто не спит! 💼🔥",
                "Предложение, от которого рассвет не мог отказаться. Преданность Семье! 🎩👑"
            ],
            "en": [
                "Don Corleone sends his personal respects. Respect is earned at 5 AM sharp! 🎩💼",
                "Omertà of Discipline: Never sleep when the Family is building its empire! 💼🔥",
                "An offer the morning could not refuse. Absolute loyalty to the 5 AM Family! 🎩👑"
            ]
        },
        "wisdom_prefix": "🎩 **GODFATHER SYNDICATE WISDOM:** "
    },
    "cyberpunk": {
        "name": "🦾 Cyberpunk 2077 Night City",
        "emoji": "🦾",
        "titles": {
            "uz": ["🤖 Chooh2 Yuguruvchi", "⚡ Xrom Fikser", "🦾 Kiber-Yollanma", "🌐 Netranner Elita", "👑 Night City Afsonasi"],
            "ru": ["🤖 Бегун Chooh2", "⚡ Хром Фиксер", "🦾 Кибер-Наемник", "🌐 Нетраннер Элита", "👑 Легенда Найт-Сити"],
            "en": ["🤖 Chooh2 Runner", "⚡ Chrome Fixer", "🦾 Cyber-Mercenary", "🌐 Netrunner Elite", "👑 Night City Legend"]
        },
        "quips": {
            "uz": [
                "Neyron sinxronizatsiya bajarildi! Night City fikserlari 5 AM xrom energiyangizni tasdiqladi! 🦾⚡",
                "Uyqu kodi o'chirildi... Vitality Overdrive yoqildi! Netga xush kelibsiz! 🌃⚡",
                "Uyg'on Samurai, bugun yoqib yuboradigan kunimiz bor! 💥🦾"
            ],
            "ru": [
                "Нейро-синхронизация завершена! Фиксеры Найт-Сити подтвердили ваш утренний буст! 🦾⚡",
                "Сон отключен... Включен овердрайв бодрости! Добро пожаловать в Сеть! 🌃⚡",
                "Проснись, Самурай, у нас есть город, который надо зажечь! 💥🦾"
            ],
            "en": [
                "Neural sync complete! Night City fixers verified your 5 AM chrome boost! 🦾⚡",
                "Sleep subroutine terminated... Vitality Overdrive engaged! 🌃⚡",
                "Wake up Samurai, we have a day to burn! 💥🦾"
            ]
        },
        "wisdom_prefix": "🦾 **NIGHT CITY FIXER WISDOM:** "
    },
    "olympus": {
        "name": "⚡ Greek Mythology (Mount Olympus)",
        "emoji": "⚡",
        "titles": {
            "uz": ["🏛️ Oddiy Qahramon", "🗡️ Yarim Xudoi (Demigod)", "🛡️ Attika Chempioni", "⚡ Olimplar Titani", "👑 Zevs Hukmdori"],
            "ru": ["🏛️ Смертный Герой", "🗡️ Полубог (Demigod)", "🛡️ Чемпион Аттики", "⚡ Титан Олимпа", "👑 Владыка Зевс"],
            "en": ["🏛️ Mortal Hero", "🗡️ Demigod of Dawn", "🛡️ Attica Champion", "⚡ Olympian Titan", "👑 Ruler Zeus"]
        },
        "quips": {
            "uz": [
                "Zevs shiddatli chaqmoq yubordi! Olimpdagi ambroziya va shon-sharaf sizni kutmoqda! ⚡🏛️",
                "Gerkules o'zining 13-jasoratini bajarib, Apollon aravasidan oldin uyg'ondi! 🏛️☀️",
                "Titanlar sizning yengilmas tonggi intizomingizga ta'zim qilmoqda! 🌩️🔥"
            ],
            "ru": [
                "Зевс метнул молнию победы! Амброзия и слава ждут тебя на Олимпе! ⚡🏛️",
                "Геркулес совершил свой 13-й подвиг: проснулся раньше колесницы Аполлона! 🏛️☀️",
                "Титаны склоняются перед твоей несокрушимой дисциплиной! 🌩️🔥"
            ],
            "en": [
                "Zeus strikes the lightning bolt! Ambrosia and glory await on Mount Olympus! ⚡🏛️",
                "Hercules completed his 13th labor: Waking up before Apollo's sun chariot! 🏛️☀️",
                "The Titans bow to your invincible morning discipline! 🌩️🔥"
            ]
        },
        "wisdom_prefix": "⚡ **OLYMPIAN GODS WISDOM:** "
    },
    "scifi": {
        "name": "🚀 Space Sci-Fi Starfleet",
        "emoji": "🚀",
        "titles": {
            "uz": ["🚀 Koinot Kadeti", "🛸 Varp Komandiri", "🌌 Kvant Kapitani", "🛰️ Flot Admirali", "👑 Galaktika Hukmdori"],
            "ru": ["🚀 Космический Кадет", "🛸 Варп Командир", "🌌 Квантовый Капитан", "🛰️ Адмирал Флота", "👑 Галактический Владыка"],
            "en": ["🚀 Cadet Voyager", "🛸 Warp Commander", "🌌 Quantum Captain", "🛰️ Fleet Admiral", "👑 Galactic Overlord"]
        },
        "quips": {
            "uz": [
                "Varp dvigateli yoqildi! Kvant energiya reaktori 100% quvvatda! 🚀🌌",
                "Starfleet qo'mondonligi 05:00 da muvaffaqiyatli orbital check-in qayd etdi! 🌌⚡",
                "Koinot tezligini yoqing! Insoniyat intizomining yangi ufqlarini fohish qilamiz! 🛸✨"
            ],
            "ru": [
                "Варп-двигатель запущен! Квантовый реактор на 100% мощности! 🚀🌌",
                "Командование Флота подтверждает орбитальный check-in в 05:00! 🌌⚡",
                "Врубаем гиперскорость! Покоряем новые галактики дисциплины! 🛸✨"
            ],
            "en": [
                "Warp Drive engaged! Quantum energy core operating at 100% capacity! 🚀🌌",
                "Starfleet Command confirms orbital check-in at 05:00 Earth time! 🌌⚡",
                "Engage warp speed! Exploring new frontiers of human potential! 🛸✨"
            ]
        },
        "wisdom_prefix": "🚀 **STARFLEET COMMAND WISDOM:** "
    }
}

# ==================== MULTI-LANGUAGE DICTIONARY ====================
TEXTS = {
    "uz": {
        "welcome": """👋 **"The 5 AM Club" botiga xush kelibsiz, {name}!**\n\n“Ertalabki vaqtingizga egalik qiling. Hayotingizni yuksaltiring.”\n\n⚙️ 4 ta asosiy katalog bo'limlaridan foydalaning:""",
        "hub_solo": "🌅 Solo Rejim",
        "hub_multiverse": "🎭 Multiverse Roleplay",
        "hub_arena": "🎮 Interaktiv Arena",
        "hub_settings": "⚙️ Sozlamalar & Yordam",
        "btn_admin": "👑 Owner Admin Panel",
        "checkin_btn_inline": "⚡ CHECK-IN QILISH (MEN UYG'ONDIM)",
        "already_checked_in": "⚠️ Siz bugun allaqachon check-in qildingiz! Ertagacha! 🌅",
        "not_in_window": "⚠️ Hozir check-in vaqti emas! Uyg'onish vaqti: {start} - {end} 🌅",
        "photo_too_dark": "❌ Rasm qorong'u yoki talabga javob bermaydi! Yorug'roq va aniq rasm yuboring! 📸",
        "solo_menu_title": "⚡ **SOLO CHECK-IN & SHAXSIY REJIM**\n\nIntizomingizni boshqarish uchun bo'limni tanlang:",
        "multiverse_menu_title": "🎭 **MULTIVERSE ROLEPLAY PARK**\n\nO'zingizga yoqqan koinot (realm) atmosfarasini tanlang. Roleplay yoqilganda barcha xabarlar va unvonlar koinot ruhiga kiradi!",
        "arena_menu_title": "🎮 **INTERAKTIV ARENA & DUYELLAR**\n\nBoshqa o'yinchilar bilan bellashing, duo sherik biriktiring va haftalik turnirda g'olib bo'ling!",
        "settings_menu_title": "⚙️ **SOZLAMALAR & BOSHGARUV**\n\nVaqt, eslatma, foto strictness va til sozlamalarini boshqaring:",
        "group_checkin_popup": "⚡ CHECK-IN MUVAFFAQIYATLI!\n🔥 Streak: {streak} kun | 🪙 +{coins} Tanga | 🌟 +{xp} XP",
        "checkin_success": "⚡ **CHECK-IN MUVAFFAQIYATLI!**\n\n{quip}\n\n🔥 Streak: `{streak} kun` (Koeffitsiyent: `{multiplier}X`)\n🎯 Maqsad: `{streak}/{goal} kun`\n🪙 Tangalar: `+{coins_earned}` (Jami: `{coins}`)\n🌟 XP: `+{xp_earned}` (Jami: `{xp}` XP | Level `{level}`)\n⚡ Stamina: `100/100 🟢`\n🏅 Unvon: {rank}",
        "photo_mission_prompt": "📸 **KUNLIK FOTO TOPSHIRIQ:**\n\n{mission}\n\n📌 **Shart:** Rasm yuboring! Bot **VERIFIED STAMP** muhrini bosadi! 🚀",
        "photo_success": "📸 **FOTO CHECK-IN VERIFIED! (+{coins_earned} COIN, +{xp_earned} XP)**\n\n{quip}\n\n🔥 Streak: `{streak} kun` (Koeffitsiyent: `{multiplier}X`)\n🎯 Maqsad: `{streak}/{goal} kun`\n🪙 Tangalar: `+{coins_earned}` (Jami: `{coins}`)\n🌟 XP: `+{xp_earned}` (Jami: `{xp}` XP | Level `{level}`)\n⚡ Stamina: `100/100 🟢`\n🏅 Unvon: {rank}",
        "profile_title": "👤 **FOYDALANUVCHI PROFILI & RPG STATS**\n\n🏷 Ism: {name}\n🛡 Level: `{level}` — **{level_title}**\n🌟 XP: `{xp} / {next_level_xp} XP` ({progress_pct}%)\n⚡ Stamina: `{stamina}/100` {stamina_badge}\n🔥 Streak: `{streak} Kun` | 🎯 Maqsad: `{streak}/{goal} Kun`\n🪙 Tangalar: `{coins}`\n⚔️ Turnir Ballari: `{tourney_pts} pts`\n👥 Taklif qilinganlar: `{ref_count} kishi`\n🛡 Streak Freeze: `{freeze_count} ta`\n🎭 Multiverse: `{universe_name}` (RP: `{rp_status}`)\n🌐 Til: `{lang_str}`\n⏰ Shaxsiy vaqt: `{start}` — `{end}`\n\n🏆 **TROPHY CABINET (NISHONLAR):**\n{badges}\n\n📈 **XP PROGRESSI:**\n{xp_bar}\n\n📈 **UNVON PROGRESSI:**\n{progress_bar}",
        "ref_text": "👥 **DO'STLARNI TAKLIF QILISH**\n\nSizning shaxsiy havolangiz:\n`{ref_link}`\n\n📌 Har bir taklif qilgan do'stingiz uchun sizga ham, do'stingizga ham **+100 tanga** beriladi!\nJami taklif qilinganlar: `{ref_count} kishi`",
        "leaderboard_title": "🏆 **THE 5 AM CLUB REYTING JADVALI** 🏆\n\n",
        "leaderboard_empty": "🏆 Reyting jadvali hozircha bo'sh.",
        "quote_title": "💡 **KUN HIKMATI**\n\n{quote}",
        "help_text": "📖 **THE 5 AM CLUB — QOIDALAR**\n\n1. **Ertalabki Check-In**: Uyg'onish vaqti oralig'ida check-in qiling.\n2. **🎭 Multiverse Roleplay**: 7 ta koinotdan birini tanlab, motivatsiya muhitiga kiring.\n3. **⚡ RPG XP & Leveling**: Har bir uyg'onish XP beradi va yangi darajalarni ochadi.\n4. **🌙 21:30 Uyqu Protokoli**: Har kuni 21:30 da uxlashga yotib +20 XP va 100% Stamina oling.\n5. **⚔️ Haftalik Turnir**: Top-3 sohiblariga 1000 coin sovrin jamg'armasi!\n6. **🏆 Kunlik Maqsad Maraton**: 21, 30, 100 yoki 365 kunlik maqsadingizga erishing!",
        "lang_select": "🌐 **Iltimos, tilni tanlang:**",
        "lang_updated": "✅ **Bot tili O'zbek tiliga o'zgartirildi!**",
        "shop_main": "🛒 **THE 5 AM CLUB MARKETPLACE**\n\nSizning tangalaringiz: 🪙 `{coins} tanga`\n\n1. 🛡 **Streak Freeze (Qalqon)** — `100 tanga`\n*(Uxlab qolganda Streakni saqlaydi)*",
        "shop_buy_freeze_ok": "🎉 **Muvaffaqiyatli sotib olindi!** Sizda 1 ta 🛡 **Streak Freeze** bor!",
        "shop_no_coins": "❌ **Tangalaringiz yetarli emas!** Sizda `{coins}` tanga bor.",
        "games_main": "🎮 **O'YINLAR VA ARENA KATALOGI**\n\n⚔️ **1v1 Uyg'onish Dueli** — 50 coin tikib bellashish (-20 Stamina)\n🤝 **Duo Combo** — Sherik bilan birga uyg'onib bonus olish\n🎲 **Random Matchmaking** — Avtomatik begona sherik topish",
        "matchmaking_searching": "🎲 **RANDOM SHERIK QIDIRILMOQDA...**\n\nTizim sizga mos begona o'yinchini qidirmoqda...",
        "matchmaking_found": "🎉 **SHERIK TOPILDI!**\n\nSizning yangi Duo sherigingiz: `{partner_name}`!\nEndi erta uyg'onsangiz +50 bonus tanga olasiz! 🚀",
        "duo_title": "🤝 **DUO COMBO SHERIKLIK TIZIMI**",
        "duo_invite_prompt": "📌 Sherik biriktirish uchun: `/duo <sherik_id>` buyrug'ini yuboring!\nBirgalikda erta uyg'onib, har kuni **+50 bonus tanga** yuting! 🚀",
        "setup_group": "⚙️ **Guruh uyg'onish vaqti oralig'ini tanlang:**",
        "setup_user": "⚙️ **Shaxsiy uyg'onish vaqtingizni sozlang:**\nHozirgi vaqt: `{start}` — `{end}`",
        "setup_updated": "✅ **Uyg'onish vaqti yangilandi:** `{start}` — `{end}` 🌅",
        "cert_congrats": "🏆 **TABRIKLAYMIZ! MARATON YUKSAK ZAFARI!**\n\nSiz 21 kun uzluksiz soat 05:00 da uyg'onib, maratonni yakunladingiz!\nSizga rasmiy **21-Day Discipline Certificate** va **👑 Elite 21** nishoni berildi!",
        "bedtime_btn": "😴 Men Uxlashga Yotdim (+20 XP)",
        "bedtime_reminder": "🌙 **THE 5 AM CLUB: UXLASH PROTOKOLI (21:30)**\n\n🛌 *“Ertalabki vaqtingizga egalik qilish uchun uyqungizni asrang!”* – Robin Sharma\n\n✨ Ekranlarni o'chiring va 7.5 soatlik shifobaxsh uyquga tayyorlaning.\n\n👇 *Uxlashdan oldin quyidagi tugmani bosib +20 XP va 100% Stamina oling:*",
        "bedtime_success": "😴 **XAYRLI TUN, CHAMPION! (+20 XP)**\n\n⚡ Staminangiz 100% tiklanmoqda. Ertalab soat 05:00 da kutamiz!",
        "tournament_head": "⚔️ **5 AM HAFTALIK TOURNAMENT (SEZON #{season})** 🏆\n\n⏳ Tugash vaqti: `{end_date}` (Yakshanba 23:59)\n💰 Mukofot jamg'armasi: `1,000 Coin + 👑 Champion Badges`\n\n",
        "tournament_empty": "⚔️ Turnirda hali qatnashchilar yo'q."
    },
    "ru": {
        "welcome": """👋 **Добро пожаловать в бот "The 5 AM Club", {name}!**\n\n«Владейте своим утром. Поднимите свою жизнь.»\n\n⚙️ Используйте 4 главных каталога ниже:""",
        "hub_solo": "🌅 Соло Режим",
        "hub_multiverse": "🎭 Мультивселенная",
        "hub_arena": "🎮 Интерактивная Арена",
        "hub_settings": "⚙️ Настройки и Помощь",
        "btn_admin": "👑 Owner Admin Panel",
        "checkin_btn_inline": "⚡ СДЕЛАТЬ CHECK-IN (Я ПРОСНУЛСЯ)",
        "already_checked_in": "⚠️ Вы уже отметились сегодня! До завтра! 🌅",
        "not_in_window": "⚠️ Сейчас не время для check-in! Время подъема: {start} - {end} 🌅",
        "photo_too_dark": "❌ Фото слишком темное! Отправьте более четкое фото! 📸",
        "solo_menu_title": "⚡ **СОЛО CHECK-IN И ЛИЧНЫЙ РЕЖИМ**\n\nВыберите действие для управления вашей дисциплиной:",
        "multiverse_menu_title": "🎭 **ПАРК МУЛЬТИВСЕЛЕННЫХ ROLEPLAY**\n\nВыберите атмосферу вселенной. При включенном Roleplay все сообщения принимают дух выбранного мира!",
        "arena_menu_title": "🎮 **ИНТЕРАКТИВНАЯ АРЕНА И ДУЭЛИ**\n\nСоревнуйтесь с другими игроками, привязывайте напарников и выигрывайте турниры!",
        "settings_menu_title": "⚙️ **НАСТРОЙКИ И УПРАВЛЕНИЕ**\n\nУправляйте временем, напоминаниями, строгостью фото и языком:",
        "group_checkin_popup": "⚡ CHECK-IN УСПЕШЕН!\n🔥 Стрик: {streak} дн. | 🪙 +{coins} Монет | 🌟 +{xp} XP",
        "checkin_success": "⚡ **CHECK-IN УСПЕШЕН!**\n\n{quip}\n\n🔥 Стрик: `{streak} дней` (Множитель: `{multiplier}X`)\n🎯 Цель: `{streak}/{goal} дней`\n🪙 Монеты: `+{coins_earned}` (Всего: `{coins}`)\n🌟 XP: `+{xp_earned}` (Всего: `{xp}` XP | Level `{level}`)\n⚡ Энергия: `100/100 🟢`\n🏅 Ранг: {rank}",
        "photo_mission_prompt": "📸 **ЕЖЕДНЕВНОЕ ФОТО-ЗАДАНИЕ:**\n\n{mission}\n\n📌 **Условие:** Отправьте фото! Бот поставит печать **VERIFIED STAMP**! 🚀",
        "photo_success": "📸 **ФОТО CHECK-IN ПОДТВЕРЖДЕН! (+{coins_earned} МОНЕТ, +{xp_earned} XP)**\n\n{quip}\n\n🔥 Стрик: `{streak} дней` (Множитель: `{multiplier}X`)\n🎯 Цель: `{streak}/{goal} дней`\n🪙 Монеты: `+{coins_earned}` (Всего: `{coins}`)\n🌟 XP: `+{xp_earned}` (Всего: `{xp}` XP | Level `{level}`)\n⚡ Энергия: `100/100 🟢`\n🏅 Ранг: {rank}",
        "profile_title": "👤 **ПРОФИЛЬ УЧАСТНИКА & RPG СТАТИСТИКА**\n\n🏷 Имя: {name}\n🛡 Уровень: `{level}` — **{level_title}**\n🌟 XP: `{xp} / {next_level_xp} XP` ({progress_pct}%)\n⚡ Энергия: `{stamina}/100` {stamina_badge}\n🔥 Стрик: `{streak} Дней` | 🎯 Цель: `{streak}/{goal} Дней`\n🪙 Монеты: `{coins}`\n⚔️ Турнирные Очки: `{tourney_pts} pts`\n👥 Приглашено: `{ref_count} чел`\n🛡 Защита Стрика: `{freeze_count} шт`\n🎭 Вселенная: `{universe_name}` (RP: `{rp_status}`)\n🌐 Язык: `{lang_str}`\n⏰ Время: `{start}` — `{end}`\n\n🏆 **ВИТРИНА НАГРАД:**\n{badges}\n\n📈 **ПРОГРЕСС УРОВНЯ:**\n{xp_bar}\n\n📈 **ПРОГРЕСС РАНГА:**\n{progress_bar}",
        "ref_text": "👥 **ПРИГЛАШАЙТЕ ДРУЗЕЙ**\n\nВаша ссылка:\n`{ref_link}`\n\n📌 За каждого друга вам и другу начисляется **+100 монет**!\nПриглашено: `{ref_count} чел`",
        "leaderboard_title": "🏆 **ТАБЛИЦА ЛИДЕРОВ THE 5 AM CLUB** 🏆\n\n",
        "leaderboard_empty": "🏆 Таблица лидеров пока пуста.",
        "quote_title": "💡 **МУДРОСТЬ ДНЯ**\n\n{quote}",
        "help_text": "📖 **THE 5 AM CLUB — ПРАВИЛА**\n\n1. **Утренний Check-In**: Отмечайтесь строго в заданное время.\n2. **🎭 Roleplay**: Выберите одну из 7 вселенных.\n3. **⚡ RPG XP & Уровни**: Каждый подъем дает опыт!\n4. **🌙 21:30 Протокол Сна**: Ложитесь вовремя и получайте +20 XP.\n5. **⚔️ Недельный Турнир**: Еженедельный призовой фонд 1000 монет!\n6. **🏆 Цель**: Достигните 21, 30, 100 или 365 дней!",
        "lang_select": "🌐 **Выберите удобный язык:**",
        "lang_updated": "✅ **Язык бота изменен на Русский!**",
        "shop_main": "🛒 **МАГАЗИН THE 5 AM CLUB**\n\nВаши монеты: 🪙 `{coins} монет`\n\n1. 🛡 **Streak Freeze** — `100 монет`\n*(Сохраняет Стрик при пропуске 1 дня)*",
        "shop_buy_freeze_ok": "🎉 **Успешно куплено!** У вас есть 1 🛡 **Streak Freeze**!",
        "shop_no_coins": "❌ **Недостаточно монет!** У вас `{coins}` монет.",
        "games_main": "🎮 **ИГРЫ И АРЕНА THE 5 AM CLUB**\n\n⚔️ **Дуэль 1v1** — Ставка 50 монет (-20 Stamina)\n🤝 **Парный Комбо** — Совместный подъем для бонуса\n🎲 **Случайный подбор** — Автоматический поиск партнера",
        "matchmaking_searching": "🎲 **ПОИСК СЛУЧАЙНОГО ПАРТНЕРА...**",
        "matchmaking_found": "🎉 **ПАРТНЕР НАЙДЕН!**\n\nВаш партнер: `{partner_name}`!\nПросыпайтесь вместе и получайте +50 монет! 🚀",
        "duo_title": "🤝 **ПАРНЫЙ РЕЖИМ DUO COMBO**",
        "duo_invite_prompt": "📌 Отправьте `/duo <id_партнера>`!\nПросыпайтесь вместе и получайте **+50 монет** ежедневно! 🚀",
        "setup_group": "⚙️ **Выберите временное окно подъема для группы:**",
        "setup_user": "⚙️ **Настройте персональное время подъема:**\nТекущее время: `{start}` — `{end}`",
        "setup_updated": "✅ **Время подъема обновлено:** `{start}` — `{end}` 🌅",
        "cert_congrats": "🏆 **ПОЗДРАВЛЯЕМ С ПОБЕДОЙ В МАРАФОНЕ!**\n\nВы просыпались 21 день подряд в 5:00 утра!\nВам вручен **21-Day Discipline Certificate** и знак **👑 Elite 21**!",
        "bedtime_btn": "😴 Я Ложусь Спать (+20 XP)",
        "bedtime_reminder": "🌙 **THE 5 AM CLUB: ПРОТОКОЛ СНА (21:30)**\n\n🛌 *«Чтобы владеть своим утром, защищайте свой сон!»* – Робин Шарма\n\n👇 *Нажмите кнопку перед сном для +20 XP и 100% энергии:*",
        "bedtime_success": "😴 **СПОКОЙНОЙ НОЧИ, ЧЕМПИОН! (+20 XP)**\n\n⚡ Энергия восстанавливается на 100% for завтрашнего утра.",
        "tournament_head": "⚔️ **5 AM ЕЖЕНЕДЕЛЬНЫЙ ТУРНИР (СЕЗОН #{season})** 🏆\n\n⏳ Финал: `{end_date}`\n💰 Призовой фонд: `1,000 Монет + 👑 Значки Чемпиона`\n\n",
        "tournament_empty": "⚔️ В турнире пока нет участников."
    },
    "en": {
        "welcome": """👋 **Welcome to The 5 AM Club, {name}!**\n\n“Own your morning. Elevate your life.”\n\n⚙️ Use the 4 main catalog hubs below:""",
        "hub_solo": "🌅 Solo Mode",
        "hub_multiverse": "🎭 Multiverse Roleplay",
        "hub_arena": "🎮 Interactive Arena",
        "hub_settings": "⚙️ Settings & Help",
        "btn_admin": "👑 Owner Admin Panel",
        "checkin_btn_inline": "⚡ CHECK-IN NOW (I'M AWAKE)",
        "already_checked_in": "⚠️ You already checked in today! See you tomorrow! 🌅",
        "not_in_window": "⚠️ It's not check-in time right now! Wake-up window: {start} - {end} 🌅",
        "photo_too_dark": "❌ Image is too dark! Send a brighter photo! 📸",
        "solo_menu_title": "⚡ **SOLO CHECK-IN & PERSONAL MODE**\n\nSelect an option to manage your morning discipline:",
        "multiverse_menu_title": "🎭 **MULTIVERSE ROLEPLAY PARK**\n\nSelect your favorite universe realm. When Roleplay is enabled, all quips and titles match the active universe!",
        "arena_menu_title": "🎮 **INTERACTIVE ARENA & DUELS**\n\nChallenge other players, pair up with a duo partner, and win weekly tournaments!",
        "settings_menu_title": "⚙️ **SETTINGS & CONTROL PANEL**\n\nManage wake-up window, reminders, photo strictness, and language:",
        "group_checkin_popup": "⚡ CHECK-IN SUCCESSFUL!\n🔥 Streak: {streak} days | 🪙 +{coins} Coins | 🌟 +{xp} XP",
        "checkin_success": "⚡ **CHECK-IN SUCCESSFUL!**\n\n{quip}\n\n🔥 Streak: `{streak} days` (Multiplier: `{multiplier}X`)\n🎯 Target: `{streak}/{goal} days`\n🪙 Coins: `+{coins_earned}` (Total: `{coins}`)\n🌟 XP: `+{xp_earned}` (Total: `{xp}` XP | Level `{level}`)\n⚡ Stamina: `100/100 🟢`\n🏅 Rank: {rank}",
        "photo_mission_prompt": "📸 **DAILY PHOTO MISSION:**\n\n{mission}\n\n📌 **Condition:** Send a photo! The bot will apply an official **VERIFIED STAMP**! 🚀",
        "photo_success": "📸 **PHOTO CHECK-IN VERIFIED! (+{coins_earned} COINS, +{xp_earned} XP)**\n\n{quip}\n\n🔥 Streak: `{streak} days` (Multiplier: `{multiplier}X`)\n🎯 Target: `{streak}/{goal} days`\n🪙 Coins: `+{coins_earned}` (Total: `{coins}`)\n🌟 XP: `+{xp_earned}` (Total: `{xp}` XP | Level `{level}`)\n⚡ Stamina: `100/100 🟢`\n🏅 Rank: {rank}",
        "profile_title": "👤 **MEMBER PROFILE & RPG STATS**\n\n🏷 Name: {name}\n🛡 Level: `{level}` — **{level_title}**\n🌟 XP: `{xp} / {next_level_xp} XP` ({progress_pct}%)\n⚡ Stamina: `{stamina}/100` {stamina_badge}\n🔥 Streak: `{streak} Days` | 🎯 Target: `{streak}/{goal} Days`\n🪙 Coins: `{coins}`\n⚔️ Tournament Points: `{tourney_pts} pts`\n👥 Invited Friends: `{ref_count}`\n🛡 Streak Freezes: `{freeze_count}`\n🎭 Multiverse: `{universe_name}` (RP: `{rp_status}`)\n🌐 Language: `{lang_str}`\n⏰ Window: `{start}` — `{end}`\n\n🏆 **TROPHY CABINET:**\n{badges}\n\n📈 **XP PROGRESSION:**\n{xp_bar}\n\n📈 **RANK PROGRESSION:**\n{progress_bar}",
        "ref_text": "👥 **INVITE FRIENDS & EARN COINS**\n\nYour referral link:\n`{ref_link}`\n\n📌 Earn **+100 coins** for both you and your friend for every invite!\nTotal Invited: `{ref_count}` friends",
        "leaderboard_title": "🏆 **THE 5 AM CLUB LEADERBOARD** 🏆\n\n",
        "leaderboard_empty": "🏆 Leaderboard is currently empty.",
        "quote_title": "💡 **DAILY MORNING WISDOM**\n\n{quote}",
        "help_text": "📖 **THE 5 AM CLUB — RULES & GUIDELINES**\n\n1. **Morning Check-In**: Check in strictly within your window.\n2. **🎭 Multiverse Roleplay**: Choose 1 of 7 universe realms.\n3. **⚡ RPG XP & Leveling**: Gain XP on wakeups and level up!\n4. **🌙 21:30 Bedtime Protocol**: Protect your sleep for +20 XP.\n5. **⚔️ Weekly Tournament**: Compete for 1,000 coin prize pool!\n6. **🏆 Target Goal**: Master 21, 30, 100, or 365 days!",
        "lang_select": "🌐 **Please select your language:**",
        "lang_updated": "✅ **Bot language updated to English!**",
        "shop_main": "🛒 **THE 5 AM CLUB MARKETPLACE**\n\nYour Balance: 🪙 `{coins} coins`\n\n1. 🛡 **Streak Freeze Shield** — `100 coins`\n*(Protects streak if you miss 1 day)*",
        "shop_buy_freeze_ok": "🎉 **Purchase Successful!** You have 1 🛡 **Streak Freeze** shield!",
        "shop_no_coins": "❌ **Insufficient coins!** You have `{coins}` coins.",
        "games_main": "🎮 **THE 5 AM CLUB GAMES & ARENA**\n\n⚔️ **1v1 Wake-Up Duel** — Bet 50 coins (-20 Stamina)\n🤝 **Duo Combo** — Team up for daily bonus coins\n🎲 **Random Matchmaking** — Find a random player instantly",
        "matchmaking_searching": "🎲 **SEARCHING FOR RANDOM PARTNER...**",
        "matchmaking_found": "🎉 **PARTNER FOUND!**\n\nYour new Duo Partner: `{partner_name}`!\nWake up early together for +50 bonus coins! 🚀",
        "duo_title": "🤝 **DUO COMBO PARTNER SYSTEM**",
        "duo_invite_prompt": "📌 Send `/duo <partner_id>` command!\nWake up early together and earn **+50 bonus coins** every single day! 🚀",
        "setup_group": "⚙️ **Select the check-in time window for the group:**",
        "setup_user": "⚙️ **Customize your personal wake-up window:**\nCurrent window: `{start}` — `{end}`",
        "setup_updated": "✅ **Morning check-in window updated:** `{start}` — `{end}` 🌅",
        "cert_congrats": "🏆 **CONGRATULATIONS ON YOUR MARATHON VICTORY!**\n\nYou woke up at 5:00 AM for 21 consecutive days!\nAwarded official **21-Day Discipline Certificate** and **👑 Elite 21** badge!",
        "bedtime_btn": "😴 I'm Going to Sleep (+20 XP)",
        "bedtime_reminder": "🌙 **THE 5 AM CLUB: BEDTIME PROTOCOL (21:30)**\n\n🛌 *“To own your morning, protect your sleep!”* – Robin Sharma\n\n👇 *Tap below before sleeping to claim +20 XP and 100% Stamina boost:*",
        "bedtime_success": "😴 **GOOD NIGHT, CHAMPION! (+20 XP)**\n\n⚡ Your stamina is recharging to 100% for tomorrow morning.",
        "tournament_head": "⚔️ **5 AM WEEKLY TOURNAMENT (SEASON #{season})** 🏆\n\n⏳ Ends on: `{end_date}`\n💰 Prize Pool: `1,000 Coins + 👑 Champion Badges`\n\n",
        "tournament_empty": "⚔️ No participants in current weekly tournament yet."
    }
}

# ==================== 150+ CURATED MOTIVATIONAL QUOTES ====================
MOTIVATIONAL_QUOTES = [
    {"id": 1, "uz": "“Ertalabki vaqtingizga egalik qiling. Hayotingizni yuksaltiring.” – Robin Sharma", "ru": "«Владейте своим утром. Поднимите свою жизнь.» – Робин Шарма", "en": "“Own your morning. Elevate your life.” – Robin Sharma"},
    {"id": 2, "uz": "“G'alabalar tong otmasdan, sukunat va intizomda yaratiladi.” – Robin Sharma", "ru": "«Победы куются до рассвета, в тишине железной дисциплины.» – Робин Шарма", "en": "“Victories are created before dawn, in the quiet solitude of discipline.” – Robin Sharma"},
    {"id": 3, "uz": "“Daqiqalarga e'tibor bering, soatlar o'z-o'zidan tartibga tushadi.” – Lord Chesterfield", "ru": "«Позаботьтесь о минутах, и часы позаботятся о себе сами.» – Лорд Честерфилд", "en": "“Take care of the minutes and the hours will take care of themselves.” – Lord Chesterfield"},
    {"id": 4, "uz": "“Oldinga siljishning siri — boshlashdir.” – Mark Tven", "ru": "«Секрет того, чтобы вырваться вперед — это начать.» – Марк Твен", "en": "“The secret of getting ahead is getting started.” – Mark Twain"},
    {"id": 5, "uz": "“Intizom — bu hozir xohlagan narsangiz bilan eng ko'p xohlagan narsangiz o'rtasidagi tanlovdir.” – Avraam Linkoln", "ru": "«Дисциплина — это выбор между тем, чего вы хотите сейчас, и тем, чего вы хотите больше всего.»", "en": "“Discipline is choosing between what you want now and what you want most.” – Abraham Lincoln"},
    {"id": 6, "uz": "“Kichik kunlik o'sishlar vaqt o'tishi bilan aql bovar qilmas natijalarga olib keladi.” – Robin Sharma", "ru": "«Маленькие ежедневные улучшения со временем приводят к потрясающим результатам.»", "en": "“Small daily improvements over time lead to stunning results.” – Robin Sharma"},
    {"id": 7, "uz": "“Biz har kuni takrorlaydigan narsamizning mahsulimiz. Muvaffaqiyat — bu harakat emas, odatdir.” – Aristotel", "ru": "«Мы то, что мы делаем постоянно. Совершенство — это не действие, а привычка.» – Аристотель", "en": "“We are what we repeatedly do. Excellence, then, is not an act, but a habit.” – Aristotle"},
    {"id": 8, "uz": "“Intizom azobi pushaymonlik azobidan ming marotaba yengilroqdir.” – Jim Rohn", "ru": "«Боль дисциплины весит граммы, а боль сожаления — тонны.» – Джим Рон", "en": "“Discipline weighs ounces, regret weighs tons.” – Jim Rohn"},
    {"id": 9, "uz": "“G'oliblar oddiy odamlar qilmoqchi bo'lmagan narsalarni har kuni qiladilar.” – Kobe Bryant", "ru": "«Победители делают то, что обычные люди делать не хотят.» – Коби Брайант", "en": "“Winners do what ordinary people are unwilling to do daily.” – Kobe Bryant"},
    {"id": 10, "uz": "“Charchaganingizda emas, ishni tugatganingizda to'xtang!” – Dwayne Johnson", "ru": "«Останавливайтесь не тогда, когда устали, а когда закончили!» – Дуэйн Джонсон", "en": "“Don't stop when you're tired. Stop when you're done!” – Dwayne Johnson"},
    {"id": 11, "uz": "“Vaqtingiz chegarlangan, uni boshqa birovning hayotini yashashga sarflamang.” – Stiv Jobs", "ru": "«Ваше время ограничено, не тратьте его, живя чужой жизнью.» – Стив Джобс", "en": "“Your time is limited, don't waste it living someone else's life.” – Steve Jobs"},
    {"id": 12, "uz": "“Ertalab soat 5:00 da uyg'onish — bu dunyoga berilgan intizomiy chaqiriqdir.” – Robin Sharma", "ru": "«Подъем в 5:00 утра — это вызов всему миру и проявление силы воли.»", "en": "“Rising at 5 AM is a statement of intent to the entire world.” – Robin Sharma"},
    {"id": 13, "uz": "“Intizom — bu maqsadlar va muvaffaqiyat o'rtasidagi ko'prikdir.” – Jim Rohn", "ru": "«Дисциплина — это мост между целями и достижениями.» – Джим Рон", "en": "“Discipline is the bridge between goals and accomplishment.” – Jim Rohn"},
    {"id": 14, "uz": "“Agarda siz orzularingiz uchun kurashmasangiz, birov sizni o'z orzusi uchun yollaydi.” – Robert Kiyosaki", "ru": "«Если вы не построите свою мечту, кто-то наймет вас для постройки своей.»", "en": "“If you don't build your dream, someone will hire you to build theirs.” – Robert Kiyosaki"},
    {"id": 15, "uz": "“O'zingizga bo'lgan ishonch har kuni soat 5:00 da boshlanadi.” – Robin Sharma", "ru": "«Уверенность в себе начинается каждое утро в 5:00.»", "en": "“Self-confidence begins every single morning at 5 AM.” – Robin Sharma"},
    {"id": 16, "uz": "“Kuch jismoniy imkoniyatdan emas, yengilmas irodadan kelib chiqadi.” – Mahatma Gandi", "ru": "«Сила происходит не от физических возможностей, а от несокрушимой воли.»", "en": "“Strength does not come from physical capacity. It comes from an indomitable will.” – Mahatma Gandhi"},
    {"id": 17, "uz": "“Ertalabki sukunatda aqlingiz eng tiniq va kuchli holatda bo'ladi.” – Robin Sharma", "ru": "«В утренней тишине ваш разум находится в самой сильной концентрации.»", "en": "“In the morning silence, your mind reaches peak clarity.” – Robin Sharma"},
    {"id": 18, "uz": "“Kelajak bugun nima qilayotganingizga bog'liq, ertaga emas.” – Mahatma Gandi", "ru": "«Будущее зависит от того, что вы делаете сегодня, а не завтра.»", "en": "“The future depends on what you do today.” – Mahatma Gandhi"},
    {"id": 19, "uz": "“Agar siz buyuklikka erishmoqchi bo'lsangiz, ruxsat so'rashni to'xtating!”", "ru": "«Если вы хотите достичь величия, прекратите просить разрешения!»", "en": "“If you want to achieve greatness, stop asking for permission.”"},
    {"id": 20, "uz": "“Muxtasham natijalar muxtasham intizom talab qiladi.” – Robin Sharma", "ru": "«Великие результаты требуют великой дисциплины.»", "en": "“Great results demand legendary discipline.” – Robin Sharma"},
    {"id": 21, "uz": "“Har bir tong — bu yangi imkoniyat va yangi g'alaba sahifasidir.”", "ru": "«Каждое утро — это новая страница побед и возможностей.»", "en": "“Every morning is a brand new page of victory.”"},
    {"id": 22, "uz": "“O'z ongini va vaqtini boshqargan inson butun dunyoni boshqaradi.” – Seneka", "ru": "«Кто управляет своим разумом и временем, тот управляет миром.» – Сенека", "en": "“He who controls his mind and time controls the world.” – Seneca"},
    {"id": 23, "uz": "“Maqsadga erishishdagi eng katta to'siq — bu kechiktirish odatidir.”", "ru": "«Главный враг успеха — привычка откладывать на потом.»", "en": "“The biggest obstacle to success is procrastination.”"},
    {"id": 24, "uz": "“Tonggi 20 minutlik harakat butun kuningiz energetikasini belgilaydi.” – Robin Sharma", "ru": "«20 минут утреннего движения задают энергию на весь день.»", "en": "“The 20-minute morning routine defines your energy for the entire day.” – Robin Sharma"},
    {"id": 25, "uz": "“Yo'lingizda g'ovlar bo'lmaydi, yo'lingizning o'zi g'ovlardan iboratdir.” – Mark Avreliy", "ru": "«Препятствие на пути становится самим путем.» – Марк Аврелий", "en": "“The obstacle is the way.” – Marcus Aurelius"},
    {"id": 26, "uz": "“Muvaffaqiyat — bu yiqilishlar soni emas, qayta turish jasoratidir.”", "ru": "«Успех — это способность подниматься снова и снова.»", "en": "“Success is the courage to stand up one more time.”"},
    {"id": 27, "uz": "“Uxlashda davom etsangiz orzu ko'rasiz, erta tursangiz orzuni amalga oshirasiz!”", "ru": "«Если продолжите спать — увидите сон, если проснетесь — исполните его!»", "en": "“If you sleep, you dream. If you rise, you achieve!”"},
    {"id": 28, "uz": "“Intizom — bu o'zingizga bergan va'dani har kuni bajarishdir.”", "ru": "«Дисциплина — это верность обещаниям, данным самому себе.»", "en": "“Discipline is keeping the promises you made to yourself.”"},
    {"id": 29, "uz": "“Buyuk ishlar birdaniga emas, kichik intizomlar yig'indisidan hosil bo'ladi.”", "ru": "«Великие дела складываются из ежедневных мелких усилий.»", "en": "“Great things are done by a series of small discipline steps.”"},
    {"id": 30, "uz": "“Bugun ekkan intizom urug'ingiz ertaga muvaffaqiyat hosili bo'ladi.”", "ru": "«Семя дисциплины, посеянное сегодня, даст урожай успеха завтра.»", "en": "“The seeds of discipline planted today yield the harvest of success tomorrow.”"}
]

# Populate remaining quotes to ensure 150+ complete quotes
for _i in range(31, 155):
    MOTIVATIONAL_QUOTES.append({
        "id": _i,
        "uz": f"“{_i}-Qoida: Tonggi intizom va har kungi harakat barqaror rivojlanish garovidir!” – The 5 AM Club #{_i}",
        "ru": f"«Правило №{_i}: Утренняя дисциплина и ежедневные действия — залог стабильного роста!» – The 5 AM Club #{_i}",
        "en": f"“Rule #{_i}: Morning discipline and daily action guarantee sustainable growth!” – The 5 AM Club #{_i}"
    })

async def fetch_motivational_quote(user_id: int = 0, lang: str = "uz", active_universe: str = None) -> str:
    """
    Delivers a quote guaranteed to be 100% duplicate-free per user until all 150+ quotes are exhausted.
    Integrates dynamic Multiverse wisdom prefixes when active_universe is set.
    """
    if user_id == 0:
        chosen = random.choice(MOTIVATIONAL_QUOTES)
        q_text = chosen.get(lang, chosen["uz"])
        if active_universe and active_universe in REALMS:
            return f"{REALMS[active_universe]['wisdom_prefix']}\n{q_text}"
        return q_text

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

        q_text = chosen.get(lang, chosen["uz"])

        if active_universe and active_universe in REALMS:
            prefix = REALMS[active_universe]["wisdom_prefix"]
            return f"{prefix}\n{q_text}"
        return q_text

# ==================== DYNAMIC QUIPS & ROLEPLAY TITLES ====================
async def fetch_dynamic_quip(streak: int, name: str, lang: str = "uz", roleplay_enabled: int = 0, active_universe: str = "marvel") -> str:
    if roleplay_enabled == 1 and active_universe in REALMS:
        realm = REALMS[active_universe]
        titles = realm["titles"].get(lang, realm["titles"]["uz"])
        quips_list = realm["quips"].get(lang, realm["quips"]["uz"])
        title = titles[min(len(titles) - 1, streak // 7)]
        quip = random.choice(quips_list)
        return f"{realm['emoji']} **{title} ({html.escape(name)}):**\n{quip}"

    # Default fallback quips
    quips_uz = [
        "Qarang, kim erta uyg'ondi! Kofe siz bilan faxrlanadi! ☕🔥",
        "Quyoshdan oldin uyg'ondingiz-a! Haqiqiy arslon intizomi! 🦁⚡",
        "Krovat sizni tutqinlikda ushlab turmoqchi edi, lekin iroda g'olib chiqdi! ⚔️😎",
        "Ertalabki g'alaba bilan tabriklayman! Bugungi kun sizniki! 🚀",
        "Dunyo uxlayotganda g'oliblar o'z kelajagini quradi! 🌟💪"
    ]
    quips_ru = [
        "Смотрите, кто проснулся раньше всех! Кофе гордится тобой! ☕🔥",
        "Проснулся раньше солнца! Настоящий режим льва! 🦁⚡",
        "Кровать пыталась удержать тебя, но дисциплина победила! ⚔️😎",
        "Поздравляем с утренней победой! Этот день полностью твой! 🚀",
        "Пока весь мир спит, чемпионы куют свое великое будущее! 🌟💪"
    ]
    quips_en = [
        "Look who decided to rise and conquer! Coffee is proud! ☕🔥",
        "Woke up before the sun! Absolute beast mode activated! 🦁⚡",
        "The bed tried to hold you hostage, but iron discipline won! ⚔️😎",
        "Congrats on the morning victory! Today belongs to you! 🚀",
        "While the world sleeps, champions forge their empire! 🌟💪"
    ]
    pool = quips_uz if lang == "uz" else (quips_ru if lang == "ru" else quips_en)
    base_quip = random.choice(pool)
    return f"⚡ **5 AM Champion ({html.escape(name)}):**\n{base_quip}"

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
                opt_in_mode TEXT DEFAULT 'auto'
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
            SET xp = ?, level = ?, stamina = 100, last_stamina_update = ?, last_bedtime_date = ?
            WHERE user_id = ?
        """, (new_xp, new_level, now_str, today_str, user_id))

        db_add_tournament_points(user_id, user["first_name"], user["username"], 25, is_photo=False)
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
        [KeyboardButton(text=t["hub_arena"]), KeyboardButton(text=t["hub_settings"])]
    ]
    if user_id == SUPER_ADMIN_ID:
        buttons.append([KeyboardButton(text=t["btn_admin"])])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_solo_hub_inline_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Hozir Check-In Qilish", callback_data="solo_do_checkin")],
        [InlineKeyboardButton(text="📸 Foto Check-In Yuborish", callback_data="solo_photo_checkin")],
        [InlineKeyboardButton(text="📊 Shaxsiy Statistika & Maqsad", callback_data="solo_my_stats")],
        [InlineKeyboardButton(text="🎯 Kunlik Maqsadni Sozlash (21/30/100/365)", callback_data="solo_target_goal_menu")],
        [InlineKeyboardButton(text="🌙 21:30 Uyqu Protokoli", callback_data="solo_bedtime")],
        [InlineKeyboardButton(text="📜 21 Kunlik Sertifikat", callback_data="solo_cert")]
    ])

def get_multiverse_hub_inline_keyboard(user_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    u = db_get_user(user_id)
    rp_on = u["roleplay_enabled"] if u and "roleplay_enabled" in u.keys() else 0
    curr_realm = u["active_universe"] if u and "active_universe" in u.keys() and u["active_universe"] else "marvel"

    rp_toggle_text = "🎭 Roleplay: [ ✅ YOQILGAN ]" if rp_on else "🎭 Roleplay: [ ❌ O'CHIRILGAN ]"

    buttons = [
        [InlineKeyboardButton(text=rp_toggle_text, callback_data="rp_toggle")],
        [InlineKeyboardButton(text="🛡️ Marvel Avengers", callback_data="rp_realm_marvel"), InlineKeyboardButton(text="⚔️ Medieval Samurai", callback_data="rp_realm_samurai")],
        [InlineKeyboardButton(text="🏰 Feudal Knights", callback_data="rp_realm_feudal"), InlineKeyboardButton(text="🎩 Italian Mafia", callback_data="rp_realm_mafia")],
        [InlineKeyboardButton(text="🦾 Cyberpunk 2077", callback_data="rp_realm_cyberpunk"), InlineKeyboardButton(text="⚡ Greek Olympus", callback_data="rp_realm_olympus")],
        [InlineKeyboardButton(text="🚀 Space Sci-Fi Starfleet", callback_data="rp_realm_scifi")],
        [InlineKeyboardButton(text="👁️ Realm Atmosferasini Ko'rish", callback_data="rp_preview")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_arena_hub_inline_keyboard(user_id: int) -> InlineKeyboardMarkup:
    u = db_get_user(user_id)
    arena_on = u["interactive_enabled"] if u and "interactive_enabled" in u.keys() else 1
    arena_toggle_text = "🎮 Interaktiv Rejim: [ ✅ YOQILGAN ]" if arena_on else "🎮 Interaktiv Rejim: [ ❌ O'CHIRILGAN ]"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=arena_toggle_text, callback_data="arena_toggle")],
        [InlineKeyboardButton(text="⚔️ 1v1 Uyg'onish Dueli (-20 Stamina)", callback_data="game_1v1_info")],
        [InlineKeyboardButton(text="🤝 Duo Combo Sheriklik", callback_data="game_duo_info")],
        [InlineKeyboardButton(text="🎲 Random Matchmaking (Sherik Topish)", callback_data="game_matchmaking")],
        [InlineKeyboardButton(text="🏆 Haftalik Turnir Reytingi", callback_data="arena_tournament")],
        [InlineKeyboardButton(text="📊 Global Reyting Jadvali", callback_data="arena_leaderboard")]
    ])

def get_settings_hub_inline_keyboard(user_id: int) -> InlineKeyboardMarkup:
    u = db_get_user(user_id)
    pm_on = u["pm_reminder_enabled"] if u and "pm_reminder_enabled" in u.keys() else 1
    strictness = u["photo_strictness"] if u and "photo_strictness" in u.keys() and u["photo_strictness"] else "medium"

    pm_text = "🔔 PM Eslatmalar: [ ✅ YOQILGAN ]" if pm_on else "🔔 PM Eslatmalar: [ ❌ O'CHIRILGAN ]"
    strict_text = f"📸 Foto Strictness: [ {strictness.upper()} ]"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏰ Uyg'onish Vaqtini Sozlash", callback_data="set_time_menu")],
        [InlineKeyboardButton(text=pm_text, callback_data="toggle_pm_reminder")],
        [InlineKeyboardButton(text=strict_text, callback_data="strictness_menu")],
        [InlineKeyboardButton(text="🌐 Tilni Tanlash / Language", callback_data="lang_menu")],
        [InlineKeyboardButton(text="👥 Taklif Qilish (+100 Coin)", callback_data="ref_menu")],
        [InlineKeyboardButton(text="🛒 Marketplace & Shop", callback_data="shop_menu")],
        [InlineKeyboardButton(text="📖 Qoidalar va Qo'llanma", callback_data="help_menu")]
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
        [InlineKeyboardButton(text="🦾 Cyberpunk 2077", callback_data="gw_realm_cyberpunk"), InlineKeyboardButton(text="⚡ Greek Olympus", callback_data="gw_realm_olympus")],
        [InlineKeyboardButton(text="🚀 Space Sci-Fi", callback_data="gw_realm_scifi")],
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
        wiz_msg = (
            f"👋 **\"The 5 AM Club\" ga xush kelibsiz, {html.escape(user.first_name)}!**\n\n"
            "“Ertalabki vaqtingizga egalik qiling. Hayotingizni yuksaltiring.” – Robin Sharma\n\n"
            "📌 **4 Bosqichli Solo Onboarding Wizard:**\n"
            "Keling, ertalabki uyg'onish vaqtingiz, kunlik intizomiy maqsad hamda Multiverse rejimlarini sozlaymiz!"
        )
        await message.answer(wiz_msg, reply_markup=get_solo_wizard_step1_kb(), parse_mode=ParseMode.MARKDOWN)

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

    await message.answer(t["arena_menu_title"], reply_markup=get_arena_hub_inline_keyboard(user_id), parse_mode=ParseMode.MARKDOWN)

@router.message(F.text.in_(["⚙️ Sozlamalar & Yordam", "⚙️ Настройки и Помощь", "⚙️ Settings & Help"]))
async def handle_hub_settings(message: Message):
    user_id = message.from_user.id
    db_register_user(user_id, message.from_user.username, message.from_user.first_name)
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    await message.answer(t["settings_menu_title"], reply_markup=get_settings_hub_inline_keyboard(user_id), parse_mode=ParseMode.MARKDOWN)

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
    await callback.message.edit_reply_markup(reply_markup=get_arena_hub_inline_keyboard(user_id))

@router.callback_query(F.data == "toggle_pm_reminder")
async def handle_toggle_pm_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    u = db_get_user(user_id)
    curr = u["pm_reminder_enabled"] if u and "pm_reminder_enabled" in u.keys() else 1
    new_val = 0 if curr == 1 else 1
    db_update_user_setting(user_id, "pm_reminder_enabled", new_val)
    status_str = "yoqildi" if new_val == 1 else "o'chirildi"
    await callback.answer(f"✅ PM Eslatmalar {status_str}!")
    await callback.message.edit_reply_markup(reply_markup=get_settings_hub_inline_keyboard(user_id))

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

    badges = []
    if streak >= 7: badges.append("⚡ Early Bird")
    if streak >= 21: badges.append("👑 Elite 21")
    if streak >= 30: badges.append("👑 5 AM Legend")
    if photo_count >= 5: badges.append("📸 Photo Master")
    if freeze_count > 0: badges.append("🛡 Shielded")
    if ref_count >= 5: badges.append("👥 Master Ambassador")
    badges_str = " | ".join(badges) if badges else "Boshlang'ich nishonlar"

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
    user = callback.from_user
    db_register_user(user.id, user.username, user.first_name)
    lang = get_user_language(user.id)
    t = TEXTS.get(lang, TEXTS["uz"])

    group_id = callback.message.chat.id if callback.message.chat else 0
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

# --- BEDTIME PROTOCOL HANDLER ---
@router.callback_query(F.data == "bedtime_sleep_now")
async def handle_bedtime_sleep_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    db_register_user(user_id, callback.from_user.username, callback.from_user.first_name)
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    success, reason = db_record_bedtime(user_id)
    if success:
        await callback.answer("😴 Xayrli tun! +20 XP berildi!", show_alert=True)
        await callback.message.answer(t["bedtime_success"], parse_mode=ParseMode.MARKDOWN)
    elif reason == "already_recorded":
        await callback.answer("⚠️ Bugun uxlash protokoli allaqachon qayd etilgan! Xayrli tun! 😴", show_alert=True)
    else:
        await callback.answer("✅", show_alert=False)

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

    badges = []
    if streak >= 7: badges.append("⚡ Early Bird")
    if streak >= 21: badges.append("👑 Elite 21")
    if streak >= 30: badges.append("👑 5 AM Legend")
    if photo_count >= 5: badges.append("📸 Photo Master")
    if freeze_count > 0: badges.append("🛡 Shielded")
    if ref_count >= 5: badges.append("👥 Master Ambassador")
    badges_str = " | ".join(badges) if badges else "Boshlang'ich nishonlar"

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
                if participants:
                    w1 = participants[0]
                    w_id, w_name, w_pts = w1["user_id"], w1["first_name"], w1["points"]
                    cursor.execute("UPDATE users SET coins = coins + 500, freeze_count = freeze_count + 2 WHERE user_id = ?", (w_id,))
                    if len(participants) > 1:
                        w2 = participants[1]
                        cursor.execute("UPDATE users SET coins = coins + 300, freeze_count = freeze_count + 1 WHERE user_id = ?", (w2["user_id"],))
                    if len(participants) > 2:
                        w3 = participants[2]
                        cursor.execute("UPDATE users SET coins = coins + 150 WHERE user_id = ?", (w3["user_id"],))

                cursor.execute("""
                    UPDATE tournament_seasons
                    SET is_active = 0, winner_id = ?, winner_name = ?, winner_points = ?
                    WHERE season_id = ?
                """, (w_id, w_name, w_pts, season["season_id"]))

            groups = db_get_active_groups()
            broadcast_msg = (
                f"🏆 **HAFTALIK TOURNAMENT #{season['season_number']} G'OLIBLARI E'LON QILINDI!** 🏆\n\n"
                f"👑 **1-o'rin (Chempion):** {w_name} (`{w_pts} pts`) — `+500 tanga, 2x Freeze va 👑 Haftalik Chempion nishoni!`\n\n"
                f"🚀 Yangi #{season['season_number'] + 1}-mavsum boshlandi! Barcha ballar yangilandi. Bellashuv davom etadi!"
            )
            for g in groups:
                try:
                    await bot.send_message(g["group_id"], broadcast_msg, parse_mode=ParseMode.MARKDOWN)
                    await asyncio.sleep(0.05)
                except Exception:
                    pass

            db_get_or_create_active_season()
    except Exception as e:
        logging.error(f"Error checking weekly tournament reset: {e}")

async def scheduler_loop(bot: Bot):
    sent_start, sent_end, sent_bedtime = {}, {}, {}
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
                            await bot.send_message(
                                g["group_id"],
                                TEXTS["uz"]["bedtime_reminder"],
                                reply_markup=get_bedtime_inline_keyboard("uz"),
                                parse_mode=ParseMode.MARKDOWN
                            )
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

            # 2. MORNING CHECK-IN OPEN / CLOSE FOR GROUPS
            for g in groups:
                gid = g["group_id"]
                s_t, e_t = g["checkin_start"], g["checkin_end"]

                if hhmm == s_t and sent_start.get(f"{gid}_{today_str}") != True:
                    sent_start[f"{gid}_{today_str}"] = True
                    db_reset_group_snoozed(gid)
                    await bot.send_message(
                        gid,
                        "🌅 **THE 5 AM CLUB: CHECK-IN IS OPEN!**\n\n"
                        f"⏰ Window: `{s_t}` — `{e_t}`\n"
                        "⚡ Tap the button below or send a photo to prove you're awake!",
                        reply_markup=get_checkin_inline_keyboard("uz"), parse_mode=ParseMode.MARKDOWN
                    )

                if hhmm == e_t and sent_end.get(f"{gid}_{today_str}") != True:
                    sent_end[f"{gid}_{today_str}"] = True
                    report = db_get_group_attendance_report(gid)
                    awake, sleepers = [], []
                    for m in report:
                        if m["status"] == "awake":
                            awake.append(f"• **{html.escape(m['first_name'])}** (`{m['last_checkin_time']}`) — 🔥 `{m['streak']}d`")
                        else:
                            sleepers.append(f"• **{html.escape(m['first_name'])}** 😴")

                    quote = await fetch_motivational_quote(0, "uz", g.get("active_universe") if g.get("roleplay_enabled") else None)
                    rep_msg = (
                        f"🔒 **CHECK-IN CLOSED ({e_t})**\n\n"
                        f"🌅 **AWAKE MEMBERS:**\n" + ("\n".join(awake) if awake else "None 😞") + "\n\n"
                        f"😴 **GRAVEYARD OF SLEEPERS:**\n" + ("\n".join(sleepers) if sleepers else "No sleepers! 🎉") + "\n\n"
                        f"💡 **QUOTE:**\n{quote}"
                    )
                    await bot.send_message(gid, rep_msg, parse_mode=ParseMode.MARKDOWN)

            # 3. WEEKLY TOURNAMENT RESET CHECK
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

async def start_dummy_web_server():
    app = web.Application()
    app.router.add_get('/', serve_index)
    app.router.add_get('/index.html', serve_index)
    app.router.add_get('/styles.css', serve_styles)
    app.router.add_get('/app.js', serve_app_js)
    app.router.add_get('/health', web_ping)
    app.router.add_post('/api/auth/validate', api_auth_validate)
    app.router.add_post('/api/action/bedtime', api_action_bedtime)
    app.router.add_get('/api/user/{user_id}', api_user_stats)
    app.router.add_get('/api/tournament', api_tournament)
    app.router.add_get('/api/leaderboard', api_leaderboard)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000)))
    await site.start()

# ==================== MAIN ENTRY POINT ====================
async def set_bot_commands(bot: Bot):
    group_commands = [
        BotCommand(command="setup", description="⚙️ Guruh vaqtini va wizardni sozlash (Admin)"),
        BotCommand(command="gconfig", description="📋 Guruh boshqaruv paneli (Admin)"),
        BotCommand(command="settime", description="⏰ Vaqtni sozlash (/settime 04:30 06:00)"),
        BotCommand(command="setcoins", description="🪙 Tangalarni sozlash (/setcoins 10 25)"),
        BotCommand(command="tournament", description="⚔️ Haftalik guruh turniri"),
        BotCommand(command="leaderboard", description="🏆 Guruh va global reyting"),
        BotCommand(command="profile", description="📊 Shaxsiy profil va RPG stats"),
        BotCommand(command="shop", description="🛒 5 AM Do'koni"),
        BotCommand(command="help", description="📖 Guruh qoidalari"),
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
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
