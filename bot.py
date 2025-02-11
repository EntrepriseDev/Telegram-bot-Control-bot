import logging
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Configuration des tokens
TELEGRAM_BOT_TOKEN = "7516380781:AAE_XvPn_7KA6diabmcaZOqBMxBzXAHv0aw"

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionnaire pour stocker les données des groupes
GROUP_DATA = {}

# Charger les données de groupes depuis un fichier JSON (persistant)
def load_group_data():
    global GROUP_DATA
    try:
        with open('group_data.json', 'r') as f:
            GROUP_DATA = json.load(f)
    except FileNotFoundError:
        GROUP_DATA = {}  # Si le fichier n'existe pas, on crée un dictionnaire vide

# Sauvegarder les données des groupes dans un fichier JSON
def save_group_data():
    try:
        with open('group_data.json', 'w') as f:
            json.dump(GROUP_DATA, f, indent=4)  # Utilisation de indent=4 pour une meilleure lisibilité du JSON
        logger.info("Données sauvegardées avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des données : {e}")

# Fonction de démarrage du bot
async def start(update: Update, context: CallbackContext) -> None:
    """Répond au /start"""
    await update.message.reply_text("Bienvenue ! Utilisez /help pour voir les commandes disponibles.")

# Afficher les règles d'un groupe
async def show_rules(update: Update, context: CallbackContext) -> None:
    """Montre les règles d'un groupe"""
    chat_id = update.message.chat.id
    if chat_id in GROUP_DATA and "rules" in GROUP_DATA[chat_id]:
        rules = GROUP_DATA[chat_id]["rules"]
        await update.message.reply_text(f"Règles de ce groupe :\n{rules}")
    else:
        await update.message.reply_text("Ce groupe n'a pas encore de règles définies.")

# Ajouter une ou plusieurs règles d'un groupe
async def add_rules(update: Update, context: CallbackContext) -> None:
    """Ajoute une règle au groupe, seulement si l'utilisateur est l'administrateur"""
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id

    # Récupère les administrateurs du groupe
    admins = await update.message.chat.get_administrators()

    # Vérifie si l'utilisateur est administrateur
    is_admin = any(admin.user.id == user_id for admin in admins)

    if is_admin:
        rule_text = ' '.join(context.args)
        if chat_id not in GROUP_DATA:
            GROUP_DATA[chat_id] = {"rules": ""}
        if rule_text:
            GROUP_DATA[chat_id]["rules"] += f"\n{rule_text}"  # Ajoute la nouvelle règle
            save_group_data()  # Sauvegarder après ajout
            await update.message.reply_text(f"Règle ajoutée : {rule_text}")
        else:
            await update.message.reply_text("Veuillez fournir le texte de la règle après la commande.")
    else:
        await update.message.reply_text("Tu n'es pas un administrateur pour ajouter des règles.")

# Modifier les règles d'un groupe
async def modify_rules(update: Update, context: CallbackContext) -> None:
    """Modifie les règles d'un groupe"""
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id

    # Récupère les administrateurs du groupe
    admins = await update.message.chat.get_administrators()

    # Vérifie si l'utilisateur est administrateur
    is_admin = any(admin.user.id == user_id for admin in admins)

    if is_admin:
        rules_text = ' '.join(context.args)
        if rules_text:
            GROUP_DATA[chat_id]["rules"] = rules_text  # Remplace les règles existantes
            save_group_data()  # Sauvegarder après modification
            await update.message.reply_text(f"Les règles ont été modifiées :\n{rules_text}")
        else:
            await update.message.reply_text("Veuillez fournir les nouvelles règles après la commande.")
    else:
        await update.message.reply_text("Seul l'admin peut modifier les règles.")

# Supprimer une règle spécifique
async def remove_rule(update: Update, context: CallbackContext) -> None:
    """Supprime une règle spécifique d'un groupe"""
    chat_id = update.message.chat.id
    if chat_id in GROUP_DATA and "rules" in GROUP_DATA[chat_id]:
        rule_to_remove = ' '.join(context.args)
        rules = GROUP_DATA[chat_id]["rules"].split("\n")
        
        if rule_to_remove in rules:
            rules.remove(rule_to_remove)
            GROUP_DATA[chat_id]["rules"] = "\n".join(rules)
            save_group_data()  # Sauvegarder après suppression
            await update.message.reply_text(f"La règle '{rule_to_remove}' a été supprimée.")
        else:
            await update.message.reply_text(f"La règle '{rule_to_remove}' n'existe pas dans les règles du groupe.")
    else:
        await update.message.reply_text("Ce groupe n'a pas encore de règles définies.")

