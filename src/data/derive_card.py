from database import KANJI_CARD_KIND, KANA_CARD_KIND, PHRASE_CARD_KIND
from .card import Card
from .kana_card import KanaCard
from .kanji_card import KanjiCard
from .phrase_card import PhraseCard

def derive_card_type(c: Card) -> KanaCard | KanjiCard | PhraseCard:
    if c.kind == KANA_CARD_KIND:
        kc = KanaCard.by_card_id(c.id)
        if kc is None:
            raise ValueError(f"Card has valid kind of {c.kind} but no associated kana_card with card_id of {c.id}")
        return kc
    elif c.kind == KANJI_CARD_KIND:
        kjc = KanjiCard.by_card_id(c.id)
        if kjc is None:
            raise ValueError(f"Card has valid kind of {c.kind} but no associated kanji_card with card_id of {c.id}")
        return kjc
    elif c.kind == PHRASE_CARD_KIND:
        pc = PhraseCard.by_card_id(c.id)
        if pc is None:
            raise ValueError(f"Card has valid kind of {c.kind} but no associated phrase_card with card_id of {c.id}")
        return pc
    else:
        raise ValueError(f"Card has invalid kind of '{c.kind}'")
    
