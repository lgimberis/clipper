from tkinter import *
from tkinter.ttk import *


class RangeSlider(Frame):
    """RangeSlider presents a double-headed slider defining 'in' and 'out', or 'min' and 'max'.

    """
    LINE_COLOR = "#476b6b"
    LINE_WIDTH = 3
    HEAD_COLOUR_INNER = "#5c8a8a"
    HEAD_COLOUR_OUTER = "#c2d6d6"
    HEAD_RADIUS = 10
    HEAD_RADIUS_INNER = 5
    HEAD_LINE_WIDTH = 2
    DIGIT_PRECISION = '.1f' # for showing in the canvas

    def __init__(self, master, value_min=0, value_max=1, width=400, height=40, value_display=lambda v: f"{v:0.2f}"):
        Frame.__init__(self, master, height=height, width=width)
        self.master = master

        self.value_min = value_min
        self.value_max = value_max
        self.value_display = value_display

        self.height = height
        self.width = width

        self.slider = (RangeSlider.HEAD_RADIUS, self.height * 1 / 2,
                       self.width - RangeSlider.HEAD_RADIUS, self.height * 1 / 2)

        self.pos_to_value = lambda p: value_min + (value_max - value_min) * (p - self.slider[0]) / (self.slider[2] - self.slider[0])
        self.value_to_pos = lambda v: self.slider[0] + (self.slider[2] - self.slider[0]) * (v - value_min) / (value_max - value_min)

        self.bar_offset = (-self.HEAD_RADIUS, -self.HEAD_RADIUS, self.HEAD_RADIUS, self.HEAD_RADIUS)

        self.selected_bar = None  #Bar selected for movement

        self.canvas = Canvas(self, height=self.height, width=self.width)
        self.canvas.pack()
        self.canvas.bind("<Motion>", self.__onclick)
        self.canvas.bind("<B1-Motion>", self.__clicked_move)

        self.canvas.create_line(*self.slider, fill=RangeSlider.LINE_COLOR, width=RangeSlider.LINE_WIDTH)
        self.bar_in = self.__add_bar(value_min)
        self.value_in = self.value_min
        self.bar_out = self.__add_bar(value_max)
        self.value_out = self.value_max

    def __checkSelection(self, x, y):
        """TODO
        """

        def check_bbox(bbox, _x, _y):
            return (bbox[0] < _x and bbox[2] > _x and bbox[1] < _y and bbox[3] > _y)

        bar_in = check_bbox(self.canvas.bbox(self.bar_in[0]), x, y)
        bar_out = check_bbox(self.canvas.bbox(self.bar_out[0]), x, y)

        if bar_in and bar_out:
            return True  # both Overlap
        elif bar_in:
            return self.bar_in
        elif bar_out:
            return self.bar_out
        else:
            return None

    def __onclick(self, event):
        self.selected_bar = self.__checkSelection(event.x, event.y)
        cursor = ("hand2" if self.selected_bar else "")
        self.canvas.config(cursor=cursor)

    def __clicked_move(self, event):
        if self.selected_bar:
            centre_x = min(self.slider[2], max(self.slider[0], event.x))
            if self.selected_bar is self.bar_in:
                centre_x = min(self.value_to_pos(self.value_out), centre_x)
                bar_value = self.value_in = self.pos_to_value(centre_x)
            elif self.selected_bar is self.bar_out:
                centre_x = max(self.value_to_pos(self.value_in), centre_x)
                bar_value = self.value_out = self.pos_to_value(centre_x)
            else:
                pos_in = self.value_to_pos(self.value_in)
                pos_out = self.value_to_pos(self.value_out)
                bar_value = self.pos_to_value(centre_x)
                if centre_x > pos_out:
                    # Select the 'out' bar only when we're clearly pulling it right
                    self.selected_bar = self.bar_out
                else:
                    self.selected_bar = self.bar_in
            centre_y = self.slider[1]

            r = RangeSlider.HEAD_RADIUS
            self.canvas.coords(self.selected_bar[0], (centre_x - r, centre_y - r, centre_x + r, centre_y + r))
            r = RangeSlider.HEAD_RADIUS_INNER
            self.canvas.coords(self.selected_bar[1], (centre_x - r, centre_y - r, centre_x + r, centre_y + r))
            self.canvas.itemconfigure(self.selected_bar[2], text=self.value_display(bar_value))
            # TODO move text?

    def __add_bar(self, value):
        centre_x, centre_y = self.value_to_pos(value), self.slider[1]

        r = RangeSlider.HEAD_RADIUS
        outer = self.canvas.create_oval(centre_x - r, centre_y - r,
                                        centre_x + r, centre_y + r,
                                        fill=RangeSlider.HEAD_COLOUR_OUTER,
                                        width=RangeSlider.HEAD_LINE_WIDTH, outline="", )

        r = RangeSlider.HEAD_RADIUS_INNER
        inner = self.canvas.create_oval(centre_x - r, centre_y - r,
                                        centre_x + r, centre_y + r,
                                        fill=RangeSlider.HEAD_COLOUR_INNER,
                                        width=RangeSlider.HEAD_LINE_WIDTH, outline="", )

        text_y = centre_y + RangeSlider.HEAD_RADIUS + 8  #FIXME awfulness
        text = self.canvas.create_text(centre_x, text_y, text=self.value_display(value))

        return [outer, inner, text]

