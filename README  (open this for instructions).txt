STEPS TO BE FOLLOWED TO MODIFY PYTHON CODE:

1. Open the project folder directory in your code editor (e.g. VSCode).

2. Install the required Python packages:
	
	pip install -r requirements.txt

3. Environment Variables Configuration:
	- Copy `.env.example` to `.env` in the project root:
		cp .env.example .env
	- Open `.env` and fill in your details:
		BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
		CHAT_ID=YOUR_TELEGRAM_CHAT_ID
		MQTT_BROKER=broker.emqx.io
		MQTT_TOPIC=emqx/esp32
		MODEL_PATH=best_float32.tflite

4. Set up ngrok:
	- Download ngrok or install via `pip install ngrok`.
	- Authenticate ngrok if using for the first time: `ngrok config add-authtoken <your-token>`
	- Test running: `ngrok http 5000`

5. Telegram Bot setup (using BotFather in Telegram):
	- Create a bot via @BotFather to get your Bot API token.
	- Obtain your Telegram Chat ID by opening:
	  https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
	- Enter `BOT_TOKEN` and `CHAT_ID` inside your `.env` file.

6. Model path (.tflite):
	- By default, `best_float32.tflite` is loaded automatically from the project root folder.
	- No hardcoded paths are required! You can also override the model path via `MODEL_PATH` in `.env`.


STEPS TO MODIFY ESP32 CODE:

1. Install required libraries in Arduino IDE:
	- WiFi
	- PubSubClient
	- NTPClient

2. Open `esp32_code_cctv/esp32_code_cctv.ino`.
	- Set your Wi-Fi credentials (`ssid` and `password` on lines 11 & 12).
	- Ensure `mqtt_topic` matches the `MQTT_TOPIC` defined in your `.env` file.

3. Pin Configuration:
	- Connect the data pin of the active buzzer to GPIO 4 on your ESP32.

4. Non-blocking Buzzer Timer:
	- The ESP32 now uses a non-blocking `millis()` timer for the 60-second alert period, keeping the system fully responsive and connected to MQTT throughout.


THATS IT!

Now after flashing the code to your ESP32:
1. Run the Python application: `python "smart_cctv_python code.py"`
2. Power up your ESP32.
3. When the camera detects a person, it triggers the ESP32 buzzer and sends a live streaming link to your Telegram bot!
