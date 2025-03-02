from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
)
import requests
from linebot.models import ImageSendMessage

LINE_CHANNEL_ACCESS_TOKEN = "jhJocTrG2WWZocXJkj2TGNtchpZKEsxS5n7DssQKi2pgad1k83Rz9iJmtU8P6JoPxlJgry9wkW7NgB3ENgb2yVuaDnlVtHB3CmupkHQt/6K7aVxVPptE19s3f6tJ1lnGblJie4P5PBEoDIlp+T+aKgdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "9c41d2a0275ecd4e398efd7d2e4548f7"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

PREDICTION_API_URL = "https://ensemble-t564.onrender.com/predict"

app = Flask(__name__)

user_sessions = {}

@app.route("/", methods=["GET"])
def home():
    return "Line Chatbot for Penguin Prediction is Running."

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_input = event.message.text.strip().lower()

    if user_input in ["help", "ช่วยเหลือ","วิธีใช้","สอบถาม"]:
        reply_text = (
            "🔹 วิธีใช้ระบบพยากรณ์\n"
            "1️⃣ พิมพ์ 'Prediction' เพื่อเริ่มต้น\n"
            "2️⃣ บอทจะถามค่าที่ต้องกรอกทีละข้อ\n"
            "3️⃣ ตอบค่าต่างๆ ตามที่ระบบขอ\n"
            "4️⃣ หลังจากกรอกครบ ระบบจะทำการพยากรณ์ผล"
        )
        reply_image=ImageSendMessage(
            original_content_url="https://www.voyagers.travel/_ipx/w_2400&f_webp&q_85/google/travel-web-app-1.appspot.com/flamelink/media/King%20penguin%20-%20Canva%20-%20zona.jpg%3Falt=media",
            preview_image_url="https://www.voyagers.travel/_ipx/w_2400&f_webp&q_85/google/travel-web-app-1.appspot.com/flamelink/media/King%20penguin%20-%20Canva%20-%20zona.jpg%3Falt=media"

        )

        line_bot_api.reply_message(event.reply_token,[TextSendMessage(text=reply_text),reply_image])
        return

    if user_input in ["prediction","พยากรณ์","ทำนาย","predict","predictions"]:
        user_sessions[user_id] = {"step": 1, "data": {}}
        reply_text = "กรุณากรอกค่า Bill Length (mm) เช่น 40.1"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

    if user_id in user_sessions:
        session = user_sessions[user_id]
        step = session["step"]

        try:
            if step == 1:
                session["data"]["bill_length_mm"] = float(user_input)
                reply_text = "กรุณากรอกค่า Bill Depth (mm) เช่น 18.7"
                session["step"] += 1
            elif step == 2:
                session["data"]["bill_depth_mm"] = float(user_input)
                reply_text = "กรุณากรอกค่า Flipper Length (mm) เช่น 190.5"
                session["step"] += 1
            elif step == 3:
                session["data"]["flipper_length_mm"] = float(user_input)
                reply_text = "กรุณากรอกค่า Body Mass (g) เช่น 3500"
                session["step"] += 1
            elif step == 4:
                session["data"]["body_mass_g"] = float(user_input)
                reply_text = "กรุณาเลือกเพศของนก (MALE หรือ FEMALE)"
                session["step"] += 1

                quick_reply = QuickReply(
                    items=[
                        QuickReplyButton(action=MessageAction(label="MALE", text="MALE")),
                        QuickReplyButton(action=MessageAction(label="FEMALE", text="FEMALE"))
                    ]
                )
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text, quick_reply=quick_reply))
                return
            elif step == 5:
                session["data"]["sex"] = user_input.upper()

                if session["data"]["sex"] not in ["MALE", "FEMALE"]:
                    reply_text = "กรุณาเลือกเพศเป็น 'MALE' หรือ 'FEMALE' เท่านั้น"
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
                    return

                response = requests.post(PREDICTION_API_URL, json=session["data"])
                result = response.json()

                if "prediction" in result:
                    reply_text = f"สายพันธุ์ที่คาดการณ์: {result['prediction']}"
                else:
                    reply_text = f"Error: {result.get('error', 'ไม่สามารถพยากรณ์ได้')}"

                del user_sessions[user_id]
            else:
                reply_text = "มีข้อผิดพลาด กรุณาลองใหม่"

        except ValueError:
            reply_text = "กรุณากรอกค่าตัวเลขที่ถูกต้อง"

        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

    quick_reply = QuickReply(
        items=[
            QuickReplyButton(action=MessageAction(label="เริ่มพยากรณ์", text="Prediction")),
            QuickReplyButton(action=MessageAction(label="วิธีใช้", text="ช่วยเหลือ"))
        ]
    )
    reply_text = "ไม่เข้าใจคำสั่ง กรุณาเลือกจากปุ่มด้านล่าง"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text, quick_reply=quick_reply))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
