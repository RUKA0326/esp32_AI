# Work Progress

Date: 2026-05-06

## Current ESP32 LED Test

- Board connection: `COM3`
- Runtime: ESP32 MicroPython with `mpremote`
- Main program: `main.py`
- Full-color LED type: WS2812 / NeoPixel
- NeoPixel data pin: GPIO `26`
- NeoPixel count: `3`

## Current Behavior

The ESP32 now runs an RGB blink test on boot:

- Pixel 1 lights red at brightness `64`
- Pixel 2 lights green at brightness `64`
- Pixel 3 lights blue at brightness `64`
- LEDs stay on for `1` second
- LEDs turn off for `1` second
- This repeats `10` times, for about `20` seconds total
- All NeoPixels are turned off at the end

The normal red, yellow, and green status LEDs are turned off before the RGB test starts:

- Red LED: GPIO `16`
- Yellow LED: GPIO `12`
- Green LED: GPIO `13`

## Files Updated

- `main.py`: boot program for the RGB blink test
- `test_rgb_once.py`: direct `mpremote run` test file for the same RGB behavior

## Commands Used

```powershell
.\.venv\Scripts\mpremote.exe connect COM3 run test_rgb_once.py
.\.venv\Scripts\mpremote.exe connect COM3 cp main.py :main.py
.\.venv\Scripts\mpremote.exe connect COM3 reset
```

Note: Global `uv` was not available in this terminal, so the project virtual environment's `mpremote.exe` was used directly.
