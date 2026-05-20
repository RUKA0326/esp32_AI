import bluetooth
import struct
from micropython import const


_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_UUID16_COMPLETE = const(0x03)
_ADV_TYPE_UUID32_COMPLETE = const(0x05)
_ADV_TYPE_UUID128_COMPLETE = const(0x07)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    bluetooth.FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    bluetooth.FLAG_WRITE | getattr(bluetooth, "FLAG_WRITE_NO_RESPONSE", 0),
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)


def advertising_payload(name=None, services=None):
    payload = bytearray()

    def append(adv_type, value):
        payload.extend(struct.pack("BB", len(value) + 1, adv_type))
        payload.extend(value)

    append(_ADV_TYPE_FLAGS, struct.pack("B", 0x06))

    if name:
        append(_ADV_TYPE_NAME, name.encode() if isinstance(name, str) else name)

    if services:
        for uuid in services:
            data = bytes(uuid)
            if len(data) == 2:
                append(_ADV_TYPE_UUID16_COMPLETE, data)
            elif len(data) == 4:
                append(_ADV_TYPE_UUID32_COMPLETE, data)
            elif len(data) == 16:
                append(_ADV_TYPE_UUID128_COMPLETE, data)

    return payload


class BLEUART:
    """Nordic UART compatible BLE service for phone apps like nRF Connect."""

    def __init__(self, ble, name="ESP32-BLE", rxbuf=100):
        self._ble = ble
        self._name = name
        self._connections = set()
        self._write_callback = None
        self._connect_callback = None
        self._disconnect_callback = None

        self._ble.active(True)
        self._ble.config(gap_name=name)
        self._ble.irq(self._irq)
        ((self._tx_handle, self._rx_handle),) = self._ble.gatts_register_services(
            (_UART_SERVICE,)
        )
        self._ble.gatts_set_buffer(self._rx_handle, rxbuf, True)
        self.advertise()

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            if self._connect_callback:
                self._connect_callback(conn_handle)

        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self._connections.discard(conn_handle)
            if self._disconnect_callback:
                self._disconnect_callback(conn_handle)
            self.advertise()

        elif event == _IRQ_GATTS_WRITE:
            _, value_handle = data
            if value_handle == self._rx_handle and self._write_callback:
                self._write_callback(self._ble.gatts_read(self._rx_handle))

    def on_write(self, callback):
        self._write_callback = callback

    def on_connect(self, callback):
        self._connect_callback = callback

    def on_disconnect(self, callback):
        self._disconnect_callback = callback

    def advertise(self, interval_us=500000):
        payload = advertising_payload(name=self._name)
        self._ble.gap_advertise(interval_us, adv_data=payload)

    def is_connected(self):
        return bool(self._connections)

    def send(self, data):
        if not self._connections:
            return

        if isinstance(data, str):
            data = data.encode()

        for conn_handle in self._connections:
            for start in range(0, len(data), 20):
                self._ble.gatts_notify(conn_handle, self._tx_handle, data[start:start + 20])

    def close(self):
        for conn_handle in self._connections:
            self._ble.gap_disconnect(conn_handle)
        self._connections.clear()
        self._ble.active(False)
