#ifndef MENU_CONTROLLER_H
#define MENU_CONTROLLER_H

#include <Arduino.h>

enum MenuItem {
    MENU_BOOKS,
    MENU_GALLERY,
    MENU_ITEM_COUNT
};

class MenuController {
public:
    void init();
    void moveUp();
    void moveDown();
    MenuItem getSelected() { return selectedItem; }
    int getSelectedIndex() { return (int)selectedItem; }
    
private:
    MenuItem selectedItem = MENU_BOOKS;
};

#endif