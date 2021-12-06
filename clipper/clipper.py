import locale
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import ttk

import ffmpy

from range_slider import RangeSlider


def timestamp_to_seconds(t):
    partitions = t.split(":")
    seconds = 0
    weight = [1, 60, 3600]
    for partition in partitions[::-1]:
        seconds += partition * weight
    return seconds


def seconds_to_timestamp(s, level=None):
    hours, s_current = divmod(int(s), 3600)
    minutes, seconds = divmod(s_current, 60)

    if level=="hours" or (not level and hours > 0):
        return f"{hours}:{minutes:02}:{seconds:02}"
    elif level=="minutes" or (not level and minutes > 0):
        return f"{minutes}:{seconds:02}"
    else:
        return f"{seconds}"


def seconds_to_timestamp_builder(maximum):
    if maximum > 3599:
        k = lambda h, m, s: f"{h}:{m:02}:{s:02}"
    elif maximum > 59:
        k = lambda h, m, s: f"{h*60+m:02}:{s:02}"
    else:
        k = lambda h, m, s: f"{(h*60+m)*60+s:02}"

    def f(s):
        hours, s_current = divmod(int(s), 3600)
        minutes, seconds = divmod(s_current, 60)
        return k(hours, minutes, seconds)
    return f


def run_clip(file_in, file_out, start, duration):
    ff = ffmpy.FFmpeg(
        inputs={str(file_in): ['-ss', start]},
        outputs={str(file_out): ['-c', 'copy', '-t', duration]},
    )
    ff.run()


def main(file=None):
    master = tk.Tk()
    if len(sys.argv) > 1:
        file = Path(sys.argv[1])
    else:
        if not file:
            return

    if file.is_file():
        ff = ffmpy.FFprobe(
            global_options=('-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1'),
            inputs={file: None},
        )
        output = ff.run(stdout=subprocess.PIPE)
        file_duration = int(float(output[0].decode(locale.getpreferredencoding()).strip()))

        main_frame = ttk.Frame(master)
        main_frame.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))

        w = RangeSlider(main_frame, value_min=0, value_max=file_duration, value_display=seconds_to_timestamp_builder(file_duration))
        w.grid(row=1)

        b = ttk.Button(main_frame, text="Clip")
        b.grid(row=2, sticky=(tk.E))

        tk.mainloop()


if __name__ == "__main__":
    main(Path('1.mp4'))
