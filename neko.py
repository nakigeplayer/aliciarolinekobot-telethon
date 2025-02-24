from telethon import TelegramClient, events
import os
import smtplib
from email.message import EmailMessage
import shutil

# Suponiendo que user_emails es un diccionario que contiene los correos de los usuarios
user_emails = {}

async def send_mail(event):
    user_id = event.sender_id
    if user_id not in user_emails:
        await event.reply("No has registrado ningún correo, usa /setmail para hacerlo.")
        return
    
    email = user_emails[user_id]
    msg = EmailMessage()
    msg['Subject'] = 'Mensaje de Telegram'
    msg['From'] = os.getenv('DISMAIL')
    msg['To'] = email

    if event.message.text:
        msg.set_content(event.message.text)
    elif event.message.media:
        media = await event.client.download_media(event.message, file='mailtemp/')
        if os.path.getsize(media) < 59 * 1024 * 1024:  # 59 MB
            with open(media, 'rb') as f:
                msg.add_attachment(f.read(), maintype='application', subtype='octet-stream', filename=os.path.basename(media))
        else:
            await event.reply("El archivo supera el límite de lo permitido (59 MB).")
            return
    
    try:
        with smtplib.SMTP('disroot.org', 587) as server:
            server.starttls()
            server.login(os.getenv('DISMAIL'), os.getenv('DISPASS'))
            server.send_message(msg)
        await event.reply("Correo electrónico enviado correctamente.")
        await event.reply("Archivo enviado", reply_to=event.message.id)
    except Exception as e:
        await event.reply(f"Error al enviar el correo: {e}")
    finally:
        shutil.rmtree('mailtemp')
        os.mkdir('mailtemp')

# Configuración del cliente de Telethon
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# Manejo del evento de comando para /sendmail
@client.on(events.NewMessage(pattern='/sendmail'))
async def send_mail_handler(event):
    await send_mail(event)

# Manejo del evento de comando para /setmail
@client.on(events.NewMessage(pattern='/setmail'))
async def set_mail_handler(event):
    await set_mail(event)

# Manejo de cualquier mensaje recibido
@client.on(events.NewMessage)
async def handle_all_messages(event):
    if event.message.media:
        await send_mail(event)

client.start()
client.run_until_disconnected()
