import asyncio
import random
import os
from aiohttp import web
from datetime import datetime, time, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

# Sizning bot tokeningiz va guruh ID raqamingiz
TOKEN = "8843755987:AAGv5bETK_19ONTppu9APSkGJHmmeTNF2y8"
GROUP_CHAT_ID = -1004349705982

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Vaqtincha ma'lumotlar bazasi (Xotirada saqlash uchun)
users = {}
attendance_today = set()
attendance_active = False

# Inglizcha produktiv iqtiboslar
QUOTES = [
    "“The secret of getting ahead is getting started.” — Mark Twain",
    "“Don't watch the clock; do what it does. Keep going.” — Sam Levenson",
    "“Success is not final; failure is not fatal: It is the courage to continue that counts.” — Winston Churchill",
    "“Either you run the day, or the day runs you.” — Jim Rohn",
    "“Small disciplines repeated with consistency every day lead to great achievements.” — Robin Sharma",
    "“Win the morning, win the day.” — Tim Ferriss",
]


def get_attendance_keyboard():
  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[[
          InlineKeyboardButton(
              text="✅ Davomatdan o'tish (Check-in)",
              callback_data="check_in",
          )
      ]]
  )
  return keyboard


@dp.message(Command("start"))
async def cmd_start(message: Message):
  if message.chat.type == "private":
    await message.answer(
        "Salom! Bu 5 AM Club jamoasi uchun davomat boti.\nIltimos, guruhimizda"
        " botni admin qiling va ishtirok eting."
    )


# Davomat tugmasi bosilganda
@dp.callback_query(F.data == "check_in")
async def process_check_in(callback: CallbackQuery):
  global attendance_active
  if not attendance_active:
    await callback.answer(
        "Hozir davomat vaqti emas! Davomat 04:30 dan 06:00 gacha ochiq.",
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
      users[user_id]["streak"] = (
          1  # Agar bir kun qoldirsa streak boshidan boshlanadi
      )

    users[user_id]["last_date"] = today_str
    await callback.answer(
        "Tabriklaymiz! Tonggi uyg'onishingiz qayd etildi! 🔥", show_alert=True
    )
  else:
    await callback.answer(
        "Siz allaqachon bugun ro'yxatdan o'tgansiz!", show_alert=True
    )


# Reyting va streakni ko'rish buyrug'i
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


# Fon jarayonlari: Har kuni 4:30 da ochish, 6:00 da yopish va quote yuborish
async def scheduler():
  global attendance_active
  while True:
    now = datetime.now()
    current_time = now.time()

    # Soat 04:30 da davomatni ochish
    if current_time.hour == 4 and current_time.minute == 30:
      attendance_active = True
      attendance_today.clear()
      await bot.send_message(
          GROUP_CHAT_ID,
          "🌅 **Xayrli tong, 5 AM Club!**\nTonggi davomat boshlandi! Soat"
          " 06:00 gacha quyidagi tugmani bosing va uyg'onganingizni"
          " tasdiqlang!",
          reply_markup=get_attendance_keyboard(),
          parse_mode="Markdown",
      )
      await asyncio.sleep(60)

    # Soat 06:00 da davomatni yopish va natijalarni chiqarish
    elif current_time.hour == 6 and current_time.minute == 0:
      if attendance_active:
        attendance_active = False

        present_list = [users[uid]["name"] for uid in attendance_today]
        absent_list = [
            u["name"] for uid, u in users.items() if uid not in attendance_today
        ]

        report = "📊 **Tonggi davomat yakunlandi (06:00):**\n\n"
        report += (
            f"✅ **Uyg'onganlar ({len(present_list)}):**\n"
            + (
                "\n".join([f"- {name}" for name in present_list])
                if present_list
                else "Hech kim yo'q"
            )
            + "\n\n"
        )
        report += (
            f"❌ **Uyg'onmaganlar / Qolganlar ({len(absent_list)}):**\n"
            + (
                "\n".join([f"- {name}" for name in absent_list])
                if absent_list
                else "Hamma uyg'ongan!"
            )
        )

        await bot.send_message(GROUP_CHAT_ID, report, parse_mode="Markdown")
      await asyncio.sleep(60)

    # Har kuni soat 08:00 da motivatsion quote yuborish
    elif current_time.hour == 8 and current_time.minute == 0:
      quote = random.choice(QUOTES)
      await bot.send_message(
          GROUP_CHAT_ID,
          f"💡 **Daily Motivation:**\n\n{quote}",
          parse_mode="Markdown",
      )
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
# --------------------------------------

async def main():
    # Agar sizda taymer (scheduler) ishga tushadigan kod bo'lsa, u shu yerda qolsin:
    # scheduler.start() 
    
    # 1. Yolg'onchi serverni ishga tushiramiz (Render aldanishi uchun)
    import asyncio
    asyncio.create_task(web_server())
    
    # 2. Botni ishga tushiramiz
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
