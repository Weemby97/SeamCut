import numpy as np

try:
    from numba import njit
    HAS_NUMBA = True
except Exception:
    HAS_NUMBA = False

    def njit(*args, **kwargs):
        if args and callable(args[0]):
            return args[0]
        return lambda f: f

BIG = 1e5
LUMA = np.array([0.299, 0.587, 0.114], dtype=np.float32)


class Cancelled(Exception):
    pass


def energy(rgb, mask):
    gray = rgb.astype(np.float32) @ LUMA
    p = np.pad(gray, 1, mode="edge")
    e = np.abs(p[1:-1, 2:] - p[1:-1, :-2]) + np.abs(p[2:, 1:-1] - p[:-2, 1:-1])
    return e + mask.astype(np.float32) * np.float32(BIG)


@njit(cache=True)
def find_seam(e):
    h, w = e.shape
    dp = e.astype(np.float64)
    back = np.zeros((h, w), dtype=np.int8)
    for y in range(1, h):
        for x in range(w):
            best = dp[y - 1, x]
            b = 0
            if x > 0 and dp[y - 1, x - 1] < best:
                best = dp[y - 1, x - 1]
                b = -1
            if x < w - 1 and dp[y - 1, x + 1] < best:
                best = dp[y - 1, x + 1]
                b = 1
            dp[y, x] += best
            back[y, x] = b
    seam = np.empty(h, dtype=np.int32)
    x = 0
    m = dp[h - 1, 0]
    for i in range(1, w):
        if dp[h - 1, i] < m:
            m = dp[h - 1, i]
            x = i
    seam[h - 1] = x
    for y in range(h - 1, 0, -1):
        x += int(back[y, x])
        seam[y - 1] = x
    return seam


@njit(cache=True)
def _remove_rgb(img, seam):
    h, w, c = img.shape
    out = np.empty((h, w - 1, c), dtype=img.dtype)
    for y in range(h):
        sx = seam[y]
        out[y, :sx, :] = img[y, :sx, :]
        out[y, sx:, :] = img[y, sx + 1:, :]
    return out


@njit(cache=True)
def _remove_2d(a, seam):
    h, w = a.shape
    out = np.empty((h, w - 1), dtype=a.dtype)
    for y in range(h):
        sx = seam[y]
        out[y, :sx] = a[y, :sx]
        out[y, sx:] = a[y, sx + 1:]
    return out


def carve(rgb, mask, target_w, target_h, progress=None, cancelled=None):
    H, W = rgb.shape[:2]
    target_w = max(1, min(W, int(target_w)))
    target_h = max(1, min(H, int(target_h)))

    removed = np.zeros(H * W, dtype=bool)
    idx = np.arange(H * W, dtype=np.int32).reshape(H, W)
    img = np.ascontiguousarray(rgb)
    m = np.ascontiguousarray(mask.astype(np.int8))

    total = max(1, (W - target_w) + (H - target_h))
    done = 0

    def run(img, m, idx, n):
        nonlocal done
        for _ in range(n):
            if cancelled and cancelled():
                raise Cancelled()
            seam = find_seam(energy(img, m))
            removed[idx[np.arange(img.shape[0]), seam]] = True
            img = _remove_rgb(img, seam)
            m = _remove_2d(m, seam)
            idx = _remove_2d(idx, seam)
            done += 1
            if progress and done % 2 == 0:
                progress(done / total)
        return img, m, idx

    img, m, idx = run(img, m, idx, W - target_w)

    if H - target_h > 0:
        img = np.ascontiguousarray(img.transpose(1, 0, 2))
        m = np.ascontiguousarray(m.T)
        idx = np.ascontiguousarray(idx.T)
        img, m, idx = run(img, m, idx, H - target_h)
        img = np.ascontiguousarray(img.transpose(1, 0, 2))

    if progress:
        progress(1.0)
    return img, removed.reshape(H, W)


def warmup():
    img = np.random.randint(0, 255, (16, 16, 3), dtype=np.uint8)
    carve(img, np.zeros((16, 16), dtype=np.int8), 14, 14)
