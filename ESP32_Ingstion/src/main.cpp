#include <Arduino.h>
#include "Config.h"
#include "WiFiManager.h"
#include "DisplayController.h"
#include "BookReader.h"
#include "ButtonController.h"
#include "MenuController.h"
#include "BookSelector.h"
#include <SD.h>
#include <SPI.h>

WiFiManager wifiManager;
DisplayController display;
BookReader reader;
ButtonController buttons;
MenuController menu;
BookSelector bookSelector;

enum AppState {
    STATE_READING,
    STATE_MENU,
    STATE_BOOK_GRID
};

AppState appState = STATE_READING;

void setup() {
    Serial.begin(115200);
    delay(2000);
    Serial.println("\n=== Book Reader ===");
    
    pinMode(EPD_PWR, OUTPUT);
    digitalWrite(EPD_PWR, LOW);
    pinMode(EPD_CS, OUTPUT);
    digitalWrite(EPD_CS, HIGH);
    pinMode(SD_CS, OUTPUT);
    digitalWrite(SD_CS, HIGH);
    
    SPI.begin(18, 19, 23);
    delay(100);
    
    Serial.println("Initializing SD...");
    if (!SD.begin(SD_CS, SPI)) {
        Serial.println("SD FAILED");
        while(1) delay(1000);
    }
    Serial.println("SD OK");
    
    if (!SD.exists("/books")) {
        SD.mkdir("/books");
    }
    
    buttons.init();
    menu.init();
    bookSelector.init();
    bookSelector.loadBooks();
    
    display.init();
    display.showMessage("Connecting WiFi...");
    
    if (!wifiManager.connect()) {
        display.showMessage("WiFi Failed");
        while(1) delay(1000);
    }
    
    String bookId = "3fb1ff92e94d";
    
    if (SD.exists(("/books/" + bookId + "/meta.json").c_str())) {
        Serial.println("Book already on SD card");
    } else {
        display.showMessage("Downloading book...");
        
        if (!reader.downloadBook(bookId)) {
            display.showMessage("Download Failed");
            while(1) delay(1000);
        }
    }
    
    display.showMessage("Loading book...");
    
    if (!reader.loadBook(bookId)) {
        display.showMessage("Load Failed");
        while(1) delay(1000);
    }
    
    String page = reader.getCurrentPage();
    display.displayBookPage(page, reader.getBookTitle(), 
                           reader.getCurrentPageNum(), reader.getTotalPages(), 2);
    
    Serial.println("=== Ready ===");
}

void loop() {
    ButtonPress button = buttons.checkButton();
    
    if (appState == STATE_MENU) {
        // Menu mode
        switch (button) {
            case MENU_UP:
                menu.moveUp();
                display.showMenu(menu.getSelectedIndex());
                break;
                
            case MENU_DOWN:
                menu.moveDown();
                display.showMenu(menu.getSelectedIndex());
                break;
                
            case MENU_SELECT: {
                if (menu.getSelected() == MENU_BOOKS) {
                    Serial.println("Selected: Books");
                    appState = STATE_BOOK_GRID;
                    buttons.setReadingMode(false);
                    display.showBookGrid(bookSelector);
                } 
                else if (menu.getSelected() == MENU_GALLERY) {
                    Serial.println("Selected: Gallery");
                    display.showMessage("Gallery\nComing Soon!");
                }
                break;
            }
                
            case BACK: {
                appState = STATE_READING;
                buttons.setReadingMode(true);
                display.hideMenu();
                
                String page = reader.getCurrentPage();
                display.displayBookPage(page, reader.getBookTitle(), 
                                       reader.getCurrentPageNum(), reader.getTotalPages(), 2);
                break;
            }
                
            default:
                break;
        }
    }
    else if (appState == STATE_BOOK_GRID) {
        // Book grid navigation
        switch (button) {
            case MENU_UP:
                bookSelector.moveUp();
                display.showBookGrid(bookSelector);
                break;
                
            case MENU_DOWN:
                bookSelector.moveDown();
                display.showBookGrid(bookSelector);
                break;
                
            case MENU_LEFT:
                bookSelector.moveLeft();
                display.showBookGrid(bookSelector);
                break;
                
            case MENU_RIGHT:
                bookSelector.moveRight();
                display.showBookGrid(bookSelector);
                break;
                
            case MENU_SELECT: {
                BookInfo selected = bookSelector.getSelectedBook();
                if (!selected.isPlaceholder) {
                    Serial.printf("Loading book: %s\n", selected.title.c_str());
                    
                    if (reader.loadBook(selected.bookId)) {
                        appState = STATE_READING;
                        buttons.setReadingMode(true);
                        
                        String page = reader.getCurrentPage();
                        display.displayBookPage(page, reader.getBookTitle(), 
                                               reader.getCurrentPageNum(), reader.getTotalPages(), 2);
                    } else {
                        display.showMessage("Failed to\nload book");
                    }
                }
                break;
            }
                
            case BACK:
                appState = STATE_MENU;
                display.showMenu(menu.getSelectedIndex());
                break;
                
            default:
                break;
        }
    }
    else {
        // Reading mode (STATE_READING)
        switch (button) {
            case NEXT_PAGE: {
                if (reader.nextPage()) {
                    String page = reader.getCurrentPage();
                    display.displayBookPage(page, reader.getBookTitle(), 
                                           reader.getCurrentPageNum(), reader.getTotalPages(), 2);
                } else {
                    Serial.println("End of book");
                }
                break;
            }
                
            case PREV_PAGE: {
                if (reader.previousPage()) {
                    String page = reader.getCurrentPage();
                    display.displayBookPage(page, reader.getBookTitle(), 
                                           reader.getCurrentPageNum(), reader.getTotalPages(), 2);
                } else {
                    Serial.println("Start of book");
                }
                break;
            }
                
            case MENU:
                appState = STATE_MENU;
                buttons.setReadingMode(false);
                display.showMenu(menu.getSelectedIndex());
                break;
                
            default:
                break;
        }
    }
    
    delay(100);
}