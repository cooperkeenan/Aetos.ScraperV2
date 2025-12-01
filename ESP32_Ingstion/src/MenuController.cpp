#include "MenuController.h"

void MenuController::init() {
    selectedItem = MENU_BOOKS;
    Serial.println("Menu controller initialized");
}

void MenuController::moveUp() {
    if (selectedItem > 0) {
        selectedItem = (MenuItem)((int)selectedItem - 1);
        Serial.printf("Menu: Selected %d\n", (int)selectedItem);
    }
}

void MenuController::moveDown() {
    if (selectedItem < MENU_ITEM_COUNT - 1) {
        selectedItem = (MenuItem)((int)selectedItem + 1);
        Serial.printf("Menu: Selected %d\n", (int)selectedItem);
    }
}