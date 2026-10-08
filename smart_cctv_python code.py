from multiprocessing import Process, Queue
import paho.mqtt.client as mqtt
import time
import subprocess
import time
import re
from datetime import datetime
from queue import Empty
import cv2
from ultralytics import YOLO
from flask import Flask, Response
import asyncio
from telegram import Bot
import socket

import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def generate_live_cam_link():
    hostname = socket.gethostname()
    ipv4_address = socket.gethostbyname(hostname)
    link=f"http://{ipv4_address}:5000/video_feed"
    return link


# SETTING UP MQTT :
broker = os.environ.get("MQTT_BROKER", "broker.emqx.io")
port = int(os.environ.get("MQTT_PORT", 1883))
topic = os.environ.get("MQTT_TOPIC", "emqx/esp32")

# TELEGRAM BOT DETAILS
bot_token = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
chat_id = os.environ.get("CHAT_ID", "YOUR_CHAT_ID")


def start_ngrok():
    port=5000
    # Start ngrok and capture the output
    process = subprocess.Popen(['ngrok', 'http', str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)  # Wait for ngrok to initialize

    # Fetch the ngrok URL
    ngrok_output = subprocess.check_output(['curl', '-s', 'http://localhost:4040/api/tunnels'])
    ngrok_output = ngrok_output.decode('utf-8')

    # Extract the forwarding URL from the ngrok output
    url_pattern = re.compile(r'"public_url":"(https://[a-zA-Z0-9\-\.]+\.ngrok-free\.app)"')
    match = url_pattern.search(ngrok_output)

    if match:
        ngrok_url = match.group(1)+ "/video_feed"
        return ngrok_url
    else:
        raise Exception("Ngrok URL not found")


async def send_message_tele(text):
    if not bot_token or bot_token == 'YOUR_BOT_TOKEN' or not chat_id or chat_id == 'YOUR_CHAT_ID':
        print("[WARNING] Telegram bot_token or chat_id not configured in .env. Skipping Telegram message.")
        return
    try:
        bot = Bot(token=bot_token)
        await bot.send_message(chat_id=chat_id, text=text)
        print("Message sent TO TELEGRAM BOT!")
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram message: {e}")

def send_telegram_msg(message):
    if not bot_token or bot_token == 'YOUR_BOT_TOKEN' or not chat_id or chat_id == 'YOUR_CHAT_ID':
        print("[WARNING] Telegram bot_token or chat_id not configured in .env. Skipping Telegram message.")
        return
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(send_message_tele(message))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

def current_time():
    return datetime.now().strftime("%H:%M:%S")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to {broker} with result code {rc}")
        client.subscribe(topic, qos=0)
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    received_msg = msg.payload.decode()
    if received_msg.startswith("ESP32:"):
        received_msg = received_msg[6:]
        userdata.put(received_msg)

def receive_msg(queue):
    client = mqtt.Client(userdata=queue)
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(broker, port, 60)
        client.loop_forever()
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")

def send_message(message):
    prefixed_message = f"{message}"
    client = mqtt.Client()
    try:
        client.connect(broker, port, 60)
        client.publish(topic, prefixed_message)
        print(f"Sent message: {prefixed_message}\n")
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")

def get_latest_message(queue):
    try:
        return queue.get_nowait()
    except Empty:
        return None

# FLASK VIDEO STREAMING FUNCTION:
def start_flask_stream(frame_queue):
    app = Flask(__name__)

    def generate_frames():
        while True:
            frame = frame_queue.get()
            if frame is None:
                break
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    @app.route('/video_feed')
    def video_feed():
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    # Use Ngrok URL and port 5000 (HTTPS) for secure connection
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)


    
# SETTING UP TFLITE FOR OBJECT DETECTION:
def perform_real_time_detection(frame_queue):
    model_path = os.environ.get("MODEL_PATH", os.path.join(BASE_DIR, "best_float32.tflite"))
    if not os.path.isabs(model_path):
        model_path = os.path.join(BASE_DIR, model_path)
    print(f"Loading TFLite model from: {model_path}")
    model = YOLO(model_path)
    print(model.names)
    webcamera = cv2.VideoCapture(0)

    while True:
        success, frame = webcamera.read()
        if not success:
            break
        results = model.track(frame, classes=0, conf=0.4, imgsz=416)
        cv2.putText(frame, f"Total: {len(results[0].boxes)}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        try:
            for result in results:
                item_cls_index = result.boxes.cls[0].item()
                detected_item = result.names[item_cls_index]
                if detected_item == "person":
                    send_message("PC:TURN ON BUZZER")
                    print("send msg to turn on buzzer")
        except:
            detected_item = None
        frame_queue.put(results[0].plot())
        if cv2.waitKey(1) == ord('q'):
            break
    webcamera.release()
    cv2.destroyAllWindows()
    frame_queue.put(None)  # Signal to the Flask app that the stream is over

def main(frame_queue):

    send_telegram_msg(f"CLICK LINK BELOW TO WATCH FOOTAGE FROM LIVE CAMERA \n \n{start_ngrok()}")
    perform_real_time_detection(frame_queue)

if __name__ == '__main__':
    frame_queue = Queue()
    receive_process = Process(target=receive_msg, args=(frame_queue,))
    receive_process.start()

    flask_process = Process(target=start_flask_stream, args=(frame_queue,))
    flask_process.start()

    main(frame_queue)

    receive_process.join()
    flask_process.join()
