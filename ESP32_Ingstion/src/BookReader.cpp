#include "BookReader.h"
#include "Config.h"

bool BookReader::downloadBook(const String& bookId) {
    Serial.printf("Downloading book: %s\n", bookId.c_str());
    
    if (!downloadMetadata(bookId)) {
        Serial.println("Failed to download metadata");
        return false;
    }
    
    Serial.printf("Book: %s by %s\n", metadata.title.c_str(), metadata.author.c_str());
    Serial.printf("Total chapters: %d\n", metadata.totalChapters);
    
    String bookDir = "/books/" + bookId;
    if (!SD.exists(bookDir.c_str())) {
        SD.mkdir(bookDir.c_str());
    }
    
    File metaFile = SD.open((bookDir + "/meta.json").c_str(), FILE_WRITE);
    if (metaFile) {
        JsonDocument doc;
        doc["title"] = metadata.title;
        doc["author"] = metadata.author;
        doc["bookId"] = metadata.bookId;
        doc["totalChapters"] = metadata.totalChapters;
        serializeJson(doc, metaFile);
        metaFile.close();
    }
    
    String chapDir = bookDir + "/chapters";
    if (!SD.exists(chapDir.c_str())) {
        SD.mkdir(chapDir.c_str());
    }
    
    for (int i = 1; i <= metadata.totalChapters; i++) {
        Serial.printf("Downloading chapter %d/%d...", i, metadata.totalChapters);
        if (downloadChapter(bookId, i)) {
            Serial.println(" OK");
        } else {
            Serial.println(" FAILED");
            return false;
        }
        delay(500);
    }
    
    Serial.println("Download complete!");
    return true;
}

bool BookReader::downloadMetadata(const String& bookId) {
    HTTPClient http;
    
    String url = "https://firestore.googleapis.com/v1/projects/" + 
                 FIREBASE_PROJECT + "/databases/(default)/documents/books/" + bookId;
    
    Serial.printf("GET %s\n", url.c_str());
    http.begin(url);
    int code = http.GET();
    
    if (code != 200) {
        Serial.printf("HTTP %d\n", code);
        http.end();
        return false;
    }
    
    String payload = http.getString();
    http.end();
    
    JsonDocument doc;
    if (deserializeJson(doc, payload)) {
        Serial.println("JSON parse failed");
        return false;
    }
    
    metadata.title = doc["fields"]["title"]["stringValue"].as<String>();
    metadata.author = doc["fields"]["author"]["stringValue"].as<String>();
    metadata.bookId = bookId;
    metadata.totalChapters = doc["fields"]["total_chapters"]["integerValue"].as<int>();
    
    return true;
}

bool BookReader::downloadChapter(const String& bookId, int chapterNum) {
    HTTPClient http;
    
    String url = "https://firestore.googleapis.com/v1/projects/" + 
                 FIREBASE_PROJECT + "/databases/(default)/documents/books/" + 
                 bookId + "/chapters/" + String(chapterNum);
    
    Serial.printf("\nChapter %d: ", chapterNum);
    http.begin(url);
    http.setTimeout(10000);  // 10 second timeout
    
    unsigned long start = millis();
    int code = http.GET();
    unsigned long elapsed = millis() - start;
    
    Serial.printf("HTTP %d (%lu ms)\n", code, elapsed);
    
    if (code != 200) {
        http.end();
        return false;
    }
    
    String filename = "/books/" + bookId + "/chapters/" + String(chapterNum) + ".json";
    digitalWrite(EPD_CS, HIGH);
    
    File file = SD.open(filename.c_str(), FILE_WRITE);
    if (!file) {
        Serial.println("File open failed");
        http.end();
        return false;
    }
    
    // Get the entire response as a string (simpler, no streaming issues)
    String payload = http.getString();
    file.print(payload);
    file.close();
    http.end();
    
    Serial.printf("Saved %d bytes\n", payload.length());
    
    return payload.length() > 0;
}

bool BookReader::loadBook(const String& bookId) {
    String metaPath = "/books/" + bookId + "/meta.json";
    
    if (!SD.exists(metaPath.c_str())) {
        Serial.println("Book not found");
        return false;
    }
    
    File metaFile = SD.open(metaPath.c_str(), FILE_READ);
    if (!metaFile) return false;
    
    JsonDocument doc;
    deserializeJson(doc, metaFile);
    metaFile.close();
    
    metadata.title = doc["title"].as<String>();
    metadata.author = doc["author"].as<String>();
    metadata.bookId = doc["bookId"].as<String>();
    metadata.totalChapters = doc["totalChapters"];
    
    currentChapterNum = 1;
    currentPage = 0;
    globalPageNum = 0;
    
    return loadChapter(1);
}

bool BookReader::loadChapter(int chapterNum) {
    String path = "/books/" + metadata.bookId + "/chapters/" + String(chapterNum) + ".json";
    
    File file = SD.open(path.c_str(), FILE_READ);
    if (!file) {
        Serial.printf("Failed to open chapter %d\n", chapterNum);
        return false;
    }
    
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, file);
    file.close();
    
    if (error) {
        Serial.printf("Chapter parse failed: %s\n", error.c_str());
        return false;
    }
    
    // Firestore REST API wraps data in "fields" object
    // Each field has a type wrapper like {"stringValue": "actual content"}
    
    if (!doc["fields"]["content"]["stringValue"]) {
        Serial.println("No content field found");
        return false;
    }
    
    String content = doc["fields"]["content"]["stringValue"].as<String>();
    
    if (content.length() == 0) {
        Serial.println("Content is empty!");
        return false;
    }
    
    currentChapterContent = content;
    calculatePagination();
    
    Serial.printf("Loaded chapter %d: %d chars, %d pages\n", 
                  chapterNum, content.length(), totalPagesInChapter);
    return true;
}

void BookReader::calculatePagination() {
    totalPagesInChapter = (currentChapterContent.length() + CHARS_PER_PAGE - 1) / CHARS_PER_PAGE;
    if (totalPagesInChapter == 0) totalPagesInChapter = 1;
}

String BookReader::getCurrentPage() {
    int startPos = currentPage * CHARS_PER_PAGE;
    int endPos = min(startPos + CHARS_PER_PAGE, (int)currentChapterContent.length());
    return currentChapterContent.substring(startPos, endPos);
}

int BookReader::getCurrentPageNum() {
    return globalPageNum + 1;
}

int BookReader::getTotalPages() {
    return metadata.totalChapters * 10;
}

bool BookReader::nextPage() {
    if (currentPage + 1 < totalPagesInChapter) {
        currentPage++;
        globalPageNum++;
        return true;
    }
    
    if (currentChapterNum < metadata.totalChapters) {
        currentChapterNum++;
        currentPage = 0;
        globalPageNum++;
        return loadChapter(currentChapterNum);
    }
    
    return false;
}

bool BookReader::previousPage() {
    if (currentPage > 0) {
        currentPage--;
        globalPageNum--;
        return true;
    }
    
    if (currentChapterNum > 1) {
        currentChapterNum--;
        if (loadChapter(currentChapterNum)) {
            currentPage = totalPagesInChapter - 1;
            globalPageNum--;
            return true;
        }
    }
    
    return false;
}