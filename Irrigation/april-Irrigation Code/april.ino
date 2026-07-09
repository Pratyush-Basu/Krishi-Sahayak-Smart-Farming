#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>

#define SOIL_SENSOR_PIN A0
#define RELAY_PIN D1

// ── আপনার WiFi ──────────────────────────
const char* ssid     = "realme Narzo 10A";
const char* password = "soubhik77";

// ── Flask server এর URL ──────────────────
// Cloudflare URL হলে: "https://abc-xyz.trycloudflare.com"
// Same network হলে:   "http://192.168.1.xxx:5000"
const char* serverURL = "http://10.101.7.101:5000";

int moistureThreshold = 30;

WiFiClient wifiClient;

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, INPUT);

  // WiFi connect
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected! IP: " + WiFi.localIP().toString());
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {

    int moistureRaw     = analogRead(SOIL_SENSOR_PIN);
    int moisturePercent = map(moistureRaw, 1023, 0, 0, 100);
    moisturePercent     = constrain(moisturePercent, 0, 100);

    // ── Step 1: Data Flask এ POST করো ───
    HTTPClient http;
    String postURL = String(serverURL) + "/sensor";
    http.begin(wifiClient, postURL);
    http.addHeader("Content-Type", "application/json");

    String json = "{\"raw\":" + String(moistureRaw) +
                  ",\"moisture\":" + String(moisturePercent) + "}";
    int httpCode = http.POST(json);
    http.end();

    // ── Step 2: Pump command Flask থেকে GET করো ─
    String cmdURL = String(serverURL) + "/command";
    http.begin(wifiClient, cmdURL);
    int code = http.GET();
    if (code == 200) {
      String response = http.getString();
      response.trim();

      if (response == "PUMP:ON") {
        pinMode(RELAY_PIN, OUTPUT);
        digitalWrite(RELAY_PIN, LOW);
        Serial.println("PUMP: ON");
      } else if (response == "PUMP:OFF") {
        pinMode(RELAY_PIN, INPUT);
        Serial.println("PUMP: OFF");
      }
    }
    http.end();

    Serial.print("Raw: ");
    Serial.print(moistureRaw);
    Serial.print(" | Moisture: ");
    Serial.print(moisturePercent);
    Serial.println(" %");
  }

  delay(5000);
}