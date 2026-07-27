import asyncio
import logging
import os
import random
import sqlite3
from datetime import datetime, timedelta
import pytz
import aiohttp
from aiohttp import web

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ChatMemberUpdated
)
from aiogram.enums import ParseMode, ChatType, ChatMemberStatus
from aiogram.types.reaction_type_emoji import ReactionTypeEmoji

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8843755987:AAF4gGBSVa1SKr8oxq26kX__C3b8WSkTFz4")
DEFAULT_GROUP_ID = int(os.getenv("GROUP_CHAT_ID", "-1004349705982"))
TIMEZONE_STR = "Asia/Tashkent"
DB_NAME = "5amclub.db"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ==================== DYNAMIC QUIPS & QUOTES GENERATOR ====================
# We use combinations to create thousands of unique messages instantly
GREETINGS = [
    "Look who decided to join the living world!", "Bro actually woke up before the sun!",
    "The bed tried to hold you hostage, but discipline won!", "Another day, another victory.",
    "Even your alarm clock is shocked.", "Zzz... Oh wait, you're actually awake?!",
    "Rise and grind!", "Welcome to the elite club.", "Boom! Champion has arrived.",
    "Morning beast mode activated."
]

PRAISES = [
    "Coffee is already proud of you.", "Absolute beast mode activated.", 
    "Robin Sharma is smiling down right now.", "Don't go back to sleep!",
    "Early bird gets the whole universe!", "Keep this legendary momentum going.",
    "Your future self is thanking you.", "Discipline equals freedom.",
    "Setting the standard for the rest of us.", "Unstoppable force of nature."
]

EMOJIS = ["🔥", "⚡", "🦅", "🏆", "😎", "💪", "🚀", "👑", "🌟", "✨"]

async def fetch_dynamic_quip(streak: int, name: str) -> str:
    # 1. Try to fetch a dynamic affirmation from the internet API
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.affirmations.dev/", timeout=2) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    affirmation = data.get("affirmation", "")
                    if affirmation:
                        return f"⚡ **{name}**, remember: {affirmation}! Keep grinding."
    except Exception:
        pass # If internet fails, fallback to our massive dynamic combination generator
        
    # 2. Dynamic Combination Generator (thousands of variations)
    greeting = random.choice(GREETINGS)
    praise = random.choice(PRAISES)
    emoji = random.choice(EMOJIS)
    
    base_text = f"{greeting} {praise} {emoji}"
    
    if streak >= 30:
        return f"👑 **LEGEND ALERT! ({streak} Days Straight):** {base_text}"
    elif streak >= 10:
        return f"🔥 **STREAK MONSTER ({streak} Days):** {base_text}"
    else:
        return f"⚡ **AWAKE & ALIVE:** {base_text}"

async def fetch_motivational_quote() -> str:
    fallback_quotes = [
        "“Take care of the minutes and the hours will take care of themselves.” – Lord Chesterfield",
        "“The secret of getting ahead is getting started.” – Mark Twain",
        "“Own your morning. Elevate your life.” – Robin Sharma",
        "“Victories are created before dawn, in the quiet solitude of discipline.” – Robin Sharma",
        "“Discipline is choosing between what you want now and what you want most.” – Abraham Lincoln",
        "“You will never change your life until you change something you do daily.” – John C. Maxwell"
    ]
    # Fetch from ZenQuotes API
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://zenquotes.io/api/random", timeout=4) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        return f"“{data[0]['q']}”\n— *{data[0]['a']}*"
    except Exception:
        pass
    return random.choice(fallback_quotes)

# ==================== DATABASE ENGINE ====================
def init_sqlite_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            streak INTEGER DEFAULT 0,
            coins INTEGER DEFAULT 0,
            last_checkin_date TEXT,
            status TEXT DEFAULT 'snoozed',
            created_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            group_id INTEGER PRIMARY KEY,
            title TEXT,
            checkin_start TEXT DEFAULT '04:30',
            checkin_end TEXT DEFAULT '06:00',
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
    conn.commit()
    conn.close()

