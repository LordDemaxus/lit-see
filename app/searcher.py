from ebooklib import epub
from bs4 import BeautifulSoup
import ebooklib
import requests
import analyzer

def search_book(search_term):
    # Construct the search URL
    search_url = f"https://www.gutenberg.org/ebooks/search/?query={'+'.join(search_term.lower().split(' '))}&submit_search=Go%21"

    response = requests.get(search_url)

    # Check if request was successful
    if response.status_code != 200:
        print("Failed to access the webpage")
        return

    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    book_link = soup.find('li', class_='booklink')
    
    if not book_link:
        print("No books found on the page")
        return

    # Get the book's specific page URL
    book_url = "https://www.gutenberg.org" + book_link.find('a')['href']
    book_response = requests.get(book_url)
    book_soup = BeautifulSoup(book_response.content, 'html.parser')
    download_link = book_soup.find('a', string=lambda text: text and 'EPUB3' in text.upper())
    if not download_link:
        download_link = book_soup.find('a', string=lambda text: text and 'EPUB' in text.upper())
        if not download_link:
            print("No epub version exists for this book")
            return
    file_url = "https://www.gutenberg.org" + download_link['href']
    book_content = requests.get(file_url)
    temp_file = f"{'_'.join(search_term.split(' '))}.epub"
    with open(temp_file, 'wb') as file:
        file.write(book_content.content)
    print(f"EPUB downloaded successfully as '{temp_file}'")
    return(f"{temp_file}")

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
    return {'title': book.get_metadata('DC', 'title')[0][0], 'author': book.get_metadata('DC', 'creator')[0][0], 'text': text, 'tokens': len(analyzer.word_tokenize(text))}  # Separate sections with blank lines
