
import asyncio
import hashlib
import json

from urllib.parse import urljoin, urlparse, urldefrag

from playwright.async_api import async_playwright

from config import (
    BASE_URL,
    MAX_PAGES,
    REQUEST_DELAY,
    HTML_DIR
)


# def normalize_url(url):

#     url, _ = urldefrag(url)

#     return url.rstrip("/")


from urllib.parse import urlsplit, urlunsplit

def normalize_url(url):
    parsed = urlsplit(url)

    path = parsed.path.rstrip("/") or "/"

    return urlunsplit((
        parsed.scheme,
        parsed.netloc,
        path,
        parsed.query,
        parsed.fragment
    ))


def is_internal_url(url):

    base_domain = urlparse(BASE_URL).netloc
    parsed = urlparse(url)

    return (
        parsed.scheme in ("http", "https")
        and parsed.netloc == base_domain
    )


def get_filename(url):

    return hashlib.md5(
        url.encode()
    ).hexdigest() + ".html"


async def discover_links(page):

    links = await page.locator("a[href]").evaluate_all(
        """
        elements => elements.map(
            element => element.href
        )
        """
    )

    discovered = set()

    for link in links:

        if is_internal_url(link):
            discovered.add(normalize_url(link))

    return discovered


async def crawl_website():

    visited = set()
    queue = [normalize_url(BASE_URL + "#/home")]

    page_metadata = []

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True
        )

        context = await browser.new_context(
            viewport={
                "width": 1440,
                "height": 1000
            }
        )

        page = await context.new_page()

        while queue and len(visited) < MAX_PAGES:

            current_url = queue.pop(0)

            if current_url in visited:
                continue

            visited.add(current_url)

            try:

                print(f"\nCrawling: {current_url}")

                await page.goto(
                    current_url,
                    wait_until="domcontentloaded",
                    timeout=60000
                )

                # Allow SPA content to render
                await page.wait_for_timeout(2500)

                # Scroll to trigger lazy-loaded content
                for _ in range(3):

                    await page.evaluate(
                        "window.scrollTo(0, document.body.scrollHeight)"
                    )

                    await page.wait_for_timeout(700)

                # Capture the rendered HTML
                html = await page.content()

                filename = get_filename(current_url)

                html_path = HTML_DIR / filename

                html_path.write_text(
                    html,
                    encoding="utf-8"
                )

                page_metadata.append({
                    "url": current_url,
                    "html_file": filename,
                    "title": await page.title()
                })

                print(f"Saved HTML: {filename}")

                # Discover more internal pages
                new_links = await discover_links(page)

                for link in new_links:

                    if link not in visited and link not in queue:
                        queue.append(link)

                print(f"New links found: {len(new_links)}")
                print(f"Total pages discovered: {len(visited)}")

                await asyncio.sleep(REQUEST_DELAY)

            except Exception as error:

                print(
                    f"Error crawling {current_url}: {error}"
                )

        await browser.close()

    # Save crawl metadata
    metadata_path = HTML_DIR / "pages_metadata.json"

    metadata_path.write_text(
        json.dumps(page_metadata, indent=2),
        encoding="utf-8"
    )

    print("\nCrawling completed.")
    print(f"Total pages visited: {len(visited)}")

    return page_metadata
