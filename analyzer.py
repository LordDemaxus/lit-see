import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
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
    characters = [ent.text for ent in doc.ents if ent.label_ == "PERSON" and ent.text.lower() not in exclude_characters]
    character_count = Counter(characters)
    sorted_characters = character_count.most_common()
    max_freq = max(character_count.values()) if character_count else 1
    min_freq = min(character_count.values()) if character_count else 1
    importance_score = lambda count: (count - min_freq) / (max_freq - min_freq)
    return {character: importance_score(count) for character, count in sorted_characters}
