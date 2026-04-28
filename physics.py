import mmap
import ctypes
import random
import json
import os


class MockPhysics:
    def __init__(self):
        self.packetId = 0

        self.gas = 0.0
        self.brake = 0.0
        self.fuel = 60.0

        self.gear = 1
        self.rpms = 1000
        self.speedKmh = 0.0

    def update(self):
        # symulacja wejść kierowcy
        self.gas = max(0.0, min(1.0, self.gas + random.uniform(-0.1, 0.1)))
        self.brake = max(0.0, min(1.0, self.brake + random.uniform(-0.05, 0.05)))

        # symulacja RPM
        target_rpm = 1000 + self.gas * 7000
        self.rpms += int((target_rpm - self.rpms) * 0.1)

        # symulacja prędkości
        self.speedKmh += self.gas * 2 - self.brake * 3
        self.speedKmh = max(0.0, self.speedKmh)

        # biegi
        if self.rpms > 6500:
            self.gear = min(6, self.gear + 1)
            self.rpms -= 2000
        elif self.rpms < 2000:
            self.gear = max(1, self.gear - 1)

        # paliwo
        self.fuel -= self.gas * 0.01
        self.fuel = max(0.0, self.fuel)

        self.packetId += 1


class CarConfigLoader:
    def __init__(self, car):
        self.car = car
        self.path = rf"C:\Users\Guest\Desktop\telemetry\cars_config\{car}.json"
        if not os.path.exists(self.path):
            self.car = "Default"
            self.path = rf"C:\Users\Guest\Desktop\telemetry\cars_config\default.json"

    def load(self):
        print(f"Loaded car config: {self.car}")
        with open(self.path) as f:
            return json.load(f)


class ACPhysics:
    """
    Reader shared memory: acpmf_physics
    """

    # =========================
    # STRUKTURA
    # =========================
    class SPageFilePhysics(ctypes.Structure):
        _pack_ = 4
        _fields_ = [
            # ===== GLOBAL =====
            ("packetId", ctypes.c_int),
            # ===== PEDAŁY =====
            ("gas", ctypes.c_float),
            ("brake", ctypes.c_float),
            ("fuel", ctypes.c_float),
            # ===== BIEGI / SILNIK =====
            ("gear", ctypes.c_int),
            ("rpms", ctypes.c_int),
            # ===== RUCH =====
            ("steerAngle", ctypes.c_float),
            ("speedKmh", ctypes.c_float),
            # ===== PRĘDKOŚCI WEKTOROWE =====
            ("velocity", ctypes.c_float * 3),
            ("accG", ctypes.c_float * 3),
            # ===== KOŁA =====
            ("wheelSlip", ctypes.c_float * 4),
            ("wheelLoad", ctypes.c_float * 4),
            ("wheelsPressure", ctypes.c_float * 4),
            ("wheelAngularSpeed", ctypes.c_float * 4),
            ("tyreWear", ctypes.c_float * 4),
            ("tyreDirtyLevel", ctypes.c_float * 4),
            ("tyreCoreTemperature", ctypes.c_float * 4),
            # ===== ZAWIESZENIE =====
            ("camberRAD", ctypes.c_float * 4),
            ("suspensionTravel", ctypes.c_float * 4),
            # ===== ELEKTRONIKA =====
            ("drs", ctypes.c_float),
            ("tc", ctypes.c_float),
            ("heading", ctypes.c_float),
            ("pitch", ctypes.c_float),
            ("roll", ctypes.c_float),
            # ===== TOR / KONTAKT =====
            ("cgHeight", ctypes.c_float),
            ("carDamage", ctypes.c_float * 5),
            ("numberOfTyresOut", ctypes.c_int),
            # ===== PIT / LIMITER =====
            ("pitLimiterOn", ctypes.c_int),
            ("abs", ctypes.c_float),
            # ===== TEMPERATURY =====
            ("kersCharge", ctypes.c_float),
            ("kersInput", ctypes.c_float),
            ("autoShifterOn", ctypes.c_int),
            ("rideHeight", ctypes.c_float * 2),
            ("turboBoost", ctypes.c_float),
            # ===== BALANS HAMULCÓW =====
            ("ballast", ctypes.c_float),
            ("airDensity", ctypes.c_float),
            # ===== KOŁA 2 =====
            ("airTemp", ctypes.c_float),
            ("roadTemp", ctypes.c_float),
            ("localAngularVel", ctypes.c_float * 3),
            ("finalFF", ctypes.c_float),
            # ===== DODATKOWE =====
            ("performanceMeter", ctypes.c_float),
            ("engineBrake", ctypes.c_int),
            ("ersRecoveryLevel", ctypes.c_int),
            ("ersPowerLevel", ctypes.c_int),
            ("ersHeatCharging", ctypes.c_int),
            ("ersIsCharging", ctypes.c_int),
            ("kersCurrentKJ", ctypes.c_float),
            ("drsAvailable", ctypes.c_int),
            ("drsEnabled", ctypes.c_int),
            ("brakeTemp", ctypes.c_float * 4),
            ("clutch", ctypes.c_float),
            ("tyreTempI", ctypes.c_float * 4),
            ("tyreTempM", ctypes.c_float * 4),
            ("tyreTempO", ctypes.c_float * 4),
            ("isAIControlled", ctypes.c_int),
            ("tyreContactPoint", ctypes.c_float * 12),
            ("tyreContactNormal", ctypes.c_float * 12),
            ("tyreContactHeading", ctypes.c_float * 12),
            ("brakeBias", ctypes.c_float),
        ]

    # =========================
    # INIT
    # =========================
    def __init__(self):
        self.mm = None
        self.physics = None
        self.last_packet = -1

        self.connected = self._connect()

    # =========================
    # POŁĄCZENIE
    # =========================
    def _connect(self):
        try:
            size = ctypes.sizeof(self.SPageFilePhysics)

            self.mm = mmap.mmap(0, size, "acpmf_physics")

            self.physics = self.SPageFilePhysics.from_buffer(self.mm)

            return True

        except Exception:
            return False

    # =========================
    # UPDATE (NA ŻYWO)
    # =========================
    def update(self):
        if not self.connected:
            return False

        return self.physics.packetId != self.last_packet

    # =========================
    # POBIERANIE DANYCH
    # =========================
    def get(self):
        if not self.connected:
            return None

        self.last_packet = self.physics.packetId

        def convert(value):
            # stringi / bytes
            if isinstance(value, bytes):
                return value.decode("utf-8", errors="ignore").rstrip("\x00")
            # tablice ctypes
            if hasattr(value, "__len__") and not isinstance(value, (str, bytes)):
                try:
                    return [convert(v) for v in value]
                except:
                    return value
            return value

        return {
            field_name: convert(getattr(self.physics, field_name))
            for field_name, _ in self.physics._fields_
        }

    # =========================
    # CLEANUP
    # =========================
    def close(self):
        if self.mm:
            self.mm.close()


