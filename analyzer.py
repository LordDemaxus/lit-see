import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import spacy

nlp = spacy.load("en_core_web_sm")

nltk.download("punkt")

def clean_text(text):
    words = word_tokenize(text)
    words = [word.lower() for word in words if word.isalnum()]
    return " ".join(words)

def extract_characters(text):
    doc = nlp(text)
    return [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
