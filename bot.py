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

# Vérifier si l'utilisateur est un admin du groupe
async def is_admin(update: Update):
    chat_member = await update.message.chat.get_member(update.message.from_user.id)
    return chat_member.status in ['administrator', 'creator']

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

# Commande /ban
async def ban_user(update: Update, context: CallbackContext):
    """Bannir un utilisateur du groupe."""
    if not await is_admin(update):
        await update.message.reply_text("Vous devez être un administrateur pour bannir un utilisateur.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /ban @username")
        return

    user_mention = context.args[0]  # Récupérer l'argument (le nom d'utilisateur)
    
    # Extraire l'ID de l'utilisateur à partir de son mention @username
    user_id = await get_user_id_from_mention(update, user_mention)
    if not user_id:
        await update.message.reply_text(f"L'utilisateur {user_mention} n'a pas été trouvé.")
        return

    try:
        # Bannir l'utilisateur du groupe
        await update.message.chat.ban_member(user_id)
        # Ajouter l'utilisateur à la liste des bannis dans les données
        chat_id = str(update.message.chat.id)
        if chat_id not in GROUP_DATA:
            GROUP_DATA[chat_id] = {}
        if "banned_users" not in GROUP_DATA[chat_id]:
            GROUP_DATA[chat_id]["banned_users"] = []
        if user_id not in GROUP_DATA[chat_id]["banned_users"]:
            GROUP_DATA[chat_id]["banned_users"].append(user_id)
        save_group_data()

        await update.message.reply_text(f"L'utilisateur {user_mention} a été banni ! 🚫")
    except Exception as e:
        logger.error(f"Erreur lors du bannissement : {e}")
        await update.message.reply_text(f"Impossible de bannir l'utilisateur {user_mention}.")

# Commande /unban
async def unban_user(update: Update, context: CallbackContext):
    """Débannir un utilisateur du groupe."""
    if not await is_admin(update):
        await update.message.reply_text("Vous devez être un administrateur pour débannir un utilisateur.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /unban @username")
        return

    user_mention = context.args[0]
    
    # Extraire l'ID de l'utilisateur à partir de son mention @username
    user_id = await get_user_id_from_mention(update, user_mention)
    if not user_id:
        await update.message.reply_text(f"L'utilisateur {user_mention} n'a pas été trouvé.")
        return

    try:
        # Débannir l'utilisateur du groupe
        await update.message.chat.unban_member(user_id)
        # Retirer l'utilisateur de la liste des bannis
        chat_id = str(update.message.chat.id)
        if chat_id in GROUP_DATA and "banned_users" in GROUP_DATA[chat_id]:
            if user_id in GROUP_DATA[chat_id]["banned_users"]:
                GROUP_DATA[chat_id]["banned_users"].remove(user_id)
                save_group_data()

        await update.message.reply_text(f"L'utilisateur {user_mention} a été débanni ! ✅")
    except Exception as e:
        logger.error(f"Erreur lors du débannissement : {e}")
        await update.message.reply_text(f"Impossible de débannir l'utilisateur {user_mention}.")

# Commande /listban
async def list_banned_users(update: Update, context: CallbackContext):
    """Lister les utilisateurs bannis du groupe."""
    chat_id = str(update.message.chat.id)
    banned_users = GROUP_DATA.get(chat_id, {}).get("banned_users", [])
    
    if not banned_users:
        await update.message.reply_text("Aucun utilisateur banni dans ce groupe.")
    else:
        banned_list = "\n".join([f"@{user}" for user in banned_users])
        await update.message.reply_text(f"Utilisateurs bannis :\n{banned_list}")

# Fonction pour récupérer l'ID d'un utilisateur à partir de son mention
async def get_user_id_from_mention(update: Update, mention: str):
    """Récupère l'ID de l'utilisateur à partir de son mention (format @username)."""
    try:
        username = mention.lstrip('@')
        member = await update.message.chat.get_member(username)
        return member.user.id
    except Exception as e:
        logger.error(f"Erreur lors de la recherche de l'utilisateur {mention}: {e}")
        return None

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
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("listban", list_banned_users))

    # Définir le webhook
    webhook_url = f"https://telegram-bot-control-bot.onrender.com/{TELEGRAM_BOT_TOKEN}"
    application.bot.set_webhook(url=webhook_url)

    # Démarrer Flask
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    main()
