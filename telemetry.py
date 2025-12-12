import mmap
import ctypes
import time
import serial


# --- Definicja struktury telemetrycznej ---
class SPageFilePhysics(ctypes.Structure):
    _fields_ = [
        ("packetId", ctypes.c_int),
        ("gas", ctypes.c_float),
        ("brake", ctypes.c_float),
        ("fuel", ctypes.c_float),
        ("gear", ctypes.c_int),
        ("rpm", ctypes.c_int),  # <-- tu jest RPM
        ("speedKmh", ctypes.c_float),
    ]


class ArduinoConnector:
    def __init__(self):
        self.ser = serial.Serial("COM3", 9600, timeout=1)
        time.sleep(2)  # czas na reset Arduino

    def send(self, data, to_print=True):
        data_str = f"{data};"  # dodaj separator
        if to_print:
            print("Sending:", data_str)
        self.ser.write(data_str.encode())
        time.sleep(0.01)

    def read(self, to_print=True):
        resp = self.ser.readline().decode()
        if to_print:
            print("Reading: " + resp)
        return resp


# --- Otwieramy shared memory Assetto Corsa ---
TAGNAME = r"Local\acpmf_physics"
SIZE = ctypes.sizeof(SPageFilePhysics)

try:
    mm = mmap.mmap(-1, SIZE, TAGNAME)
except Exception as e:
    print("Nie można otworzyć shared memory Assetto Corsa:", e)
    exit(1)

conn = ArduinoConnector()

# --- Główna pętla ---
while True:
    mm.seek(0)
    raw = mm.read(SIZE)
    data = SPageFilePhysics.from_buffer_copy(raw)
    conn.send(data.rpm)
    # conn.read()
