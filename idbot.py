import os, time, json, telebot, logging
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

# -------------------- CONFIGURATION --------------------
TOKEN = '8978422983:AAFfb_gDEdZWqk8RSg0J7OZ4l9BzLs6bI1s'
DATA_FILE = "user_data.json"

ENABLE_CHANNEL_CHECK = True
REQUIRED_CHANNEL = "https://t.me/+fkKWsFmum3BhNTE1"
REQUIRED_CHANNEL_ID = -1002387714877
ADMIN_IDS = [8417161342]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- DATA STORAGE --------------------
class UserData:
    def __init__(self):
        self.data = {}
        self.load()
    def load(self):
        try:
            with open(DATA_FILE, 'r') as f: self.data = json.load(f)
        except: self.data = {}
    def save(self):
        with open(DATA_FILE, 'w') as f: json.dump(self.data, f, indent=2)
    def get_user_data(self, user_id):
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {'channels': [], 'groups': [], 'verified': False}
            self.save()
        return self.data[uid]
    def is_verified(self, user_id):
        return self.get_user_data(user_id).get('verified', False)
    def set_verified(self, user_id, status=True):
        self.get_user_data(user_id)['verified'] = status
        self.save()
    # ---------- Channel owner mapping ----------
    def get_channel_owner(self, channel_id):
        return self.data.get('channel_owners', {}).get(str(channel_id))
    def set_channel_owner(self, channel_id, user_id):
        if 'channel_owners' not in self.data:
            self.data['channel_owners'] = {}
        self.data['channel_owners'][str(channel_id)] = user_id
        self.save()
    # ---------- Channel & Group storage ----------
    def add_channel(self, user_id, channel_id, channel_name):
        ud = self.get_user_data(user_id)
        for ch in ud['channels']:
            if ch['id'] == channel_id:
                if ch['name'] != channel_name:
                    ch['name'] = channel_name
                    self.save()
                return True
        ud['channels'].append({'id': channel_id, 'name': channel_name})
        self.save()
        return True
    def get_channels(self, user_id):
        return self.get_user_data(user_id)['channels']
    def remove_channel(self, user_id, channel_id):
        ud = self.get_user_data(user_id)
        ud['channels'] = [ch for ch in ud['channels'] if ch['id'] != channel_id]
        self.save()
        return True
    def add_group(self, user_id, group_id, group_name):
        ud = self.get_user_data(user_id)
        for gr in ud['groups']:
            if gr['id'] == group_id:
                if gr['name'] != group_name:
                    gr['name'] = group_name
                    self.save()
                return True
        ud['groups'].append({'id': group_id, 'name': group_name})
        self.save()
        return True
    def get_groups(self, user_id):
        return self.get_user_data(user_id)['groups']
    def remove_group(self, user_id, group_id):
        ud = self.get_user_data(user_id)
        ud['groups'] = [gr for gr in ud['groups'] if gr['id'] != group_id]
        self.save()
        return True

db = UserData()
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# -------------------- CHANNEL CHECK (only for /start) --------------------
def is_admin(user_id):
    return user_id in ADMIN_IDS

def check_membership(user_id):
    if not ENABLE_CHANNEL_CHECK or is_admin(user_id):
        return True
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL_ID, user_id)
        return member.status not in ['left', 'kicked', 'banned']
    except Exception as e:
        logger.error(f"Membership check error: {e}")
        return False

def send_join_prompt(chat_id):
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("📢 Join Channel", url=REQUIRED_CHANNEL))
    kb.row(InlineKeyboardButton("✅ I have joined", callback_data="check_join"))
    bot.send_message(
        chat_id,
        "⚠️ **You must join our official channel to use this bot!**\n\n"
        "1. Click the button below to join.\n"
        "2. After joining, click 'I have joined'.",
        reply_markup=kb,
        parse_mode='Markdown'
    )

