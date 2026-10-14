#!/usr/bin/env python3
"""
Thread di ascolto per Gamepad / Controller USB & Bluetooth (Linux evdev).
Rileva automaticamente i controller collegati e invia lo stato dei pulsanti
direttamente all'emulatore melonDS a latenza zero.
"""

import threading
import time
from pathlib import Path

# Libretro Joypad Button IDs
RETRO_DEVICE_ID_JOYPAD_B = 0
RETRO_DEVICE_ID_JOYPAD_Y = 1
RETRO_DEVICE_ID_JOYPAD_SELECT = 2
RETRO_DEVICE_ID_JOYPAD_START = 3
RETRO_DEVICE_ID_JOYPAD_UP = 4
RETRO_DEVICE_ID_JOYPAD_DOWN = 5
RETRO_DEVICE_ID_JOYPAD_LEFT = 6
RETRO_DEVICE_ID_JOYPAD_RIGHT = 7
RETRO_DEVICE_ID_JOYPAD_A = 8
RETRO_DEVICE_ID_JOYPAD_X = 9
RETRO_DEVICE_ID_JOYPAD_L = 10
RETRO_DEVICE_ID_JOYPAD_R = 11

EVDEV_BTN_MAP = {
    304: RETRO_DEVICE_ID_JOYPAD_A,     # BTN_SOUTH / BTN_A
    305: RETRO_DEVICE_ID_JOYPAD_B,     # BTN_EAST / BTN_B
    307: RETRO_DEVICE_ID_JOYPAD_X,     # BTN_WEST / BTN_X
    308: RETRO_DEVICE_ID_JOYPAD_Y,     # BTN_NORTH / BTN_Y
    310: RETRO_DEVICE_ID_JOYPAD_L,     # BTN_TL (L1)
    311: RETRO_DEVICE_ID_JOYPAD_R,     # BTN_TR (R1)
    314: RETRO_DEVICE_ID_JOYPAD_SELECT,# BTN_SELECT / BACK
    315: RETRO_DEVICE_ID_JOYPAD_START, # BTN_START / OPTIONS
    # D-pad standard buttons
    544: RETRO_DEVICE_ID_JOYPAD_UP,    # BTN_DPAD_UP
    545: RETRO_DEVICE_ID_JOYPAD_DOWN,  # BTN_DPAD_DOWN
    546: RETRO_DEVICE_ID_JOYPAD_LEFT,  # BTN_DPAD_LEFT
    547: RETRO_DEVICE_ID_JOYPAD_RIGHT, # BTN_DPAD_RIGHT
}


class GamepadListener(threading.Thread):
    def __init__(self, emu_thread):
        super().__init__(daemon=True)
        self.emu_thread = emu_thread
        self.running = True

    def run(self):
        try:
            import evdev
        except ImportError:
            return

        while self.running:
            # Trova un controller collegato
            dev = None
            try:
                for path in evdev.list_devices():
                    d = evdev.InputDevice(path)
                    caps = d.capabilities()
                    # Verifica presenza di tasti gamepad (EV_KEY)
                    if 1 in caps:
                        keys = caps[1]
                        if 304 in keys or 305 in keys or 310 in keys:
                            dev = d
                            break
            except Exception:
                pass

            if not dev:
                time.sleep(1.5)
                continue

            try:
                for event in dev.read_loop():
                    if not self.running:
                        break

                    # Gestione Pulsanti Standard
                    if event.type == 1: # EV_KEY
                        if event.code in EVDEV_BTN_MAP:
                            retro_id = EVDEV_BTN_MAP[event.code]
                            self.emu_thread.set_key(retro_id, bool(event.value))

                    # Gestione D-Pad Analogico o Hat (ABS_HAT0X, ABS_HAT0Y)
                    elif event.type == 3: # EV_ABS
                        if event.code == 16: # ABS_HAT0X (Orizzontale)
                            if event.value == -1:
                                self.emu_thread.set_key(RETRO_DEVICE_ID_JOYPAD_LEFT, True)
                                self.emu_thread.set_key(RETRO_DEVICE_ID_JOYPAD_RIGHT, False)
                            elif event.value == 1:
                                self.emu_thread.set_key(RETRO_DEVICE_ID_JOYPAD_RIGHT, True)
                                self.emu_thread.set_key(RETRO_DEVICE_ID_JOYPAD_LEFT, False)
                            else:
                                self.emu_thread.set_key(RETRO_DEVICE_ID_JOYPAD_LEFT, False)
                                self.emu_thread.set_key(RETRO_DEVICE_ID_JOYPAD_RIGHT, False)

                        elif event.code == 17: # ABS_HAT0Y (Verticale)
                            if event.value == -1:
                                self.emu_thread.set_key(RETRO_DEVICE_ID_JOYPAD_UP, True)
                                self.emu_thread.set_key(RETRO_DEVICE_ID_JOYPAD_DOWN, False)
                            elif event.value == 1:
                                self.emu_thread.set_key(RETRO_DEVICE_ID_JOYPAD_DOWN, True)
                                self.emu_thread.set_key(RETRO_DEVICE_ID_JOYPAD_UP, False)
                            else:
                                self.emu_thread.set_key(RETRO_DEVICE_ID_JOYPAD_UP, False)
                                self.emu_thread.set_key(RETRO_DEVICE_ID_JOYPAD_DOWN, False)
            except Exception:
                time.sleep(1.0)

    def stop(self):
        self.running = False

