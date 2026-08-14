import asyncio
import logging
import os
import random
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
import pytz
import aiohttp
from aiohttp import web
from PIL import Image, ImageDraw, ImageFont
import io

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
    Supports windows that span past midnight safely.
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
            # Handles overnight window (e.g. 23:00 to 06:00)
            return now_time >= start_time or now_time <= end_time
    except Exception as e:
        logging.error(f"Error checking time window ({start_str} - {end_str}): {e}")
        return True

# ==================== SMART PHOTO VERIFICATION (PILLOW) ====================
def verify_image_quality(image_bytes: bytes) -> tuple[bool, str]:
    """
    Analyzes brightness & color variance using Pillow.
    Rejects pitch black, camera-covered, or uniform blank photos.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        # Resize thumbnail to 100x100 for rapid statistical analysis
        thumb = img.resize((100, 100))
        pixels = list(thumb.getdata())

        brightnesses = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in pixels]
        avg_brightness = sum(brightnesses) / len(brightnesses)

        variance = sum((b - avg_brightness) ** 2 for b in brightnesses) / len(brightnesses)
        std_dev = variance ** 0.5

        logging.info(f"Photo verification metrics: Brightness={avg_brightness:.2f}, StdDev={std_dev:.2f}")

        # Dark threshold: < 26 (too dark/pitch black)
        # Variance threshold: < 10 (solid color/blank sheet)
        if avg_brightness < 26:
            return False, "dark"
        if std_dev < 10:
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

# ==================== MULTI-LANGUAGE DICTIONARY ====================
TEXTS = {
    "uz": {
        "welcome": '👋 **"The 5 AM Club" botiga xush kelibsiz, {name}!**\n\n“Ertalabki vaqtingizga egalik qiling. Hayotingizni yuksaltiring.”\n\n⚙️ Tugmalar va menyulardan foydalanish uchun quyidagi menyuni bosing:',
        "btn_checkin": "⚡ Solo Check-In",
        "btn_photo_checkin": "📸 Foto Check-In",
        "btn_games": "🎮 O'yinlar va Duyellar",
        "btn_shop": "🛒 Do'kon & Bozor",
        "btn_ref": "👥 Taklif Qilish (+100 Coin)",
        "btn_profile": "📊 Profilim",
        "btn_leaderboard": "🏆 Reyting",
        "btn_quote": "💡 Kun Iqtibosi",
        "btn_setup": "⚙️ Sozlamalar",
        "btn_lang": "🌐 Til / Language",
        "btn_help": "📖 Qoidalar",
        "btn_admin": "👑 Owner Admin Panel",
        "checkin_btn_inline": "⚡ CHECK-IN QILISH (MEN UYG'ONDIM)",
        "already_checked_in": "⚠️ Siz bugun allaqachon check-in qildingiz! Ertagacha! 🌅",
        "not_in_window": "⚠️ Hozir check-in vaqti emas! Uyg'onish vaqti: {start} - {end} 🌅",
        "photo_too_dark": "❌ Rasm juda qorong'u yoki talabga javob bermaydi! Iltimos, yorug'roq va aniq rasm yuboring! 📸",
        "solo_menu_title": "⚡ **SOLO CHECK-IN MENYUSI**\n\nErtalabki intizom va natijalaringizni boshqarish uchun kerakli bo'limni tanlang:",
        "btn_submenu_now": "⚡ Hozir Check-In Qilish",
        "btn_submenu_photo": "📸 Foto Check-In",
        "btn_submenu_time": "⏰ Vaqtni Sozlash",
        "btn_submenu_stats": "📊 Shaxsiy Statistika",
        "group_checkin_popup": "⚡ CHECK-IN MUVAFFAQIYATLI!\n🔥 Streak: {streak} kun | 🪙 +{coins} Tanga",
        "checkin_success": "⚡ **CHECK-IN MUVAFFAQIYATLI!**\n\n{quip}\n\n🔥 Streak: `{streak} kun` (Koeffitsiyent: `{multiplier}X`)\n🪙 Tangalar: `+{coins_earned}` (Jami: `{coins}`)\n🏅 Unvon: {rank}",
        "photo_mission_prompt": "📸 **KUNLIK FOTO TOPSHIRIQ:**\n\n{mission}\n\n📌 **Shart:** Rasm yuboring! Bot rasmingizga rasmiy **VERIFIED STAMP** muhrini bosib, tangalaringizni beradi! 🚀",
        "photo_success": "📸 **FOTO CHECK-IN VERIFIED! (+{coins_earned} COIN)**\n\n{quip}\n\n🔥 Streak: `{streak} kun` (Koeffitsiyent: `{multiplier}X`)\n🪙 Tangalar: `+{coins_earned}` (Jami: `{coins}`)\n🏅 Unvon: {rank}\n\n✨ *Yuqoridagi muhrlangan rasmni Story'ingizga joylashingiz mumkin!*",
        "profile_title": "👤 **FOYDALANUVCHI PROFILI**\n\n🏷 Ism: {name}\n🔥 Streak: `{streak} Kun` (Koeffitsiyent: `{multiplier}X`)\n🪙 Tangalar: `{coins}`\n👥 Taklif qilinganlar: `{ref_count} kishi`\n🛡 Streak Freeze: `{freeze_count} ta`\n📸 Foto Check-Inlar: `{photo_count} ta`\n🏅 Unvon: {rank}\n🌐 Til: `{lang_str}`\n⏰ Shaxsiy vaqt: `{start}` — `{end}`\n\n🏆 **TROPHY CABINET (NISHONLAR):**\n{badges}\n\n📈 **UNVON DARAJASI:**\n{progress_bar}",
        "ref_text": "👥 **DO'STLARNI TAKLIF QILISH VA TANGA ISHLASH**\n\nSizning shaxsiy taklif havolangiz:\n`{ref_link}`\n\n📌 **Qoida:** Har bir taklif qilgan do'stingiz uchun sizga ham, do'stingizga ham **+100 tanga** beriladi!\n\nJami taklif qilingan do'stlar: `{ref_count} kishi`",
        "leaderboard_title": "🏆 **THE 5 AM CLUB REYTING JADVALI** 🏆\n\n",
        "leaderboard_empty": "🏆 Reyting jadvali hozircha bo'sh.",
        "quote_title": "💡 **KUN HIKMATI**\n\n{quote}",
        "help_text": "📖 **THE 5 AM CLUB — QOIDALAR**\n\n1. **Ertalabki Check-In**: Uyg'onish vaqti oralig'ida check-in qiling.\n2. **⚡ Streak Multiplier**: Streak oshgani sari tangalar 2.0X gacha ko'payadi!\n3. **📸 Smart Foto Tasdiq**: Pillow orqali qorong'u/soxta rasmlar rad etiladi.\n4. **🏆 21 Kunlik Maraton**: 21 kun uzluksiz uyg'onsangiz rasmiy Oltin Sertifikat va 👑 Elite 21 nishonini olasiz!\n5. **👥 Taklif Tizimi**: Do'stlarni taklif qiling va +100 tangadan ishlang!",
        "lang_select": "🌐 **Iltimos, o'zingizga ma'qul tilni tanlang:**",
        "lang_updated": "✅ **Botingiz tili O'zbek tiliga o'zgartirildi!**",
        "shop_main": "🛒 **THE 5 AM CLUB DO'KONI VA BOZORI**\n\nSizning tangalaringiz: 🪙 `{coins} tanga`\n\nQaysi bo'limga kirmoqchisiz?",
        "shop_global": "🌐 **GLOBAL DO'KON (TIZIM MAHSULOTLARI)**\n\nSizning tangalaringiz: 🪙 `{coins}`\n\n1. 🛡 **Streak Freeze (Qalqon)** — `100 tanga`\n*(Uxlab qolganda Streakni 0 ga tushishdan 1 marta saqlaydi)*",
        "shop_buy_freeze_ok": "🎉 **Muvaffaqiyatli sotib olindi!** Sizda 1 ta 🛡 **Streak Freeze** qalqoni bor!",
        "shop_no_coins": "❌ **Tangalaringiz yetarli emas!** Sizda `{coins}` tanga bor.",
        "games_main": "🎮 **THE 5 AM CLUB O'YINLAR VA ARENA KATALOGI**\n\nO'zingizga ma'qul rejimni tanlang:\n\n⚔️ **1v1 Uyg'onish Dueli** — 50 coin tikib bellashish\n🤝 **Duo Combo** — Sherik bilan birga uyg'onib bonus olish\n🎲 **Random Matchmaking** — Tizimdan avtomatik begona sherik topish",
        "matchmaking_searching": "🎲 **RANDOM SHERIK QIDIRILMOQDA...**\n\nTizim sizga mos begona o'yinchini qidirmoqda. Sherik topilishi bilan bot xabar beradi!",
        "matchmaking_found": "🎉 **SHERIK TOPILDI!**\n\nSizning yangi Duo sherigingiz: `{partner_name}`!\nEndi ikkangiz ham erta uyg'onsangiz +50 bonus tanga olasiz! 🚀",
        "duo_title": "🤝 **DUO COMBO SHERIKLIK TIZIMI**",
        "duo_invite_prompt": "📌 **Sherik biriktirish uchun:** `/duo <sherik_id>` buyrug'ini yuboring!\nBirgalikda erta uyg'onib, har kuni **+50 bonus tanga** yuting! 🚀",
        "setup_group": "⚙️ **Guruh uyg'onish vaqti oralig'ini tanlang:**",
        "setup_user": "⚙️ **Shaxsiy uyg'onish vaqtingizni sozlang:**\nHozirgi vaqt: `{start}` — `{end}`",
        "setup_updated": "✅ **Uyg'onish vaqti muvaffaqiyatli o'zgartirildi:** `{start}` — `{end}` 🌅",
        "cert_congrats": "🏆 **TABRIKLAYMIZ! 21 KUNLIK MARATON YUKSAK ZAFARI!**\n\nSiz 21 kun uzluksiz soat 05:00 da uyg'onib, intizom maratonini muvaffaqiyatli yakunladingiz!\n\nSizga rasmiy **21-Day Discipline Certificate** hamda **👑 Elite 21** nishoni topshirildi!"
    },
    "ru": {
        "welcome": '👋 **Добро пожаловать в бот "The 5 AM Club", {name}!**\n\n«Владейте своим утром. Поднимите свою жизнь.»\n\n⚙️ Используйте меню ниже для навигации:',
        "btn_checkin": "⚡ Solo Check-In",
        "btn_photo_checkin": "📸 Фото Check-In",
        "btn_games": "🎮 Игры и Дуэли",
        "btn_shop": "🛒 Магазин и Рынок",
        "btn_ref": "👥 Пригласить (+100 Монет)",
        "btn_profile": "📊 Мой Профиль",
        "btn_leaderboard": "🏆 Рейтинг",
        "btn_quote": "💡 Цитата Дня",
        "btn_setup": "⚙️ Настройки",
        "btn_lang": "🌐 Til / Language",
        "btn_help": "📖 Правила",
        "btn_admin": "👑 Owner Admin Panel",
        "checkin_btn_inline": "⚡ СДЕЛАТЬ CHECK-IN (Я ПРОСНУЛСЯ)",
        "already_checked_in": "⚠️ Вы уже отметились сегодня! До завтра! 🌅",
        "not_in_window": "⚠️ Сейчас не время для check-in! Время подъема: {start} - {end} 🌅",
        "photo_too_dark": "❌ Фото слишком темное или не соответствует требованиям! Пожалуйста, отправьте более четкое фото! 📸",
        "solo_menu_title": "⚡ **МЕНЮ СОЛО CHECK-IN**\n\nВыберите действие для управления вашей утренней дисциплиной:",
        "btn_submenu_now": "⚡ Сделать Check-In Сейчас",
        "btn_submenu_photo": "📸 Фото Check-In",
        "btn_submenu_time": "⏰ Настройка Времени",
        "btn_submenu_stats": "📊 Личная Статистика",
        "group_checkin_popup": "⚡ CHECK-IN УСПЕШЕН!\n🔥 Стрик: {streak} дн. | 🪙 +{coins} Монет",
        "checkin_success": "⚡ **CHECK-IN УСПЕШЕН!**\n\n{quip}\n\n🔥 Стрик: `{streak} дней` (Множитель: `{multiplier}X`)\n🪙 Монеты: `+{coins_earned}` (Всего: `{coins}`)\n🏅 Ранг: {rank}",
        "photo_mission_prompt": "📸 **ЕЖЕДНЕВНОЕ ФОТО-ЗАДАНИЕ:**\n\n{mission}\n\n📌 **Условие:** Отправьте фото! Бот поставит официальную печать **VERIFIED STAMP**! 🚀",
        "photo_success": "📸 **ФОТО CHECK-IN ПОДТВЕРЖДЕН! (+{coins_earned} МОНЕТ)**\n\n{quip}\n\n🔥 Стрик: `{streak} дней` (Множитель: `{multiplier}X`)\n🪙 Монеты: `+{coins_earned}` (Всего: `{coins}`)\n🏅 Ранг: {rank}\n\n✨ *Вы можете выложить фото с печатью в Сторис!*",
        "profile_title": "👤 **ПРОФИЛЬ УЧАСТНИКА**\n\n🏷 Имя: {name}\n🔥 Стрик: `{streak} Дней` (Множитель: `{multiplier}X`)\n🪙 Монеты: `{coins}`\n👥 Приглашено: `{ref_count} чел`\n🛡 Защита Стрика: `{freeze_count} шт`\n📸 Фото Check-In: `{photo_count} раз`\n🏅 Ранг: {rank}\n🌐 Язык: `{lang_str}`\n⏰ Время: `{start}` — `{end}`\n\n🏆 **ВИТРИНА НАГРАД (TROPHY CABINET):**\n{badges}\n\n📈 **ПРОГРЕСС РАНГА:**\n{progress_bar}",
        "ref_text": "👥 **ПРИГЛАШАЙТЕ ДРУЗЕЙ И ЗАРАБАТЫВАЙТЕ МОНЕТЫ**\n\nВаша уникальная ссылка:\n`{ref_link}`\n\n📌 **Правило:** За каждого приглашенного друга вам и другу начисляется **+100 монет**!\n\nВсего приглашено: `{ref_count} чел`",
        "leaderboard_title": "🏆 **ТАБЛИЦА ЛИДЕРОВ THE 5 AM CLUB** 🏆\n\n",
        "leaderboard_empty": "🏆 Таблица лидеров пока пуста.",
        "quote_title": "💡 **МУДРОСТЬ ДНЯ**\n\n{quote}",
        "help_text": "📖 **THE 5 AM CLUB — ПРАВИЛА**\n\n1. **Утренний Check-In**: Отмечайтесь строго в заданное время.\n2. **⚡ Множитель Стрика**: Растет со временем до 2.0X!\n3. **📸 Smart Фото-Анализ**: Защита от темных и пустых фото.\n4. **🏆 21 Дневный Марафон**: Продержитесь 21 день и получите официальный Золотой Сертификат!\n5. **👥 Рефералы**: Приглашайте друзей и получайте +100 монет!",
        "lang_select": "🌐 **Пожалуйста, выберите удобный язык:**",
        "lang_updated": "✅ **Язык бота изменен на Русский!**",
        "shop_main": "🛒 **МАГАЗИН И РЫНОК THE 5 AM CLUB**\n\nВаши монеты: 🪙 `{coins} монет`\n\nВыберите раздел:",
        "shop_global": "🌐 **ГЛОБАЛЬНЫЙ МАГАЗИН**\n\nВаши монеты: 🪙 `{coins}`\n\n1. 🛡 **Streak Freeze** — `100 монет`\n*(Сохраняет Стрик при пропуске 1 дня)*",
        "shop_buy_freeze_ok": "🎉 **Успешно куплено!** У вас есть 1 🛡 **Streak Freeze**!",
        "shop_no_coins": "❌ **Недостаточно монет!** У вас `{coins}` монет.",
        "games_main": "🎮 **КАТАЛОГ ИГР И АРЕНА THE 5 AM CLUB**\n\nВыберите режим:\n\n⚔️ **Дуэль 1v1** — Ставка 50 монет на ранний подъем\n🤝 **Парный Комбо** — Совместный подъем для бонуса\n🎲 **Случайный подбор** — Автоматический поиск партнера",
        "matchmaking_searching": "🎲 **ПОИСК СЛУЧАЙНОГО ПАРТНЕРА...**\n\nСистема ищет игрока. Бот уведомит при подборе!",
        "matchmaking_found": "🎉 **ПАРТНЕР НАЙДЕН!**\n\nВаш новый партнер: `{partner_name}`!\nПросыпайтесь вовремя вместе и получайте +50 монет! 🚀",
        "duo_title": "🤝 **ПАРНЫЙ РЕЖИМ DUO COMBO**",
        "duo_invite_prompt": "📌 **Для привязки партнера:** отправьте команду `/duo <id_партнера>`!\nПросыпайтесь вовремя вместе и получайте **+50 бонусных монет** каждый день! 🚀",
        "setup_group": "⚙️ **Выберите временное окно подъема для группы:**",
        "setup_user": "⚙️ **Настройте ваше персональное время подъема:**\nТекущее время: `{start}` — `{end}`",
        "setup_updated": "✅ **Время подъема успешно обновлено:** `{start}` — `{end}` 🌅",
        "cert_congrats": "🏆 **ПОЗДРАВЛЯЕМ! ПОБЕДА В 21-ДНЕВНОМ МАРАФОНЕ!**\n\nВы просыпались в 5:00 утра 21 день подряд и успешно завершили марафон дисциплины!\n\nВам вручен официальный **21-Day Discipline Certificate** и знак отличия **👑 Elite 21**!"
    },
    "en": {
        "welcome": '👋 **Welcome to The 5 AM Club, {name}!**\n\n“Own your morning. Elevate your life.”\n\n⚙️ Use the menu below to navigate:',
        "btn_checkin": "⚡ Solo Check-In",
        "btn_photo_checkin": "📸 Photo Check-In",
        "btn_games": "🎮 Games & Duels",
        "btn_shop": "🛒 Shop & Market",
        "btn_ref": "👥 Invite Friends (+100 Coins)",
        "btn_profile": "📊 My Profile",
        "btn_leaderboard": "🏆 Leaderboard",
        "btn_quote": "💡 Daily Quote",
        "btn_setup": "⚙️ Time Setup",
        "btn_lang": "🌐 Til / Language",
        "btn_help": "📖 Help & Rules",
        "btn_admin": "👑 Owner Admin Panel",
        "checkin_btn_inline": "⚡ CHECK-IN NOW (I'M AWAKE)",
        "already_checked_in": "⚠️ You already checked in today! See you tomorrow! 🌅",
        "not_in_window": "⚠️ It's not check-in time right now! Wake-up window: {start} - {end} 🌅",
        "photo_too_dark": "❌ Image is too dark or does not meet requirements! Please send a brighter and clearer photo! 📸",
        "solo_menu_title": "⚡ **SOLO CHECK-IN SUBMENU**\n\nSelect an option below to manage your morning discipline:",
        "btn_submenu_now": "⚡ Check-In Now",
        "btn_submenu_photo": "📸 Photo Check-In",
        "btn_submenu_time": "⏰ Adjust Time",
        "btn_submenu_stats": "📊 Personal Stats",
        "group_checkin_popup": "⚡ CHECK-IN SUCCESSFUL!\n🔥 Streak: {streak} days | 🪙 +{coins} Coins",
        "checkin_success": "⚡ **CHECK-IN SUCCESSFUL!**\n\n{quip}\n\n🔥 Streak: `{streak} days` (Multiplier: `{multiplier}X`)\n🪙 Coins: `+{coins_earned}` (Total: `{coins}`)\n🏅 Rank: {rank}",
        "photo_mission_prompt": "📸 **DAILY PHOTO MISSION:**\n\n{mission}\n\n📌 **Condition:** Send a photo! The bot will apply an official **VERIFIED STAMP**! 🚀",
        "photo_success": "📸 **PHOTO CHECK-IN VERIFIED! (+{coins_earned} COINS)**\n\n{quip}\n\n🔥 Streak: `{streak} days` (Multiplier: `{multiplier}X`)\n🪙 Coins: `+{coins_earned}` (Total: `{coins}`)\n🏅 Rank: {rank}\n\n✨ *Feel free to share your stamped photo on Stories!*",
        "profile_title": "👤 **MEMBER PROFILE**\n\n🏷 Name: {name}\n🔥 Streak: `{streak} Days` (Multiplier: `{multiplier}X`)\n🪙 Coins: `{coins}`\n👥 Invited Friends: `{ref_count}`\n🛡 Streak Freezes: `{freeze_count}`\n📸 Photo Check-Ins: `{photo_count}`\n🏅 Rank: {rank}\n🌐 Language: `{lang_str}`\n⏰ Window: `{start}` — `{end}`\n\n🏆 **TROPHY CABINET:**\n{badges}\n\n📈 **RANK PROGRESSION:**\n{progress_bar}",
        "ref_text": "👥 **INVITE FRIENDS & EARN COINS**\n\nYour personal referral link:\n`{ref_link}`\n\n📌 **Rule:** Earn **+100 coins** for both you and your friend for every successful invite!\n\nTotal Invited: `{ref_count}` friends",
        "leaderboard_title": "🏆 **THE 5 AM CLUB LEADERBOARD** 🏆\n\n",
        "leaderboard_empty": "🏆 Leaderboard is currently empty.",
        "quote_title": "💡 **DAILY MORNING WISDOM**\n\n{quote}",
        "help_text": "📖 **THE 5 AM CLUB — RULES & GUIDELINES**\n\n1. **Morning Check-In**: Check in strictly within your wake-up window.\n2. **⚡ Streak Multiplier**: Earn up to 2.0X coins as your streak grows!\n3. **📸 Smart Photo Verification**: Pillow filters out blank/dark images.\n4. **🏆 21-Day Challenge**: Complete 21 days for an official Golden Certificate!\n5. **👥 Referral System**: Invite friends to earn +100 coins!",
        "lang_select": "🌐 **Please select your preferred language:**",
        "lang_updated": "✅ **Bot language updated to English!**",
        "shop_main": "🛒 **THE 5 AM CLUB MARKETPLACE**\n\nYour Balance: 🪙 `{coins} coins`\n\nSelect a section below:",
        "shop_global": "🌐 **GLOBAL SHOP**\n\nYour Balance: 🪙 `{coins}`\n\n1. 🛡 **Streak Freeze Shield** — `100 coins`\n*(Protects your streak if you miss 1 day)*",
        "shop_buy_freeze_ok": "🎉 **Purchase Successful!** You have 1 🛡 **Streak Freeze** shield!",
        "shop_no_coins": "❌ **Insufficient coins!** You have `{coins}` coins.",
        "games_main": "🎮 **THE 5 AM CLUB GAMES & ARENA**\n\nSelect a game mode below:\n\n⚔️ **1v1 Wake-Up Duel** — Bet 50 coins on waking up early\n🤝 **Duo Combo** — Team up for daily bonus coins\n🎲 **Random Matchmaking** — Find a random player instantly",
        "matchmaking_searching": "🎲 **SEARCHING FOR RANDOM PARTNER...**\n\nThe system is matching you with another player. You will be notified!",
        "matchmaking_found": "🎉 **PARTNER FOUND!**\n\nYour new Duo Partner: `{partner_name}`!\nWake up early together to earn +50 bonus coins! 🚀",
        "duo_title": "🤝 **DUO COMBO PARTNER SYSTEM**",
        "duo_invite_prompt": "📌 **To link a partner:** send `/duo <partner_id>` command!\nWake up early together and earn **+50 bonus coins** every single day! 🚀",
        "setup_group": "⚙️ **Select the check-in time window for the group:**",
        "setup_user": "⚙️ **Customize your personal morning check-in window:**\nCurrent window: `{start}` — `{end}`",
        "setup_updated": "✅ **Morning check-in window successfully updated:** `{start}` — `{end}` 🌅",
        "cert_congrats": "🏆 **CONGRATULATIONS! 21-DAY MARATHON VICTORY!**\n\nYou woke up at 5:00 AM for 21 consecutive days and mastered morning discipline!\n\nYou have been awarded the official **21-Day Discipline Certificate** and **👑 Elite 21** badge!"
    }
}

# ==================== INFINITE DYNAMIC QUIPS & ROLEPLAY TITLES ====================
ROLEPLAY_TITLES = {
    "uz": ["🦁 Tonggi Arslon", "🦅 Lochin Nigoh", "⚡ Cha chaqmoq", "👑 Sahar Qiroli", "🌄 Tonggi Chempion", "⚔️ Intizom Bahodiri", "🚀 Koinot Sayyohi", "🏆 Oltin Qaqnus"],
    "ru": ["🦁 Утренний Лев", "🦅 Соколиный Взор", "⚡ Утренняя Молния", "👑 Король Рассвета", "🌄 Чемпион Утра", "⚔️ Богатырь Дисциплины", "🚀 Покоритель Рассвета", "🏆 Золотой Феникс"],
    "en": ["🦁 Morning Lion", "🦅 Falcon Eye", "⚡ Morning Lightning", "👑 Dawn King", "🌄 Morning Champion", "⚔️ Discipline Warrior", "🚀 Dawn Voyager", "🏆 Golden Phoenix"]
}

DYNAMIC_QUIPS = {
    "uz": [
        "Qarang, kim erta uyg'ondi! Kofe siz bilan faxrlanadi! ☕🔥",
        "Quyoshdan oldin uyg'ondingiz-a! Haqiqiy arslon intizomi! 🦁⚡",
        "Krovat sizni tutqinlikda ushlab turmoqchi edi, lekin iroda g'olib chiqdi! ⚔️😎",
        "Ertalabki g'alaba bilan tabriklayman! Bugungi kun sizniki! 🚀",
        "Hatto budilnigingiz ham sizning intizomingizdan hayratda! ⏰🔥",
        "Dunyo uxlayotganda g'oliblar o'z kelajagini quradi! 🌟💪",
        "Robin Sharma aytganidek: 'Tonggi g'alaba — kunlik muvaffaqiyat garovidir!' 📖✨",
        "Bunday sur'atda sizni hech narsa to'xtata olmaydi! 🦅🔥"
    ],
    "ru": [
        "Смотрите, кто проснулся раньше всех! Кофе гордится тобой! ☕🔥",
        "Проснулся раньше солнца! Настоящий режим льва! 🦁⚡",
        "Кровать пыталась удержать тебя, но дисциплина победила! ⚔️😎",
        "Поздравляем с утренней победой! Этот день полностью твой! 🚀",
        "Даже твой будильник в шоке от твоей пунктуальности! ⏰🔥",
        "Пока весь мир спит, чемпионы куют свое великое будущее! 🌟💪",
        "Как писал Робин Шарма: 'Владей своим утром — владей своей судьбой!' 📖✨",
        "С таким невероятным темпом тебя ничто не остановит! 🦅🔥"
    ],
    "en": [
        "Look who decided to rise and conquer! Coffee is proud! ☕🔥",
        "Woke up before the sun! Absolute beast mode activated! 🦁⚡",
        "The bed tried to hold you hostage, but iron discipline won! ⚔️😎",
        "Congrats on the morning victory! Today belongs to you! 🚀",
        "Even your alarm clock is shocked by your consistency! ⏰🔥",
        "While the world sleeps, champions forge their empire! 🌟💪",
        "As Robin Sharma said: 'Own your morning, elevate your life!' 📖✨",
        "Unstoppable momentum! Keep pushing past limits! 🦅🔥"
    ]
}

async def fetch_dynamic_quip(streak: int, name: str, lang: str = "uz") -> str:
    titles = ROLEPLAY_TITLES.get(lang, ROLEPLAY_TITLES["uz"])
    quips_list = DYNAMIC_QUIPS.get(lang, DYNAMIC_QUIPS["uz"])
    role_title = random.choice(titles)
    base_joke = random.choice(quips_list)

    # Optional dynamic online affirmation fetch
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.affirmations.dev/", timeout=aiohttp.ClientTimeout(total=1.5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    aff = data.get("affirmation", "")
                    if aff and lang == "en":
                        return f"{role_title} **{name}**: {base_joke}\n✨ *Affirmation:* {aff}"
    except Exception:
        pass

    if streak >= 30:
        return f"👑 **LEGEND ({streak} Days) — {role_title}:**\n{base_joke}"
    elif streak >= 10:
        return f"🔥 **STREAK MONSTER ({streak} Days) — {role_title}:**\n{base_joke}"
    else:
        return f"⚡ **{role_title} ({name}):**\n{base_joke}"

MOTIVATIONAL_QUOTES = {
    "uz": [
        "“Ertalabki vaqtingizga egalik qiling. Hayotingizni yuksaltiring.” – Robin Sharma",
        "“G'alabalar tong otmasdan, sukunat va intizomda yaratiladi.” – Robin Sharma",
        "“Daqiqalarga e'tibor bering, soatlar o'z-o'zidan tartibga tushadi.” – Lord Chesterfield",
        "“Oldinga siljishning siri — boshlashdir.” – Mark Tven",
        "“Intizom — bu hozir xohlagan narsangiz bilan eng ko'p xohlagan narsangiz o'rtasidagi tanlovdir.” – Avraam Linkoln",
        "“Kichik kunlik o'sishlar vaqt o'tishi bilan aql bovar qilmas natijalarga olib keladi.” – Robin Sharma"
    ],
    "ru": [
        "«Владейте своим утром. Поднимите свою жизнь.» – Робин Шарма",
        "«Победы куются до рассвета, в тишине железной дисциплины.» – Робин Шарма",
        "«Позаботьтесь о минутах, и часы позаботятся о себе сами.» – Лорд Честерфилд",
        "«Секрет того, чтобы вырваться вперед — это начать.» – Марк Твен",
        "«Дисциплина — это решение делать то, чего не хочется делать, чтобы достичь того, чего очень хочется.»",
        "«Маленькие ежедневные улучшения со временем приводят к потрясающим результатам.»"
    ],
    "en": [
        "“Own your morning. Elevate your life.” – Robin Sharma",
        "“Victories are created before dawn, in the quiet solitude of discipline.” – Robin Sharma",
        "“Take care of the minutes and the hours will take care of themselves.” – Lord Chesterfield",
        "“The secret of getting ahead is getting started.” – Mark Twain",
        "“Discipline is choosing between what you want now and what you want most.” – Abraham Lincoln",
        "“Small daily improvements over time lead to stunning results.” – Robin Sharma"
    ]
}

async def fetch_motivational_quote(lang: str = "uz") -> str:
    fallback = MOTIVATIONAL_QUOTES.get(lang, MOTIVATIONAL_QUOTES["uz"])
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://zenquotes.io/api/random", timeout=aiohttp.ClientTimeout(total=2.5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        if lang == "en":
                            return f"“{data[0]['q']}”\n— *{data[0]['a']}*"
    except Exception:
        pass
    return random.choice(fallback)

# ==================== PHOTO STAMPING ENGINE ====================
def stamp_photo_with_watermark(image_bytes: bytes, name: str, streak: int, rank: str) -> bytes:
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        width, height = img.size

        banner_height = int(height * 0.12)
        if banner_height < 60:
            banner_height = 60

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

# ==================== 21-DAY CERTIFICATE GENERATOR ====================
def generate_21day_certificate(name: str) -> bytes:
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

# ==================== STREAK MULTIPLIER ENGINE ====================
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

# ==================== DATABASE INITIALIZATION & OPERATIONS ====================
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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                title TEXT,
                checkin_start TEXT DEFAULT '04:30',
                checkin_end TEXT DEFAULT '06:00',
                normal_coins INTEGER DEFAULT 10,
                photo_coins INTEGER DEFAULT 25,
                timezone TEXT DEFAULT 'Asia/Tashkent',
                is_active INTEGER DEFAULT 1
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

def db_register_user(user_id: int, username: str, first_name: str, ref_by: int = 0):
    with get_db() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        existing = cursor.fetchone()

        if not existing:
            initial_coins = 100 if ref_by and ref_by != user_id else 0
            cursor.execute("""
                INSERT INTO users (user_id, username, first_name, coins, referred_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, username or "", first_name or "Member", initial_coins, ref_by, now_str))

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

