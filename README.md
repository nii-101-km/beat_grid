# Beat Grid

[Русская инструкция](README.ru.md)

Beat Grid is a small local tool for inspecting estimated beat intervals and preparing an audio selection for repainting. It uses a browser interface, defaults to English, and can be switched to Russian. Audio analysis runs on your computer.

- Display detected beat times and intervals, highlight deviations from the median, and export a CSV.
- Set selection boundaries directly from the beat table.
- Compare beats around the selection with the file's median beat interval and calculate a suggested shift for the right-hand audio.
- Download a new WAV with the edit inside the selection; the original file is not modified.

## Setup

Python 3.10 or newer is recommended. On Linux or macOS, from this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./start.sh
```

The program opens a local page in your browser. Press `Ctrl+C` in the terminal to stop it. If a `.venv` is present, `start.sh` uses it; alternatively, set `BEAT_GRID_PYTHON` to a Python interpreter with the dependencies installed. For compatibility with an existing local setup, the launcher also checks `~/apps/ComfyUI/venv/bin/python` before falling back to `python3`.

On Windows, install the dependencies in a Python environment and run:

```powershell
python beat_grid.py
```

Use WAV or FLAC for best compatibility. Other formats depend on your installed `soundfile`/libsndfile. Audacity `.aup3` projects are not audio files: export the relevant audio first. The interface accepts files up to 256 MiB and excerpts up to 15 minutes.

## Workflow

1. Choose a file. If it is an excerpt, enter its start time in the original project in seconds: for example, 3:16 is `196`. Use `0` for a full track.
2. Click **Analyze**. The table shows beat times in project seconds and interval lengths in milliseconds.
3. Select the start and end using the table buttons, or enter them manually. Each row's **Start** uses its first beat; **End** uses its next beat.
4. Click **Calculate shift**. The program compares the nearest detected beats outside the selection using the file-wide median interval and the number of table intervals between them. Deviations within the configurable tolerance (15 ms by default) suggest a zero shift. The shift can be changed manually.
5. Click **Create WAV** to download the whole edited audio file. A positive shift inserts silence in the middle of the selection; a negative shift cuts audio there. Audio after the selection moves as one piece, and the output duration changes by the shift. The edit can produce an audible join: it is intended to be repaired when repainting. Output is 32-bit float WAV with the input's sample rate and channel count.

To analyze in the terminal instead:

```bash
./start.sh audio.wav --offset 196
./start.sh audio.wav --offset 196 --bpm 134
```

## Limitations

Beats are estimates made from the full mix, not precise measurements of individual drum hits. Tempo can be detected at half or double speed, or a beat may be missed. A global median is a poor reference for a track with tempo changes; errors can accumulate over long selections. Check the suggested shift and the result by ear before using it. A zero suggestion means the calculated deviation is within the chosen tolerance, not that timing is guaranteed correct. The program does not perform repainting.

## Tests

```bash
python -m unittest discover -s tests
```

## License

[MIT](LICENSE).
