#ifndef BUTTON_CONTROLLER_H
#define BUTTON_CONTROLLER_H

#include <Arduino.h>

enum ButtonType {
    BTN_NONE,
    BTN_BACK,
    BTN_SELECT,
    BTN_DOWN,
    BTN_UP,
    BTN_RIGHT,
    BTN_LEFT,
    BTN_MENU
};

enum ButtonPress {
    NONE,
    NEXT_PAGE,
    PREV_PAGE,
    MENU,
    BACK,
    MENU_UP,
    MENU_DOWN,
    MENU_LEFT,      
    MENU_RIGHT,     
    MENU_SELECT
};

class ButtonController {
public:
    void init();
    ButtonPress checkButton();
    void setReadingMode(bool enabled);
    bool getReadingMode();
    
private:
    ButtonType identifyButton(int reading);
    ButtonPress mapButtonInReadingMode(ButtonType button);
    ButtonPress mapButtonInMenuMode(ButtonType button);
    
    unsigned long lastPressTime = 0;
    static const unsigned long READING_DEBOUNCE = 5500;
    static const unsigned long MENU_DEBOUNCE = 500;
    bool isReadingMode = true;
};

#endif