#include "DisplayController.h"
#include "Config.h"
#include "TextFormatter.h"
#include <Fonts/FreeMonoBold9pt7b.h>

void DisplayController::init() {
    pinMode(EPD_PWR, OUTPUT);
    digitalWrite(EPD_PWR, LOW);
    isPowered = false;
    
    display = new GxEPD2_BW<GxEPD2_750_T7, GxEPD2_750_T7::HEIGHT>(
        GxEPD2_750_T7(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY)
    );
    
    Serial.println("Display initialized");
}

void DisplayController::powerOn() {
    if (!isPowered) {
        digitalWrite(SD_CS, HIGH);
        digitalWrite(EPD_PWR, HIGH);
        delay(100);
        display->init(115200);
        isPowered = true;
        Serial.println("Display powered ON");
    }
}

void DisplayController::powerOff() {
    if (isPowered) {
        display->hibernate();
        digitalWrite(EPD_PWR, LOW);
        isPowered = false;
        Serial.println("Display powered OFF");
    }
}

void DisplayController::showMessage(const char* message) {
    powerOn();
    digitalWrite(SD_CS, HIGH);
    
    display->setRotation(1);
    display->setFullWindow();
    
    display->firstPage();
    do {
        display->fillScreen(GxEPD_WHITE);
        display->setTextColor(GxEPD_BLACK);
        display->setFont(&FreeMonoBold9pt7b);
        display->setCursor(10, 30);
        display->println(message);
    } while (display->nextPage());
    
    Serial.printf("Message: %s\n", message);
}



void DisplayController::displayBookPage(const String& content, const String& header, int pageNum, int totalPages, int fontSize) {
    powerOn();
    digitalWrite(SD_CS, HIGH);
    
    // Clean the content using TextFormatter
    String cleanedContent = TextFormatter::cleanUTF8ToASCII(content);
    
    display->setRotation(1);
    display->setFullWindow();
    
    display->firstPage();
    do {
        display->fillScreen(GxEPD_WHITE);
        display->setTextColor(GxEPD_BLACK);
        
        display->setFont();
        display->setTextSize(1);
        display->setCursor(display->width() - 50, 10);
        display->printf("%d/%d", pageNum, totalPages);
        
        display->setTextSize(fontSize);
        
        int charWidth = 6 * fontSize;
        int lineHeight = 10 * fontSize;
        int y = 30;
        int x = 10;
        int maxX = display->width() - 10;
        int maxY = display->height() - 20;
        
        String word = "";
        
        for (int i = 0; i < cleanedContent.length(); i++) {
            char c = cleanedContent[i];
            
            if (c == '\n') {
                if (word.length() > 0) {
                    int wordWidth = word.length() * charWidth;
                    if (x + wordWidth > maxX) {
                        y += lineHeight;
                        x = 10;
                    }
                    if (y <= maxY) {
                        for (int j = 0; j < word.length(); j++) {
                            display->setCursor(x, y);
                            display->print(word[j]);
                            x += charWidth;
                        }
                    }
                    word = "";
                }
                y += lineHeight;
                x = 10;
                continue;
            }
            
            if (c == ' ') {
                int wordWidth = word.length() * charWidth;
                
                if (x + wordWidth > maxX) {
                    y += lineHeight;
                    x = 10;
                }
                
                if (y > maxY) break;
                
                for (int j = 0; j < word.length(); j++) {
                    display->setCursor(x, y);
                    display->print(word[j]);
                    x += charWidth;
                }
                
                if (x + charWidth <= maxX) {
                    display->setCursor(x, y);
                    display->print(' ');
                    x += charWidth;
                }
                
                word = "";
            } else {
                word += c;
            }
        }
        
        if (word.length() > 0 && y <= maxY) {
            int wordWidth = word.length() * charWidth;
            if (x + wordWidth > maxX) {
                y += lineHeight;
                x = 10;
            }
            for (int j = 0; j < word.length(); j++) {
                display->setCursor(x, y);
                display->print(word[j]);
                x += charWidth;
            }
        }
        
    } while (display->nextPage());
    
    Serial.printf("Page %d/%d displayed\n", pageNum, totalPages);
}

