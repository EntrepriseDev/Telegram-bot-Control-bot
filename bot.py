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

# Token du bot Telegram (défini via les variables d’environnement)
TELEGRAM_BOT_TOKEN = "7516380781:AAE_XvPn_7KA6diabmcaZOqBMxBzXAHv0aw"
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Le token du bot Telegram n'est pas défini !")

# Initialisation de l'application Telegram
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Base de données JSON pour stocker les groupes
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

# Commande /leaderboard
async def leaderboard(update: Update, context: CallbackContext):
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
async def webhook():
    """Route du webhook qui traite les mises à jour de Telegram"""
    data = request.get_json()
    logger.info(f"Requête reçue : {json.dumps(data, indent=4)}")  # Debug

    if not data:
        logger.error("Requête vide reçue.")
        return "Bad Request", 400

    update = Update.de_json(data, application.bot)

    # Initialisation correcte avant le traitement
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
    application.add_handler(CommandHandler("leaderboard", leaderboard))

    # Définir le webhook
    webhook_url = f"https://ton-domaine-sur-render.com/{TELEGRAM_BOT_TOKEN}"
    application.bot.set_webhook(url=webhook_url)

    # Démarrer Flask
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    main()
