WIFI_SSID = "your-wifi-ssid"
WIFI_PASSWORD = "your-wifi-password"
OLED_DRIVER = "ssd1306"  # use "sh1106" if your OLED module needs it

# Optional: override this if your NEC remote uses different command codes.
# Run `uv run mpremote connect COM3 run test_ir_remote.py`, press each key,
# then replace the command values below.
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
