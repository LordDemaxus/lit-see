import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download("punkt")
nltk.download("stopwords")

def clean_text(text):
    words = word_tokenize(text)
    words = [word.lower() for word in words if word.isalnum()]
    return " ".join(words)
