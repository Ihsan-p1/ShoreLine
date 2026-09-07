# ShoreLine

Keyboard-first photo culling for photographers. ShoreLine handles the first pass over a
large shoot: keep, reject, or flag for review, without reaching for the mouse. Built with
Python and Qt (PySide6).

I wrote it for my own workflow. Use it, fork it, change it, but it comes as-is with no
promise of support.

## Features

- Cull thousands of photos from the keyboard alone.
- One state machine per photo: UNSEEN, then KEPT, REJECTED, or REVIEW. A photo marked for
  review can still become kept or rejected; kept and rejected cannot flip straight into
  each other.
- Asynchronous caching, so moving to the next photo does not wait on a decode.
- Focus and noise readouts from Laplacian variance, shown as low, medium, or high with a
  short explanation.
- Export the kept photos to a separate folder in one action.
- Xbox-style gamepad support, hot-pluggable.
- Runs offline. Nothing is uploaded anywhere.

## Prerequisites

- Python 3.10 or newer
- pip

## Installation

```bash
git clone https://github.com/Ihsan-p1/ShoreLine.git
cd ShoreLine
pip install -r requirements.txt
```

Dependencies: PySide6, OpenCV, Pillow, exifread, and pygame for the gamepad.

## Usage

```bash
python main.py
```

Click Import Folder, or drag a folder of images onto the window.

### Keyboard

| Key | Action |
| :--- | :--- |
| L | Keep photo |
| J | Reject photo |
| K | Mark for review |
| A / D | Previous / next photo |
| W | Toggle 100% zoom |
| S (hold) | Show focus and noise analysis |
| I | Toggle the details panel |
| E | Export kept photos |
| U | Undo the last action |

### Gamepad

A controller is picked up when plugged in and released when unplugged. Button indices
follow the Xbox layout and may differ on other pads.

| Control | Action |
| :--- | :--- |
| A | Keep photo |
| B | Reject photo |
| Y | Mark for review |
| LB | Undo |
| RB | Next photo |
| D-pad left / right | Previous / next photo |
| LT (hold) | Show focus and noise analysis |
| RT | Toggle 100% zoom |

## Project structure

```
ShoreLine/
├── main.py                 # Entry point
├── resources/styles.qss    # Qt stylesheet
└── src/
    ├── app.py              # Main window
    ├── core/               # State machine, session, image loader, analyzer
    ├── widgets/            # Photo viewer, filmstrip, details panel, tech overlay
    ├── input/              # Keyboard and gamepad handlers
    └── utils/exif_reader.py
```

## Contributing

Fork it, branch, commit, push, open a pull request. There is no test suite to satisfy yet.
