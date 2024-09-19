from telethon import TelegramClient, events
import requests
from bs4 import BeautifulSoup
import re
import os
import shutil
import zipfile
import py7zr
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase 
from email import encoders
from moodleclient import upload_token

# Configura tu API ID y Hash aquí

api_id = os.getenv('API_ID')
api_hash =  os.getenv('API_HASH')
bot_token =  os.getenv('TOKEN')

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

print("El bot se ha iniciado, para detenerlo pulse CTRL+C")


# Define the admin and temporary users
admin_users = list(map(int, os.getenv('ADMINS').split(',')))
users = list(map(int, os.getenv('USERS').split(',')))
temp_users = []
temp_chats = []

# Combine admin_users and temp_users into allowed_users
allowed_users = admin_users + users + temp_users + temp_chats

@client.on(events.NewMessage(pattern=r'[/.]?adduser ?(.*)'))
async def add_user(event):
    sender = await event.get_sender()
    user_id = sender.id

    user_id_to_add = int(event.pattern_match.group(1))
    if user_id not in admin_users:
        await event.reply('No eres admin')
        return

    if user_id_to_add not in temp_users:
        temp_users.append(user_id_to_add)
        temp_users.extend([user_id_to_add])
        await event.reply(f'User {user_id_to_add} added to temp_users.')
    else:
        await event.reply(f'User {user_id_to_add} is already in temp_users.')

@client.on(events.NewMessage(pattern=r'[/.]?remuser ?(.*)'))
async def remove_user(event):
    sender = await event.get_sender()
    user_id = sender.id

    user_id_to_remove = int(event.pattern_match.group(1))
    if user_id not in admin_users:
        await event.reply('No eres admin')
        return

    if user_id_to_remove in temp_users:
        temp_users.remove(user_id_to_remove)
        temp_users.remove(user_id_to_remove)
        await event.reply(f'User {user_id_to_remove} removed from temp_users.')
    else:
        await event.reply(f'User {user_id_to_remove} is not in temp_users.')


@client.on(events.NewMessage(pattern=r'[/.]?addchat'))
async def add_chat(event):
    sender = await event.get_sender()
    user_id = sender.id
    chat_id = event.chat_id

    if user_id not in admin_users:
        await event.reply('No eres admin')
        return

    if chat_id not in temp_chats:
        temp_chats.append(chat_id)
        temp_chats.extend([chat_id])
        await event.reply(f'Chat {chat_id} añadido a temp_chats.')
    else:
        await event.reply(f'Chat {chat_id} ya está en temp_chats.')

@client.on(events.NewMessage(pattern=r'[/.]?remchat'))
async def rem_chat(event):
    sender = await event.get_sender()
    user_id = sender.id
    chat_id = event.chat_id

    if user_id not in admin_users:
        await event.reply('No eres admin')
        return

    if chat_id in allowed_chats:
        temp_chats.remove(chat_id)
        await event.reply(f'Chat {chat_id} eliminado de temp_chats.')
    else:
        await event.reply(f'Chat {chat_id} no está en temp_chats')

@client.on(events.NewMessage(pattern=r'[/.]?addreplied'))
async def add_user(event):
    sender = await event.get_sender()
    user_id = sender.id

    if not event.is_reply:
        await event.reply('Por favor, responde a un mensaje para usar este comando.')
        return

    replied_message = await event.get_reply_message()
    user_id_to_add = replied_message.sender_id

    if user_id not in admin_users:
        await event.reply('No eres admin')
        return

    if user_id_to_add not in temp_users:
        temp_users.append(user_id_to_add)
        allowed_users.extend([user_id_to_add])
        await event.reply(f'User {user_id_to_add} added to temp_users.')
    else:
        await event.reply(f'User {user_id_to_add} is already in temp_users.')

@client.on(events.NewMessage(pattern=r'[/.]?remreplied'))
async def rem_user(event):
    sender = await event.get_sender()
    user_id = sender.id

    if not event.is_reply:
        await event.reply('Por favor, responde a un mensaje para usar este comando.')
        return

    replied_message = await event.get_reply_message()
    user_id_to_remove = replied_message.sender_id

    if user_id not in admin_users:
        await event.reply('No eres admin')
        return

    if user_id_to_remove in temp_users:
        temp_users.remove(user_id_to_remove)
        allowed_users.remove(user_id_to_remove)
        await event.reply(f'User {user_id_to_remove} removed from temp_users.')
    else:
        await event.reply(f'User {user_id_to_remove} is not in temp_users.')



@client.on(events.NewMessage(pattern=r'[/.]?start'))
async def start(event):
    sender = await event.get_sender()
    username = sender.id

    if event.chat_id not in allowed_users:
        return
    await event.respond('Funcionando')





