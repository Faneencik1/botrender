from flask import Flask
from threading import Thread
import logging

app = Flask('')

# Отключаем логи от сервера Flask (werkzeug)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def home():
    return "Я жив!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
