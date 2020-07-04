from nltk.corpus import wordnet as wn
from typing import Any

def tag_to_int(tag: Any) -> int:
    return [
        wn.NOUN,
        wn.VERB,
        wn.ADJ,
        wn.ADV,
        ""
    ].index(tag)

def int_to_tag(integer: int) -> Any:
    return [
        wn.NOUN,
        wn.VERB,
        wn.ADJ,
        wn.ADV,
        ""
    ][integer]