# -------------------- KEYBOARDS & LOADING --------------------
def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🚀GET MY ID", "📢 GET CHANNEL ID")
    kb.row("👥 GET GROUP ID", "🎃USER HELP")
    return kb

def help_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🚀GET MY ID", "📢 GET CHANNEL ID")
    kb.row("👥 GET GROUP ID", "🤖 AI ASSISTANT")
    kb.row("🏠 MAIN MENU")
    return kb

def show_loading(chat_id):
    msg = bot.send_message(chat_id, "🌺 Loading: [▱▱▱▱▱▱▱▱▱▱] 0%")
    steps = [
        ("🌼 [▰▱▱▱▱▱▱▱▱▱] 10%",0.15), ("🌻 [▰▰▱▱▱▱▱▱▱▱] 20%",0.15),
        ("🌸 [▰▰▰▱▱▱▱▱▱▱] 30%",0.15), ("🌹 [▰▰▰▰▱▱▱▱▱▱] 40%",0.15),
        ("🍁 [▰▰▰▰▰▱▱▱▱▱] 50%",0.15), ("🌿 [▰▰▰▰▰▰▱▱▱▱] 60%",0.15),
        ("🌳 [▰▰▰▰▰▰▰▱▱▱] 70%",0.15), ("🌲 [▰▰▰▰▰▰▰▰▱▱] 80%",0.15),
        ("🪷 [▰▰▰▰▰▰▰▰▰▱] 90%",0.15), ("✅ [▰▰▰▰▰▰▰▰▰▰] 100%",0.15)
    ]
    for text, delay in steps:
        time.sleep(delay)
        try: bot.edit_message_text(f"🌺 Loading: {text}", chat_id, msg.message_id)
        except: pass
    return msg

# ===================== CHAT MEMBER HANDLER (fallback owner detection) =====================
@bot.chat_member_handler()
def handle_chat_member(chat_member_update):
    chat = chat_member_update.chat
    from_user = chat_member_update.from_user
    new_chat_member = chat_member_update.new_chat_member
    if chat.type in ['channel', 'group', 'supergroup'] and new_chat_member.status in ['member', 'administrator']:
        if from_user and not from_user.is_bot:
            db.set_channel_owner(chat.id, from_user.id)
            logger.info(f"Bot added to {chat.type} {chat.id} by user {from_user.id}")

# ===================== COMMAND HANDLERS =====================
@bot.message_handler(commands=['start'])
@bot.channel_post_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        bot.send_message(message.chat.id, "👋 Hello! Use commands like /getmyid in a private chat with me.", parse_mode="Markdown")
        return
    if not check_membership(user_id):
        send_join_prompt(message.chat.id)
        return
    db.set_verified(user_id, True)
    name = message.chat.title if message.chat.type=="channel" else message.from_user.first_name
    text = (f"🗽{name} welcome back to ID Bot! 👋\n\n"
            f"🔍 *Chat ID Finder Bot* 🧞\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🚀 /getmyid – get your chat ID\n"
            f"🚀 /Channelid – For channel ID\n"
            f"👥 /groupid – For Group ID\n"
            f"🚀 /help – Manual\n\n"
            f"🛸 add me on your Group/channel & ❤️‍🔥 run commands to get your IDs 🦹 !")
    if message.chat.type == "channel":
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_keyboard())

@bot.message_handler(commands=['help'])
@bot.channel_post_handler(commands=['help'])
def help_command(message):
    name = message.chat.title if message.chat.type=="channel" else message.from_user.first_name
    text = (f"✨ *HELP* ✨\n"
            f"════════════════\n"
            f"👋 Hey {name}!\n\n"
            f"📌 *COMMANDS*\n"
            f"🚀 /getmyid → Your ID\n"
            f"📢 /Channelid → Channel ID\n"
            f"👥 /groupid → Group ID\n"
            f"🤖 /helpAi → AI Assistant\n\n"
            f"━━━━━━━━━━━━━━\n"
            f"🤖 *AI ASSISTANT* 🧠\n"
            f"━━━━━━━━━━━━━━\n"
            f"✅ Only bot-related answers\n"
            f"⛔ No admin requests\n"
            f"⚡ Powered by DeepSeek\n\n"
            f"💡 Add me to group/channel 🚀\n"
            f"🔗 Dev: @OWNERHIMANSHU\n"
            f"🏠 /start for buttons\n"
            f"════════════════\n"
            f"🎉 Happy Hunting! 🎉")
    if message.chat.type == "channel":
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=help_keyboard())

