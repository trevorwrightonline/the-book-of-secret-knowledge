"""Render the end-state of every beat to a contact sheet: python3 lib/preview.py videos/x/build.py out/sheet.png"""
import sys, os, importlib.util, subprocess, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib.pyplot as plt
from engine import Ctx
spec = importlib.util.spec_from_file_location("b", sys.argv[1]); b = importlib.util.module_from_spec(spec)
sys.argv = [sys.argv[0], "none", sys.argv[2]]
spec.loader.exec_module(b)
d = os.path.splitext(sys.argv[2])[0] + "_frames"; os.makedirs(d, exist_ok=True)
for f in glob.glob(d + "/*.png"): os.remove(f)
for si, sc in enumerate(b.S):
    for bi in range(len(sc.beats)):
        fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
        c = Ctx(beat=bi, bp=1.0, t=99, beat_t=99, beat_d=10, W=1920, H=1080)
        sc.draw(fig, c)
        if hasattr(b, "hud"): b.hud(fig, c, si)
        fig.savefig(f"{d}/s{si:02d}_b{bi}.png", dpi=40); plt.close(fig)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-pattern_type", "glob", "-i", d + "/s*.png",
                "-vf", "tile=4x9:padding=6", sys.argv[2]], check=True)
