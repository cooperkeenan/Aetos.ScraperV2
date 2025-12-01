#ifndef TEXT_FORMATTER_H
#define TEXT_FORMATTER_H

#include <Arduino.h>

class TextFormatter {
public:
    static String cleanUTF8ToASCII(const String& content);
    
private:
    static bool isUTF8SmartQuote(unsigned char c2, unsigned char c3, char& replacement);
    static bool isUTF8Punctuation(unsigned char c2, unsigned char c3, String& replacement);
};

#endif