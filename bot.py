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

# Token du bot Telegram
TELEGRAM_BOT_TOKEN = "7516380781:AAE_XvPn_7KA6diabmcaZOqBMxBzXAHv0aw"
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Le token du bot Telegram n'est pas défini !")

# Initialisation de l'application Telegram
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Base de données JSON pour stocker les groupes et les joueurs
GROUP_DATA_FILE = "group_data.json"
GROUP_DATA = {}

def load_group_data():
    global GROUP_DATA
    try:
        with open(GROUP_DATA_FILE, 'r') as f:
            GROUP_DATA = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        GROUP_DATA = {}

def save_group_data():
    try:
        with open(GROUP_DATA_FILE, 'w') as f:
            json.dump(GROUP_DATA, f, indent=4)
        logger.info("Données sauvegardées avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde : {e}")

async def is_admin(update: Update):
    chat_member = await update.message.chat.get_member(update.message.from_user.id)
    return chat_member.status in ['administrator', 'creator']

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Bienvenue ! Utilisez /help pour voir les commandes.")

async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "/start - Démarrer le bot\n"
        "/help - Voir la liste des commandes\n"
        "/rules - Afficher les règles\n"
        "/setrules [texte] - Ajouter une règle\n"
        "/ban [@user] - Bannir un utilisateur\n"
        "/unban [@user] - Débannir un utilisateur\n"
        "/mute [@user] - Mettre un utilisateur en sourdine\n"
        "/unmute [@user] - Réactiver un utilisateur\n"
        "/warn [@user] - Avertir un utilisateur\n"
        "/warnlist - Voir les avertissements\n"
        "/leaderboard - Voir le classement des groupes\n"
        "/resetleaderboard - Réinitialiser le classement\n"
    )
    await update.message.reply_text(help_text)

async def mute_user(update: Update, context: CallbackContext):
    if not await is_admin(update):
        await update.message.reply_text("Seuls les admins peuvent mettre en sourdine.")
        return
    await update.message.reply_text("Fonction en cours de développement.")

async def unmute_user(update: Update, context: CallbackContext):
    if not await is_admin(update):
        await update.message.reply_text("Seuls les admins peuvent réactiver un utilisateur.")
        return
    await update.message.reply_text("Fonction en cours de développement.")

async def warn_user(update: Update, context: CallbackContext):
    if not await is_admin(update):
        await update.message.reply_text("Seuls les admins peuvent avertir un utilisateur.")
        return
    await update.message.reply_text("Fonction en cours de développement.")

async def warn_list(update: Update, context: CallbackContext):
    await update.message.reply_text("Fonction en cours de développement.")

async def reset_leaderboard(update: Update, context: CallbackContext):
    if not await is_admin(update):
        await update.message.reply_text("Seuls les admins peuvent réinitialiser le classement.")
        return
    global GROUP_DATA
    for group in GROUP_DATA.keys():
        GROUP_DATA[group]["score"] = 0
    save_group_data()
    await update.message.reply_text("Le classement a été réinitialisé !")

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Le bot Telegram est en ligne ! 🚀"

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
async def webhook():
    data = request.get_json()
    if not data:
        return "Bad Request", 400
    update = Update.de_json(data, application.bot)
    await application.initialize()
    await application.process_update(update)
    return "OK", 200

def main():
    load_group_data()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))
    application.add_handler(CommandHandler("warn", warn_user))
    application.add_handler(CommandHandler("warnlist", warn_list))
    application.add_handler(CommandHandler("resetleaderboard", reset_leaderboard))
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    main()
