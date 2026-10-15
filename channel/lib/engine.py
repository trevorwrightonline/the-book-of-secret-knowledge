"""Minimal video engine: narrated scenes -> animated matplotlib frames -> mp4.

A video is a list of Scenes. Each scene has one or more narration "beats".
Every beat gets its own TTS clip, so visuals can change exactly when the
narration moves on. draw(fig, ctx) renders one frame; ctx carries the
current beat index and its eased animation progress.
"""
import os, re, subprocess, wave
from dataclasses import dataclass, field
from typing import Callable, List, Optional

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- theme ----------
C = dict(
    bg="#0E1726", panel="#17233B", grid="#24324F", text="#F2F5FA", muted="#8A99B5",
    green="#3DDC97", red="#FF6B6B", amber="#FFC145", blue="#4EA8FF",
    purple="#B88CFF", gray="#9AA5B8", teal="#2EC4B6",
)
FONT = "Inter"
plt.rcParams.update({
    "font.family": FONT, "text.color": C["text"], "axes.labelcolor": C["muted"],
    "xtick.color": C["muted"], "ytick.color": C["muted"], "axes.edgecolor": C["grid"],
    "axes.facecolor": C["bg"], "figure.facecolor": C["bg"], "savefig.facecolor": C["bg"],
})


def ease(p):  # easeOutCubic
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 3


def money(v, dec=0):
    return f"${v:,.{dec}f}"


# ---------- data structures ----------
@dataclass
class Ctx:
    beat: int          # index of current beat within scene
    bp: float          # eased progress (0..1) of the current beat's animation
    t: float           # seconds since scene start
    beat_t: float      # seconds since beat start
    beat_d: float      # duration of current beat (s)
    W: int
    H: int


@dataclass
class Scene:
    beats: List[str]
    draw: Callable
    chapter: Optional[str] = None
    anim: float = 1.2           # seconds each beat animates for
    live: bool = False          # redraw every frame even when animation done
    durations: list = field(default_factory=list)  # filled in by TTS


# ---------- TTS ----------
_kokoro = None


def tts(text, path, voice="af_heart", speed=1.0):
    global _kokoro
    if os.path.exists(path):
        return
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(os.path.join(ROOT, "models/kokoro-v1.0.onnx"),
                         os.path.join(ROOT, "models/voices-v1.0.bin"))
    samples, sr = _kokoro.create(text, voice=voice, speed=speed, lang="en-us")
    sf.write(path, samples, sr)


SR = 24000
BEAT_GAP = 0.25
SCENE_GAP = 0.55
TAIL = 1.5


def build_audio(scenes, workdir, voice, speed):
    os.makedirs(workdir, exist_ok=True)
    chunks = []
    for si, sc in enumerate(scenes):
        sc.durations = []
        for bi, text in enumerate(sc.beats):
            p = os.path.join(workdir, f"s{si:02d}_b{bi:02d}.wav")
            tts(text, p, voice, speed)
            a, sr = sf.read(p, dtype="float32")
            assert sr == SR
            gap = BEAT_GAP if bi < len(sc.beats) - 1 else SCENE_GAP
            if si == len(scenes) - 1 and bi == len(sc.beats) - 1:
                gap = TAIL
            chunks.append(a)
            chunks.append(np.zeros(int(gap * SR), dtype="float32"))
            sc.durations.append(len(a) / SR + gap)
    audio = np.concatenate(chunks)
    out = os.path.join(workdir, "narration.wav")
    sf.write(out, audio, SR)
    return out, len(audio) / SR


# ---------- captions / chapters ----------
def _ts(sec, srt=True):
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if srt:
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"
    return f"{int(m)}:{int(s):02d}" if h == 0 else f"{int(h)}:{int(m):02d}:{int(s):02d}"


