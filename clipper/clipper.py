import locale
from pathlib import Path
import subprocess
import sys
import time
import tkinter as tk
from tkinter import filedialog, ttk

import ffmpy
from range_slider.range_slider import RangeSlider


class Clipper:
    """Primary app class with GUI and function state management.
    """

    MAX_PRINT_FILENAME_CHARACTERS = 50
    BUTTON_CLIP_ENABLED_TEXT = "Clip"

    def __init__(self, _file=""):
        """Instantiate the app's GUI. Select the passed file if it's valid.
        """
        self.master = tk.Tk()
        self.master.title('Clipper')

        self.range_slider = RangeSlider(self.master,
                                        value_min=0, value_max=1)
        self.range_slider.grid(row=1, column=1, columnspan=3)

        self.button_clip = ttk.Button(self.master, command=self.clip, text=self.BUTTON_CLIP_ENABLED_TEXT)
        self.button_clip.grid(row=2, rowspan=2, column=3, sticky="E")

        self.button_open = ttk.Button(self.master, text="Open File", command=self.select_new_file)
        self.button_open.grid(row=2, rowspan=2, column=1, sticky="W")

        self.label_filename = ttk.Label(self.master)
        self.label_filename.grid(row=2, column=2, sticky="NESW")

        self.label_status = ttk.Label(self.master, text="")
        self.label_status.grid(row=3, column=2, sticky="NESW")

        self.use_negative_ts = tk.IntVar()
        self.use_negative_ts.set(1)
        self.negative_ts_checkbox = ttk.Checkbutton(self.master, text="Avoid negative timestamps (video only)", variable=self.use_negative_ts)
        self.negative_ts_checkbox.grid(row=4, column=1, columnspan=3, sticky="NW")

        self.file = Path()
        self.file_duration = 1
        if _file:
            # When starting up with a file in args, open it without the prompt
            self.select_new_file(_file)
        else:
            self.no_file_selected()
        self.master.mainloop()

    def select_new_file(self, _file=""):
        """Open a dialog for the user to select a file.

        Upon selecting a file, change the state to 'working' by enabling the clip button,
        and changing the label text to the file.
        If a filename is passed to clipper.py's args, it will need to be loaded without prompting the user.
        """

        if _file:
            new_file = _file
        else:
            new_file = filedialog.askopenfilename()

        if new_file and Path(new_file).is_file():
            self.file = Path(new_file)
            self.file_duration = Clipper.get_file_duration(self.file)
            if self.file_duration > 0:
                self.range_slider.change_min_max(0, self.file_duration)
                self.range_slider.change_display(RangeSlider.timestamp_display_builder(self.file_duration))
                self.button_clip["state"] = "enabled"
                if len(self.file.name) > self.MAX_PRINT_FILENAME_CHARACTERS:
                    # Special handling of 'very long' input filenames
                    label_text = f"{str(self.file.name)[:self.MAX_PRINT_FILENAME_CHARACTERS//2]}..." \
                                 f"{str(self.file.name)[-self.MAX_PRINT_FILENAME_CHARACTERS//2:]}"
                else:
                    label_text = str(self.file.name)
                self.label_filename["text"] = label_text.strip()
                self.label_status["text"] = ""

    def no_file_selected(self):
        """Correctly set label text and other state variables for having no file selected.
        """
        self.label_filename["text"] = "No file selected!"
        self.range_slider.change_display(value_display=lambda v:"??:??")
        self.button_clip["state"] = "disabled"

    def clip(self):
        """Perform the primary 'clipping' operation with the given in-out marks on the chosen file.
        """

        if not self.file.is_file():
            self.file = Path()
            self.label_status["text"] = "The chosen file appears to have been deleted.\nOperation cancelled."
            self.no_file_selected()
            return

        # Update the button text and grey it out to make it clear it's working
        self.button_clip["state"] = "disabled"
        self.button_clip["text"] = "Running..."
        self.master.update()

        # Grab a timestamp to produce a unique file
        file_out = self.file.with_stem(f"{self.file.stem}_clip{time.strftime('%H%M%S')}")

        # Grab the variables to pass to ffmpeg from the slider
        value_in, value_out = self.range_slider.get_in_and_out()
        timestamp_ss = Clipper.seconds_to_timestamp(value_in)
        timestamp_t = Clipper.seconds_to_timestamp(value_out - value_in)

        # Run ffmpeg to make the clip
        avoid_negative_ts = bool(self.use_negative_ts.get())
        Clipper.run_clip(self.file, file_out, timestamp_ss, timestamp_t, avoid_negative_ts)

        # Re-enable the button
        self.button_clip["state"] = "enabled"
        self.button_clip["text"] = self.BUTTON_CLIP_ENABLED_TEXT
        if len(str(file_out.name)) > self.MAX_PRINT_FILENAME_CHARACTERS:
            # Special handling of 'very long' output filenames
            label_file_out = f"...{str(file_out.name)[-self.MAX_PRINT_FILENAME_CHARACTERS:]}"
        else:
            label_file_out = str(file_out.name)
        self.label_status["text"] = f"Exported clip as {label_file_out}"

    @staticmethod
    def run_clip(file_in: Path, file_out: Path, start: str, duration: str, avoid_negative_ts: bool):
        """Run ffmpeg to cut file_in from start for time duration, and save as file_out.

        -map 0 is passed to ensure all streams are copied.
        -disposition:a 0 is passed to ensure players such as VLC don't choose the incorrect audio track as 'default'.
        """

        output_arguments = ['-c', 'copy', '-map', '0', '-disposition:a', '0', '-t', duration]
        if avoid_negative_ts:
            output_arguments.append('-avoid_negative_ts')
            output_arguments.append('make_zero')
        ff = ffmpy.FFmpeg(
            inputs={str(file_in): ['-ss', start]},
            outputs={str(file_out): output_arguments},
        )
        ff.run(stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    @staticmethod
    def get_file_duration(_file: Path) -> int:
        """Find the duration in seconds of the given file.

        This is a non-trivial operation that requires use of FFprobe.
        Chain conversion str->float->int is required: int() on a string representation of a float raises a ValueError.
        """

        if _file and _file.is_file():
            ff = ffmpy.FFprobe(
                global_options=('-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1'),
                inputs={_file: None},
            )
            output = ff.run(stdout=subprocess.PIPE, stderr=subprocess.PIPE,)
            file_duration = int(float(output[0].decode(locale.getpreferredencoding()).strip()))
            return file_duration

    @staticmethod
    def seconds_to_timestamp(total_seconds) -> str:
        """Convert a number of seconds to a timestamp in the standard format HH:MM:SS.

        Returns a single string containing a timestamp corresponding to the argument 'total_seconds'.
        """

        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)

        return f"{hours}:{minutes:02}:{seconds:02}"


if __name__ == "__main__":
    file = "".join(sys.argv[1:])  # Allow opening with file already selected if passed as argument to script
    Clipper(file)
