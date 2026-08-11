import os
import re
import sys
import json
import time
import asyncio
import requests
import subprocess
import urllib.parse
import yt_dlp
import cloudscraper
import m3u8
import core as helper
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN
from aiohttp import ClientSession
from pyromod import listen
from subprocess import getstatusoutput
from pytube import YouTube
from aiohttp import web
import logging
from logging.handlers import RotatingFileHandler
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("logs.txt", maxBytes=50000000, backupCount=10),
        logging.StreamHandler(),
    ],
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging = logging.getLogger()

# Initialize the bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

my_name = "Mr_X45"
cookies_file_path = os.getenv("COOKIES_FILE_PATH", "/modules/youtube_cookies.txt")

# ⚡ Fast Aria2c Multi-Thread Engine
def pwdlx_video(url: str, output_filename: str):
    cmd = [
        "yt-dlp",
        "--newline",
        "--merge-output-format", "mp4",
        "--remux-video", "mp4",
        "--concurrent-fragments", "16",
        "--downloader", "aria2c",
        "--downloader-args", "aria2c:-x16 -s16 -k1M -j16",
        "--add-header", "Referer:https://penpencil.co/",
        "--add-header", "Origin:https://penpencil.co",
        "-o", output_filename,
        url,
    ]
    subprocess.run(cmd, check=True)
    return output_filename

def extract_content_id(url):
    try:
        if "contentId=" in url:
            parts = url.split("contentId=")
            if len(parts) > 1:
                content_id = parts[1]
                for char in ["?", "&"]:
                    if char in content_id:
                        content_id = content_id.split(char)[0]
                if content_id.endswith(".m3u8"):
                    content_id = content_id[:-5]
                elif ".m3u8" in content_id:
                    content_id = content_id.split(".m3u8")[0]
                return content_id
        return None
    except Exception as e:
        return None

def get_jw_signed_url(content_id, access_token):
    url = f"https://api.classplusapp.com/cams/uploader/video/jw-signed-url?contentId={urllib.parse.quote(content_id, safe='')}"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en",
        "Origin": "https://web.classplusapp.com",
        "Referer": "https://web.classplusapp.com/",
        "Region": "IN",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/139.0.0.0 Safari/537.36",
        "X-Access-Token": access_token,
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        return data.get("url")
    except Exception as e:
        return None

routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("https://pw-downloader-bot.onrender.com/")

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app

# 🌟 PREMIUM START COMMAND
@bot.on_message(filters.command("start"))
async def start(client: Client, msg: Message):
    welcome_text = (
        f"╭───❮ **MR_X45 BATCH EXTRACTOR** ❯───►\n"
        f"│\n"
        f"├──» **WELCOME:** {msg.from_user.mention}\n"
        f"├──» **STATUS:** **ONLINE & ACTIVE** ⚡\n"
        f"│\n"
        f"╰───╭⚡ **POWERED BY MR_X45** ⚡╯───►"
    )
    start_message = await client.send_message(msg.chat.id, welcome_text)
    await asyncio.sleep(1)

@bot.on_message(filters.command(["stop"]))
async def restart_handler(_, m):
    stop_text = (
        f"╭───❮ **ENGINE STOPPED** ❯───►\n"
        f"│\n"
        f"├──» **STATUS:** **PROCESS TERMINATED** 🛑\n"
        f"│\n"
        f"╰───╭⚡ **MR_X45 STUDIO** ⚡╯───►"
    )
    await m.reply_text(stop_text, quote=True)
    os.execl(sys.executable, sys.executable, *sys.argv)

