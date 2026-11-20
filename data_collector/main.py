
import asyncio

from crawler import crawl_website
from extractor import extract_all_pages
from exporter import export_to_csv


async def main():

    print("=" * 60)
    print("DAR GLOBAL WEBSITE DATA EXTRACTION")
    print("=" * 60)

    # STEP 1: Crawl website and collect HTML
    metadata = await crawl_website()

    print(f"\nPages collected: {len(metadata)}")

    # STEP 2: Send HTML to OpenRouter
    records = await extract_all_pages(metadata)

    print(f"\nRecords extracted: {len(records)}")

    # STEP 3: Export CSV
    export_to_csv(records)

    print("\nPROCESS COMPLETED")


if __name__ == "__main__":

    asyncio.run(main())
