# Vocal Extractor

Upload any song and get **studio-quality vocal stems**, using the current
state-of-the-art open-source separation models (BS-Roformer / MelBand-Roformer
ensembles from the UVR / MVSEP community).

| Output | What it is |
|---|---|
| `vocals` | The full vocal stem (lead + harmonies) |
| `instrumental` | Everything except vocals |
| `lead_vocals` / `backing_vocals` | Lead singer separated from harmonies & backing (`--backing`) |
| `vocals_dry` / `lead_vocals_dry` | Vocal with reverb & echo removed (`--dereverb`) |
| `drums` / `bass` / `other` | Instrumental split further with Demucs HT-FT (`--four-stems`) |

## Fastest way: Google Colab (free GPU, nothing to install)

Open [`Vocal_Extractor_Colab.ipynb`](Vocal_Extractor_Colab.ipynb) in Google Colab,
choose *Runtime → Change runtime type → T4 GPU*, and run all cells. You get a
link to the web UI where you upload songs and download stems.

## Install locally

Requires Python 3.10+ and [ffmpeg](https://ffmpeg.org/download.html).

```bash
pip install -r requirements.txt
# NVIDIA GPU? use this instead for ~20x speed:
#   pip install "audio-separator[gpu]" audioread gradio
```

Models (~200–900 MB each) download automatically on first use into
`~/.cache/vocal-extractor/models` (override with `VOCAL_EXTRACTOR_MODELS`).

## Use it

### Web UI (upload in the browser)

```bash
python app.py            # then open http://127.0.0.1:7860
python app.py --share    # also creates a public link
```

### Command line

```bash
python -m vocal_extractor "my song.mp3"                 # vocals + instrumental
python -m vocal_extractor song.mp3 --all -f flac        # every stem, FLAC
python -m vocal_extractor *.mp3 -q clean --dereverb     # batch, cleanest vocals, dry
```

Stems are written to `stems/<song name>/`.

### Quality modes (`-q`)

| Mode | Models | Use when |
|---|---|---|
| `best` *(default)* | BS-Roformer Resurrection + MelBand Big Beta 6X, averaged | Best all-round vocal quality |
| `clean` | BS-Roformer Revive 2 + Kim FT2 bleedless, min-spectrum | You hear instruments in the vocal |
| `full` | BS-Roformer Revive 3e + becruily vocals, max-spectrum | Quiet harmonies, breaths or ad-libs get lost |
| `fast` | BS-Roformer Resurrection only | Quick previews, slow machines |

## Tips for the best results

- Feed it the **highest-quality source** you have (WAV/FLAC > 320k MP3 > YouTube rips).
- For an a cappella to use in a remix, try `-q clean --dereverb`.
- For AI voice training (RVC etc.), use `-q clean --backing --dereverb` and take `lead_vocals_dry`.
- Speed on CPU is roughly 5–10× the song length per model; a GPU makes a 4‑minute song take well under a minute.

## Python API

```python
from vocal_extractor import ExtractionOptions, extract

stems = extract("song.mp3", "stems", ExtractionOptions(quality="best", dereverb=True))
print(stems["vocals"], stems["vocals_dry"])
```