void DisplayController::setPartialUpdate(bool enabled) {
    if (enabled && isPowered) {
        display->setPartialWindow(0, 0, display->width(), display->height());
        Serial.println("Display: Partial refresh enabled");
    } else if (isPowered) {
        display->setFullWindow();
        Serial.println("Display: Full refresh enabled");
    }
}

void DisplayController::showMenu(int selectedIndex) {
    powerOn();
    digitalWrite(SD_CS, HIGH);
    
    display->setRotation(1);
    
    // Use partial refresh for faster update
    int menuWidth = 300;
    int menuHeight = 200;
    int menuX = (display->width() - menuWidth) / 2;
    int menuY = (display->height() - menuHeight) / 2;
    
    display->setPartialWindow(menuX, menuY, menuWidth, menuHeight);
    
    display->firstPage();
    do {
        // Draw white background
        display->fillRect(menuX, menuY, menuWidth, menuHeight, GxEPD_WHITE);
        
        // Draw border
        display->drawRect(menuX, menuY, menuWidth, menuHeight, GxEPD_BLACK);
        display->drawRect(menuX + 1, menuY + 1, menuWidth - 2, menuHeight - 2, GxEPD_BLACK);
        
        display->setTextColor(GxEPD_BLACK);
        display->setFont(&FreeMonoBold9pt7b);
        
        int itemY = menuY + 70;
        int itemSpacing = 50;
        
        // Books
        if (selectedIndex == 0) {
            display->fillRect(menuX + 20, itemY - 25, menuWidth - 40, 35, GxEPD_BLACK);
            display->setTextColor(GxEPD_WHITE);
        } else {
            display->setTextColor(GxEPD_BLACK);
        }
        display->setCursor(menuX + menuWidth / 2 - 40, itemY);
        display->print("Books");
        
        // Gallery
        itemY += itemSpacing;
        if (selectedIndex == 1) {
            display->fillRect(menuX + 20, itemY - 25, menuWidth - 40, 35, GxEPD_BLACK);
            display->setTextColor(GxEPD_WHITE);
        } else {
            display->setTextColor(GxEPD_BLACK);
        }
        display->setCursor(menuX + menuWidth / 2 - 55, itemY);
        display->print("Gallery");
        
    } while (display->nextPage());
    
    Serial.println("Menu displayed (partial refresh)");
}

void DisplayController::hideMenu() {
    // Switch back to full window for next update
    if (isPowered) {
        display->setFullWindow();
    }
    Serial.println("Menu hidden, full refresh mode");
}

