"""Clean a class recording for the podcast (approved preset "B · Balanced").

mono → trim dead air at start/end → rumble cut → noise reduction →
dynamic leveling (lifts quiet audience voices) → gentle compression →
two-pass loudness normalization to -16 LUFS → peak limiter → 64 kbps mono MP3.

Usage: clean_audio.py INPUT OUTPUT.mp3 STATS.json
"""
import json
import re
import subprocess
import sys

TRIM = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.5,"
        "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=1,areverse")
BALANCED = ("highpass=f=80,afftdn=nr=12:nf=-48:tn=1,"
            "dynaudnorm=f=400:g=21:p=0.9:m=10:s=8,"
            "acompressor=threshold=-20dB:ratio=3:attack=10:release=200:makeup=2")
LOUDNORM = "loudnorm=I=-16:TP=-1.5:LRA=11"
LIMITER = "alimiter=limit=0.75:attack=5:release=50:level=false"


def ffmpeg(*args):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", *args],
                          check=True, capture_output=True, text=True)


def last_json(text):
    return json.loads(re.findall(r"\{[^{}]*\}", text)[-1])


def main(src, out, stats_path):
    chain = f"aresample=48000,pan=mono|c0=0.5*c0+0.5*c1,{TRIM},{BALANCED}"

    # Pass 1: measure loudness after cleanup.
    r = ffmpeg("-i", src, "-vn", "-af", f"{chain},{LOUDNORM}:print_format=json", "-f", "null", "-")
    m = last_json(r.stderr)

    # Pass 2: apply measured normalization, limit peaks, encode.
    ln = (f"{LOUDNORM}:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
          f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
          f":offset={m['target_offset']}:linear=true")
    ffmpeg("-y", "-i", src, "-vn", "-af", f"{chain},{ln},{LIMITER},aresample=44100",
           "-ac", "1", "-c:a", "libmp3lame", "-b:a", "64k", "-id3v2_version", "3", out)

    # Measure the result so the pull request can show it.
    r = ffmpeg("-i", out, "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-")
    summary = r.stderr[r.stderr.rfind("Summary:"):]
    num = lambda key: float(re.search(rf"{key}:\s+(-?[\d.]+|-inf)", summary).group(1))
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out],
        check=True, capture_output=True, text=True).stdout.strip())
    stats = {
        "duration_seconds": round(dur),
        "loudness_lufs": num("I"),
        "loudness_range_lu": num("LRA"),
        "true_peak_dbfs": num("Peak"),
        "original_loudness_lufs": float(m["input_i"]),
    }
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main(*sys.argv[1:4])
