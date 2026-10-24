"""Style embeddings (CSD): a vector per picture that is near for pictures in one style, whatever they show.

CSD (Somepalli et al., "Measuring Style Similarity in Diffusion Models", 2024; github.com/learn2phoenix/CSD) is a
CLIP ViT-L/14 image encoder trained so that pictures in one style land near each other: the style vector is the
encoder's class token, after its final layer norm, times a learned 1024 x 768 projection, made unit length. Two
pictures' style similarity is the dot product of their vectors.

The weights are the authors' (huggingface.co/tomg-group-umd/CSD-ViT-L, CC BY 4.0, pinned below). They are not
shipped: `moodreel csd setup` downloads them once (2.4 GB, with the user's say-so) and keeps the image encoder and
style projection as a 0.6 GB half-precision file in ~/.moodreel/models/csd; the download is deleted afterwards. The
encoder runs here in numpy, with no deep-learning framework: preprocessing as the authors' (shortest side to 224,
bicubic; centre crop 224; CLIP's mean and deviation), then the ViT-L/14 forward pass (QuickGELU, layer norm eps
1e-5), computed in float32.
"""
from __future__ import annotations

import hashlib
import pickle
import urllib.request
import zipfile
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

from .. import library

NAME = "CSD ViT-L/14 (tomg-group-umd/CSD-ViT-L @ 5bc26a6)"
URL = "https://huggingface.co/tomg-group-umd/CSD-ViT-L/resolve/5bc26a6fb0487f3f00a2a7313135103a005b1b67/pytorch_model.bin"
SHA256 = "40e92fad63a361b8136100cd234c42d401ef9b34ff1748234318929ebcc7e7a1"
SIZE, PATCH, WIDTH, LAYERS, HEADS = 224, 14, 1024, 24, 16
MEAN = np.array([0.48145466, 0.4578275, 0.40821073], np.float32)
STD = np.array([0.26862954, 0.26130258, 0.27577711], np.float32)


def home() -> Path:
    return library.home() / "models" / "csd"


def weights() -> Path:
    return home() / "csd-vit-l-style.npz"


def ready() -> bool:
    return weights().exists()


# --- reading the PyTorch checkpoint without PyTorch -------------------------------------------------------------
# A torch .bin is a zip: data.pkl (the object tree) and data/<key> (raw tensor storages). The unpickler below builds
# only lazy descriptions of tensors; any other class the pickle names becomes an inert stub, so nothing in the file
# runs as code.

DTYPES = {"FloatStorage": np.float32, "HalfStorage": np.float16, "BFloat16Storage": None, "DoubleStorage": np.float64,
          "LongStorage": np.int64, "IntStorage": np.int32, "ShortStorage": np.int16, "CharStorage": np.int8,
          "ByteStorage": np.uint8, "BoolStorage": np.bool_}


class _Stub:
    def __init__(self, *a, **k):
        pass

    def __setstate__(self, state):
        pass


class _Lazy:
    def __init__(self, key, dtype, offset, size, stride):
        self.key, self.dtype, self.offset, self.size, self.stride = key, dtype, offset, tuple(size), tuple(stride)


class _Dict(dict):                                     # an OrderedDict: state dicts carry a _metadata attribute
    pass


def _rebuild_tensor(storage, offset, size, stride, *rest):
    key, dtype = storage
    return _Lazy(key, dtype, offset, size, stride)


def _rebuild_parameter(data, *rest):
    return data


class _Unpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if (module, name) == ("torch._utils", "_rebuild_tensor_v2"):
            return _rebuild_tensor
        if (module, name) == ("torch._utils", "_rebuild_parameter"):
            return _rebuild_parameter
        if (module, name) == ("collections", "OrderedDict"):
            return _Dict
        if module == "torch" and name in DTYPES:
            return name
        return _Stub

    def persistent_load(self, pid):
        kind, storage_type, key, _location, _numel = pid
        if kind != "storage" or storage_type not in DTYPES or DTYPES[storage_type] is None:
            raise pickle.UnpicklingError(f"unsupported storage {pid!r}")
        return key, DTYPES[storage_type]


def _materialise(z: zipfile.ZipFile, prefix: str, t: _Lazy) -> np.ndarray:
    raw = np.frombuffer(z.read(f"{prefix}data/{t.key}"), dtype=t.dtype)
    if not t.size:
        return raw[t.offset:t.offset + 1].reshape(()).copy()
    item = raw.itemsize
    return np.lib.stride_tricks.as_strided(raw[t.offset:], shape=t.size, strides=[s * item for s in t.stride]).copy()


