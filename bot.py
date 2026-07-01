"""
ULTRA BOT - для Scalingo (aiogram)
"""
import asyncio
import json
import os
import logging
import sys
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "8839213272:AAFG0LmyA1_L3aOwL4gx3dAuQYiHGx4C7s8"
ADMIN_ID = 8750877979
DATA_FILE = "data.json"

# ================= ДАННЫЕ =================
class Data:
    def __init__(self):
        self.subs = set()
        self.fav = None
        self.np = None
        self.wait = {}
        self.users = {}
        self.load()
    
    def load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE) as f:
                    d = json.load(f)
                    self.subs = set(d.get("subs", []))
                    self.fav = d.get("fav")
                    self.np = d.get("np")
                    self.wait = d.get("wait", {})
                    self.users = d.get("users", {})
            except: pass
    
    def save(self):
        try:
            with open(DATA_FILE, "w") as f:
                json.dump({"subs": list(self.subs), "fav": self.fav, "np": self.np, "wait": self.wait, "users": self.users}, f)
        except: pass

data = Data()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ================= СТАТУС =================
def status_msg():
    m = "📊 <b>СТАТУС</b>\n\n"
    m += "<b>TG:</b> смотри в профиле\n\n"
    m += "<b>🎵 Сейчас играет:</b> "
    m += data.np if data.np else "ничего"
    m += "\n\n<b>❤️ Любимые треки:</b>\n"
    if data.fav:
        for t in data.fav.split("\n"):
            if t.strip(): m += f"• {t.strip()}\n"
    else:
        m += "• пока нет\n"
    m += f"\n<i>Обновлено: {datetime.now().strftime('%H:%M:%S')}</i>"
    return m

# ================= КОМАНДЫ =================
@dp.message(Command("start", "help"))
async def start_cmd(message: types.Message):
    await message.answer("👋 Привет! Напиши сообщение — я передам.\n/status — статус\n/sub — подписка")

@dp.message(Command("status"))
async def status_cmd(message: types.Message):
    await message.answer(status_msg())

@dp.message(Command("sub"))
async def sub_cmd(message: types.Message):
    data.subs.add(message.chat.id)
    data.save()
    await message.answer("✅ Подписка!")

@dp.message(Command("unsub"))
async def unsub_cmd(message: types.Message):
    data.subs.discard(message.chat.id)
    data.save()
    await message.answer("✅ Отписка")

@dp.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    msg = f"👑 Панель\n\n👥 {len(data.subs)}\n❤️ {len(data.fav.split(chr(10))) if data.fav else 0}\n💬 {len(data.wait)}\n🎵 {data.np or '—'}"
    await message.answer(msg)

@dp.message(Command("set"))
async def set_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    t = message.text[5:].strip() if len(message.text) > 5 else ""
    data.np = None if t.lower() in ["off","none","стоп",""] else t
    data.save()
    await message.answer(f"🎵 {'Сброшено' if not data.np else 'Играет: '+t}")
    
    for sub in data.subs:
        try: await bot.send_message(sub, f"🔄 Трек: {data.np or 'остановлен'}\n\n{status_msg()}")
        except: pass

@dp.message(Command("fav"))
async def fav_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    t = message.text[5:].strip() if len(message.text) > 5 else ""
    if t:
        data.fav = (data.fav + "\n" + t) if data.fav else t
        data.save()
        await message.answer(f"❤️ {t}")

@dp.message(Command("delfav"))
async def delfav_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    t = message.text[8:].strip() if len(message.text) > 8 else ""
    if data.fav and t:
        data.fav = "\n".join([x for x in data.fav.split("\n") if x.strip() != t]) or None
        data.save()
    await message.answer("✅ Удалено")

@dp.message(Command("favoff"))
async def favoff_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    data.fav = None
    data.save()
    await message.answer("✅ Очищено")

@dp.message(Command("reply"))
async def reply_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        target = int(parts[1])
        text = " ".join(parts[2:])
        await bot.send_message(target, f"📩 Ответ:\n\n{text}")
        await message.answer("✅")
        if str(target) in data.wait: del data.wait[str(target)]; data.save()
    except: await message.answer("❌ /reply ID текст")

@dp.message(Command("broadcast"))
async def broadcast_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text[10:].strip() if len(message.text) > 10 else ""
    ok = 0
    for sub in data.subs:
        try:
            await bot.send_message(sub, f"📢 {text}")
            ok += 1
        except: pass
    await message.answer(f"✅ {ok}/{len(data.subs)}")

@dp.message(Command("users"))
async def users_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    if data.users:
        m = "👥 Пользователи:\n\n"
        for uid, info in list(data.users.items())[:15]:
            m += f"<code>{uid}</code> {info['name']}\n"
        await message.answer(m)
    else: await message.answer("Пусто")

@dp.message(Command("waiting"))
async def waiting_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    if data.wait:
        m = "💬 Ждут:\n\n"
        for uid, info in data.wait.items():
            m += f"<code>{uid}</code> {info['name']}\n  {info['t'][:40]}\n\n"
        await message.answer(m)
    else: await message.answer("Никто")

# ================= СООБЩЕНИЯ =================
@dp.message()
async def handle_message(message: types.Message):
    user = message.from_user
    uid = str(user.id)
    name = user.first_name or "?"
    text = message.text or ""
    
    if user.id == ADMIN_ID: return
    
    if uid not in data.users:
        data.users[uid] = {"name": name, "c": 0}
    data.users[uid]["c"] += 1
    data.users[uid]["name"] = name
    
    if uid not in data.wait:
        data.wait[uid] = {"name": name, "t": text}
    else:
        data.wait[uid]["t"] = text
    
    data.save()
    
    msg = f"💬 <b>{name}</b> [<code>{uid}</code>]\n🕐 {datetime.now().strftime('%H:%M')}\n\n📝 {text}\n\n<code>/reply {uid} ответ</code>"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📝 Ответить", callback_data=f"reply_{uid}"),
        InlineKeyboardButton(text="✅ Прочитано", callback_data=f"read_{uid}")
    ]])
    
    await bot.send_message(ADMIN_ID, msg, reply_markup=keyboard)
    await message.answer("👋 Передал! Отвечу позже.\n/status")

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    
    action, uid = callback.data.split("_", 1)
    
    if action == "reply":
        await callback.message.edit_text(f"📝 <code>/reply {uid} ответ</code>")
    elif action == "read":
        if uid in data.wait: del data.wait[uid]; data.save()
        await callback.message.edit_text("✅ Прочитано")
    
    await callback.answer()

# ================= ЗАПУСК =================
async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())