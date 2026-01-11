from dataclasses import dataclass
from typing import List, Dict, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize


@dataclass
class TfidfVectorStore:
    corpus: List[Dict[str, Any]]
    vectorizer: TfidfVectorizer
    matrix: Any  # scipy sparse

    @classmethod
    def from_corpus(cls, corpus: List[Dict[str, Any]]) -> "TfidfVectorStore":
        texts = [d["text"] for d in corpus]
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(texts)
        matrix = normalize(matrix)
        return cls(corpus=corpus, vectorizer=vectorizer, matrix=matrix)

    def search(self, query: str, top_k: int = 6) -> List[Dict[str, Any]]:
        qv = self.vectorizer.transform([query])
        qv = normalize(qv)

        scores = (self.matrix @ qv.T).toarray().ravel()
        idxs = np.argsort(scores)[::-1][:top_k]

        results = []
        for i in idxs:
            d = self.corpus[int(i)]
            results.append(
                {
                    "doc_id": d["doc_id"],
                    "title": d["title"],
                    "snippet": d["text"][:280],
                    "score": float(scores[int(i)]),
                    "metadata": d.get("metadata", {}),
                }
            )
        return results
