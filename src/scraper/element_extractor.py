import re
from typing import Any, Dict, Optional

from selenium.webdriver.common.by import By


class ElementExtractor:

    @staticmethod
    def extract_listing_data(element, url: str) -> Optional[Dict[str, Any]]:
        try:
            parent = element
            for _ in range(3):
                parent = parent.find_element(By.XPATH, "..")

            title = ElementExtractor.extract_title(element)
            if not title:
                return None

            return {
                "url": url,
                "title": title,
                "price": ElementExtractor.extract_price(parent),
                "image_url": ElementExtractor.extract_image(parent),
                "location": ElementExtractor.extract_location(parent),
            }
        except:
            return None

    @staticmethod
    def extract_title(element) -> Optional[str]:
        try:
            img_elements = element.find_elements(By.TAG_NAME, "img")
            for img in img_elements:
                alt = img.get_attribute("alt")
                if alt and alt.strip():
                    # Skip if it's just a price (e.g., "£395" or "£1,250")
                    if re.match(r"^£\s*\d+(?:,\d{3})*$", alt.strip()):
                        continue
                    # Skip if it starts with price
                    if alt.strip().startswith("£"):
                        continue
                    # Remove location suffix (e.g., "Camera in Edinburgh")
                    title = re.sub(r"\s+in\s+[\w\s,]+$", "", alt)
                    return title.strip()
        except:
            pass
        return None

    @staticmethod
    def extract_price(element) -> Optional[float]:
        try:
            text_elements = element.find_elements(
                By.XPATH, ".//*[contains(text(), '£')]"
            )
            for elem in text_elements:
                match = re.search(r"£\s*(\d+(?:,\d{3})*)", elem.text)
                if match:
                    return float(match.group(1).replace(",", ""))
        except:
            pass
        return None

    @staticmethod
    def extract_image(element) -> Optional[str]:
        try:
            img_elements = element.find_elements(By.TAG_NAME, "img")
            for img in img_elements:
                src = img.get_attribute("src")
                if src and "fbcdn.net" in src:
                    return src
        except:
            pass
        return None

    @staticmethod
    def extract_location(element) -> Optional[str]:
        try:
            for line in element.text.split("\n"):
                if any(word in line.lower() for word in ["mile", "km", "away"]):
                    return line.strip()
        except:
            pass
        return None