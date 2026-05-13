param(
    [string]$Port = "COM3"
)

uv run mpremote connect $Port cp boot.py :
uv run mpremote connect $Port cp main.py :
uv run mpremote connect $Port cp -r ./lib :
uv run mpremote connect $Port reset
