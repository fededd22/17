import subprocess
import sys
import re

# دالة لتثبيت المكتبات إذا لم تكن مثبتة تلقائيًا
def install_missing_packages():
    with open(__file__, "r", encoding="utf-8") as f:
        code = f.read()

    # البحث عن جميع المكتبات المستوردة
    imported_packages = set(re.findall(r"^\s*import\s+([a-zA-Z0-9_]+)|^\s*from\s+([a-zA-Z0-9_]+)\s+import", code, re.MULTILINE))
    
    # تحويل النتائج إلى قائمة أسماء مكتبات
    packages = {pkg for group in imported_packages for pkg in group if pkg}
    
    for package in packages:
        try:
            __import__(package)  # محاولة استيراد المكتبة
        except ImportError:
            print(f"⚙️ تثبيت المكتبة {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# تثبيت المكتبات غير الموجودة
install_missing_packages()


import subprocess
import os
import asyncio
import importlib
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from keep_alive import keep_alive

keep_alive()
# 🔑 Configuration du bot
TOKEN = "8013473015:AAGQBnXIK4zDyHhm5evChCA8F9jH9faIhkA"
BASE_DIR = "scripts"
processes = {}
user_states = {}
banned_users = set()
ADMINS = [1726923679]  # IDs des administrateurs
BOT_MODE = "public"  # Peut être "public" ou "private"

# 📂 Créer le dossier des scripts s'il n'existe pas
os.makedirs(BASE_DIR, exist_ok=True)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 🎛️ Clavier principal pour les utilisateurs normaux
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Ajouter un fichier")],
        [KeyboardButton(text="▶️ Exécuter un script")],
        [KeyboardButton(text="📜 Liste des fichiers")],
        [KeyboardButton(text="❌ Supprimer un fichier")],
    ],
    resize_keyboard=True
)

# 🎛️ Clavier principal pour les admins
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Ajouter un fichier")],
        [KeyboardButton(text="▶️ Exécuter un script")],
        [KeyboardButton(text="📜 Liste des fichiers")],
        [KeyboardButton(text="❌ Supprimer un fichier")],
        [KeyboardButton(text="👑 Panel admin")],
    ],
    resize_keyboard=True
)

# 🎛️ Panel admin
admin_panel_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔒 Bannir un utilisateur"), KeyboardButton(text="🔓 Débannir un utilisateur")],
        [KeyboardButton(text="💾 Sauvegarder fichiers utilisateur")],
        [KeyboardButton(text="📋 Liste de tous les fichiers")],
        [KeyboardButton(text="🛑 Supprimer fichier utilisateur")],
        [KeyboardButton(text="🔐 Mode privé"), KeyboardButton(text="🌍 Mode public")],
        [KeyboardButton(text="💻 Envoyer commande terminal")],
        [KeyboardButton(text="⬅️ Retour au menu principal")],
    ],
    resize_keyboard=True
)

# 🎛️ Clavier pour la saisie manuelle des commandes
command_input_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="saisir la commande manuellement")],
        [KeyboardButton(text="⬅️ Annuler")],
    ],
    resize_keyboard=True
)

# 🏁 Commande /start
@dp.message(Command("start"))
async def start(message: types.Message):
    if BOT_MODE == "private" and message.from_user.id not in ADMINS:
        await message.reply("🚫 Le bot est en mode privé, seuls les admins peuvent l'utiliser.")
        return
    
    if message.from_user.id in banned_users:
        await message.reply("🚫 Vous êtes banni de ce bot.")
        return
    
    keyboard = admin_keyboard if message.from_user.id in ADMINS else main_keyboard
    await message.reply("👋 Bonjour ! Choisissez une action :", reply_markup=keyboard)

# 👑 Panel admin
@dp.message(lambda message: message.text == "👑 Panel admin" and message.from_user.id in ADMINS)
async def admin_panel(message: types.Message):
    await message.reply("👑 Panel d'administration", reply_markup=admin_panel_keyboard)