def read_checkpoint(path: Path) -> dict[str, np.ndarray]:
    """The model's state dict from a torch .bin, as numpy arrays (the 'module.' prefix dropped)."""
    with zipfile.ZipFile(path) as z:
        pkl = next(n for n in z.namelist() if n.endswith("data.pkl"))
        prefix = pkl[: -len("data.pkl")]
        tree = _Unpickler(z.open(pkl)).load()
        sd = tree.get("model_state_dict", tree) if isinstance(tree, dict) else tree
        return {k.removeprefix("module."): _materialise(z, prefix, v) for k, v in sd.items() if isinstance(v, _Lazy)}


def convert(sd: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """The encoder and the style projection, matrices in float16 (the rest float32)."""
    out = {}
    for k, v in sd.items():
        if k.startswith("backbone."):
            out[k.removeprefix("backbone.")] = v
        elif k == "last_layer_style":
            out["style_proj"] = v
    expect = 3 + 2 + 2 + LAYERS * 12 + 1                   # embeddings, ln_pre, ln_post, the blocks, the projection
    if len(out) != expect or out["style_proj"].shape != (WIDTH, 768):
        raise SystemExit(f"checkpoint: expected {expect} encoder arrays and a 1024 x 768 style projection, got {len(out)}")
    return {k: v.astype(np.float16 if v.ndim >= 2 and v.size > 100_000 else np.float32) for k, v in out.items()}


def setup(say=print) -> Path:
    """Download the weights (pinned, checked), keep the encoder and style projection, delete the download."""
    if ready():
        return weights()
    home().mkdir(parents=True, exist_ok=True)
    src = home() / "pytorch_model.bin"
    if not src.exists():
        say(f"downloading {URL} (2.4 GB) ...")
        part = src.with_suffix(".part")
        with urllib.request.urlopen(URL, timeout=600) as r, open(part, "wb") as f:
            while chunk := r.read(1 << 22):
                f.write(chunk)
        part.rename(src)
    h = hashlib.sha256()
    with open(src, "rb") as f:
        while chunk := f.read(1 << 24):
            h.update(chunk)
    if h.hexdigest() != SHA256:
        raise SystemExit(f"{src}: SHA-256 {h.hexdigest()} is not the pinned {SHA256}; delete it and run setup again")
    say("converting ...")
    arrays = convert(read_checkpoint(src))
    tmp = home() / "csd-vit-l-style.tmp.npz"
    np.savez(tmp, **arrays)
    tmp.rename(weights())
    src.unlink()
    return weights()


# --- the encoder ----------------------------------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _params() -> dict[str, np.ndarray]:
    if not ready():
        raise SystemExit("style embeddings are not set up: run `moodreel csd setup` (downloads 2.4 GB once)")
    with np.load(weights()) as z:
        return {k: z[k].astype(np.float32) for k in z.files}


def preprocess(rgb: np.ndarray) -> np.ndarray:
    """The authors' eval transform: shortest side to 224 (bicubic), centre crop 224, CLIP normalisation."""
    im = Image.fromarray(np.asarray(rgb, np.uint8)).convert("RGB")
    w, h = im.size
    if w <= h:
        size = (SIZE, int(SIZE * h / w))
    else:
        size = (int(SIZE * w / h), SIZE)
    im = im.resize(size, Image.BICUBIC)
    left, top = int(round((size[0] - SIZE) / 2.0)), int(round((size[1] - SIZE) / 2.0))
    x = np.asarray(im.crop((left, top, left + SIZE, top + SIZE)), np.float32) / 255.0
    return ((x - MEAN) / STD).transpose(2, 0, 1)


def _ln(x, w, b, eps=1e-5):
    mu = x.mean(-1, keepdims=True)
    var = ((x - mu) ** 2).mean(-1, keepdims=True)
    return (x - mu) / np.sqrt(var + eps) * w + b


def _softmax(x):
    x = x - x.max(-1, keepdims=True)
    np.exp(x, out=x)
    return x / x.sum(-1, keepdims=True)


def encode(x: np.ndarray) -> np.ndarray:
    """(B, 3, 224, 224) normalised pictures -> (B, 768) unit style vectors."""
    P = _params()
    B, g = x.shape[0], SIZE // PATCH
    patches = x.reshape(B, 3, g, PATCH, g, PATCH).transpose(0, 2, 4, 1, 3, 5).reshape(B, g * g, 3 * PATCH * PATCH)
    h = patches @ P["conv1.weight"].reshape(WIDTH, -1).T
    h = np.concatenate([np.broadcast_to(P["class_embedding"], (B, 1, WIDTH)), h], axis=1) + P["positional_embedding"]
    h = _ln(h, P["ln_pre.weight"], P["ln_pre.bias"])
    n, dh = h.shape[1], WIDTH // HEADS
    for i in range(LAYERS):
        r = f"transformer.resblocks.{i}."
        a = _ln(h, P[r + "ln_1.weight"], P[r + "ln_1.bias"])
        qkv = a @ P[r + "attn.in_proj_weight"].T + P[r + "attn.in_proj_bias"]
        q, k, v = (qkv[..., j * WIDTH:(j + 1) * WIDTH].reshape(B, n, HEADS, dh).transpose(0, 2, 1, 3) for j in range(3))
        att = _softmax((q / np.sqrt(dh)) @ k.transpose(0, 1, 3, 2))
        o = (att @ v).transpose(0, 2, 1, 3).reshape(B, n, WIDTH)
        h = h + o @ P[r + "attn.out_proj.weight"].T + P[r + "attn.out_proj.bias"]
        m = _ln(h, P[r + "ln_2.weight"], P[r + "ln_2.bias"]) @ P[r + "mlp.c_fc.weight"].T + P[r + "mlp.c_fc.bias"]
        m = m * (1.0 / (1.0 + np.exp(-1.702 * m)))       # QuickGELU, as CLIP
        h = h + m @ P[r + "mlp.c_proj.weight"].T + P[r + "mlp.c_proj.bias"]
    cls = _ln(h[:, 0], P["ln_post.weight"], P["ln_post.bias"])
    s = cls @ P["style_proj"]
    return s / np.linalg.norm(s, axis=1, keepdims=True)


def embed(pictures: list[np.ndarray], batch: int = 8) -> np.ndarray:
    """Style vectors for RGB pictures, one row each."""
    out = [encode(np.stack([preprocess(p) for p in pictures[i:i + batch]])) for i in range(0, len(pictures), batch)]
    return np.concatenate(out) if out else np.zeros((0, 768), np.float32)


# --- the references' style, and a still against it ----------------------------------------------------------------
# Calibrated on the ten example films (four frames of a film as its references, other moments of it as positives,
# every other film's frames as negatives): other moments of a film scored at or above the references' own lowest
# leave-one-out agreement less 0.05, while frames of other films mostly scored 0.2-0.55. The floor is that agreement
# less 0.05, kept within 0.45 (below it most styles look alike) and 0.70 (a new subject in the same style rarely
# scores higher, however alike the references are to each other).
MARGIN, LOW, HIGH, ALONE = 0.05, 0.45, 0.70, 0.60


def _unit(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def summary(ref_ids: list[str], vectors: np.ndarray) -> dict:
    """The references' style: one centre (each reference weighs the same, however many frames it gave), how well
    each agrees with the others (each reference against the centre of the rest, or each frame against the other
    frames when there is one reference), and the floor a style frame has to reach."""
    ids = list(dict.fromkeys(ref_ids))
    by_ref = np.stack([_unit(vectors[[i for i, r in enumerate(ref_ids) if r == rid]].mean(0)) for rid in ids])
    centre = _unit(by_ref.mean(0))
    groups = by_ref if len(ids) > 1 else vectors
    loo = [float(groups[i] @ _unit(np.delete(groups, i, 0).mean(0))) for i in range(len(groups))] if len(groups) > 1 else []
    floor = float(np.clip(min(loo) - MARGIN, LOW, HIGH)) if loo else ALONE
    return {"model": NAME, "pictures": len(ref_ids), "references": len(ids),
            "agreement": {"min": round(min(loo), 3), "median": round(float(np.median(loo)), 3)} if loo else None,
            "floor": round(floor, 3), "centre": [round(float(x), 5) for x in centre],
            "per_picture": [{"ref": r, "vector": [round(float(x), 5) for x in v]} for r, v in zip(ref_ids, vectors)]}


def score(pictures: list[np.ndarray], style: dict) -> list[dict]:
    """Each picture's style similarity to the references' centre, against the floor."""
    centre = np.asarray(style["centre"], np.float32)
    per = np.asarray([p["vector"] for p in style["per_picture"]], np.float32)
    out = []
    for v in embed(pictures):
        sims = per @ v
        out.append({"similarity": round(float(v @ centre), 3), "floor": style["floor"],
                    "nearest_reference": style["per_picture"][int(np.argmax(sims))]["ref"],
                    "ok": bool(v @ centre >= style["floor"])})
    return out
