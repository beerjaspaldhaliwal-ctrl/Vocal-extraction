"""Command-line interface: python -m vocal_extractor song.mp3 [options]"""

import argparse
import logging
import sys

from . import presets
from .pipeline import DEFAULT_MODEL_DIR, OUTPUT_FORMATS, ExtractionOptions, extract


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="vocal-extractor",
        description="Extract studio-quality vocal stems from any song.",
    )
    parser.add_argument("songs", nargs="+", help="audio/video files (mp3, wav, flac, m4a, mp4, ...)")
    parser.add_argument("-o", "--output", default="stems", help="output folder (default: ./stems)")
    parser.add_argument("-q", "--quality", choices=presets.QUALITY_MODES, default=presets.DEFAULT_QUALITY,
                        help="; ".join(f"{k}: {v['label']}" for k, v in presets.QUALITY_MODES.items()))
    parser.add_argument("--backing", action="store_true", help="also split lead vs backing vocals")
    parser.add_argument("--dereverb", action="store_true", help="also output a reverb/echo-free vocal")
    parser.add_argument("--four-stems", action="store_true", help="also split instrumental into drums/bass/other")
    parser.add_argument("--all", action="store_true", help="enable --backing, --dereverb and --four-stems")
    parser.add_argument("-f", "--format", choices=OUTPUT_FORMATS, default="wav", help="output format (default: wav)")
    parser.add_argument("--model-dir", default=DEFAULT_MODEL_DIR, help="where models are cached")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    opts = ExtractionOptions(
        quality=args.quality,
        split_backing=args.backing or args.all,
        dereverb=args.dereverb or args.all,
        four_stems=args.four_stems or args.all,
        output_format=args.format,
        model_dir=args.model_dir,
    )

    failed = 0
    for song in args.songs:
        print(f"\n=== {song} ===")
        try:
            outputs = extract(song, args.output, opts)
        except Exception as exc:  # keep going with the other songs
            print(f"FAILED: {exc}", file=sys.stderr)
            failed += 1
            continue
        for name, path in outputs.items():
            print(f"  {name:16s} -> {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
