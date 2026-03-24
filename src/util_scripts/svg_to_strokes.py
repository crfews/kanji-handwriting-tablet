################################################################################
# Imports
################################################################################

#from logic import drawing_utils
from svgpathtools import svg2paths2, Path as SvgPath
import argparse
from pathlib import Path
from typing import Generator
import numpy as np
from data import *

################################################################################
# Function Definitions
################################################################################



def _sample_svg_path(p: SvgPath, n: int) -> np.ndarray:
    if n <= 1:
        z = p.point(0.0)
        return np.array([[z.real, z.imag]], dtype=np.float32)

    total = p.length()
    assert total is not None
    total = float(total)

    if total <= 1e-6:
        z = p.point(0.0)
        return np.repeat(np.array([[z.real, z.imag]], dtype=np.float32), n, axis=0)

    ds = np.linspace(0.0, total, n, dtype=np.float32)
    pts = np.zeros((n*2,), dtype=np.float32)

    for i, d in enumerate(ds):
        t = p.ilength(d, s_tol=1e-4, maxits=50)
        z = p.point(t)
        pts[i*2] = float(z.real)
        pts[i*2 + 1] = float(z.imag)

    return pts



def svg_to_strokes(svg_path: str, points_per_stroke: int) -> list[list[float]]:
    s2p2 = svg2paths2(svg_path)
    svg_attrs = None
    paths = s2p2[0]
    attrs = s2p2[1]
    if len(s2p2) == 3:
        svg_attrs = s2p2[2]

    samps: list[np.ndarray] = []
    for p in paths:
        pts = _sample_svg_path(p, points_per_stroke)
        samps.append(pts)

    if not samps:
        return []
    
    return [list(s) for s in samps]


def cmd_one(args: argparse.Namespace) -> None:
    raise NotImplemented

def _char_from_filename(svg_path: Path) -> str | None:
    try:
        return chr(int(svg_path.stem, 16))
    except Exception:
        return

def cmd_batch(args: argparse.Namespace) -> None:
    svg_dir = Path(args.svg_dir)

    svgs = sorted(svg_dir.glob("*.svg"))

    
    if args.limit and args.limit > 0:
        svgs = svgs[:args.limit]

    kana = set([k.kana for k in KanaCard.every()])
    kanji = set([k.kanji for k in KanjiCard.every()])

    changed: list[KanaCard | KanjiCard] = []
    
    for p in svgs:
        c = _char_from_filename(p)
        if c not in kana and c not in kanji:
            continue
        
        strokes = svg_to_strokes(str(p), args.point_count)

        if c in kana:
            kc = KanaCard.by_kana(c)
            assert kc
            kc.drawing = Drawing.create(strokes, c)
        elif c in kanji:
            kc = KanjiCard.by_kanji(c)
            assert kc
            kc.drawing = Drawing.create(strokes, c)
        else:
            continue
        print(c)
        changed.append(kc)

    with maybe_connection_commit(None) as con:
        total = len(changed)
        count = 0
        for c in changed:
            print(f'{++count} / {total}')
            c.sync(con=con)

def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_one = sub.add_parser("one", help="Convert one SVG to JSON with strokes.")
    ap_one.add_argument("--svg", required=True)
    ap_one.add_argument("--point-count",
                        type=int,
                        default=32,
                        help="Points sampled per stroke path")
    ap_one.set_defaults(func=cmd_one)

    ap_batch = sub.add_parser("batch", help="Convert a folder of SVGs to JSONL.")
    ap_batch.add_argument("--svg-dir",
                          required=True)
    ap_batch.add_argument("--point-count",
                          type=int,
                          default=64)
    ap_batch.add_argument("--limit",
                          type=int,
                          default=0)
    ap_batch.set_defaults(func=cmd_batch)

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
