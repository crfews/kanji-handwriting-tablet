import numpy as np
from scipy.spatial import procrustes
from numpy.typing import NDArray

def interpolate_line(line: list[float], point_count: int) -> NDArray[np.float32]:
    """Takes an alternating list of x and y values and returns a vector of
    2 * point_count values representing a stretched or compacted equivalent
    line"""
    x = np.array(line[0::2])
    y = np.array(line[1::2])

    assert x.size == y.size
    
    old_lin = np.linspace(0, 1, x.size)
    new_lin = np.linspace(0, 1, point_count)
    x = np.interp(new_lin, old_lin, x)
    y = np.interp(new_lin, old_lin, y)

    return np.stack([x,y],axis=1,dtype=np.float32)

def process_strokes(strokes: list[list[float]], point_count: int=100, size=100) -> NDArray[np.float32]:
    """Maps a sequence of lines onto a 'size' X 'size' 2D space where each line is comprised
    of point_count number of points or point_count * 2 x/y values."""
    normalized = np.array([interpolate_line(line,point_count) for line in strokes])
    mins = normalized.min(axis=(0,1))
    maxs = normalized.max(axis=(0,1))
    normalized = (normalized - mins) / (maxs - mins) * size
    return normalized.reshape(normalized.shape[0], -1)


def compare_drawings(
    drawing1: list[list[float]],
    drawing2: list[list[float]],
    point_count: int = 100,
    size: int = 100,
    stroke_order_weight: float = 0.5
) -> float:
    """
    Compares two drawings and returns a dissimilarity score where 0 is identical.
    
    Accounts for:
    - Per-stroke shape similarity (via Procrustes)
    - Stroke count difference
    - Stroke ordering
    
    stroke_order_weight controls how much penalty is applied for differing stroke counts.
    """
    strokes1 = process_strokes(drawing1, point_count, size)
    strokes2 = process_strokes(drawing2, point_count, size)

    n1, n2 = len(strokes1), len(strokes2)

    # Penalty for different number of strokes
    stroke_count_penalty = abs(n1 - n2) * stroke_order_weight

    # Compare only the strokes we have in common, in order
    common_strokes = min(n1, n2)
    disparities = []
    for i in range(common_strokes):
        s1 = strokes1[i].reshape(-1, 2)
        s2 = strokes2[i].reshape(-1, 2)
        _, _, disparity = procrustes(s1, s2)
        disparities.append(disparity)

    mean_disparity = np.mean(disparities) if disparities else 1.0

    return float(mean_disparity) + stroke_count_penalty
    
def bin_drawing_respose(
    drawing1: list[list[float]],
    drawing2: list[list[float]],
    good_ok_threshold=0.03,
    ok_bad_threshold=0.08) -> int:

    assert good_ok_threshold < ok_bad_threshold
    procrustes_grade = compare_drawings(drawing1, drawing2)

    if procrustes_grade < good_ok_threshold:
        return 0
    elif procrustes_grade < ok_bad_threshold:
        return 1
    else:
        return 2

# def chunk_line(line: list[float], chunk_count: int) -> NDArray[np.float32]:
#     """Takes a line of arbitrary length, and turns it into a numpy array of
#     '_stroke_chunk_count' * 2 floats. Each odd float represents an average
#     x point for each chunk and each even float represents an average y point
#     for each chunk."""

#     x = np.array(line[0::2])
#     y = np.array(line[1::2])

#     assert x.size == y.size

#     chunk_size = x.size // chunk_count
#     start_inds = np.arange(chunk_count) * chunk_size
#     chunk_lengths = np.full(chunk_count, chunk_size, dtype=int)
#     chunk_lengths[-1] = x.size - (chunk_count - 1) * chunk_size

#     x_sums = np.add.reduceat(x, start_inds)
#     y_sums = np.add.reduceat(y, start_inds)
#     x_means = x_sums / chunk_lengths
#     y_means = y_sums / chunk_lengths

#     out = np.empty(2 * chunk_count, dtype=np.float32)
#     out[0::2] = x_means
#     out[1::2] = y_means
#     return out