def db_update_user_lang(user_id: int, lang: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))

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

        partner_id = user["duo_partner_id"]
        if partner_id and partner_id != 0:
            cursor.execute("SELECT last_checkin_date FROM users WHERE user_id = ?", (partner_id,))
            p_row = cursor.fetchone()
            if p_row and p_row["last_checkin_date"] == today_str:
                coins_earned += 50

        new_coins = user["coins"] + coins_earned
        new_photo_count = user["photo_count"] + (1 if is_photo else 0)

        cursor.execute("""
            UPDATE users 
            SET streak = ?, coins = ?, photo_count = ?, last_checkin_date = ?, status = 'awake'
            WHERE user_id = ?
        """, (new_streak, new_coins, new_photo_count, today_str, user_id))

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

        return {
            "streak": new_streak,
            "multiplier": multiplier,
            "coins": new_coins,
            "photo_count": new_photo_count,
            "coins_earned": coins_earned,
            "checkin_time": time_str
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
        cursor.execute("SELECT first_name, username, streak, coins FROM users ORDER BY streak DESC, coins DESC LIMIT ?", (limit,))
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

def get_user_language(user_id: int) -> str:
    user = db_get_user(user_id)
    if user and "lang" in user.keys() and user["lang"]:
        return user["lang"]
    return "uz"

# ==================== KEYBOARDS ====================
def get_main_reply_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    buttons = [
        [KeyboardButton(text=t["btn_checkin"]), KeyboardButton(text=t["btn_photo_checkin"])],
        [KeyboardButton(text=t["btn_games"]), KeyboardButton(text=t["btn_shop"])],
        [KeyboardButton(text=t["btn_ref"]), KeyboardButton(text=t["btn_profile"])],
        [KeyboardButton(text=t["btn_leaderboard"]), KeyboardButton(text=t["btn_quote"])],
        [KeyboardButton(text=t["btn_setup"]), KeyboardButton(text=t["btn_lang"]), KeyboardButton(text=t["btn_help"])]
    ]
    if user_id == SUPER_ADMIN_ID:
        buttons.append([KeyboardButton(text=t["btn_admin"])])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_solo_checkin_submenu_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["uz"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["btn_submenu_now"], callback_data="solo_do_checkin")],
        [InlineKeyboardButton(text=t["btn_submenu_photo"], callback_data="solo_photo_checkin")],
        [InlineKeyboardButton(text=t["btn_submenu_time"], callback_data="solo_setup_time")],
        [InlineKeyboardButton(text=t["btn_submenu_stats"], callback_data="solo_my_stats")]
    ])