def db_register_user(user_id: int, username: str, first_name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO users (user_id, username, first_name, created_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name
    """, (user_id, username or "", first_name or "Member", now_str))
    conn.commit()
    conn.close()

def db_register_group(group_id: int, title: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO groups (group_id, title)
        VALUES (?, ?)
        ON CONFLICT(group_id) DO UPDATE SET title = excluded.title
    """, (group_id, title or "5 AM Club Group"))
    conn.commit()
    conn.close()

def db_link_group_member(group_id: int, user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO group_members (group_id, user_id)
        VALUES (?, ?)
        ON CONFLICT(group_id, user_id) DO NOTHING
    """, (group_id, user_id))
    conn.commit()
    conn.close()

def db_get_user(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def db_get_active_groups():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM groups WHERE is_active = 1")
    rows = cursor.fetchall()
    conn.close()
    return rows

def db_update_group_times(group_id: int, start_time: str, end_time: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE groups SET checkin_start = ?, checkin_end = ? WHERE group_id = ?", (start_time, end_time, group_id))
    conn.commit()
    conn.close()

def db_process_checkin(user_id: int, group_id: int = 0, is_early: bool = False):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    tz = pytz.timezone(TIMEZONE_STR)
    now = datetime.now(tz)
    today_str = now.strftime("%Y-%m-%d")
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    time_str = now.strftime("%H:%M:%S")
    
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return None
        
    last_date = user["last_checkin_date"]
    current_streak = user["streak"]
    
    if last_date == today_str:
        conn.close()
        return "already"
        
    yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    if last_date == yesterday_str:
        new_streak = current_streak + 1
    else:
        new_streak = 1
        
    coins_earned = 15 if is_early else 10
    new_coins = user["coins"] + coins_earned
    
    cursor.execute("""
        UPDATE users 
        SET streak = ?, coins = ?, last_checkin_date = ?, status = 'awake'
        WHERE user_id = ?
    """, (new_streak, new_coins, today_str, user_id))
    
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
        
    conn.commit()
    conn.close()
    
    return {
        "streak": new_streak,
        "coins": new_coins,
        "coins_earned": coins_earned,
        "checkin_time": time_str
    }

def db_reset_group_snoozed(group_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE group_members SET status = 'snoozed' WHERE group_id = ?", (group_id,))
    conn.commit()
    conn.close()

def db_get_group_attendance_report(group_id: int):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.user_id, u.first_name, u.username, gm.status, gm.last_checkin_time, u.streak
        FROM group_members gm
        JOIN users u ON gm.user_id = u.user_id
        WHERE gm.group_id = ?
    """, (group_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def db_get_global_leaderboard(limit: int = 10):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, username, streak, coins FROM users ORDER BY streak DESC, coins DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# ==================== GAMIFICATION HELPERS ====================
def get_user_rank(streak: int) -> str:
    if streak >= 30: return "👑 5 AM Legend"
    elif streak >= 15: return "🏆 Morning Master"
    elif streak >= 8: return "⚔️ Discipline Warrior"
    elif streak >= 4: return "⚡ Rising Phoenix"
    else: return "🌅 Dawn Novice"

def generate_progress_bar(streak: int) -> str:
    if streak < 4: target, prev, next_rank = 4, 0, "Rising Phoenix ⚡"
    elif streak < 8: target, prev, next_rank = 8, 4, "Discipline Warrior ⚔️"
    elif streak < 15: target, prev, next_rank = 15, 8, "Morning Master 🏆"
    elif streak < 30: target, prev, next_rank = 30, 15, "5 AM Legend 👑"
    else: return "👑 **Max Rank Achieved: 5 AM Legend!**"

    progress = max(0.0, min(1.0, (streak - prev) / (target - prev)))
    filled_length = int(round(10 * progress))
    bar = '█' * filled_length + '░' * (10 - filled_length)
    pct = int(progress * 100)
    days_left = target - streak
    return f"Progress: [{bar}] {pct}%\nNext Rank: **{next_rank}** in {days_left} day(s)"

# ==================== KEYBOARDS ====================
def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="⚡ Solo Check-In"), KeyboardButton(text="📊 My Profile")],
        [KeyboardButton(text="🏆 Leaderboard"), KeyboardButton(text="💡 Daily Quote")],
        [KeyboardButton(text="⚙️ Help & Rules")]
    ], resize_keyboard=True)

def get_checkin_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ CHECK-IN NOW (I'M AWAKE)", callback_data="do_checkin")]
    ])

