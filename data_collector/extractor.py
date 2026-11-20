
import json
import asyncio

import httpx

from bs4 import BeautifulSoup
from pydantic import ValidationError

from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    HTML_DIR,
    EXTRACTED_DIR
)

from schemas import ExtractionResult


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


SYSTEM_PROMPT = """
You are an expert web data extraction system.

Your task is to extract ALL meaningful structured information
from the supplied HTML which contains information about Dar Global projects, news, and company details.

The HTML comes from the Dar Global website.

Instructions:

1. Identify and extract all meaningful and independent information blocks.
 

2. Extract all meaningful independent information blocks.

3. For project data, extract information such as:
   project name, developer, location, price, property types,
   description, amenities, payment plans, completion dates,
   and other available details.

4. For news data, extract:
   title, publication date, article content and other details.

5. For other information , extract:
   exract the relevant details

6. DO NOT inventing missing values.

7. Preserve original values and currencies.

8. Do not infer information that is not present in the HTML.

9. If a page contains multiple distinct informations,
   return multiple information blocks.

10. Ignore navigation menus, advertisements, cookie notices,
    footer links and generic UI elements unless they contain
    meaningful business information.

11. Return valid JSON only, following this structure:

{
    "infomation_blocks": [
        {
            "title": "Invented title which is suitable for representing the information block. The Title should be concise, descriptive and independant of other information blocks",
            "summarized_data": "Summarized data for the information block",
            "source_url": "Page URL"
        }
    ]
}

If no meaningful information is found, return:
{"infomation_blocks": []}

IMPORTANT: Do not include any additional text, explanations, or comments outside the JSON structure.

"""


def clean_html(html):

    soup = BeautifulSoup(html, "html.parser")

    for element in soup([
        "script",
        "style",
        "noscript",
        "svg"
    ]):
        element.decompose()

    return str(soup.body or soup)


async def extract_with_llm(
    client,
    html,
    source_url
):

    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is missing")

    cleaned_html = clean_html(html)

    # Keep request size manageable
    cleaned_html = cleaned_html[:60000]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "temperature": 0,
        "response_format": {
            "type": "json_object"
        },
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": (
                    f"Source URL: {source_url}\n\n"
                    "Extract all meaningful information "
                    "from this HTML:\n\n"
                    f"{cleaned_html}"
                )
            }
        ]
    }

    response = await client.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=120
    )

    print(f"LLM response status: {response.status_code}")
    # print(f"LLM response content: {response.text}...")

    response.raise_for_status()

    result = response.json()

    content = result["choices"][0]["message"]["content"]

    extracted_json = json.loads(content)
    print(f"Extracted JSON: {json.dumps(extracted_json, indent=2)}")

    # Validate using Pydantic
    validated = ExtractionResult.model_validate(
        extracted_json
    )
    print(f"Validated result: {validated.model_dump_json(indent=2)}")

    # Fill source URL when the model omits it
    for infomation_block in validated.infomation_blocks:

        if not infomation_block.source_url:
            infomation_block.source_url = source_url

    print(f"Final validated result: {str(validated)}")

    return validated


async def process_html_file(client, metadata):

    source_url = metadata["url"]

    html_path = HTML_DIR / metadata["html_file"]

    html = html_path.read_text(
        encoding="utf-8"
    )

    print(f"\nSending to LLM: {source_url}")

    try:

        result = await extract_with_llm(
            client,
            html,
            source_url
        )

        output_name = html_path.stem + ".json"

        output_path = EXTRACTED_DIR / output_name

        output_path.write_text(
            result.model_dump_json(indent=2),
            encoding="utf-8"
        )

        print(
            f"Extracted {len(result.infomation_blocks)} infomation_blocks"
        )

        return result.infomation_blocks

    except (ValidationError, json.JSONDecodeError) as error:

        print(f"Validation/JSON error: {error}")

    except Exception as error:

        print(f"Extraction failed: {error}")

    return []


async def extract_all_pages(metadata):

    all_infomation_blocks = []

    limits = httpx.Limits(
        max_connections=1,
        max_keepalive_connections=1
    )

    async with httpx.AsyncClient(
        limits=limits
    ) as client:

        for page_metadata in metadata:

            infomation_blocks = await process_html_file(
                client,
                page_metadata
            )

            all_infomation_blocks.extend(infomation_blocks)

            # Avoid overwhelming the API
            await asyncio.sleep(40)

    print("infomation blocks extracted from all pages", all_infomation_blocks)

    return all_infomation_blocks
