from micropython import alloc_emergency_exception_buf, const
from machine import Pin
from time import ticks_diff, ticks_us


alloc_emergency_exception_buf(100)

_IDLE_US = const(25000)
_MIN_FRAME = const(66)
_MAX_PULSES = const(100)


def _near(value, target, margin):
    return target - margin <= value <= target + margin


class NECRemote:
    def __init__(self, pin, pull=None):
        mode = Pin.IN
        self.pin = Pin(pin, mode) if pull is None else Pin(pin, mode, pull)
        self._last = ticks_us()
        self._count = 0
        self._ready = False
        self._pulses = [0] * _MAX_PULSES
        self._last_code = None
        self.pin.irq(
            trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING,
            handler=self._edge,
        )

    def _edge(self, pin):
        now = ticks_us()
        duration = ticks_diff(now, self._last)
        self._last = now

        if duration > _IDLE_US:
            self._count = 0
            self._ready = False
            return

        if self._count < _MAX_PULSES:
            self._pulses[self._count] = duration
            self._count += 1

    def read(self):
        if self._count >= 4 and ticks_diff(ticks_us(), self._last) > _IDLE_US:
            self._ready = True

        if not self._ready:
            return None

        self.pin.irq(handler=None)
        count = self._count
        pulses = self._pulses[:count]
        self._count = 0
        self._ready = False
        self.pin.irq(
            trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING,
            handler=self._edge,
        )

        code = self._decode(pulses)
        if code == "REPEAT":
            return self._last_code
        if code is not None:
            self._last_code = code
        return code

    def _decode(self, pulses):
        if len(pulses) < 4:
            return None

        if _near(pulses[0], 9000, 1800) and _near(pulses[1], 2250, 800):
            return "REPEAT"

        if len(pulses) < _MIN_FRAME:
            return None
        if not (_near(pulses[0], 9000, 1800) and _near(pulses[1], 4500, 1200)):
            return None

        value = 0
        for bit in range(32):
            high = pulses[3 + bit * 2]
            if _near(high, 1690, 650):
                value |= 1 << bit
            elif not _near(high, 560, 350):
                return None

        address = value & 0xFF
        address_inv = (value >> 8) & 0xFF
        command = (value >> 16) & 0xFF
        command_inv = (value >> 24) & 0xFF

        if (address ^ address_inv) != 0xFF:
            return None
        if (command ^ command_inv) != 0xFF:
            return None

        return {
            "address": address,
            "command": command,
            "raw": value,
        }
