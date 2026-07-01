"""
ULTRA BOT - для Scalingo
Использует python-telegram-bot (легче чем Telethon)
"""
import asyncio
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

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
                json.dump({
                    "subs": list(self.subs),
                    "fav": self.fav,
                    "np": self.np,
                    "wait": self.wait,
                    "users": self.users
                }, f)
        except: pass

data = Data()

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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Напиши сообщение — я передам.\n/status — статус\n/sub — подписка")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(status_msg(), parse_mode="HTML")

async def sub_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data.subs.add(update.effective_chat.id)
    data.save()
    await update.message.reply_text("✅ Подписка!")

async def unsub_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data.subs.discard(update.effective_chat.id)
    data.save()
    await update.message.reply_text("✅ Отписка")

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = f"👑 Панель\n\n👥 {len(data.subs)}\n❤️ {len(data.fav.split(chr(10))) if data.fav else 0}\n💬 {len(data.wait)}\n🎵 {data.np or '—'}"
    await update.message.reply_text(msg)

async def set_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    t = " ".join(context.args)
    data.np = None if t.lower() in ["off","none","стоп"] else t
    data.save()
    await update.message.reply_text(f"🎵 {'Сброшено' if not data.np else 'Играет: '+t}")
    
    # Уведомить подписчиков
    if data.subs:
        for sub in data.subs:
            try:
                await context.bot.send_message(sub, f"🔄 Трек: {data.np or 'остановлен'}\n\n{status_msg()}", parse_mode="HTML")
            except: pass

async def fav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    t = " ".join(context.args)
    data.fav = (data.fav + "\n" + t) if data.fav else t
    data.save()
    await update.message.reply_text(f"❤️ {t}")

async def delfav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    t = " ".join(context.args)
    if data.fav:
        data.fav = "\n".join([x for x in data.fav.split("\n") if x.strip() != t]) or None
        data.save()
    await update.message.reply_text("✅ Удалено")

async def favoff_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    data.fav = None
    data.save()
    await update.message.reply_text("✅ Очищено")

async def reply_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target = int(context.args[0])
        text = " ".join(context.args[1:])
        await context.bot.send_message(target, f"📩 Ответ:\n\n{text}")
        await update.message.reply_text("✅")
        if str(target) in data.wait: del data.wait[str(target)]; data.save()
    except: await update.message.reply_text("❌ /reply ID текст")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    text = " ".join(context.args)
    ok = 0
    for sub in data.subs:
        try:
            await context.bot.send_message(sub, f"📢 {text}")
            ok += 1
        except: pass
    await update.message.reply_text(f"✅ {ok}/{len(data.subs)}")

async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if data.users:
        m = "👥 Пользователи:\n\n"
        for uid, info in list(data.users.items())[:15]:
            m += f"<code>{uid}</code> {info['name']}\n"
        await update.message.reply_text(m, parse_mode="HTML")
    else: await update.message.reply_text("Пусто")

async def waiting_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if data.wait:
        m = "💬 Ждут:\n\n"
        for uid, info in data.wait.items():
            m += f"<code>{uid}</code> {info['name']}\n  {info['t'][:40]}\n\n"
        await update.message.reply_text(m, parse_mode="HTML")
    else: await update.message.reply_text("Никто")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)
    name = user.first_name or "?"
    text = update.message.text or ""
    
    if user.id == ADMIN_ID: return  # Админ использует команды
    
    # Сохраняем
    if uid not in data.users:
        data.users[uid] = {"name": name, "c": 0}
    data.users[uid]["c"] += 1
    data.users[uid]["name"] = name
    
    if uid not in data.wait:
        data.wait[uid] = {"name": name, "t": text}
    else:
        data.wait[uid]["t"] = text
    
    data.save()
    
    # Пересылаем админу
    msg = f"💬 <b>{name}</b> [<code>{uid}</code>]\n🕐 {datetime.now().strftime('%H:%M')}\n\n📝 {text}\n\n<code>/reply {uid} ответ</code>"
    
    keyboard = [[
        InlineKeyboardButton("📝 Ответить", callback_data=f"reply_{uid}"),
        InlineKeyboardButton("✅ Прочитано", callback_data=f"read_{uid}")
    ]]
    
    await context.bot.send_message(ADMIN_ID, msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    await update.message.reply_text("👋 Передал! Отвечу позже.\n/status")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID: return
    
    action, uid = query.data.split("_", 1)
    
    if action == "reply":
        await query.edit_message_text(f"📝 <code>/reply {uid} ответ</code>", parse_mode="HTML")
    elif action == "read":
        if uid in data.wait: del data.wait[uid]; data.save()
        await query.edit_message_text("✅ Прочитано")
    
    await query.answer()

# ================= ЗАПУСК =================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("sub", sub_cmd))
    app.add_handler(CommandHandler("unsub", unsub_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("set", set_cmd))
    app.add_handler(CommandHandler("fav", fav_cmd))
    app.add_handler(CommandHandler("delfav", delfav_cmd))
    app.add_handler(CommandHandler("favoff", favoff_cmd))
    app.add_handler(CommandHandler("reply", reply_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(CommandHandler("waiting", waiting_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("✅ Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
