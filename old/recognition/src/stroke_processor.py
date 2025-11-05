import shelve
import numpy as np
from numpy.typing import NDArray

# GLOBALS #####################################################################

SHELVE_NAME = 'recognizer.shelve'
#STROKE_CHUNK_COUNT = 3
STROKE_CHUNK_COUNT = 8

# FUNCTIONS ###################################################################


def chunk_line(line: list[float]) -> NDArray[np.float32]:
    x = np.array(line[0::2])
    y = np.array(line[1::2])

    assert x.size == y.size

    chunk_size = x.size // STROKE_CHUNK_COUNT
    start_inds = np.arange(STROKE_CHUNK_COUNT) * chunk_size
    chunk_lengths = np.full(STROKE_CHUNK_COUNT, chunk_size, dtype=int)
    chunk_lengths[-1] = x.size - (STROKE_CHUNK_COUNT - 1) * chunk_size

    x_sums = np.add.reduceat(x, start_inds)
    y_sums = np.add.reduceat(y, start_inds)
    x_means = x_sums / chunk_lengths
    y_means = y_sums / chunk_lengths

    out = np.empty(2 * STROKE_CHUNK_COUNT, dtype=np.float32)
    out[0::2] = x_means
    out[1::2] = y_means
    return out.tolist()


def process_strokes(lines: list[list[float]]):
    x_min = min([min(line[0::2]) for line in lines])
    x_max = max([max(line[0::2]) for line in lines])
    y_min = min([min(line[1::2]) for line in lines])
    y_max = max([max(line[1::2]) for line in lines])

    chunked_lines = np.array([chunk_line(line) for line in lines])

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


def shelve_stroke_key(stroke_count: int):
    return f'{stroke_count}-stroke-character'


def find_char(strokes: list[list[float]]) -> str:
    stroke_key = shelve_stroke_key(len(strokes))
    strokes = process_strokes(strokes)
    char = None

    with shelve.open(SHELVE_NAME) as db:
        lowest_sum = None

        for k in db[stroke_key]:
            val = db[stroke_key][k]

            sub_arr = np.absolute(val - strokes)
            sum = np.sum(sub_arr)

            if lowest_sum is None or lowest_sum > sum:
                char = k
                lowest_sum = sum

    return char


def shelve_char(char: str,
                strokes: list[list[float]],
                override=False):
    stroke_key = shelve_stroke_key(len(strokes))

    with shelve.open(SHELVE_NAME) as db:
        if stroke_key not in db:
            db[stroke_key] = {}

        if char not in db[stroke_key] or override:
            list_strokes = process_strokes(strokes)
            print(list_strokes)
            diction = db[stroke_key]
            diction[char] = list_strokes
            db[stroke_key] = diction
            db.sync()
        else:
            print('Char already exists! Call with'
                  ' override=True to overwrite')
        db.close()


def shelve_dump():
    with shelve.open(SHELVE_NAME) as db:
        for k in db:
            print(f'{k}:\t{db[k]}')
        db.close()
