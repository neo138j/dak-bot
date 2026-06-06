import os
import json
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler
)

# Load questions
with open("questions.json", encoding="utf-8") as f:
    ALL_QUESTIONS = json.load(f)

TOKEN = os.environ.get("BOT_TOKEN", "")

# Block sizes
BLOCK_SIZE = 50
BLOCKS = {
    "b1": (0, 50),
    "b2": (50, 100),
    "b3": (100, 150),
    "b4": (150, 200),
    "b5": (200, 250),
    "b6": (250, 300),
    "b7": (300, len(ALL_QUESTIONS)),
}

RANDOM_SIZES = {
    "r10": 10,
    "r20": 20,
    "r50": 50,
    "rall": len(ALL_QUESTIONS),
}

# user_sessions[user_id] = {questions, index, score, total, mode}
user_sessions = {}


def get_block_questions(key):
    start, end = BLOCKS[key]
    return ALL_QUESTIONS[start:end]


def shuffle_answers(q):
    answers = [q["correct"]] + q["wrong"]
    random.shuffle(answers)
    return answers


def build_question_message(session):
    idx = session["index"]
    total = session["total"]
    q = session["questions"][idx]
    answers = shuffle_answers(q)
    session["current_answers"] = answers
    session["correct_answer"] = q["correct"]

    text = (
        f"📝 Savol {idx + 1}/{total}\n\n"
        f"❓ {q['q']}"
    )

    keyboard = []
    labels = ["🅰️", "🅱️", "🅲️", "🅳️"]
    for i, ans in enumerate(answers):
        keyboard.append([InlineKeyboardButton(
            f"{labels[i]} {ans}",
            callback_data=f"ans_{i}"
        )])
    keyboard.append([InlineKeyboardButton("🛑 To'xtatish", callback_data="stop")])

    return text, InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"👋 Salom, {user.first_name}!\n\n"
        f"🎓 *DAK Test Bot*\n"
        f"Jami savollar: *{len(ALL_QUESTIONS)} ta*\n\n"
        f"📦 *Bloklar bo'yicha:*\n"
        f"/quiz\\_b1 — Blok 1 (1–50)\n"
        f"/quiz\\_b2 — Blok 2 (51–100)\n"
        f"/quiz\\_b3 — Blok 3 (101–150)\n"
        f"/quiz\\_b4 — Blok 4 (151–200)\n"
        f"/quiz\\_b5 — Blok 5 (201–250)\n"
        f"/quiz\\_b6 — Blok 6 (251–300)\n"
        f"/quiz\\_b7 — Blok 7 (301–{len(ALL_QUESTIONS)})\n\n"
        f"🎲 *Aralash:*\n"
        f"/quiz10 — 10 ta savol\n"
        f"/quiz20 — 20 ta savol\n"
        f"/quiz50 — 50 ta savol\n"
        f"/quizall — Barcha {len(ALL_QUESTIONS)} ta savol\n\n"
        f"/stop — Testni to'xtatish"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE, questions: list, mode: str):
    uid = update.effective_user.id
    qs = questions.copy()
    random.shuffle(qs)

    user_sessions[uid] = {
        "questions": qs,
        "index": 0,
        "score": 0,
        "total": len(qs),
        "mode": mode,
        "current_answers": [],
        "correct_answer": "",
    }

    session = user_sessions[uid]
    text, markup = build_question_message(session)
    await update.message.reply_text(
        f"🚀 Test boshlandi! Jami {len(qs)} ta savol.\n\n" + text,
        reply_markup=markup
    )


async def quiz_block(update: Update, context: ContextTypes.DEFAULT_TYPE, block_key: str):
    qs = get_block_questions(block_key)
    start_num, end_num = BLOCKS[block_key]
    await start_quiz(update, context, qs, f"Blok {block_key[1:]} ({start_num+1}–{end_num})")


async def cmd_b1(update, context): await quiz_block(update, context, "b1")
async def cmd_b2(update, context): await quiz_block(update, context, "b2")
async def cmd_b3(update, context): await quiz_block(update, context, "b3")
async def cmd_b4(update, context): await quiz_block(update, context, "b4")
async def cmd_b5(update, context): await quiz_block(update, context, "b5")
async def cmd_b6(update, context): await quiz_block(update, context, "b6")
async def cmd_b7(update, context): await quiz_block(update, context, "b7")


