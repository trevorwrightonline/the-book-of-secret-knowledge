# Channel video pipeline

Data-driven housing videos: public data → animated charts → AI narration → captions → MP4, all in code.

## What's here
| Path | What |
|---|---|
| `lib/engine.py` | Scenes → narrated, animated 1080p/vertical video (matplotlib + ffmpeg), SRT captions, chapters, loudness normalisation |
| `lib/words.py` | Spells out numbers for the narrator |
| `lib/preview.py` | Contact sheet of every beat's final frame (quick visual QA) |
| `videos/v03_real_cost/` | **The Real Cost of a $400,000 House (It's Not $400,000)** |
| `videos/v01_rent_vs_buy/` | **Is Renting Really "Throwing Money Away"? I Ran 30 Years of Numbers** (`model.py` = the simulation) |
| `videos/v02_down_payment/` | **How Long It Takes to Save a Down Payment in 50 Big US Cities** (`cities.csv` = city → core county) |
| `videos/shorts/` | 6 vertical Shorts cut from the three videos, captions burned in |
| `data/` | Downloaded source data (FRED, Zillow, Damodaran) |

## Setup
```bash
pip install matplotlib pandas numpy kokoro-onnx soundfile xlrd
mkdir -p models && cd models
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```
Needs `ffmpeg` and the Inter font. Narration voice: Kokoro `af_heart` (Apache-2.0 model, OK for commercial use).

## Build
```bash
python3 videos/v03_real_cost/build.py        # → out/v03_real_cost/{mp4, thumbnail.png, captions.srt, description.txt, facts.json}
python3 videos/v01_rent_vs_buy/build.py
python3 videos/v02_down_payment/build.py
python3 videos/shorts/build.py               # → out/shorts/*.mp4 + titles.txt
python3 lib/preview.py videos/v01_rent_vs_buy/build.py out/sheet.png   # visual QA
```
Every number in the narration and on screen is computed from the data at build time. Refresh `data/` and rebuild to update.

## Upload checklist (per long-form video)
1. Upload the MP4, set the custom thumbnail.
2. Paste `description.txt` (chapters, method and sources are already in it).
3. Upload `captions.srt` as English subtitles.
4. End screen → next video in the series; add to its playlist.
5. Pinned comment, e.g. *"What city should I run next? Most-liked reply gets its own video."*
6. Altered/synthetic content: these are charts with an AI narrator, not realistic depictions of real people or events, so the toggle generally isn't required. The description can still say "Narration uses an AI voice", for transparency.
7. Shorts: set each Short's **Related video** to its long-form video (see `out/shorts/titles.txt`).

The Shorts show `@the30secondagent` in the footer. Change it in `videos/shorts/build.py` (`captions()`) after the rebrand.
