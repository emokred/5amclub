import os
import asyncio
import random
import aiohttp
from datetime import datetime, timedelta
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton
)

# Configuration
TOKEN = "8843755987:AAF4gGBSVa1SKr8oxq26kX__C3b8WSkTFz4"
GROUP_CHAT_ID = -1004349705982
ADMIN_ID = 6377617416  # Updated Admin ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Databases & States
users = {}
attendance_today = set()
attendance_active = False

# Backup motivational quotes (in English)
LOCAL_QUOTES = [
    "“Small disciplines repeated with consistency every day lead to great achievements.” — Robin Sharma",
    "“We are what we repeatedly do. Excellence, then, is not an act, but a habit.” — Will Durant",
    "“Success is not final; failure is not fatal: It is the courage to continue that counts.” — Winston Churchill",
    "“Believe you can and you're halfway there.” — Theodore Roosevelt",
    "“The secret of getting ahead is getting started.” — Mark Twain",
    "“You don't have to be great to start, but you have to start to be great.” — Zig Ziglar"
]

# Fetch daily quote from API
async def get_random_quote_from_internet():
    url = "https://zenquotes.io/api/random"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return f"“{data[0]['q']}” — {data[0]['a']}"
    except Exception as e:
        print(f"Error fetching quote: {e}")
    return random.choice(LOCAL_QUOTES)

# --- KEYBOARDS ---
def get_user_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 My Stats"), KeyboardButton(text="🏆 Leaderboard")],
            [KeyboardButton(text="💡 Daily Spark"), KeyboardButton(text="❓ How It Works")]
        ],
        resize_keyboard=True
    )

def get_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 My Stats"), KeyboardButton(text="🏆 Leaderboard")],
            [KeyboardButton(text="💡 Daily Spark"), KeyboardButton(text="❓ How It Works")],
            [KeyboardButton(text="👥 Members List")]
        ],
        resize_keyboard=True
    )

def get_attendance_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚡ Check In Now!",
                    callback_data="check_in",
                )
            ]
        ]
    )

# --- COMMANDS ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    if user_id not in users:
        users[user_id] = {"name": user_name, "streak": 0, "last_date": ""}

    if message.chat.type == "private":
        if user_id == ADMIN_ID:
            await message.answer("Hey Admin! 👑 Welcome back to the command center.", reply_markup=get_admin_menu())
        else:
            await message.answer("Welcome to the **5 AM Club**! 🌅\nBig goals start with early mornings. Use the menu below to stay on track:", reply_markup=get_user_menu())
    else:
        await message.answer("5 AM Club Bot is active! 🚀 Direct message me to view your personal stats and commands.")

# --- CHECK-IN CALLBACK ---
@dp.callback_query(F.data == "check_in")
async def process_check_in(callback: CallbackQuery):
    global attendance_active
    if not attendance_active:
        await callback.answer(
            "Check-in is currently closed! ⏰ Doors open from 04:30 AM to 06:00 AM.",
            show_alert=True,
        )
        return

    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    today_str = datetime.now().strftime("%Y-%m-%d")

    if user_id not in users:
        users[user_id] = {"name": user_name, "streak": 0, "last_date": ""}

    if user_id not in attendance_today:
        attendance_today.add(user_id)
        last_date = users[user_id]["last_date"]
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        if last_date == yesterday_str or last_date == "":
            users[user_id]["streak"] += 1
        elif last_date != today_str:
            users[user_id]["streak"] = 1 

        users[user_id]["last_date"] = today_str
        await callback.answer("Boom! You're checked in for today! Keep that streak burning 🔥", show_alert=True)
    else:
        await callback.answer("You've already checked in today! Solid discipline 👊", show_alert=True)

# --- MENU BUTTON HANDLERS ---
@dp.message(F.text == "🏆 Leaderboard")
@dp.message(Command("ranking"))
async def cmd_ranking(message: Message):
    if not users:
        await message.answer("No members registered yet. Be the first!")
        return
    sorted_users = sorted(users.values(), key=lambda x: x["streak"], reverse=True)
    text = "🏆 **5 AM Club Discipline Leaderboard:**\n\n"
    for idx, u in enumerate(sorted_users[:10], 1):
        text += f"{idx}. {u['name']} — 🔥 {u['streak']} days streak\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "📊 My Stats")
