import shelve
import numpy as np
import os
from numpy.typing import NDArray

# GLOBALS #####################################################################

_SHELVE_NAME = 'recognizer.shelve'
_db_open: bool = False

#### PRIVATE FUNCTIONS #########################################################

def _chunk_line(line: list[float], chunk_count: int) -> NDArray[np.float32]:
    """Takes a line of arbitrary length, and turns it into a numpy array of
    '_stroke_chunk_count' * 2 floats. Each odd float represents an average
    x point for each chunk and each even float represents an average y point
    for each chunk."""

    x = np.array(line[0::2])
    y = np.array(line[1::2])

    assert x.size == y.size

    chunk_size = x.size // chunk_count
    start_inds = np.arange(chunk_count) * chunk_size
    chunk_lengths = np.full(chunk_count, chunk_size, dtype=int)
    chunk_lengths[-1] = x.size - (chunk_count - 1) * chunk_size

    x_sums = np.add.reduceat(x, start_inds)
    y_sums = np.add.reduceat(y, start_inds)
    x_means = x_sums / chunk_lengths
    y_means = y_sums / chunk_lengths

    out = np.empty(2 * chunk_count, dtype=np.float32)
    out[0::2] = x_means
    out[1::2] = y_means
    return out.tolist()


def _process_strokes(strokes: list[list[float]], chunk_count: int):
        """Returns a 'chunked' average of a sequence of lines."""

        x_min = min([min(line[0::2]) for line in strokes])
        x_max = max([max(line[0::2]) for line in strokes])
        y_min = min([min(line[1::2]) for line in strokes])
        y_max = max([max(line[1::2]) for line in strokes])

        chunked_lines = np.array([_chunk_line(line, chunk_count) for line in strokes])

        for i in range(len(chunked_lines)):
            if (x_max - x_min) > 1:
                chunked_lines[i][0::2] -= x_min
                chunked_lines[i][0::2] /= x_max - x_min
            else:
                chunked_lines[i][0::2] = .5
            if (y_max - y_min) > 1:
                chunked_lines[i][1::2] -= y_min
                chunked_lines[i][1::2] /= y_max - y_min
            else:
                chunked_lines[i][1::2] = .5

        chunked_lines *= 100
        return chunked_lines.astype(np.int8)


def _open_db() -> shelve.DbfilenameShelf:
    global _db_open
    if _db_open:
        raise RuntimeError("'_open_db' may not be called if already open")
    _db_open = True
    
    shelve_path = os.path.abspath(__file__)
    print(shelve_path)
    shelve_path = os.path.dirname(shelve_path)
    shelve_path = os.path.join(shelve_path, _SHELVE_NAME)
    db = shelve.open(shelve_path)
    print(shelve_path)
    if 'characters' not in db:
        db['characters'] = {}
    if 'processed' not in db:
        db['processed'] = {}
    if 'chunk_count' not in db:
        db['chunk_count'] = 9

    return db


def _close_db(db: shelve.DbfilenameShelf):
    global _db_open
    if not _db_open:
        raise RuntimeError("'_close_db' may not be called if not open")
    db.sync()
    db.close()
    _db_open = False

def _close_db_no_sync(db: shelve.DbfilenameShelf):
    global _db_open
    if not _db_open:
        raise RuntimeError("'_close_db_no_sync' may not be called if not open")
    db.clear()
    db.close()
    _db_open = False


def _db_process_character(db: shelve.DbfilenameShelf, char: str) -> None:
    strokes = db['characters'][char]['raw']
    stroke_count = db['characters'][char]['stroke_count']
    chunk_count = db['chunk_count']

    # Process the character
    all_proc = db['processed']
    if stroke_count not in all_proc:
        all_proc[stroke_count] = {}

    all_proc[stroke_count][char] = _process_strokes(strokes, chunk_count)
    db['processed'] = all_proc

    
def add_character(char: str, strokes: list[list[float]]):
    print('called')
    db = _open_db()
    try:
        # Remove any data from the old instance if there
        if char in db['characters']:
            strk_cnt = db['characters'][char]['stroke_count']
            if strk_cnt in db['processed']:
                old_processed = db['processed']
                old_processed[strk_cnt].pop(char, None)
                db['processed'] = old_processed

        # Add the character
        characters = db['characters']
        characters[char] = {
            'stroke_count': len(strokes),
            'raw': strokes
        }
        db['characters'] = characters

        _db_process_character(db, char)
    except Exception as e:
        print(e)
    finally:
        _close_db(db)


def set_chunk_count(chunk_count: int):
    """Sets the chunk count of the database and reprocesses all characters
    if it changes"""
    
    db = _open_db()
    try:
        if db['chunk_count'] != chunk_count:
            db['processed'] = {}
            db['chunk_count'] = chunk_count

            chars = [k for k in db['characters']]

            for c in chars:
                _db_process_character(db, c)
    finally:
        _close_db(db)


def search_strokes(strokes: list[list[float]]) -> str | None:

    stroke_count = len(strokes)

    lowest_mean = None
    found_char = None

    db = _open_db()
    try:
        chunk_cnt = db['chunk_cnt']
        this_processed = _process_strokes(strokes, chunk_cnt)
        
        of_stroke_count = db['processed'][stroke_count]

        for k in of_stroke_count:
            val = of_stroke_count[k]
            sub_arr = np.absolute(val - this_processed)
            difference_mean = np.mean(sub_arr)

            if lowest_mean is None or lowest_mean > difference_mean:
                lowest_mean = difference_mean
                found_char = k
    finally:
        _close_db_no_sync(db)

    return found_char

    
    
