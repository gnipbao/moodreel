"""Narration: a film's lines, voiced, placed on its timeline, and handed to the picture for its subtitles.

`narration.json` in the film:

  {"voice": "Samantha", "rate": 175,
   "lines": [{"id": "open", "at": 1.0, "text": "Every morning starts the same way."},
             {"id": "next", "gap": 0.5, "text": "Then it doesn't."},          (after the line before, 0.4 s by default)
             {"id": "hit", "cue": "title", "text": "Moodreel."}]}               (on a cue of the film's score.json)

`write` voices each line (macOS `say`, the system's voices; cached by voice, rate and text), lays the lines at their
times into `out/voice.wav` (the film's length), and writes `voice.js`: VOICE.lines with each line's start and end, and
line(t), the line being spoken at t, for the picture's subtitles. Lines that overlap or run past the film's end are
refused. A system voice is a draft voice: CREDITS says so, and a film for publication gets a voice licensed for it,
or a recorded reading (`--music`-style: put the recording's WAV at out/voice.wav and skip `write`).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np

SR = 48000
GAP = 0.4            # s between lines, unless a line says otherwise
SPEECH_DB = -16.0    # dBFS RMS the spoken parts are brought to: the voice is the mix's anchor, the music sits under it


def _say(text: str, voice: str, rate: int, cache: Path) -> Path:
    if not shutil.which("say"):
        raise SystemExit("no text-to-speech here: `say` is macOS's; elsewhere record the lines and put out/voice.wav in place")
    key = hashlib.sha256(f"say|{voice}|{rate}|{text}".encode()).hexdigest()[:16]
    wav = cache / f"{key}.wav"
    if not wav.exists():
        aiff = cache / f"{key}.aiff"
        subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", str(aiff), text], check=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(aiff), "-ac", "1", "-ar", str(SR), str(wav)], check=True)
        aiff.unlink()
    return wav


def _read(wav: Path) -> np.ndarray:
    from scipy.io import wavfile
    sr, x = wavfile.read(wav)
    assert sr == SR
    return x.astype(np.float32) / 32768.0


def write(film: Path) -> dict:
    from scipy.io import wavfile
    film = Path(film)
    spec = json.loads((film / "narration.json").read_text())
    f = json.loads((film / "film.json").read_text())
    cues = {}
    if (film / "score.json").exists():
        from .score.score import timeline
        cues = {c["name"]: c["t"] for c in timeline(json.loads((film / "score.json").read_text()))["cues"]}
    voice, rate = spec.get("voice", "Samantha"), int(spec.get("rate", 175))
    cache = film / "out" / "voice-cache"
    cache.mkdir(parents=True, exist_ok=True)
    track = np.zeros(int(f["duration"] * SR) + SR, np.float32)
    lines, end = [], 0.0
    for i, ln in enumerate(spec["lines"]):
        if "at" in ln:
            start = float(ln["at"])
        elif "cue" in ln:
            if ln["cue"] not in cues:
                raise SystemExit(f"line {ln.get('id', i)}: no cue {ln['cue']!r} in score.json")
            start = cues[ln["cue"]]
        else:
            start = end + float(ln.get("gap", GAP))
        audio = _read(_say(ln["text"], ln.get("voice", voice), int(ln.get("rate", rate)), cache))
        dur = len(audio) / SR
        if start < end - 1e-6:
            raise SystemExit(f"line {ln.get('id', i)} starts at {start:.2f} s, before the line before it ends ({end:.2f} s)")
        if start + dur > f["duration"]:
            raise SystemExit(f"line {ln.get('id', i)} runs to {start + dur:.2f} s, past the film's {f['duration']} s")
        i0 = int(round(start * SR))
        track[i0:i0 + len(audio)] += audio
        end = start + dur
        lines.append({"id": ln.get("id", f"l{i + 1}"), "text": ln["text"], "start": round(start, 3), "end": round(end, 3)})
    track = track[: int(f["duration"] * SR)]
    spoken = np.abs(track) > 1e-4
    if spoken.any():                                      # level the voice; a soft knee rather than clipping a peak
        gain = 10 ** (SPEECH_DB / 20) / float(np.sqrt(np.mean(track[spoken] ** 2)))
        track = np.tanh(track * gain / 0.95) * 0.95
    wavfile.write(film / "out" / "voice.wav", SR, (np.clip(track, -1, 1) * 32767).astype(np.int16))
    (film / "voice.js").write_text(
        "// Written by `moodreel voice` from narration.json: when each line is spoken, for the subtitles.\n"
        f"export const VOICE = {json.dumps({'voice': voice, 'lines': lines}, indent=1, ensure_ascii=False)};\n"
        "// the line being spoken at t, or null\n"
        "export const line = t => VOICE.lines.find(l => t >= l.start && t < l.end) || null;\n")
    credits = film / "CREDITS"
    note = (f"- Narration: system voice '{voice}' (macOS `say`), a draft voice: for publication use a voice licensed for "
            "it or a recorded reading\n")
    text = credits.read_text() if credits.exists() else ""
    if note not in text:
        credits.write_text(text + note)
    return {"wav": str(film / "out" / "voice.wav"), "js": str(film / "voice.js"), "lines": len(lines),
            "spoken_s": round(sum(ln["end"] - ln["start"] for ln in lines), 2)}
