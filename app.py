# @title #Line
from flask import Flask, request, abort, jsonify
from linebot.v3.webhook import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    PushMessageRequest
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import threading
from schedule import start_scheduler, handle_user_text
import logging
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    force=True,
)

start_scheduler()
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

@app.route("/", methods=["GET"])
def home():
    instance = os.environ.get("WEBSITE_INSTANCE_ID", "local")
    app.logger.info("AWAKE ping received - instance")
    return jsonify({
        "status": "awake",
        "instance": instance
    }), 200

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    app.logger.info("Received webhook - signature: %s, body: %s", signature, body)
    print("Webhook received:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature.")
        abort(400)

    return 'OK'
"""
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    response = handle_user_text(event.message.text)
    print(event.message.text)
    app.logger.info("Handling message - user: %s, text: %s, response: %s", event.source.user_id, event.message.text, response)
    # Reply using v3 MessagingApi
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=response)]
        )
    )
"""
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    response = handle_user_text(event.message.text)

    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(
        line_bot_api.reply_message,
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=response)]
        )
    )

    try:
        app.logger.info("Trying reply_message with 60-second timeout")
        future.result(timeout=60)
        app.logger.info("reply_message succeeded")
        return

    except FuturesTimeoutError:
        app.logger.error("reply_message did not finish within 60 seconds; switching to push_message")

    except Exception:
        app.logger.exception("reply_message failed; switching to push_message")

    finally:
        executor.shutdown(wait=False)

    try:
        app.logger.info("Trying push_message fallback")
        line_bot_api.push_message(
            PushMessageRequest(
                to=event.source.user_id,
                messages=[TextMessage(text=response)]
            )
        )
        app.logger.info("push_message fallback succeeded")
    except Exception:
        app.logger.exception("push_message fallback failed")
        
def run_flask():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    run_flask()