@bot.message_handler(func=lambda m: m.text=="🏠 MAIN MENU")
def main_menu(m): start_command(m)
@bot.message_handler(func=lambda m: m.text=="🎃USER HELP")
def user_help(m): help_command(m)

@bot.message_handler(commands=['getmyid'])
@bot.channel_post_handler(commands=['getmyid'])
@bot.message_handler(func=lambda m: m.text=="🚀GET MY ID")
def get_my_id(message):
    if message.chat.type == "channel":
        cid = message.chat.id
        name = message.chat.title or "Channel"
    else:
        cid = message.from_user.id
        name = message.from_user.first_name
    loading = show_loading(message.chat.id)
    try: bot.delete_message(message.chat.id, loading.message_id)
    except: pass
    final = (f"🐦‍🔥 *CHAT ID FOUND* 🌹🌹\n"
             f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
             f"👋 Hello *{name}*!\n"
             f"📌 Your Chat ID: `{cid}`\n"
             f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
             f"🥀 *Owner:* @OWNERHIMANSHU 💨")
    if message.chat.type == "channel":
        bot.send_message(message.chat.id, final, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, final, parse_mode="Markdown", reply_markup=main_keyboard())

@bot.message_handler(commands=['Channelid'])
@bot.channel_post_handler(commands=['Channelid'])
@bot.message_handler(func=lambda m: m.text=="📢 GET CHANNEL ID")
def channel_id_command(message):
    if message.chat.type == "channel":
        bot.send_message(message.chat.id, f"📌 This channel's ID: `{message.chat.id}`", parse_mode="Markdown")
        return
    user_name = message.from_user.first_name
    text = (f"🗽 Hello {user_name}! 👋\n"
            f"🔍 Chat ID Finder Bot 🧞\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🐦‍🔥 To get Channel ID 💨\n"
            f"🚀 Click below to select saved channel\n"
            f"🛸 Or forward a message to auto-save\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🛸 Get your channel ID now! 🎭🪎🪎")
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("💠 ADD TO CHANNEL", url="https://t.me/TeligramidBot?startchannel&admin=post_messages"))
    kb.row(InlineKeyboardButton("🍂 MY CHANNELS", callback_data="find_channels"))
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=kb)

@bot.message_handler(commands=['groupid'])
@bot.channel_post_handler(commands=['groupid'])
@bot.message_handler(func=lambda m: m.text=="👥 GET GROUP ID")
def group_id_command(message):
    if message.chat.type in ["group", "supergroup"]:
        gid = message.chat.id
        gname = message.chat.title or "Unknown Group"
        db.add_group(message.from_user.id, gid, gname)
        bot.send_message(message.chat.id, f"📌 This group's ID: `{gid}`\n\n✅ Group saved for you.", parse_mode="Markdown")
        return
    user_name = message.from_user.first_name
    text = (f"🗽 Hello {user_name}! 👋\n"
            f"🔍 Chat ID Finder Bot 🧞\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🐦‍🔥 To get Group ID 💨\n"
            f"🚀 Click below to select saved group\n"
            f"🛸 Use `/**` in group to auto-save\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🛸 Get your group ID now! 🎭🪎🪎")
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("💠 ADD TO GROUP", url="https://t.me/TeligramidBot?startgroup&admin=post_messages"))
    kb.row(InlineKeyboardButton("🍂 MY GROUPS", callback_data="find_groups"))
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=kb)

