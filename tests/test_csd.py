"""Style embeddings: the checkpoint reader, the authors' preprocessing, the encoder against PyTorch, the floor."""
import pickle
import sys
import types
import zipfile

import numpy as np
import pytest

from moodreel.measure import csd


def pictures():
    """Three pictures drawn in code: stripes on a gradient, a coloured checkerboard, seeded noise (320 x 180)."""
    y, x = np.mgrid[0:180, 0:320]
    a = np.stack([x / 320 * 255, (np.sin(x / 9) > 0) * 200 + 20, 255 - y / 180 * 255], -1)
    b = np.where(((x // 20) + (y // 20)) % 2 == 0, 1, 0)[..., None] * np.array([230, 60, 40]) + 15
    c = np.random.default_rng(7).integers(0, 256, (180, 320, 3))
    return [p.astype(np.uint8) for p in (a, b, c)]


# PyTorch's output for pictures() (OpenAI CLIP's VisionTransformer as CSD builds it, torch 2.8, the converted
# weights): the similarities and each vector's first eight numbers
REF_SIMS = [[1.0, 0.4841, 0.51], [0.4841, 1.0, 0.3543], [0.51, 0.3543, 1.0]]
REF_HEADS = [[0.0045, 0.0163, -0.005, 0.0665, 0.0001, -0.0791, -0.0336, 0.0339],
             [-0.01, -0.0166, 0.0115, -0.0407, 0.016, -0.0919, 0.0071, -0.0017],
             [-0.031, -0.0127, 0.0123, 0.0764, 0.0044, -0.0895, -0.0148, -0.0007]]


def _fake_torch_checkpoint(path, tensors, extra):
    """Write a .bin the way torch.save does (a zip with data.pkl and raw storages), without torch."""
    torch = types.ModuleType("torch")
    utils = types.ModuleType("torch._utils")

    class FloatStorage:
        pass

    def _rebuild_tensor_v2(*a):
        pass

    FloatStorage.__module__, FloatStorage.__qualname__ = "torch", "FloatStorage"
    _rebuild_tensor_v2.__module__, _rebuild_tensor_v2.__qualname__ = "torch._utils", "_rebuild_tensor_v2"
    torch.FloatStorage, utils._rebuild_tensor_v2 = FloatStorage, _rebuild_tensor_v2
    sys.modules.update({"torch": torch, "torch._utils": utils})
    try:
        storages = {}

        class T:
            def __init__(self, key, arr, size, stride):
                self.key, self.arr, self.size, self.stride = key, arr, size, stride

            def __reduce__(self):
                return _rebuild_tensor_v2, (("S", self.key), 0, self.size, self.stride, False, {})

        class P(pickle.Pickler):
            def persistent_id(self, obj):
                if isinstance(obj, tuple) and len(obj) == 2 and obj[0] == "S":
                    return ("storage", FloatStorage, obj[1], "cpu", storages[obj[1]].size)
                return None

        tree = {"model_state_dict": {}, **extra}
        for i, (name, (arr, size, stride)) in enumerate(tensors.items()):
            storages[str(i)] = arr.astype(np.float32).ravel()
            tree["model_state_dict"][name] = T(str(i), arr, size, stride)
        with zipfile.ZipFile(path, "w") as z:
            import io
            buf = io.BytesIO()
            P(buf, protocol=2).dump(tree)
            z.writestr("archive/data.pkl", buf.getvalue())
            for k, a in storages.items():
                z.writestr(f"archive/data/{k}", a.tobytes())
    finally:
        sys.modules.pop("torch"), sys.modules.pop("torch._utils")


class Boom:
    """An object whose unpickling would run a command, if anything trusted the pickle."""

    def __reduce__(self):
        import os
        return os.system, ("touch /tmp/moodreel-csd-should-not-exist",)


def test_checkpoint_reader_rebuilds_tensors_and_runs_nothing(tmp_path):
    base = np.arange(12, dtype=np.float32)
    tensors = {"module.a": (base, (3, 4), (4, 1)),          # row-major
               "module.b": (base, (4, 3), (1, 4))}          # the transpose: a stride, not a copy
    path = tmp_path / "fake.bin"
    _fake_torch_checkpoint(path, tensors, {"args": Boom()})
    sd = csd.read_checkpoint(path)
    assert set(sd) == {"a", "b"}                            # the module. prefix is dropped
    assert np.array_equal(sd["a"], base.reshape(3, 4))
    assert np.array_equal(sd["b"], base.reshape(3, 4).T)
    import os
    assert not os.path.exists("/tmp/moodreel-csd-should-not-exist")


def test_preprocess_is_the_authors_transform():
    grey = np.full((180, 320, 3), 128, np.uint8)
    x = csd.preprocess(grey)
    assert x.shape == (3, 224, 224)
    assert np.allclose(x[:, 0, 0], (128 / 255 - csd.MEAN) / csd.STD, atol=1e-5)
    wide = np.zeros((100, 400, 3), np.uint8)
    wide[:, 150:250] = 255                                  # the centre crop keeps the middle
    assert csd.preprocess(wide)[0, 112, 112] > 1.5 and csd.preprocess(wide)[0, 112, 5] > 1.5


def test_floor_comes_from_how_well_the_references_agree():
    rng = np.random.default_rng(1)
    style = csd._unit(rng.normal(size=768))
    vecs = csd._unit(style + 0.6 * rng.normal(size=(6, 768)) / np.sqrt(768) * 8)
    s = csd.summary(["r1", "r1", "r2", "r2", "r3", "r3"], vecs)
    assert s["references"] == 3 and len(s["per_picture"]) == 6
    assert csd.LOW <= s["floor"] <= csd.HIGH
    assert s["floor"] == round(float(np.clip(s["agreement"]["min"] - csd.MARGIN, csd.LOW, csd.HIGH)), 3)
    one = csd.summary(["r1"], vecs[:1])
    assert one["floor"] == csd.ALONE and one["agreement"] is None


@pytest.mark.skipif(not csd.ready(), reason="style embeddings not set up (moodreel csd setup)")
def test_encoder_matches_pytorch():
    v = csd.embed(pictures())
    assert np.allclose(v @ v.T, REF_SIMS, atol=2e-3)
    assert np.allclose(v[:, :8], REF_HEADS, atol=2e-3)
