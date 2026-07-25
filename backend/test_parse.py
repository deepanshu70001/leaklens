import asyncio
import os
import sys

# Ensure backend directory is in path for imports to work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.extraction_service import parse_sms_text
from app.services.recurring_detector import detect_recurring

async def main():
    sms = """Your a/c XX8742 debited INR 299.00 on 20-Feb-2024 for AMAZON PRIME VIDEO. Avl bal: INR 52,340.75
Your a/c XX8742 debited INR 149.00 on 05-Feb-2024 for HOTSTAR SUBSCRIPTION. Avl bal: INR 52,489.75
Your a/c XX8742 debited INR 99.00 on 28-Jan-2024 for ZEE5.COM. Avl bal: INR 52,588.75"""
    txns = await parse_sms_text(sms)
    subs = detect_recurring(txns)
    print(f"Detected {len(subs)} subscriptions")
    for s in subs:
        print(s)

if __name__ == "__main__":
    asyncio.run(main())
