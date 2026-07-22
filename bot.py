import os
import asyncio
import random
import aiohttp  # Xatolikni bartaraf etish uchun aiohttp to'liq ulandi
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

# Yangi token va guruh ID
TOKEN = "8843755987:AAF4gGBSVa1SKr8oxq26kX__C3b8WSkTFz4"
GROUP_CHAT_ID = -1004349705982
ADMIN_ID = 123456789  # O'zingizning Telegram ID raqamingizni yozing

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Bazalar va holatlar
users = {}
attendance_today = set()
attendance_active = False

# Zaxiradagi motivatsion iqtiboslar (Internet qotib qolsa shulardan foydalanadi)
LOCAL_QUOTES = [
    "“Small disciplines repeated with consistency every day lead to great achievements.” — Robin Sharma",
    "“We are what we repeatedly do. Excellence, then, is not an act, but a habit.” — Will Durant",
    "“Success is not final; failure is not fatal: It is the courage to continue that counts.” — Winston Churchill",
    "“Believe you can and you're halfway there.” — Theodore Roosevelt",
    "“The secret of getting ahead is getting started.” — Mark Twain"
]

# API orqali quote olish funksiyasi (xatolar to'liq bartaraf etildi)
async def get_random_quote_from_internet():
    url = "https://zenquotes.io/api/random"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return f"“{data[0]['q']}” — {data[0]['a']}"
    except Exception as e:
        print(f"Quote olishda xatolik: {e}")
    # Agar API ishlamasa, mahalliy ro'yxatdan bittasini tanlaydi
    return random.choice(LOCAL_QUOTES)

# --- MENYULAR ---
def get_user_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Mening statistikam"), KeyboardButton(text="🏆 Top Reyting")],
            [KeyboardButton(text="💡 Tonggi motivatsiya"), KeyboardButton(text="ℹ️ Yordam / Qoidalar")]
        ],
        resize_keyboard=True
    )

def get_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Mening statistikam"), KeyboardButton(text="🏆 Top Reyting")],
            [KeyboardButton(text="💡 Tonggi motivatsiya"), KeyboardButton(text="ℹ️ Yordam / Qoidalar")],
            [KeyboardButton(text="👥 Ishtirokchilar")]
        ],
        resize_keyboard=True
    )

def get_attendance_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Davomatdan o'tish (Check-in)",
                    callback_data="check_in",
                )
            ]
        ]
    )

# --- /start ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    if user_id not in users:
        users[user_id] = {"name": user_name, "streak": 0, "last_date": ""}

    if message.chat.type == "private":
        if user_id == ADMIN_ID:
            await message.answer("Assalomu alaykum, Admin!", reply_markup=get_admin_menu())
        else:
            await message.answer("Xush kelibsiz! 5 AM Club botiga marhamat.", reply_markup=get_user_menu())
    else:
        await message.answer("Bot guruhda ishlamoqda. Shaxsiy statistika uchun menga lichkada yozing!")

