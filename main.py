import telebot
from flask import Flask, request
import time
import threading
import os

# Token y bot
TOKEN = os.environ.get("BOT_TOKEN")  # ⚠️ más seguro usar variables de entorno
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# IDs autorizados
user1_id = 659933340
user2_id = 947245094

# Diccionario para mensajes temporales
mensajes_temporales = {}

# Enviar mensaje de estado al iniciar (una sola vez, puede fallar en deploy inicial)
try:
    bot.send_message(user1_id, "🤖 Bot activo. Podés empezar a chatear.")
    bot.send_message(user2_id, "🤖 Bot activo. Podés empezar a chatear.")
except:
    pass

# Manejador de mensajes
@bot.message_handler(func=lambda m: True)
def reenviar_mensaje(mensaje):
    if mensaje.from_user.id == user1_id:
        reenviado = bot.send_message(user2_id, f"👤 {mensaje.text}")
    elif mensaje.from_user.id == user2_id:
        reenviado = bot.send_message(user1_id, f"👤 {mensaje.text}")
    else:
        bot.send_message(mensaje.chat.id, "🚫 Este bot es solo para dos usuarios autorizados.")
        return

    ahora = time.time()
    mensajes_temporales[mensaje.message_id] = {'chat_id': mensaje.chat.id, 'timestamp': ahora}
    mensajes_temporales[reenviado.message_id] = {'chat_id': reenviado.chat.id, 'timestamp': ahora}

# Borrado automático en segundo plano
def borrar_mensajes():
    while True:
        ahora = time.time()
        for mid in list(mensajes_temporales.keys()):
            info = mensajes_temporales[mid]
            if ahora - info['timestamp'] > 60:
                try:
                    bot.delete_message(info['chat_id'], mid)
                    del mensajes_temporales[mid]
                except:
                    pass
        time.sleep(5)

threading.Thread(target=borrar_mensajes, daemon=True).start()

# Ruta webhook
@app.route(f'/{TOKEN}', methods=['POST'])
def recibir_update():
    json_update = request.get_json()
    update = telebot.types.Update.de_json(json_update)
    bot.process_new_updates([update])
    return "ok", 200

# Ruta raíz opcional (puede ser útil para test)
@app.route('/')
def index():
    return "Bot puente activo via webhook."

# Configurar webhook al iniciar
@app.before_first_request
def activar_webhook():
    webhook_url = f'https://{os.environ.get("RENDER_EXTERNAL_HOSTNAME")}/{TOKEN}'
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)

# Iniciar app Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
