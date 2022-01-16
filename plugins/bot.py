import logging
import re
from pyrogram.errors import MessageNotModified, UnknownError
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('log.txt'), logging.StreamHandler()],
    level=logging.INFO)
LOGGER = logging.getLogger(__name__)
import os
import time
import subprocess
import asyncio
import shutil
import time
from natsort import natsorted
from config import Config
from pyrogram import Client, filters
from helper_func.exceptions import NotSupportedExtractionArchive
from helper_func.progress import TimeFormatter, progress_for_pyrogram
from pyrogram.errors import FloodWait
from helper_func.get_base_name import get_base_name
from helper_func.auth_user_check import AuthUserCheck
from helper_func.new_filename_gen import new_filename_gen
from helper_func.absolute_paths import absolute_paths
from helper_func.progress import humanbytes
from helper_func.force_sub import ForceSub

@Client.on_message(filters.command(Config.UNZIP_COMMAND))
async def unarchiver(client, message):
    if await AuthUserCheck(message.chat.id, message.from_user.id):
        # force subscribe +
        FSub = await ForceSub(client, message)
        if FSub == 400:
            return
        # force subscribe -
        if message.reply_to_message is not None:
            try:
                filenameformessage = message.reply_to_message.document.file_name
            except:
                await message.reply_text("Send and read (x345): /" + Config.HELP_COMMANDS[0], reply_to_message_id = message.message_id)
                return
            sizeformessage = message.reply_to_message.document.file_size
            if message.reply_to_message.media and filenameformessage.endswith(tuple(Config.EXTENSIONS)):
                chat_id = message.chat.id
                download_folder_for_each_user = Config.DOWNLOAD_DIR + '/' + str(message.from_user.id)
                dl_full_file_path = download_folder_for_each_user + '/' + message.reply_to_message.document.file_name
                if Config.ONE_PROCESS_PER_USER:
                    if os.path.isdir(download_folder_for_each_user):
                        await message.reply_text(Config.ONE_PROCESS_PER_USER_STR, reply_to_message_id = message.message_id)
                        return
                if not os.path.isdir(download_folder_for_each_user):
                    try:
                        os.mkdir(download_folder_for_each_user)
                        LOGGER.info("download_folder_for_each_user not found. created: " + download_folder_for_each_user)
                    except OSError as exc:
                        pass
                dl_full_file_path = await new_filename_gen(dl_full_file_path) # gen new filename if exist
                c_time = time.time()
                password = None
                if " " in message.text:
                    password = message.text.split(" ", 1)
                text = None
                if password is not None:
                    LOGGER.info("command: " + password[0] + " password: " + password[1] + " for user: " + str(message.from_user.id))
                    text = "Downloading with password: `" + password[1] + "`\nPlease wait.\n" 
                else:
                    LOGGER.info("no password.")
                    text = "Downloading without password. Please wait."
                #
                downloadingmessage = await message.reply_text(
                    text=text,
                    parse_mode = 'markdown',
                    disable_notification=True,
                    reply_to_message_id = message.message_id,
                )
                islocked = None
                abc = dl_full_file_path
                path, onlyfilename = os.path.split(abc)
                LOGGER.info("File size: " + str(sizeformessage))
                LOGGER.info("Ignoring file size: " + str(Config.SHOW_PROGRESS_MIN_SIZE_DOWNLOAD))
                if sizeformessage > Config.SHOW_PROGRESS_MIN_SIZE_DOWNLOAD:
                    try:
                        LOGGER.info("document size was bigger than config. showing process.")
                        if password is not None:
                            islocked = "🔒"
                        else:
                            islocked = "🔓"
                        download_location = await client.download_media(
                            message=message.reply_to_message,
                            file_name=dl_full_file_path,
                            progress=progress_for_pyrogram,
                            progress_args=(
                                Config.DOWNLOADING_STR.format(str(filenameformessage),
                                humanbytes(sizeformessage),
                                islocked
                                ),
                            downloadingmessage,
                            c_time
                            )
                        )
                    except UnknownError as e:
                        await message.reply_text("Download Failed.\nerror code 148:\n\n" + e.x, reply_to_message_id = message.message_id)
                        ############
                        if Config.ONE_PROCESS_PER_USER:
                            try:
                                shutil.rmtree(path) # delete folder for user
                            except:
                                pass
                            try:
                                os.rmdir(path)
                            except:
                                pass
                        else:
                            os.remove(dl_full_file_path)
                        return
                    except:
                        await message.reply_text("Download Failed.\nerror code: x100", reply_to_message_id = message.message_id)
                        ############
                        if Config.ONE_PROCESS_PER_USER:
                            try:
                                shutil.rmtree(path) # delete folder for user
                            except:
                                pass
                            try:
                                os.rmdir(path)
                            except:
                                pass
                        else:
                            os.remove(dl_full_file_path)
                        ##############
                        return
                else:
                    try:
                        LOGGER.info("document size was smaller than config. no need to showing process.")
                        download_location = await client.download_media(
                            message=message.reply_to_message,
                            file_name=dl_full_file_path,
                        )
                    ##################
                    except UnknownError as e:
                        await message.reply_text("Download Failed.\nerror code 148:\n\n" + e.x, reply_to_message_id = message.message_id)
                        ############
                        if Config.ONE_PROCESS_PER_USER:
                            try:
                                shutil.rmtree(path) # delete folder for user
                            except:
                                pass
                            try:
                                os.rmdir(path)
                            except:
                                pass
                        else:
                            os.remove(dl_full_file_path)
                        return
                    ##########################
                    except:
                        await message.reply_text("Download Failed.\nerror code: x101", reply_to_message_id = message.message_id)
                        ############
                        if Config.ONE_PROCESS_PER_USER:
                            try:
                                shutil.rmtree(path) # delete folder for user
                            except:
                                pass
                            try:
                                os.rmdir(path)
                            except:
                                pass
                        else:
                            os.remove(dl_full_file_path)
                        ##############
                        return
                if download_location is None:
                    try:
                        await client.edit_message_text(
                            text='Download Failed.\nerror code: x102',
                            chat_id=chat_id,
                            message_id=downloadingmessage.message_id
                        )
                        ############
                        if Config.ONE_PROCESS_PER_USER:
                            try:
                                shutil.rmtree(path) # delete folder for user
                            except:
                                pass
                            try:
                                os.rmdir(path)
                            except:
                                pass
                        else:
                            os.remove(dl_full_file_path)
                        ##############
                        return
                    except MessageNotModified:
                        pass
                    except FloodWait as f_e:
                        time.sleep(f_e.x)
                    return
                try:
                    await client.edit_message_text(
                        text=Config.DOWNLOAD_SUCCESS.format(TimeFormatter((time.time() - c_time)*1000)),
                        chat_id=chat_id,
                        message_id=downloadingmessage.message_id
                    )
                except MessageNotModified:
                    pass
                except FloodWait as f_e:
                    time.sleep(f_e.x)
                LOGGER.info(f"\ndownload_location: " + download_location)
                LOGGER.info(f"\ndownload_folder_for_each_user: " + dl_full_file_path)
                tg_filename = os.path.basename(download_location)
                LOGGER.info("\ntg_filename: " + tg_filename)
                #
                ext = message.reply_to_message.document.file_name.split('.').pop()
                LOGGER.info("\next: " + ext)
                
                LOGGER.info("\nonlyfilename: " + onlyfilename)
                LOGGER.info("\npath: " + path)
                #
                try:
                    # path = await get_base_name(onlyfilename)
                    LOGGER.info(f"Extracting: {onlyfilename}")
                    if password is not None:
                        LOGGER.info("dl_full_file_path: " + dl_full_file_path)
                        LOGGER.info("path: " + path)
                        toexec = "cd \"" + path + "\" && pextract \"" + onlyfilename  + "\" " + password[1]
                        archive_result = process = subprocess.Popen(
                            toexec, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                        stdout, stderr = process.communicate()
                        reply = ''
                        stderr = stderr.decode()
                        stdout = stdout.decode()
                        if stdout:
                            reply += f"Stdout:\n`{stdout}`\n"
                            LOGGER.info(f"Shell - {toexec} - {stdout}")
                        if stderr:
                            reply += f"Stderr:\n`{stderr}`\n"
                        LOGGER.error(f"Shell - {toexec} - {stderr}")
                        #archive_result = subprocess.run([ toexec , dl_full_file_path, str(password)])
                    else:
                        LOGGER.info("dl_full_file_path: " + dl_full_file_path)
                        LOGGER.info("path: " + path)
                        toexec = "cd \"" + path + "\" && nextract \"" + onlyfilename + "\""
                        archive_result = process = subprocess.Popen(
                            toexec, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                        stdout, stderr = process.communicate()
                        reply = ''
                        stderr = stderr.decode()
                        stdout = stdout.decode()
                        if stdout:
                            reply += f"Stdout:\n`{stdout}`\n"
                            LOGGER.info(f"Shell - {toexec} - {stdout}")
                        if stderr:
                            reply += f"Stderr:\n`{stderr}`\n"
                        LOGGER.error(f"Shell - {toexec} - {stderr}")
                        # archive_result = subprocess.run([toexec, dl_full_file_path])
                    deleteiferrors = None
                    if archive_result.returncode == 0:
                        toup = await get_base_name(dl_full_file_path)
                        deleteiferrors = toup
                        LOGGER.info("extracted folder (to upload): " + toup)
                        # dosyayı sil.
                        os.remove(dl_full_file_path)
                        # sahte dosya oluştur. yeni gelen dosyalar için.
                        shutil.copyfile("dontdeletethis.txt", dl_full_file_path)
                        LOGGER.info(f"Deleted archive: {onlyfilename} full path: {dl_full_file_path}")
                    else:
                        LOGGER.warning('Unable to extract archive!') # burda hata verip çıkar.
                        await client.edit_message_text(
                            text="❌\n\nAn error occurred while extracting the archive. Probably the password was entered incorrectly.",
                            chat_id=chat_id,
                            message_id=downloadingmessage.message_id)
                        if deleteiferrors is not None:
                            try:
                                os.remove(dl_full_file_path)
                            except:
                                pass
                            try:
                                shutil.rmtree(deleteiferrors) # delete folder for user for download
                            except:
                                pass
                            try:
                                os.rmdir(deleteiferrors)
                            except:
                                pass
                            deleteiferrors = None
                        return
                        #path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
                    LOGGER.info(f'got path: {path}')
                except NotSupportedExtractionArchive:
                    LOGGER.info("Not any valid archive.")
                    await message.reply_text("❌\n\nNot any valid archive.", reply_to_message_id = message.message_id)
                    return
                ####################################################3
                start = time.time()
                if archive_result.returncode == 0:
                    extracted_files = [i async for i in absolute_paths(toup)]
                    # sorting +
                    if Config.SORT_FILES_BEFORE_SEND:
                        if Config.USE_NATSORT:
                            extracted_files = natsorted(extracted_files)
                        else:
                            extracted_files = extracted_files.sort()
                    # sorting -
                    filescount = len(extracted_files)
                    fileatnow = 0
                    successcount = 0
                    unsuccesscount = 0
                    c_time = time.time() # hata verirse alttaki
                    for file in extracted_files:
                        # c_time = time.time()
                        finame = file
                        finame = finame.strip()
                        finame = re.sub(r'(usr\/src\/app\/downloads\/)\w+','', finame)
                        finame = finame.strip()
                        finame = finame.lstrip('/')
                        #### check thumb in every file 
                        thumb = None
                        thumbnail_location = os.path.join(Config.DOWNLOAD_DIR, "thumbnails", str(message.from_user.id) + ".jpg")
                        if os.path.isfile(thumbnail_location):
                            thumb = thumbnail_location
                        ####
                        try:
                            LOGGER.info("force_document was: " + str(Config.FORCE_DOC_UPLOAD))
                            try:
                                fileatnow += 1
                                await client.send_document(
                                    chat_id = message.chat.id,
                                    document = file,
                                    caption = f"`{finame}`",
                                    thumb = thumb,
                                    disable_notification=True,
                                    parse_mode = 'markdown',
                                    force_document = Config.FORCE_DOC_UPLOAD,
                                    reply_to_message_id = downloadingmessage.message_id,
                                    progress = progress_for_pyrogram,
                                    progress_args=(
                                        Config.UPLOADING_STR.format(
                                            filenameformessage,
                                            humanbytes(sizeformessage),
                                            islocked,
                                            finame,
                                            humanbytes(os.path.getsize(file)),
                                            str(fileatnow) + ' / ' + str(filescount)
                                        ),
                                        downloadingmessage,
                                        c_time
                                    )
                                )
                                successcount += 1
                            except FloodWait as e:
                                print(f"Sleep of {e.x}s caused by FloodWait")
                                await asyncio.sleep(e.x)
                                # bekle ve tekrar gönder
                                await client.send_document(
                                    chat_id = message.chat.id,
                                    document = file,
                                    caption = f"`{finame}`",
                                    thumb = thumb,
                                    disable_notification=True,
                                    parse_mode = 'markdown',
                                    force_document = Config.FORCE_DOC_UPLOAD,
                                    reply_to_message_id = downloadingmessage.message_id,
                                    progress = progress_for_pyrogram,
                                    progress_args=(
                                        Config.UPLOADING_STR.format(
                                            filenameformessage,
                                            humanbytes(sizeformessage),
                                            islocked,
                                            finame,
                                            humanbytes(os.path.getsize(file)),
                                            str(fileatnow) + ' / ' + str(filescount)
                                        ),
                                        downloadingmessage,
                                        c_time
                                    )
                                )
                            except:
                                await message.reply_text("Cannot send:\n\n" + "`" + finame + "`", reply_to_message_id = downloadingmessage.message_id)
                                unsuccesscount += 1
                            time.sleep(Config.SLEEP_TIME_BETWEEN_SEND_FILES) # sleep for speed
                            try:
                                os.remove(file)
                                LOGGER.info("Deleted uploaded file: " + file)
                            except:
                                LOGGER.info("Cannot deleted uploaded file: " + file)
                                pass
                        except FloodWait as e:
                            time.sleep(e.x)
                            LOGGER.info("Sleeping for floodwait: " + str(e.x))
                    text = Config.UPLOAD_SUCCESS.format(
                        TimeFormatter((time.time() - start)*1000),
                        filenameformessage,
                        humanbytes(sizeformessage),
                        message.reply_to_message.link,
                        str(successcount) + ' / ' + str(filescount),
                        str(unsuccesscount) + ' / ' + str(filescount)
                    )
                    await client.edit_message_text(
                        text=text,
                        chat_id=chat_id,
                        parse_mode = 'markdown',
                        message_id = downloadingmessage.message_id)
                    await message.reply_text(
                        text = text,
                        reply_to_message_id = downloadingmessage.message_id,
                        parse_mode = 'markdown'
                    )
                try:
                    os.remove(dl_full_file_path)
                except:
                    pass
                try:
                    shutil.rmtree(toup) # delete folder for user for download
                except:
                    pass
                try:
                    os.rmdir(toup)
                except:
                    pass
                ############
                if Config.ONE_PROCESS_PER_USER:
                    try:
                        shutil.rmtree(path) # delete folder for user
                    except:
                        pass
                    try:
                        os.rmdir(path)
                    except:
                        pass
                ##############
            else:
                await message.reply_text("Send and read (x225): /" + Config.HELP_COMMANDS[0], reply_to_message_id = message.message_id)
        else:
            await message.reply_text("Send and read (x230): /" + Config.HELP_COMMANDS[0], reply_to_message_id = message.message_id)
    else:
        await message.reply_text(Config.UNAUTHORIZED_TEXT_STR, reply_to_message_id = message.message_id)