# 💻 Envoyer commande terminal (admin seulement)
@dp.message(lambda message: message.text == "💻 Envoyer commande terminal" and message.from_user.id in ADMINS)
async def send_terminal_command(message: types.Message):
    user_states[message.from_user.id] = "terminal_command"
    await message.reply("📝 Entrez la commande à exécuter dans le terminal:", reply_markup=command_input_keyboard)

# Gestion des commandes terminal
@dp.message(lambda message: user_states.get(message.from_user.id) == "terminal_command" and message.from_user.id in ADMINS)
async def handle_terminal_command(message: types.Message):
    if message.text == "⬅️ Annuler":
        user_states.pop(message.from_user.id, None)
        await message.reply("👑 Panel d'administration", reply_markup=admin_panel_keyboard)
        return
    
    if message.text == "saisir la commande manuellement":
        user_states[message.from_user.id] = "manual_command_input"
        await message.reply("📝 Entrez maintenant la commande à exécuter:")
        return
    
    command = message.text
    await message.reply(f"⚙️ Exécution de la commande: `{command}`", parse_mode="Markdown")
    
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if stdout:
            output = stdout.decode()
            if len(output) > 4000:
                output = output[:4000] + "\n... (sortie tronquée)"
            await message.reply(f"📤 Sortie:\n```\n{output}\n```", parse_mode="Markdown")
        
        if stderr:
            error = stderr.decode()
            if len(error) > 4000:
                error = error[:4000] + "\n... (erreur tronquée)"
            await message.reply(f"⚠️ Erreur:\n```\n{error}\n```", parse_mode="Markdown")
        
        if process.returncode == 0:
            await message.reply("✅ Commande exécutée avec succès!")
        else:
            await message.reply(f"❌ Commande terminée avec le code de sortie: {process.returncode}")
    
    except Exception as e:
        await message.reply(f"⚠️ Erreur lors de l'exécution de la commande: {str(e)}")
    
    user_states.pop(message.from_user.id, None)
    await message.reply("👑 Panel d'administration", reply_markup=admin_panel_keyboard)

# 🔐 Passer en mode privé (admin seulement)
@dp.message(lambda message: message.text == "🔐 Mode privé" and message.from_user.id in ADMINS)
async def set_private_mode(message: types.Message):
    global BOT_MODE
    BOT_MODE = "private"
    await message.reply("✅ Le bot est maintenant en mode privé (admins seulement)")
    await message.reply("👑 Panel d'administration", reply_markup=admin_panel_keyboard)

# 🌍 Passer en mode public (tout le monde)
@dp.message(lambda message: message.text == "🌍 Mode public" and message.from_user.id in ADMINS)
async def set_public_mode(message: types.Message):
    global BOT_MODE
    BOT_MODE = "public"
    await message.reply("✅ Le bot est maintenant en mode public (tout le monde)")
    await message.reply("👑 Panel d'administration", reply_markup=admin_panel_keyboard)

# 📋 Liste de tous les fichiers
@dp.message(lambda message: message.text == "📋 Liste de tous les fichiers" and message.from_user.id in ADMINS)
async def list_all_files(message: types.Message):
    MAX_MESSAGE_LENGTH = 4000
    
    text = "📜 Liste des fichiers de tous les utilisateurs:\n"
    messages = [text]
    current_length = len(text)
    
    for user_id in os.listdir(BASE_DIR):
        user_folder = os.path.join(BASE_DIR, str(user_id))
        if os.path.isdir(user_folder):
            files = os.listdir(user_folder)
            user_text = f"\n👤 {user_id}:\n"
            
            for file in files:
                status = "🟢 Actif" if (int(user_id), file) in processes and processes[(int(user_id), file)].returncode is None else "🔴 Inactif"
                file_line = f" - {file}: {status}\n"
                
                if current_length + len(user_text) + len(file_line) > MAX_MESSAGE_LENGTH:
                    messages.append("📜 Liste des fichiers (suite):\n")
                    current_length = len(messages[-1])
                
                messages[-1] += user_text + file_line
                current_length += len(user_text) + len(file_line)
                user_text = ""
    
    for msg in messages:
        await message.reply(msg)
    
    await message.reply("👑 Panel d'administration", reply_markup=admin_panel_keyboard)

