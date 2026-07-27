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
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8843755987:AAF4gGBSVa1SKr8oxq26kX__C3b8WSkTFz4")
DEFAULT_GROUP_ID = int(os.getenv("GROUP_CHAT_ID", "-1004349705982"))
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "0"))
TIMEZONE_STR = "Asia/Tashkent"

DB_NAME = "5amclub.db"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ==================== DATABASE ENGINE ====================
def init_sqlite_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Users table
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
    
    # Groups table
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
    
    # Group members table
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
    
    # Check-in history table
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

def db_get_group(group_id: int):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM groups WHERE group_id = ?", (group_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def db_update_group_times(group_id: int, start_time: str, end_time: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE groups SET checkin_start = ?, checkin_end = ? WHERE group_id = ?
    """, (start_time, end_time, group_id))
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
    cursor.execute("""
        SELECT first_name, username, streak, coins 
        FROM users 
        ORDER BY streak DESC, coins DESC 
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# ==================== GAMIFICATION HELPERS ====================
def get_user_rank(streak: int) -> str:
    if streak >= 30:
        return "👑 5 AM Legend"
    elif streak >= 15:
        return "🏆 Morning Master"
    elif streak >= 8:
        return "⚔️ Discipline Warrior"
    elif streak >= 4:
        return "⚡ Rising Phoenix"
    else:
        return "🌅 Dawn Novice"

def generate_progress_bar(streak: int) -> str:
    if streak < 4:
        target, prev, next_rank = 4, 0, "Rising Phoenix ⚡"
    elif streak < 8:
        target, prev, next_rank = 8, 4, "Discipline Warrior ⚔️"
    elif streak < 15:
        target, prev, next_rank = 15, 8, "Morning Master 🏆"
    elif streak < 30:
        target, prev, next_rank = 30, 15, "5 AM Legend 👑"
    else:
        return "👑 **Max Rank Achieved: 5 AM Legend!**"

    progress = max(0.0, min(1.0, (streak - prev) / (target - prev)))
    filled_length = int(round(10 * progress))
    bar = '█' * filled_length + '░' * (10 - filled_length)
    pct = int(progress * 100)
    days_left = target - streak
    return f"Progress: [{bar}] {pct}%\nNext Rank: **{next_rank}** in {days_left} day(s)"

async def fetch_motivational_quote() -> str:
    fallback_quotes = [
        "“Take care of the minutes and the hours will take care of themselves.” – Lord Chesterfield",
        "“The secret of getting ahead is getting started.” – Mark Twain",
        "“Own your morning. Elevate your life.” – Robin Sharma",
        "“Victories are created before dawn, in the quiet solitude of discipline.” – Robin Sharma",
        "“Discipline is choosing between what you want now and what you want most.” – Abraham Lincoln",
        "“You will never change your life until you change something you do daily.” – John C. Maxwell",
        "“Small daily improvements over time lead to stunning results.” – Robin Sharma",
        "“The hard work you put in early pays off when the rest of the world wakes up.”",
        "“Excuses are the nails used to build a house of nothing.” – Jim Rohn"
    ]
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://zenquotes.io/api/random", timeout=aiohttp.ClientTimeout(total=4)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        return f"“{data[0]['q']}”\n— *{data[0]['a']}*"
    except Exception:
        pass
    return random.choice(fallback_quotes)

