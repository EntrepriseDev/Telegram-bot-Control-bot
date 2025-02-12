import logging
import json
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token du bot Telegram
TELEGRAM_BOT_TOKEN = "7516380781:AAE_XvPn_7KA6diabmcaZOqBMxBzXAHv0aw"

# Base de données des groupes (stockée en JSON)
GROUP_DATA = {}

# Charger les données depuis le fichier JSON
def load_group_data():
    global GROUP_DATA
    try:
        with open('group_data.json', 'r') as f:
            GROUP_DATA = json.load(f)
    except FileNotFoundError:
        GROUP_DATA = {}

# Sauvegarder les données
def save_group_data():
    try:
        with open('group_data.json', 'w') as f:
            json.dump(GROUP_DATA, f, indent=4)
        logger.info("Données sauvegardées avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde : {e}")

# Commande /start
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Bienvenue ! Utilisez /help pour voir les commandes.")

# Commande /help
async def help_command(update: Update, context: CallbackContext) -> None:
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
    )
    await update.message.reply_text(help_text)

# Commande /rules
async def show_rules(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.message.chat.id)
    rules = GROUP_DATA.get(chat_id, {}).get("rules", "Aucune règle définie.")
    await update.message.reply_text(f"Règles :\n{rules}")

# Commande /setrules
async def add_rules(update: Update, context: CallbackContext) -> None:
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
async def ban_user(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Veuillez mentionner un utilisateur à bannir.")
        return
    await update.message.reply_text(f"L'utilisateur {context.args[0]} a été banni.")

# Commande /unban
async def unban_user(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Veuillez mentionner un utilisateur à débannir.")
        return
    await update.message.reply_text(f"L'utilisateur {context.args[0]} a été débanni.")

# Commande /warn
async def warn_user(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Veuillez mentionner un utilisateur à avertir.")
        return
    await update.message.reply_text(f"L'utilisateur {context.args[0]} a été averti.")

# Commande /leaderboard
async def leaderboard(update: Update, context: CallbackContext) -> None:
    leaderboard_text = "Classement des groupes :\n"
    for group, data in GROUP_DATA.items():
        leaderboard_text += f"{group}: {data.get('score', 0)} points\n"
    await update.message.reply_text(leaderboard_text)

# Initialisation de Flask
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Le bot Telegram est en ligne ! 🚀"

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    logger.info(f"Requête reçue : {json.dumps(data, indent=4)}")  # Debug

    if not data:
        logger.error("Requête vide reçue.")
        return "Bad Request", 400
    
    update = Update.de_json(data, bot)
    logger.info("Mise à jour Telegram reçue, traitement en cours...")

    import asyncio

    async def process():
        await application.initialize()  # Correction ici
        await application.process_update(update)

    asyncio.run(process())  # Exécuter la coroutine correctement

    return "OK", 200

def main():
    """Démarrer l'application Flask et le bot Telegram"""
    load_group_data()

    global bot
    global application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    bot = application.bot

    # Ajouter les commandes au bot
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("rules", show_rules))
    application.add_handler(CommandHandler("setrules", add_rules))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CommandHandler("warn", warn_user))
    application.add_handler(CommandHandler("leaderboard", leaderboard))

    # Définir le webhook
    webhook_url = f"https://telegram-bot-control-bot.onrender.com/{TELEGRAM_BOT_TOKEN}"
    bot.set_webhook(url=webhook_url)

    # Démarrer Flask
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    main()
