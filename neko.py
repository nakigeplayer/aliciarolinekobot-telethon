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

# Obtener la palabra secreta de la variable de entorno
CODEWORD = os.getenv("CODEWORD")

@client.on(events.NewMessage(pattern='/access (.+)'))
async def handler(event):
    user_id = event.sender_id
    
    # Obtener la palabra secreta del mensaje
    message_codeword = event.pattern_match.group(1)
    
    if message_codeword == CODEWORD:
        # Añadir el ID del usuario a la lista temp_users si no está ya añadido
        if user_id not in temp_users:
            temp_users.append(user_id)
            allowed_users.append(user_id)  # Añadir también a allowed_users
            await event.reply("Acceso concedido.")
        else:
            await event.reply("Ya estás en la lista de acceso temporal.")
    else:
        await event.reply("Palabra secreta incorrecta.")

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
from telethon import TelegramClient, events
import os


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




@client.on(events.NewMessage(pattern=r'[/.]?start'))
async def start(event):
    sender = await event.get_sender()
    username = sender.id

    if event.chat_id not in allowed_users:
        return
    await event.respond('Funcionando')

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
                link = upload_token(filename,  os.getenv('NUBETOKEN'), os.getenv('NUBELINK'))
                await event.respond(link)
                #await event.respond("Enlace:\n\n"+link)
            except Exception as ex:
                await event.respond(ex)
            finally:
                os.remove(filename)
                
                  
    
client.start()
client.run_until_disconnected()


