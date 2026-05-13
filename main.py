from machine import I2C, Pin
from time import sleep

try:
    from buzzer import Buzzer
    from ir_nec import NECRemote
    from kit_pins import BUZZER, IR_RECEIVER, OLED_SCL, OLED_SDA
    from sh1106 import SH1106_I2C
    from ssd1306 import SSD1306_I2C
except ImportError:
    from lib.buzzer import Buzzer
    from lib.ir_nec import NECRemote
    from lib.kit_pins import BUZZER, IR_RECEIVER, OLED_SCL, OLED_SDA
    from lib.sh1106 import SH1106_I2C
    from lib.ssd1306 import SSD1306_I2C

try:
    from config import OLED_DRIVER
except ImportError:
    OLED_DRIVER = "ssd1306"

try:
    from config import NEC_DIGIT_COMMANDS
except ImportError:
    NEC_DIGIT_COMMANDS = {
        0x19: "0",
        0x45: "1",
        0x46: "2",
        0x47: "3",
        0x44: "4",
        0x40: "5",
        0x43: "6",
        0x07: "7",
        0x15: "8",
        0x09: "9",
    }


SEGMENTS = {
    "0": "ABCDEF",
    "1": "BC",
    "2": "ABGED",
    "3": "ABGCD",
    "4": "FBGC",
    "5": "AFGCD",
    "6": "AFGECD",
    "7": "ABC",
    "8": "ABCDEFG",
    "9": "ABFGCD",
}


def make_oled(i2c):
    if OLED_DRIVER.lower() == "sh1106":
        return SH1106_I2C(128, 64, i2c)
    return SSD1306_I2C(128, 64, i2c)


def draw_segment(oled, segment, x, y, width, height, thickness):
    half = height // 2
    if segment == "A":
        oled.fill_rect(x + thickness, y, width - thickness * 2, thickness, 1)
    elif segment == "B":
        oled.fill_rect(x + width - thickness, y + thickness, thickness, half - thickness, 1)
    elif segment == "C":
        oled.fill_rect(x + width - thickness, y + half, thickness, half - thickness, 1)
    elif segment == "D":
        oled.fill_rect(x + thickness, y + height - thickness, width - thickness * 2, thickness, 1)
    elif segment == "E":
        oled.fill_rect(x, y + half, thickness, half - thickness, 1)
    elif segment == "F":
        oled.fill_rect(x, y + thickness, thickness, half - thickness, 1)
    elif segment == "G":
        oled.fill_rect(
            x + thickness,
            y + half - thickness // 2,
            width - thickness * 2,
            thickness,
            1,
        )


def draw_big_digit(oled, digit, x=86, y=6, width=38, height=52, thickness=6):
    for segment in SEGMENTS[digit]:
        draw_segment(oled, segment, x, y, width, height, thickness)


def show_ready(oled):
    oled.fill(0)
    oled.text("NEC IR READY", 0, 0)
    oled.text("Press 0-9", 0, 16)
    oled.text("IR pin: %d" % IR_RECEIVER, 0, 32)
    oled.show()


def show_digit(oled, digit, history, command):
    oled.fill(0)
    oled.text("Last:", 0, 0)
    oled.text("Digits:", 0, 24)
    oled.text(history[-10:], 0, 36)
    oled.text("cmd:%02X" % command, 0, 56)
    draw_big_digit(oled, digit)
    oled.show()


def show_unknown(oled, code):
    oled.fill(0)
    oled.text("NEC key", 0, 0)
    oled.text("Not mapped", 0, 14)
    oled.text("addr:%02X" % code["address"], 0, 30)
    oled.text("cmd :%02X" % code["command"], 0, 42)
    oled.text("raw:%08X" % code["raw"], 0, 56)
    oled.show()


def main():
    i2c = I2C(0, scl=Pin(OLED_SCL), sda=Pin(OLED_SDA), freq=400000)
    oled = make_oled(i2c)
    remote = NECRemote(IR_RECEIVER)
    buzzer = Buzzer(BUZZER)
    history = ""

    show_ready(oled)
    print("NEC IR ready. Press 0-9 on the remote.")

    while True:
        code = remote.read()
        if code:
            command = code["command"]
            digit = NEC_DIGIT_COMMANDS.get(command)
            if digit is None:
                show_unknown(oled, code)
                print(
                    "NEC unmapped addr=0x%02X cmd=0x%02X raw=0x%08X"
                    % (code["address"], command, code["raw"])
                )
            else:
                history += digit
                history = history[-32:]
                show_digit(oled, digit, history, command)
                buzzer.tone(1200, 0.03)
                print(
                    "NEC digit=%s addr=0x%02X cmd=0x%02X raw=0x%08X"
                    % (digit, code["address"], command, code["raw"])
                )
        sleep(0.02)


main()
