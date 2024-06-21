# Smart Surveillance System with Person Detection and Remote Access
This project integrates hardware components, machine learning, and communication protocols to create an intelligent surveillance system. It uses an ESP32 microcontroller with TensorFlow Lite for person detection. When a person is detected, the system activates a buzzer and provides remote access via a Telegram bot

Here are the key features:

# Person Detection using ESP32 and TensorFlow Lite:
An camera, connected to PC dectects the intruder. 
TensorFlow Lite (TFLite) runs a neural network model to detect people in these images.
When a person is detected, the system triggers an action.

# Buzzer Activation via MQTT:
The PC communicates with the ESP32 using MQTT.
Upon person detection, the PC sends an MQTT message to the ESP32, activating a buzzer or other alert mechanism.

# Telegram Bot for Remote Viewing:
A Telegram bot provides a link to live footage from the CCTV.
Users can access the stream remotely via their smartphones.
Overall, this project enhances security by detecting people, alerting through a buzzer, and enabling remote monitoring.
