"""Build moodreel/score/samples.json: the instrument samples `moodreel samples fetch` downloads.

The samples are Versilian Studios Chamber Orchestra 2, Community Edition (CC0 1.0, github.com/sgossner/VSCO-2-CE),
pinned to one commit. One dynamic layer and one round-robin per instrument keeps the set near 250 MB of the
library's 2.3 GB. The file names do not share one octave convention (the violins' lowest file is called G2, a violin's
lowest note is G3), so each sample's octave is measured: the lowest partial of its pitch class with real energy,
voted over each folder. Then its tuning: where the fundamental is clear and sits more than 25 cents from the named
note (a mislabelled file, an out-of-tune top key), the measured pitch is kept instead. Timpani carry no note names;
their pitch is the strongest peak between 70 and 220 Hz.

  uv run python scripts/vsco_samples.py          (downloads into ~/.moodreel/samples, writes the manifest)
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from moodreel.score.samples import read, root  # noqa: E402

REPO, COMMIT = "sgossner/VSCO-2-CE", "440300901dfe9275fd84e0b7763af1f8443ae62e"
RAW = f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/"
OUT = Path(__file__).resolve().parents[1] / "moodreel" / "score" / "samples.json"

# instrument: (folder, file pattern, release in seconds after the note ends)
PICK = {
    "piano": [("Keys/Upright Piano", r"Player_dyn2_rr1_\d+\.wav", 0.35)],
    "strings": [("Strings/Cello Section/susvib", r"susvib_.*_v3_1\.wav", 0.4),
                ("Strings/Violin Section/susVib", r"VlnEns_susVib_.*_v2\.wav", 0.4)],
    "pizz": [("Strings/Cello Section/pizzT", r"pizzT_.*_v2_RR1\.wav", 0.1),
             ("Strings/Violin Section/Pizz", r"VlnEns_Pizz_.*_v2_rr1\.wav", 0.1)],
    "trumpet": [("Brass/Trumpet/stac", r"Sum_SHTrumpet_stac_.*_v2_rr1\.wav", 0.08)],
    "horn": [("Brass/F Horn/stac", r"MOHorn_stac_.*_v2_rr1\.wav", 0.08)],
    "tuba": [("Brass/Tuba/stac", r"Tuba3_stac_.*_v2_rr1_Sum\.wav", 0.08)],
    "clarinet": [("Woodwinds/Clarinet/susLong", r"DCClar_susLong_.*_v2_rr1_sum\.wav", 0.15)],
    "marimba": [("Percussion/Marimba", r"Marimba_hit_.*\.wav", 0.2)],
    "glock": [("Percussion/Glock", r"glock_medium_.*\.wav", 0.4)],
    "harp": [("Strings/Harp", r"KSHarp_.*\.wav", 0.5)],
    "timpani": [("Percussion/Timpani", r"Timpani\d_Hit_v3_rr1_Sum\.wav", 0.6)],
    "timpani_roll": [("Percussion/Timpani/Rolls", r"Timpani\d_Roll_v3_rr1_Sum\.wav", 0.3)],
}
PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def named(path: str) -> int | None:
    """The MIDI note a file name says (C4 = 60), or None."""
    m = re.search(r"_([A-G])(#?)(-?\d)(?=_|\.wav)", path)
    return None if not m else 12 * (int(m[3]) + 1) + PC[m[1]] + (1 if m[2] else 0)


def spectrum(x: np.ndarray, sr: int) -> tuple[np.ndarray, np.ndarray]:
    a = int(0.08 * sr)
    seg = x[a:a + int(0.5 * sr)]
    mag = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), 1 << 16))
    return np.fft.rfftfreq(1 << 16, 1 / sr), mag


def octave_shift(x: np.ndarray, sr: int, midi: int) -> int:
    """How many octaves the true fundamental sits from the named note: the lowest octave with real energy."""
    f, mag = spectrum(x, sr)
    band = {}
    for k in range(-2, 3):
        f0 = 440 * 2 ** ((midi + 12 * k - 69) / 12)
        if 25 < f0 < 5000:
            band[k] = mag[(f > f0 * 0.975) & (f < f0 * 1.025)].max()
    top = max(band.values())
    return min(k for k, v in band.items() if v >= 0.12 * top)


def tuning(x: np.ndarray, sr: int, midi: float) -> float | None:
    """The measured pitch near midi (within 1.5 semitones), when the fundamental is clear and 25+ cents off."""
    f, mag = spectrum(x, sr)
    f0 = 440 * 2 ** ((midi - 69) / 12)
    win = (f > f0 * 2 ** (-1.5 / 12)) & (f < f0 * 2 ** (1.5 / 12))
    if mag[win].max() < 0.3 * mag.max():
        return None
    got = 69 + 12 * np.log2(f[win][np.argmax(mag[win])] / 440)
    return round(float(got), 2) if abs(got - midi) > 0.25 else None


def drum_pitch(x: np.ndarray, sr: int) -> float:
    f, mag = spectrum(x, sr)
    sel = (f > 70) & (f < 220)
    peak = f[sel][np.argmax(mag[sel])]
    return round(69 + 12 * np.log2(peak / 440), 2)


def main() -> None:
    tree = json.loads(urllib.request.urlopen(f"https://api.github.com/repos/{REPO}/git/trees/{COMMIT}?recursive=1").read())
    blobs = [x["path"] for x in tree["tree"] if x["type"] == "blob"]
    chart = urllib.request.urlopen(RAW + urllib.parse.quote("Keys/Upright Piano/MappingChart.txt")).read().decode()
    piano_key = {int(a): int(b) for a, b in re.findall(r"(\d{3})=(\d+)", chart)}
    dest = root()
    manifest = {"source": {"name": "Versilian Studios Chamber Orchestra 2, Community Edition",
                           "repo": f"https://github.com/{REPO}", "commit": COMMIT, "license": "CC0 1.0",
                           "credit": "Versilian Studios; upright piano by Simon Dalzell (Ivy Audio)"},
                "instruments": {}}
    for name, picks in PICK.items():
        files = []
        for folder, pattern, release in picks:
            group, shifts = [], []
            for p in sorted(b for b in blobs if b.rsplit("/", 1)[0] == folder and re.fullmatch(pattern, b.rsplit("/", 1)[1])):
                local = dest / p
                if not local.exists():
                    local.parent.mkdir(parents=True, exist_ok=True)
                    data = urllib.request.urlopen(RAW + urllib.parse.quote(p)).read()
                    local.write_bytes(data)
                data = local.read_bytes()
                x, sr = read(local)
                if name == "piano":
                    midi, how = piano_key[int(re.search(r"_(\d{3})\.wav$", p)[1])], "mapping chart"
                elif name.startswith("timpani"):
                    midi, how = drum_pitch(x, sr), "measured"
                else:
                    midi, how = named(p), "name"
                    shifts.append(octave_shift(x, sr, midi))
                group.append({"path": p, "midi": midi, "release": release, "bytes": len(data),
                              "sha256": hashlib.sha256(data).hexdigest(), "pitch_from": how})
            if shifts:                                    # one naming convention per folder: the vote
                vote = Counter(shifts).most_common(1)[0][0]
                print(f"{folder}: octave shifts {dict(Counter(shifts))} -> {vote:+d}")
                for e in group:
                    e["midi"] += 12 * vote
                    if vote:
                        e["pitch_from"] = f"name, {vote:+d} octave (measured)"
            for e in group:
                if not name.startswith("timpani"):
                    tuned = tuning(read(dest / e["path"])[0], read(dest / e["path"])[1], e["midi"])
                    if tuned is not None:
                        print(f"{e['path']}: listed {e['midi']}, measured {tuned}")
                        e["pitch_from"] += f"; tuned by measurement ({100 * (tuned - e['midi']):+.0f} cents)"
                        e["midi"] = tuned
            files += group
        manifest["instruments"][name] = sorted(files, key=lambda e: e["midi"])
    OUT.write_text(json.dumps(manifest, indent=1) + "\n")
    total = sum(e["bytes"] for fs in manifest["instruments"].values() for e in fs)
    print(f"{sum(len(v) for v in manifest['instruments'].values())} files, {total / 1e6:.0f} MB -> {OUT}")


if __name__ == "__main__":
    main()
