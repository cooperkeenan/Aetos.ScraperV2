#ifndef DISPLAY_CONTROLLER_H
#define DISPLAY_CONTROLLER_H

#include <Arduino.h>
#include <GxEPD2_BW.h>
#include "BookSelector.h"

class DisplayController {
public:
    void init();
    void powerOn();
    void powerOff();
    void showMessage(const char* message);
    void displayBookPage(const String& content, const String& header, int pageNum, int totalPages, int fontSize = 2);
    void showMenu(int selectedIndex);
    void hideMenu();
    void setPartialUpdate(bool enabled);
    void showBookGrid(BookSelector& selector);

    
private:
    GxEPD2_BW<GxEPD2_750_T7, GxEPD2_750_T7::HEIGHT>* display = nullptr;
    bool isPowered = false;
};

#endif