"""Transcribe with open-source Whisper (faster-whisper, CPU, int8).

Usage: transcribe.py AUDIO OUT_BASE   → writes OUT_BASE.txt and OUT_BASE.srt
"""
import os
import sys
import time

from faster_whisper import WhisperModel

from common import SHOW_DIR, load_config


def ts(sec):
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main(audio, out_base):
    cfg = load_config()
    glossary = (SHOW_DIR / "glossary.txt").read_text().strip()
    prompt = f"{cfg['whisper_prompt']} {glossary}."

    started = time.time()
    model = WhisperModel(cfg["whisper_model"], device="cpu", compute_type="int8",
                         cpu_threads=os.cpu_count() or 4)
    segments, info = model.transcribe(
        audio, language=cfg["show"]["language"], beam_size=5, vad_filter=True,
        initial_prompt=prompt, condition_on_previous_text=False,
    )

    paragraphs, para, srt = [], [], []
    for i, seg in enumerate(segments, 1):
        text = seg.text.strip()
        if not text:
            continue
        srt.append(f"{i}\n{ts(seg.start)} --> {ts(seg.end)}\n{text}\n")
        para.append(text)
        if len(para) >= 6 and text.endswith((".", "?", "!")):
            paragraphs.append(" ".join(para))
            para = []
    if para:
        paragraphs.append(" ".join(para))

    with open(f"{out_base}.txt", "w") as f:
        f.write("\n\n".join(paragraphs) + "\n")
    with open(f"{out_base}.srt", "w") as f:
        f.write("\n".join(srt))
    print(f"Transcribed {info.duration/60:.1f} min of audio in {(time.time()-started)/60:.1f} min")


if __name__ == "__main__":
    main(*sys.argv[1:3])
