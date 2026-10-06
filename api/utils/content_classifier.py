"""
Content Classifier — Validate if text is a political narrative (BR4).

Rejects non-political content (recipes, poems, code, etc.) before
sending to the expensive Groq API. Uses keyword-based heuristic.
"""

import re

# Keywords that indicate political content (Indonesian & English)
POLITICAL_KEYWORDS_ID = {
    "pemerintah", "presiden", "menteri", "dpr", "dprd", "mpr",
    "partai", "politik", "kebijakan", "regulasi", "undang-undang",
    "pemilu", "pilkada", "pilpres", "legislatif", "eksekutif",
    "yudikatif", "koalisi", "oposisi", "parlemen", "kabinet",
    "anggaran", "apbn", "apbd", "kementerian", "gubernur",
    "bupati", "walikota", "caleg", "capres", "cawapres",
    "demokrasi", "reformasi", "oligarki", "konstitusi",
    "rakyat", "negara", "bangsa", "republik", "indonesia",
    "golkar", "pdip", "gerindra", "nasdem", "pks", "demokrat",
    "prabowo", "jokowi", "ganjar", "anies", "megawati",
    "omnibus", "kkn", "korupsi", "kpk", "mk", "ma",
    "kampanye", "buzzer", "hoax", "propaganda", "narasi",
    "perppu", "ruu", "uu", "perda", "peraturan",
}

POLITICAL_KEYWORDS_EN = {
    "government", "president", "minister", "parliament", "policy",
    "regulation", "election", "legislative", "executive", "judicial",
    "coalition", "opposition", "cabinet", "democracy", "constitution",
    "political", "politics", "politician", "senate", "congress",
    "indonesia", "jakarta", "campaign", "propaganda", "narrative",
    "corruption", "reform", "oligarchy", "populism", "authoritarian",
}

ALL_POLITICAL_KEYWORDS = POLITICAL_KEYWORDS_ID | POLITICAL_KEYWORDS_EN

# Minimum percentage of words that should be political keywords
MIN_POLITICAL_DENSITY = 0.02  # At least 2% of words should be political

def is_political_content(text: str) -> bool:
    """
    Check if text is likely about politics.

    Args:
        text: The text to classify.

    Returns:
        True if the text appears to be political content.
    """
    words = re.findall(r"\b[\w-]+\b", text.lower())

    if not words:
        return False

    political_count = sum(1 for w in words if w in ALL_POLITICAL_KEYWORDS)

    # Either absolute count (at least 2 political keywords) or density-based
    if political_count >= 2:
        return True

    density = political_count / len(words)
    return density >= MIN_POLITICAL_DENSITY

