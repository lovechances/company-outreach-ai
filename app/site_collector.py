import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def fetch_html(url: str) -> str:
    response = requests.get(
        url,
        timeout=15,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()
    return response.text


def extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # remove obvious junk blocks if present
    for tag in soup(["nav", "footer", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    lines = []
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned:
            lines.append(cleaned)

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def find_priority_links(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []

    keywords = [
        "about",
        "pricing",
        "faq",
        "features",
        "feature",
        "product",
        "services",
        "service",
        "solutions",
    ]

    base_domain = urlparse(base_url).netloc

    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        full_url = urljoin(base_url, href)

        parsed = urlparse(full_url)

        if parsed.netloc != base_domain:
            continue

        path = parsed.path.lower()

        if any(word in path for word in keywords):
            links.append(full_url)

    # dedupe, preserve order
    seen = set()
    cleaned = []
    for link in links:
        if link not in seen:
            seen.add(link)
            cleaned.append(link)

    return cleaned[:5]


def collect_site(url: str) -> dict:
    try:
        homepage_html = fetch_html(url)
    except Exception as e:
        return {
            "tool": "collector",
            "status": "error",
            "message": f"Could not fetch homepage: {e}",
            "data": {
                "source_url": url,
                "pages": [],
                "combined_text": "",
                "usable": False,
            },
        }

    homepage_text = extract_text_from_html(homepage_html)
    links = find_priority_links(homepage_html, url)

    pages = [{
        "url": url,
        "label": "homepage",
        "text": homepage_text,
    }]

    for link in links:
        try:
            html = fetch_html(link)
            text = extract_text_from_html(html)

            label = urlparse(link).path.strip("/") or "page"

            pages.append({
                "url": link,
                "label": label,
                "text": text,
            })
        except Exception:
            continue

    combined_parts = []
    for page in pages:
        if page["text"]:
            combined_parts.append(f"[PAGE: {page['label']}]\n{page['text']}")

    combined_text = "\n\n".join(combined_parts)

    word_count = len(combined_text.split())

    page_count = len(pages)

    if word_count < 250:
        return {
            "tool": "collector",
            "status": "failed",
            "message": "Site did not yield enough usable text. It may be JS-rendered, blocked, or too thin.",
            "data": {
                "source_url": url,
                "pages": pages,
                "combined_text": combined_text,
                "usable": False,
                "word_count": word_count,
                "collection_status": "failed",
            },
        }

    collection_status = "full" if page_count >= 3 else "partial"

    return {
        "tool": "collector",
        "status": "ok",
        "message": f"Collected {page_count} page(s) with {word_count} words.",
        "data": {
            "source_url": url,
            "pages": pages,
            "combined_text": combined_text,
            "usable": True,
            "word_count": word_count,
            "collection_status": collection_status,
        },
    }