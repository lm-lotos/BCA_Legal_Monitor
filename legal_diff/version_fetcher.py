import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pypdf import PdfReader
import os
from legal_diff.diff_renderer import render_diff


def fetch_document_page(url):
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        return soup

    except requests.RequestException:
        return None


def parse_bgbl_url(url):
    parts = url.rstrip("/").split("/")

    try:
        bgbl_index = parts.index("bgbl")

        part = parts[bgbl_index + 1]
        year = parts[bgbl_index + 2]
        number = parts[bgbl_index + 3]
        document_type = parts[bgbl_index + 4]

        return {
            "part": part,
            "year": year,
            "number": number,
            "document_type": document_type,
        }

    except (ValueError, IndexError):
        return None


def build_bgbl_id(url):
    document = parse_bgbl_url(url)

    if not document:
        return None

    part = {
        "1": "I",
        "2": "II",
    }.get(document["part"], document["part"])
    year = document["year"]
    number = document["number"]

    return f"BGBl. {year} {part} Nr. {number}"


def extract_document_text(url):
    soup = fetch_document_page(url)

    if soup is None:
        return None

    main = soup.find("main")

    if main is None:
        return None

    text = main.get_text(" ", strip=True)

    return text or None


def find_regulation_pdf(url):
    soup = fetch_document_page(url)

    if soup is None:
        return None

    for link in soup.find_all("a", href=True):
        label = link.get_text(" ", strip=True)

        if "Regelungstext" in label:
            href = str(link["href"])

            if href.startswith("http"):
                return href

            return urljoin(url, href)

    return None


def download_pdf(pdf_url):
    if not pdf_url:
        return None

    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()

        return response.content

    except requests.RequestException:
        return None
    

def extract_pdf_text(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text_parts = []

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text_parts.append(page_text)

        return "\n".join(text_parts)

    except Exception:
        return None

def save_pdf(pdf_data, filename):
    if not pdf_data:
        return None

    file_path = f"data/{filename}"

    with open(file_path, "wb") as file:
        file.write(pdf_data)

    return file_path


def extract_change_text(pdf_text):
    if not pdf_text:
        return None

    start_marker = "Artikel 1"
    end_marker = "Artikel 2"

    start = pdf_text.find(start_marker)
    end = pdf_text.find(end_marker, start)

    if start == -1:
        return None

    if end == -1:
        return pdf_text[start:].strip()

    return pdf_text[start:end].strip()


def identify_change_target(change_text):
    if not change_text:
        return None

    lines = [line.strip() for line in change_text.splitlines() if line.strip()]

    target = {
        "law": None,
        "section": None,
        "instruction": None,
    }

    for line in lines:
        if line.startswith("Änderung der "):
            target["law"] = line.replace("Änderung der ", "", 1).strip()

        if line.startswith("In Anlage "):
            target["section"] = line.split(" wird ", 1)[0].replace("In ", "", 1).strip()
            target["instruction"] = line

    return target


def fetch_current_section(section):
    if not section:
        return None

    section_slug = section.lower().replace(" ", "_")
    url = f"https://www.gesetze-im-internet.de/aufenthv/{section_slug}.html"

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.find("div", class_="jurAbsatz")

        if not content:
            return None

        return content.get_text("\n", strip=True)

    except requests.RequestException as error:
        print("CURRENT SECTION ERROR:", error)
        return None

    
def reconstruct_previous_section(current_text, instruction):
    if not current_text or not instruction:
        return None

    if '„Indien“ gestrichen' in instruction:
        marker = "Jordanien"

        if marker not in current_text:
            return None

        return current_text.replace(marker, f"Indien\n{marker}", 1)

    return None


def build_legal_comparison(url):
    pdf_url = find_regulation_pdf(url)

    if not pdf_url:
        return None

    pdf_data = download_pdf(pdf_url)

    if not pdf_data:
        return None

    saved_path = save_pdf(pdf_data, "temp_legal_change.pdf")

    if not saved_path:
        return None

    try:
        pdf_text = extract_pdf_text(saved_path)

        if not pdf_text:
            return None

        change_text = extract_change_text(pdf_text)
        change_target = identify_change_target(change_text)

        if not change_target:
            return None

        current_text = fetch_current_section(change_target.get("section"))

        if not current_text:
            return None

        previous_text = reconstruct_previous_section(
            current_text,
            change_target.get("instruction"),
        )

        if not previous_text:
            return None

        return {
            "old_text": previous_text,
            "new_text": current_text,
            "law": change_target.get("law"),
            "section": change_target.get("section"),
            "instruction": change_target.get("instruction"),
        }

    finally:
        if os.path.exists(saved_path):
            os.remove(saved_path)


if __name__ == "__main__":
    test_url = "https://www.recht.bund.de/bgbl/1/2026/161/VO"

    comparison = build_legal_comparison(test_url)

    print("\n--- LEGAL COMPARISON ---")
    print(comparison)
    