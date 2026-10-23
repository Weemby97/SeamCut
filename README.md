<p align="center">
  <img src="assets/logo.svg" width="128" alt="seamcut logo">
</p>

<h1 align="center">seamcut</h1>

<p align="center">
  Content-aware image resizing for the desktop. Shrinks a picture by removing the lowest-energy pixel paths (seams), so people and objects stay intact.
</p>

<p align="center">
  <a href="https://github.com/Weemby97/seamcut/releases/latest">Download</a> ·
  <a href="LICENSE">MIT License</a>
</p>

## Features

- Separate target width and height
- Mask brush: red = **protect**, green = **remove**, right-click = erase
- Seam visualization (removed paths drawn over the original)
- Drag and drop, paste with Ctrl+V, save as PNG / JPEG / WebP
- Runs on a background thread, so the UI never freezes, and it can be cancelled
- Fast dynamic programming with numba (falls back to pure Python if missing)
- Modern dark UI with a custom window frame

## Download

Grab the latest Windows build from the [Releases](https://github.com/Weemby97/seamcut/releases/latest) page, unzip it and run `seamcut.exe`.

## Run from source

```bat
git clone https://github.com/Weemby97/seamcut.git
cd seamcut
run.bat
```

`run.bat` creates a virtual environment, installs dependencies and launches the app. Manual setup:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py [image.jpg]
```

## Build an executable

```bat
build.bat
```

Output: `dist\seamcut\seamcut.exe`

To regenerate the icons from `assets/logo.svg`:

```bash
python tools/make_icons.py
```

## How it works

1. Energy map: gray-level difference between neighboring pixels (`|dx| + |dy|`)
2. Dynamic programming finds the vertical path with the lowest total energy
3. The path is removed and the process repeats
4. For height, the image is transposed and the same process runs again

Mask pixels add `±1e5` to the energy, so seams avoid protected areas and prefer removal areas.

## Roadmap

- [ ] Forward energy
- [ ] Seam insertion (enlarging)
- [ ] Automatic face protection mask
- [ ] Batch processing

## License

MIT