# ==================== DIRECT SAVE – CHANNEL & GROUP (with owner fallback) ====================
@bot.message_handler(func=lambda message: message.text in ['/*', '/Csave', '/**', '/Gsave'])
@bot.channel_post_handler(func=lambda message: message.text in ['/*', '/Csave', '/**', '/Gsave'])
def save_group_or_channel(message):
    chat_type = message.chat.type
    if chat_type in ["group", "supergroup"]:
        gid = message.chat.id
        gname = message.chat.title or "Unknown Group"
        user_id = message.from_user.id
        db.add_group(user_id, gid, gname)
        loading = show_loading(message.chat.id)
        try: bot.delete_message(message.chat.id, loading.message_id)
        except: pass
        final = (f"🐦‍🔥 *GROUP ID FOUND* 🌹🌹\n"
                 f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                 f"👋 Hello *{message.from_user.first_name}*!\n"
                 f"📌 Your GROUP ID: `{gid}`\n"
                 f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                 f"🥀 *Owner:* @OWNERHIMANSHU 💨")
        bot.reply_to(message, final, parse_mode="Markdown")
    elif chat_type == "channel":
        cid = message.chat.id
        cname = message.chat.title or "Unknown Channel"

        # 1. Try to get stored owner
        owner_id = db.get_channel_owner(cid)

        # 2. If not found, try to fetch admins and set first non-bot admin as owner
        if not owner_id:
            try:
                admins = bot.get_chat_administrators(cid)
                for admin in admins:
                    if not admin.user.is_bot:
                        owner_id = admin.user.id
                        db.set_channel_owner(cid, owner_id)
                        logger.info(f"Owner set to {owner_id} from admin list for channel {cid}")
                        break
            except Exception as e:
                logger.error(f"Could not fetch admins for channel {cid}: {e}")

        # 3. If still no owner, ask user to forward a message
        if not owner_id:
            bot.reply_to(message, "❌ Could not determine channel owner. Please forward a message from this channel to me in private chat, then try again.", parse_mode="Markdown")
            return

        # Save channel for the found owner
        db.add_channel(owner_id, cid, cname)
        loading = show_loading(message.chat.id)
        try: bot.delete_message(message.chat.id, loading.message_id)
        except: pass
        final = (f"🐦‍🔥 *CHANNEL ID FOUND* 🌹🌹\n"
                 f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                 f"👋 Hello Owner (ID: `{owner_id}`)!\n"
                 f"📌 Your CHANNEL ID: `{cid}`\n"
                 f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                 f"🥀 *Owner:* @OWNERHIMANSHU 💨")
        bot.reply_to(message, final, parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ This command only works in groups or channels.", parse_mode="Markdown")

# ===================== CALLBACKS =====================
@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    user_id = call.from_user.id
    if check_membership(user_id):
        db.set_verified(user_id, True)
        bot.edit_message_text(
            "✅ **Verification successful!**\nYou can now use the bot.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='Markdown'
        )
        name = call.from_user.first_name
        text = (f"🗽{name} welcome back to ID Bot! 👋\n\n"
                f"🔍 *Chat ID Finder Bot* 🧞\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🚀 /getmyid – get your chat ID\n"
                f"🚀 /Channelid – For channel ID\n"
                f"👥 /groupid – For Group ID\n"
                f"🚀 /help – Manual\n\n"
                f"🛸 add me on your Group/channel & ❤️‍🔥 run commands to get your IDs 🦹 !")
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=main_keyboard())
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined the channel yet! Please join and click again.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "find_channels")
def find_channels(call):
    user_id = call.from_user.id
    channels = db.get_channels(user_id)
    if not channels:
        kb = InlineKeyboardMarkup()
        kb.row(InlineKeyboardButton("💠 ADD TO CHANNEL", url="https://t.me/TeligramidBot?startchannel&admin=post_messages"))
        bot.send_message(call.message.chat.id, "🚫 No channels saved yet.\nAdd me to your channel and use `/*` in channel to save.", parse_mode="Markdown", reply_markup=kb)
    else:
        kb = InlineKeyboardMarkup()
        for ch in channels:
            name = ch['name'][:18] + ".." if len(ch['name'])>18 else ch['name']
            kb.row(
                InlineKeyboardButton(name, callback_data=f"chid_{ch['id']}"),
                InlineKeyboardButton("🗑️", callback_data=f"del_ch_{ch['id']}")
            )
        bot.send_message(call.message.chat.id, f"📋 *Your Channels*\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n🍻 Tap name to get ID, 🗑️ to delete.", parse_mode="Markdown", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "find_groups")
