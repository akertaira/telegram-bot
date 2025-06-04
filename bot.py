import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Загрузка данных из info.json
with open("info.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Словари для состояния
user_state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_user.id] = {}
    authors = list(data.keys())
    keyboard = [[author] for author in authors]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Приветствую! Я — бот по русской литературе XIX века.\n\n"
        "📖 Что я умею:\n"
        "— рассказывать о великих писателях\n"
        "— делиться кратким содержанием их произведений\n"
        "— проводить тесты для самопроверки\n\n"
        "👉 Начнём? Выберите писателя:",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    state = user_state.get(user_id, {})

    # Выбор автора
    if text in data:
        user_state[user_id] = {"author": text}
        bio = data[text]["bio"]
        works = list(data[text]["works"].keys())
        keyboard = [[work] for work in works]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(f"✒️ {text}\n{bio}\n\nВыберите произведение:", reply_markup=reply_markup)
        return

    # Выбор произведения
    if "author" in state and text in data[state["author"]]["works"]:
        user_state[user_id]["work"] = text
        summary = data[state["author"]]["works"][text]["summary"]
        user_state[user_id]["quiz"] = data[state["author"]]["works"][text]["questions"]
        user_state[user_id]["q_index"] = 0
        user_state[user_id]["score"] = 0
        reply_markup = ReplyKeyboardMarkup([["✅ Я изучил(а), перейти к тесту"]], resize_keyboard=True)
        await update.message.reply_text(f"📘 {text}\n\n{summary}", reply_markup=reply_markup)
        return

    # Переход к тесту
    if text.startswith("✅ Я изучил"):
        await send_question(update, user_id)
        return

    # Ответ на вопрос
    if "quiz" in state:
        current_q = state["quiz"][state["q_index"] - 1]
        correct = current_q["answer"]
        if text == correct:
            user_state[user_id]["score"] += 1
            await update.message.reply_text("✅ Верно!")
        else:
            await update.message.reply_text(f"❌ Неверно. Правильный ответ: {correct}")

        if state["q_index"] < len(state["quiz"]):
            await send_question(update, user_id)
        else:
            total = len(state["quiz"])
            score = state["score"]
            keyboard = [["🔙 Вернуться к списку писателей"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                f"🧾 Вы завершили тест!\n🎯 Ваш результат: {score} из {total} верно.",
                reply_markup=reply_markup
            )
            user_state[user_id] = {}
        return

    # Повторный запуск или выход
    if text == "🔙 Вернуться к списку писателей":
        return await start(update, context)


    await update.message.reply_text("Пожалуйста, выберите вариант из предложенного меню.")

async def send_question(update: Update, user_id):
    state = user_state[user_id]
    question_data = state["quiz"][state["q_index"]]
    state["q_index"] += 1

    keyboard = [[option] for option in question_data["options"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(f"❓ Вопрос {state['q_index']} из {len(state['quiz'])}\n{question_data['question']}", reply_markup=reply_markup)

def main():
    app = ApplicationBuilder().token("7589109384:AAFKf4Ca8OFvYSwzeQqTUqEt6AMwWTQmldM").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == '__main__':
    main()
