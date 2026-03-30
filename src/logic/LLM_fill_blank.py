from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
import os
import random
from typing import Optional

from data import Drawing, KanaCard, KanjiCard, PhraseCard
from data.helpers import is_kana, is_kanji

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional runtime dependency
    OpenAI = None

MODEL_NAME = os.getenv("OPENAI_FILL_BLANK_MODEL", os.getenv("OPENAI_MODEL", "gpt-5-mini"))
BLANK_CHAR = "_"
_ALLOWED_PUNCTUATION = set(" 　。、！？・ー〜「」『』（）()…-—")


@dataclass(slots=True)
class FillBlankExercise:
    sentence: str
    blanked_sentence: str
    answer: str
    english_meaning: str
    hint: str
    source: str


PhraseExample = tuple[str, str, str]


def _pick_phrase_text(card: PhraseCard) -> str:
    kp = (card.kanji_phrase or "").strip()
    if kp:
        return kp
    return (card.kana_phrase or "").strip()


@lru_cache(maxsize=1)
def _load_inventory() -> tuple[set[str], list[str], list[str], list[PhraseExample]]:
    kana_chars = sorted(
        {
            c.kana.strip()
            for c in KanaCard.in_db()
            if getattr(c, "kana", None) and len(c.kana.strip()) == 1
        }
    )
    kanji_chars = sorted(
        {
            c.kanji.strip()
            for c in KanjiCard.in_db()
            if getattr(c, "kanji", None) and len(c.kanji.strip()) == 1
        }
    )

    allowed_chars = set(kana_chars) | set(kanji_chars)

    phrase_examples: list[PhraseExample] = []
    seen_text: set[str] = set()
    for card in PhraseCard.in_db():
        text = _pick_phrase_text(card)
        if not text or text in seen_text:
            continue

        japanese_chars = [ch for ch in text if is_kana(ch) or is_kanji(ch)]
        if len(japanese_chars) < 2 or len(japanese_chars) > 12:
            continue
        if not all(ch in allowed_chars for ch in japanese_chars):
            continue

        phrase_examples.append(
            (
                text,
                (card.meaning or "").strip(),
                (card.grammar or "").strip(),
            )
        )
        seen_text.add(text)

    return allowed_chars, kana_chars, kanji_chars, phrase_examples


def _build_hint(answer: str) -> str:
    kc = KanjiCard.by_kanji(answer)
    if kc is not None:
        pieces: list[str] = []
        if kc.meaning:
            pieces.append(f"meaning: {kc.meaning}")
        readings = " / ".join(p for p in [kc.on_yomi, kc.kun_yomi] if p)
        if readings:
            pieces.append(f"reading: {readings}")
        return " • ".join(pieces) if pieces else "This blank is a kanji already in your database."

    kana = KanaCard.by_kana(answer)
    if kana is not None and getattr(kana, "romaji", None):
        return f"romaji: {kana.romaji}"

    return "Use one character already present in your study database."


def _is_allowed_sentence(sentence: str, allowed_chars: set[str]) -> bool:
    if not sentence:
        return False

    for ch in sentence:
        if ch in allowed_chars or ch in _ALLOWED_PUNCTUATION:
            continue
        if ch.isspace():
            continue
        if is_kana(ch) or is_kanji(ch):
            return False
        return False
    return True


def _has_saved_drawing(glyph: str) -> bool:
    matches = Drawing.by_glyph(glyph)
    return bool(matches)


def _candidate_answers(text: str, allowed_chars: set[str]) -> list[str]:
    chars = [ch for ch in text if ch in allowed_chars and (is_kana(ch) or is_kanji(ch))]
    preferred = [ch for ch in chars if is_kanji(ch)]

    preferred_with_drawings = [ch for ch in preferred if _has_saved_drawing(ch)]
    if preferred_with_drawings:
        return preferred_with_drawings

    chars_with_drawings = [ch for ch in chars if _has_saved_drawing(ch)]
    if chars_with_drawings:
        return chars_with_drawings

    return preferred or chars


def _fallback_exercise(
    phrase_examples: list[PhraseExample],
    allowed_chars: set[str],
    preferred_answer: Optional[str] = None,
    reason: str = "",
) -> FillBlankExercise:
    if not phrase_examples:
        raise ValueError("No short phrase cards were found in db.sqlite3.")

    pool = phrase_examples
    if preferred_answer:
        narrowed = [item for item in phrase_examples if preferred_answer in item[0]]
        if narrowed:
            pool = narrowed

    text, meaning, grammar = random.choice(pool)
    candidates = _candidate_answers(text, allowed_chars)
    if not candidates:
        raise ValueError("Could not find a valid blank character from the database.")

    answer = preferred_answer if preferred_answer in candidates else random.choice(candidates)
    blanked_sentence = text.replace(answer, BLANK_CHAR, 1)

    hint_parts: list[str] = []
    if grammar:
        hint_parts.append(grammar)
    hint_parts.append(_build_hint(answer))

    source = "Database fallback"
    if reason:
        source = f"{source} ({reason})"

    return FillBlankExercise(
        sentence=text,
        blanked_sentence=blanked_sentence,
        answer=answer,
        english_meaning=meaning or "",
        hint=" • ".join(part for part in hint_parts if part),
        source=source,
    )


