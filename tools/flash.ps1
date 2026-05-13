param(
    [string]$Port = "COM3",
    [Parameter(Mandatory = $true)]
    [string]$Firmware,
    [string]$Chip = "esp32",
    [string]$Address = "0x1000",
    [int]$Baud = 460800
)

uv run esptool --chip $Chip --port $Port erase_flash
uv run esptool --chip $Chip --port $Port --baud $Baud write_flash $Address $Firmware