def get_checkin_inline_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["uz"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["checkin_btn_inline"], callback_data="do_checkin")]
    ])

def get_games_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Random Sherik Topish (Matchmaking)", callback_data="game_matchmaking")],
        [InlineKeyboardButton(text="🤝 Duo Combo (Sherik Taklif Qilish)", callback_data="game_duo_info")],
        [InlineKeyboardButton(text="⚔️ 1v1 Uyg'onish Dueli (50 Coin Tikish)", callback_data="game_1v1_info")]
    ])

def get_language_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="set_lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en")
        ]
    ])

def get_shop_main_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Global Do'kon (Tizim)", callback_data="shop_global")],
        [InlineKeyboardButton(text="🛡 Streak Freeze Olish (100 Coin)", callback_data="buy_freeze")]
    ])

def get_group_config_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏰ Vaqt: 04:30 - 06:00", callback_data="set_time_grp_04:30_06:00"),
            InlineKeyboardButton(text="⏰ Vaqt: 05:00 - 07:00", callback_data="set_time_grp_05:00_07:00")
        ],
        [
            InlineKeyboardButton(text="🪙 Tangalar: 10 / 25 Coin", callback_data="set_coins_grp_10_25"),
            InlineKeyboardButton(text="🪙 Tangalar: 15 / 35 Coin", callback_data="set_coins_grp_15_35")
        ]
    ])

