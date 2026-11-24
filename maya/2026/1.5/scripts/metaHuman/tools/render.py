"""Tiny software renderer (numpy z-buffer, flat Lambert) for checking meshes."""
import numpy as np


def look_rotation(yaw=0.0, pitch=0.0):
    y, p = np.radians(yaw), np.radians(pitch)
    Ry = np.array([[np.cos(y), 0, np.sin(y)], [0, 1, 0], [-np.sin(y), 0, np.cos(y)]])
    Rx = np.array([[1, 0, 0], [0, np.cos(p), -np.sin(p)], [0, np.sin(p), np.cos(p)]])
    return Rx @ Ry


def render(meshes, size=600, yaw=0.0, pitch=0.0, center=None, extent=None, bg=1.0, marks=None, mark_colors=None,
           return_camera=False, grid=0):
    """meshes: list of (verts (N,3), tris (T,3), rgb). Camera looks down -Z (Y up), orthographic.
    marks: optional (K,3) points drawn as dots. Returns HxWx3 float image."""
    R = look_rotation(yaw, pitch)
    allv = np.concatenate([m[0] for m in meshes])
    if center is None:
        center = (allv.max(0) + allv.min(0)) / 2
    if extent is None:
        q = (allv - center) @ R.T
        extent = max(np.ptp(q[:, 0]), np.ptp(q[:, 1])) * 0.55
    img = np.full((size, size, 3), bg, np.float32)
    zbuf = np.full((size, size), -np.inf, np.float32)
    light = np.array([0.3, 0.4, 1.0])
    light /= np.linalg.norm(light)
    for verts, tris, rgb in meshes:
        v = (verts - center) @ R.T
        sx = (v[:, 0] / extent * 0.5 + 0.5) * (size - 1)
        sy = (0.5 - v[:, 1] / extent * 0.5) * (size - 1)
        sz = v[:, 2]
        a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
        n = np.cross(v[b] - v[a], v[c] - v[a])
        nl = np.linalg.norm(n, axis=1) + 1e-12
        shade = np.abs((n / nl[:, None]) @ light) * 0.8 + 0.2
        x0 = np.floor(np.minimum(np.minimum(sx[a], sx[b]), sx[c])).astype(int).clip(0, size - 1)
        x1 = np.ceil(np.maximum(np.maximum(sx[a], sx[b]), sx[c])).astype(int).clip(0, size - 1)
        y0 = np.floor(np.minimum(np.minimum(sy[a], sy[b]), sy[c])).astype(int).clip(0, size - 1)
        y1 = np.ceil(np.maximum(np.maximum(sy[a], sy[b]), sy[c])).astype(int).clip(0, size - 1)
        col = np.asarray(rgb, np.float32)
        for t in range(len(tris)):
            if x1[t] < x0[t] or y1[t] < y0[t]:
                continue
            xs = np.arange(x0[t], x1[t] + 1)
            ys = np.arange(y0[t], y1[t] + 1)
            X, Y = np.meshgrid(xs, ys)
            ax_, ay_, bx_, by_, cx_, cy_ = sx[a[t]], sy[a[t]], sx[b[t]], sy[b[t]], sx[c[t]], sy[c[t]]
            den = (by_ - cy_) * (ax_ - cx_) + (cx_ - bx_) * (ay_ - cy_)
            if abs(den) < 1e-12:
                continue
            w0 = ((by_ - cy_) * (X - cx_) + (cx_ - bx_) * (Y - cy_)) / den
            w1 = ((cy_ - ay_) * (X - cx_) + (ax_ - cx_) * (Y - cy_)) / den
            w2 = 1 - w0 - w1
            inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not inside.any():
                continue
            z = w0 * sz[a[t]] + w1 * sz[b[t]] + w2 * sz[c[t]]
            Yi, Xi = Y[inside], X[inside]
            zi = z[inside]
            closer = zi > zbuf[Yi, Xi]
            Yi, Xi, zi = Yi[closer], Xi[closer], zi[closer]
            zbuf[Yi, Xi] = zi
            img[Yi, Xi] = col * shade[t]
    if grid:
        for g in range(0, size, grid):
            img[g, :, :] = img[g, :, :] * 0.6 + np.array([0.2, 0.5, 1.0]) * 0.4
            img[:, g, :] = img[:, g, :] * 0.6 + np.array([0.2, 0.5, 1.0]) * 0.4
    if marks is not None:
        v = (np.asarray(marks) - center) @ R.T
        sx = (v[:, 0] / extent * 0.5 + 0.5) * (size - 1)
        sy = (0.5 - v[:, 1] / extent * 0.5) * (size - 1)
        for k, (x, y) in enumerate(zip(sx, sy)):
            c = (1, 0, 0) if mark_colors is None else mark_colors[k]
            xi, yi = int(round(x)), int(round(y))
            img[max(0, yi - 2):yi + 3, max(0, xi - 2):xi + 3] = c
    if return_camera:
        return img, {"R": R, "center": np.asarray(center, float), "extent": float(extent), "size": size, "zbuf": zbuf}
    return img


def unproject(cam, px, py):
    """Pixel (x right, y down) -> 3D point on the rendered surface (None if background)."""
    size, ext = cam["size"], cam["extent"]
    xi, yi = int(np.clip(round(px), 0, cam["size"] - 1)), int(np.clip(round(py), 0, cam["size"] - 1))
    z = cam["zbuf"][yi, xi]
    if not np.isfinite(z):
        win = cam["zbuf"][max(0, yi - 3):yi + 4, max(0, xi - 3):xi + 4]
        if not np.isfinite(win).any():
            return None
        z = win[np.isfinite(win)].max()
    x = (px / (size - 1) - 0.5) * 2 * ext
    y = (0.5 - py / (size - 1)) * 2 * ext
    return np.array([x, y, z]) @ cam["R"] + cam["center"]


def label_grid(img, grid, color=(0.1, 0.2, 0.8)):
    """Write pixel coordinates along the borders (needs PIL)."""
    from PIL import Image, ImageDraw
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for g in range(0, img.shape[0], grid):
        d.text((2, g + 1), str(g), fill=tuple(int(c * 255) for c in color))
        d.text((g + 1, 2), str(g), fill=tuple(int(c * 255) for c in color))
    return np.asarray(im).astype(np.float32) / 255.0


def save(img, path):
    """PNG with Pillow if available, otherwise a .ppm next to it (no extra dependency)."""
    data = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    try:
        from PIL import Image
        Image.fromarray(data).save(path)
        return path
    except ImportError:
        path = path.rsplit(".", 1)[0] + ".ppm"
        with open(path, "wb") as f:
            f.write(b"P6 %d %d 255\n" % (data.shape[1], data.shape[0]))
            f.write(data.tobytes())
        return path
