from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests

# ✅ ใส่ค่า API Key ตรงๆ ในโค้ด (ไม่ใช้ Environment Variables)
LINE_CHANNEL_ACCESS_TOKEN = "jhJocTrG2WWZocXJkj2TGNtchpZKEsxS5n7DssQKi2pgad1k83Rz9iJmtU8P6JoPxlJgry9wkW7NgB3ENgb2yVuaDnlVtHB3CmupkHQt/6K7aVxVPptE19s3f6tJ1lnGblJie4P5PBEoDIlp+T+aKgdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "9c41d2a0275ecd4e398efd7d2e4548f7"

# ✅ ตรวจสอบว่าค่าถูกต้องหรือไม่
if not LINE_CHANNEL_ACCESS_TOKEN or LINE_CHANNEL_ACCESS_TOKEN == "None":
    raise ValueError("❌ ERROR: LINE_CHANNEL_ACCESS_TOKEN ไม่มีค่า หรือไม่ถูกต้อง")

if not LINE_CHANNEL_SECRET or LINE_CHANNEL_SECRET == "None":
    raise ValueError("❌ ERROR: LINE_CHANNEL_SECRET ไม่มีค่า หรือไม่ถูกต้อง")

# ✅ ตั้งค่า API ของ LINE
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ✅ URL ของ API พยากรณ์
PREDICTION_API_URL = "https://ensemble-t564.onrender.com/predict"

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "✅ Line Chatbot for Penguin Prediction is Running."

@app.route("/callback", methods=["POST"])
def callback():
    """ รับข้อมูลจาก LINE Webhook """
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text.strip()
    print(f"📩 User Input: {user_input}")

    try:
        user_data = parse_user_input(user_input)

        if not user_data:
            reply_text = "❌ กรุณาส่งข้อมูลในรูปแบบ: \nBill Length, Bill Depth, Flipper Length, Body Mass, Sex"
        else:
            response = requests.post(PREDICTION_API_URL, json=user_data)
            result = response.json()

            if "prediction" in result:
                reply_text = f"🐧 สายพันธุ์ที่คาดการณ์: {result['prediction']}"
            else:
                reply_text = f"❌ Error: {result['error']}"

    except Exception as e:
        reply_text = f"❌ Error: {str(e)}"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

def parse_user_input(text):
    """ แปลงข้อความที่ผู้ใช้ส่งมาให้เป็น JSON สำหรับ API """
    try:
        parts = text.split(",")
        if len(parts) != 5:
            return None
        
        return {
            "bill_length_mm": float(parts[0]),
            "bill_depth_mm": float(parts[1]),
            "flipper_length_mm": float(parts[2]),
            "body_mass_g": float(parts[3]),
            "sex": parts[4].strip().upper()
        }
    except:
        return None

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