def get_setup_keyboard(is_group: bool = True) -> InlineKeyboardMarkup:
    prefix = "set_time_grp_" if is_group else "set_time_usr_"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="04:30 - 05:30", callback_data=f"{prefix}04:30_05:30"),
            InlineKeyboardButton(text="04:30 - 06:00", callback_data=f"{prefix}04:30_06:00")
        ],
        [
            InlineKeyboardButton(text="05:00 - 06:00", callback_data=f"{prefix}05:00_06:00"),
            InlineKeyboardButton(text="05:00 - 07:00", callback_data=f"{prefix}05:00_07:00")
        ]
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
    lang = get_user_language(user.id)
    t = TEXTS.get(lang, TEXTS["uz"])

    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        db_register_group(message.chat.id, message.chat.title)
        db_link_group_member(message.chat.id, user.id)
        await message.reply("🌅 **The 5 AM Club Bot is Active!** Group members auto-registered.", parse_mode=ParseMode.MARKDOWN)
    else:
        welcome_text = t["welcome"].format(name=user.first_name)
        await message.answer(welcome_text, reply_markup=get_main_reply_keyboard(user.id), parse_mode=ParseMode.MARKDOWN)

# --- SOLO CHECK-IN & SUBMENU HANDLERS ---
@router.message(F.text.in_(["⚡ Solo Check-In", "⚡ Соло Check-In"]))
@router.message(Command("checkin"))
async def handle_solo_checkin_submenu(message: Message):
    user_id = message.from_user.id
    db_register_user(user_id, message.from_user.username, message.from_user.first_name)
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    await message.reply(
        t["solo_menu_title"],
        reply_markup=get_solo_checkin_submenu_keyboard(lang),
        parse_mode=ParseMode.MARKDOWN
    )

