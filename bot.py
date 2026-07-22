import os
import asyncio
import random
from datetime import datetime, time, timedelta
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

# Sizning bot tokeningiz va guruh ID raqamingiz
TOKEN = "8843755987:AAEy-VnJ0biQJBop80PwgnCUdKGuv_qgOwc"
GROUP_CHAT_ID = -1004349705982
ADMIN_ID = 123456789  # O'zingizning Telegram ID raqamingizni yozing

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Vaqtincha ma'lumotlar bazasi (Xotirada saqlash uchun)
users = {}
attendance_today = set()
attendance_active = False

# Internetdan avtomatik iqtibos (quote) olib keluvchi funksiya
async def get_random_quote_from_internet():
    url = "https://zenquotes.io/api/random"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    quote_text = data[0]['q']
                    author = data[0]['a']
                    return f"“{quote_text}” — {author}"
        except Exception:
            pass
    # Agar internetda xatolik bo'lsa, zaxiradagi matn chiqadi
    return "“Small disciplines repeated with consistency every day lead to great achievements.” — Robin Sharma"

# --- LICHKA MENYULARI ---
def get_user_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Mening statistikam"), KeyboardButton(text="🏆 Top Reyting")],
            [KeyboardButton(text="💡 Tonggi motivatsiya"), KeyboardButton(text="⚙️ Vaqtni o'zgartirish")],
            [KeyboardButton(text="ℹ️ Yordam / Qoidalar")]
        ],
        resize_keyboard=True
    )

def get_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Mening statistikam"), KeyboardButton(text="🏆 Top Reyting")],
            [KeyboardButton(text="💡 Tonggi motivatsiya"), KeyboardButton(text="⚙️ Vaqtni o'zgartirish")],
            [KeyboardButton(text="📢 Broadcast (Xabar yuborish)"), KeyboardButton(text="👥 Ishtirokchilar")]
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

# --- /start BUYRUQI ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    if message.chat.type == "private":
        if message.from_user.id == ADMIN_ID:
            await message.answer("Assalomu alaykum, Admin! Xush kelibsiz.", reply_markup=get_admin_menu())
        else:
            await message.answer("Xush kelibsiz! 5 AM Club botiga marhamat. Kerakli tugmani tanlang:", reply_markup=get_user_menu())
    else:
        await message.answer("Bot guruhda ishlamoqda. Shaxsiy statistika va menyular uchun menga lichkada yozing!")


# --- DAVOMAT TUGMASI BOSILGANDA ---
@dp.callback_query(F.data == "check_in")
async def process_check_in(callback: CallbackQuery):
    global attendance_active
    if not attendance_active:
        await callback.answer(
            "Hozir davomat vaqti emas! Davomat 20:20 dan 20:25 gacha ochiq.",
            show_alert=True,
        )
        return

    user_id = callback.from_user.id
    user_name = callback.from_user.first_name
    today_str = datetime.now().strftime("%Y-%m-%d")

    if user_id not in users:
        users[user_id] = {"name": user_name, "streak": 0, "last_date": ""}

    # Agar bugun allaqachon bosmagan bo'lsa
    if user_id not in attendance_today:
        attendance_today.add(user_id)

        # Streakni hisoblash
        last_date = users[user_id]["last_date"]
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        if last_date == yesterday_str or last_date == "":
            users[user_id]["streak"] += 1
        elif last_date != today_str:
            users[user_id]["streak"] = 1  # Agar bir kun qoldirsa streak boshidan boshlanadi

        users[user_id]["last_date"] = today_str
        await callback.answer(
            "Tabriklaymiz! O'g'onishingiz / ishtirokingiz qayd etildi! 🔥", show_alert=True
        )
    else:
        await callback.answer(
            "Siz allaqachon bugun ro'yxatdan o'tgansiz!", show_alert=True
        )


# --- REYTING (Lichka yoki guruh uchun) ---
@dp.message(F.text == "🏆 Top Reyting")
@dp.message(Command("ranking"))
async def cmd_ranking(message: Message):
    if not users:
        await message.answer("Hozircha reytingda ishtirokchilar yo'q.")
        return

    # Streak bo'yicha saralash
    sorted_users = sorted(
        users.values(), key=lambda x: x["streak"], reverse=True
    )

    text = "🏆 **5 AM Club Intizom Reytingi (Streak):**\n\n"
    for idx, u in enumerate(sorted_users[:10], 1):
        text += f"{idx}. {u['name']} — 🔥 {u['streak']} kun ketma-ket\n"

    await message.answer(text, parse_mode="Markdown")


