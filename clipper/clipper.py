import locale
from pathlib import Path
import subprocess
import sys
import tkinter as tk

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


def run_clip(file_in, file_out, start, duration):
    ff = ffmpy.FFmpeg(
        inputs={str(file_in): ['-ss', start]},
        outputs={str(file_out): ['-c', 'copy', '-t', duration]},
    )
    ff.run()


def main():
    master = tk.Tk()
    if len(sys.argv) > 1:
        file = Path(sys.argv[1])
        if file.is_file():
            ff = ffmpy.FFprobe(
                global_options=('-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1'),
                inputs={file: None},
            )
            output = ff.run(stdout=subprocess.PIPE)
            file_duration = int(float(output[0].decode(locale.getpreferredencoding()).strip()))

            w = RangeSlider(master, value_min=0, value_max=file_duration, value_display=seconds_to_timestamp)
            w.pack()

            tk.mainloop()


if __name__ == "__main__":
    main()
