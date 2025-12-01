#include "BookSelector.h"
#include <vector>
#include <ArduinoJson.h> 

void BookSelector::init() {
    selectedRow = 0;
    selectedCol = 0;
    currentPage = 0;
    Serial.println("Book selector initialized");
}

void BookSelector::loadBooks() {
    books.clear();
    loadBooksFromSD();
    addPlaceholders();
    Serial.printf("Loaded %d books\n", books.size());
}

void BookSelector::loadBooksFromSD() {
    File root = SD.open("/books");
    if (!root) {
        Serial.println("Failed to open /books directory");
        return;
    }
    
    File file = root.openNextFile();
    while (file) {
        if (file.isDirectory()) {
            String bookId = String(file.name());
            String metaPath = "/books/" + bookId + "/meta.json";
            
            if (SD.exists(metaPath.c_str())) {
                File metaFile = SD.open(metaPath.c_str(), FILE_READ);
                if (metaFile) {
                    JsonDocument doc;
                    if (!deserializeJson(doc, metaFile)) {
                        BookInfo info;
                        info.bookId = bookId;
                        info.title = doc["title"].as<String>();
                        info.author = doc["author"].as<String>();
                        info.isPlaceholder = false;
                        books.push_back(info);
                    }
                    metaFile.close();
                }
            }
        }
        file = root.openNextFile();
    }
    root.close();
}

void BookSelector::addPlaceholders() {
    // Add placeholders to fill up to 15 slots
    for (int i = books.size(); i < 15; i++) {
        BookInfo placeholder;
        placeholder.bookId = "";
        placeholder.title = "Empty Slot";
        placeholder.author = "";
        placeholder.isPlaceholder = true;
        books.push_back(placeholder);
    }
}

void BookSelector::moveUp() {
    if (selectedRow > 0) {
        selectedRow--;
        Serial.printf("Grid position: [%d, %d]\n", selectedRow, selectedCol);
    }
}

void BookSelector::moveDown() {
    int totalOnPage = min(BOOKS_PER_PAGE, (int)books.size() - (currentPage * BOOKS_PER_PAGE));
    int maxRow = (totalOnPage - 1) / COLS;
    
    if (selectedRow < maxRow) {
        selectedRow++;
        Serial.printf("Grid position: [%d, %d]\n", selectedRow, selectedCol);
    }
}

void BookSelector::moveLeft() {
    if (selectedCol > 0) {
        selectedCol--;
        Serial.printf("Grid position: [%d, %d]\n", selectedRow, selectedCol);
    }
}

void BookSelector::moveRight() {
    if (selectedCol < COLS - 1) {
        int index = selectedRow * COLS + selectedCol + 1;
        int totalOnPage = min(BOOKS_PER_PAGE, (int)books.size() - (currentPage * BOOKS_PER_PAGE));
        
        if (index < totalOnPage) {
            selectedCol++;
            Serial.printf("Grid position: [%d, %d]\n", selectedRow, selectedCol);
        }
    }
}

void BookSelector::nextPage() {
    if (currentPage < getTotalPages() - 1) {
        currentPage++;
        selectedRow = 0;
        selectedCol = 0;
        Serial.printf("Page %d/%d\n", currentPage + 1, getTotalPages());
    }
}

void BookSelector::previousPage() {
    if (currentPage > 0) {
        currentPage--;
        selectedRow = 0;
        selectedCol = 0;
        Serial.printf("Page %d/%d\n", currentPage + 1, getTotalPages());
    }
}

BookInfo BookSelector::getSelectedBook() {
    int index = (currentPage * BOOKS_PER_PAGE) + (selectedRow * COLS) + selectedCol;
    if (index < books.size()) {
        return books[index];
    }
    BookInfo empty;
    empty.isPlaceholder = true;
    return empty;
}

void BookSelector::getBooksOnCurrentPage(BookInfo* pageBooks, int& count) {
    int startIndex = currentPage * BOOKS_PER_PAGE;
    count = 0;
    
    for (int i = 0; i < BOOKS_PER_PAGE && (startIndex + i) < books.size(); i++) {
        pageBooks[count++] = books[startIndex + i];
    }
}