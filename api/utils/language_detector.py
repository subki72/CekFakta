"""
Language Detector — Auto-detect bahasa input (FR3.3).

Uses a simple heuristic approach based on common Indonesian stopwords.
This avoids adding heavy NLP libraries (keeping bundle size small for Vercel).
For mixed-language text (BR5), detects the dominant language.
"""

import re

# Common Indonesian stopwords/function words that rarely appear in English
INDONESIAN_MARKERS = {
    "yang", "dan", "di", "dari", "untuk", "dengan", "pada", "ini",
    "itu", "adalah", "ke", "akan", "juga", "sudah", "tidak", "bisa",
    "ada", "saya", "mereka", "kami", "kita", "telah", "oleh", "atau",
    "dalam", "karena", "bahwa", "tersebut", "menjadi", "seperti",
    "hanya", "lebih", "antara", "saat", "setelah", "tahun", "baru",
    "masih", "harus", "kata", "mengatakan", "pemerintah", "negara",
    "rakyat", "partai", "politik", "kebijakan", "presiden",
    "dia", "ia", "agar", "namun", "tetapi", "sedangkan", "serta",
    "jika", "maka", "hingga", "dapat", "perlu", "tentang",
}

# Common English function words (subset to distinguish from Indonesian)
ENGLISH_MARKERS = {
    "the", "is", "are", "was", "were", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "shall", "can", "must", "that", "which", "who",
    "whom", "this", "these", "those", "with", "from", "about", "into",
    "through", "during", "before", "after", "above", "between",
    "government", "president", "policy", "political", "because",
    "however", "therefore", "although", "whether", "their", "they",
}


def detect_language(text: str) -> str:
    """
    Detect whether text is primarily Indonesian or English.

    Args:
        text: Input text to analyze.

    Returns:
        'id' for Indonesian, 'en' for English.
    """
    words = re.findall(r"\b[\w-]+\b", text.lower())

    if not words:
        return "id"  # Default to Indonesian

    id_count = sum(1 for w in words if w in INDONESIAN_MARKERS)
    en_count = sum(1 for w in words if w in ENGLISH_MARKERS)

    # If both are zero (very short text or unusual vocabulary), default to Indonesian
    if id_count == 0 and en_count == 0:
        return "id"

    return "id" if id_count >= en_count else "en"
