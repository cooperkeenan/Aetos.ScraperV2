import os
import requests
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv(
    "ORCHESTRATOR_WEBHOOK_URL",
    "https://aetos-orchestrator-func-gycubdb8cxd0fsgs.uksouth-01.azurewebsites.net/api/webhooks/scraper/job-complete",
)
API_KEY = os.getenv("ORCHESTRATOR_API_KEY", "aetos-production-key-2024")

payload = {
    "job_id": "f8b7bd27-f844-4b62-a327-d81cc9c82ec6",
    "brands": ["Canon", "Nikon", "Sony"],
    "matches": [
        {
            "listing": {
                "url": "https://www.facebook.com/marketplace/item/123456789",
                "title": "Canon EOS 1300D DSLR Camera",
                "price": 150.0,
                "location": "Edinburgh, United Kingdom",
            },
            "product": {
                "id": 1,
                "brand": "Canon",
                "model": "1300D",
                "full_name": "Canon EOS 1300D",
            },
            "confidence": 88.0,
            "match_breakdown": {
                "title_score": 100.0,
                "price_score": 80.0,
                "keyword_score": 100.0,
            },
            "reasons": ["Exact model match: '1300D'"],
            "potential_profit": 50.0,
        }
    ],
}

print(f"Sending to: {WEBHOOK_URL}")
print(f"API Key: {API_KEY[:10]}...")
print()

response = requests.post(
    WEBHOOK_URL,
    json=payload,
    headers={"x-api-key": API_KEY},
    timeout=30,
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")