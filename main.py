from machine import I2C, Pin
from time import sleep, ticks_diff, ticks_ms

from boot import connect_wifi

try:
    import requests
except ImportError:
    import urequests as requests

try:
    from buzzer import Buzzer
    from ir_nec import NECRemote
    from kit_pins import (
        BUZZER,
        IR_RECEIVER,
        LED_GREEN,
        LED_RED,
        LED_YELLOW,
        OLED_SCL,
        OLED_SDA,
        RELAY,
    )
    from sh1106 import SH1106_I2C
    from ssd1306 import SSD1306_I2C
    from zh_oled import draw_lines
except ImportError:
    from lib.buzzer import Buzzer
    from lib.ir_nec import NECRemote
    from lib.kit_pins import (
        BUZZER,
        IR_RECEIVER,
        LED_GREEN,
        LED_RED,
        LED_YELLOW,
        OLED_SCL,
        OLED_SDA,
        RELAY,
    )
    from lib.sh1106 import SH1106_I2C
    from lib.ssd1306 import SSD1306_I2C
    from lib.zh_oled import draw_lines

try:
    from config import OLED_DRIVER
except ImportError:
    OLED_DRIVER = "ssd1306"


API_URL = (
    "https://api.open-meteo.com/v1/forecast?"
    "latitude=23.9769&longitude=121.6044"
    "&current=temperature_2m,relative_humidity_2m,"
    "apparent_temperature,weather_code,wind_speed_10m"
    "&daily=weather_code,temperature_2m_max,temperature_2m_min,"
    "precipitation_probability_max"
    "&timezone=Asia%2FTaipei&forecast_days=1"
)

SNAPSHOT = {
    "date": "2026-05-13",
    "time": "10:00",
    "condition": "Drizzle",
    "temp": 26.4,
    "feels": 31.2,
    "humidity": 78,
    "wind": 0.9,
    "high": 26.4,
    "low": 23.7,
    "rain": 100,
    "source": "Snapshot",
}

WEATHER_CODES = {
    0: "Clear",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Cloudy",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    80: "Rain showers",
    81: "Showers",
    82: "Heavy showers",
    95: "Thunderstorm",
}

REMOTE_NAMES = {
    0x45: "CH-",
    0x46: "CH",
    0x47: "CH+",
    0x44: "PREV",
    0x40: "NEXT",
    0x43: "PLAY",
    0x07: "VOL-",
    0x15: "VOL+",
    0x09: "EQ",
    0x16: "0",
    0x0C: "1",
    0x18: "2",
    0x5E: "3",
    0x08: "4",
    0x1C: "5",
    0x5A: "6",
    0x42: "7",
    0x52: "8",
    0x4A: "9",
}


def weather_name(code):
    return WEATHER_CODES.get(code, "Weather %s" % code)


def fetch_weather():
    response = requests.get(API_URL)
    try:
        data = response.json()
    finally:
        response.close()

    current = data["current"]
    daily = data["daily"]
    time_text = current["time"].split("T")
    code = daily["weather_code"][0]
    return {
        "date": time_text[0],
        "time": time_text[1],
        "condition": weather_name(code),
        "temp": current["temperature_2m"],
        "feels": current["apparent_temperature"],
        "humidity": current["relative_humidity_2m"],
        "wind": current["wind_speed_10m"],
        "high": daily["temperature_2m_max"][0],
        "low": daily["temperature_2m_min"][0],
        "rain": daily["precipitation_probability_max"][0],
        "source": "Open-Meteo",
    }


def format_weather(weather):
    return [
        "花蓮今日天氣",
        weather["date"][5:] + " " + weather["time"],
        "溫%.1fC 濕%d%%" % (weather["temp"], weather["humidity"]),
        "高%.1f 低%.1f" % (weather["high"], weather["low"]),
        "降雨%d%%" % weather["rain"],
    ]


def make_oled(i2c):
    if OLED_DRIVER.lower() == "sh1106":
        return SH1106_I2C(128, 64, i2c)
    return SSD1306_I2C(128, 64, i2c)


def toggle(pin):
    pin.value(0 if pin.value() else 1)


def handle_remote(code, outputs, buzzer):
    command = code["command"]
    name = REMOTE_NAMES.get(command, "UNKNOWN")
    action = "Show code"

    if command == 0x0C:
        toggle(outputs["red"])
        action = "紅燈"
    elif command == 0x18:
        toggle(outputs["yellow"])
        action = "黃燈"
    elif command == 0x5E:
        toggle(outputs["green"])
        action = "綠燈"
    elif command == 0x16:
        for pin in outputs.values():
            pin.value(0)
        action = "全部關"
    elif command == 0x43:
        toggle(outputs["relay"])
        action = "繼電器"
    elif command == 0x15:
        buzzer.tone(880, 0.08)
        action = "蜂鳴高"
    elif command == 0x07:
        buzzer.tone(440, 0.08)
        action = "蜂鳴低"
    elif command in (0x45, 0x46, 0x47):
        action = "天氣"

    return [
        "遙控器",
        "按鍵 " + name,
        "碼 0x%02X" % command,
        "Addr 0x%02X" % code["address"],
        "功能 " + action,
    ]


def main():
    i2c = I2C(0, scl=Pin(OLED_SCL), sda=Pin(OLED_SDA), freq=400000)
    oled = make_oled(i2c)
    remote = NECRemote(IR_RECEIVER)
    buzzer = Buzzer(BUZZER)
    outputs = {
        "red": Pin(LED_RED, Pin.OUT),
        "yellow": Pin(LED_YELLOW, Pin.OUT),
        "green": Pin(LED_GREEN, Pin.OUT),
        "relay": Pin(RELAY, Pin.OUT),
    }
    for pin in outputs.values():
        pin.value(0)

    draw_lines(oled, ["花蓮今日天氣", "WiFi"])
    wlan = connect_wifi(timeout_seconds=15)

    weather = SNAPSHOT
    if wlan and wlan.isconnected():
        try:
            weather = fetch_weather()
        except Exception as exc:
            weather = SNAPSHOT
            weather["source"] = "Saved"
            print("Weather fetch failed:", exc)
    else:
        print("Wi-Fi unavailable; showing saved weather snapshot.")

    draw_lines(oled, format_weather(weather))
    next_weather_refresh = ticks_ms() + 300000
    show_weather_at = ticks_ms()

    while True:
        code = remote.read()
        if code:
            lines = handle_remote(code, outputs, buzzer)
            draw_lines(oled, lines)
            show_weather_at = ticks_ms() + 2500
            print(
                "IR addr=0x%02X cmd=0x%02X raw=0x%08X"
                % (code["address"], code["command"], code["raw"])
            )

        now = ticks_ms()
        if ticks_diff(now, show_weather_at) >= 0:
            draw_lines(oled, format_weather(weather))
            show_weather_at = now + 300000

        if wlan and wlan.isconnected() and ticks_diff(now, next_weather_refresh) >= 0:
            try:
                weather = fetch_weather()
                draw_lines(oled, format_weather(weather))
            except Exception as exc:
                print("Weather refresh failed:", exc)
            next_weather_refresh = now + 300000

        sleep(0.02)


main()
