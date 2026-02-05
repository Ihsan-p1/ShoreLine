# ShoreLine

**Personal photo culling for photographers.**

ShoreLine is a fast, keyboard-first desktop application designed to speed up the initial selection process of extensive photo shoots. Built with Python and Qt (PySide6).

> **Note**: This tool was developed specifically for my personal workflow. It is open for anyone to use, fork, or modify, but it is provided "as-is" without guaranteed support.

## Features

- **Keyboard-First Design**: Cull thousands of photos without touching the mouse.
- **State Machine**: Simple UNSEEN → KEPT / REJECTED / REVIEW flow.
- **Instant Navigation**: Asynchronous caching prevents loading delays.
- **Technical Analysis**: Real-time focus peaking and noise level indicators.
- **Export Workflow**: Copy kept photos to a separate folder with one click.
- **Privacy Focused**: Runs entirely offline on your local machine.

## Prerequisites

- **Python 3.10+**
- **pip** (Python package manager)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Ihsan-p1/ShoreLine.git
   cd ShoreLine
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. Click **Import Folder** or drag and drop a folder of images.

3. Use keyboard shortcuts to cull:

   | Key | Action |
   | :--- | :--- |
   | **L** | Keep photo |
   | **J** | Reject photo |
   | **K** | Mark for review |
   | **A / D** | Previous / Next photo |
   | **W** | Toggle 100% Zoom |
   | **S** (hold) | Show Focus & Noise analysis |
   | **I** | Toggle Details Panel |
   | **E** | Export Kept Photos |
   | **U** | Undo last action |

## Project Structure

```
ShoreLine/
├── main.py                 # Entry point
├── resources/              # Stylesheets and assets
└── src/
    ├── app.py              # Main window logic
    ├── core/               # State machine, session, image loader
    ├── widgets/            # Custom UI components
    ├── input/              # Keyboard & gamepad handling
    └── utils/              # EXIF and helper functions
```

## Contributing

1. Fork the project.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