# 🔒 Bannir un utilisateur
@dp.message(lambda message: message.text == "🔒 Bannir un utilisateur" and message.from_user.id in ADMINS)
async def ban_user_prompt(message: types.Message):
    user_states[message.from_user.id] = "ban_user"
    await message.reply("📝 Envoyez l'ID de l'utilisateur à bannir:")

# 🔓 Débannir un utilisateur
@dp.message(lambda message: message.text == "🔓 Débannir un utilisateur" and message.from_user.id in ADMINS)
async def unban_user_prompt(message: types.Message):
    user_states[message.from_user.id] = "unban_user"
    await message.reply("📝 Envoyez l'ID de l'utilisateur à débannir:")

# 💾 Sauvegarder fichiers utilisateur
@dp.message(lambda message: message.text == "💾 Sauvegarder fichiers utilisateur" and message.from_user.id in ADMINS)
async def save_user_prompt(message: types.Message):
    user_states[message.from_user.id] = "save_user"
    await message.reply("📝 Envoyez l'ID de l'utilisateur dont vous voulez sauvegarder les fichiers:")

# 🛑 Supprimer fichier utilisateur
@dp.message(lambda message: message.text == "🛑 Supprimer fichier utilisateur" and message.from_user.id in ADMINS)
async def admin_stop_file_prompt(message: types.Message):
    user_states[message.from_user.id] = "admin_stop_file_user"
    await message.reply("📝 Envoyez l'ID de l'utilisateur dont vous voulez supprimer les fichiers:")

# ➕ Ajouter un fichier
@dp.message(lambda message: message.text == "➕ Ajouter un fichier")
async def prompt_add_file(message: types.Message):
    if BOT_MODE == "private" and message.from_user.id not in ADMINS:
        await message.reply("🚫 Le bot est en mode privé, seuls les admins peuvent l'utiliser.")
        return
    
    if message.from_user.id in banned_users:
        await message.reply("🚫 Vous êtes banni de ce bot.")
        return
    
    user_states[message.from_user.id] = "ajout_fichier"
    await message.reply("📤 Envoyez-moi un fichier .py, .txt, .session ou .bot.session à ajouter.")

@dp.message(lambda message: message.document and user_states.get(message.from_user.id) == "ajout_fichier")
async def handle_file_upload(message: types.Message):
    user_id = message.from_user.id

    if user_id in banned_users:
        await message.reply("🚫 Vous êtes banni de ce bot.")
        return

    document = message.document
    allowed_extensions = ('.py', '.txt', '.session', '.bot.session')
    if not document.file_name.lower().endswith(allowed_extensions):
        await message.reply("⚠️ Seuls les fichiers .py, .txt, .session et .bot.session sont acceptés.")
        return

    user_folder = os.path.join(BASE_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)

    if user_id not in ADMINS:
        existing_files = os.listdir(user_folder)
        if len(existing_files) >= 4:
            await message.reply("⚠️ Vous ne pouvez pas avoir plus de 4 fichiers. Supprimez-en un d'abord.")
            return

    file_path = os.path.join(user_folder, document.file_name)
    file = await bot.get_file(document.file_id)
    await bot.download_file(file.file_path, file_path)

    await message.reply(f"✅ Le fichier **{document.file_name}** a été ajouté avec succès!")
    user_states.pop(user_id, None)

# Fonction pour vérifier et installer les bibliothèques
def check_and_install_libraries(file_path):
    if not file_path.endswith('.py'):
        return []
        
    with open(file_path, 'r') as file:
        script_content = file.read()

    imports = [line for line in script_content.splitlines() if line.startswith("import") or line.startswith("from")]
    missing_libraries = []

    for imp in imports:
        try:
            if imp.startswith("import"):
                module = imp.split()[1]
                importlib.import_module(module)
            elif imp.startswith("from"):
                module = imp.split()[1]
                importlib.import_module(module)
        except ImportError:
            module = imp.split()[1]
            missing_libraries.append(module)

    if missing_libraries:
        for lib in missing_libraries:
            subprocess.run(["pip", "install", lib])

    return missing_libraries

