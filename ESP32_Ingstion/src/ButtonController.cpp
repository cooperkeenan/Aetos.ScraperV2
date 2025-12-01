#include "ButtonController.h"
#include "Config.h"

void ButtonController::init() {
    pinMode(BUTTON_PIN, INPUT);
    Serial.println("Button controller initialized");
}

ButtonPress ButtonController::checkButton() {
    unsigned long now = millis();
    
    // Use different debounce times based on mode
    unsigned long debounceTime = isReadingMode ? READING_DEBOUNCE : MENU_DEBOUNCE;
    
    if (now - lastPressTime < debounceTime) {
        return NONE;
    }
    
    int reading = analogRead(BUTTON_PIN);
    ButtonType button = identifyButton(reading);
    
    if (button == BTN_NONE) {
        return NONE;
    }
    
    lastPressTime = now;
    
    if (isReadingMode) {
        return mapButtonInReadingMode(button);
    } else {
        return mapButtonInMenuMode(button);
    }
}

ButtonType ButtonController::identifyButton(int reading) {
    switch (reading) {
        case 0 ... 400:
            Serial.println("Button: BACK");
            return BTN_BACK;
            
        case 1700 ... 2100:
            Serial.println("Button: SELECT");
            return BTN_SELECT;
            
        case 2400 ... 2700:
            Serial.println("Button: DOWN");
            return BTN_DOWN;
            
        case 2800 ... 3000:
            Serial.println("Button: UP");
            return BTN_UP;
            
        case 3200 ... 3350:
            Serial.println("Button: RIGHT");
            return BTN_RIGHT;
            
        case 3351 ... 3500:
            Serial.println("Button: LEFT");
            return BTN_LEFT;
            
        case 3001 ... 3199:
            Serial.println("Button: MENU");
            return BTN_MENU;
            
        default:
            return BTN_NONE;
    }
}

ButtonPress ButtonController::mapButtonInReadingMode(ButtonType button) {
    switch (button) {
        case BTN_RIGHT:
            return NEXT_PAGE;
            
        case BTN_LEFT:
            return PREV_PAGE;
            
        case BTN_MENU:
            return MENU;
            
        case BTN_BACK:
            return BACK;
            
        default:
            return NONE;
    }
}

ButtonPress ButtonController::mapButtonInMenuMode(ButtonType button) {
    switch (button) {
        case BTN_UP:
            return MENU_UP;
            
        case BTN_DOWN:
            return MENU_DOWN;
            
        case BTN_LEFT:      
            return MENU_LEFT;
            
        case BTN_RIGHT:     
            return MENU_RIGHT;
            
        case BTN_SELECT:
            return MENU_SELECT;
            
        case BTN_BACK:
            return BACK;
            
        default:
            return NONE;
    }
}

void ButtonController::setReadingMode(bool enabled) {
    isReadingMode = enabled;
    Serial.printf("Mode: %s\n", enabled ? "Reading" : "Menu");
}

bool ButtonController::getReadingMode() {
    return isReadingMode;
}