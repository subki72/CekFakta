from api.utils.content_classifier import is_political_content
from api.utils.language_detector import detect_language


def test_detect_language_id():
    text = "Pemerintah dan DPR sedang membahas undang-undang baru hari ini."
    assert detect_language(text) == "id"

def test_detect_language_en():
    text = "The president and the government are discussing new policies today."
    assert detect_language(text) == "en"

def test_detect_language_mixed():
    text = "Pemerintah is doing something about the policy hari ini."
    # id words: pemerintah, hari, ini (but hari is not in marker, ini is)
    # en words: is, doing, something, about, the, policy
    assert detect_language(text) == "en"

def test_detect_language_empty():
    assert detect_language("") == "id"

def test_is_political_content_true():
    text = "Pemilu tahun ini sangat kompetitif dengan banyak partai yang berpartisipasi."
    assert is_political_content(text) == True

def test_is_political_content_false():
    text = "Resep nasi goreng ini sangat mudah dibuat dan lezat rasanya."
    assert is_political_content(text) == False

def test_is_political_content_density():
    # Long text with very few political words might still be true if absolute count >= 2
    text = "Buku ini bagus. " * 50 + " pemerintah presiden"
    assert is_political_content(text) == True

def test_is_political_content_empty():
    assert is_political_content("") is False


def test_is_political_content_with_punctuation():
    # Punctuation attached to political keywords should still be recognized
    text = "Presiden, Jokowi, dan jajaran menteri."
    assert is_political_content(text) is True