async def user_stats(message: Message):
    user_data = users.get(message.from_user.id, {"streak": 0})
    await message.answer(f"📊 **Your Personal Discipline Stats:**\n\n- Current Streak: **{user_data.get('streak', 0)} days** 🔥\n\n*Keep showing up every morning!*")

@dp.message(F.text == "💡 Daily Spark")
async def morning_motivation(message: Message):
    quote = await get_random_quote_from_internet()
    await message.answer(f"💡 **Daily Mindset Booster:**\n\n{quote}")

@dp.message(F.text == "❓ How It Works")
async def help_rules(message: Message):
    await message.answer("⚡ **5 AM Club Rules:**\n\n1. Check-in opens at **04:30 AM** daily.\n2. Tap the **Check In Now!** button before **06:00 AM**.\n3. Build your daily streak and claim the top of the leaderboard!")

@dp.message(F.text == "👥 Members List")
async def admin_users(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"👥 Total registered members: **{len(users)}**")

# --- SCHEDULER (04:30, 06:00, 08:00) ---
async def scheduler():
    global attendance_active
    while True:
        now = datetime.now()
        current_time = now.time()

        # 1. 04:30 AM — Open Check-in
        if current_time.hour == 4 and current_time.minute == 30:
            attendance_active = True
            attendance_today.clear()
            msg_text = "🌅 **Good Morning, 5 AM Club!**\n\nRise and grind! Check-in is now OPEN until 06:00 AM. Hit the button below to keep your streak alive! 🔥"
            
            try:
                await bot.send_message(GROUP_CHAT_ID, msg_text, reply_markup=get_attendance_keyboard(), parse_mode="Markdown")
            except Exception as e:
                print(f"Error sending group notification: {e}")

            for uid in users.keys():
                try:
                    await bot.send_message(uid, msg_text, reply_markup=get_attendance_keyboard(), parse_mode="Markdown")
                except Exception:
                    pass

            await asyncio.sleep(60)

        # 2. 06:00 AM — Close Check-in & Post Attendance Report
        elif current_time.hour == 6 and current_time.minute == 0:
            if attendance_active:
                attendance_active = False
                present_list = [users[uid]["name"] for uid in attendance_today]
                absent_list = [u["name"] for uid, u in users.items() if uid not in attendance_today]

                report = "⏰ **Check-in Closed for Today! (06:00 AM)**\n\n"
                report += f"✅ **Early Birds ({len(present_list)}):**\n" + ("\n".join([f"- {n}" for n in present_list]) if present_list else "None today 💤") + "\n\n"
                report += f"❌ **Snoozed / Missed ({len(absent_list)}):**\n" + ("\n".join([f"- {n}" for n in absent_list]) if absent_list else "Everyone checked in! Amazing 🎉") + "\n\n*Consistency is everything. See you tomorrow at 04:30 AM!*"

                try:
                    await bot.send_message(GROUP_CHAT_ID, report, parse_mode="Markdown")
                except Exception as e:
                    print(f"Error sending report: {e}")
            await asyncio.sleep(60)

        # 3. 08:00 AM — Send Daily Quote
        elif current_time.hour == 8 and current_time.minute == 0:
            quote = await get_random_quote_from_internet()
            try:
                await bot.send_message(GROUP_CHAT_ID, f"💡 **Daily Morning Spark:**\n\n{quote}", parse_mode="Markdown")
            except Exception as e:
                print(f"Error sending quote: {e}")
            await asyncio.sleep(60)

        await asyncio.sleep(30)

# --- SERVER & BOT LAUNCH ---
async def handle(request):
    return web.Response(text="5 AM Club Bot is live and running!")

async def web_server():
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    await site.start()

async def main():
    asyncio.create_task(web_server())
    asyncio.create_task(scheduler())
    
    # Prevent Telegram Conflict Error
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
