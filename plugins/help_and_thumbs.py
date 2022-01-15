import os
from config import Config
from pyrogram import Client, filters
from helper_func.auth_user_check import AuthUserCheck
from helper_func.force_sub import ForceSub
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image

@Client.on_message(filters.command(Config.HELP_COMMANDS))
async def start(bot, update):
    if await AuthUserCheck(update.chat.id, update.from_user.id):
        # force subscribe +
        FSub = await ForceSub(bot, update)
        if FSub == 400:
            return
        # force subscribe -
        await update.reply_text(Config.START_TEXT_STR, reply_to_message_id = update.message_id)
    else:
        await update.reply_text(Config.UNAUTHORIZED_TEXT_STR, reply_to_message_id = update.message_id)

@Client.on_message(filters.command(Config.SAVE_THUMB_COMMAND))
async def save_thumb(client, message):
    if await AuthUserCheck(message.chat.id, message.from_user.id):
        # force subscribe +
        FSub = await ForceSub(client, message)
        if FSub == 400:
            return
        # force subscribe -
        thumbnail_location = os.path.join(Config.DOWNLOAD_DIR, "thumbnails")
        thumb_image_path = os.path.join(
            thumbnail_location, str(message.from_user.id) + ".jpg"
        )
        if message.reply_to_message is not None:
            try:
                if not os.path.isdir(thumbnail_location):
                    os.makedirs(thumbnail_location)
                download_location = thumbnail_location + "/"
                downloaded_file_name = await client.download_media(
                    message=message.reply_to_message, file_name=download_location
                )
                Image.open(downloaded_file_name).convert("RGB").save(downloaded_file_name)
                metadata = extractMetadata(createParser(downloaded_file_name))
                height = 0
                if metadata.has("height"):
                    height = metadata.get("height")
                img = Image.open(downloaded_file_name)
                img.resize((320, height))
                img.save(thumb_image_path, "JPEG")
                os.remove(downloaded_file_name)
                await message.reply_text(f"✅\n\n🇬🇧 Custom thumbnail saved.\nThis image will be used in the upload.",
                    f" Clear: /{Config.CLEAR_THUMB_COMMAND[0]}",
                    reply_to_message_id = message.message_id)
            except:
                await message.reply_text("❌\n\n🇬🇧 Reply to a photo with this command to save custom thumbnail",
                    reply_to_message_id = message.message_id)
        else:
            await message.reply_text("❌\n\n🇬🇧 Reply to a photo with this command to save custom thumbnail\n" + ",
                reply_to_message_id = message.message_id)

@Client.on_message(filters.command(Config.CLEAR_THUMB_COMMAND))
async def clear_thumb(client, message):
    if await AuthUserCheck(message.chat.id, message.from_user.id):
        # force subscribe +
        FSub = await ForceSub(client, message)
        if FSub == 400:
            return
        # force subscribe -
        thumbnail_location = os.path.join(Config.DOWNLOAD_DIR, "thumbnails")
        thumb_image_path = os.path.join(
            thumbnail_location, str(message.from_user.id) + ".jpg"
        )
        if os.path.exists(thumb_image_path):
            os.remove(thumb_image_path)
            await message.reply_text("✅\n\n Custom thumbnail cleared successfully.",
                    reply_to_message_id = message.message_id)
        else:
            await message.reply_text("❌\n\n Nothing to clear.",
                    reply_to_message_id = message.message_id)

@Client.on_message(filters.command(Config.SHOW_THUMB_COMMAND))
async def show_thumb(client, message):
    if await AuthUserCheck(message.chat.id, message.from_user.id):
        # force subscribe +
        FSub = await ForceSub(client, message)
        if FSub == 400:
            return
        # force subscribe -
        thumbnail_location = os.path.join(Config.DOWNLOAD_DIR, "thumbnails")
        thumb_image_path = os.path.join(
            thumbnail_location, str(message.from_user.id) + ".jpg"
        )
        if os.path.exists(thumb_image_path):
            await message.reply_photo(thumb_image_path,
            caption = "Here is your curent thumbnail.",
                    reply_to_message_id = message.message_id,
            ttl_seconds = 10
            )
            
        else:
            await message.reply_text(f"🇬🇧 You have not set a thumbnail. Send /{Config.HELP_COMMANDS[0]} and read.\n" + \
            f"🇹🇷 Küçük resim ayarlamamışsın ki? /{Config.HELP_COMMANDS[0]} yazıp oku.",
                    reply_to_message_id = message.message_id)