# ==================== HANDLERS ====================
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    db_register_user(user.id, user.username, user.first_name)
    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        db_register_group(message.chat.id, message.chat.title)
        db_link_group_member(message.chat.id, user.id)
        await message.reply("🌅 **The 5 AM Club Bot is Active!** Group members auto-registered.", parse_mode=ParseMode.MARKDOWN)
    else:
        welcome_text = (
            f"👋 **Welcome to The 5 AM Club, {user.first_name}!**\n\n"
            "“Own your morning. Elevate your life.” Use the menu below to track your check-ins."
        )
        await message.answer(welcome_text, reply_markup=get_main_reply_keyboard(), parse_mode=ParseMode.MARKDOWN)

@router.message(Command("setup"))
async def cmd_setup(message: Message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ Group command only.")
        return
    member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
        await message.reply("⛔ Admins only.")
        return
    args = message.text.split()
    if len(args) != 3:
        await message.reply("ℹ️ Usage: `/setup 04:30 06:00`", parse_mode=ParseMode.MARKDOWN)
        return
    db_register_group(message.chat.id, message.chat.title)
    db_update_group_times(message.chat.id, args[1], args[2])
    await message.reply(f"✅ Schedule updated: `{args[1]}` to `{args[2]}`", parse_mode=ParseMode.MARKDOWN)

@router.message(F.text == "⚡ Solo Check-In")
async def handle_solo_checkin(message: Message):
    user_id = message.from_user.id
    db_register_user(user_id, message.from_user.username, message.from_user.first_name)
    tz = pytz.timezone(TIMEZONE_STR)
    res = db_process_checkin(user_id, group_id=0, is_early=(datetime.now(tz).strftime("%H:%M") <= "05:00"))
    
    if res == "already":
        await message.reply("⚠️ You already checked in today! See you tomorrow! 🌅")
    elif res:
        quip = await fetch_dynamic_quip(res["streak"], message.from_user.first_name)
        await message.reply(
            f"⚡ **SOLO CHECK-IN SUCCESSFUL!**\n\n"
            f"{quip}\n\n"
            f"🔥 Streak: `{res['streak']} days` | 🪙 Coins: `+{res['coins_earned']}` (Total: `{res['coins']}`)\n"
            f"🏅 Rank: {get_user_rank(res['streak'])}",
            parse_mode=ParseMode.MARKDOWN
        )

@router.callback_query(F.data == "do_checkin")
async def handle_callback_checkin(callback: CallbackQuery):
    user = callback.from_user
    db_register_user(user.id, user.username, user.first_name)
    group_id = callback.message.chat.id if callback.message.chat else 0
    if group_id != 0:
        db_link_group_member(group_id, user.id)
        
    tz = pytz.timezone(TIMEZONE_STR)
    res = db_process_checkin(user.id, group_id=group_id, is_early=(datetime.now(tz).strftime("%H:%M") <= "05:00"))
    
    if res == "already":
        await callback.answer("⚠️ You already checked in today!", show_alert=True)
    elif res:
        await callback.answer("✅ Morning Check-In Completed!", show_alert=False)
        
        # 1. BOT REACTION (Add dynamic emoji reaction)
        try:
            chosen_emoji = random.choice(["🔥", "⚡", "🦅", "🏆", "🎉", "💪", "👍"])
            await callback.message.react(reaction=[ReactionTypeEmoji(emoji=chosen_emoji)])
        except Exception as e:
            logging.error(f"Failed to react: {e}")
            
        # 2. DYNAMIC & ENDLESS SHOUTOUT MESSAGE (Internet/Generator mix)
        quip = await fetch_dynamic_quip(res["streak"], user.first_name)
        announcement = (
            f"⚡ **CHECK-IN CONFIRMED**\n\n"
            f"{quip}\n\n"
            f"⏰ Time: `{res['checkin_time']}` | 🔥 Streak: `{res['streak']} days`\n"
            f"🪙 Coins: `+{res['coins_earned']}` | 🏅 Rank: {get_user_rank(res['streak'])}"
        )
        await callback.message.answer(announcement, parse_mode=ParseMode.MARKDOWN)

@router.message(F.text == "📊 My Profile")
async def handle_my_profile(message: Message):