# 🚀 CORE TXT HANDLER COMMANDS (/Mrx45 & /Official)
@bot.on_message(filters.command(["Mrx45", "Official"]))
async def txt_handler(bot: Client, m: Message):
    prompt_txt = (
        f"╭───❮ **TXT BATCH LEECHER** ❯───►\n"
        f"│\n"
        f"├──» **SEND TXT FILE TO BEGIN EXTRACTING** 📥\n"
        f"│\n"
        f"╰───╭⚡ **MR_X45 STUDIO** ⚡╯───►"
    )
    editable = await m.reply_text(prompt_txt)
    input_msg: Message = await bot.listen(editable.chat.id)
    x = await input_msg.download()
    await input_msg.delete(True)
    file_name, ext = os.path.splitext(os.path.basename(x))
    credit = f"@rahulx45_vibe"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." # Default Token

    try:
        with open(x, "r") as f:
            content = f.read()
        content = content.split("\n")
        links = [i.split("://", 1) for i in content if "://" in i]
        os.remove(x)
    except Exception:
        await m.reply_text("❌ **INVALID TXT FILE! RESEND AGAIN.**")
        if os.path.exists(x):
            os.remove(x)
        return

    # STEP 1: INDEX
    await editable.edit(
        f"╭───❮ **TOTAL LINKS FOUND:** `{len(links)}` ❯───►\n"
        f"│\n"
        f"├──» **ENTER START INDEX:** *(DEFAULT 1)*\n"
        f"│\n"
        f"╰───╭⚡ **MR_X45 STUDIO** ⚡╯───►"
    )
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)
    try:
        arg = int(raw_text)
    except Exception:
        arg = 1

    # STEP 2: BATCH NAME
    await editable.edit(
        f"╭───❮ **BATCH NAME SETUP** ❯───►\n"
        f"│\n"
        f"├──» **ENTER BATCH NAME** OR SEND `/Rahul`\n"
        f"│\n"
        f"╰───╭⚡ **MR_X45 STUDIO** ⚡╯───►"
    )
    input1: Message = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)
    b_name = file_name if raw_text0 == '/Rahul' else raw_text0

    # STEP 3: RESOLUTION
    res_menu = (
        f"╭───❮ **SELECT RESOLUTION** ❯───►\n"
        f"├──» **144**\n"
        f"├──» **240**\n"
        f"├──» **360**\n"
        f"├──» **480**\n"
        f"├──» **720**\n"
        f"├──» **1080**\n"
        f"╰───╭⚡ **MR_X45 STUDIO** ⚡╯───►"
    )
    await editable.edit(res_menu)
    input2: Message = await bot.listen(editable.chat.id)
    raw_text2 = input2.text.strip()
    await input2.delete(True)
    
    res_map = {"144": "256x144", "240": "426x240", "360": "640x360", "480": "854x480", "720": "1280x720", "1080": "1920x1080"}
    res = res_map.get(raw_text2, "854x480")

    # STEP 4: UPLOADER NAME
    await editable.edit(
        f"╭───❮ **CREDITS SETUP** ❯───►\n"
        f"│\n"
        f"├──» **ENTER UPLOADER NAME** OR SEND `/Rahul`\n"
        f"│\n"
        f"╰───╭⚡ **MR_X45 STUDIO** ⚡╯───►"
    )
    input3: Message = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)
    CR = credit if raw_text3 in ['/Rahul', '/Official', '/Cutie'] else raw_text3

    # STEP 5: TOKEN
    await editable.edit(
        f"╭───❮ **PW TOKEN SETUP** ❯───►\n"
        f"│\n"
        f"├──» **ENTER PW TOKEN** OR SEND `/X45`\n"
        f"│\n"
        f"╰───╭⚡ **MR_X45 STUDIO** ⚡╯───►"
    )
    input4: Message = await bot.listen(editable.chat.id)
    raw_text4 = input4.text
    await input4.delete(True)
    access_token = token if raw_text4 in ['/X45', '/vip'] else raw_text4

    # STEP 6: THUMBNAIL
    await editable.edit(
        f"╭───❮ **THUMBNAIL SETUP** ❯───►\n"
        f"│\n"
        f"├──» **SEND THUMBNAIL URL** OR TYPE `no`\n"
        f"│\n"
        f"╰───╭⚡ **MR_X45 STUDIO** ⚡╯───►"
    )
    input6: Message = await bot.listen(editable.chat.id)
    raw_text6 = input6.text
    await input6.delete(True)
    await editable.delete()

    thumb = raw_text6
    if thumb.startswith("http://") or thumb.startswith("https://"):
        getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb = "no"

    count = int(arg)
    
    # DOWNLOAD LOOP
    try:
        for i in range(arg - 1, len(links)):
            Vxy = links[i][1].replace("file/d/", "uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing", "")
            url = "https://" + Vxy

            if 'https://contentId=' in url or 'contentHashIdl=' in url:
                content_id = extract_content_id(url)
                cpurl = get_jw_signed_url(content_id, access_token)
                if cpurl:
                    url = cpurl

            elif '/master.mpd' in url or "/dash/" in url or "parentId=" in url:
                if "parentId=" in url or "childId=" in url:
                    url = f"https://ankitshakyaxapi.vercel.app/download?mpd_url={url}&token={raw_text4}&quality={raw_text2}"
                else:
                    url = f"https://ankitshakyaxapi.vercel.app/download?mpd_url={url}&quality={raw_text2}"

            name1 = links[i][0].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            name = f'{str(count).zfill(3)}) {name1[:60]} {my_name}'

            if "youtu" in url:
                ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"

            cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

            # PREMIUM CAPTION BOLD FORMATTING
            cc = (
                f"╭───❮ **MR_X45 LECTURE EXTRACTED** ❯───►\n"
                f"│\n"
                f"├──» **ID:** `{str(count).zfill(3)}` \n"
                f"├──» **TITLE:** **{name1}**\n"
                f"├──» **QUALITY:** **{raw_text2}p HD**\n"
                f"├──» **BATCH:** **{b_name}**\n"
                f"│\n"
                f"├──» **EXTRACTED BY:** **{CR}**\n"
                f"│\n"
                f"╰───╭⚡ **POWERED BY MR_X45** ⚡╯───►"
            )

            cc1 = (
                f"╭───❮ **MR_X45 DOCUMENT EXTRACTED** ❯───►\n"
                f"│\n"
                f"├──» **ID:** `{str(count).zfill(3)}` \n"
                f"├──» **TITLE:** **{name1}**\n"
                f"├──» **BATCH:** **{b_name}**\n"
                f"│\n"
                f"├──» **EXTRACTED BY:** **{CR}**\n"
                f"│\n"
                f"╰───╭⚡ **POWERED BY MR_X45** ⚡╯───►"
            )

            try:
                if ".pdf" in url:
                    scraper = cloudscraper.create_scraper()
                    response = scraper.get(url.replace(" ", "%20"))
                    if response.status_code == 200:
                        with open(f'{name}.pdf', 'wb') as file:
                            file.write(response.content)
                        await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                        count += 1
                        os.remove(f'{name}.pdf')
                else:
                    download_status = (
                        f"╭───❮ **DOWNLOADING LECTURE** ❯───►\n"
                        f"│\n"
                        f"├──» **INDEX:** `{str(count).zfill(3)}` \n"
                        f"├──» **TITLE:** **{name1[:40]}**\n"
                        f"├──» **QUALITY:** **{raw_text2}p**\n"
                        f"│\n"
                        f"╰───╭⚡ **MR_X45 STUDIO** ⚡╯───►"
                    )
                    prog = await m.reply_text(download_status)
                    output_filename = f"{name}.mp4"
                    res_file = pwdlx_video(url, output_filename)
                    await prog.delete(True)
                    await helper.send_vid(bot, m, cc, res_file, thumb, name, prog)
                    count += 1
                    await asyncio.sleep(1)

            except FloodWait as e:
                await asyncio.sleep(e.x)
                continue
            except Exception as e:
                await m.reply_text(
                    f"╭───❮ **DOWNLOAD FAILED** ❯───►\n"
                    f"│\n"
                    f"├──» **ID:** `{str(count).zfill(3)}` \n"
                    f"├──» **TITLE:** **{name1[:30]}**\n"
                    f"│\n"
                    f"╰───╭⚡ **MR_X45 STUDIO** ⚡╯───►"
                )
                continue

    except Exception as e:
        await m.reply_text(f"❌ **ERROR:** `{str(e)}`")

    done_text = (
        f"╭───❮ **EXTRACTION COMPLETED** ❯───►\n"
        f"│\n"
        f"├──» **ALL LECTURES EXTRACTED SUCCESSFULLY** ✅\n"
        f"│\n"
        f"╰───╭⚡ **MR_X45 STUDIO** ⚡╯───►"
    )
    await m.reply_text(done_text)

bot.run()