def write_srt(scenes, path):
    t, n, out = 0.0, 1, []
    for sc in scenes:
        for text, d in zip(sc.beats, sc.durations):
            speech = d - (BEAT_GAP if d > BEAT_GAP else 0)
            parts = [p for p in re.split(r"(?<=[.?!])\s+", text) if p]
            total = sum(len(p) for p in parts)
            st = t
            for p in parts:
                dur = speech * len(p) / total
                out.append(f"{n}\n{_ts(st)} --> {_ts(st + dur)}\n{p}\n")
                n += 1
                st += dur
            t += d
    open(path, "w").write("\n".join(out))


def chapters(scenes):
    t, res = 0.0, []
    for sc in scenes:
        if sc.chapter:
            res.append(f"{_ts(t, srt=False)} {sc.chapter}")
        t += sum(sc.durations)
    return res


# ---------- rendering ----------
def render(scenes, out_mp4, W=1920, H=1080, fps=30, voice="af_heart", speed=1.0,
           workdir=None, overlay=None):
    workdir = workdir or os.path.splitext(out_mp4)[0] + "_work"
    audio, total = build_audio(scenes, workdir, voice, speed)
    dpi = 100
    fig = plt.figure(figsize=(W / dpi, H / dpi), dpi=dpi)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-i", audio,
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out_mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    frame_no = 0
    for si, sc in enumerate(scenes):
        scene_t = 0.0
        for bi, d in enumerate(sc.durations):
            n = int(round((scene_t + d) * fps)) - int(round(scene_t * fps))
            cached = None
            for k in range(n):
                bt = k / fps
                bp = ease(bt / sc.anim) if sc.anim > 0 else 1.0
                if cached is not None and bp >= 1.0 and not sc.live:
                    proc.stdin.write(cached)
                    continue
                fig.clf()
                ctx = Ctx(beat=bi, bp=bp, t=scene_t + bt, beat_t=bt, beat_d=d, W=W, H=H)
                sc.draw(fig, ctx)
                if overlay:
                    overlay(fig, ctx, si)
                fig.canvas.draw()
                buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].tobytes()
                if bp >= 1.0:
                    cached = buf
                proc.stdin.write(buf)
            frame_no += n
            scene_t += d
    proc.stdin.close()
    proc.wait()
    plt.close(fig)
    assert proc.returncode == 0, "ffmpeg failed"
    loudnorm(out_mp4)
    return total, workdir


def loudnorm(mp4, target=-14):
    """Normalise narration to YouTube's playback loudness (about -14 LUFS)."""
    tmp = mp4 + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-c:v", "copy",
                    "-af", f"loudnorm=I={target}:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "2",  # loudnorm upsamples; resample for players
                    "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, mp4)


def still(draw, path, W=1280, H=720):
    dpi = 100
    fig = plt.figure(figsize=(W / dpi, H / dpi), dpi=dpi)
    draw(fig)
    fig.savefig(path, dpi=dpi)
    plt.close(fig)


# ---------- drawing helpers ----------
def txt(fig, x, y, s, size=40, weight="bold", color=None, ha="center", va="center",
        alpha=1.0, **kw):
    return fig.text(x, y, s, fontsize=size, fontweight=weight, color=color or C["text"],
                    ha=ha, va=va, alpha=max(0.0, min(1.0, alpha)), parse_math=False, **kw)


def box(fig, x, y, w, h, color, alpha=1.0, r=0.012):
    from matplotlib.patches import FancyBboxPatch
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                       transform=fig.transFigure, facecolor=color, edgecolor="none",
                       alpha=max(0.0, min(1.0, alpha)))
    fig.patches.append(p)
    return p


def source(fig, s):
    txt(fig, 0.03, 0.035, s, size=15, weight="normal", color=C["muted"], ha="left")


def badge(fig, x, y, s, color=None, size=16):
    txt(fig, x, y, s, size=size, weight="bold", color=C["bg"], ha="left",
        bbox=dict(boxstyle="round,pad=0.35", facecolor=color or C["amber"], edgecolor="none"))