command_rename = False

@client.on(events.NewMessage(pattern=r'[/.]?rename (.+)'))
async def rename(event):
    global command_rename

    sender = await event.get_sender()
    username = sender.id

    if event.chat_id not in allowed_users:
        return

    if command_rename:
        await event.respond("El comando está en uso actualmente, espere un poco")
        return

    command_rename = False

    if event.is_reply:
        reply_message = await event.get_reply_message()
        if reply_message.media:
            try:
                await event.respond("Descargando el archivo para renombrarlo...")
                new_name = event.pattern_match.group(1)
                file_path = await client.download_media(reply_message.media)
                new_file_path = os.path.join(os.path.dirname(file_path), new_name)
                os.rename(file_path, new_file_path)
                await event.respond("Subiendo el archivo con nuevo nombre...")
                await client.send_file(event.chat_id, new_file_path, force_document=True)
                os.remove(new_file_path)
            except Exception as e:
                await event.respond(f'Error: {str(e)}')
        else:
            await event.respond('Ejecute el comando respondiendo a un archivo')
    else:
        await event.respond('Ejecute el comando respondiendo a un archivo')

    command_rename = False













compress_in_progress = False

user_comp = {}

@client.on(events.NewMessage(pattern=r'[/.]?setsize (.+)'))
async def set_comp(event):
    sender = await event.get_sender()
    username = sender.id
    valor = event.pattern_match.group(1)
    
    user_comp[username] = int(valor)
    await event.reply(f"Tamaño de archivos {valor} MB registrado para el usuario {username}")

def compressfile(filename, sizd):
    maxsize = 1024 * 1024 * sizd
    mult_file =  zipfile.MultiFile(filename+'.7z', maxsize)
    zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
    zip.write(filename)
    zip.close()
    mult_file.close()
    files = []
    for part in zipfile.files:
        files.append(part)
    return files

import os
import shutil

# Define la carpeta que deseas limpiar
download_folder = 'descargas'

def clear_folder(folder):
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(e)







@client.on(events.NewMessage(pattern=r'[/.]?compress'))
async def compress(event):
    global compress_in_progress
    sender = await event.get_sender()
    username = sender.id

    if event.chat_id not in allowed_users:
        return

    if compress_in_progress:
        await event.respond("El comando está en uso actualmente, espere un poco")
        return

    if event.is_reply:
        reply_message = await event.get_reply_message()
        if reply_message.media:
            try:
                compress_in_progress = True
                os.system("rm -rf ./server/*")
                await event.respond("Descargando el archivo para comprimirlo...")

                # Crear carpeta temporal
                #temp_dir = "server/tempcompress"
                #os.makedirs(temp_dir, exist_ok=True)
                #temp_test_dir = os.path.join(temp_dir, "test")
                #os.makedirs(temp_test_dir, exist_ok=True)

                # Descargar archivo
                file_path = await client.download_media(reply_message.media, file="server")
                #file_path = reply_message.file.name
                #with open(file_path, "wb") as out:
                #    await download_file(event.client, reply_message.media, out)

                # Comprimir archivo
                #compressed_file = os.path.join(temp_test_dir, os.path.basename(file_path) + '.7z')

                await event.respond("Comprimiendo el archivo...")

                try:
                    sizd = user_comp[username]
                except:
                    sizd = 10
                
                # Comprimir archivo
                #with py7zr.SevenZipFile(compressed_file, 'w') as archive:
                #    archive.write(file_path, os.path.basename(file_path))

                # Dividir archivo comprimido
                #parts = split_file(compressed_file, sizd * 1024 * 1024)
                parts = compressfile(file_path, sizd)
                await event.respond(f"Se ha comprimido el archivo, ahora se enviarán las partes")
                

                # Enviar partes
                for part in parts:
                    try:
                        await client.send_file(event.chat_id, part)
                        #with open(part, "rb") as out:
                        #    await upload_file(client, out)
                    except:pass

                await event.respond("Esas son todas las partes")
                shutil.rmtree('server')
                os.mkdir('server')
                # Limpiar archivos temporales
                '''
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        os.remove(os.path.join(root, file))
                for root, dirs in os.walk(temp_dir):
                    if dirs:
                        os.rmdir(root)
                '''

                compress_in_progress = False
            except Exception as e:
                await event.respond(f'Error: {str(e)}')
            finally:
                compress_in_progress = False
        else:
            await event.respond('Ejecute el comando respondiendo a un archivo')
    else:
        await event.respond('Ejecute el comando respondiendo a un archivo')

