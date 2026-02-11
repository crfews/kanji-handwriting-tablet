from .card import Card
from .kana_card import KanaCard
from .kanji_card import KanjiCard
from .phrase_card import PhraseCard

def derive_card_type(c: Card) -> KanaCard | KanjiCard | PhraseCard:
    knc = KanaCard.by_card_id(c.id)
    kjc = KanjiCard.by_card_id(c.id)
    pc = PhraseCard.by_card_id(c.id)

    # There should only every be one type for a card
    only_one = (knc is not None and kjc is None and pc is None)\
               or (knc is None and kjc is not None and pc is None)\
               or (knc is None and kjc is None and pc is not None)
    assert only_one
    
    if knc:
        return knc
    elif kjc:
        return kjc
    elif pc:
        return pc
    raise ValueError('Could not associate card to derived type')
    
