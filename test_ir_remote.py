from time import sleep

try:
    from ir_nec import NECRemote
    from kit_pins import IR_RECEIVER
except ImportError:
    from lib.ir_nec import NECRemote
    from lib.kit_pins import IR_RECEIVER


remote = NECRemote(IR_RECEIVER)

print("Press remote buttons. Ctrl+C to stop.")
while True:
    code = remote.read()
    if code:
        print(
            "addr=0x%02X cmd=0x%02X raw=0x%08X"
            % (code["address"], code["command"], code["raw"])
        )
    sleep(0.02)
