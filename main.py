import telebot
import yt_dlp
import os
import re
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# 🔑 Bot Token Setup
BOT_TOKEN = "8630261473:AAG-349fL3P-xL5x_Rmt_p8m3tw"
print(f"DEBUG: Bot Token Loaded: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}

# 🌐 Dummy Health-Check Server (Render Keep-Alive)
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Engine Active!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

def fix_pw_url(raw_url):
    url = raw_url.strip()
    if "/dash/" in url or "/hls/" in url:
        return re.sub(r'/(dash|hls)/.*$', '/master.m3u8', url)
    return url

def make_pbar(percent):
    done = int(percent // 10)
    return "█" * done + "░" * (10 - done)

# 1️⃣ Start & URL Handlers
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 **PW / JS Script URL Bhejo Bhai!**", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text and message.text.startswith("http"))
def handle_url(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'url': fix_pw_url(message.text)}
    
    msg = bot.reply_to(message, "📝 **Batch Name दर्ज करें:**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_batch_name)

def process_batch_name(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        return
    user_data[chat_id]['batch_name'] = message.text.strip()

    msg = bot.reply_to(message, "👤 **Uploaded By में क्या नाम लिखना है?**", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_uploader_name)

def process_uploader_name(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        return
    user_data[chat_id]['uploader'] = message.text.strip()

    menu_text = """╭───❮ SELECT RESOLUTION ❯────►
├───» 144
├───» 240
├───» 360
├───» 480
├───» 720
├───» 1080
╰───╭⚡[ Mr_X45 ]⚡╯───►"""

    bot.reply_to(message, f"```\n{menu_text}\n```", parse_mode="MarkdownV2")

@bot.message_handler(func=lambda message: message.text and any(q in message.text for q in ["144", "240", "360", "480", "720", "1080"]))
def handle_quality(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        return

    quality_match = re.search(r'(144|240|360|480|720|1080)', message.text)
    if not quality_match:
        return

    data = user_data.pop(chat_id)
    data['quality'] = quality_match.group(1)

    status_msg = bot.reply_to(
        message, 
        f"🚀 **DOWNLOAD STARTED...**\n\n📦 **Batch:** `{data['batch_name']}`\n🎯 **Quality:** `{data['quality']}p`", 
        parse_mode="Markdown"
    )

    threading.Thread(target=process_download, args=(chat_id, data, status_msg.message_id)).start()

def process_download(chat_id, data, status_msg_id):
    output_file = f"lecture_{chat_id}.mp4"

    ydl_opts = {
        'format': f'bestvideo[height<={data["quality"]}]+bestaudio/best[height<={data["quality"]}]/best',
        'outtmpl': output_file,
        'external_downloader': 'aria2c',
        'external_downloader_args': ['-j', '16', '-x', '16', '-s', '16', '-k', '1M'],
        'nocheckcertificate': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'https://penpencil.co/',
            'Origin': 'https://penpencil.co'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([data['url']])

        bot.edit_message_text("⬆️ **DOWNLOAD COMPLETE! UPLOADING...**", chat_id, status_msg_id, parse_mode="Markdown")

        caption_text = f"""
📚 <b>Batch:</b> {data['batch_name']}
🎯 <b>Quality:</b> {data['quality']}p HD
🔗 <b>LNK:</b> <a href="{data['url']}">Click Here To Stream</a>

━━━━━━━━━━━━━━━━━━━━
🎓 <b>Uploaded By:</b> {data['uploader']}
⚡ <b>Powered By:</b> <b>Mr_X45 Studio</b>
━━━━━━━━━━━━━━━━━━━━
        """

        with open(output_file, 'rb') as video:
            bot.send_video(
                chat_id, 
                video, 
                caption=caption_text.strip(), 
                parse_mode="HTML"
            )

        if os.path.exists(output_file):
            os.remove(output_file)

    except Exception as e:
        bot.reply_to(chat_id, f"❌ **Error:** `{str(e)}`", parse_mode="Markdown")

# 🚀 Start Background HTTP Server
threading.Thread(target=run_dummy_server, daemon=True).start()

# 🤖 Start Polling
try:
    bot.remove_webhook(drop_pending_updates=True)
except Exception:
    pass

bot.infinity_polling()
