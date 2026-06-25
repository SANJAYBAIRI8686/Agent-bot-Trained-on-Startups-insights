import os
import re
import math
import logging
import docx
from collections import Counter
from typing import List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


def tokenize(text: str) -> List[str]:
    """
    Tokenizes text by lowercasing and finding all alphanumeric words.
    """
    return re.findall(r'\b\w+\b', text.lower())


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
                
            # Chunk essays into ~1200 character chunks
            for essay in essays:
                current_chunk = []
                current_len = 0
                for paragraph in essay["paragraphs"]:
                    current_chunk.append(paragraph)
                    current_len += len(paragraph)
                    if current_len >= 1200:
                        corpus.append({
                            "essay_title": essay["title"],
                            "source_file": filename,
                            "content": "\n\n".join(current_chunk)
                        })
                        current_chunk = []
                        current_len = 0
                if current_chunk:
                    corpus.append({
                        "essay_title": essay["title"],
                        "source_file": filename,
                        "content": "\n\n".join(current_chunk)
                    })
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
