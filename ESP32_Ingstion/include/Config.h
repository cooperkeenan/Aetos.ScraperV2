#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

extern const char* WIFI_SSID;
extern const char* WIFI_PASSWORD;
extern const String FIREBASE_PROJECT;

extern const int EPD_CS;
extern const int EPD_DC;
extern const int EPD_RST;
extern const int EPD_BUSY;
extern const int EPD_PWR;
extern const int SD_CS;

extern const int BUTTON_PIN;

#endif