def _request_openai_exercise(
    answer: str,
    related_examples: list[PhraseExample],
    kana_chars: list[str],
    allowed_chars: set[str],
) -> FillBlankExercise:
    if OpenAI is None:
        raise RuntimeError("The `openai` package is not available in this environment.")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    whitelist = sorted(
        {
            ch
            for text, _, _ in related_examples
            for ch in text
            if ch in allowed_chars and (is_kana(ch) or is_kanji(ch))
        }
    )

    if answer not in whitelist:
        whitelist.append(answer)

    if len(whitelist) < 14:
        extra_kana = random.sample(kana_chars, k=min(14 - len(whitelist), len(kana_chars)))
        whitelist.extend(ch for ch in extra_kana if ch not in whitelist)

    example_block = "\n".join(
        f"- {text} :: {meaning}" if meaning else f"- {text}"
        for text, meaning, _ in related_examples[:6]
    )

    prompt = f"""
        You are generating one beginner-friendly Japanese fill-in-the-blank exercise.

        Rules:
        - The missing answer must be exactly this one character: {answer}
        - Use ONLY Japanese characters from this database-derived whitelist: {''.join(whitelist)}
        - You may also use simple punctuation like 。、！？ and spaces
        - Keep the sentence short and natural (about 4 to 12 characters)
        - No romaji and no English in the sentence
        - The sentence must contain the answer character

        Database examples:
        {example_block}

        Required:
        {{
        "sentence": "short Japanese sentence",
        "answer": "{answer}",
        "english_meaning": "brief English meaning of the sentence",
        "hint": "short hint for the learner"
        }}
    """.strip()

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "FillBlankExercise",
                "schema": {
                    "type": "object",
                    "properties": {
                        "sentence": {"type": "string"},
                        "answer": {"type": "string"},
                        "english_meaning": {"type": "string"},
                        "hint": {"type": "string"},
                    },
                    "required": ["sentence", "answer", "english_meaning", "hint"],
                    "additionalProperties": False,
                },
            },
        },
        timeout=30,
    )

    payload = json.loads(response.choices[0].message.content)
    sentence = (payload.get("sentence") or "").strip()
    returned_answer = (payload.get("answer") or "").strip()
    english_meaning = (payload.get("english_meaning") or "").strip()
    hint = (payload.get("hint") or "").strip()

    if returned_answer != answer:
        raise ValueError("OpenAI returned a different answer character than requested.")
    if len(returned_answer) != 1 or returned_answer not in allowed_chars:
        raise ValueError("OpenAI returned an answer that is not in the database.")
    if returned_answer not in sentence:
        raise ValueError("OpenAI returned a sentence that does not include the answer.")
    if not _is_allowed_sentence(sentence, allowed_chars):
        raise ValueError("OpenAI returned characters that are not present in the database.")

    return FillBlankExercise(
        sentence=sentence,
        blanked_sentence=sentence.replace(returned_answer, BLANK_CHAR, 1),
        answer=returned_answer,
        english_meaning=english_meaning,
        hint=hint or _build_hint(returned_answer),
        source=f"OpenAI ({MODEL_NAME})",
    )


def generate_fill_blank_exercise() -> FillBlankExercise:
    """
    Build one short fill-in-the-blank exercise using only characters already
    present in db.sqlite3. OpenAI is used when available; otherwise it falls back
    to a short phrase already stored in the database.
    """
    allowed_chars, kana_chars, _, phrase_examples = _load_inventory()
    if not allowed_chars:
        raise ValueError("No kana or kanji cards were found in db.sqlite3.")

    if not phrase_examples:
        raise ValueError("No phrase cards are available for fill-in-the-blank practice.")

    seed_text, seed_meaning, _ = random.choice(phrase_examples)
    seed_candidates = _candidate_answers(seed_text, allowed_chars)
    if not seed_candidates:
        raise ValueError("Could not choose a database-backed character for practice.")

    answer = random.choice(seed_candidates)
    related_examples = [item for item in phrase_examples if answer in item[0]][:8]
    if not related_examples:
        related_examples = [random.choice(phrase_examples)]

    try:
        return _request_openai_exercise(answer, related_examples, kana_chars, allowed_chars)
    except Exception as exc:
        reason = str(exc).strip() or "OpenAI unavailable"
        if len(reason) > 120:
            reason = reason[:117] + "..."
        return _fallback_exercise(
            phrase_examples,
            allowed_chars,
            preferred_answer=answer,
            reason=reason,
        )
