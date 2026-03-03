from data import Drawing

def grade_strokes(s: list[list[float]], target_glyph: str, top_n: int = 20) -> int:
    assert top_n >= 1
    canidates = [d.glyph for d in Drawing.by_strokes_fuzzy(s,top_n)]

 
    if top_n == 1:
        if target_glyph in canidates:
            return 0
        else:
            return 2
    elif top_n == 2:
        if target_glyph == canidates[0]:
            return 0
        elif target_glyph == canidates[1]:
            return 1
        else:
            return 2
    else:
        if target_glyph in canidates[:top_n//2]:
            return 0
        elif target_glyph in canidates[top_n//2:]:
            return 1
        else:
            return 2