@router.callback_query(F.data == "solo_do_checkin")
async def handle_solo_do_checkin_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    db_register_user(user_id, callback.from_user.username, callback.from_user.first_name)
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    u = db_get_user(user_id)
    start_t = u["checkin_start"] if u and "checkin_start" in u.keys() and u["checkin_start"] else "04:30"
    end_t = u["checkin_end"] if u and "checkin_end" in u.keys() and u["checkin_end"] else "06:00"

    # Strict Time-Window Enforcement
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

        quip = await fetch_dynamic_quip(res["streak"], callback.from_user.first_name, lang=lang)
        rank = get_user_rank(res["streak"], lang=lang)
        msg_text = t["checkin_success"].format(
            quip=quip,
            streak=res["streak"],
            multiplier=res["multiplier"],
            coins_earned=res["coins_earned"],
            coins=res["coins"],
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

@router.callback_query(F.data == "solo_setup_time")
async def handle_solo_setup_time_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])
    u = db_get_user(user_id)
    start_t = u["checkin_start"] if u and "checkin_start" in u.keys() and u["checkin_start"] else "04:30"
    end_t = u["checkin_end"] if u and "checkin_end" in u.keys() and u["checkin_end"] else "06:00"

    await callback.answer()
    await callback.message.answer(
        t["setup_user"].format(start=start_t, end=end_t),
        reply_markup=get_setup_keyboard(is_group=False),
        parse_mode=ParseMode.MARKDOWN
    )

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
    photo_count = user["photo_count"] if "photo_count" in user.keys() else 0
    freeze_count = user["freeze_count"] if "freeze_count" in user.keys() else 0
    ref_count = user["referral_count"] if "referral_count" in user.keys() else 0
    rank = get_user_rank(streak, lang=lang)
    progress_bar = generate_progress_bar(streak, lang=lang)
    lang_names = {"uz": "🇺🇿 O'zbekcha", "ru": "🇷🇺 Русский", "en": "🇬🇧 English"}
    start_t = user["checkin_start"] if "checkin_start" in user.keys() and user["checkin_start"] else "04:30"
    end_t = user["checkin_end"] if "checkin_end" in user.keys() and user["checkin_end"] else "06:00"

    badges = []
    if streak >= 7: badges.append("⚡ Early Bird")
    if streak >= 21: badges.append("👑 Elite 21")
    if streak >= 30: badges.append("👑 5 AM Legend")
    if photo_count >= 5: badges.append("📸 Photo Master")
    if freeze_count > 0: badges.append("🛡 Shielded")
    if ref_count >= 5: badges.append("👥 Master Ambassador")
    badges_str = " | ".join(badges) if badges else "Boshlang'ich nishonlar"

    profile_text = t["profile_title"].format(
        name=user['first_name'],
        streak=streak,
        multiplier=get_streak_multiplier(streak),
        coins=coins,
        ref_count=ref_count,
        freeze_count=freeze_count,
        photo_count=photo_count,
        rank=rank,
        start=start_t,
        end=end_t,
        badges=badges_str,
        lang_str=lang_names.get(lang, "🇺🇿 O'zbekcha"),
        progress_bar=progress_bar
    )
    await callback.message.answer(profile_text, parse_mode=ParseMode.MARKDOWN)