# --- CHECK-IN ---
@dp.callback_query(F.data == "check_in")
async def process_check_in(callback: CallbackQuery):
    global attendance_active
    if not attendance_active:
        await callback.answer(
            "Hozir davomat vaqti emas! Davomat 20:40 dan 20:45 gacha ochiq bo'ladi.",
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
        await callback.answer("Tabriklaymiz! Ishtirokingiz qayd etildi! 🔥", show_alert=True)
    else:
        await callback.answer("Siz allaqachon bugun ro'yxatdan o'tgansiz!", show_alert=True)

# --- REYTING VA TUGMALAR ---
@dp.message(F.text == "🏆 Top Reyting")
@dp.message(Command("ranking"))
async def cmd_ranking(message: Message):
    if not users:
        await message.answer("Hozircha reytingda ishtirokchilar yo'q.")
        return
    sorted_users = sorted(users.values(), key=lambda x: x["streak"], reverse=True)
    text = "🏆 **5 AM Club Intizom Reytingi (Streak):**\n\n"
    for idx, u in enumerate(sorted_users[:10], 1):
        text += f"{idx}. {u['name']} — 🔥 {u['streak']} kun ketma-ket\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "📊 Mening statistikam")
async def user_stats(message: Message):
    user_data = users.get(message.from_user.id, {"streak": 0})
    await message.answer(f"📊 **Sizning statistikangiz:**\n\n- Joriy streak: {user_data.get('streak', 0)} kun")

@dp.message(F.text == "💡 Tonggi motivatsiya")
async def morning_motivation(message: Message):
    quote = await get_random_quote_from_internet()
    await message.answer(f"💡 **Motivatsiya:**\n\n{quote}")

@dp.message(F.text == "ℹ️ Yordam / Qoidalar")
async def help_rules(message: Message):
    await message.answer("ℹ️ **Qoidalar:**\nBelgilangan vaqtda (20:40) bot tashlagan xabarga kirib, davomat tugmasini bosishingiz kerak.")

@dp.message(F.text == "👥 Ishtirokchilar")
async def admin_users(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"👥 Jami ro'yxatdan o'tganlar soni: {len(users)} ta")

# --- SCHEDULER (Yangi vaqtlar: 20:40, 20:45, 20:50) ---
async def scheduler():
    global attendance_active
    while True:
        now = datetime.now()
        current_time = now.time()

        # 1. Soat 20:40 - Davomatni ochish
        if current_time.hour == 20 and current_time.minute == 40:
            attendance_active = True
            attendance_today.clear()
            msg_text = "🌅 **Davomat boshlandi!**\nSoat 20:45 gacha quyidagi tugmani bosing:"
            
            try:
                await bot.send_message(GROUP_CHAT_ID, msg_text, reply_markup=get_attendance_keyboard(), parse_mode="Markdown")
            except Exception as e:
                print(f"Guruhga yuborishda xatolik: {e}")

            for uid in users.keys():
                try:
                    await bot.send_message(uid, msg_text, reply_markup=get_attendance_keyboard(), parse_mode="Markdown")
                except Exception:
                    pass

            await asyncio.sleep(60) # 1 daqiqa kutish, keyingi siklga o'tish uchun

        # 2. Soat 20:45 - Davomatni yopish
        elif current_time.hour == 20 and current_time.minute == 45:
            if attendance_active:
                attendance_active = False
                present_list = [users[uid]["name"] for uid in attendance_today]
                absent_list = [u["name"] for uid, u in users.items() if uid not in attendance_today]

                report = "📊 **Davomat yakunlandi (20:45):**\n\n"
                report += f"✅ **Ishtirok etganlar ({len(present_list)}):**\n" + ("\n".join([f"- {n}" for n in present_list]) if present_list else "Yo'q") + "\n\n"
                report += f"❌ **Qatnashmaganlar ({len(absent_list)}):**\n" + ("\n".join([f"- {n}" for n in absent_list]) if absent_list else "Hamma qatnashdi!")

                try:
                    await bot.send_message(GROUP_CHAT_ID, report, parse_mode="Markdown")
                except Exception:
                    pass
            await asyncio.sleep(60)

        # 3. Soat 20:50 - Motivatsiya yuborish
        elif current_time.hour == 20 and current_time.minute == 50:
            quote = await get_random_quote_from_internet()
            try:
                await bot.send_message(GROUP_CHAT_ID, f"💡 **Kunlik Motivatsiya:**\n\n{quote}", parse_mode="Markdown")
            except Exception:
                pass
            await asyncio.sleep(60)

        await asyncio.sleep(30) # Har 30 soniyada vaqtni tekshirib turadi

# --- SERVER VA BOTNI ISHGA TUSHIRISH ---
async def handle(request):
    return web.Response(text="Bot muvaffaqiyatli ishlamoqda!")

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
    
    # Conflict Error (Ulanishlar to'qnashuvi)ni bartaraf etish uchun eski webhooklarni o'chiramiz
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Botni ishga tushiramiz
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
