"""Sampled instruments: real recordings, played at any pitch and length.

The samples are a pinned subset of Versilian Studios Chamber Orchestra 2, Community Edition (CC0 1.0): upright piano,
strings (cello and violin sections, sustained), pizzicato, trumpet, horn, tuba, clarinet, marimba, glockenspiel, harp,
timpani hits and rolls. samples.json lists every file with its commit, size, SHA-256 and measured pitch
(scripts/vsco_samples.py builds it). They are not shipped: `moodreel samples fetch` downloads them (about 250 MB,
once, with the user's say-so) into ~/.moodreel/samples, and checks every file against the manifest.

A note takes the sample nearest its pitch, resampled to it (a shift of at most a few semitones), cut at its length
with the instrument's release and a short fade. The same score always draws the same audio.
"""
from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

import numpy as np

from .. import library

MANIFEST = Path(__file__).with_name("samples.json")
SR = 48000


def root() -> Path:
    return library.home() / "samples" / "vsco2ce"


@lru_cache(maxsize=1)
def manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def entries() -> list[dict]:
    return [e for fs in manifest()["instruments"].values() for e in fs]


def missing() -> list[dict]:
    """Files not on disk yet, or not the size the manifest says."""
    out = []
    for e in entries():
        p = root() / e["path"]
        if not p.exists() or p.stat().st_size != e["bytes"]:
            out.append(e)
    return out


def fetch(say=print) -> dict:
    """Download what is missing, at the pinned commit, and check every file's SHA-256."""
    src = manifest()["source"]
    raw = f"https://raw.githubusercontent.com/{src['repo'].split('github.com/')[1]}/{src['commit']}/"
    todo = missing()
    for k, e in enumerate(todo):
        p = root() / e["path"]
        p.parent.mkdir(parents=True, exist_ok=True)
        data = urllib.request.urlopen(raw + urllib.parse.quote(e["path"]), timeout=120).read()
        if hashlib.sha256(data).hexdigest() != e["sha256"]:
            raise SystemExit(f"{e['path']}: SHA-256 does not match the manifest; nothing written")
        p.write_bytes(data)
        say(f"[{k + 1}/{len(todo)}] {e['path']}")
    bad = [e["path"] for e in entries() if hashlib.sha256((root() / e["path"]).read_bytes()).hexdigest() != e["sha256"]]
    if bad:
        raise SystemExit(f"{len(bad)} sample files differ from the manifest (first: {bad[0]}); delete them and fetch again")
    return {"files": len(entries()), "downloaded": len(todo), "bytes": sum(e["bytes"] for e in entries()), "dir": str(root())}


def ready() -> bool:
    return MANIFEST.exists() and not missing()


def credit() -> str:
    s = manifest()["source"]
    return f"Instrument samples: {s['name']} ({s['license']}), {s['repo']} at {s['commit'][:7]}; {s['credit']}"


def read(path: Path) -> tuple[np.ndarray, int]:
    """A WAV file as mono float32 in [-1, 1] and its rate (16- and 24-bit PCM and float)."""
    import warnings

    from scipy.io import wavfile
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")                  # sampler chunks (smpl, LIST) are not audio
        sr, x = wavfile.read(path)
    if x.dtype.kind == "i":
        x = x.astype(np.float32) / float(np.iinfo(x.dtype).max)
    elif x.dtype.kind == "u":
        x = (x.astype(np.float32) - 128) / 128
    x = x.astype(np.float32)
    return (x.mean(axis=1) if x.ndim == 2 else x), int(sr)


@lru_cache(maxsize=256)
def _sample(path: str) -> tuple[np.ndarray, int]:
    x, sr = read(root() / path)
    peak = float(np.abs(x).max()) or 1.0
    return x / peak, sr                                   # every sample at full scale: the part sets the level


@lru_cache(maxsize=1024)
def _shifted(path: str, semis: float, length: int) -> np.ndarray:
    from scipy.signal import resample_poly
    x, sr = _sample(path)
    ratio = Fraction((SR / sr) / 2 ** (semis / 12)).limit_denominator(200)   # output samples per input sample
    need = int(length / float(ratio)) + 64
    y = resample_poly(x[:need], ratio.numerator, ratio.denominator).astype(np.float32)
    return y[:length]


def instruments() -> list[str]:
    return list(manifest()["instruments"])


def note(inst: str, midi: float, dur: float, level: float = 1.0) -> np.ndarray:
    """One note: the nearest sample shifted to midi, held dur seconds, then its release fading out."""
    fs = manifest()["instruments"].get(inst)
    if not fs:
        raise ValueError(f"no sampled instrument {inst!r}: one of {', '.join(instruments())}")
    e = min(fs, key=lambda e: (abs(e["midi"] - midi), e["midi"] < midi))   # ties: shift a sample down, not up
    rel = e["release"]
    n = int((dur + rel) * SR)
    y = _shifted(e["path"], round(float(midi - e["midi"]), 3), n).copy()
    fade = max(1, min(len(y), int(rel * SR)))
    start = max(0, len(y) - fade)
    y[start:] *= np.linspace(1, 0, len(y) - start) ** 2
    return y * level


def chord(inst: str, notes, dur: float, level: float = 1.0) -> np.ndarray:
    xs = [note(inst, m, dur, level) for m in notes]
    out = np.zeros(max(len(x) for x in xs), np.float32)
    for x in xs:
        out[:len(x)] += x
    return out / np.sqrt(len(xs))
