import telebot
import yt_dlp
import os
import re
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = "8823136614:AAGEoT0TmZayMpnu2PC56vte3DDdFKHWyVw"
bot = telebot.TeleBot(BOT_TOKEN)

# 🌐 Render Keep-Alive Server
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Engine Active")

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
    bot.reply_to(message, "👋 PW Link Bhejo Bhai!")

@bot.message_handler(func=lambda message: message.text and message.text.startswith("http"))
def download_lecture(message):
    chat_id = message.chat.id
    raw_url = message.text.strip()
    m3u8_url = fix_pw_url(raw_url)

    status_msg = bot.reply_to(message, "⏳ **Extracting Stream & Downloading...**\n`[░░░░░░░░░░] 0%`", parse_mode="Markdown")

    threading.Thread(target=process_stream, args=(chat_id, m3u8_url, status_msg.message_id)).start()

def make_progress_bar(percent):
    done = int(percent // 10)
    return "█" * done + "░" * (10 - done)

def process_stream(chat_id, m3u8_url, status_msg_id):
    output_file = f"lecture_{chat_id}.mp4"
    last_update = [time.time()]

    # 📊 Real-Time Download Progress Hook
    def my_hook(d):
        if d['status'] == 'downloading':
            now = time.time()
            if now - last_update[0] > 3: # Har 3 sec me update
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    percent = (downloaded / total) * 100
                    p_bar = make_progress_bar(percent)
                    speed = d.get('_speed_str', 'N/A')
                    text = f"📥 **DOWNLOADING LECTURE...**\n`[{p_bar}] {percent:.1f}%`\n🚀 **Speed:** `{speed}`"
                    try:
                        bot.edit_message_text(text, chat_id, status_msg_id, parse_mode="Markdown")
                    except Exception:
                        pass
                last_update[0] = now

    # ⚡ Robust Multi-Thread Stream Downloader Engine
    ydl_opts = {
        'format': 'bestvideo[height<=480]+bestaudio/best[height<=480]/best',
        'outtmpl': output_file,
        'concurrent_fragment_downloads': 10,
        'fragment_retries': 100,
        'skip_unavailable_fragments': True,
        'progress_hooks': [my_hook],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'https://penpencil.co/',
            'Origin': 'https://penpencil.co'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([m3u8_url])

        bot.edit_message_text("⬆️ **DOWNLOAD COMPLETE! UPLOADING TO TELEGRAM...**\n`[██████████] 100%`", chat_id, status_msg_id, parse_mode="Markdown")

        # Upload Lecture
        with open(output_file, 'rb') as video:
            bot.send_video(
                chat_id, 
                video, 
                caption="🎓 **PW Lecture Successfully Extracted!**\n⚡ **Uploaded By:** Mr_X45", 
                parse_mode="Markdown"
            )

        if os.path.exists(output_file):
            os.remove(output_file)

    except Exception as e:
        bot.reply_to(chat_id, f"❌ **Error:** `{str(e)}`", parse_mode="Markdown")

threading.Thread(target=run_dummy_server, daemon=True).start()

try:
    bot.remove_webhook(drop_pending_updates=True)
except Exception:
    pass

print("Mr_X45 Direct Extractor Active!")
bot.infinity_polling()
