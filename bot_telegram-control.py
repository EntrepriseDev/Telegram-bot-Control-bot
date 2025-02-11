import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "7516380781:AAE_XvPn_7KA6diabmcaZOqBMxBzXAHv0aw"

# Connexion à la base de données
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS banned_words (
            group_id INTEGER,
            word TEXT,
            PRIMARY KEY (group_id, word)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_scores (
            group_id INTEGER PRIMARY KEY,
            score INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# Ajouter un mot interdit
async def add_banned_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Utilisation : /addword <mot>")
        return
    
    word = context.args[0].lower()
    group_id = update.message.chat.id
    
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO banned_words (group_id, word) VALUES (?, ?)", (group_id, word))
        conn.commit()
        await update.message.reply_text(f"Le mot '{word}' a été ajouté à la liste des interdictions !")
    except sqlite3.IntegrityError:
        await update.message.reply_text("Ce mot est déjà interdit !")
    finally:
        conn.close()

# Supprimer un mot interdit
async def remove_banned_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Utilisation : /removeword <mot>")
        return
    
    word = context.args[0].lower()
    group_id = update.message.chat.id
    
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM banned_words WHERE group_id = ? AND word = ?", (group_id, word))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"Le mot '{word}' a été supprimé de la liste des interdictions !")

# Vérifier et supprimer les messages contenant des mots interdits
async def filter_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    group_id = update.message.chat.id
    
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT word FROM banned_words WHERE group_id = ?", (group_id,))
    banned_words = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    if any(word in text for word in banned_words):
        await update.message.delete()
        await update.message.reply_text("🚫 Message supprimé : langage inapproprié !")

# Démarrer un jeu simple (exemple : quiz)
async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.message.chat.id
    await update.message.reply_text("🎲 Début du jeu ! Répondez à cette question :\n\nQuel est la capitale de la France ? (Répondez avec /answer <réponse>)")
    context.bot_data[group_id] = "paris"

# Vérifier la réponse au jeu
async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Utilisation : /answer <réponse>")
        return
    
    group_id = update.message.chat.id
    answer = " ".join(context.args).lower()
    
    if group_id in context.bot_data and context.bot_data[group_id] == answer:
        await update.message.reply_text("🎉 Bonne réponse ! +10 points pour le groupe !")
        
        conn = sqlite3.connect("bot_data.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO group_scores (group_id, score) VALUES (?, 10) ON CONFLICT(group_id) DO UPDATE SET score = score + 10", (group_id,))
        conn.commit()
        conn.close()
    else:
        await update.message.reply_text("❌ Mauvaise réponse, essayez encore !")

# Afficher le classement des groupes
async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT group_id, score FROM group_scores ORDER BY score DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        await update.message.reply_text("Aucun groupe n'a encore marqué de points.")
        return
    
    leaderboard = "🏆 Classement des meilleurs groupes :\n"
    for rank, (group_id, score) in enumerate(rows, start=1):
        leaderboard += f"{rank}. Groupe {group_id} - {score} points\n"
    
    await update.message.reply_text(leaderboard)

# Initialiser le bot
async def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("addword", add_banned_word))
    app.add_handler(CommandHandler("removeword", remove_banned_word))
    app.add_handler(CommandHandler("startgame", start_game))
    app.add_handler(CommandHandler("answer", check_answer))
    app.add_handler(CommandHandler("leaderboard", show_leaderboard))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_messages))
    
    print("Le bot est en cours d'exécution...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())