# ==================== KEYBOARDS ====================
def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="⚡ Solo Check-In"), KeyboardButton(text="📊 My Profile")],
        [KeyboardButton(text="🏆 Leaderboard"), KeyboardButton(text="💡 Daily Quote")],
        [KeyboardButton(text="⚙️ Help & Rules")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_checkin_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ CHECK-IN NOW (I'M AWAKE)", callback_query_data="do_checkin")]
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
        await message.reply(
            "🌅 **The 5 AM Club Bot is Active in this Group!**\n\n"
            "Group members will be automatically registered. Daily check-in window starts every morning at 04:30 AM.\n"
            "Group Admins can use `/setup 04:30 06:00` to adjust times.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        welcome_text = (
            f"👋 **Welcome to The 5 AM Club, {user.first_name}!**\n\n"
            "“Own your morning. Elevate your life.”\n\n"
            "This bot tracks your early morning discipline, builds your streak, and awards coins for consistency.\n\n"
            "📌 **Features:**\n"
            "• **Solo Check-In**: Complete your attendance directly here.\n"
            "• **Group Integration**: Add the bot to your group for team accountability.\n"
            "• **Gamification**: Earn ranks, badges, and coins every morning!"
        )
        await message.answer(welcome_text, reply_markup=get_main_reply_keyboard(), parse_mode=ParseMode.MARKDOWN)

@router.message(Command("setup"))
async def cmd_setup(message: Message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ The `/setup` command can only be used inside groups.")
        return
        
    member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
        await message.reply("⛔ Only group administrators can configure check-in settings.")
        return
        
    args = message.text.split()
    if len(args) != 3:
        await message.reply("ℹ️ **Usage:** `/setup <start_time> <end_time>`\n*Example:* `/setup 04:30 06:00`", parse_mode=ParseMode.MARKDOWN)
        return
        
    start_t, end_t = args[1], args[2]
    db_register_group(message.chat.id, message.chat.title)
    db_update_group_times(message.chat.id, start_t, end_t)
    
    await message.reply(
        f"✅ **Check-In Schedule Updated!**\n\n"
        f"⏰ **Start Time**: `{start_t}`\n"
        f"🔒 **End Time**: `{end_t}`\n"
        f"🌍 **Timezone**: `{TIMEZONE_STR}`",
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(F.text == "⚡ Solo Check-In")
async def handle_solo_checkin(message: Message):
    user_id = message.from_user.id
    db_register_user(user_id, message.from_user.username, message.from_user.first_name)
    
    tz = pytz.timezone(TIMEZONE_STR)
    now = datetime.now(tz)
    current_time_str = now.strftime("%H:%M")
    
    # Allow solo checkin between 04:30 and 06:00 (or any morning test window)
    res = db_process_checkin(user_id, group_id=0, is_early=(current_time_str <= "05:00"))
    
    if res == "already":
        await message.reply("⚠️ **You have already completed your check-in for today!** See you tomorrow morning! 🌅", parse_mode=ParseMode.MARKDOWN)
    elif res:
        rank = get_user_rank(res["streak"])
        await message.reply(
            f"⚡ **SOLO CHECK-IN SUCCESSFUL!**\n\n"
            f"👤 **Member**: {message.from_user.first_name}\n"
            f"⏰ **Time**: `{res['checkin_time']}`\n"
            f"🔥 **Current Streak**: `{res['streak']} days`\n"
            f"🪙 **Coins Earned**: `+{res['coins_earned']}` (Total: `{res['coins']}`)\n"
            f"🏅 **Rank**: {rank}\n\n"
            f"Great job rising early! Keep the momentum going! 💪",
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
    now = datetime.now(tz)
    current_time_str = now.strftime("%H:%M")
    
    res = db_process_checkin(user.id, group_id=group_id, is_early=(current_time_str <= "05:00"))
    
    if res == "already":
        await callback.answer("⚠️ You have already checked in today!", show_alert=True)
    elif res:
        await callback.answer("✅ Morning Check-In Completed!", show_alert=False)
        rank = get_user_rank(res["streak"])
        announcement = (
            f"⚡ **CHECK-IN CONFIRMED!**\n\n"
            f"👤 **Member**: {user.first_name}\n"
            f"⏰ **Time**: `{res['checkin_time']}`\n"
            f"🔥 **Streak**: `{res['streak']} days`\n"
            f"🪙 **Coins Earned**: `+{res['coins_earned']}`\n"
            f"🏅 **Rank**: {rank}"
        )
        await callback.message.answer(announcement, parse_mode=ParseMode.MARKDOWN)

@router.message(F.text == "📊 My Profile")
async def handle_my_profile(message: Message):
    user_id = message.from_user.id
    user = db_get_user(user_id)
    if not user:
        db_register_user(user_id, message.from_user.username, message.from_user.first_name)
        user = db_get_user(user_id)
        
    streak = user["streak"]
    coins = user["coins"]
    rank = get_user_rank(streak)
    progress_bar = generate_progress_bar(streak)
    
    profile_text = (
        f"👤 **MEMBER PROFILE**\n\n"
        f"🏷 **Name**: {user['first_name']}\n"
        f"🔥 **Streak**: `{streak} Days`\n"
        f"🪙 **Coins**: `{coins}`\n"
        f"🏅 **Rank**: {rank}\n\n"
        f"📈 **RANK PROGRESSION:**\n"
        f"{progress_bar}\n\n"
        f"“Victory belongs to the most persevering.”"
    )
    await message.answer(profile_text, parse_mode=ParseMode.MARKDOWN)

@router.message(F.text == "🏆 Leaderboard")
async def handle_leaderboard(message: Message):
    leaderboard = db_get_global_leaderboard(limit=10)
    if not leaderboard:
        await message.answer("🏆 **LEADERBOARD**\n\nNo active risers recorded yet.")
        return
        
    text = "🏆 **THE 5 AM CLUB GLOBAL LEADERBOARD** 🏆\n\n"
    medals = ["🥇", "🥈", "🥉"]
    
    for idx, row in enumerate(leaderboard, start=1):
        icon = medals[idx-1] if idx <= 3 else f"`#{idx}`"
        name = row["first_name"]
        streak = row["streak"]
        coins = row["coins"]
        rank = get_user_rank(streak)
        text += f"{icon} **{name}** — `{streak}d streak` | `{coins} coins` | {rank}\n"
        
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)

@router.message(F.text == "💡 Daily Quote")
async def handle_daily_quote(message: Message):
    quote = await fetch_motivational_quote()
    await message.answer(f"💡 **DAILY MORNING WISDOM**\n\n{quote}", parse_mode=ParseMode.MARKDOWN)

@router.message(F.text == "⚙️ Help & Rules")
async def handle_help(message: Message):
    help_text = (
        "📖 **THE 5 AM CLUB — RULES & GUIDELINES**\n\n"
        "1. **Morning Check-In**: The check-in window opens every morning at `04:30 AM` and closes at `06:00 AM`.\n"
        "2. **Early Bird Bonus**: Check in within the first 15 minutes (`04:30 - 04:45`) to earn **+15 Coins**.\n"
        "3. **Consistency**: Missing a check-in resets your streak to `0`.\n"
        "4. **Graveyard of Sleepers**: At 06:00 AM, a daily report is posted to the group showing those who woke up vs those who slept in."
    )
    await message.answer(help_text, parse_mode=ParseMode.MARKDOWN)

@router.message(F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]))
async def handle_group_auto_capture(message: Message):
    if message.from_user and not message.from_user.is_bot:
        db_register_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        db_register_group(message.chat.id, message.chat.title)
        db_link_group_member(message.chat.id, message.from_user.id)

# ==================== SCHEDULER & AUTOMATION ====================
async def scheduler_loop(bot: Bot):
    sent_start_flags = {}
    sent_end_flags = {}
    
    while True:
        try:
            tz = pytz.timezone(TIMEZONE_STR)
            now = datetime.now(tz)
            today_str = now.strftime("%Y-%m-%d")
            current_hhmm = now.strftime("%H:%M")
            
            groups = db_get_active_groups()
            
            # Ensure default group is registered if empty
            if not groups:
                db_register_group(DEFAULT_GROUP_ID, "5 AM Club Primary Group")
                groups = db_get_active_groups()
                
            for g in groups:
                gid = g["group_id"]
                start_t = g["checkin_start"]
                end_t = g["checkin_end"]
                
                # 1. Trigger Check-in Start Announcement
                if current_hhmm == start_t and sent_start_flags.get(f"{gid}_{today_str}") != True:
                    sent_start_flags[f"{gid}_{today_str}"] = True
                    db_reset_group_snoozed(gid)
                    
                    msg = (
                        "🌅 **THE 5 AM CLUB: MORNING CHECK-IN IS OPEN!**\n\n"
                        "“Rise early, conquer your day, and claim your victory!”\n\n"
                        f"⏰ Check-In Window: `{start_t}` — `{end_t}`\n"
                        "⚡ Click the button below to register your attendance and earn bonus coins!"
                    )
                    try:
                        await bot.send_message(gid, msg, reply_markup=get_checkin_inline_keyboard(), parse_mode=ParseMode.MARKDOWN)
                    except Exception as e:
                        logging.error(f"Failed to send start message to group {gid}: {e}")
                        
                # 2. Trigger Check-in End & Graveyard Report
                if current_hhmm == end_t and sent_end_flags.get(f"{gid}_{today_str}") != True:
                    sent_end_flags[f"{gid}_{today_str}"] = True
                    
                    report_members = db_get_group_attendance_report(gid)
                    awake_list = []
                    sleepers_list = []
                    
                    for m in report_members:
                        name = m["first_name"]
                        if m["status"] == "awake":
                            awake_list.append(f"• **{name}** (`{m['last_checkin_time']}`) — 🔥 `{m['streak']}d`")
                        else:
                            sleepers_list.append(f"• **{name}** 😴")
                            
                    quote = await fetch_motivational_quote()
                    
                    report_msg = f"🔒 **CHECK-IN WINDOW CLOSED ({end_t})**\n\n"
                    report_msg += "🌅 **EARLY BIRDS (AWAKE):**\n"
                    report_msg += "\n".join(awake_list) if awake_list else "None checked in today 😞\n"
                    
                    report_msg += "\n\n😴 **GRAVEYARD OF SLEEPERS (HALL OF SHAME):**\n"
                    report_msg += "\n".join(sleepers_list) if sleepers_list else "No sleepers today! Excellent team effort! 🎉\n"
                    
                    report_msg += f"\n\n💡 **MOTIVATION FOR THE DAY:**\n{quote}"
                    
                    try:
                        await bot.send_message(gid, report_msg, parse_mode=ParseMode.MARKDOWN)
                    except Exception as e:
                        logging.error(f"Failed to send report message to group {gid}: {e}")
                        
        except Exception as e:
            logging.error(f"Error in scheduler loop: {e}")
            
        await asyncio.sleep(25)

# ==================== RENDER KEEPALIVE SERVER ====================
async def handle_web_ping(request):
    return web.Response(text="5 AM Club Bot is running 24/7 on Render!")

async def start_dummy_web_server():
    app = web.Application()
    app.router.add_get('/', handle_web_ping)
    app.router.add_get('/health', handle_web_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Render healthcheck HTTP server running on port {port}")

# ==================== MAIN ENTRY POINT ====================
async def main():
    init_sqlite_db()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    # Start web server for Render port binding
    await start_dummy_web_server()
    
    # Start background scheduler
    asyncio.create_task(scheduler_loop(bot))
    
    logging.info("5 AM Club Bot is starting polling...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
