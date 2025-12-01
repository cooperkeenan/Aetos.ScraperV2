#include "TextFormatter.h"

String TextFormatter::cleanUTF8ToASCII(const String& content) {
    String cleaned = "";
    cleaned.reserve(content.length());  // Pre-allocate memory
    
    for (int i = 0; i < content.length(); i++) {
        unsigned char c = content[i];
        
        // UTF-8 3-byte sequence (starts with 0xE2)
        if (c == 0xE2 && i + 2 < content.length()) {
            unsigned char c2 = content[i + 1];
            unsigned char c3 = content[i + 2];
            
            char quoteReplacement;
            String punctReplacement;
            
            // Check for smart quotes
            if (isUTF8SmartQuote(c2, c3, quoteReplacement)) {
                cleaned += quoteReplacement;
                i += 2;
                continue;
            }
            
            // Check for dashes/ellipsis
            if (isUTF8Punctuation(c2, c3, punctReplacement)) {
                cleaned += punctReplacement;
                i += 2;
                continue;
            }
            
            // Unknown UTF-8 sequence - skip it
            i += 2;
            continue;
        }
        
        // Handle control characters
        if (c == '\n') {
            cleaned += '\n';
        }
        else if (c == '\r') {
            // Skip carriage returns
            continue;
        }
        else if (c == '\t') {
            cleaned += "    ";  // Tab to 4 spaces
        }
        // Only add printable ASCII (32-126)
        else if (c >= 32 && c <= 126) {
            cleaned += (char)c;
        }
        // Skip other non-printable characters
    }
    
    return cleaned;
}

bool TextFormatter::isUTF8SmartQuote(unsigned char c2, unsigned char c3, char& replacement) {
    if (c2 != 0x80) return false;
    
    switch (c3) {
        case 0x98:  // ' (left single quote)
        case 0x99:  // ' (right single quote)
            replacement = '\'';
            return true;
            
        case 0x9C:  // " (left double quote)
        case 0x9D:  // " (right double quote)
            replacement = '"';
            return true;
            
        default:
            return false;
    }
}

bool TextFormatter::isUTF8Punctuation(unsigned char c2, unsigned char c3, String& replacement) {
    if (c2 != 0x80) return false;
    
    switch (c3) {
        case 0x93:  // – (en dash)
        case 0x94:  // — (em dash)
            replacement = "-";
            return true;
            
        case 0xA6:  // … (ellipsis)
            replacement = "... ";
            return true;
            
        case 0xA2:  // • (bullet)
            replacement = "*";
            return true;
            
        default:
            return false;
    }
}