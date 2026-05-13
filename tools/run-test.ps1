param(
    [string]$File = "test_led.py",
    [string]$Port = "COM3"
)

uv run mpremote connect $Port run $File