# def process_strokes(strokes: list[list[float]], chunk_count: int):
#         """Returns a 'chunked' average of a sequence of lines."""

#         x_min = min([min(line[0::2]) for line in strokes])
#         x_max = max([max(line[0::2]) for line in strokes])
#         y_min = min([min(line[1::2]) for line in strokes])
#         y_max = max([max(line[1::2]) for line in strokes])

#         chunked_lines = np.array([interpolate_line(line, chunk_count) for line in strokes])

#         for i in range(len(chunked_lines)):
#             if (x_max - x_min) > 1:
#                 chunked_lines[i][0::2] -= x_min
#                 chunked_lines[i][0::2] /= x_max - x_min
#             else:
#                 chunked_lines[i][0::2] = .5
#             if (y_max - y_min) > 1:
#                 chunked_lines[i][1::2] -= y_min
#                 chunked_lines[i][1::2] /= y_max - y_min
#             else:
#                 chunked_lines[i][1::2] = .5

#         chunked_lines *= 100
#         return chunked_lines.astype(np.int8)




def normalize_strokes(strokes: list[list[float]],
                      width: float,
                      height: float,
                      pad: float = 12.0,
                      keep_aspect: bool = True,
                      flip_y: bool = False) -> list[list[float]]:
    """
    Map raw strokes into [pad..width-pad] x [pad..height-pad].

    Input:  strokes = [[x0,y0,x1,y1,...], ...]
    Output: same structure, but mapped into target pixel space.
    """
    if width <= 0 or height <= 0:
        raise ValueError("width/height must be positive")

    # Validate + gather arrays
    arrays: list[np.ndarray] = []
    total_pts = 0
    for s in strokes:
        if len(s) % 2 != 0:
            raise ValueError("Each stroke must have even length: [x0,y0,x1,y1,...]")
        if len(s) == 0:
            arrays.append(np.empty((0, 2), dtype=np.float64))
            continue
        a = np.asarray(s, dtype=np.float64).reshape(-1, 2)  # (N,2)
        arrays.append(a)
        total_pts += a.shape[0]

    if total_pts == 0:
        return [list(s) for s in strokes]

    # Stack for global bounds
    all_pts = np.vstack([a for a in arrays if a.shape[0] > 0])  # (M,2)
    minxy = all_pts.min(axis=0)
    maxxy = all_pts.max(axis=0)
    span = maxxy - minxy

    # Drawable area
    W = float(width)
    H = float(height)
    inner_w = max(1.0, W - 2.0 * pad)
    inner_h = max(1.0, H - 2.0 * pad)

    # Degenerate cases: all points same or line-ish
    # We'll still scale by the non-degenerate axis if possible; otherwise center.
    eps = 1e-12
    span_x = float(span[0])
    span_y = float(span[1])

    if span_x < eps and span_y < eps:
        cx = W * 0.5
        cy = H * 0.5
        out: list[list[float]] = []
        for a in arrays:
            if a.shape[0] == 0:
                out.append([])
            else:
                b = np.empty_like(a)
                b[:, 0] = cx
                b[:, 1] = cy
                out.append(b.reshape(-1).tolist())
        return out

    # Compute scale
    if keep_aspect:
        sx = inner_w / max(span_x, eps)
        sy = inner_h / max(span_y, eps)
        s = min(sx, sy)
        sx = sy = s
    else:
        sx = inner_w / max(span_x, eps)
        sy = inner_h / max(span_y, eps)

    # Size after scaling (for centering)
    draw_w = span_x * sx
    draw_h = span_y * sy
    ox = pad + (inner_w - draw_w) * 0.5
    oy = pad + (inner_h - draw_h) * 0.5

    out_strokes: list[list[float]] = []
    for a in arrays:
        if a.shape[0] == 0:
            out_strokes.append([])
            continue

        b = a.copy()
        b[:, 0] = (b[:, 0] - minxy[0]) * sx
        b[:, 1] = (b[:, 1] - minxy[1]) * sy

        if flip_y:
            b[:, 1] = draw_h - b[:, 1]

        b[:, 0] += ox
        b[:, 1] += oy

        out_strokes.append(b.reshape(-1).tolist())

    return out_strokes
