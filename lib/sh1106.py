from micropython import const
import framebuf


_SET_CONTRAST = const(0x81)
_SET_NORM_INV = const(0xA6)
_SET_DISP = const(0xAE)
_SET_SCAN_DIR = const(0xC8)
_SET_SEG_REMAP = const(0xA1)
_LOW_COLUMN = const(0x00)
_HIGH_COLUMN = const(0x10)
_PAGE_ADDRESS = const(0xB0)


class SH1106_I2C(framebuf.FrameBuffer):
    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        self.width = width
        self.height = height
        self.i2c = i2c
        self.addr = addr
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def write_cmd(self, cmd):
        self.i2c.writeto(self.addr, bytearray([0x80, cmd]))

    def write_data(self, data):
        self.i2c.writeto(self.addr, b"\x40" + data)

    def init_display(self):
        for cmd in (
            _SET_DISP,
            0xD5,
            0x80,
            0xA8,
            self.height - 1,
            0xD3,
            0x00,
            0x40,
            0xAD,
            0x8B,
            0xA4,
            _SET_NORM_INV,
            0xD9,
            0x22 if self.external_vcc else 0xF1,
            0xDB,
            0x40,
            _SET_SEG_REMAP,
            _SET_SCAN_DIR,
            _SET_CONTRAST,
            0x7F,
            _SET_DISP | 0x01,
        ):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(_SET_DISP)

    def poweron(self):
        self.write_cmd(_SET_DISP | 0x01)

    def contrast(self, contrast):
        self.write_cmd(_SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(0xA7 if invert else _SET_NORM_INV)

    def show(self):
        for page in range(self.pages):
            self.write_cmd(_PAGE_ADDRESS | page)
            # SH1106 uses a 132-column RAM. Most 128x64 modules need +2 offset.
            self.write_cmd(_LOW_COLUMN | 0x02)
            self.write_cmd(_HIGH_COLUMN | 0x00)
            start = self.width * page
            end = start + self.width
            self.write_data(self.buffer[start:end])
