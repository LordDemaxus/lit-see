import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import spacy

spacy.require_gpu()
nlp = spacy.load("en_core_web_trf")

nltk.download("punkt")

exclude_characters = {"gutenberg"}

def clean_text(text):
    words = word_tokenize(text)
    words = [word.lower() for word in words if word.isalnum()]
    return " ".join(words)

def extract_characters(text):
    doc = nlp(text)
    return [ent.text for ent in doc.ents if ent.label_ == "PERSON" and ent.text.lower() not in exclude_characters]