# --- LICHKA TUGMALARI ---
@dp.message(F.text == "📊 Mening statistikam")
async def user_stats(message: Message):
    user_id = message.from_user.id
    user_data = users.get(user_id, {"streak": 0})
    streak = user_data.get("streak", 0)
    await message.answer(f"📊 **Sizning statistikangiz:**\n\n- Joriy streak: {streak} kun")

@dp.message(F.text == "💡 Tonggi motivatsiya")
async def morning_motivation(message: Message):
    quote = await get_random_quote_from_internet()
    await message.answer(f"💡 **Kun motivatsiyasi:**\n\n{quote}")

@dp.message(F.text == "⚙️ Vaqtni o'zgartirish")
async def change_time(message: Message):
    await message.answer("⏰ O'zingizga qulay vaqtni tanlash funksiyasi tez orada ishga tushadi!")

@dp.message(F.text == "ℹ️ Yordam / Qoidalar")
async def help_rules(message: Message):
    await message.answer("ℹ️ **Qoidalar:**\nBelgilangan vaqtda bot tashlagan xabarga kirib, davomat tugmasini bosishingiz kerak.")

@dp.message(F.text == "📢 Broadcast (Xabar yuborish)")
async def admin_broadcast(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("📢 Hammaga yuboriladigan xabar matnini kiriting:")
    else:
        await message.answer("Kechirasiz, bu buyruq faqat admin uchun.")

@dp.message(F.text == "👥 Ishtirokchilar")
async def admin_users(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"👥 Jami ro'yxatdan o'tganlar soni: {len(users)} ta")
    else:
        await message.answer("Kechirasiz, bu buyruq faqat admin uchun.")


# --- TEST REJIMI UCHUN SCHEDULER (20:20, 20:25, 20:30) ---
async def scheduler():
    global attendance_active
    while True:
        now = datetime.now()
        current_time = now.time()

        # 1. Soat 20:20 da davomatni ochish
        if current_time.hour == 20 and current_time.minute == 20:
            attendance_active = True
            attendance_today.clear()
            try:
                await bot.send_message(
                    GROUP_CHAT_ID,
                    "🌅 **Test davomat boshlandi!**\nSoat 20:25 gacha quyidagi tugmani bosing va ishtirokingizni tasdiqlang!",
                    reply_markup=get_attendance_keyboard(),
                    parse_mode="Markdown",
                )
            except Exception as e:
                print(f"Xatolik (20:20): {e}")
            await asyncio.sleep(60)

        # 2. Soat 20:25 da davomatni yopish va hisobot berish
        elif current_time.hour == 20 and current_time.minute == 25:
            if attendance_active:
                attendance_active = False

                present_list = [users[uid]["name"] for uid in attendance_today]
                absent_list = [
                    u["name"] for uid, u in users.items() if uid not in attendance_today
                ]

                report = "📊 **Test davomat yakunlandi (20:25):**\n\n"
                report += (
                    f"✅ **Ishtirok etganlar ({len(present_list)}):**\n"
                    + ("\n".join([f"- {name}" for name in present_list]) if present_list else "Hech kim yo'q")
                    + "\n\n"
                )
                report += (
                    f"❌ **Ishtirok etmaganlar ({len(absent_list)}):**\n"
                    + ("\n".join([f"- {name}" for name in absent_list]) if absent_list else "Hamma qatnashdi!")
                )

                try:
                    await bot.send_message(GROUP_CHAT_ID, report, parse_mode="Markdown")
                except Exception as e:
                    print(f"Xatolik (20:25): {e}")
            await asyncio.sleep(60)

        # 3. Soat 20:30 da internetdan olingan iqtibosni (quote) yuborish
        elif current_time.hour == 20 and current_time.minute == 30:
            quote = await get_random_quote_from_internet()
            try:
                await bot.send_message(
                    GROUP_CHAT_ID,
                    f"💡 **Daily Motivation:**\n\n{quote}",
                    parse_mode="Markdown",
                )
            except Exception as e:
                print(f"Xatolik (20:30): {e}")
            await asyncio.sleep(60)

        await asyncio.sleep(30)


# --- RENDER UCHUN YOLG'ONCHI SERVER ---
async def handle(request):
    return web.Response(text="Bot muvaffaqiyatli ishlayapti!")

async def web_server():
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    # 1. Yolg'onchi serverni ishga tushiramiz
    asyncio.create_task(web_server())
    # 2. Vaqtni o'lchaydigan taymerni (scheduler) ishga tushiramiz
    asyncio.create_task(scheduler())
    # 3. Botni ishga tushiramiz (eski seanslarni tozalovchi parametr bilan)
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
