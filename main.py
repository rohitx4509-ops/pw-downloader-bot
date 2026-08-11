import telebot
import yt_dlp
import os
import re
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# 🔑 Bot Token
BOT_TOKEN = "8823136614:AAGEoT0TmZayMpnu2PC56vte3DDdFKHWyVw"
bot = telebot.TeleBot(BOT_TOKEN)

user_links = {}

# 🌐 Render Web Service Port Binding
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running Alive!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

def fix_pw_url(raw_url):
    url = raw_url.strip()
    if "/dash/" in url or "/hls/" in url:
        return re.sub(r'/(dash|hls)/.*$', '/master.m3u8', url)
    return url

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "नमस्ते भाई! मुझे कोई भी PW लेक्चर लिंक भेजो।")

@bot.message_handler(func=lambda message: message.text.startswith("http"))
def ask_quality(message):
    fixed_url = fix_pw_url(message.text)
    user_links[message.chat.id] = fixed_url
    
    menu_text = """╭───❮ENTER RESOLUTION❯────►
├───» send 144
├───» send 240
├───» send 360
├───» send 480
├───» send 720
├───» send 1080
╰───╭⚡[ Mr_X45 ]⚡╯───►"""

    bot.reply_to(message, f"```\n{menu_text}\n```", parse_mode="MarkdownV2")

def process_download(chat_id, m3u8_url, user_choice, msg_id):
    output_file = f"lecture_{chat_id}.mp4"

    ydl_opts = {
        'format': f'bestvideo[height<={user_choice}]+bestaudio/best[height<={user_choice}]/best',
        'outtmpl': output_file,
        'concurrent_fragment_downloads': 16,
        'fragment_retries': 50,
        'skip_unavailable_fragments': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://penpencil.co/',
            'Origin': 'https://penpencil.co'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([m3u8_url])

        bot.edit_message_text("⬆️ डाउनलोड पूरा हो गया! टेलीग्राम पर वीडियो अपलोड हो रही है...", chat_id, msg_id)
        
        caption_text = f"📦 <b>Title:</b> PW Lecture [{user_choice}p]\n🔗 <b>LNK:</b> Click Here\n\n🎓 <b>Uploaded By:</b> Mr_X45 ⚡"

        with open(output_file, 'rb') as video:
            bot.send_video(
                chat_id, 
                video, 
                caption=caption_text, 
                parse_mode="HTML"
            )

        if os.path.exists(output_file):
            os.remove(output_file)

    except Exception as e:
        bot.reply_to(chat_id, f"❌ एरर आया: {str(e)}")

@bot.message_handler(func=lambda message: message.chat.id in user_links)
def download_selected_quality(message):
    chat_id = message.chat.id
    m3u8_url = user_links.pop(chat_id)
    user_choice = message.text.replace("send", "").strip()

    msg = bot.reply_to(message, f"🚀 DOWNLOADING STARTED\n🔗 Link » {m3u8_url}\n\n⚡ 16x Multi-Thread स्पीड से डाउनलोड हो रहा है...")

    threading.Thread(target=process_download, args=(chat_id, m3u8_url, user_choice, msg.message_id)).start()

# 🌐 Web Server
threading.Thread(target=run_dummy_server, daemon=True).start()

# 🧹 Conflict Fix
try:
    bot.remove_webhook(drop_pending_updates=True)
except Exception:
    pass

print("Mr_X45 बोट (Web Service Active) चालू हो गया है...")
bot.infinity_polling()