# --- GROUP INLINE BUTTON CHECK-IN WITH COMPACT POPUP ALERT ---
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

    # Strict Time-Window Enforcement
    if not is_time_in_window(start_t, end_t):
        warning_msg = t["not_in_window"].format(start=start_t, end=end_t)
        await callback.answer(warning_msg, show_alert=True)
        return

    res = db_process_checkin(user.id, group_id=group_id, is_photo=False)

    if res == "already":
        await callback.answer(t["already_checked_in"], show_alert=True)
    elif res:
        # Compact Group Popup Alert (Item 2 Requirement)
        popup_text = t["group_checkin_popup"].format(streak=res['streak'], coins=res['coins_earned'])
        await callback.answer(popup_text, show_alert=True)

        try:
            chosen_emoji = random.choice(["🔥", "⚡", "🦅", "🏆", "🎉", "💪", "👍"])
            await callback.message.react(reaction=[ReactionTypeEmoji(emoji=chosen_emoji)])
        except Exception:
            pass

        # In private chats only, send full detailed confirmation
        if group_id == 0:
            quip = await fetch_dynamic_quip(res["streak"], user.first_name, lang=lang)
            rank = get_user_rank(res["streak"], lang=lang)
            msg_text = t["checkin_success"].format(
                quip=quip,
                streak=res["streak"],
                multiplier=res["multiplier"],
                coins_earned=res["coins_earned"],
                coins=res["coins"],
                rank=rank
            )
            await callback.message.answer(msg_text, parse_mode=ParseMode.MARKDOWN)

# --- REFERRAL HANDLER ---
@router.message(F.text.in_(["👥 Taklif Qilish (+100 Coin)", "👥 Пригласить (+100 Монет)", "👥 Invite Friends (+100 Coins)"]))
@router.message(Command("ref"))
async def handle_referral_btn(message: Message):
    user_id = message.from_user.id
    user = db_get_user(user_id)
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    ref_count = user["referral_count"] if user and "referral_count" in user.keys() else 0

    msg = t["ref_text"].format(ref_link=ref_link, ref_count=ref_count)
    await message.answer(msg, parse_mode=ParseMode.MARKDOWN)

# --- GAMES & ARENA CATALOG HANDLERS ---
@router.message(F.text.in_(["🎮 O'yinlar va Duyellar", "🎮 Игры и Дуэли", "🎮 Games & Duels"]))
async def handle_games_catalog_btn(message: Message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    await message.answer(t["games_main"], reply_markup=get_games_inline_keyboard(), parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data == "game_matchmaking")
async def handle_matchmaking_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    partner_id, partner_name = db_matchmaking_find_or_enqueue(user_id)
    if partner_id:
        await callback.message.edit_text(t["matchmaking_found"].format(partner_name=partner_name), parse_mode=ParseMode.MARKDOWN)
        try:
            await callback.bot.send_message(partner_id, t["matchmaking_found"].format(partner_name=callback.from_user.first_name), parse_mode=ParseMode.MARKDOWN)
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
        "Do'stingiz bilan 50 tanga tikib bellashing! Kim ertalab birinchi foto check-in qilsa, **100 tangalik bank**ni yutib oladi!\n\n"
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
@router.message(F.text.in_(["🛒 Do'kon & Bozor", "🛒 Магазин и Рынок", "🛒 Shop & Market"]))
@router.message(Command("shop"))
async def handle_shop_main(message: Message):
    user_id = message.from_user.id
    user = db_get_user(user_id)
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])
    coins = user["coins"] if user else 0

    await message.answer(t["shop_main"].format(coins=coins), reply_markup=get_shop_main_inline_keyboard(), parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data == "shop_global")
async def handle_shop_global_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = db_get_user(user_id)
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])
    coins = user["coins"] if user else 0

    await callback.message.edit_text(t["shop_global"].format(coins=coins), reply_markup=get_shop_main_inline_keyboard(), parse_mode=ParseMode.MARKDOWN)

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

# --- INTERACTIVE GROUP ADMIN CONFIGURATION HANDLERS ---
@router.message(Command("gconfig"))
async def cmd_group_config_interactive(message: Message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ Bu buyruq faqat guruhlar uchun.")
        return

    member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR] and message.from_user.id != SUPER_ADMIN_ID:
        await message.reply("⛔ Bu buyruq faqat guruh adminlari uchun!")
        return

    g = db_get_group(message.chat.id)
    if not g:
        db_register_group(message.chat.id, message.chat.title)
        g = db_get_group(message.chat.id)

    s_t = g["checkin_start"] if "checkin_start" in g.keys() else "04:30"
    e_t = g["checkin_end"] if "checkin_end" in g.keys() else "06:00"
    n_c = g["normal_coins"] if "normal_coins" in g.keys() else 10
    p_c = g["photo_coins"] if "photo_coins" in g.keys() else 25

    msg = (
        f"⚙️ **GURUH SOZLAMALARI (INTERAKTIV PANEL):**\n\n"
        f"👥 Guruh: **{g['title']}**\n"
        f"⏰ Check-In Vaqti: `{s_t}` — `{e_t}`\n"
        f"⚡ Oddiy Check-In: `+{n_c} tanga`\n"
        f"📸 Foto Check-In: `+{p_c} tanga`\n\n"
        f"👇 **Sozlash uchun quyidagi tugmalardan birini bosing:**"
    )
    await message.reply(msg, reply_markup=get_group_config_inline_keyboard(), parse_mode=ParseMode.MARKDOWN)

@router.message(Command("settime"))
async def cmd_set_time(message: Message):
    args = message.text.split()
    if len(args) != 3:
        await message.reply("ℹ️ **Foydalanish:** `/settime <boshlanish> <tugash>`\n*Misol:* `/settime 04:30 06:00`", parse_mode=ParseMode.MARKDOWN)
        return

    start_t, end_t = args[1], args[2]
    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR] and message.from_user.id != SUPER_ADMIN_ID:
            await message.reply("⛔ Bu buyruq faqat guruh adminlari uchun!")
            return
        db_register_group(message.chat.id, message.chat.title)
        db_update_group_times(message.chat.id, start_t, end_t)
        await message.reply(f"✅ **Guruh uyg'onish vaqti yangilandi:** `{start_t}` — `{end_t}` 🌅", parse_mode=ParseMode.MARKDOWN)
    else:
        db_register_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        db_update_user_times(message.from_user.id, start_t, end_t)
        await message.reply(f"✅ **Shaxsiy uyg'onish vaqtingiz yangilandi:** `{start_t}` — `{end_t}` 🌅", parse_mode=ParseMode.MARKDOWN)

