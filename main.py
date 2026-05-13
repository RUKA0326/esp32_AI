from machine import I2C, Pin
from time import sleep

from boot import connect_wifi

try:
    import requests
except ImportError:
    import urequests as requests

try:
    from kit_pins import OLED_SCL, OLED_SDA
    from sh1106 import SH1106_I2C
    from ssd1306 import SSD1306_I2C
except ImportError:
    from lib.kit_pins import OLED_SCL, OLED_SDA
    from lib.sh1106 import SH1106_I2C
    from lib.ssd1306 import SSD1306_I2C

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


def fit(text):
    return str(text)[:16]


def draw(oled, lines):
    oled.fill(0)
    for row, line in enumerate(lines[:6]):
        oled.text(fit(line), 0, row * 10)
    oled.show()


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
        "Hualien Today",
        weather["date"][5:] + " " + weather["time"],
        weather["condition"],
        "Now %.1fC RH %d%%" % (weather["temp"], weather["humidity"]),
        "H %.1f L %.1fC" % (weather["high"], weather["low"]),
        "Rain %d%% %s" % (weather["rain"], weather["source"]),
    ]


def make_oled(i2c):
    if OLED_DRIVER.lower() == "sh1106":
        return SH1106_I2C(128, 64, i2c)
    return SSD1306_I2C(128, 64, i2c)


def main():
    i2c = I2C(0, scl=Pin(OLED_SCL), sda=Pin(OLED_SDA), freq=400000)
    oled = make_oled(i2c)

    draw(oled, ["Hualien Weather", "Connecting WiFi"])
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

    while True:
        draw(oled, format_weather(weather))
        sleep(300)
        if wlan and wlan.isconnected():
            try:
                weather = fetch_weather()
            except Exception as exc:
                print("Weather refresh failed:", exc)


main()
