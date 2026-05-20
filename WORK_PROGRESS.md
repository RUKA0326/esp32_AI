# Work Progress

Date: 2026-05-20

## Today's Work: iPhone BLE UART Control

### Goal

Add Bluetooth support that works with iPhone 13. iPhone does not expose the
classic Bluetooth Serial Port Profile (SPP), so the project now uses BLE
with a Nordic UART compatible service.

### What Was Built

- `lib/ble_uart.py` -- reusable BLE UART service using:
  - Service UUID: `6E400001-B5A3-F393-E0A9-E50E24DCCA9E`
  - RX/write UUID: `6E400002-B5A3-F393-E0A9-E50E24DCCA9E`
  - TX/notify UUID: `6E400003-B5A3-F393-E0A9-E50E24DCCA9E`
- `main.py` keeps the existing NEC IR digit display and buzzer behavior, then
  adds BLE advertising as `ESP32-BLE`, phone commands, RGB/status LED control,
  and IR notifications to the phone.
- `tools/deploy.ps1` now prefers `.venv\Scripts\mpremote.exe` before falling
  back to `uv run mpremote`.

### iPhone 13 Test App

Use a BLE utility app such as `nRF Connect` or `LightBlue`. Scan for
`ESP32-BLE`, connect, enable notifications on TX, then write text commands
to RX.

### Phone Commands

```text
HELP
STATUS
RGB OFF
RGB RED
RGB GREEN
RGB BLUE
RGB WHITE
RGB 64 0 0
LED RED ON
LED YELLOW OFF
LED GREEN ON
LED ALL OFF
```

When an IR key is pressed, the phone receives a notification like:

```text
IR digit=5 addr=0x00 cmd=0x40 raw=0xBF40FF00
```

---

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
