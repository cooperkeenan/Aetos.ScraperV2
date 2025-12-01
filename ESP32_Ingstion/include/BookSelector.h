#ifndef BOOK_SELECTOR_H
#define BOOK_SELECTOR_H

#include <Arduino.h>
#include <SD.h>
#include <ArduinoJson.h>
#include <vector>  

struct BookInfo {
    String bookId;
    String title;
    String author;
    bool isPlaceholder;
};

class BookSelector {
public:
    void init();
    void loadBooks();
    void moveUp();
    void moveDown();
    void moveLeft();
    void moveRight();
    void nextPage();
    void previousPage();
    
    int getSelectedRow() { return selectedRow; }
    int getSelectedCol() { return selectedCol; }
    int getCurrentPage() { return currentPage; }
    int getTotalPages() { return (books.size() + BOOKS_PER_PAGE - 1) / BOOKS_PER_PAGE; }
    
    BookInfo getSelectedBook();
    void getBooksOnCurrentPage(BookInfo* pageBooks, int& count);
    
private:
    static const int ROWS = 4;
    static const int COLS = 3;
    static const int BOOKS_PER_PAGE = ROWS * COLS;
    
    std::vector<BookInfo> books;
    int selectedRow = 0;
    int selectedCol = 0;
    int currentPage = 0;
    
    void loadBooksFromSD();
    void addPlaceholders();
};

#endif