#include <WiFi.h>
#include <PubSubClient.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

#define BUZZER_PIN 4

//WIFI credetials
const char *ssid = "wifi_ssid";           
const char *password = "wifi_password"; 

//MQTT SETUP
const char *mqtt_broker = "broker.emqx.io"; //REPLACE WITH UR BROKER ID (SAME AS ESP32)
const char *mqtt_topic = "emqx/esp32"; //REPLACE WITH TOPIC (SAME AS ESP32)
const int mqtt_port = 1883; //REPLACE WITH PORT (SAME AS ESP32)

WiFiClient espClient;
PubSubClient mqtt_client(espClient);

// NTP Client
WiFiUDP ntpUDP;
const long utcOffsetInSeconds = 5.5 * 3600; 
NTPClient timeClient(ntpUDP, "pool.ntp.org", utcOffsetInSeconds, 60000);

char last_received_msg[256]; // Global variable to store the last received message
bool buzzerActive = false;
unsigned long buzzerStartTime = 0;
const unsigned long BUZZER_DURATION_MS = 60000; // Alert duration (1 minute)
// Function Declarations
void connectToWiFi();
void connectToMQTT();
void mqttCallback(char *mqtt_topic, byte *payload, unsigned int length);
String generate_current_time();
void send_msg(const char* message);
void receive_msg();
void receiveTask(void *parameter);

void setup() {
    Serial.begin(115200);
    connectToWiFi();
    mqtt_client.setServer(mqtt_broker, mqtt_port);
    mqtt_client.setKeepAlive(60);
    mqtt_client.setCallback(mqttCallback);
    connectToMQTT();
    timeClient.begin();
    pinMode(BUZZER_PIN, OUTPUT);


    // Create a task for receiving messages
    xTaskCreate(receiveTask, "Receive Task", 10000, NULL, 1, NULL);
}
void connectToWiFi() {
    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nConnected to WiFi");
}
void connectToMQTT() {
    while (!mqtt_client.connected()) {
        String client_id = "esp32-client-" + String(WiFi.macAddress());
        Serial.printf("Connecting to MQTT Broker as %s.....\n", client_id.c_str());
        if (mqtt_client.connect(client_id.c_str())) { 
            Serial.println("Connected to MQTT broker");
            mqtt_client.subscribe(mqtt_topic);
            Serial.println("Subscribed to topic: " + String(mqtt_topic));
            send_msg("Hi, I'm ESP32 0.00 g"); 
        } else {
            Serial.print("Failed, rc=");
            Serial.print(mqtt_client.state());
            Serial.println(" try again in 5 seconds");
            delay(5000);
        }
    }
}

void mqttCallback(char *topic, byte *payload, unsigned int length) {
    // Create a temporary buffer to store the received message
    char temp_msg[256];
    memset(temp_msg, 0, sizeof(temp_msg)); // Clear the temporary buffer

    
    for (unsigned int i = 0; i < length; i++) {
        temp_msg[i] = (char)payload[i];
    }

    if (strncmp(temp_msg, "PC:", 3) == 0) {
        // If it does, copy it to last_received_msg
        memset(last_received_msg, 0, sizeof(last_received_msg)); // Clear previous message
        strncpy(last_received_msg, temp_msg + 3, sizeof(last_received_msg) - 1); // Copy new message

    }
    
}
String generate_current_time() { //THIS FUNCTION GENERATES CURRENT TIME, THIS IS USED AS AN EXAMPLE TO DEMONSTRATE THE COMMUNICATION, DELETE THSI IF NOT NEEEDED
    timeClient.update();
    int currentHour = timeClient.getHours();
    int currentMinute = timeClient.getMinutes();
    int currentSecond = timeClient.getSeconds(); 

    char timeStr[9];
    sprintf(timeStr, "%02d:%02d:%02d", currentHour, currentMinute,currentSecond);
    return String(timeStr);
}

void send_msg(const char* message) {
    String formatted_message = "ESP32: " + String(message); //MSG SEND FROM ESP32 WILL HAVE A PREFIX "ESP32:" THIS WILL BE REMOVED IN PYTHON CODE
    mqtt_client.publish(mqtt_topic,formatted_message.c_str());
}

void receive_msg() {
    mqtt_client.loop();
}

void receiveTask(void *parameter) {
    while (1) {
        if (!mqtt_client.connected()) {
            connectToMQTT();
        }
        receive_msg(); // This will run continuously and handle incoming messages
        vTaskDelay(10 / portTICK_PERIOD_MS); // Short delay to prevent WDT reset
    }
}

void loop() {
    if (!mqtt_client.connected()) {
        connectToMQTT();
    }

    String received_msg(last_received_msg); // Convert char array to String object
    if (received_msg == "TURN ON BUZZER") {
       Serial.print("PERSON DETECTED AT TIME: ");
       Serial.println(generate_current_time());
       digitalWrite(BUZZER_PIN, HIGH);
       buzzerActive = true;
       buzzerStartTime = millis();
       // Reset last_received_msg after handling
       memset(last_received_msg, 0, sizeof(last_received_msg));
    }

    // Non-blocking timer to turn buzzer off after duration expires
    if (buzzerActive && (millis() - buzzerStartTime >= BUZZER_DURATION_MS)) {
       digitalWrite(BUZZER_PIN, LOW);
       buzzerActive = false;
       Serial.println("Buzzer turned OFF after timeout.");
    }
}
