"""Web UI: upload a song in your browser and download the stems.

Run:  python app.py   (then open http://127.0.0.1:7860)
"""

import argparse
import tempfile

import gradio as gr

from vocal_extractor import ExtractionOptions, extract, presets

QUALITY_CHOICES = [(v["label"], k) for k, v in presets.QUALITY_MODES.items()]
STEMS = ["vocals", "instrumental", "lead_vocals", "backing_vocals", "vocals_dry",
         "lead_vocals_dry", "drums", "bass", "other"]


def run(song, quality, backing, dereverb, four_stems, fmt, progress=gr.Progress()):
    if not song:
        raise gr.Error("Please upload a song first.")
    out_dir = tempfile.mkdtemp(prefix="stems_")
    opts = ExtractionOptions(quality=quality, split_backing=backing, dereverb=dereverb,
                             four_stems=four_stems, output_format=fmt)
    outputs = extract(song, out_dir, opts, progress=lambda p, msg: progress(p, desc=msg))
    players = [gr.update(value=outputs.get(s), visible=s in outputs) for s in STEMS]
    return [*players, list(outputs.values())]


with gr.Blocks(title="Vocal Extractor") as demo:
    gr.Markdown("# Vocal Extractor\nUpload any song and get clean, studio-quality vocal stems.")
    with gr.Row():
        with gr.Column():
            song = gr.Audio(label="Song", type="filepath", sources=["upload"])
            quality = gr.Radio(QUALITY_CHOICES, value=presets.DEFAULT_QUALITY, label="Vocal model")
            backing = gr.Checkbox(label="Split lead vs backing vocals")
            dereverb = gr.Checkbox(label="Remove reverb / echo from vocals")
            four_stems = gr.Checkbox(label="Also split instrumental into drums / bass / other")
            fmt = gr.Radio(["wav", "flac", "mp3"], value="wav", label="Output format")
            go = gr.Button("Extract stems", variant="primary")
        with gr.Column():
            players = [gr.Audio(label=s.replace("_", " ").title(), visible=s in ("vocals", "instrumental"),
                                interactive=False) for s in STEMS]
            files = gr.File(label="Download all", file_count="multiple")
    go.click(run, [song, quality, backing, dereverb, four_stems, fmt], [*players, files])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--share", action="store_true", help="create a public link (useful on Colab)")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()
    demo.queue().launch(share=args.share, server_port=args.port)