# Ajouter un utilisateur à la liste des utilisateurs du groupe
async def add_user(update: Update, context: CallbackContext) -> None:
    """Ajoute un utilisateur à la liste des utilisateurs d'un groupe"""
    chat_id = update.message.chat.id
    if chat_id not in GROUP_DATA:
        GROUP_DATA[chat_id] = {"users": [], "banned": []}
    
    user = update.message.reply_to_message.from_user
    if user.id not in GROUP_DATA[chat_id]["users"]:
        GROUP_DATA[chat_id]["users"].append(user.id)
        save_group_data()  # Sauvegarder après ajout
        await update.message.reply_text(f"{user.full_name} a été ajouté à la liste des utilisateurs.")
    else:
        await update.message.reply_text(f"{user.full_name} est déjà dans la liste des utilisateurs.")

# Supprimer un utilisateur de la liste des utilisateurs du groupe
async def remove_user(update: Update, context: CallbackContext) -> None:
    """Supprime un utilisateur de la liste des utilisateurs d'un groupe"""
    chat_id = update.message.chat.id
    if chat_id in GROUP_DATA and "users" in GROUP_DATA[chat_id]:
        user = update.message.reply_to_message.from_user
        if user.id in GROUP_DATA[chat_id]["users"]:
            GROUP_DATA[chat_id]["users"].remove(user.id)
            save_group_data()  # Sauvegarder après suppression
            await update.message.reply_text(f"{user.full_name} a été supprimé de la liste des utilisateurs.")
        else:
            await update.message.reply_text(f"{user.full_name} n'est pas dans la liste des utilisateurs.")
    else:
        await update.message.reply_text("Ce groupe n'a pas encore d'utilisateurs définis.")

# Bannir un utilisateur
async def ban_user(update: Update, context: CallbackContext) -> None:
    """Bannit un utilisateur du groupe"""
    chat_id = update.message.chat.id
    if chat_id not in GROUP_DATA:
        GROUP_DATA[chat_id] = {"users": [], "banned": []}

    user = update.message.reply_to_message.from_user
    if user.id not in GROUP_DATA[chat_id]["banned"]:
        GROUP_DATA[chat_id]["banned"].append(user.id)
        save_group_data()  # Sauvegarder après ajout au groupe des bannis
        await update.message.reply_text(f"{user.full_name} a été banni du groupe.")
    else:
        await update.message.reply_text(f"{user.full_name} est déjà banni.")

# Lister les membres bannis
async def list_banned(update: Update, context: CallbackContext) -> None:
    """Affiche les membres bannis du groupe"""
    chat_id = update.message.chat.id
    if chat_id in GROUP_DATA and "banned" in GROUP_DATA[chat_id]:
        banned_users = GROUP_DATA[chat_id]["banned"]
        if banned_users:
            banned_names = [str(user) for user in banned_users]
            await update.message.reply_text(f"Membres bannis :\n" + "\n".join(banned_names))
        else:
            await update.message.reply_text("Il n'y a actuellement aucun membre banni.")
    else:
        await update.message.reply_text("Ce groupe n'a pas de membres bannis.")

# Fonction d'aide
async def help_command(update: Update, context: CallbackContext) -> None:
    """Affiche les commandes disponibles"""
    help_text = (
        "/start - Démarre le bot\n"
        "/rules - Affiche les règles du groupe\n"
        "/setrules [règle] - Ajoute une règle au groupe\n"
        "/modifyrules [nouvelles règles] - Modifie les règles du groupe\n"
        "/removerule [règle] - Supprime une règle du groupe\n"
        "/adduser - Ajoute un utilisateur au groupe\n"
        "/removeuser - Supprime un utilisateur du groupe\n"
        "/banuser - Bannit un utilisateur du groupe\n"
        "/bannedusers - Liste les membres bannis du groupe"
    )
    await update.message.reply_text(help_text)

# Fonction principale pour démarrer le bot
def main() -> None:
    """Démarre le bot"""
    load_group_data()

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Commandes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("rules", show_rules))
    application.add_handler(CommandHandler("setrules", add_rules))
    application.add_handler(CommandHandler("modifyrules", modify_rules))
    application.add_handler(CommandHandler("removerule", remove_rule))
    application.add_handler(CommandHandler("adduser", add_user))
    application.add_handler(CommandHandler("removeuser", remove_user))
    application.add_handler(CommandHandler("banuser", ban_user))
    application.add_handler(CommandHandler("bannedusers", list_banned))
    application.add_handler(CommandHandler("help", help_command))

    # Lancer le bot
    application.run_polling()

if __name__ == "__main__":
    main()
