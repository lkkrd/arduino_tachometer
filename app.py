import tkinter as tk
import random
import math
import time
import mmap
import ctypes
import json
import os
from physics import ACPhysics, ACStatic, MockPhysics, PhysicsConnector


class App:
    def __init__(self, root):
        # self.physics = connect()
        self.physics = ACPhysics()
        self.static = ACStatic()
        self.conn = PhysicsConnector()
        self.car = self.conn.get("carModel")
        self.car_config = self.conn.car_config

        # window
        self.root = root
        self.root.title(f"Assetto Corsa Telemetry: {self.car}")

        # Labels
        self.speed_label = tk.Label(root, text="Speed: --- km/h", font=("Arial", 16))
        self.speed_label.pack(pady=5)

        self.rpm_label = tk.Label(root, text="RPM: ---", font=("Arial", 16))
        self.rpm_label.pack(pady=5)

        self.gear_label = tk.Label(root, text="Gear: ---", font=("Arial", 16))
        self.gear_label.pack(pady=5)

        self.gas_label = tk.Label(root, text="Gas: ---", font=("Arial", 16))
        self.gas_label.pack(pady=5)

        self.brake_label = tk.Label(root, text="Brake: ---", font=("Arial", 16))
        self.brake_label.pack(pady=5)

        # self.slip_label = tk.Label(root, text="Slip: ---", font=("Arial", 16))
        # self.slip_label.pack(pady=5)

        self.status_label = tk.Label(root, text="", fg="red")
        self.status_label.pack(pady=10)

        self.canvas = tk.Canvas(root, width=200, height=200)
        self.canvas.pack()

        self.dot = self.canvas.create_oval(80, 80, 120, 120, fill="black")

        r = 10
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        self.slip_fl = self.canvas.create_oval(0, 0, r * 2, r * 2, fill="white")
        self.slip_fr = self.canvas.create_oval(w - r * 2, 0, w, r * 2, fill="white")
        self.slip_rl = self.canvas.create_oval(0, h - r * 2, r * 2, h, fill="white")
        self.slip_rr = self.canvas.create_oval(w - r * 2, h - r * 2, w, h, fill="white")

        self.last_packet = -1
        self.update()

    def update_dot_color(self):
        d = self.conn.get("rpms", "midrpm", "maxrpm")
        rpm = d["rpms"]
        midrpm = d["midrpm"]
        maxrpm = d["maxrpm"]

        def get_thing(
            rpm,
            midrpm=midrpm,
            maxrpm=maxrpm,
        ):
            return int(0 + (rpm - midrpm) * (255 - 0) / (maxrpm - midrpm))

        # przeliczanie koloru
        ratio = rpm / maxrpm

        r = max(0, get_thing(rpm))
        g = 255 - max(0, get_thing(rpm))
        b = 0

        # clamp RGB (na wszelki wypadek)
        r = max(0, min(255, r))
        g = max(0, min(255, g))

        if ratio > 0.95:
            self.canvas.itemconfig(self.dot, fill=f"#DD00FF")
        else:
            self.canvas.itemconfig(self.dot, fill=f"#{r:02x}{g:02x}{b:02x}")

    def update_slip_dots(self, fl, fr, rl, rr, r=10):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        def get_color(slip):
            if slip > 1:
                return "#FF0000"
            else:
                return "#FFFFFF"

        # added here bcse after rendering canvas width and height doesn't work
        self.canvas.coords(self.slip_fl, 0, 0, r * 2, r * 2)
        self.canvas.coords(self.slip_fr, w - r * 2, 0, w, r * 2)
        self.canvas.coords(self.slip_rl, 0, h - r * 2, r * 2, h)
        self.canvas.coords(self.slip_rr, w - r * 2, h - r * 2, w, h)

        self.canvas.itemconfig(self.slip_fl, fill=get_color(fl))
        self.canvas.itemconfig(self.slip_fr, fill=get_color(fr))
        self.canvas.itemconfig(self.slip_rl, fill=get_color(rl))
        self.canvas.itemconfig(self.slip_rr, fill=get_color(rr))

    def update(self):

        fl_slip, fr_slip, rl_slip, rr_slip = self.conn.get("wheelSlip")

        if not self.physics:
            self.status_label.config(text="Brak połączenia z grą")
        else:
            d = self.conn.get("speedKmh", "rpms", "gear", "gas", "brake")
            self.speed_label.config(text=f"Speed: {d['speedKmh']:.0f} km/h")
            self.rpm_label.config(text=f"RPM: {d['rpms']}")
            self.gear_label.config(text=f"Gear: {d['gear'] - 1}")
            self.gas_label.config(text=f"Gas: {d['gas']*100:.0f}")
            self.brake_label.config(text=f"Brake: {d['brake']*100:.0f}%")
            # self.slip_label.config(text=f"Slip: {list(slip)}")

            self.update_dot_color()
            self.update_slip_dots(fl_slip, fr_slip, rl_slip, rr_slip)
            self.physics.update()

        # odświeżanie co ~16 ms (~60 FPS)
        self.root.after(16, self.update)


# =========================
# START APP
# =========================

root = tk.Tk()
app = App(root)
root.mainloop()
