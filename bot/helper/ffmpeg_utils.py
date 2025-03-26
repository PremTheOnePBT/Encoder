import asyncio
import pyrogram
from pyrogram import filters
import os
import sys
import json
from pathlib import Path
import anitopy
import psutil
import time
import itertools
import math
import re
import shutil
import signal
import logging
from .function import hbs, info
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from bot import ffmpeg, app, LOG_CHANNEL, data
from subprocess import call, check_output
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
import subprocess
from subprocess import Popen, PIPE

logz = 5121002601

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
LOGGER = logging.getLogger(__name__)

async def run_subprocess(cmd):
    """Runs an asynchronous shell subprocess"""
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    return await process.communicate()

async def download_logo():
    """Automatically downloads the logo before encoding"""
    logo_path = "logo.png"
    logo_url = "https://telegra.ph/file/7d6d3298f8f1c23ed748b.png"

    if not os.path.exists(logo_path):  # Avoid re-downloading if already present
        subprocess.run(["wget", "-O", logo_path, logo_url])

    return logo_path

@app.on_callback_query()
async def stats(_, event):
    """Handles button clicks in Telegram"""
    try:
        if "stats" in event.data:
            data_s = event.data
            file = data_s.replace("stats", "")
            ot = hbs(int(Path(file).stat().st_size))
            ans = f"File:\n{file}\nEncoded File Size:\n{ot}"
            await event.answer(ans, show_alert=True)
        elif "cancel" in event.data:
            for proc in psutil.process_iter():
                if proc.name() == "ffmpeg":
                    os.kill(proc.pid, signal.SIGKILL)
    except Exception as er:
        await event.answer("Something Went Wrong 🤔\nResend Media Mwa", show_alert=True)

async def encode(filepath, msg):
    """Encoding function with logo overlay"""
    basefilepath, extension = os.path.splitext(filepath)
    output_filepath = basefilepath + "_R136A1_Encodes.mkv"
    ffmpeg_code = str(ffmpeg[0])

    # Download the logo before encoding
    logo_path = await download_logo()

    # Modify FFmpeg command to include overlay logo
    ffmpeg_cmd = f'ffmpeg -loglevel error -i "{filepath}" -i "{logo_path}" -filter_complex "overlay=main_w-overlay_w-10:main_h-overlay_h-10" {ffmpeg_code} -y "{output_filepath}"'

    try:
        await msg.edit(
            text="Encoding In Progress \n Processing...",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("STATS 🏢", callback_data=f"stats{output_filepath}")],
                    [InlineKeyboardButton("❌ Cancel ❌", callback_data="cancel")]
                ]
            )
        )

        process = await run_subprocess(ffmpeg_cmd)
        LOGGER.info(process)
        return output_filepath
    except Exception as er:
        LOGGER.error(f"Encoding Error: {er}")
        return None

async def get_thumbnail(in_filename):
    """Extracts a thumbnail from the video"""
    out_filename = 'thumb.jpg'
    try:
        code = f'ffmpeg -hide_banner -loglevel error -i "{in_filename}" -map 0:v -ss 00:20 -frames:v 1 "{out_filename}" -y'
        process = await run_subprocess(code)
        return out_filename
    except Exception as er:
        LOGGER.error(f"Thumbnail Extraction Error: {er}")
        return None

async def get_duration(filepath):
    """Gets the duration of a video file"""
    metadata = extractMetadata(createParser(filepath))
    return metadata.get('duration').seconds if metadata and metadata.has("duration") else 0

async def startup():
    """Starts the bot and sends a startup message"""
    await app.start()
    await app.send_message(LOG_CHANNEL, "**Bot Is Back Online! 🛰️**")
    LOGGER.info("The Bot Has Started")
