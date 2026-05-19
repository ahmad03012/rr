import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import string
import json
import os
import time

# --- PENGATURAN ---
TOKEN = '8620322880:AAEqjN2T_aguZ7vmNAMmZHuiXT4wiWSfnlA'
ADMIN_ID = '7565497204'
CHANNEL_USERNAME = '@dinopinksy'
GROUP_USERNAME = '@dinopinkygrup'
CHANNEL_BACKUP = '@backuppinky'

# GANTI INI kalau sudah dapat File ID logomu dari log Termux
THUMBNAIL_PERMANEN = 'AgACAgUAAxkBAAMzagWJKhpQRJRGN7NuX11DeYQeooEAAu0RaxvGZzFUvVopVJB7JJ8BAAMCAAN5AAM7BA' 

bot = telebot.TeleBot(TOKEN)
DB_FILE = 'database_media.json'
post_queue = {}

# --- FUNGSI DATABASE ---
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_db(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=4)

media_db = load_db()

def is_subscribed_both(user_id):
    try:
        status_ch = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        status_gr = bot.get_chat_member(GROUP_USERNAME, user_id).status
        valid = ['creator', 'administrator', 'member']
        return status_ch in valid and status_gr in valid
    except:
        return False

def kirim_media_proses(chat_id, kode):
    if kode in media_db:
        data = media_db[kode]
        if data['tipe'] == 'photo': 
            bot.send_photo(chat_id, data['file_id'])
        elif data['tipe'] == 'video': 
            bot.send_video(chat_id, data['file_id'])
        elif data['tipe'] == 'document': 
            bot.send_document(chat_id, data['file_id'])
    else:
        bot.send_message(chat_id, "❌ Link media tidak valid atau kadaluarsa.")


# --- HANDLER START ---
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    teks_perintah = message.text.split()
    
    # Buat link tombol biar gak typo
    url_ch = f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"
    url_gr = f"https://t.me/{GROUP_USERNAME.lstrip('@')}"

    # 1. JIKA START BIASA (TANPA LINK MEDIA)
    if len(teks_perintah) <= 1:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Join Channel", url=url_ch))
        markup.add(InlineKeyboardButton("💬 Join Grup", url=url_gr))

        bot.reply_to(message, f"Halo {message.from_user.first_name}! 👋\nGabung dulu ya untuk akses media.", reply_markup=markup)
        return

    # 2. JIKA START DENGAN LINK MEDIA (Contoh: /start abc123)
    kode = teks_perintah[1]

    if is_subscribed_both(user_id):
        # Kalau sudah join, langsung kirim filenya
        kirim_media_proses(user_id, kode)
    else:
        # INI YANG PERLU DIPERBAIKI: Tambahin tombol Join lagi di sini
        markup = InlineKeyboardMarkup()
        btn_ch = InlineKeyboardButton("📢 Join Channel", url=url_ch)
        btn_gr = InlineKeyboardButton("💬 Join Grup", url=url_gr)
        btn_cek = InlineKeyboardButton("🔄 Saya Sudah Join", callback_data=f"cek_{kode}")
        
        # Susun tombolnya biar rapi
        markup.add(btn_ch, btn_gr) # Tombol join sejajar
        markup.add(btn_cek)        # Tombol cek di bawahnya

        bot.reply_to(message, "🔒 **AKSES TERKUNCI**\nKamu harus join Channel dan Grup dulu baru bisa ambil file ini!", reply_markup=markup, parse_mode="Markdown")


# --- HANDLER POST ---
@bot.message_handler(commands=['p'])
def post_cepat(message):
    if str(message.from_user.id) != str(ADMIN_ID): return
    teks = message.text.split(maxsplit=1)
    judul = teks[1] if len(teks) > 1 else "Media Terbaru"
    post_queue[message.from_user.id] = {'step': 'file_saja', 'judul': judul}
    bot.reply_to(message, f"📌 Judul: {judul}\nKirim File Aslinya sekarang!")