class ACStatic:
    """
    Reader shared memory: acpmf_static
    """

    class SPageFileStatic(ctypes.Structure):
        _pack_ = 1
        _fields_ = [
            ("smVersion", ctypes.c_wchar * 15),
            ("acVersion", ctypes.c_wchar * 15),
            ("numberOfSessions", ctypes.c_int),
            ("numCars", ctypes.c_int),
            ("carModel", ctypes.c_wchar * 33),
            ("track", ctypes.c_wchar * 33),
            ("playerName", ctypes.c_wchar * 33),
            ("playerSurname", ctypes.c_wchar * 33),
            ("sectorCount", ctypes.c_int),
            ("maxTorque", ctypes.c_float),
            ("maxPower", ctypes.c_float),
            ("maxRpm", ctypes.c_int),
            ("maxFuel", ctypes.c_float),
            ("suspensionMaxTravel", ctypes.c_float * 4),
            ("tyreRadius", ctypes.c_float * 4),
            ("maxTurboBoost", ctypes.c_float),
        ]

    # =========================
    # INIT
    # =========================
    def __init__(self):
        self.mm = None
        self.static = None
        self.connected = self._connect()

    # =========================
    # POŁĄCZENIE
    # =========================
    def _connect(self):
        try:
            size = ctypes.sizeof(self.SPageFileStatic)

            self.mm = mmap.mmap(0, size, "acpmf_static")

            self.static = self.SPageFileStatic.from_buffer(self.mm)

            return True

        except Exception:
            return False

    def get(self):
        if not self.connected:
            return None

        def convert(value):
            # stringi / bytes
            if isinstance(value, bytes):
                return value.decode("utf-8", errors="ignore").rstrip("\x00")
            # tablice ctypes
            if hasattr(value, "__len__") and not isinstance(value, (str, bytes)):
                try:
                    return [convert(v) for v in value]
                except:
                    return value
            return value

        return {
            field_name: convert(getattr(self.static, field_name))
            for field_name, _ in self.static._fields_
        }

    def close(self):
        if self.mm:
            self.mm.close()


class PhysicsConnector:
    def __init__(self):
        self.physics = ACPhysics()
        self.static = ACStatic()
        self.car_loader = CarConfigLoader(self.static.get()["carModel"])
        self.car_config = self.car_loader.load()

    def get(self, *args):
        self.physics.update()

        d_physics = self.physics.get()  # returns dict
        d_static = self.static.get()  # returns dict

        combined = d_physics | d_static | self.car_config
        if len(args) > 1:
            return {arg: combined.get(arg) for arg in args}
        return combined[args[0]]


conn = PhysicsConnector()
print(conn.get("speedKmh", "rpms", "wheelSlip"))
