import tkinter as tk
import random
import math
import time
import mmap
import ctypes
from physics import ACPhysics, ACStatic, MockPhysics


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Assetto Corsa Telemetry")

        # self.physics = connect()
        self.physics = ACPhysics()
        self.static = ACStatic()

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

        self.status_label = tk.Label(root, text="", fg="red")
        self.status_label.pack(pady=10)

        self.canvas = tk.Canvas(root, width=200, height=200)
        self.canvas.pack()

        self.dot = self.canvas.create_oval(80, 80, 120, 120, fill="black")

        self.last_packet = -1

        self.update()

    def update_dot_color(self, maxrpm=7000):
        rpm = self.physics.get()["rpm"]
        rpm = max(0, min(maxrpm, rpm))

        # przeliczanie koloru
        ratio = rpm / maxrpm

        r = int(255 * ratio)
        g = int(255 * (1 - ratio))
        b = 0

        # clamp RGB (na wszelki wypadek)
        r = max(0, min(255, r))
        g = max(0, min(255, g))

        self.canvas.itemconfig(self.dot, fill=f"#{r:02x}{g:02x}{b:02x}")

    def update(self):
        if not self.physics:
            self.status_label.config(text="Brak połączenia z grą")
        else:
            self.speed_label.config(
                text=f"Speed: {self.physics.get()['speed']:.1f} km/h"
            )
            self.rpm_label.config(text=f"RPM: {self.physics.get()['rpm']}")
            self.gear_label.config(text=f"Gear: {self.physics.get()['gear']}")
            self.gas_label.config(text=f"Gas: {self.physics.get()['gas']:.2f}")
            self.brake_label.config(
                text=f"Brake: {self.physics.get()['brake']*100:.0f}%"
            )
            self.update_dot_color()

            self.physics.update()

        # odświeżanie co ~16 ms (~60 FPS)
        self.root.after(16, self.update)


ac = ACPhysics()
acs = ACStatic()
car = acs.get()["car"]
print(acs.get())

# =========================
# START APP
# =========================

root = tk.Tk()
app = App(root)
root.mainloop()
