import logging
import re
from typing import Any, Dict, Optional

from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)


class ElementExtractor:

    @staticmethod
    def extract_listing_data(element, url: str) -> Optional[Dict[str, Any]]:
        try:
            # Get parent container
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
            aria_label = element.get_attribute("aria-label")
            if aria_label:
                return aria_label.strip()

            text = element.text.strip()
            if text:
                return text.split("\n")[0]

            return None
        except:
            return None

    @staticmethod
    def extract_price(element) -> Optional[float]:
        try:
            text_elements = element.find_elements(
                By.XPATH, ".//*[contains(text(), '£') or contains(text(), '$')]"
            )

            for text_elem in text_elements:
                text = text_elem.text.strip()
                price_match = re.search(r"[£$]?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)", text)
                if price_match:
                    return float(price_match.group(1).replace(",", ""))

            return None
        except:
            return None

    @staticmethod
    def extract_image(element) -> Optional[str]:
        try:
            img_elements = element.find_elements(By.TAG_NAME, "img")
            for img in img_elements:
                src = img.get_attribute("src")
                if src and "fbcdn.net" in src:
                    return src
            return None
        except:
            return None

    @staticmethod
    def extract_location(element) -> Optional[str]:
        try:
            text = element.text
            lines = text.split("\n")

            for line in lines:
                if any(word in line.lower() for word in ["mile", "km", "away"]):
                    return line.strip()

            return None
        except:
            return None
