import os
import json
import logging

import requests, urllib
from flask import Flask, request

app = Flask(__name__)

def send_message(msg):
  url  = 'https://api.groupme.com/v3/bots/post'
  data = {
    "bot_id": os.getenv('GROUPME_BOT_ID'),
    "text": msg
  }
  resp = requests.post(url, data=json.dumps(data))

@app.route('/', methods=['POST'])
def webhook():
  
  data = request.get_json()
  
  # We don't want to reply to ourselves!
  if data['name'] != 'Milo':
    msg = data['name']
    send_message(msg)

  return "OK", 200

