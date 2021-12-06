import locale
from pathlib import Path
import subprocess
import sys
import time
import tkinter as tk
from tkinter import messagebox
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


def seconds_to_timestamp(s):
    hours, s_current = divmod(int(s), 3600)
    minutes, seconds = divmod(s_current, 60)

    if hours > 0:
        return f"{hours}:{minutes:02}:{seconds:02}"
    elif minutes > 0:
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
        outputs={str(file_out): ['-c', 'copy', '-map', '0', '-t', duration]},
    )
    ff.run(stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main():
    master = tk.Tk()
    master.title('Clipper')
    if len(sys.argv) > 1:
        file = Path(sys.argv[1])

        if file.is_file():
            ff = ffmpy.FFprobe(
                global_options=('-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1'),
                inputs={file: None},
            )
            output = ff.run(stdout=subprocess.PIPE, stderr=subprocess.PIPE,)
            file_duration = int(float(output[0].decode(locale.getpreferredencoding()).strip()))

            main_frame = ttk.Frame(master)
            main_frame.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))

            w = RangeSlider(main_frame, value_min=0, value_max=file_duration, value_display=seconds_to_timestamp_builder(file_duration))
            w.grid(row=1)

            def clip():
                b["state"] = "disabled"
                b["text"] = "Running..."
                # Grab a timestamp for unique filename
                file_out = file.with_stem(f"{file.stem}_clip{time.strftime('%H%M%S')}")
                value_in, value_out = w.get_in_and_out()
                timestamp_ss = seconds_to_timestamp(value_in)
                timestamp_t = seconds_to_timestamp(value_out - value_in)
                master.update()
                run_clip(file, file_out, timestamp_ss, timestamp_t)
                master.quit()

            b = ttk.Button(main_frame, text="Clip", command=clip)
            b.grid(row=2, sticky=(tk.E))

            tk.mainloop()
    else:
        messagebox.showerror("Error", "Please drag a file onto Clipper.")


if __name__ == "__main__":
    main()