@router.message(Command("setcoins"))
async def cmd_set_coins(message: Message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ Bu buyruq faqat guruhlar uchun.")
        return

    member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR] and message.from_user.id != SUPER_ADMIN_ID:
        await message.reply("⛔ Bu buyruq faqat guruh adminlari uchun!")
        return

    args = message.text.split()
    if len(args) != 3:
        await message.reply("ℹ️ **Foydalanish:** `/setcoins <oddiy_tanga> <foto_tanga>`\n*Misol:* `/setcoins 15 35`", parse_mode=ParseMode.MARKDOWN)
        return

    try:
        normal_c, photo_c = int(args[1]), int(args[2])
        db_register_group(message.chat.id, message.chat.title)
        db_update_group_coins(message.chat.id, normal_c, photo_c)
        await message.reply(f"✅ **Guruh tangalari yangilandi:**\n⚡ Oddiy: `+{normal_c}` | 📸 Foto: `+{photo_c}`", parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await message.reply("❌ Noto'g'ri qiymatlar kiritildi.")

@router.callback_query(F.data.startswith("set_coins_grp_"))
async def handle_set_coins_grp_cb(callback: CallbackQuery):
    user_id = callback.from_user.id
    member = await callback.bot.get_chat_member(callback.message.chat.id, user_id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR] and user_id != SUPER_ADMIN_ID:
        await callback.answer("⛔ Bu tugmani faqat guruh admini bosishi mumkin!", show_alert=True)
        return

    parts = callback.data.split("_")
    normal_c, photo_c = int(parts[3]), int(parts[4])
    group_id = callback.message.chat.id
    db_register_group(group_id, callback.message.chat.title or "5 AM Club Group")
    db_update_group_coins(group_id, normal_c, photo_c)

    await callback.answer("✅ Tangalar sozlandi!", show_alert=False)
    await callback.message.edit_text(
        f"✅ **Guruh Tangalari Yangilandi!**\n\n⚡ Oddiy Check-In: `+{normal_c} tanga`\n📸 Foto Check-In: `+{photo_c} tanga`",
        parse_mode=ParseMode.MARKDOWN
    )

# --- PHOTO CHECK-IN PROMPT & SMART VERIFICATION ---
@router.message(F.text.in_(["📸 Foto Check-In", "📸 Фото Check-In", "📸 Photo Check-In"]))
async def handle_photo_checkin_btn(message: Message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])
    mission = get_random_photo_mission(lang)

    prompt = t["photo_mission_prompt"].format(mission=mission)
    await message.answer(prompt, parse_mode=ParseMode.MARKDOWN)

