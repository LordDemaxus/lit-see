from ebooklib import epub
from bs4 import BeautifulSoup
import ebooklib
import requests

def extract_book_from_epub(filename):
    """Extract the text of a book from an epub file and return it"""
    book = epub.read_epub(filename)
    markdown_content = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), "html.parser")

            # Convert HTML to Markdown format
            for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
                level = int(h.name[1])  # Extract heading level (h1 -> 1, h2 -> 2)
                h.replace_with(f"{'#' * level} {h.get_text()}\n")

            for bold in soup.find_all(["b", "strong"]):
                bold.replace_with(f"**{bold.get_text()}**")

            for italic in soup.find_all(["i", "em"]):
                italic.replace_with(f"*{italic.get_text()}*")

            for li in soup.find_all("li"):
                li.insert_before("\n- ")
                li.unwrap()  # Remove list tags but keep text

            # Extract and clean text
            markdown_text = soup.get_text(separator="\n", strip=True)
            markdown_content.append(markdown_text)
    text = "\n\n".join(markdown_content)        
    return {'title': book.get_metadata('DC', 'title')[0][0], 'author': book.get_metadata('DC', 'creator')[0][0], 'text': text, 'sentiment': sentiment_analysis(text)}  # Separate sections with blank lines
