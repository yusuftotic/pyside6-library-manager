import requests
from bs4 import BeautifulSoup
import isbnlib

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'en-US,en;q=0.9,tr;q=0.8',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def scrape_amazon_book(isbn_code: str, headers: dict = None) -> dict:
    if headers is None:
        headers = DEFAULT_HEADERS

    canonical_isbn = isbnlib.canonical(isbn_code)
    
    if isbnlib.is_isbn13(canonical_isbn):
        isbn10_code = isbnlib.to_isbn10(canonical_isbn)
    elif isbnlib.is_isbn10(canonical_isbn):
        isbn10_code = canonical_isbn
    else:
        raise ValueError("You should enter a valid ISBN.")
    
    book_amazon_url = f"https://www.amazon.com/dp/{isbn10_code}"
    page = requests.get(url=book_amazon_url, headers=headers)
    soup = BeautifulSoup(page.text, "html.parser")

    title = ""
    author = ""
    publisher = ""
    publication_date = ""
    isbn10 = ""
    isbn13 = ""
    page_count = ""
    language = ""
    description = ""

    if soup.find(id="productTitle"):
        title = soup.find(id="productTitle").text.strip()

    if soup.find(class_="author") and soup.find(class_="author").a:
        author = soup.find(class_="author").a.text

    detail_bullets = soup.find(id="detailBullets_feature_div")
    if detail_bullets and detail_bullets.find("ul"):
        for i in detail_bullets.find("ul").find_all(class_="a-list-item"):
            spans = i.find_all("span")
            if len(spans) >= 2:
                key_text = spans[0].text
                val_text = spans[1].text
                
                if "Publisher" in key_text:
                    publisher = val_text
                elif "Publication date" in key_text:
                    publication_date = val_text
                elif "ISBN-10" in key_text:
                    isbn10 = val_text
                elif "ISBN-13" in key_text:
                    isbn13 = val_text
                elif "Print length" in key_text:
                    page_count = val_text
                elif "Language" in key_text:
                    language = val_text

    is_description = bool(soup.find(id="bookDescription_feature_div"))
    if is_description:
        description = soup.find(id="bookDescription_feature_div").text.strip().replace(" Read more", "")

    return {
        "title": title,
        "author": author,
        "publisher": publisher,
        "publication_date": publication_date,
        "isbn10": isbn10,
        "isbn13": isbn13,
        "page_count": page_count,
        "language": language,
        "description": description,
    }
