from time import sleep, ticks_diff, ticks_ms

try:
    from ir_nec import NECRemote
    from kit_pins import IR_RECEIVER
except ImportError:
    from lib.ir_nec import NECRemote
    from lib.kit_pins import IR_RECEIVER


remote = NECRemote(IR_RECEIVER)
started = ticks_ms()
count = 0
last_raw = None

print("Press 0-9 now. Capture stops after 10 keys or 60 seconds.")

while count < 10 and ticks_diff(ticks_ms(), started) < 60000:
    code = remote.read()
    if code and code["raw"] != last_raw:
        count += 1
        last_raw = code["raw"]
        print(
            "%d addr=0x%02X cmd=0x%02X raw=0x%08X"
            % (count, code["address"], code["command"], code["raw"])
        )
    sleep(0.02)

print("Captured %d keys." % count)
