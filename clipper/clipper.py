import tkinter as tk
from range_slider import RangeSlider

master = tk.Tk()

def hscale_cb(value):
    print('horizontal: {v}'.format(v=value))

w = RangeSlider(master)
#w = tk.Scale(master, from_=0, to=100, orient=tk.HORIZONTAL, command=hscale_cb)
w.pack()

tk.mainloop()