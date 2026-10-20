import os
import json
import logging
from datetime import datetime
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import soundfile as sf
import noisereduce as nr
import librosa

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("❌ Ошибка: Токен не найден! Проверь файл .env")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

JSON_FILE = "users.json"


# ==========================================
# БЛОК СОХРАНЕНИЯ В JSON
# ==========================================

def log_user_action(user: types.User, action_type: str):
    """Сохраняет данные пользователя и его действие в понятный JSON-файл."""
    data = []
    
    # Если файл уже существует, считываем старые данные
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []

    # Создаем новую запись о действии
    new_entry = {
        "user_id": user.id,
        "username": user.username or "No username",
        "full_name": user.full_name,
        "action_type": action_type,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Добавляем в общий список
    data.append(new_entry)

    # Сохраняем обратно в файл с красивыми отступами (indent=4)
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# ==========================================
# ФУНКЦИИ ФИЛЬТРАЦИИ
# ==========================================

def enhance_image(input_path: str, output_path: str):
    img = Image.open(input_path).convert("RGB")
    img_np = np.array(img)
    denoised = cv2.fastNlMeansDenoisingColored(img_np, None, 10, 10, 7, 21)
    img = Image.fromarray(denoised)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    img = ImageEnhance.Contrast(img).enhance(1.2)
    img.save(output_path, quality=95)


def enhance_audio(input_path: str, output_path: str):
    data, sr = librosa.load(input_path, sr=None)
    reduced_noise = nr.reduce_noise(y=data, sr=sr, prop_decrease=0.85)
    sf.write(output_path, reduced_noise, sr)


def enhance_video(input_path: str, output_path: str):
    cap = cv2.VideoCapture(input_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        denoised_frame = cv2.fastNlMeansDenoisingColored(frame, None, 6, 6, 7, 21)
        out.write(denoised_frame)
        
    cap.release()
    out.release()


# ==========================================
# ОБРАБОТЧИКИ СООБЩЕНИЙ
# ==========================================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    log_user_action(message.from_user, "START")
    try:
        await message.delete()
    except Exception:
        pass

    await message.answer(
        "⚡ **Твой мультимедиа-фильтр!**\n\n"
        "Просто отправь мне файл (фото, голосовое, видео или кружочек), "
        "и я выдам тебе уже отфильтрованную и чистую версию."
    )


@dp.message(F.photo)
async def handle_photo(message: types.Message):
    log_user_action(message.from_user, "PHOTO")
    processing = await message.answer("🔄 Обрабатываю изображение на цифровом уровне...")
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    in_file, out_file = f"in_{photo.file_id}.jpg", f"out_{photo.file_id}.jpg"
    await bot.download(file_info, destination=in_file)
    
    try:
        enhance_image(in_file, out_file)
        await message.answer_photo(FSInputFile(out_file), caption="✨ Картинка улучшена и очищена.")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {e}")
    finally:
        if os.path.exists(in_file): os.remove(in_file)
        if os.path.exists(out_file): os.remove(out_file)
        await bot.delete_message(message.chat.id, processing.message_id)


@dp.message(F.voice)
async def handle_voice(message: types.Message):
    log_user_action(message.from_user, "VOICE")
    processing = await message.answer("🔄 Очищаю голосовое от посторонних шумов и машин...")
    voice = message.voice
    file_info = await bot.get_file(voice.file_id)
    in_file, out_file = f"in_{voice.file_id}.ogg", f"out_{voice.file_id}.wav"
    await bot.download(file_info, destination=in_file)
    
    try:
        enhance_audio(in_file, out_file)
        await message.answer_voice(FSInputFile(out_file), caption="🎧 Голос полностью очищен от шумов.")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {e}")
    finally:
        if os.path.exists(in_file): os.remove(in_file)
        if os.path.exists(out_file): os.remove(out_file)
        await bot.delete_message(message.chat.id, processing.message_id)


@dp.message(F.video)
async def handle_video(message: types.Message):
    log_user_action(message.from_user, "VIDEO")
    processing = await message.answer("🔄 Обрабатываю видео (это может занять время)...")
    video = message.video
    file_info = await bot.get_file(video.file_id)
    in_file, out_file = f"in_{video.file_id}.mp4", f"out_{video.file_id}.mp4"
    await bot.download(file_info, destination=in_file)
    
    try:
        enhance_video(in_file, out_file)
        await message.answer_video(FSInputFile(out_file), caption="🎬 Видео успешно отфильтровано.")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {e}")
    finally:
        if os.path.exists(in_file): os.remove(in_file)
        if os.path.exists(out_file): os.remove(out_file)
        await bot.delete_message(message.chat.id, processing.message_id)


@dp.message(F.video_note)
async def handle_video_note(message: types.Message):
    log_user_action(message.from_user, "VIDEO_NOTE")
    processing = await message.answer("🔄 Обрабатываю видео-заметку...")
    video_note = message.video_note
    file_info = await bot.get_file(video_note.file_id)
    in_file, out_file = f"in_{video_note.file_id}.mp4", f"out_{video_note.file_id}.mp4"
    await bot.download(file_info, destination=in_file)
    
    try:
        enhance_video(in_file, out_file)
        video_note_from_pc = FSInputFile(out_file)
        await message.answer_video_note(video_note_from_pc)
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {e}")
    finally:
        if os.path.exists(in_file): os.remove(in_file)
        if os.path.exists(out_file): os.remove(out_file)
        await bot.delete_message(message.chat.id, processing.message_id)


@dp.message(F.document | F.audio | F.animation)
async def handle_any_file(message: types.Message):
    log_user_action(message.from_user, "OTHER_FILE")
    await message.answer(
        "📂 Я получил твой файл! Сейчас я работаю с фото, видео и голосовыми сообщениями."
    )


@dp.message()
async def handle_unknown(message: types.Message):
    log_user_action(message.from_user, "TEXT_OR_UNKNOWN")
    await message.answer("🤔 Я пока не умею обрабатывать этот формат, отправь мне фото, видео или голосовое сообщение.")


if __name__ == "__main__":
    import asyncio
    print("Бот успешно запущен и сохраняет активность в users.json...")
    asyncio.run(dp.start_polling(bot))