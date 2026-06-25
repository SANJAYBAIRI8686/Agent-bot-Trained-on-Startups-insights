import os
import re
import math
import logging
import docx
from collections import Counter
from typing import List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

# Standard English stop words to filter out for better keyword matching relevance
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few", "for",
    "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's",
    "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm",
    "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't",
    "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't",
    "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't",
    "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's",
    "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
    "yourselves"
}


def tokenize(text: str) -> List[str]:
    """
    Tokenizes text by lowercasing, finding alphanumeric words, and filtering stop-words.
    """
    words = re.findall(r'\b\w+\b', text.lower())
    return [w for w in words if w not in STOP_WORDS]


class BM25Searcher:
    """
    In-memory BM25 ranker for searching text chunks.
    """
    def __init__(self, corpus: List[Dict[str, Any]], k1: float = 1.5, b: float = 0.75):
        self.corpus = corpus
        self.k1 = k1
        self.b = b
        self.doc_len = [len(tokenize(doc["content"])) for doc in corpus]
        self.avg_doc_len = sum(self.doc_len) / len(corpus) if corpus else 1.0
        self.doc_freqs = []
        self.idf = {}
        self.nd = len(corpus)
        
        all_words = set()
        for doc in corpus:
            words = tokenize(doc["content"])
            self.doc_freqs.append(Counter(words))
            all_words.update(words)
            
        for word in all_words:
            n_q = sum(1 for df in self.doc_freqs if word in df)
            self.idf[word] = math.log((self.nd - n_q + 0.5) / (n_q + 0.5) + 1.0)
            
    def search(self, query: str, top_n: int = 10) -> List[Dict[str, Any]]:
        query_words = tokenize(query)
        if not query_words or self.nd == 0:
            return []
            
        scores = [0.0] * self.nd
        for i in range(self.nd):
            doc_len = self.doc_len[i]
            df = self.doc_freqs[i]
            for word in query_words:
                if word not in self.idf:
                    continue
                f = df.get(word, 0)
                scores[i] += self.idf[word] * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len))
        
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in ranked[:top_n]:
            if score > 0.0:
                results.append({
                    "title": self.corpus[idx]["essay_title"],
                    "url": self.corpus[idx]["source_file"],
                    "content": self.corpus[idx]["content"],
                    "score": score
                })
        return results


# Global singleton instance of the searcher
_searcher = None


def get_searcher() -> BM25Searcher:
    """
    Initializes and returns the singleton BM25Searcher instance.
    Loads and chunks all .docx files from the configured DOCX_DIR.
    """
    global _searcher
    if _searcher is not None:
        return _searcher
        
    logger.info("Initializing BM25 Docx Searcher...")
    
    # Resolve DOCX directory relative to the project root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    
    docx_dir = settings.DOCX_DIR
    if not os.path.isabs(docx_dir):
        docx_dir = os.path.join(project_root, docx_dir)
        
    logger.info(f"Scanning directory for .docx files: {docx_dir}")
    
    if not os.path.exists(docx_dir):
        logger.error(f"DOCX directory does not exist: {docx_dir}")
        _searcher = BM25Searcher([])
        return _searcher
        
    # Read and chunk all .docx files
    corpus = []
    try:
        docx_files = [f for f in os.listdir(docx_dir) if f.endswith(".docx") and not f.startswith("~$")]
    except Exception as e:
        logger.error(f"Failed to list directory {docx_dir}: {e}")
        docx_files = []
        
    if not docx_files:
        logger.warning(f"No .docx files found in directory: {docx_dir}")
        _searcher = BM25Searcher([])
        return _searcher
        
    for filename in docx_files:
        file_path = os.path.join(docx_dir, filename)
        try:
            logger.info(f"Parsing document: {file_path}")
            doc = docx.Document(file_path)
            
            # Group paragraphs by header (e.g. === Heading ===)
            essays = []
            current_essay = {"title": "Introduction", "paragraphs": []}
            
            for p in doc.paragraphs:
                text = p.text.strip()
                if not text:
                    continue
                match = re.match(r'^===\s*(.*?)\s*===', text)
                if match:
                    if current_essay["paragraphs"]:
                        essays.append(current_essay)
                    current_essay = {"title": match.group(1).strip(), "paragraphs": []}
                else:
                    current_essay["paragraphs"].append(text)
                    
            if current_essay["paragraphs"]:
                essays.append(current_essay)
                
            # Sliding window paragraph chunking with overlap & title enrichment
            for essay in essays:
                paragraphs = essay["paragraphs"]
                if not paragraphs:
                    continue
                
                i = 0
                n = len(paragraphs)
                while i < n:
                    chunk_paragraphs = []
                    current_len = 0
                    j = i
                    while j < n and current_len < 1200:
                        chunk_paragraphs.append(paragraphs[j])
                        current_len += len(paragraphs[j])
                        j += 1
                        
                    # Title enrichment: prepend the essay title for maximum keyword match relevance
                    content = f"Essay Title: {essay['title']}\n\n" + "\n\n".join(chunk_paragraphs)
                    
                    corpus.append({
                        "essay_title": essay["title"],
                        "source_file": filename,
                        "content": content
                    })
                    
                    if j >= n:
                        break
                        
                    # Calculate paragraph overlap index (up to ~250 chars)
                    overlap_len = 0
                    step_back = 0
                    for k in range(j - 1, i, -1):
                        overlap_len += len(paragraphs[k])
                        if overlap_len > 250:
                            break
                        step_back += 1
                        
                    if step_back > 0:
                        i = j - step_back
                    else:
                        i = j
        except Exception as e:
            logger.error(f"Error parsing .docx file {filename}: {e}", exc_info=True)
            
    logger.info(f"Initialized searcher index with {len(corpus)} chunks.")
    _searcher = BM25Searcher(corpus)
    return _searcher


def docx_search(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search the indexed .docx chunks for a query.
    Returns a list of dicts with: 'title', 'url', 'content'.
    """
    searcher = get_searcher()
    return searcher.search(query, top_n=max_results)
