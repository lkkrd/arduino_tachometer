import mmap
import ctypes
import time
import serial


class SPageFilePhysics(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("packetId", ctypes.c_int),
        ("gas", ctypes.c_float),
        ("brake", ctypes.c_float),
        ("fuel", ctypes.c_float),
        ("gear", ctypes.c_int),
        ("rpm", ctypes.c_int),  # rpms
        ("steerAngle", ctypes.c_float),
        ("speedKmh", ctypes.c_float),
        ("velocity", ctypes.c_float * 3),
        ("accG", ctypes.c_float * 3),  # g forces
        ("wheelSlip", ctypes.c_float * 4),  # wheel slip
        ("wheelLoad", ctypes.c_float * 4),
        ("wheelsPressure", ctypes.c_float * 4),
        ("wheelAngularSpeed", ctypes.c_float * 4),
        ("tyreWear", ctypes.c_float * 4),  # tyre wear
        ("tyreDirtyLevel", ctypes.c_float * 4),
        ("tyreCoreTemperature", ctypes.c_float * 4),
        ("camberRAD", ctypes.c_float * 4),
        ("suspensionTravel", ctypes.c_float * 4),
        ("drs", ctypes.c_float),
        ("tc", ctypes.c_float),
        ("heading", ctypes.c_float),
        ("pitch", ctypes.c_float),
        ("roll", ctypes.c_float),
        ("cgHeight", ctypes.c_float),
        ("carDamage", ctypes.c_float * 5),
        ("numberOfTyresOut", ctypes.c_int),
        ("pitLimiterOn", ctypes.c_int),
        ("abs", ctypes.c_float),
        ("kersCurrentKJ", ctypes.c_float),
        ("drsAvailable", ctypes.c_int),
        ("drsEnabled", ctypes.c_int),
        ("brakeTemp", ctypes.c_float * 4),
        ("clutch", ctypes.c_float),
        ("tyreTempI", ctypes.c_float * 4),
        ("tyreTempM", ctypes.c_float * 4),
        ("tyreTempO", ctypes.c_float * 4),
        ("isAIControlled", ctypes.c_int),
        ("tyreContactPoint", ctypes.c_float * 4 * 3),
        ("tyreContactNormal", ctypes.c_float * 4 * 3),
        ("tyreContactHeading", ctypes.c_float * 4 * 3),
        ("brakeBias", ctypes.c_float),  # brake bias
        ("localVelocity", ctypes.c_float * 3),
    ]


class ArduinoConnector:

    def __init__(self):
        self.ser = serial.Serial("COM3", 9600, timeout=1)
        time.sleep(2)  # Arduino reset

    def send(self, *data, to_print=True):

        data_str = ""
        for stat in data:
            data_str += f"{stat};"
        data_str += "\n"

        if to_print:
            print("Sending:", data_str[:-1])  # omitting new line for readability
        self.ser.write(data_str.encode())
        time.sleep(0.01)

    def read(self, to_print=True):
        resp = self.ser.readline().decode()
        if to_print:
            print("Reading: " + resp)
        return resp


TAGNAME_PHYSICS = r"Local\acpmf_physics"
SIZE_PHYSICS = ctypes.sizeof(SPageFilePhysics)

try:
    mm_physics = mmap.mmap(-1, SIZE_PHYSICS, TAGNAME_PHYSICS)
except Exception as e:
    print("Failed to access AC shared memory:", e)
    exit(1)

conn = ArduinoConnector()

max_g0 = 0
max_g1 = 0
min_g0 = 0
min_g1 = 0
while True:
    mm_physics.seek(0)
    raw = mm_physics.read(SIZE_PHYSICS)
    data = SPageFilePhysics.from_buffer_copy(raw)
    conn.send(data.rpm, str(data.accG[0])[:4], str(data.accG[2])[:4])
    max_g0 = max(max_g0, data.accG[0])
    max_g1 = max(max_g1, data.accG[1])
    min_g0 = min(min_g0, data.accG[0])
    min_g1 = min(min_g1, data.accG[1])
