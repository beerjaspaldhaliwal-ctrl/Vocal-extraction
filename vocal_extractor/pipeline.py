"""Multi-stage separation pipeline.

song -> [vocals, instrumental]
          vocals       -> [lead_vocals, backing_vocals]   (optional)
          lead/vocals  -> [vocals_dry]                     (optional de-reverb)
          instrumental -> [drums, bass, other]             (optional)
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import presets

log = logging.getLogger("vocal_extractor")

DEFAULT_MODEL_DIR = os.environ.get(
    "VOCAL_EXTRACTOR_MODELS", str(Path.home() / ".cache" / "vocal-extractor" / "models")
)
OUTPUT_FORMATS = ("wav", "flac", "mp3")

# Stem labels that different models use for "the voice" vs "everything else".
_VOCAL_NAMES = {"vocals", "vocal", "voice", "lead", "lead vocals", "lead_vocals"}
_DRY_NAMES = {"noreverb", "no reverb", "dry", "no_reverb", "no echo", "noecho", "no-reverb"}

ProgressFn = Callable[[float, str], None]


@dataclass
class ExtractionOptions:
    quality: str = presets.DEFAULT_QUALITY
    split_backing: bool = False
    dereverb: bool = False
    four_stems: bool = False
    output_format: str = "wav"
    model_dir: str = DEFAULT_MODEL_DIR


def _stem_name(path: str) -> str:
    """audio-separator names outputs '<input>_(<Stem>)_<model>.<ext>'.

    Chained stages nest these names, so the last tag is this stage's stem.
    """
    tags = re.findall(r"_\(([^)]+)\)", Path(path).name)
    return tags[-1].strip().lower() if tags else ""


def _run(input_path: str, work_dir: str, model_dir: str, model: str | None = None,
         preset: str | None = None) -> dict[str, str]:
    """Separate one file with one model (or ensemble preset); return {stem: path}."""
    from audio_separator.separator import Separator  # heavy import, keep lazy

    out_dir = tempfile.mkdtemp(dir=work_dir)
    separator = Separator(
        log_level=logging.WARNING,
        model_file_dir=model_dir,
        output_dir=out_dir,
        output_format="WAV",
        ensemble_preset=preset,
    )
    separator.load_model() if preset else separator.load_model(model_filename=model)
    files = separator.separate(input_path)
    return {_stem_name(f): os.path.join(out_dir, os.path.basename(f)) for f in files}


def _pick(stems: dict[str, str], names: set[str]) -> tuple[str, str]:
    """Split a two-stem result into (matching stem, the other stem)."""
    hit = next((k for k in stems if k in names), None)
    if hit is None:
        raise RuntimeError(f"Unexpected stems from model: {sorted(stems)}")
    rest = [v for k, v in stems.items() if k != hit]
    return stems[hit], rest[0] if rest else ""


def _export(src: str, dst_no_ext: Path, fmt: str) -> str:
    dst = f"{dst_no_ext}.{fmt}"
    if fmt == "wav":
        shutil.copyfile(src, dst)
    else:
        codec = ["-c:a", "flac"] if fmt == "flac" else ["-c:a", "libmp3lame", "-b:a", "320k"]
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, *codec, dst], check=True)
    return dst


def extract(song: str, output_dir: str, options: ExtractionOptions | None = None,
            progress: ProgressFn | None = None) -> dict[str, str]:
    """Extract stems from ``song`` into ``output_dir/<song name>/``.

    Returns a mapping of stem name -> output file path.
    """
    opts = options or ExtractionOptions()
    if opts.quality not in presets.QUALITY_MODES:
        raise ValueError(f"quality must be one of {list(presets.QUALITY_MODES)}")
    if opts.output_format not in OUTPUT_FORMATS:
        raise ValueError(f"output_format must be one of {OUTPUT_FORMATS}")
    if not os.path.isfile(song):
        raise FileNotFoundError(song)

    steps = 1 + opts.split_backing + opts.dereverb + opts.four_stems
    done = 0

    def step(msg: str) -> None:
        log.info(msg)
        if progress:
            progress(done / steps, msg)

    os.makedirs(opts.model_dir, exist_ok=True)
    dest = Path(output_dir) / Path(song).stem
    dest.mkdir(parents=True, exist_ok=True)
    results: dict[str, str] = {}

    with tempfile.TemporaryDirectory() as work:
        # Normalise any input (mp3, m4a, video, ...) to 44.1 kHz stereo WAV.
        source = os.path.join(work, "input.wav")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", song, "-vn",
                        "-ar", "44100", "-ac", "2", source], check=True)

        mode = presets.QUALITY_MODES[opts.quality]
        step(f"Separating vocals: {mode['label']}")
        stems = _run(source, work, opts.model_dir, model=mode.get("model"), preset=mode.get("preset"))
        vocals, instrumental = _pick(stems, _VOCAL_NAMES)
        done += 1

        lead = vocals
        if opts.split_backing:
            step("Splitting lead and backing vocals")
            stems = _run(vocals, work, opts.model_dir, model=presets.KARAOKE_MODEL)
            lead, backing = _pick(stems, _VOCAL_NAMES)
            results["lead_vocals"] = lead
            results["backing_vocals"] = backing
            done += 1

        if opts.dereverb:
            step("Removing reverb / echo from vocals")
            stems = _run(lead, work, opts.model_dir, model=presets.DEREVERB_MODEL)
            dry, _ = _pick(stems, _DRY_NAMES)
            results["lead_vocals_dry" if opts.split_backing else "vocals_dry"] = dry
            done += 1

        if opts.four_stems:
            step("Splitting instrumental into drums / bass / other")
            stems = _run(instrumental, work, opts.model_dir, model=presets.FOUR_STEM_MODEL)
            for name in ("drums", "bass", "other"):
                if name in stems:
                    results[name] = stems[name]
            done += 1

        results = {"vocals": vocals, "instrumental": instrumental, **results}
        outputs = {name: _export(path, dest / name, opts.output_format)
                   for name, path in results.items()}

    if progress:
        progress(1.0, "Done")
    return outputs
