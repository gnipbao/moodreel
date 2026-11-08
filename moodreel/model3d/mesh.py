"""Meshes from distance fields: surface nets, then every vertex pulled onto the true surface.

Surface nets is the dual of marching cubes. The field is sampled on a grid; every grid edge whose two ends lie on
opposite sides of the surface becomes one quad, joining a vertex in each of the four cells around that edge. Plain
surface nets keeps one vertex per cell, which pinches the surface wherever a cell holds two separate pieces of it (two
opposite corners inside, say). Here a cell gets one vertex per piece: the crossed edges of a cell are grouped by
following the surface across the cell's faces (two crossed edges on a face belong together; a face with all four
crossed is split the same way from both sides, cutting off its inside corners), and each group is one vertex. Every
mesh edge then lies on exactly two faces and the mesh is closed, with outward winding taken from the direction of the
sign change. The outermost grid layer counts as outside, so even a shape the box cuts comes out closed.

The vertices start at the mean of their crossings (linear interpolation along each edge) and are then projected onto
the zero set by Newton steps, p <- p - f(p) grad f / |grad f|^2, a few times; steps are capped at half a cell so a
vertex never jumps to another sheet. Normals are the normalised gradient there, so the mesh shades smoothly at any
size. In the rare cell where the surface passes twice through one face and closes up inside both neighbouring cells
(a handle thinner than the grid), the grid is shifted a fraction of a step and the part sampled again.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import sdf as _sdf

# corner b of a cell sits at offset (b & 1, b >> 1 & 1, b >> 2 & 1) from the cell's lowest grid point
CORNER = np.array([[b & 1, (b >> 1) & 1, (b >> 2) & 1] for b in range(8)])


def _corner_id(offset) -> int:
    return int(offset[0] + 2 * offset[1] + 4 * offset[2])


def _cell_edges():
    """The 12 edges of a cell as (axis, corner, corner). Edge 4a + ob + 2oc runs along axis a; ob and oc are its
    offsets along the next two axes in cyclic order (b = a + 1, c = a + 2)."""
    out = []
    for a in range(3):
        b, c = (a + 1) % 3, (a + 2) % 3
        for oc in (0, 1):
            for ob in (0, 1):
                lo = np.zeros(3, int)
                lo[b], lo[c] = ob, oc
                hi = lo.copy()
                hi[a] = 1
                out.append((a, _corner_id(lo), _corner_id(hi)))
    return out


EDGES = _cell_edges()


def _piece_tables():
    """For each of the 256 inside/outside patterns of a cell's corners: which surface piece each crossed edge belongs
    to (-1: not crossed) and how many pieces there are."""
    by_corners = {frozenset((p, q)): i for i, (_, p, q) in enumerate(EDGES)}
    rings = []                                     # each face's corners in order round it
    for a in range(3):
        b, c = (a + 1) % 3, (a + 2) % 3
        for side in (0, 1):
            ring = []
            for ob, oc in ((0, 0), (1, 0), (1, 1), (0, 1)):
                v = np.zeros(3, int)
                v[a], v[b], v[c] = side, ob, oc
                ring.append(_corner_id(v))
            rings.append(ring)
    piece = np.full((256, 12), -1, np.int64)
    count = np.zeros(256, np.int64)
    for code in range(256):
        inside = [(code >> k) & 1 for k in range(8)]
        crossed = [i for i, (_, p, q) in enumerate(EDGES) if inside[p] != inside[q]]
        root = {i: i for i in crossed}

        def top(i):
            while root[i] != i:
                root[i] = root[root[i]]
                i = root[i]
            return i

        def tie(i, j):
            root[top(i)] = top(j)
        for ring in rings:
            sides = [by_corners[frozenset((ring[k], ring[(k + 1) % 4]))] for k in range(4)]
            hit = [e for e in sides if e in root]
            if len(hit) == 2:
                tie(*hit)
            elif len(hit) == 4:                    # the face's diagonal corners are inside: cut each one off
                if inside[ring[0]]:
                    tie(sides[3], sides[0])
                    tie(sides[1], sides[2])
                else:
                    tie(sides[0], sides[1])
                    tie(sides[2], sides[3])
        names: dict[int, int] = {}
        for i in crossed:
            piece[code, i] = names.setdefault(top(i), len(names))
        count[code] = len(names)
    return piece, count


PIECE, PIECES = _piece_tables()


@dataclass
class Mesh:
    verts: np.ndarray       # (V, 3) float, metres
    faces: np.ndarray       # (F, 3) int, wound counter-clockwise seen from outside
    normals: np.ndarray     # (V, 3) unit outward normals

    @property
    def closed(self) -> bool:
        return topology(self.faces)["closed"]

    @property
    def euler(self) -> int:
        return topology(self.faces)["euler"]


def topology(faces) -> dict:
    """closed: every edge on exactly two faces, wound opposite ways (so the winding agrees across it);
    euler: V - E + F over the vertices the faces use (2 for one closed piece without handles)."""
    f = np.asarray(faces, np.int64).reshape(-1, 3)
    if not len(f):
        return {"closed": False, "euler": 0, "bad_edges": 0, "edges": 0, "vertices": 0, "faces": 0}
    tail = f.ravel()
    head = f[:, [1, 2, 0]].ravel()
    n = int(f.max()) + 1
    undirected = np.minimum(tail, head) * n + np.maximum(tail, head)
    keys, uses = np.unique(undirected, return_counts=True)
    one_way = len(np.unique(tail * n + head)) == len(tail)  # no half-edge twice: neighbours agree on winding
    bad = int((uses != 2).sum())
    verts = len(np.unique(f))
    return {"closed": bool(bad == 0 and one_way), "euler": int(verts - len(keys) + len(f)), "bad_edges": bad,
            "edges": int(len(keys)), "vertices": int(verts), "faces": int(len(f))}


def _sample(f, lo: np.ndarray, step: float, n: np.ndarray) -> np.ndarray:
    """The field on the grid lo + step * (i, j, k), a few x-slices at a time so the temporaries stay small."""
    out = np.empty(tuple(int(k) for k in n))
    ys = lo[1] + step * np.arange(n[1])
    zs = lo[2] + step * np.arange(n[2])
    plane_yz = np.empty((n[1] * n[2], 3))
    plane_yz[:, 1] = np.repeat(ys, n[2])
    plane_yz[:, 2] = np.tile(zs, n[1])
    per = max(1, 400_000 // len(plane_yz))
    for i0 in range(0, int(n[0]), per):
        i1 = min(int(n[0]), i0 + per)
        slab = np.tile(plane_yz, (i1 - i0, 1))
        slab[:, 0] = np.repeat(lo[0] + step * np.arange(i0, i1), len(plane_yz))
        out[i0:i1] = f(slab).reshape(i1 - i0, n[1], n[2])
    return out


def project(f, verts: np.ndarray, step: float, iterations: int = 8, tol: float = 1e-8) -> np.ndarray:
    """Newton steps onto f = 0, each capped at half a cell, never ending more than 1.5 cells from the start."""
    start = np.asarray(verts, float)
    p = start.copy()
    h = step * 1e-3
    todo = np.arange(len(p))
    for _ in range(iterations):
        d = f(p[todo])
        keep = np.abs(d) > tol
        todo, d = todo[keep], d[keep]
        if not len(todo):
            break
        g = _sdf.gradient(f, p[todo], h)
        step_vec = d[:, None] * g / np.maximum((g * g).sum(axis=1), 1e-12)[:, None]
        length = np.sqrt((step_vec * step_vec).sum(axis=1))
        q = p[todo] - step_vec * np.minimum(1.0, 0.5 * step / np.maximum(length, 1e-30))[:, None]
        moved = q - start[todo]
        far = np.sqrt((moved * moved).sum(axis=1))
        p[todo] = start[todo] + moved * np.minimum(1.0, 1.5 * step / np.maximum(far, 1e-30))[:, None]
    return p


def _split(quads: np.ndarray, verts: np.ndarray) -> np.ndarray:
    """Each quad as two triangles across its shorter diagonal, keeping the winding."""
    p = verts[quads]
    d02 = ((p[:, 0] - p[:, 2]) ** 2).sum(axis=1)
    d13 = ((p[:, 1] - p[:, 3]) ** 2).sum(axis=1)
    use02 = (d02 <= d13)[:, None]
    first = np.where(use02, quads[:, [0, 1, 2]], quads[:, [0, 1, 3]])
    second = np.where(use02, quads[:, [0, 2, 3]], quads[:, [1, 2, 3]])
    return np.stack([first, second], axis=1).reshape(-1, 3)


def _face_normals_at_verts(verts: np.ndarray, faces: np.ndarray) -> np.ndarray:
    a, b, c = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    fn = np.cross(b - a, c - a)
    acc = np.zeros_like(verts)
    for k in range(3):
        np.add.at(acc, faces[:, k], fn)
    return acc


def _nets(f, lo: np.ndarray, step: float, n: np.ndarray, iterations: int) -> Mesh:
    F = _sample(f, lo, step, n)
    tiny = 1e-12
    for axis in range(3):                          # the outer layer is outside: the surface always closes
        for end in (0, -1):
            idx = [slice(None)] * 3
            idx[axis] = end
            F[tuple(idx)] = np.maximum(F[tuple(idx)], tiny)
    F[F == 0] = tiny                               # exactly on the surface counts as outside
    inside = F < 0
    nc = n - 1
    code = np.zeros(tuple(nc), np.uint8)
    for b in range(8):
        dx, dy, dz = CORNER[b]
        code |= inside[dx:dx + nc[0], dy:dy + nc[1], dz:dz + nc[2]].astype(np.uint8) << b
    live = np.nonzero((code != 0) & (code != 255))
    if not len(live[0]):
        return Mesh(np.zeros((0, 3)), np.zeros((0, 3), np.int64), np.zeros((0, 3)))
    cells = np.stack(live, axis=1)
    kind = code[live].astype(np.intp)
    pieces = PIECES[kind]
    first = np.cumsum(pieces) - pieces             # each live cell's first vertex
    nv = int(pieces.sum())
    slot = np.full(tuple(nc), -1, np.int32)        # live cell number by position (the biggest array: keep it small)
    slot[live] = np.arange(len(cells), dtype=np.int32)

    # each vertex starts at the mean of the crossings of its piece's edges
    acc = np.zeros((nv, 3))
    hits = np.zeros(nv)
    for e, (a, p, q) in enumerate(EDGES):
        which = PIECE[kind, e]
        on = which >= 0
        if not on.any():
            continue
        c0 = cells[on] + CORNER[p]
        c1 = cells[on] + CORNER[q]
        f0 = F[c0[:, 0], c0[:, 1], c0[:, 2]]
        f1 = F[c1[:, 0], c1[:, 1], c1[:, 2]]
        where = c0.astype(float)
        where[:, a] += f0 / (f0 - f1)
        vid = first[on] + which[on]
        for k in range(3):
            acc[:, k] += np.bincount(vid, weights=where[:, k], minlength=nv)
        hits += np.bincount(vid, minlength=nv)
    verts = lo + step * acc / hits[:, None]

    # one quad per crossed grid edge, through the four cells around it, counter-clockwise seen from outside
    quads = []
    for a in range(3):
        b, c = (a + 1) % 3, (a + 2) % 3
        near = [slice(None)] * 3
        far = [slice(None)] * 3
        near[a], far[a] = slice(0, -1), slice(1, None)
        starts = np.argwhere(inside[tuple(near)] != inside[tuple(far)])
        if not len(starts):
            continue
        outward = inside[starts[:, 0], starts[:, 1], starts[:, 2]]    # inside at the start: the normal is +a
        around = []
        for db, dc in ((1, 1), (0, 1), (0, 0), (1, 0)):
            cell = starts.copy()
            cell[:, b] -= db
            cell[:, c] -= dc
            s = slot[cell[:, 0], cell[:, 1], cell[:, 2]]
            around.append(first[s] + PIECE[kind[s], 4 * a + db + 2 * dc])
        quad = np.stack(around, axis=1)
        quad[~outward] = quad[~outward][:, ::-1]
        quads.append(quad)
    quads = np.concatenate(quads)

    verts = project(f, verts, step, iterations)
    faces = _split(quads, verts)
    g = _sdf.gradient(f, verts, step * 1e-3)
    length = np.sqrt((g * g).sum(axis=1))
    flat = length < 1e-9
    if flat.any():                                 # no gradient (a crease's exact middle): use the faces around
        g[flat] = _face_normals_at_verts(verts, faces)[flat]
        length = np.sqrt((g * g).sum(axis=1))
    return Mesh(verts, faces, g / np.maximum(length, 1e-30)[:, None])


def extract(f, lo, hi, step: float, iterations: int = 8, retries: int = 3) -> Mesh:
    """The surface of field f inside the box lo-hi, sampled every `step` metres: verts (V, 3), faces (F, 3) and unit
    normals (V, 3). Leave a cell or two of room around the shape: the box clips it (closed, but flat where cut)."""
    lo = np.asarray(lo, float).reshape(3)
    hi = np.asarray(hi, float).reshape(3)
    best = None
    for attempt in range(retries + 1):
        # a later attempt starts the grid a little further out, so its samples fall elsewhere on the surface
        nudge = np.array([0.37, 0.61, 0.23]) * attempt * step
        origin = lo - nudge
        n = np.maximum(np.ceil((hi - origin) / step - 1e-9).astype(int) + 1, 3)
        m = _nets(f, origin, step, n, iterations)
        bad = topology(m.faces)["bad_edges"] if len(m.faces) else 0
        if best is None or bad < best[0]:
            best = (bad, m)
        if bad == 0:
            break
    return best[1]
