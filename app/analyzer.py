import nltk
from collections import Counter, defaultdict
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.sentiment import SentimentIntensityAnalyzer

import torch
import ollama
from sentence_transformers import SentenceTransformer, util


import spacy

spacy.require_gpu()
nlp = spacy.load("en_core_web_trf")
embedder = SentenceTransformer("all-mpnet-base-v2")

nltk.download("punkt")
nltk.download("stopwords")
nltk.download('vader_lexicon')

EXCLUDE_CHARACTERS = {"gutenberg"}
MAX_CHUNK = 2000


def clean_text(text):
    """Cleans text and returns it for word analysis functions."""
    words = word_tokenize(text)
    words = [word.lower() for word in words if word.isalnum() and word not in set(stopwords.words("english"))]
    return words

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
    characters = [ent.text for ent in doc.ents if ent.label_ == "PERSON" and ent.text.lower() not in EXCLUDE_CHARACTERS]
    character_embeddings = embedder.encode(characters, convert_to_tensor=True)
    aliases = defaultdict(set)
    merged = set()
    for i, ent1 in enumerate(characters):
        if ent1 in merged:
            continue
        for j, ent2 in enumerate(characters):
            similarity = util.pytorch_cos_sim(character_embeddings[i], character_embeddings[j]).item()
            if similarity > 0.6:
                aliases[ent1].add(ent2)
                characters[j] = ent1
        merged.add(ent1)
    character_count = Counter(characters)
    sorted_characters = character_count.most_common()
    max_freq = max(character_count.values()) if character_count else 1
    min_freq = min(character_count.values()) if character_count else 1
    importance_score = lambda count: (count - min_freq) / (max_freq - min_freq) if max_freq != min_freq else 1
    return {character: [importance_score(count), aliases[character]] for character, count in sorted_characters}

def split_text_into_chunks(text, chunk_size=2000):
    """Splits text into overlapping chunks to preserve context."""
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_token_count = 0
    for sentence in sentences:
        sentence_token_count = len(word_tokenize(sentence))  # Token count per sentence
        if current_token_count + sentence_token_count > chunk_size:
            # Add current chunk to chunks list and reset for the next chunk
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]  # Start a new chunk with the current sentence
            current_token_count = sentence_token_count
        else:
            # Add the sentence to the current chunk
            current_chunk.append(sentence)
            current_token_count += sentence_token_count
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def summarize_text(text):
    prompt = f"Summarize the following text:\n\n{text}\n\nSummary:"
    outputs = ollama.chat(model="mistral:7b-instruct-v0.3-q4_K_M", messages=[{"role": "user", "content": prompt}])
    return outputs["message"]["content"].strip()

def summarize_book(text, chunk_size=2000):
    chunks = split_text_into_chunks(text, chunk_size=chunk_size)

    summaries = [summarize_text(chunk) for chunk in chunks]
    final_summary = " ".join(summaries)
    if len(final_summary.split()) > 200:
        final_summary = summarize_book(final_summary)
    return final_summary

def create_chunk_embeddings(text, total_tokens):
    chunk_size = max(MAX_CHUNK, total_tokens / 20)
    chunks = split_text_into_chunks(text, chunk_size=chunk_size)
    embeddings = embedder.encode(chunks, convert_to_tensor=True)
    return zip(chunks, embeddings.tolist())