# --- HANDLER MEDIA UTAMA ---
@bot.message_handler(content_types=['photo', 'video', 'document'])
def handle_all_media(message):
    if str(message.from_user.id) != str(ADMIN_ID): return
    
    # DEBUG: Biar kamu bisa liat File ID foto logo di Termux
    if message.photo:
        print(f"DEBUG FILE ID: {message.photo[-1].file_id}")

    user_id = message.from_user.id
    unik_id = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    
    if message.photo: file_id, tipe = message.photo[-1].file_id, 'photo'
    elif message.video: file_id, tipe = message.video.file_id, 'video'
    elif message.document: file_id, tipe = message.document.file_id, 'document'
    else: return

        # Jika sedang dalam proses /post
    if user_id in post_queue and post_queue[user_id]['step'] == 'file_saja':
        judul = post_queue[user_id]['judul']
        media_db[unik_id] = {'file_id': file_id, 'tipe': tipe}
        save_db(media_db)

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🚀 AMBIL FILE", url=f"https://t.me/{bot.get_me().username}?start={unik_id}"))

        # 1. Post ke Channel Utama
        try:
            bot.send_photo(CHANNEL_USERNAME, THUMBNAIL_PERMANEN, caption=f"{judul}", reply_markup=markup)
        except Exception as e:
            print(f"Gagal ke Channel Utama: {e}")

        # 2. Post ke Channel Backup (Tambahan Baru)
        try:
            # Kita kirim hal yang sama ke channel backup agar ada arsipnya
            bot.send_photo(CHANNEL_BACKUP, THUMBNAIL_PERMANEN, caption=f"📦 BACKUP: {judul}\n\nLink: https://t.me/{bot.get_me().username}?start={unik_id}", reply_markup=markup)
        except Exception as e:
            print(f"Gagal ke Channel Backup: {e}")

        bot.reply_to(message, "✅ Berhasil post ke Channel Utama & Backup!")
        del post_queue[user_id]

    else:
        # Simpan biasa (tanpa post ke channel)
        media_db[unik_id] = {'file_id': file_id, 'tipe': tipe}
        save_db(media_db)
        bot.reply_to(message, f"✅ Tersimpan!\nLink: `https://t.me/{bot.get_me().username}?start={unik_id}`")

# --- CALLBACK CEK JOIN ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('cek_'))
def validasi_join(call):
    kode = call.data.split('_')[1]
    if is_subscribed_both(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        kirim_media_proses(call.message.chat.id, kode)
    else:
        bot.answer_callback_query(call.id, "❌ Kamu belum join!", show_alert=True)

# --- PING ---
@bot.message_handler(commands=['ping'])
def test_ping(message):
    start = time.time()
    msg = bot.reply_to(message, "🚀 Checking...")
    ms = round((time.time() - start) * 1000)
    bot.edit_message_text(f"📊 **ONLINE**\n⚡ `{ms} ms`\n🤖 Server: Termux", msg.chat.id, msg.message_id)

# --- FITUR KIRIM PESAN KE GRUP (BROADCAST) ---
@bot.message_handler(commands=['bc'])
def broadcast_grup(message):
    # Cek apakah yang menjalankan adalah Admin
    if str(message.from_user.id) != str(ADMIN_ID): 
        return
    
    # Ambil teks setelah perintah /bc
    teks_bc = message.text.split(maxsplit=1)
    
    if len(teks_bc) < 2:
        bot.reply_to(message, "⚠️ Format salah! Gunakan: `/bc [pesan kamu]`", parse_mode="Markdown")
        return
    
    pesan = teks_bc[1]
    
    try:
        # Kirim pesan ke grup
        bot.send_message(GROUP_USERNAME, pesan, parse_mode="Markdown")
        bot.reply_to(message, "✅ Pesan berhasil dikirim ke grup!")
    except Exception as e:
        bot.reply_to(message, f"❌ Gagal mengirim pesan:\n`{str(e)}`", parse_mode="Markdown")

print("🚀 Bot Menyala!")
bot.infinity_polling(timeout=60, long_polling_timeout=5)
