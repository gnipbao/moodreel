"""Music as data: a drum loop's tempo, beats, bars and hits come out of the mix; lyrics and analyses made elsewhere come
in; kit/music.js answers by time (hits, the camera clock, words as sung); and the stage's motion blur streaks a moving
square that a single sample leaves sharp."""
from __future__ import annotations

import json
import shutil
import subprocess
import wave
from pathlib import Path

import numpy as np
import pytest

from moodreel.measure import music

REPO = Path(__file__).resolve().parents[1]
SR = 22050
BPM, FIRST, BARS = 120.0, 0.31, 10


def _loop(path: Path) -> dict:
    """Four on the floor: a kick on every beat, a snare on 2 and 4, hats on the eighths; a pad under it all."""
    period = 60 / BPM
    n = int((FIRST + BARS * 4 * period + 1) * SR)
    y = np.zeros(n)
    rng = np.random.default_rng(3)
    beats = FIRST + np.arange(BARS * 4) * period

    def put(t, x):
        i = int(t * SR)
        y[i:i + len(x)] += x[: n - i]
    tt = np.arange(int(0.25 * SR)) / SR
    kick = np.sin(2 * np.pi * (55 + 90 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 14)
    snare = rng.normal(0, 1, len(tt)) * np.exp(-tt * 22) * 0.5 + np.sin(2 * np.pi * 190 * tt) * np.exp(-tt * 25) * 0.3
    hat = np.diff(rng.normal(0, 1, int(0.05 * SR) + 1)) * np.exp(-np.arange(int(0.05 * SR)) / SR * 90) * 0.15
    for i, b in enumerate(beats):
        put(b, kick)
        if i % 4 in (1, 3):
            put(b, snare)
        put(b, hat)
        put(b + period / 2, hat)
    y += 0.05 * np.sin(2 * np.pi * 220 * np.arange(n) / SR)
    y = (y / np.abs(y).max() * 0.8 * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(SR), w.writeframes(y.tobytes())
    return {"beats": beats, "snares": beats[1::2]}


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
def test_a_drum_loop_gives_its_tempo_beats_bars_and_drums(tmp_path):
    truth = _loop(tmp_path / "loop.wav")
    d = music.analyse(tmp_path / "loop.wav")
    assert abs(d["bpm"] - BPM) < 0.05
    b = np.array(d["beats"])
    assert np.abs(truth["beats"][:, None] - b[None]).min(axis=1).max() < 0.012          # every beat within 12 ms
    assert abs(d["downbeats"][0] - FIRST) < 0.012                                         # bars start on beat 1
    kicks = music.match(d["onsets"]["kick"], [[t, 1] for t in truth["beats"]])
    snares = music.match(d["onsets"]["snare"], [[t, 1] for t in truth["snares"]])
    assert kicks["recall"] >= 0.9 and kicks["precision"] >= 0.9
    assert snares["recall"] >= 0.8 and snares["precision"] >= 0.8
    assert abs(len(d["features"]["rms"]) - d["duration"] * 100) <= 1


def test_lyrics_in_any_of_three_shapes_and_an_analysis_from_elsewhere_shifted(tmp_path):
    words = [{"w": "I'm", "start": 1.0, "end": 1.2}, {"w": "upping", "start": 1.2, "end": 1.6, "syl": [[1.2, 1.3], [1.3, 1.6]]}]
    shapes = [{"lines": [{"text": "I'm upping", "start": 1.0, "end": 1.6, "words": words}]},
              [{"text": "I'm upping", "start": 1.0, "end": 1.6, "words": words}], words]
    for i, s in enumerate(shapes):
        (tmp_path / f"l{i}.json").write_text(json.dumps(s))
        lines = music.load_lyrics(tmp_path / f"l{i}.json")
        assert lines[0]["words"][1] == {"w": "upping", "start": 1.2, "end": 1.6, "syl": [[1.2, 1.3], [1.3, 1.6]]}
        assert lines[0]["text"] == "I'm upping" and "syl" not in lines[0]["words"][0]   # syllables kept where the aligner gave them
    a = {"duration": 4.0, "bpm": 120.0, "fps": 100, "beats": [0.5, 1.0], "downbeats": [0.5], "sections": [],
         "onsets": {"kick": [[0.5, 0.9]]}, "rms": [0.1] * 400}
    (tmp_path / "audio.json").write_text(json.dumps(a))
    d = music.from_json(tmp_path / "audio.json", music.load_lyrics(tmp_path / "l2.json"), offset=0.05)
    assert d["beats"] == [0.55, 1.05] and d["onsets"]["kick"] == [[0.55, 0.9]] and d["features"]["rms"][0] == 0.1
    assert d["lyrics"][0]["words"][0]["start"] == pytest.approx(1.05)
    assert d["lyrics"][0]["words"][1]["syl"] == [[pytest.approx(1.25), pytest.approx(1.35)], [pytest.approx(1.35), pytest.approx(1.65)]]
    out = music.write_module(d, tmp_path / "music-data.js", "a test")
    src = out.read_text()
    assert json.loads(src.split("export const AUDIO = ")[1].split(";\n")[0])["bpm"] == 120.0


KIT_TEST = """
import { music, pop } from '__KIT__';
const AUDIO = { bpm: 120, fps: 100, beats: [0, 0.5, 1, 1.5, 2, 2.5, 3], downbeats: [0, 2], sections: [],
  onsets: { kick: [[0, 1], [0.5, 0.8], [1, 1]] }, features: { rms: Array.from({ length: 300 }, (_, i) => i / 300) } };
const LYRICS = [{ text: "I'm upping my P(doom)", start: 1.0, end: 2.0, words: [
  { w: "I'm", start: 1.0, end: 1.2 }, { w: 'upping', start: 1.2, end: 1.6 },
  { w: 'my', start: 1.6, end: 1.7 }, { w: 'P(doom)', start: 1.7, end: 2.0 }] }];
const M = music(AUDIO, LYRICS), lt = M.letters('upping', 1.1), sl = M.slams([1.0]);
console.log(JSON.stringify({
  sung: M.sung('upping', 1.1), notSung: M.sung('legend', 1.1), span: M.span("I'm upping", 0.9), doom: M.sung('p(doom)', 1.75),
  l0: lt(0), l6: lt(6), hit0: M.hit('kick', 0.5), hitLater: M.hit('kick', 0.6), hitNone: M.hit('snare', 0.5),
  ct: [0.5, 0.6, 0.75, 0.99].map(t => M.ct(t)), beat: M.beatAt(1.25), bar: M.barAt(3), env: M.env('rms', 1.5),
  line: M.line('upping my').text, slam0: sl(1.0).s, slamLater: sl(1.5).s, before: sl(0.9).s, pop0: pop(0).s, popEnd: pop(0.3).s,
}));
"""


@pytest.mark.skipif(shutil.which("node") is None, reason="needs node")
def test_kit_music_answers_by_time(tmp_path):
    script = tmp_path / "music.mjs"
    script.write_text(KIT_TEST.replace("__KIT__", (REPO / "kit" / "music.js").as_uri()))
    r = json.loads(subprocess.run(["node", str(script)], capture_output=True, text=True, check=True).stdout)
    assert r["sung"] == 1.2 and r["notSung"] == 1.1 and r["doom"] == 1.7            # punctuation and case don't matter
    assert r["span"] == {"w": "I'm upping", "start": 1.0, "end": 1.6}
    assert r["l0"] == 1.2 and abs(r["l6"] - 1.6) < 1e-9                               # the letters share the sung time
    assert r["hit0"] == 0.8 and 0.4 < r["hitLater"] < 0.45 and r["hitNone"] == 0
    ct = r["ct"]
    assert ct[0] == 0.5 and all(a < b for a, b in zip(ct, ct[1:])) and ct[1] - 0.5 > 0.1 and ct[3] < 1.0  # surges early
    assert r["beat"] == 2.5 and r["bar"] == 1.5 and abs(r["env"] - 0.5) < 0.01 and r["line"] == "I'm upping my P(doom)"
    assert r["slam0"] == pytest.approx(1.14) and 1 < r["slamLater"] < 1.03 and r["before"] == 1
    assert r["pop0"] == pytest.approx(1.2) and r["popEnd"] == 1


STAGE_PAGE = """<!doctype html><html><body><script type="module">
import { stage } from './stage.js';
stage({ width: 160, height: 90, duration: 1, background: '#000',
  draw: (g, t) => { g.fillStyle = '#fff'; g.fillRect(20 + 2400 * t, 30, 8, 30); },
  finish: (g, t, src) => { g.fillStyle = '#f00'; g.fillRect(0, 0, 4, 4); } });
</script></body></html>
"""
RENDER_OK = shutil.which("node") and shutil.which("ffmpeg") and (REPO / "node_modules" / "puppeteer-core").exists()


@pytest.mark.skipif(not RENDER_OK, reason="needs node, ffmpeg and npm install")
def test_the_stage_blurs_motion_across_the_shutter_and_finishes_once(tmp_path):
    page = tmp_path / "page"
    page.mkdir()
    shutil.copyfile(REPO / "kit" / "stage.js", page / "stage.js")
    (page / "index.html").write_text(STAGE_PAGE)
    greys = {}
    for name, extra in (("sharp", []), ("blurred", ["--samples", "8", "--shutter", "1"])):
        out = tmp_path / name
        subprocess.run(["node", str(REPO / "render" / "render.mjs"), "still", str(page), "0.02", "--size", "160x90", "--fps", "24",
                        "--out", str(out), *extra], check=True, capture_output=True)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(out / "t_0.02.jpg"), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, check=True).stdout
        img = np.frombuffer(raw, np.uint8).reshape(90, 160, 3).astype(int)
        greys[name] = img
    row = lambda img: img[45, :, 1]                                       # noqa: E731  (the green channel: no red dot)
    lit = lambda img: int(((row(img) > 10) & (row(img) < 215)).sum())     # noqa: E731  (partly covered pixels)
    assert lit(greys["sharp"]) <= 4                                       # a sharp square: its edges only
    assert lit(greys["blurred"]) >= 50          # 2400 px/s over 1/24 s: 8 copies of the square, an eighth as bright, over 100 px
    for img in greys.values():
        assert img[1, 1, 0] > 180 and img[1, 1, 1] < 80                   # finish drew once, over the averaged frame
