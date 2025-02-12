import os
import logging
import json
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token du bot Telegram (via variables d’environnement)
TELEGRAM_BOT_TOKEN = "7516380781:AAE_XvPn_7KA6diabmcaZOqBMxBzXAHv0aw"
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Le token du bot Telegram n'est pas défini !")

# Initialisation de l'application Telegram
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Base de données JSON pour stocker les groupes et les joueurs
GROUP_DATA_FILE = "group_data.json"
GROUP_DATA = {}

# Charger les données des groupes
def load_group_data():
    global GROUP_DATA
    try:
        with open(GROUP_DATA_FILE, 'r') as f:
            GROUP_DATA = json.load(f)
    except FileNotFoundError:
        GROUP_DATA = {}

# Sauvegarder les données des groupes
def save_group_data():
    try:
        with open(GROUP_DATA_FILE, 'w') as f:
            json.dump(GROUP_DATA, f, indent=4)
        logger.info("Données sauvegardées avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde : {e}")

# Commande /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Bienvenue ! Utilisez /help pour voir les commandes.")

# Commande /help
async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "/start - Démarrer le bot\n"
        "/help - Voir la liste des commandes\n"
        "/rules - Afficher les règles\n"
        "/setrules [texte] - Ajouter une règle\n"
        "/ban [@user] - Bannir un utilisateur\n"
        "/unban [@user] - Débannir un utilisateur\n"
        "/warn [@user] - Avertir un utilisateur\n"
        "/leaderboard - Voir le classement des groupes\n"
        "/addword [mot] - Ajouter un mot interdit\n"
        "/removeword [mot] - Supprimer un mot interdit\n"
        "/listwords - Voir la liste des mots interdits\n"
        "/game - Lancer un jeu\n"
        "/score - Voir son score\n"
    )
    await update.message.reply_text(help_text)

# Commande /rules
async def show_rules(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat.id)
    rules = GROUP_DATA.get(chat_id, {}).get("rules", "Aucune règle définie.")
    await update.message.reply_text(f"Règles :\n{rules}")

# Commande /setrules
async def add_rules(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat.id)
    rules_text = ' '.join(context.args)

    if not rules_text:
        await update.message.reply_text("Veuillez fournir le texte de la règle après la commande.")
        return

    if chat_id not in GROUP_DATA:
        GROUP_DATA[chat_id] = {}

    GROUP_DATA[chat_id]["rules"] = rules_text
    save_group_data()
    await update.message.reply_text(f"Règles mises à jour :\n{rules_text}")

# Commande /ban
async def ban_user(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("Usage: /ban @username")
        return
    user = context.args[0]
    await update.message.reply_text(f"L'utilisateur {user} a été banni ! 🚫")

# Commande /unban
async def unban_user(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("Usage: /unban @username")
        return
    user = context.args[0]
    await update.message.reply_text(f"L'utilisateur {user} a été débanni ! ✅")

# Commande /warn
async def warn_user(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("Usage: /warn @username")
        return
    user = context.args[0]
    await update.message.reply_text(f"L'utilisateur {user} a reçu un avertissement ! ⚠️")

# Commande /leaderboard
async def leaderboard(update: Update, context: CallbackContext):
    leaderboard_text = "Classement des groupes :\n"
    for group, data in GROUP_DATA.items():
        leaderboard_text += f"{group}: {data.get('score', 0)} points\n"
    await update.message.reply_text(leaderboard_text)

# Générer une suite logique aléatoire
def generate_math_sequence():
    sequence_type = random.choice(["arithmétique", "géométrique", "carrés", "fibonacci"])
    
    if sequence_type == "arithmétique":
        start = random.randint(1, 20)
        step = random.randint(2, 10)
        sequence = [start + step * i for i in range(4)]
        answer = sequence[-1] + step
    
    elif sequence_type == "géométrique":
        start = random.randint(1, 5)
        factor = random.randint(2, 5)
        sequence = [start * (factor ** i) for i in range(4)]
        answer = sequence[-1] * factor

    elif sequence_type == "carrés":
        start = random.randint(1, 5)
        sequence = [(start + i) ** 2 for i in range(4)]
        answer = (start + 4) ** 2

    else:  # Fibonacci
        a, b = random.randint(1, 5), random.randint(1, 5)
        sequence = [a, b]
        for _ in range(2):
            sequence.append(sequence[-1] + sequence[-2])
        answer = sequence[-1] + sequence[-2]

    return sequence, answer

# Commande /game pour commencer un jeu
async def start_game(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    sequence, answer = generate_math_sequence()

    # Sauvegarde de la réponse attendue
    GAME_DATA[user_id] = {"sequence": sequence, "answer": answer}
    save_game_data()

    await update.message.reply_text(f"🔢 Trouvez le nombre suivant :\n{', '.join(map(str, sequence))}, ?")

# Vérifier la réponse de l'utilisateur
async def check_answer(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    if user_id not in GAME_DATA:
        return  # Ignorer les messages hors du jeu

    try:
        user_answer = int(update.message.text)
    except ValueError:
        return  # L'utilisateur n'a pas envoyé un nombre

    correct_answer = GAME_DATA[user_id]["answer"]

    if user_answer == correct_answer:
        await update.message.reply_text("✅ Bravo ! Bonne réponse. 🎉 +10 points 🏆")
        del GAME_DATA[user_id]  # Effacer le jeu en cours
        save_game_data()
    else:
        await update.message.reply_text("❌ Mauvaise réponse. Réessayez !")


# Commande /score
async def get_score(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    score = GROUP_DATA.get(user_id, {}).get("score", 0)
    await update.message.reply_text(f"🏆 Votre score actuel : {score}")

# Initialisation de Flask
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Le bot Telegram est en ligne ! 🚀"

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
async def webhook():
    """Route du webhook qui traite les mises à jour de Telegram"""
    data = request.get_json()
    logger.info(f"Requête reçue : {json.dumps(data, indent=4)}")

    if not data:
        return "Bad Request", 400

    update = Update.de_json(data, application.bot)
    await application.initialize()
    await application.process_update(update)

    return "OK", 200

# Démarrer le bot et Flask
def main():
    load_group_data()

    # Ajouter les handlers de commandes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("rules", show_rules))
    application.add_handler(CommandHandler("setrules", add_rules))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CommandHandler("warn", warn_user))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("game", start_game))
    application.add_handler(CommandHandler("score", get_score))

    # Définir le webhook
    webhook_url = f"https://ton-domaine-sur-render.com/{TELEGRAM_BOT_TOKEN}"
    application.bot.set_webhook(url=webhook_url)

    # Démarrer Flask
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    main()