# ❌ Supprimer un fichier
@dp.message(lambda message: message.text == "❌ Supprimer un fichier")
async def stop_and_delete_file(message: types.Message):
    if BOT_MODE == "private" and message.from_user.id not in ADMINS:
        await message.reply("🚫 Le bot est en mode privé, seuls les admins peuvent l'utiliser.")
        return
    
    user_id = message.from_user.id
    user_states[user_id] = "suppression"

    user_folder = os.path.join(BASE_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)

    files = os.listdir(user_folder)
    if not files:
        await message.reply("🚫 Aucun fichier trouvé à supprimer.")
        return

    buttons = [KeyboardButton(text=file) for file in files]
    keyboard_layout = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    keyboard_layout.append([KeyboardButton(text="⬅️ Retour au menu principal")])

    keyboard = ReplyKeyboardMarkup(keyboard=keyboard_layout, resize_keyboard=True)
    await message.reply("🔍 Choisissez un fichier à supprimer:", reply_markup=keyboard)

# 📜 Liste des fichiers
@dp.message(lambda message: message.text == "📜 Liste des fichiers")
async def list_files(message: types.Message):
    if BOT_MODE == "private" and message.from_user.id not in ADMINS:
        await message.reply("🚫 Le bot est en mode privé, seuls les admins peuvent l'utiliser.")
        return
    
    user_id = message.from_user.id
    user_folder = os.path.join(BASE_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)

    files = os.listdir(user_folder)
    if not files:
        await message.reply("🚫 Aucun fichier trouvé.")
        return

    status = {file: "🟢 Actif" if (user_id, file) in processes and processes[(user_id, file)].returncode is None else "🔴 Inactif" for file in files}
    response = "\n".join([f"{file}: {state}" for file, state in status.items()])
    await message.reply(f"📂 Vos fichiers:\n{response}")

# ▶️ Exécuter un script
@dp.message(lambda message: message.text == "▶️ Exécuter un script")
async def list_files_for_running(message: types.Message):
    if BOT_MODE == "private" and message.from_user.id not in ADMINS:
        await message.reply("🚫 Le bot est en mode privé, seuls les admins peuvent l'utiliser.")
        return
    
    user_id = message.from_user.id
    user_states[user_id] = "execution"

    user_folder = os.path.join(BASE_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)

    # Ne lister que les fichiers Python
    files = [f for f in os.listdir(user_folder) if f.lower().endswith('.py')]
    if not files:
        await message.reply("🚫 Aucun script Python trouvé.")
        return

    buttons = [KeyboardButton(text=file) for file in files]
    keyboard_layout = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    keyboard_layout.append([KeyboardButton(text="⬅️ Retour au menu principal")])

    keyboard = ReplyKeyboardMarkup(keyboard=keyboard_layout, resize_keyboard=True)
    await message.reply("🔍 Choisissez un script à exécuter:", reply_markup=keyboard)

# Bouton Retour au menu principal
@dp.message(lambda message: message.text == "⬅️ Retour au menu principal")
async def return_to_main_menu(message: types.Message):
    user_id = message.from_user.id
    user_states.pop(user_id, None)
    keyboard = admin_keyboard if user_id in ADMINS else main_keyboard
    await message.reply("🏠 Retour au menu principal.", reply_markup=keyboard)

