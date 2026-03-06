# @title #Line
from flask import Flask, request, abort
from linebot.v3.webhook import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import threading
from schedule import schedule_main, handle_user_text
app = Flask(__name__)

# ---- Replace with your real tokens ----
CHANNEL_ACCESS_TOKEN = "6swo61L6E6bF15Zjrxed0oLAmJ84ZVS6xkzSxVH1Npv0XBp9Ba8ZXwNt23eza+v1Zyfsm5ZykMRkCOY5kIKJq9raxzVQC+hlom7D1xp2Jgu7DbzfO9oj+a5DTRmi9xY21xUFVX70ss1zYRwe2wRVEgdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "e2183fb006b144e393df0d11cc8c4c46"
# ---------------------------------------

# Create Configuration with your access token
config = Configuration(access_token=CHANNEL_ACCESS_TOKEN)

# Wrap it in ApiClient (required by v3 SDK)
api_client = ApiClient(config)

# Create MessagingApi using ApiClient
line_bot_api = MessagingApi(api_client)

# Webhook handler remains the same
handler = WebhookHandler(CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    print("Webhook received:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    response = handle_user_text(event.message.text)
    print(event.message.text)
    # Reply using v3 MessagingApi
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=response)]
        )
    )

def run_flask():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    schedule_main()
    # ---- start flask in thread ----

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

print("Flask started")