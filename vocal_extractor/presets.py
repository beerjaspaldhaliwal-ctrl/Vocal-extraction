"""Model choices for each stage of the pipeline.

All models are open-source checkpoints from the UVR / MVSEP community and are
downloaded automatically the first time they are used.
"""

# Stage 1: split the song into vocals + instrumental.
# Ensembles come from audio-separator's built-in presets and combine two
# state-of-the-art Roformer models for cleaner, fuller vocals than either alone.
QUALITY_MODES = {
    "best": {
        "preset": "vocal_balanced",
        "label": "Best overall (BS-Roformer Resurrection + MelBand Big Beta 6X ensemble)",
    },
    "clean": {
        "preset": "vocal_clean",
        "label": "Cleanest - least instrument bleed (Revive 2 + Kim FT2 bleedless, min-FFT)",
    },
    "full": {
        "preset": "vocal_full",
        "label": "Fullest - keeps breaths, harmonies & ad-libs (Revive 3e + becruily, max-FFT)",
    },
    "fast": {
        "model": "bs_roformer_vocals_resurrection_unwa.ckpt",
        "label": "Fast - single BS-Roformer model (about 2x quicker)",
    },
}

DEFAULT_QUALITY = "best"

# Stage 2 (optional): split the vocal stem into lead and backing vocals.
KARAOKE_MODEL = "mel_band_roformer_karaoke_becruily.ckpt"

# Stage 3 (optional): remove reverb / echo from the (lead) vocal.
DEREVERB_MODEL = "dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt"

# Stage 4 (optional): split the instrumental into drums / bass / other.
FOUR_STEM_MODEL = "htdemucs_ft.yaml"
