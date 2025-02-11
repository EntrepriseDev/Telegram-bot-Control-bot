import logging
import json
import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Configuration des tokens
TELEGRAM_BOT_TOKEN = "7516380781:AAE_XvPn_7KA6diabmcaZOqBMxBzXAHv0aw"
WEBHOOK_URL = "https://telegram-bot-control-bot-1.onrender.com"  # Ex: https://tondomaine.com/webhook

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionnaire pour stocker les données des groupes
GROUP_DATA = {}

def load_group_data():
    global GROUP_DATA
    try:
        with open('group_data.json', 'r') as f:
            GROUP_DATA = json.load(f)
    except FileNotFoundError:
        GROUP_DATA = {}

def save_group_data():
    try:
        with open('group_data.json', 'w') as f:
            json.dump(GROUP_DATA, f, indent=4)
        logger.info("Données sauvegardées avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des données : {e}")

# Flask pour le webhook
app = Flask(__name__)
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put(update)
    return "OK", 200

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Bienvenue ! Utilisez /help pour voir les commandes disponibles.")

async def show_rules(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.message.chat.id)
    if chat_id in GROUP_DATA and "rules" in GROUP_DATA[chat_id]:
        await update.message.reply_text(f"Règles du groupe :\n{GROUP_DATA[chat_id]['rules']}")
    else:
        await update.message.reply_text("Aucune règle définie.")

async def add_rules(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.message.chat.id)
    user_id = update.message.from_user.id
    admins = await update.message.chat.get_administrators()
    if any(admin.user.id == user_id for admin in admins):
        rule_text = ' '.join(context.args)
        if chat_id not in GROUP_DATA:
            GROUP_DATA[chat_id] = {"rules": ""}
        GROUP_DATA[chat_id]["rules"] += f"\n{rule_text}"
        save_group_data()
        await update.message.reply_text(f"Règle ajoutée : {rule_text}")
    else:
        await update.message.reply_text("Seuls les admins peuvent ajouter des règles.")

async def modify_rules(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.message.chat.id)
    user_id = update.message.from_user.id
    admins = await update.message.chat.get_administrators()
    if any(admin.user.id == user_id for admin in admins):
        rules_text = ' '.join(context.args)
        if rules_text:
            GROUP_DATA[chat_id]["rules"] = rules_text
            save_group_data()
            await update.message.reply_text(f"Règles mises à jour :\n{rules_text}")
        else:
            await update.message.reply_text("Fournissez le texte des nouvelles règles.")
    else:
        await update.message.reply_text("Seuls les admins peuvent modifier les règles.")

async def remove_rule(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.message.chat.id)
    if chat_id in GROUP_DATA and "rules" in GROUP_DATA[chat_id]:
        rule_to_remove = ' '.join(context.args)
        rules = GROUP_DATA[chat_id]["rules"].split("\n")
        if rule_to_remove in rules:
            rules.remove(rule_to_remove)
            GROUP_DATA[chat_id]["rules"] = "\n".join(rules)
            save_group_data()
            await update.message.reply_text(f"Règle supprimée : {rule_to_remove}")
        else:
            await update.message.reply_text("Cette règle n'existe pas.")
    else:
        await update.message.reply_text("Aucune règle définie pour ce groupe.")

async def add_user(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.message.chat.id)
    if chat_id not in GROUP_DATA:
        GROUP_DATA[chat_id] = {"users": []}
    user = update.message.reply_to_message.from_user
    if user.id not in GROUP_DATA[chat_id]["users"]:
        GROUP_DATA[chat_id]["users"].append(user.id)
        save_group_data()
        await update.message.reply_text(f"{user.full_name} ajouté à la liste.")
    else:
        await update.message.reply_text(f"{user.full_name} est déjà dans la liste.")

async def remove_user(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.message.chat.id)
    if chat_id in GROUP_DATA and "users" in GROUP_DATA[chat_id]:
        user = update.message.reply_to_message.from_user
        if user.id in GROUP_DATA[chat_id]["users"]:
            GROUP_DATA[chat_id]["users"].remove(user.id)
            save_group_data()
            await update.message.reply_text(f"{user.full_name} retiré de la liste.")
        else:
            await update.message.reply_text(f"{user.full_name} n'est pas dans la liste.")
    else:
        await update.message.reply_text("Aucun utilisateur défini pour ce groupe.")

def main():
    load_group_data()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("rules", show_rules))
    telegram_app.add_handler(CommandHandler("setrules", add_rules))
    telegram_app.add_handler(CommandHandler("modifyrules", modify_rules))
    telegram_app.add_handler(CommandHandler("removerule", remove_rule))
    telegram_app.add_handler(CommandHandler("adduser", add_user))
    telegram_app.add_handler(CommandHandler("removeuser", remove_user))

    telegram_app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()
    app.run(host='0.0.0.0', port=5000)