def find_groups(call):
    user_id = call.from_user.id
    groups = db.get_groups(user_id)
    if not groups:
        kb = InlineKeyboardMarkup()
        kb.row(InlineKeyboardButton("💠 ADD TO GROUP", url="https://t.me/TeligramidBot?startgroup&admin=post_messages"))
        bot.send_message(call.message.chat.id, "🚫 No groups saved yet.\nAdd me to your group and use `/**` in group to save.", parse_mode="Markdown", reply_markup=kb)
    else:
        kb = InlineKeyboardMarkup()
        for gr in groups:
            name = gr['name'][:18] + ".." if len(gr['name'])>18 else gr['name']
            kb.row(
                InlineKeyboardButton(name, callback_data=f"gid_{gr['id']}"),
                InlineKeyboardButton("🗑️", callback_data=f"del_gr_{gr['id']}")
            )
        bot.send_message(call.message.chat.id, f"📋 *Your Groups*\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n🍻 Tap name to get ID, 🗑️ to delete.", parse_mode="Markdown", reply_markup=kb)
    bot.answer_callback_query(call.id)

# ---------- SHOW IDs WITH EXISTENCE CHECK ----------
@bot.callback_query_handler(func=lambda call: call.data.startswith('chid_'))
def show_channel_id(call):
    channel_id = call.data.replace('chid_','')
    user_id = call.from_user.id
    channels = db.get_channels(user_id)
    found = any(ch['id'] == int(channel_id) for ch in channels)
    if not found:
        bot.answer_callback_query(call.id, "❌ This channel is no longer in your saved list.", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        return
    loading = show_loading(call.message.chat.id)
    try: bot.delete_message(call.message.chat.id, loading.message_id)
    except: pass
    final = (f"🐦‍🔥 *CHANNEL ID FOUND* 🌹🌹\n"
             f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
             f"👋 Hello *{call.from_user.first_name}*!\n"
             f"📌 Your CHANNEL ID: `{channel_id}`\n"
             f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
             f"🥀 *Owner:* @OWNERHIMANSHU 💨")
    bot.send_message(call.message.chat.id, final, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('gid_'))
def show_group_id(call):
    group_id = call.data.replace('gid_','')
    user_id = call.from_user.id
    groups = db.get_groups(user_id)
    found = any(gr['id'] == int(group_id) for gr in groups)
    if not found:
        bot.answer_callback_query(call.id, "❌ This group is no longer in your saved list.", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        return
    loading = show_loading(call.message.chat.id)
    try: bot.delete_message(call.message.chat.id, loading.message_id)
    except: pass
    final = (f"🐦‍🔥 *GROUP ID FOUND* 🌹🌹\n"
             f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
             f"👋 Hello *{call.from_user.first_name}*!\n"
             f"📌 Your GROUP ID: `{group_id}`\n"
             f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
             f"🥀 *Owner:* @OWNERHIMANSHU 💨")
    bot.send_message(call.message.chat.id, final, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

# -------------------- DELETE CONFIRMATIONS --------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith('del_ch_'))
def confirm_delete_channel(call):
    channel_id = int(call.data.replace('del_ch_',''))
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("✅ Yes, delete", callback_data=f"confirm_del_ch_{channel_id}"),
        InlineKeyboardButton("❌ Cancel", callback_data="cancel_delete")
    )
    bot.send_message(call.message.chat.id, f"⚠️ Are you sure you want to delete this channel?\nID: `{channel_id}`", parse_mode="Markdown", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('del_gr_'))
def confirm_delete_group(call):
    group_id = int(call.data.replace('del_gr_',''))
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("✅ Yes, delete", callback_data=f"confirm_del_gr_{group_id}"),
        InlineKeyboardButton("❌ Cancel", callback_data="cancel_delete")
    )
    bot.send_message(call.message.chat.id, f"⚠️ Are you sure you want to delete this group?\nID: `{group_id}`", parse_mode="Markdown", reply_markup=kb)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_del_ch_'))
def delete_channel(call):
    channel_id = int(call.data.replace('confirm_del_ch_',''))
    db.remove_channel(call.from_user.id, channel_id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "✅ Channel removed from your saved list.")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_del_gr_'))
def delete_group(call):
    group_id = int(call.data.replace('confirm_del_gr_',''))
    db.remove_group(call.from_user.id, group_id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "✅ Group removed from your saved list.")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_delete")
def cancel_delete(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "❌ Deletion cancelled.")
    bot.answer_callback_query(call.id)

# ----- AUTO-SAVE ON FORWARD (fallback) -----
@bot.message_handler(content_types=['forward'])
@bot.channel_post_handler(content_types=['forward'])
def auto_save_forward(message):
    if message.forward_from_chat:
        chat = message.forward_from_chat
        cid = chat.id
        cname = chat.title or "Unknown"
        ctype = chat.type
        if ctype == "channel":
            if db.add_channel(message.from_user.id, cid, cname):
                bot.reply_to(message, f"✅ *Channel Saved!*\n📌 ID: `{cid}`\n📝 Name: {cname}", parse_mode="Markdown")
            else:
                bot.reply_to(message, "⚠️ This channel is already saved.", parse_mode="Markdown")
        elif ctype in ["group", "supergroup"]:
            if db.add_group(message.from_user.id, cid, cname):
                bot.reply_to(message, f"✅ *Group Saved!*\n📌 ID: `{cid}`\n📝 Name: {cname}", parse_mode="Markdown")
            else:
                bot.reply_to(message, "⚠️ This group is already saved.", parse_mode="Markdown")

# ----- ALIASES -----
@bot.message_handler(commands=['getcid'])
def get_cid(message):
    class Fake:
        id = "temp"
        from_user = message.from_user
        message = message
    find_channels(Fake())

@bot.message_handler(commands=['getgid'])
def get_gid(message):
    class Fake:
        id = "temp"
        from_user = message.from_user
        message = message
    find_groups(Fake())

# ----- DIRECT CHAT ID -----
@bot.message_handler(commands=['getchatid'])
@bot.channel_post_handler(commands=['getchatid'])
def get_chat_id(message):
    bot.send_message(message.chat.id, f"📌 This chat ID: `{message.chat.id}`", parse_mode="Markdown")

# ----- AI (optional) -----
@bot.message_handler(commands=['helpAi'])
@bot.channel_post_handler(commands=['helpAi'])
def ai_command(message):
    bot.send_message(message.chat.id, "🤖 AI Assistant is temporarily disabled. Use basic commands.")

@bot.message_handler(func=lambda m: m.text=="🤖 AI ASSISTANT")
def ai_btn(m):
    bot.send_message(m.chat.id, "Type /helpAi to use AI.")

# ----- IGNORE OTHER MESSAGES -----
@bot.message_handler(func=lambda message: True)
@bot.channel_post_handler(func=lambda message: True)
def ignore_all(message):
    pass

# -------------------- MAIN --------------------
if __name__ == "__main__":
    print("🚀 Bot started. Channel owner fallback via admin list added.")
    bot.infinity_polling()