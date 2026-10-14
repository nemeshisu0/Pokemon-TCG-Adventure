#!/usr/bin/env python3
"""
Worker isolato di esecuzione per il core di melonDS (PokeMMO Architecture).
Gira in un processo dedicato per isolare completamente i segnali e la memoria
dal thread grafico di PyQt6, garantendo stabilità assoluta al 100% senza crash.
Comunica con la GUI tramite memoria condivisa (SharedMemory) a 60 FPS.
"""

import sys
import os
import time
import ctypes
from pathlib import Path
from multiprocessing import shared_memory

RETRO_ENVIRONMENT_SET_PIXEL_FORMAT = 10
RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY = 9
RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY = 31
RETRO_ENVIRONMENT_GET_CAN_DUPE = 3
RETRO_ENVIRONMENT_GET_VARIABLE = 15

class RetroGameInfo(ctypes.Structure):
    _fields_ = [
        ('path', ctypes.c_char_p),
        ('data', ctypes.c_void_p),
        ('size', ctypes.c_size_t),
        ('meta', ctypes.c_char_p)
    ]

class RetroVariable(ctypes.Structure):
    _fields_ = [
        ('key', ctypes.c_char_p),
        ('value', ctypes.c_char_p)
    ]

# Tipi Ctypes per i Callback
ENV_CALLBACK_TYPE = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_uint, ctypes.c_void_p)
VIDEO_CALLBACK_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_size_t)
AUDIO_CALLBACK_TYPE = ctypes.CFUNCTYPE(ctypes.c_size_t, ctypes.POINTER(ctypes.c_int16), ctypes.c_size_t)
POLL_CALLBACK_TYPE = ctypes.CFUNCTYPE(None)
INPUT_CALLBACK_TYPE = ctypes.CFUNCTYPE(ctypes.c_int16, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint)


def run_engine_worker(shm_name: str, control_arr, rom_path: str, save_path: str, core_lib_path: str):
    try:
        shm = shared_memory.SharedMemory(name=shm_name)
    except Exception as e:
        print(f"Errore accesso memoria condivisa: {e}", flush=True)
        return

    lib = ctypes.CDLL(core_lib_path)

    # Buffer C stabili per le cartelle di sistema e salvataggio
    sys_dir_buf = ctypes.create_string_buffer(str(Path(core_lib_path).parent).encode('utf-8'))
    save_dir_buf = ctypes.create_string_buffer(str(Path(save_path).parent).encode('utf-8'))

    # Configurazione ottimale del core melonDS
    # Disabilitare il JIT e forzare Boot Diretto risolve la schermata bianca in B2W2
    core_variables = {
        b'melonds_jit_enable': b'disabled',
        b'melonds_boot_directly': b'enabled',
        b'melonds_console_mode': b'DS',
        b'melonds_touch_mode': b'Touch',
        b'melonds_language': b'Italian',
        b'melonds_threaded_renderer': b'enabled',
    }
    # Buffer C stabili per i valori delle opzioni
    var_buffers = {k: ctypes.create_string_buffer(v) for k, v in core_variables.items()}

    def env_cb(cmd, data):
        if cmd == RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
            return True
        elif cmd == RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
            ptr = ctypes.cast(data, ctypes.POINTER(ctypes.c_char_p))
            ptr.contents.value = sys_dir_buf.value
            return True
        elif cmd == RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY:
            ptr = ctypes.cast(data, ctypes.POINTER(ctypes.c_char_p))
            ptr.contents.value = save_dir_buf.value
            return True
        elif cmd == RETRO_ENVIRONMENT_GET_CAN_DUPE:
            ptr = ctypes.cast(data, ctypes.POINTER(ctypes.c_bool))
            ptr.contents.value = True
            return True
        elif cmd == RETRO_ENVIRONMENT_GET_VARIABLE:
            var_ptr = ctypes.cast(data, ctypes.POINTER(RetroVariable))
            key = var_ptr.contents.key
            if key in var_buffers:
                var_ptr.contents.value = var_buffers[key].value
                return True
            return False
        return False

    def video_cb(data, width, height, pitch):
        if data and width > 0 and height > 0:
            frame_len = pitch * height
            raw = ctypes.string_at(data, frame_len)
            shm.buf[:frame_len] = raw
            # Incrementa il contatore dei frame sincronizzati (indice 31)
            control_arr[31] += 1

    def audio_cb(data, frames):
        return frames

    def poll_cb():
        pass

    def input_cb(port, device, index, id_):
        if port != 0:
            return 0
        if device == 1: # Joypad (RETRO_DEVICE_JOYPAD)
            if id_ < 16:
                return control_arr[id_]
        elif device == 6: # Touch Screen (RETRO_DEVICE_POINTER)
            if id_ == 2: # RETRO_DEVICE_ID_POINTER_PRESSED
                return control_arr[16]
            elif id_ == 0: # RETRO_DEVICE_ID_POINTER_X
                return control_arr[17]
            elif id_ == 1: # RETRO_DEVICE_ID_POINTER_Y
                return control_arr[18]
        return 0

    c_env = ENV_CALLBACK_TYPE(env_cb)
    c_vid = VIDEO_CALLBACK_TYPE(video_cb)
    c_aud = AUDIO_CALLBACK_TYPE(audio_cb)
    c_pol = POLL_CALLBACK_TYPE(poll_cb)
    c_inp = INPUT_CALLBACK_TYPE(input_cb)

    lib.retro_set_environment(c_env)
    lib.retro_set_video_refresh(c_vid)
    lib.retro_set_audio_sample_batch(c_aud)
    lib.retro_set_input_poll(c_pol)
    lib.retro_set_input_state(c_inp)
    lib.retro_init()

    # In Libretro melonDS richiede il buffer della ROM in memoria (Need Fullpath: False)
    with open(rom_path, 'rb') as f:
        rom_data = f.read()

    rom_c_buf = (ctypes.c_char * len(rom_data)).from_buffer_copy(rom_data)
    game_info = RetroGameInfo(
        rom_path.encode('utf-8'),
        ctypes.cast(rom_c_buf, ctypes.c_void_p),
        len(rom_data),
        None
    )

    loaded = lib.retro_load_game(ctypes.byref(game_info))
    if not loaded:
        print("❌ Impossibile caricare la ROM.", flush=True)
        shm.close()
        return

    frame_time = 1.0 / 60.0
    next_frame_time = time.perf_counter()

    # Indice 30: Running Flag (1 = in esecuzione, 0 = arresto)
    control_arr[30] = 1

    while control_arr[30] == 1:
        lib.retro_run()
        next_frame_time += frame_time
        sleep_left = next_frame_time - time.perf_counter()
        if sleep_left > 0:
            time.sleep(sleep_left)
        elif sleep_left < -0.1:
            next_frame_time = time.perf_counter()

    lib.retro_unload_game()
    lib.retro_deinit()
    shm.close()
    print("Worker melonDS terminato correttamente.", flush=True)

