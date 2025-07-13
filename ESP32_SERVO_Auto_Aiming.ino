#include <WiFi.h>
#include <ESP32Servo.h>

const char* ssid = "LaserTurretAP";
const char* password = "12345678";

WiFiServer server(80);

Servo servoPan;
Servo servoTilt;

void setup() {
  Serial.begin(115200);
  servoPan.attach(14);   // Pan servo on GPIO 13
  servoTilt.attach(27);  // Tilt servo on GPIO 12

  // Set up Wi-Fi Access Point
  WiFi.softAP(ssid, password);
  Serial.println("Access Point Started");
  Serial.println(WiFi.softAPIP());

  server.begin();
}

void loop() {
  WiFiClient client = server.available();
  if (client) {
    Serial.println("Client connected");
    String request = client.readStringUntil('\r');
    client.flush();

    // Parse angles from request like /move?pan=90&tilt=45
    int panIndex = request.indexOf("pan=");
    int tiltIndex = request.indexOf("tilt=");
    if (panIndex != -1 && tiltIndex != -1) {
      int pan = request.substring(panIndex + 4, request.indexOf('&')).toInt();
      int tilt = request.substring(tiltIndex + 5).toInt();

      pan = constrain(pan, 0, 180);
      tilt = constrain(tilt, 0, 180);

      servoPan.write(pan);
      servoTilt.write(tilt);

      Serial.printf("Pan: %d, Tilt: %d\n", pan, tilt);
    }

    // Simple response
    client.println("HTTP/1.1 200 OK");
    client.println("Content-Type: text/plain");
    client.println();
    client.println("OK");
    client.stop();
    Serial.println("Client disconnected");
  }
}
