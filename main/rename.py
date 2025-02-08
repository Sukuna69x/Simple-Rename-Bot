import time
import os
import subprocess
from pyrogram import Client, filters, enums
from config import DOWNLOAD_LOCATION, CAPTION, ADMIN
from main.utils import progress_message, humanbytes

@Client.on_message(filters.private & filters.command("rename") & filters.user(ADMIN))             
async def rename_file(bot, msg):
    reply = msg.reply_to_message
    if len(msg.command) < 2 or not reply:
        return await msg.reply_text("Please Reply To A File or video or audio With filename + .extension eg:-(`.mkv` or `.mp4` or `.zip`)")
    
    media = reply.document or reply.audio or reply.video
    if not media:
        return await msg.reply_text("Please Reply To A File or video or audio With filename + .extension eg:-(`.mkv` or `.mp4` or `.zip`)")
    
    og_media = getattr(reply, reply.media.value)
    new_name = msg.text.split(" ", 1)[1]
    sts = await msg.reply_text("Trying to Downloading.....")
    c_time = time.time()
    
    downloaded = await reply.download(file_name=new_name, progress=progress_message, progress_args=("Download Started.....", sts, c_time)) 
    filesize = humanbytes(og_media.file_size)                
    
    if CAPTION:
        try:
            cap = CAPTION.format(file_name=new_name, file_size=filesize)
        except Exception as e:            
            return await sts.edit(text=f"Your caption Error unexpected keyword ●> ({e})")           
    else:
        cap = f"{new_name}\n\n💽 size : {filesize}"

    # Process the file with FFmpeg to add metadata and watermark
    processed_file = f"{DOWNLOAD_LOCATION}/processed_{new_name}"
    ffmpeg_command = [
        'ffmpeg',
        '-i', downloaded,
        '-metadata:s:v', 'title=Anime Empire',
        '-metadata:s:a', 'title=Anime Empire',
        '-metadata:s:s', 'title=Anime Empire',
        '-vf', "drawtext=fontfile=font.ttf:fontsize=32:fontcolor=white@0.4:x=10:y=10:text='Anime Empire'",
        processed_file
    ]
    
    try:
        subprocess.run(ffmpeg_command, check=True)
    except subprocess.CalledProcessError as e:
        return await sts.edit(f"FFmpeg Error: {e}")

    # Check for thumbnail
    dir = os.listdir(DOWNLOAD_LOCATION)
    if len(dir) == 0:
        file_thumb = await bot.download_media(og_media.thumbs[0].file_id)
        og_thumbnail = file_thumb
    else:
        try:
            og_thumbnail = f"{DOWNLOAD_LOCATION}/thumbnail.jpg"
        except Exception as e:
            print(e)        
            og_thumbnail = None
        
    await sts.edit("Trying to Uploading")
    c_time = time.time()
    try:
        await bot.send_document(msg.chat.id, document=processed_file, thumb=og_thumbnail, caption=cap, progress=progress_message, progress_args=("Upload Started.....", sts, c_time))        
    except Exception as e:  
        return await sts.edit(f"Error {e}")                       
    
    try:
        if file_thumb:
            os.remove(file_thumb)
        os.remove(downloaded)      
        os.remove(processed_file)  # Remove the processed file after sending
    except:
        pass
    
    await sts.delete()
