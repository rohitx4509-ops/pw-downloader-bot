import telebot
import yt_dlp
import os
import re
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# 🔑 Bot Token
BOT_TOKEN = "8630261473:AAHYSFP3RX8lr-7v6nXrN-hIkI0F5n38mtw"
bot = telebot.TeleBot(BOT_TOKEN)

user_data = {}

# 🌐 Render Web Service Keep-Alive + HEAD Fix
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Mr_X45 Engine Active!")

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

# 1️⃣ URL Step
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 **नमस्ते भाई!**\n\nकोई भी PW/Streamthor लेक्चर URL भेजो।", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text and message.text.startswith("http"))
def handle_url(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'url': fix_pw_url(message.text)}
    
    msg = bot.reply_to(
        message, 
        "📝 **Step 1/3:**\n\n**Batch / Course Name** दर्ज करें:\n*(उदा. `LAKSHYA NEET HINDI`)*", 
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_batch_name)

# 2️⃣ Batch Name Step
def process_batch_name(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.reply_to(message, "❌ सेशन एक्सपायर हो गया, दोबारा URL भेजें।")
        return

    user_data[chat_id]['batch_name'] = message.text.strip()

    msg = bot.reply_to(
        message, 
        "👤 **Step 2/3:**\n\n**Uploaded By** में क्या नाम लिखना है?\n*(उदा. `Rahul` या `Mr_X45`)*", 
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_uploader_name)

# 3️⃣ Uploader Name & Resolution Menu
def process_uploader_name(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.reply_to(message, "❌ सेशन एक्सपायर हो गया, दोबारा URL भेजें।")
        return

    user_data[chat_id]['uploader'] = message.text.strip()

    menu_text = """╭───❮ SELECT RESOLUTION ❯────►
├───» send 144
├───» send 240
├───» send 360
├───» send 480
├───» send 720
├───» send 1080
╰───╭⚡[ Mr_X45 ]⚡╯───►"""

    bot.reply_to(message, f"```\n{menu_text}\n```", parse_mode="MarkdownV2")

# 4️⃣ Quality Selection Handler
@bot.message_handler(func=lambda message: message.text and message.text.startswith("send "))
def handle_quality(message):
    chat_id = message.chat.id
    if chat_id not in user_data or 'url' not in user_data[chat_id]:
        bot.reply_to(message, "❌ कृपया पहले नया Video URL भेजें।")
        return

    quality_choice = message.text.replace("send ", "").strip()
    user_data[chat_id]['quality'] = quality_choice
    data = user_data.pop(chat_id)

    status_msg = bot.reply_to(
        message, 
        f"🚀 **PROCESSING STARTED**\n\n📦 **Batch:** `{data['batch_name']}`\n🎯 **Quality:** `{data['quality']}p`\n\n⏳ **Extracting Stream...**\n`[░░░░░░░░░░] 0%`", 
        parse_mode="Markdown"
    )

    threading.Thread(target=process_download, args=(chat_id, data, status_msg.message_id)).start()

def make_pbar(percent):
    done = int(percent // 10)
    return "█" * done + "░" * (10 - done)

# 5️⃣ Downloader Engine
def process_download(chat_id, data, status_msg_id):
    output_file = f"lecture_{chat_id}.mp4"
    last_update = [time.time()]

    def my_hook(d):
        if d['status'] == 'downloading':
            now = time.time()
            if now - last_update[0] > 4: # Har 4 sec me update
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    percent = (downloaded / total) * 100
                    p_bar = make_pbar(percent)
                    speed = d.get('_speed_str', 'N/A')
                    text = f"📥 **DOWNLOADING LECTURE...**\n`[{p_bar}] {percent:.1f}%`\n🚀 **Speed:** `{speed}`"
                    try:
                        bot.edit_message_text(text, chat_id, status_msg_id, parse_mode="Markdown")
                    except Exception:
                        pass
                last_update[0] = now

    ydl_opts = {
        'format': f'bestvideo[height<={data["quality"]}]+bestaudio/best[height<={data["quality"]}]/best',
        'outtmpl': output_file,
        'concurrent_fragment_downloads': 6,  # Safe speed limit for free server
        'fragment_retries': 30,
        'socket_timeout': 30,                 # Unfreeze timeout fix
        'hls_use_mpegts': True,
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
            ydl.download([data['url']])

        bot.edit_message_text("⬆️ **DOWNLOAD COMPLETE! UPLOADING TO TELEGRAM...**", chat_id, status_msg_id, parse_mode="Markdown")

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

# Server Start
threading.Thread(target=run_dummy_server, daemon=True).start()

try:
    bot.remove_webhook(drop_pending_updates=True)
except Exception:
    pass

print("Mr_X45 Bot Engine Live!")
bot.infinity_polling()