void DisplayController::showBookGrid(BookSelector& selector) {
    powerOn();
    digitalWrite(SD_CS, HIGH);
    
    display->setRotation(1);
    
    static int lastSelectedRow = -1;
    static int lastSelectedCol = -1;
    static int lastPage = -1;
    
    int currentRow = selector.getSelectedRow();
    int currentCol = selector.getSelectedCol();
    int currentPage = selector.getCurrentPage();
    
    bool pageChanged = (lastPage != currentPage);
    
    if (pageChanged) {
        display->setFullWindow();
    } else {
        display->setPartialWindow(0, 0, display->width(), display->height());
    }
    
    display->firstPage();
    do {
        if (pageChanged) {
            display->fillScreen(GxEPD_WHITE);
        }
        
        display->setTextColor(GxEPD_BLACK);
        
        const int rows = 4;
        const int cols = 3;
        const int gridMargin = 20;
        const int cellSpacing = 10;
        
        int gridWidth = display->width() - (2 * gridMargin);
        int gridHeight = display->height() - (2 * gridMargin) - 30;
        
        int cellWidth = (gridWidth - ((cols - 1) * cellSpacing)) / cols;
        int cellHeight = (gridHeight - ((rows - 1) * cellSpacing)) / rows;
        
        BookInfo pageBooks[12];
        int bookCount;
        selector.getBooksOnCurrentPage(pageBooks, bookCount);
        
        // Draw ALL cells every time (for partial refresh)
        for (int row = 0; row < rows; row++) {
            for (int col = 0; col < cols; col++) {
                int index = row * cols + col;
                if (index >= bookCount) break;
                
                int x = gridMargin + (col * (cellWidth + cellSpacing));
                int y = gridMargin + (row * (cellHeight + cellSpacing));
                
                bool isSelected = (row == currentRow && col == currentCol);
                
                // Clear the entire cell
                display->fillRoundRect(x, y, cellWidth, cellHeight, 5, GxEPD_WHITE);
                
                // Draw cell border and fill
                if (isSelected) {
                    display->fillRoundRect(x, y, cellWidth, cellHeight, 5, GxEPD_BLACK);
                    display->setTextColor(GxEPD_WHITE);
                } else {
                    display->drawRoundRect(x, y, cellWidth, cellHeight, 5, GxEPD_BLACK);
                    display->drawRoundRect(x + 1, y + 1, cellWidth - 2, cellHeight - 2, 5, GxEPD_BLACK);
                    display->setTextColor(GxEPD_BLACK);
                }
                
                // Draw title with word wrapping
                String title = pageBooks[index].title;
                display->setFont();
                display->setTextSize(1);
                
                int textPadding = 20;  // Increased padding
                int maxWidth = cellWidth - (2 * textPadding);
                int lineHeight = 10;
                int charWidth = 6;
                int maxCharsPerLine = maxWidth / charWidth;
                
                // Word wrap algorithm
                std::vector<String> lines;
                String currentLine = "";
                
                // Split by spaces
                int wordStart = 0;
                for (int i = 0; i <= title.length(); i++) {
                    if (i == title.length() || title[i] == ' ') {
                        if (i > wordStart) {
                            String word = title.substring(wordStart, i);
                            
                            // Check if adding this word exceeds line width
                            String testLine = currentLine.length() == 0 ? word : currentLine + " " + word;
                            
                            if (testLine.length() > maxCharsPerLine) {
                                if (currentLine.length() > 0) {
                                    // Save current line and start new one
                                    lines.push_back(currentLine);
                                    currentLine = word;
                                } else {
                                    // Word itself is too long, truncate it
                                    lines.push_back(word.substring(0, maxCharsPerLine - 3) + "...");
                                    currentLine = "";
                                    break;
                                }
                                
                                // Max 3 lines
                                if (lines.size() >= 3) {
                                    currentLine = "";
                                    break;
                                }
                            } else {
                                currentLine = testLine;
                            }
                        }
                        wordStart = i + 1;
                    }
                }
                
                // Add last line
                if (currentLine.length() > 0 && lines.size() < 3) {
                    lines.push_back(currentLine);
                }
                
                // Truncate if we have too many lines
                if (lines.size() > 3) {
                    lines.resize(3);
                    String lastLine = lines[2];
                    if (lastLine.length() > maxCharsPerLine - 3) {
                        lines[2] = lastLine.substring(0, maxCharsPerLine - 3) + "...";
                    } else {
                        lines[2] = lastLine + "...";
                    }
                }
                
                // Draw centered lines
                int totalTextHeight = lines.size() * lineHeight;
                int startY = y + (cellHeight - totalTextHeight) / 2 + lineHeight - 2;
                
                for (int i = 0; i < lines.size(); i++) {
                    String line = lines[i];
                    int lineWidth = line.length() * charWidth;
                    int lineX = x + (cellWidth - lineWidth) / 2;
                    int lineY = startY + (i * lineHeight);
                    
                    display->setCursor(lineX, lineY);
                    display->print(line);
                }
            }
        }
        
        // Page indicator at bottom
        display->setTextColor(GxEPD_BLACK);
        display->setFont();
        display->setTextSize(1);
        display->setCursor(display->width() / 2 - 30, display->height() - 10);
        display->printf("Page %d/%d", currentPage + 1, selector.getTotalPages());
        
    } while (display->nextPage());
    
    lastSelectedRow = currentRow;
    lastSelectedCol = currentCol;
    lastPage = currentPage;
    
    Serial.printf("Book grid displayed (row=%d, col=%d, page=%d)\n", currentRow, currentCol, currentPage);
}
