import bluetooth
from machine import I2C, Pin
from neopixel import NeoPixel
from time import sleep

try:
    from ble_uart import BLEUART
    from buzzer import Buzzer
    from ir_nec import NECRemote
    from kit_pins import (
        BUZZER,
        IR_RECEIVER,
        LED_GREEN,
        LED_RED,
        LED_YELLOW,
        NEOPIXEL,
        OLED_SCL,
        OLED_SDA,
    )
    from sh1106 import SH1106_I2C
    from ssd1306 import SSD1306_I2C
except ImportError:
    from lib.ble_uart import BLEUART
    from lib.buzzer import Buzzer
    from lib.ir_nec import NECRemote
    from lib.kit_pins import (
        BUZZER,
        IR_RECEIVER,
        LED_GREEN,
        LED_RED,
        LED_YELLOW,
        NEOPIXEL,
        OLED_SCL,
        OLED_SDA,
    )
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

DEVICE_NAME = "ESP32-BLE"
NUM_PIXELS = 3

COLOR_BY_NAME = {
    "OFF": (0, 0, 0),
    "RED": (64, 0, 0),
    "GREEN": (0, 64, 0),
    "BLUE": (0, 0, 64),
    "WHITE": (64, 64, 64),
    "CYAN": (0, 64, 64),
    "MAGENTA": (64, 0, 64),
    "YELLOW": (64, 64, 0),
}

status_leds = {
    "RED": Pin(LED_RED, Pin.OUT),
    "YELLOW": Pin(LED_YELLOW, Pin.OUT),
    "GREEN": Pin(LED_GREEN, Pin.OUT),
}
pixels = NeoPixel(Pin(NEOPIXEL), NUM_PIXELS)


def make_oled(i2c):
    if OLED_DRIVER.lower() == "sh1106":
        return SH1106_I2C(128, 64, i2c)
    return SSD1306_I2C(128, 64, i2c)


def clamp_byte(value):
    return max(0, min(255, int(value)))


def set_rgb(red, green, blue):
    color = (clamp_byte(red), clamp_byte(green), clamp_byte(blue))
    for index in range(NUM_PIXELS):
        pixels[index] = color
    pixels.write()
    return color


def set_status_led(name, state):
    led = status_leds.get(name)
    if led is None:
        return False
    led.value(1 if state else 0)
    return True


def parse_rgb(parts):
    if len(parts) == 2 and parts[1] in COLOR_BY_NAME:
        return COLOR_BY_NAME[parts[1]]

    if len(parts) == 4:
        try:
            return (
                clamp_byte(parts[1]),
                clamp_byte(parts[2]),
                clamp_byte(parts[3]),
            )
        except ValueError:
            return None

    return None


def help_text():
    return (
        "Commands:\n"
        "HELP\n"
        "STATUS\n"
        "RGB OFF|RED|GREEN|BLUE|WHITE\n"
        "RGB 64 0 0\n"
        "LED RED|YELLOW|GREEN ON|OFF\n"
        "LED ALL ON|OFF\n"
    )


def handle_ble_command(text, ble):
    cleaned = text.strip()
    if not cleaned:
        return

    upper = cleaned.upper().replace(",", " ")
    parts = upper.split()
    print("BLE command:", cleaned)

    if upper in ("HELP", "?"):
        ble.send(help_text())
        return

    if upper == "STATUS":
        led_state = ",".join(
            "%s=%d" % (name[0], led.value()) for name, led in status_leds.items()
        )
        ble.send("STATUS BLE=ON RGB=%d LED %s\n" % (NUM_PIXELS, led_state))
        return

    if parts and parts[0] == "RGB":
        color = parse_rgb(parts)
        if color is None:
            ble.send("ERR RGB. Try: RGB RED or RGB 64 0 0\n")
            return

        set_rgb(*color)
        ble.send("OK RGB %d %d %d\n" % color)
        return

    if len(parts) == 3 and parts[0] == "LED":
        target = parts[1]
        state_text = parts[2]
        if state_text not in ("ON", "OFF"):
            ble.send("ERR LED state must be ON or OFF\n")
            return

        state = state_text == "ON"
        if target == "ALL":
            for led_name in status_leds:
                set_status_led(led_name, state)
            ble.send("OK LED ALL %s\n" % state_text)
            return

        if set_status_led(target, state):
            ble.send("OK LED %s %s\n" % (target, state_text))
            return

    ble.send("ERR unknown command. Send HELP\n")


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
    for led_name in status_leds:
        set_status_led(led_name, False)
    set_rgb(0, 0, 0)

    i2c = I2C(0, scl=Pin(OLED_SCL), sda=Pin(OLED_SDA), freq=400000)
    oled = make_oled(i2c)
    remote = NECRemote(IR_RECEIVER)
    buzzer = Buzzer(BUZZER)
    rx_queue = []
    ble_events = []
    ble = BLEUART(bluetooth.BLE(), name=DEVICE_NAME)
    ble.on_write(lambda data: rx_queue.append(data))
    ble.on_connect(lambda conn: ble_events.append("connected"))
    ble.on_disconnect(lambda conn: ble_events.append("advertising"))
    history = ""

    show_ready(oled)
    print("NEC IR ready. Press 0-9 on the remote.")
    print("%s advertising for iPhone BLE apps." % DEVICE_NAME)
    print("Use nRF Connect or LightBlue, enable TX notify, then write HELP on RX.")

    while True:
        while ble_events:
            state = ble_events.pop(0)
            print("BLE", state)
            if state == "connected":
                ble.send("Connected to %s. Send HELP\n" % DEVICE_NAME)

        while rx_queue:
            raw = rx_queue.pop(0)
            try:
                text = raw.decode().strip()
            except UnicodeError:
                text = ""

            for line in text.splitlines() or [text]:
                handle_ble_command(line, ble)

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
                ble.send(
                    "IR unmapped addr=0x%02X cmd=0x%02X raw=0x%08X\n"
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
                ble.send(
                    "IR digit=%s addr=0x%02X cmd=0x%02X raw=0x%08X\n"
                    % (digit, code["address"], command, code["raw"])
                )
        sleep(0.02)


main()