async def cmd_quiz10(update, context):
    qs = random.sample(ALL_QUESTIONS, 10)
    await start_quiz(update, context, qs, "Aralash 10")

async def cmd_quiz20(update, context):
    qs = random.sample(ALL_QUESTIONS, 20)
    await start_quiz(update, context, qs, "Aralash 20")

async def cmd_quiz50(update, context):
    qs = random.sample(ALL_QUESTIONS, 50)
    await start_quiz(update, context, qs, "Aralash 50")

async def cmd_quizall(update, context):
    await start_quiz(update, context, ALL_QUESTIONS, f"Barcha {len(ALL_QUESTIONS)}")


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in user_sessions:
        s = user_sessions.pop(uid)
        await update.message.reply_text(
            f"🛑 Test to'xtatildi.\n"
            f"✅ To'g'ri javoblar: {s['score']}/{s['index']} ta\n\n"
            f"/start — Boshqa test boshlash"
        )
    else:
        await update.message.reply_text("❌ Faol test yo'q.\n/start — Testni boshlash")


async def answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id

    if query.data == "stop":
        if uid in user_sessions:
            s = user_sessions.pop(uid)
            await query.edit_message_text(
                f"🛑 Test to'xtatildi.\n"
                f"✅ To'g'ri javoblar: {s['score']}/{s['index']} ta\n\n"
                f"/start — Boshqa test boshlash"
            )
        return

    if uid not in user_sessions:
        await query.edit_message_text("❌ Test topilmadi. /start buyrug'ini yuboring.")
        return

    session = user_sessions[uid]

    if not query.data.startswith("ans_"):
        return

    chosen_idx = int(query.data.split("_")[1])
    chosen = session["current_answers"][chosen_idx]
    correct = session["correct_answer"]
    is_correct = chosen == correct

    if is_correct:
        session["score"] += 1
        feedback = f"✅ To'g'ri!\n\n✔️ {correct}"
    else:
        feedback = f"❌ Noto'g'ri!\n\n❌ Siz: {chosen}\n✔️ To'g'ri: {correct}"

    session["index"] += 1

    if session["index"] >= session["total"]:
        # Quiz finished
        score = session["score"]
        total = session["total"]
        pct = round(score / total * 100)
        if pct >= 86:
            grade = "🏆 A'lo!"
        elif pct >= 71:
            grade = "👍 Yaxshi!"
        elif pct >= 56:
            grade = "😐 Qoniqarli"
        else:
            grade = "😔 Qoniqarsiz"

        await query.edit_message_text(
            f"{feedback}\n\n"
            f"{'━'*30}\n"
            f"🏁 *Test yakunlandi!*\n\n"
            f"📊 Natija: *{score}/{total}* ({pct}%)\n"
            f"🎯 Baho: {grade}\n\n"
            f"/start — Boshqa test boshlash",
            parse_mode="Markdown"
        )
        user_sessions.pop(uid, None)
    else:
        text, markup = build_question_message(session)
        await query.edit_message_text(
            f"{feedback}\n\n{'━'*30}\n\n{text}",
            reply_markup=markup
        )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz_b1", cmd_b1))
    app.add_handler(CommandHandler("quiz_b2", cmd_b2))
    app.add_handler(CommandHandler("quiz_b3", cmd_b3))
    app.add_handler(CommandHandler("quiz_b4", cmd_b4))
    app.add_handler(CommandHandler("quiz_b5", cmd_b5))
    app.add_handler(CommandHandler("quiz_b6", cmd_b6))
    app.add_handler(CommandHandler("quiz_b7", cmd_b7))
    app.add_handler(CommandHandler("quiz10", cmd_quiz10))
    app.add_handler(CommandHandler("quiz20", cmd_quiz20))
    app.add_handler(CommandHandler("quiz50", cmd_quiz50))
    app.add_handler(CommandHandler("quizall", cmd_quizall))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CallbackQueryHandler(answer_callback))

    print("✅ Bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
