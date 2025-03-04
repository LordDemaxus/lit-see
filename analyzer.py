import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.sentiment import SentimentIntensityAnalyzer
from collections import Counter
import spacy

spacy.require_gpu()
nlp = spacy.load("en_core_web_trf")

nltk.download("punkt")
nltk.download("stopwords")
nltk.download('vader_lexicon')

exclude_characters = {"gutenberg"}

def clean_text(text):
    """Cleans text and returns it for word analysis functions."""
    words = word_tokenize(text)
    words = [word.lower() for word in words if word.isalnum() and word not in set(stopwords.words("english"))]
    return " ".join(words)

def sentiment_analyzer(text):
    """Cleans text and returns it for word analysis functions."""
    paragraphs = text.split('\n')
    Analyzer = SentimentIntensityAnalyzer()
    sentiment_score = sum([Analyzer.polarity_scores(para)['compound'] for para in paragraphs]) / len(paragraphs)
    return(sentiment_score)

def extract_characters(text):
    """Recognize and extract characters and sort them by importance_score which is a normalized frequency function.

    TODO: * Use sentiment analysis for sentences in which each character appears in as weights to better determine importance of character 
          * Remove redundant characters added due to missing last names eg. Tom and Tom Buchanan in The Great Gatsby
    """
    doc = nlp(text)
    characters = [ent.text for ent in doc.ents if ent.label_ == "PERSON" and ent.text.lower() not in exclude_characters]
    character_count = Counter(characters)
    sorted_characters = character_count.most_common()
    max_freq = max(character_count.values()) if character_count else 1
    min_freq = min(character_count.values()) if character_count else 1
    importance_score = lambda count: (count - min_freq) / (max_freq - min_freq) if max_freq != min_freq else 1
    return {character: importance_score(count) for character, count in sorted_characters}
