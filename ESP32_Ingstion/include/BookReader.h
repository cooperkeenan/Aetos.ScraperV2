#ifndef BOOK_READER_H
#define BOOK_READER_H

#include <Arduino.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <SD.h>

struct BookMetadata {
    String title;
    String author;
    String bookId;
    int totalChapters;
};

class BookReader {
public:
    bool downloadBook(const String& bookId);
    bool loadBook(const String& bookId);
    String getCurrentPage();
    bool nextPage();
    bool previousPage();
    int getCurrentPageNum();
    int getTotalPages();
    String getBookTitle() { return metadata.title; }
    
private:
    bool downloadMetadata(const String& bookId);
    bool downloadChapter(const String& bookId, int chapterNum);
    void calculatePagination();
    bool loadChapter(int chapterNum);
    
    BookMetadata metadata;
    String currentChapterContent;
    int currentChapterNum = 1;
    int currentPage = 0;
    int totalPagesInChapter = 0;
    int globalPageNum = 0;
    int totalGlobalPages = 0;
    
    const int CHARS_PER_LINE = 55;
    const int LINES_PER_PAGE = 20;
    const int CHARS_PER_PAGE = CHARS_PER_LINE * LINES_PER_PAGE;
};

#endif