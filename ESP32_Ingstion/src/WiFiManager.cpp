#include "WiFiManager.h"
#include "Config.h"

bool WiFiManager::connect() {
    Serial.println("Connecting to WiFi...");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    int retries = 0;
    while (WiFi.status() != WL_CONNECTED && retries < MAX_RETRIES) {
        delay(500);
        Serial.print(".");
        retries++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi Connected!");
        Serial.print("IP: ");
        Serial.println(WiFi.localIP());
        return true;
    }
    
    Serial.println("\nWiFi Failed!");
    return false;
}

bool WiFiManager::isConnected() {
    return WiFi.status() == WL_CONNECTED;
}