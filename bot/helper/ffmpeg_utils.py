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
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    return await process.communicate()

@app.on_callback_query()
async def stats(_, event):
    try:
     if "stats" in event.data:
      data_s = event.data
      file = data_s.replace("stats", "")
      ot = hbs(int(Path(file).stat().st_size))
      ans = f"File:\n{file}\nEncoded File Size:\n{ot}"
      await event.answer(ans, show_alert=True)
     elif "cancel" in event.data:
      for proc in psutil.process_iter():
          processName = proc.name()
          processID = proc.pid
          if processName == "ffmpeg":
             os.kill(processID, signal.SIGKILL)
     elif "HEVC" in event.data:
      codec_code = str(ffmpeg[0])
      codec_code.replace("-c:v libx265", "-c:v libx264")
      await event.answer("Changed To AVC", show_alert=True)
      ffmpeg.insert(0, codec_code)
     elif "AVC" in event.data:
      codec_code = str(ffmpeg[0])
      codec_code.replace("-c:v libx264", "-c:v libx265")
      await event.answer("Changed To HEVC", show_alert=True)
      ffmpeg.insert(0, codec_code)
     elif "480p" in event.data:
      res_code = str(ffmpeg[0])
      res_code.replace("-s 854x480", "-s 1280x720")
      await event.answer("Changed To 720p", show_alert=True)
      ffmpeg.insert(0, res_code)
     elif "720p" in event.data:
      res_code = str(ffmpeg[0])
      res_code.replace("-s 1280x720", "-s 854x480")
      await event.answer("Changed To 480p", show_alert=True)
      ffmpeg.insert(0, res_code)   
    except Exception as er:
        await event.answer("Someting Went Wrong 🤔\nResend Media Mwa", show_alert=True)           

async def encode(filepath, msg):
    basefilepath, extension = os.path.splitext(filepath)
    output_filepath = basefilepath + "HcCartoons_Encodes" + ".mkv"
    ffmpeg_code = str(ffmpeg[0])
    nam = filepath.replace("/home/runner/work/Auto-Renamer-Queue/Auto-Renamer-Queue/downloads/", " ")
    nam = nam.replace("_", " ")
    nam = nam.replace(".mkv", " ")
    nam = nam.replace(".mp4", " ")
    nam = nam.replace(".", " ")
    if "/bot/downloads/" in nam:
      nam = nam.replace("/bot/downloads", " ")
    new_name = anitopy.parse(nam)
    anime_name = new_name["anime_title"]
    joined_string = f"[{anime_name}]"
    if "anime_season" in new_name.keys():
      animes_season = new_name["anime_season"]
      joined_string = f"{joined_string}" + f" [Season {animes_season}]"
    if "episode_number" in new_name.keys():
      episode_no = new_name["episode_number"]
      joined_string = f"{joined_string}" + f" [Episode {episode_no}]"
    og = joined_string + " [ HC CARTOONS ]" + ".mkv"
    og = og.replace("/home/runner/work/Encoder/Encoder/downloads/", "")
    try:
     await msg.edit(
        text= "Encoding In Progress \n Processing", 
        reply_markup=InlineKeyboardMarkup(
        [
          [InlineKeyboardButton("STATS ☕️", callback_data=f"stats{og}" )],
          [InlineKeyboardButton("❌ Cancel ❌", callback_data=f"cancel" )],
       ])
     )
     min = await app.send_message(
        chat_id=LOG_CHANNEL,
        text= "Encoding In Progress", 
        reply_markup=InlineKeyboardMarkup(
        [
          [InlineKeyboardButton("STATS ☕️", callback_data=f"stats{og}" )],
       ])
     )
    except Exception as e:
     await msg.edit(
        text= "Encoding In Progress",
        reply_markup=InlineKeyboardMarkup(
        [
           [InlineKeyboardButton("❌ Cancel ❌", callback_data="cancel")],
        ])
      )
     min = await app.send_message(
        chat_id=LOG_CHANNEL,
        text= "Encoding In Progress",
      )
    try:
        ffmpeg_cmd = f'ffmpeg -loglevel error -i "{filepath}" {ffmpeg_code} -y "{og}"'
        process = await run_subprocess(ffmpeg_cmd)
        await min.delete()
        LOGGER.info(process)
        return og
    except Exception as er:
        return LOGGER.info(f"Error {er}")

async def get_thumbnail(in_filename):
    out_filename = 'thumb1.jpg'
    outfile = 'thumb.jpg'
    try:
        code = f'ffmpeg -hide_banner -loglevel error -i "{in_filename}" -map 0:v -ss 00:20 -frames:v 1 "{out_filename}" -y'
        process = await run_subprocess(code)
        return out_filename
    except Exception as er:
        return LOGGER.info(er)
  
async def get_duration(filepath):
    metadata = extractMetadata(createParser(filepath))
    if metadata.has("duration"):
      return metadata.get('duration').seconds
    else:
      return 0

async def get_width_height(filepath):
    metadata = extractMetadata(createParser(filepath))
    if metadata.has("width") and metadata.has("height"):
      return metadata.get("width"), metadata.get("height")
    else:
      return 1280, 720

async def startup():
    await app.start()
    await app.send_message(LOG_CHANNEL, f"**Bot Is Back Online! 🛰️**")
    LOGGER.info("The Bot Has Started")

    
async def sample_gen(app, message):
  if message.reply_to_message:
     vid = message.reply_to_message.id
     dp = await message.reply_to_message.reply_text("Downloading The Video")
     video = await app.download_media(message=message.reply_to_message)
     await dp.edit("Downloading Finished Starting To Generate Sample")
     output_file = video + 'sample_video.mkv'
     await dp.edit("Generating Sample...This May Take Few Moments")
     file_gen_cmd = f'ffmpeg -ss 10:30 -i "{video}" -map 0 -c:v copy -c:a copy -t 30 "{output_file}" -y'
     output = await run_subprocess(file_gen_cmd)   
     LOGGER.info(output)
     duration = await get_duration(output_file)
     thumbnail = await get_thumbnail(video)
  else:
     await message.reply_text('NO FILE DETECTED')
  if os.path.exists(output_file):
     await dp.edit('Uploading The Video')
     chat_id = message.chat.id
     upload = await app.send_video(
        chat_id=message.chat.id,
        video=output_file,
        caption="Sample Generated From 00:30 Of 30 SECONDS",
        supports_streaming=True,
        duration=duration,
        width=1280,
        height=720,
        file_name=output_file,
        thumb=thumbnail,
        reply_to_message_id=vid
     )
     await dp.delete()
     os.remove(video)
     os.remove(output_file)
     os.remove(thumbnail)
  else:
     await dp.edit("Failed To Generate Sample Due To Locked Infrastructure")
     os.remove(video_file)    

async def run(app, message):
  tasty = str(ffmpeg[0])
  if "-c:v libx265" in tasty:
   video_codec = "HEVC"
  else:
   video_codec = "AVC"
  if "-s 854x480" in tasty:
   res = "480p"
  else:
   res = "720p"
  await app.send_message(
    chat_id=message.chat.id, 
    text="**Settings -:**",
    reply_markup=InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(f"CODEC {video_codec}", callback_data=f"{video_codec}")],
            [InlineKeyboardButton(f"RESOLUTION {res}", callback_data=f"{res}")]
        ]))