def split_file(file_path, part_size):
    parts = []
    with open(file_path, 'rb') as f:
        part_num = 1
        while True:
            part_data = f.read(part_size)
            if not part_data:
                break
            part_file = f"{file_path}.part{part_num}"
            with open(part_file, 'wb') as part:
                part.write(part_data)
            parts.append(part_file)
            part_num += 1
    return parts       













@client.on(events.NewMessage(pattern=r'[/.]?up'))
async def upmoodle(event):

    sender = await event.get_sender()
    username = sender.id
    if username not in allowed_users:
        return
    if event.is_reply:
        reply_message = await event.get_reply_message()
        if reply_message.media:
            try:
                await event.respond("Descargando el archivo para subir a moodle...")
                filename = await client.download_media(reply_message.media)
                await event.respond("Subiendo el archivo...")
                link = upload_token(filename,  os.getenv('NUBETOKEN'), "https://cursad.jovenclub.cu")
                await event.respond("Enlace:\n\n"+link)
            except Exception as ex:
                await event.respond(ex)

def split_file(file_path, part_size):
    parts = []
    with open(file_path, 'rb') as f:
        part_num = 0
        while True:
            part_data = f.read(part_size)
            if not part_data:
                break
            part_file = f"{file_path}.part{part_num}"
            with open(part_file, 'wb') as part_f:
                part_f.write(part_data)
            parts.append(part_file)
            part_num += 1
    return parts







h3_in_use = False

def clean_string(input_string):
    return ''.join(char for char in input_string if char.isalnum() or char in '[]')


@client.on(events.NewMessage(pattern=r'[/.]?h3dl ?(.*)'))
async def download_images(event):
    global h3_in_use
    if h3_in_use:
        await event.reply("El comando está en uso actualmente, espere un poco")
        return

    h3_in_use = True
    sender = await event.get_sender()
    username = sender.id
    codes = event.pattern_match.group(1).split('π')

    if not codes:
        await event.reply("No puedes enviar el comando vacío")
        h3_in_use = False
        return

    total_codes = len(codes)
    for index, code in enumerate(codes, start=1):
        code = clean_string(code.strip())
        url = f"https://es.3hentai.net/d/{code}"

        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            await event.reply(f"Error al acceder a la página: {str(e)}")
            h3_in_use = False
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        page_title = soup.title.string if soup.title else "sin_titulo"
        folder_name = os.path.join("h3dl", clean_string(re.sub(r'[\\/*?:"<>|]', "", page_title)))

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        image_links = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and src.endswith('t.jpg'):
                image_links.append(src.replace('t.jpg', '.jpg'))

        for link in image_links:
            try:
                img_data = requests.get(link).content
                img_name = os.path.join(folder_name, os.path.basename(link))
                with open(img_name, 'wb') as handler:
                    handler.write(img_data)
            except Exception as e:
                await event.reply(f"Error al descargar el archivo {link}: {str(e)}")
                h3_in_use = False
                return

        await event.reply(f"Descargando {code} (Progreso {index}/{total_codes})")

        zip_filename = os.path.join(f"{folder_name}.cbz")
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for root, _, files in os.walk(folder_name):
                for file in files:
                    zipf.write(os.path.join(root, file), arcname=file)

        await client.send_file(event.chat_id, zip_filename)
        await event.reply(f"Archivo {code} descargado, enviando...")

    await event.reply("Todos los archivos CBZ han sido enviados correctamente")
    shutil.rmtree('h3dl')
    os.mkdir('h3dl')
    h3_in_use = False
    


    
