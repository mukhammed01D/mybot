
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot aktivik!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    
        
def save_user(user_id):
    try:
        users = set()
        if os.path.exists("users.txt"):
            with open("users.txt", "r") as f:
                users = set(f.read().splitlines())
        
        if str(user_id) not in users:
            with open("users.txt", "a") as f:
                f.write(f"{user_id}\n")
    except Exception as e:
        print(f"User saqlashda xatolik: {e}")        
        

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
import yt_dlp
import static_ffmpeg
static_ffmpeg.add_paths()
# @BotFather'dan olingan tokeningizni shu yerga qo'ying
BOT_TOKEN = "8895942423:AAFf8i-x51GUqrQlmBMcxxHHnDhSxoDfIBU"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer(
        "Salom! Menga Instagram, YouTube, TikTok yoki boshqa ijtimoiy tarmoqdan video havolasini yuboring.\n\n"
        "Men sizga video yoki musiqasini yuklab beraman!"
    )

@dp.message(F.text.startswith("http://") | F.text.startswith("https://"))
async def handle_url(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎬 Video yuklash", callback_data="dl_video"),
            InlineKeyboardButton(text="🎵 Musiqasini yuklash (MP3)", callback_data="dl_audio")
        ]
    ])
    await message.reply("Nimasini yuklab bermoqchisiz?", reply_markup=kb)

@dp.callback_query(F.data.in_({"dl_video", "dl_audio"}))
async def process_download(call: types.CallbackQuery):
    if call.message.reply_to_message and call.message.reply_to_message.text: 
        url = call.message.reply_to_message.text.strip()
    else:
        url = call.message.text.strip()
    download_type = call.data
    
    await call.message.edit_text("⏳ Yuklanmoqda, biroz kuting...")
    
    file_path = os.path.join(DOWNLOAD_DIR, f"{call.from_user.id}_{call.message.message_id}")
    
    if download_type == "dl_video":
        ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': f'{file_path}.%(ext)s',
            'quiet': True,
            'max_filesize': 50 * 1024 * 1024
        }
    else:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{file_path}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'max_filesize': 50 * 1024 * 1024
        }

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: download_media(url, ydl_opts))
        
        downloaded_file = None
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(os.path.basename(file_path)):
                downloaded_file = os.path.join(DOWNLOAD_DIR, f)
                break
                
        if downloaded_file and os.path.exists(downloaded_file):
            input_file = FSInputFile(downloaded_file)
            if download_type == "dl_video":
                await call.message.answer_video(video=input_file, caption="✅ Video yuklab olindi!")
            else:
                await call.message.answer_audio(audio=input_file, caption="✅ Musiqa yuklab olindi!")
            
            os.remove(downloaded_file)
            await call.message.delete()
        else:
            await call.message.edit_text("❌ Faylni yuklab bo'lmadi. Havola to'g'riligini tekshiring.")

    except Exception as e:
        if downloaded_file and os.path.exists(downloaded_file):
            os.remove(downloaded_file)
        await call.message.edit_text("❌ Xatolik yuz berdi: Fayl hajmi juda katta bo'lishi yoki havola yopiq profildan bo'lishi mumkin.")
        

def download_media(url, opts):
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