@router.message(F.photo)
async def handle_user_photo(message: Message):
    user = message.from_user
    db_register_user(user.id, user.username, user.first_name)
    lang = get_user_language(user.id)
    t = TEXTS.get(lang, TEXTS["uz"])

    group_id = message.chat.id if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] else 0
    if group_id != 0:
        db_link_group_member(group_id, user.id)
        g = db_get_group(group_id)
        start_t = g["checkin_start"] if g and "checkin_start" in g.keys() and g["checkin_start"] else "04:30"
        end_t = g["checkin_end"] if g and "checkin_end" in g.keys() and g["checkin_end"] else "06:00"
    else:
        u = db_get_user(user.id)
        start_t = u["checkin_start"] if u and "checkin_start" in u.keys() and u["checkin_start"] else "04:30"
        end_t = u["checkin_end"] if u and "checkin_end" in u.keys() and u["checkin_end"] else "06:00"

    # Strict Time-Window Enforcement
    if not is_time_in_window(start_t, end_t):
        await message.reply(t["not_in_window"].format(start=start_t, end=end_t), parse_mode=ParseMode.MARKDOWN)
        return

    # Download Photo and run Smart Photo Verification (Pillow)
    photo_file = message.photo[-1]
    file_info = await message.bot.get_file(photo_file.file_id)
    photo_bytes_io = await message.bot.download_file(file_info.file_path)
    photo_bytes = photo_bytes_io.read()

    is_valid_img, _ = verify_image_quality(photo_bytes)
    if not is_valid_img:
        await message.reply(t["photo_too_dark"], parse_mode=ParseMode.MARKDOWN)
        return

    res = db_process_checkin(user.id, group_id=group_id, is_photo=True)

    if res == "already":
        await message.reply(t["already_checked_in"], parse_mode=ParseMode.MARKDOWN)
        return

    rank = get_user_rank(res["streak"], lang=lang)

    stamped_bytes = stamp_photo_with_watermark(photo_bytes, user.first_name, res["streak"], rank)
    input_file = BufferedInputFile(stamped_bytes, filename="verified_stamp.jpg")

    quip = await fetch_dynamic_quip(res["streak"], user.first_name, lang=lang)
    caption_text = t["photo_success"].format(
        quip=quip,
        streak=res["streak"],
        multiplier=res["multiplier"],
        coins_earned=res["coins_earned"],
        coins=res["coins"],
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

    # 21-Day Challenge Certificate Check!
    if res["streak"] >= 21:
        u_info = db_get_user(user.id)
        if u_info and ("cert_issued" not in u_info.keys() or u_info["cert_issued"] == 0):
            cert_bytes = generate_21day_certificate(user.first_name)
            if cert_bytes:
                cert_file = BufferedInputFile(cert_bytes, filename="21day_certificate.jpg")
                cert_caption = t["cert_congrats"]
                await message.answer_photo(photo=cert_file, caption=cert_caption, parse_mode=ParseMode.MARKDOWN)
                db_set_cert_issued(user.id)

@router.callback_query(F.data == "story_share_tip")
async def handle_story_share_tip(callback: CallbackQuery):
    msg = (
        "📲 **STORY'GA JOYLASH VA DO'STLARNI HAYRATDA QOLDIRISH:**\n\n"
        "1. Yuqoridagi **VERIFIED STAMP** urilgan rasmni saqlab oling (Save to Gallery).\n"
        "2. Telegram yoki Instagram Story'ingizga joylang!\n"
        "3. Do'stlaringizga intizomingizni ko'rsatib, bot havolangizni qoldiring! 🚀"
    )
    await callback.answer()
    await callback.message.answer(msg, parse_mode=ParseMode.MARKDOWN)

# --- LANGUAGE SETUP ---
@router.message(Command("lang"))
@router.message(F.text.in_(["🌐 Til / Language", "🌐 Язык / Language", "🌐 Language / Til"]))
async def cmd_language(message: Message):
    lang = get_user_language(message.from_user.id)
    t = TEXTS.get(lang, TEXTS["uz"])
    await message.answer(t["lang_select"], reply_markup=get_language_inline_keyboard(), parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data.startswith("set_lang_"))
async def handle_set_language_callback(callback: CallbackQuery):
    selected_lang = callback.data.split("_")[2]
    user_id = callback.from_user.id
    db_register_user(user_id, callback.from_user.username, callback.from_user.first_name)
    db_update_user_lang(user_id, selected_lang)

    t = TEXTS.get(selected_lang, TEXTS["uz"])
    await callback.answer(t["lang_updated"], show_alert=False)
    await callback.message.answer(t["lang_updated"], reply_markup=get_main_reply_keyboard(user_id), parse_mode=ParseMode.MARKDOWN)

# --- TIME SETUP ---
@router.message(Command("setup"))
@router.message(F.text.in_(["⚙️ Sozlamalar", "⚙️ Настройки", "⚙️ Time Setup"]))
async def cmd_setup(message: Message):
    user_id = message.from_user.id
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        member = await message.bot.get_chat_member(message.chat.id, user_id)
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR] and user_id != SUPER_ADMIN_ID:
            await message.reply("⛔ Kechirasiz, bu buyruq faqat guruh adminlari uchun.")
            return
        await message.reply(
            t["setup_group"],
            reply_markup=get_setup_keyboard(is_group=True),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        u = db_get_user(user_id)
        start_t = u["checkin_start"] if u and "checkin_start" in u.keys() else "04:30"
        end_t = u["checkin_end"] if u and "checkin_end" in u.keys() else "06:00"
        await message.answer(
            t["setup_user"].format(start=start_t, end=end_t),
            reply_markup=get_setup_keyboard(is_group=False),
            parse_mode=ParseMode.MARKDOWN
        )

@router.callback_query(F.data.startswith("set_time_grp_"))
async def handle_group_time_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    member = await callback.bot.get_chat_member(callback.message.chat.id, user_id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR] and user_id != SUPER_ADMIN_ID:
        await callback.answer("⛔ Bu tugmani faqat guruh admini bosishi mumkin!", show_alert=True)
        return

    parts = callback.data.split("_")
    start_t, end_t = parts[3], parts[4]
    group_id = callback.message.chat.id
    db_register_group(group_id, callback.message.chat.title or "5 AM Club Group")
    db_update_group_times(group_id, start_t, end_t)

    await callback.answer("✅", show_alert=False)
    await callback.message.edit_text(t["setup_updated"].format(start=start_t, end=end_t), parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data.startswith("set_time_usr_"))
async def handle_user_time_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    parts = callback.data.split("_")
    start_t, end_t = parts[3], parts[4]
    db_register_user(user_id, callback.from_user.username, callback.from_user.first_name)
    db_update_user_times(user_id, start_t, end_t)

    await callback.answer("✅", show_alert=False)
    await callback.message.edit_text(t["setup_updated"].format(start=start_t, end=end_t), parse_mode=ParseMode.MARKDOWN)

# --- SUPER ADMIN PANEL ---
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

# --- PROFILE HANDLER (WORKS IN GROUP & PRIVATE) ---
@router.message(F.text.in_(["📊 Profilim", "📊 Мой Профиль", "📊 My Profile"]))
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
    photo_count = user["photo_count"] if "photo_count" in user.keys() else 0
    freeze_count = user["freeze_count"] if "freeze_count" in user.keys() else 0
    ref_count = user["referral_count"] if "referral_count" in user.keys() else 0
    rank = get_user_rank(streak, lang=lang)
    progress_bar = generate_progress_bar(streak, lang=lang)
    lang_names = {"uz": "🇺🇿 O'zbekcha", "ru": "🇷🇺 Русский", "en": "🇬🇧 English"}
    start_t = user["checkin_start"] if "checkin_start" in user.keys() and user["checkin_start"] else "04:30"
    end_t = user["checkin_end"] if "checkin_end" in user.keys() and user["checkin_end"] else "06:00"

    badges = []
    if streak >= 7: badges.append("⚡ Early Bird")
    if streak >= 21: badges.append("👑 Elite 21")
    if streak >= 30: badges.append("👑 5 AM Legend")
    if photo_count >= 5: badges.append("📸 Photo Master")
    if freeze_count > 0: badges.append("🛡 Shielded")
    if ref_count >= 5: badges.append("👥 Master Ambassador")
    badges_str = " | ".join(badges) if badges else "Boshlang'ich nishonlar"

    profile_text = t["profile_title"].format(
        name=user['first_name'],
        streak=streak,
        multiplier=get_streak_multiplier(streak),
        coins=coins,
        ref_count=ref_count,
        freeze_count=freeze_count,
        photo_count=photo_count,
        rank=rank,
        start=start_t,
        end=end_t,
        badges=badges_str,
        lang_str=lang_names.get(lang, "🇺🇿 O'zbekcha"),
        progress_bar=progress_bar
    )
    await message.reply(profile_text, parse_mode=ParseMode.MARKDOWN)

# --- LEADERBOARD HANDLER (WORKS IN GROUP & PRIVATE) ---
@router.message(F.text.in_(["🏆 Reyting", "🏆 Рейтинг", "🏆 Leaderboard"]))
@router.message(Command("leaderboard"))
async def handle_leaderboard(message: Message):
    lang = get_user_language(message.from_user.id)
    t = TEXTS.get(lang, TEXTS["uz"])

    lb = db_get_global_leaderboard(10)
    if not lb:
        await message.reply(t["leaderboard_empty"])
        return

    text = t["leaderboard_title"]
    for idx, row in enumerate(lb, 1):
        r_title = get_user_rank(row['streak'], lang=lang)
        text += f"`#{idx}` **{row['first_name']}** — `{row['streak']}d` | `{row['coins']} coins` | {r_title}\n"
    await message.reply(text, parse_mode=ParseMode.MARKDOWN)

# --- DAILY QUOTE HANDLER ---
@router.message(F.text.in_(["💡 Kun Iqtibosi", "💡 Цитата Дня", "💡 Daily Quote"]))
@router.message(Command("quote"))
async def handle_quote(message: Message):
    lang = get_user_language(message.from_user.id)
    t = TEXTS.get(lang, TEXTS["uz"])
    quote = await fetch_motivational_quote(lang=lang)
    await message.answer(t["quote_title"].format(quote=quote), parse_mode=ParseMode.MARKDOWN)

# --- HELP HANDLER ---
@router.message(F.text.in_(["📖 Qoidalar", "📖 Правила", "📖 Help & Rules"]))
@router.message(Command("help"))
async def handle_help(message: Message):
    lang = get_user_language(message.from_user.id)
    t = TEXTS.get(lang, TEXTS["uz"])
    await message.answer(t["help_text"], parse_mode=ParseMode.MARKDOWN)

# --- GROUP AUTO-CAPTURE & CHAT MEMBER TRACKING ---
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

# ==================== SCHEDULER ====================
async def scheduler_loop(bot: Bot):
    sent_start, sent_end = {}, {}
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
                            awake.append(f"• **{m['first_name']}** (`{m['last_checkin_time']}`) — 🔥 `{m['streak']}d`")
                        else:
                            sleepers.append(f"• **{m['first_name']}** 😴")

                    quote = await fetch_motivational_quote("uz")
                    rep_msg = (
                        f"🔒 **CHECK-IN CLOSED ({e_t})**\n\n"
                        f"🌅 **AWAKE MEMBERS:**\n" + ("\n".join(awake) if awake else "None 😞") + "\n\n"
                        f"😴 **GRAVEYARD OF SLEEPERS:**\n" + ("\n".join(sleepers) if sleepers else "No sleepers! 🎉") + "\n\n"
                        f"💡 **QUOTE:**\n{quote}"
                    )
                    await bot.send_message(gid, rep_msg, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logging.error(f"Scheduler error: {e}")
        await asyncio.sleep(25)

# ==================== RENDER WEBAPP SERVER (SERVES HTML, CSS, JS & API) ====================
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

async def api_user_stats(req):
    user_id_str = req.match_info.get("user_id", "")
    try:
        user_id = int(user_id_str)
        user = db_get_user(user_id)
        if user:
            return web.json_response({
                "status": "ok",
                "user": {
                    "id": user["user_id"],
                    "name": user["first_name"],
                    "username": user["username"],
                    "streak": user["streak"],
                    "coins": user["coins"],
                    "photo_count": user["photo_count"],
                    "freeze_count": user["freeze_count"],
                    "ref_count": user["referral_count"],
                    "lang": user["lang"]
                }
            })
    except Exception as e:
        logging.error(f"API user error: {e}")
    return web.json_response({"status": "error", "message": "User not found"}, status=404)

async def api_leaderboard(req):
    try:
        lb = db_get_global_leaderboard(10)
        data = [{"name": r["first_name"], "username": r["username"], "streak": r["streak"], "coins": r["coins"]} for r in lb]
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
    app.router.add_get('/api/user/{user_id}', api_user_stats)
    app.router.add_get('/api/leaderboard', api_leaderboard)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 10000)))
    await site.start()

# ==================== MAIN ENTRY POINT ====================
async def set_bot_commands(bot: Bot):
    group_commands = [
        BotCommand(command="setup", description="⚙️ Guruh vaqtini sozlash (Admin)"),
        BotCommand(command="gconfig", description="📋 Guruh boshqaruv paneli (Admin)"),
        BotCommand(command="settime", description="⏰ Vaqtni sozlash (/settime 04:30 06:00)"),
        BotCommand(command="setcoins", description="🪙 Tangalarni sozlash (/setcoins 10 25)"),
        BotCommand(command="leaderboard", description="🏆 Guruh va global reyting"),
        BotCommand(command="profile", description="📊 Shaxsiy profil va nishonlar"),
        BotCommand(command="shop", description="🛒 5 AM Do'koni"),
        BotCommand(command="help", description="📖 Guruh qoidalari"),
    ]
    private_commands = [
        BotCommand(command="start", description="🚀 Botni boshlash / Start"),
        BotCommand(command="checkin", description="⚡ Solo Check-In menyusi"),
        BotCommand(command="profile", description="📊 Profilim va nishonlar"),
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
