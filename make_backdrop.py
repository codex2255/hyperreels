#!/usr/bin/env python3
"""Make a Reel's moving backdrop: a bright, sharp, always-moving 1080x1920 loop from any image or video.

  python3 make_backdrop.py <image|video> <out.mp4> [--seconds 20] [--zoom 1.12:1.22] [--gamma 1.0] [--saturation 1.0]
                                                  [--start 0] [--crossfade 1.0]

Image: the picture is scaled to cover the frame, then a virtual camera glides across it on a cosine path (diagonally,
top-left to bottom-right and back) while the zoom breathes between the two --zoom values, resampled per frame so the
motion never steps. The last frame meets the first, so build.py can loop it.
Video: --seconds from --start, scaled and centre-cropped to 1080x1920, and its tail crossfaded into its head
(--crossfade s) so the loop has no jump.
--gamma below 1 lifts a dark source (0.5 is a strong lift); --saturation above 1 makes it more vivid. No blur.

The input must have a <file>.source.txt (it is client or owned media like any other); the output gets one too,
pointing back to it, so build.py accepts it.
"""
import argparse, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageEnhance

FPS, W, H = 30, 1080, 1920
VIDEO = (".mp4", ".mov", ".m4v", ".webm", ".mkv")


def lift(im, gamma, sat):
    if gamma != 1:
        a = (np.asarray(im, np.float32) / 255) ** gamma
        im = Image.fromarray((a * 255).clip(0, 255).astype(np.uint8))
    if sat != 1:
        im = ImageEnhance.Color(im).enhance(sat)
    return im


def from_image(src, out, a):
    z0, z1 = a.zoom
    im = lift(Image.open(src).convert("RGB"), a.gamma, a.saturation)
    # resize so the picture covers the frame at zoom 1 and is still sharp at the closest zoom (z1); at zoom z the
    # camera sees 1/z of that cover, and travels across whatever room is left
    s = max(W / im.width, H / im.height) * z1
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    iw, ih = im.size
    n = int(a.seconds * FPS)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-nostdin", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-profile:v", "high", "-crf", "20", "-preset", "medium",
                            "-pix_fmt", "yuv420p", "-g", "30", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        k = (1 - math.cos(2 * math.pi * t / a.seconds)) / 2                     # 0 -> 1 -> 0 over the loop
        z = z0 + (z1 - z0) * (1 - math.cos(4 * math.pi * t / a.seconds)) / 2   # zoom breathes twice per loop
        vw_p, vh_p = W * z1 / z, H * z1 / z
        x0 = (iw - vw_p) * (0.15 + 0.7 * k)
        y0 = (ih - vh_p) * (0.15 + 0.7 * k)
        sx, sy = vw_p / W, vh_p / H
        f = im.transform((W, H), Image.AFFINE, (sx, 0, x0, 0, sy, y0), resample=Image.BICUBIC)
        enc.stdin.write(f.tobytes())
    enc.stdin.close()
    if enc.wait():
        sys.exit("make_backdrop: ffmpeg failed")


def from_video(src, out, a):
    eq = []
    if a.gamma != 1 or a.saturation != 1:
        eq = [f"eq=gamma={1 / a.gamma:.3f}:saturation={a.saturation:.3f}"]
    vf = ",".join([f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos", f"crop={W}:{H}", f"fps={FPS}", *eq, "format=yuv420p"])
    d, xf = a.seconds, a.crossfade
    if xf <= 0:
        graph = f"[0:v]{vf}[v]"
    else:
        # body = [xf, d], with its last xf seconds dissolving into [0, xf]: the loop ends where it starts
        graph = (f"[0:v]{vf},split[a][b];[a]trim={xf}:{d},setpts=PTS-STARTPTS[body];[b]trim=0:{xf},setpts=PTS-STARTPTS[head];"
                 f"[body][head]xfade=transition=fade:duration={xf}:offset={d - 2 * xf:.3f}[v]")
    r = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-y", "-ss", str(a.start), "-t", str(d), "-i", src, "-an",
                        "-filter_complex", graph, "-map", "[v]", "-c:v", "libx264", "-profile:v", "high", "-crf", "20",
                        "-preset", "medium", "-g", "30", "-movflags", "+faststart", out], capture_output=True, text=True)
    if r.returncode:
        sys.exit("make_backdrop: " + r.stderr[-1500:])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("src")
    p.add_argument("out")
    p.add_argument("--seconds", type=float, default=20.0)
    p.add_argument("--zoom", default="1.12:1.22", help="min:max zoom for an image (1 = the picture just covers the frame)")
    p.add_argument("--gamma", type=float, default=1.0)
    p.add_argument("--saturation", type=float, default=1.0)
    p.add_argument("--start", type=float, default=0.0, help="video only: where to start in the source")
    p.add_argument("--crossfade", type=float, default=1.0, help="video only: seconds of tail dissolved into the head")
    a = p.parse_args()
    a.zoom = tuple(float(x) for x in a.zoom.split(":"))
    if not os.path.isfile(a.src + ".source.txt"):
        sys.exit(f"make_backdrop: {a.src} has no .source.txt next to it (where it came from, owner, permission, date)")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    (from_video if a.src.lower().endswith(VIDEO) else from_image)(a.src, a.out, a)
    src_note = open(a.src + ".source.txt").read().strip()
    open(a.out + ".source.txt", "w").write(
        f"Built by make_backdrop.py from {os.path.basename(a.src)} ({a.seconds:g} s loop, zoom {a.zoom[0]:g}-{a.zoom[1]:g}, "
        f"gamma {a.gamma:g}, saturation {a.saturation:g}).\nSource of {os.path.basename(a.src)}:\n{src_note}\n")
    print(a.out)


if __name__ == "__main__":
    main()