# Gestion des actions utilisateur
@dp.message()
async def handle_user_action(message: types.Message):
    if BOT_MODE == "private" and message.from_user.id not in ADMINS:
        await message.reply("🚫 Le bot est en mode privé, seuls les admins peuvent l'utiliser.")
        return
    
    if message.from_user.id in banned_users:
        await message.reply("🚫 Vous êtes banni de ce bot.")
        return

    # Commandes admin
    if message.from_user.id in ADMINS:
        if user_states.get(message.from_user.id) == "ban_user":
            try:
                banned_user_id = int(message.text)
                banned_users.add(banned_user_id)
                await message.reply(f"✅ L'utilisateur {banned_user_id} a été banni avec succès.")
            except ValueError:
                await message.reply("⚠️ Veuillez entrer un ID utilisateur valide (chiffres seulement)")
            user_states.pop(message.from_user.id, None)
            await message.reply("👑 Panel d'administration", reply_markup=admin_panel_keyboard)
            return

        elif user_states.get(message.from_user.id) == "unban_user":
            try:
                unbanned_user_id = int(message.text)
                banned_users.discard(unbanned_user_id)
                await message.reply(f"✅ L'utilisateur {unbanned_user_id} a été débanni avec succès.")
            except ValueError:
                await message.reply("⚠️ Veuillez entrer un ID utilisateur valide (chiffres seulement)")
            user_states.pop(message.from_user.id, None)
            await message.reply("👑 Panel d'administration", reply_markup=admin_panel_keyboard)
            return

        elif user_states.get(message.from_user.id) == "save_user":
            try:
                target_user_id = int(message.text)
                user_folder = os.path.join(BASE_DIR, str(target_user_id))
                
                if not os.path.exists(user_folder):
                    await message.reply("🚫 Aucun fichier trouvé pour cet utilisateur.")
                    user_states.pop(message.from_user.id, None)
                    return
                
                files = os.listdir(user_folder)
                if not files:
                    await message.reply("🚫 Cet utilisateur n'a aucun fichier.")
                    user_states.pop(message.from_user.id, None)
                    return
                
                for file in files:
                    try:
                        await message.answer_document(
                            types.FSInputFile(os.path.join(user_folder, file)),
                            caption=f"Fichier {file} de l'utilisateur {target_user_id}"
                        )
                        await asyncio.sleep(1)
                    except Exception as e:
                        await message.reply(f"⚠️ Erreur lors de l'envoi du fichier {file}: {str(e)}")
                
                await message.reply("✅ Tous les fichiers ont été envoyés avec succès.")
            except ValueError:
                await message.reply("⚠️ Veuillez entrer un ID utilisateur valide (chiffres seulement)")
            except Exception as e:
                await message.reply(f"⚠️ Une erreur inattendue est survenue: {str(e)}")
            
            user_states.pop(message.from_user.id, None)
            await message.reply("👑 Panel d'administration", reply_markup=admin_panel_keyboard)
            return

        elif user_states.get(message.from_user.id) == "admin_stop_file_user":
            try:
                target_user_id = int(message.text)
                user_folder = os.path.join(BASE_DIR, str(target_user_id))
                if not os.path.exists(user_folder):
                    await message.reply("🚫 Aucun fichier trouvé pour cet utilisateur.")
                    user_states.pop(message.from_user.id, None)
                    return
                
                files = os.listdir(user_folder)
                if not files:
                    await message.reply("🚫 Aucun fichier trouvé pour cet utilisateur.")
                    user_states.pop(message.from_user.id, None)
                    return
                
                user_states[message.from_user.id] = ("admin_stop_file_select", target_user_id)
                
                buttons = [KeyboardButton(text=file) for file in files]
                keyboard_layout = [buttons[i:i+2] for i in range(0, len(files), 2)]
                keyboard_layout.append([KeyboardButton(text="⬅️ Retour au menu principal")])

                keyboard = ReplyKeyboardMarkup(keyboard=keyboard_layout, resize_keyboard=True)
                await message.reply(f"🔍 Choisissez un fichier de l'utilisateur {target_user_id} à supprimer:", reply_markup=keyboard)
                return
                
            except ValueError:
                await message.reply("⚠️ Veuillez entrer un ID utilisateur valide (chiffres seulement)")
                user_states.pop(message.from_user.id, None)
                await message.reply("👑 Panel d'administration", reply_markup=admin_panel_keyboard)
                return

        elif isinstance(user_states.get(message.from_user.id), tuple) and user_states[message.from_user.id][0] == "admin_stop_file_select":
            target_user_id = user_states[message.from_user.id][1]
            filename = message.text
            
            if filename == "⬅️ Retour au menu principal":
                user_states.pop(message.from_user.id, None)
                keyboard = admin_keyboard if message.from_user.id in ADMINS else main_keyboard
                await message.reply("🏠 Retour au menu principal.", reply_markup=keyboard)
                return
            
            file_path = os.path.join(BASE_DIR, str(target_user_id), filename)
            
            # Arrêter le processus si c'est un script Python en cours d'exécution
            process_stopped = False
            if filename.endswith('.py') and (target_user_id, filename) in processes:
                process = processes[(target_user_id, filename)]
                if process.returncode is None:
                    try:
                        process.terminate()
                        try:
                            await asyncio.wait_for(process.wait(), timeout=3)
                            process_stopped = True
                        except asyncio.TimeoutError:
                            process.kill()
                            process_stopped = True
                        await message.reply(f"⛔ Le script {filename} a été arrêté avec succès.")
                    except Exception as e:
                        await message.reply(f"⚠️ Erreur lors de l'arrêt du script: {str(e)}")
                    finally:
                        if (target_user_id, filename) in processes:
                            del processes[(target_user_id, filename)]
            
            # Supprimer le fichier
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    await message.reply(f"✅ Le fichier {filename} de l'utilisateur {target_user_id} a été supprimé avec succès.")
                else:
                    if not process_stopped:
                        await message.reply(f"⚠️ Le fichier {filename} n'existe pas pour l'utilisateur {target_user_id}.")
            except Exception as e:
                await message.reply(f"⚠️ Erreur lors de la suppression du fichier: {str(e)}")

            user_states.pop(message.from_user.id, None)
            await message.reply("👑 Panel d'administration", reply_markup=admin_panel_keyboard)
            return

    # Commandes normales
    user_folder = os.path.join(BASE_DIR, str(message.from_user.id))
    os.makedirs(user_folder, exist_ok=True)

    user_files = os.listdir(user_folder)
    filename = message.text
    file_path = os.path.join(user_folder, filename)

    if filename not in user_files:
        return

    if user_states.get(message.from_user.id) == "execution" and filename.endswith('.py'):
        missing_libraries = check_and_install_libraries(file_path)

        if missing_libraries:
            await message.reply(f"⚠️ Bibliothèques manquantes installées:\n" + "\n".join(missing_libraries))
        else:
            await message.reply(f"✅ Toutes les bibliothèques sont déjà installées.")

        await message.reply(f"🚀 Exécution du script {filename}...")
        process = await asyncio.create_subprocess_exec(
            'python', file_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        processes[(message.from_user.id, filename)] = process

        stdout, stderr = await process.communicate()

        if stdout:
            await message.reply(f"📤 Sortie:\n```\n{stdout.decode()}\n```", parse_mode="Markdown")
        if stderr:
            await message.reply(f"⚠️ Erreurs:\n```\n{stderr.decode()}\n```", parse_mode="Markdown")

        user_states.pop(message.from_user.id, None)

    elif user_states.get(message.from_user.id) == "suppression":
        if filename.endswith('.py') and (message.from_user.id, filename) in processes:
            process = processes[(message.from_user.id, filename)]
            if process.returncode is None:
                process.terminate()
                try:
                    await process.wait(timeout=5)
                except asyncio.TimeoutError:
                    process.kill()
            del processes[(message.from_user.id, filename)]

        if os.path.exists(file_path):
            os.remove(file_path)
            await message.reply(f"✅ Le fichier {filename} a été supprimé avec succès.")
        else:
            await message.reply(f"⚠️ Le fichier {filename} n'existe pas.")

        user_states.pop(message.from_user.id, None)

# 🚀 Lancer le bot
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())