@client.on(events.NewMessage(pattern=r'[/.]?nh ?(.*)'))
async def download_images(event):
    global h3_in_use
    if h3_in_use:
        await event.reply("El comando está en uso actualmente, espere un poco")
        return

    h3_in_use = True
    sender = await event.get_sender()
    username = sender.id
    codes = event.pattern_match.group(1).split('π')

    if not codes:
        await event.reply("No puedes enviar el comando vacío")
        h3_in_use = False
        return

    total_codes = len(codes)
    for index, code in enumerate(codes, start=1):
        code = clean_string(code.strip())

        # Check the first page to get the name
        url = f"https://nhentai.net/g/{code}/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            await event.reply(f"El código {code} es erróneo: {str(e)}")
            continue

        soup = BeautifulSoup(response.content, 'html.parser')
        title_tag = soup.find('title')
        if title_tag:
            folder_name = os.path.join("h3dl", clean_string(title_tag.text.strip()))
        else:
            folder_name = os.path.join("h3dl", clean_string(code))

        os.makedirs(folder_name, exist_ok=True)

        # Now proceed to download images
        page_number = 1
        images_downloaded = 0

        while True:
            url = f"https://nhentai.net/g/{code}/{page_number}/"
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                if page_number == 1:
                    await event.reply(f"Error al acceder a la página: {str(e)}")
                break

            soup = BeautifulSoup(response.content, 'html.parser')
            img_tag = soup.find('img', {'src': re.compile(r'.*\.(png|jpg|jpeg|gif|bmp|webp)$')})
            if not img_tag:
                break

            img_url = img_tag['src']
            img_extension = os.path.splitext(img_url)[1]
            img_data = requests.get(img_url, headers=headers).content

            img_filename = os.path.join(folder_name, f"{page_number}{img_extension}")
            with open(img_filename, 'wb') as img_file:
                img_file.write(img_data)

            images_downloaded += 1
            page_number += 1

        if images_downloaded == 0:
            await event.reply(f"No se encontraron imágenes para el código {code}")
            continue

        zip_filename = os.path.join(f"{folder_name}.cbz")
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for root, _, files in os.walk(folder_name):
                for file in files:
                    zipf.write(os.path.join(root, file), arcname=file)

        await client.send_file(event.chat_id, zip_filename)
        await event.reply(f"Archivo {code} descargado, enviando...")

    await event.reply("Todos los archivos CBZ han sido enviados correctamente")
    shutil.rmtree('h3dl')
    os.mkdir('h3dl')
    h3_in_use = False

def clean_string(s):
    return re.sub(r'\W+', '_', s)




scan_in_use = False

@client.on(events.NewMessage(pattern=r'[/.]?scan (.*)'))
async def scan(event):
    global scan_in_use
    if scan_in_use:
        await event.reply("El comando está en uso actualmente, espere un poco")
        return

    scan_in_use = True
    sender = await event.get_sender()
    url = event.pattern_match.group(1)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a', href=True)

        results = []
        for link in links:
            href = link['href']
            if not href.endswith(('.pdf', '.jpg', '.png', '.doc', '.docx', '.xls', '.xlsx')):
                page_name = link.get_text(strip=True)
                if page_name:
                    results.append(f"<li><a href='{href}'>{page_name}</a></li>")

        if results:
            html_content = f"<html><body><ul>{''.join(results)}</ul></body></html>"
            with open('results.html', 'w') as f:
                f.write(html_content)
            await event.reply(file='results.html')
            os.remove('results.html')
        else:
            await event.reply("No se encontraron enlaces de páginas web.")

    except Exception as e:
        await event.reply(f"Error al escanear la página: {e}")

    scan_in_use = False










# Variables de configuración del servidor SMTP
DISMAIL =  os.getenv('DISMAIL')
DISPASS =  os.getenv('DISPASS')

emails = {}

@client.on(events.NewMessage(pattern=r'[/.]?setmail (.+)'))
async def set_mail(event):
    sender = await event.get_sender()
    sender_id = sender.id
    chat_id = event.chat_id

    if chat_id not in allowed_users:
        return
    email = event.pattern_match.group(1)
    emails[sender_id] = email
    await event.respond(f'El correo "{email}" ha sido registrado para el usuario {sender_id} en el chat {chat_id}')

@client.on(events.NewMessage(pattern=r'[/.]?sendmail'))
async def send_mail(event):
    if event.chat_id not in allowed_users:
        return
    if event.sender_id not in emails:
        await event.respond('Use /setmail para establecer su correo')
        return
    if not event.is_reply:
        await event.respond('Debe responder a un mensaje')
        return

    reply_message = await event.get_reply_message()
    media = await reply_message.download_media() if reply_message.media else None

    if media and os.path.getsize(media) > 40 * 1024 * 1024:
        await event.respond('El adjunto no puede superar los 40MB')
        os.remove(media)
        return

    await event.respond('Descargando archivo para adjunto')

    # Crear el mensaje de correo
    msg = MIMEMultipart()
    msg['From'] = f'Neko bot <{DISMAIL}>'
    msg['To'] = emails[event.sender_id]
    msg['Subject'] = 'Enviado con desde Telegram'
    msg.attach(MIMEText(reply_message.text or 'Sin texto', 'plain'))

    if media:
        with open(media, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(media)}')
            msg.attach(part)

    try:
        with smtplib.SMTP('disroot.org', 587) as server:
            server.starttls()
            server.login(DISMAIL, DISPASS)
            server.sendmail(DISMAIL, emails[event.sender_id], msg.as_string())
        await event.respond('Correo electrónico enviado correctamente')
    except Exception as e:
        await event.respond(f'Error al enviar el correo: {e}')
    finally:
        if media:
            os.remove(media)
            
                  
    
client.start()
client.run_until_disconnected()

    
