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

# Costanti per accesso alla memoria del DS
RETRO_MEMORY_SYSTEM_RAM = 2

# Offset del flag C-Gear nella RAM del DS per Pokemon White 2 ITA (IRDI)
# Action Replay code: 2221EA25 00000002
# Indirizzo ARM9: 0x0221EA25 -> RAM offset: 0x21EA25
# Valore 0x00 = C-Gear disabilitato permanentemente
CGEAR_RAM_OFFSET = 0x21EA25

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
    # FIX CRASH OVERWORLD BW2:
    # - melonds_use_fw_settings=disabled: NON legge firmware WiFi (FreeBIOS CRC BAD)
    # - melonds_randomize_mac_address=disabled: MAC fisso, no re-init WiFi
    # - melonds_jit_enable=disabled: stabilizza il caricamento (fix schermata bianca)
    # - melonds_boot_directly=enabled: boot diretto cartuccia
    core_variables = {
        b'melonds_jit_enable':            b'disabled',
        b'melonds_boot_directly':         b'enabled',
        b'melonds_console_mode':          b'DS',
        b'melonds_touch_mode':            b'Touch',
        b'melonds_language':              b'Italian',
        b'melonds_threaded_renderer':     b'enabled',
        b'melonds_use_fw_settings':       b'disabled',
        b'melonds_randomize_mac_address': b'disabled',
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

    cgear_state = 0 # 0: attesa, 1: bypass in corso, 2: completato
    cgear_step_frame = 0
    cgear_cut_screen = False

    def video_cb(data, width, height, pitch):
        nonlocal cgear_state, cgear_step_frame, cgear_cut_screen
        if data and width > 0 and height > 0:
            frame_len = pitch * height
            raw = ctypes.string_at(data, frame_len)

            # Rilevatore C-Gear:
            if cgear_state == 0 and height >= 192 and width >= 256:
                try:
                    p1_val = raw[112 * pitch + 196 * 4]     # B channel riga 'Sì'
                    p2_val = raw[127 * pitch + 196 * 4]     # B channel riga 'NO'
                    p_box_bg = raw[120 * pitch + 230 * 4]   # Sfondo interno box
                    p_line2 = raw[178 * pitch + 100 * 4]    # Riga 2 del dialogo

                    # Bordo giallo touch screen
                    off_b = 202 * pitch + 30 * 4
                    is_yellow = (raw[off_b + 2] > 180 and raw[off_b + 1] > 150 and raw[off_b] < 100)

                    if (p_box_bg > 220 and p1_val < 130 and p2_val > 200 and p_line2 > 220) or is_yellow:
                        print("[EngineWorker] ✂ TAGLIO C-GEAR ATTIVO! Esecuzione bypass trasparente...", flush=True)
                        cgear_state = 1
                        cgear_step_frame = 0
                        cgear_cut_screen = True
                except Exception:
                    pass

            # TAGLIO SCHERMATA: mentre il bypass è in corso, oscura il display
            # per tagliare completamente la schermata del C-Gear alla vista dell'utente
            if cgear_cut_screen:
                shm.buf[:frame_len] = b'\x00' * frame_len
            else:
                shm.buf[:frame_len] = raw

            control_arr[31] += 1

    def audio_cb(data, frames):
        return frames

    def poll_cb():
        nonlocal cgear_state, cgear_step_frame, cgear_cut_screen
        if cgear_state == 1:
            cgear_step_frame += 1
            if cgear_step_frame > 125:
                cgear_state = 2
                cgear_cut_screen = False
                control_arr[27] = 2 # Notifica Overworld attivo alla GUI
                print("[EngineWorker] 🎉 BYPASS C-GEAR COMPLETATO! Overworld visualizzato.", flush=True)

    def input_cb(port, device, index, id_):
        nonlocal cgear_state, cgear_step_frame
        if port != 0:
            return 0
        if device == 1: # Joypad (RETRO_DEVICE_JOYPAD)
            if cgear_state == 1:
                # Frame-perfect sequence:
                # frame 0..7: premi DOWN (seleziona NO al primo prompt)
                # frame 15..25: premi A (conferma NO)
                # frame 50..62: premi A (conferma 'Sì, procedi senza C-Gear')
                # frame 75..88: premi A (backup conferma 'Sì, procedi senza C-Gear')
                # frame 98..110: premi A (backup conferma)
                # frame 111..125: dissolvenza schermo nero pulita verso l'Overworld
                if id_ == 5: # RETRO_DEVICE_ID_JOYPAD_DOWN
                    return 1 if (0 <= cgear_step_frame < 8) else 0
                elif id_ == 8: # RETRO_DEVICE_ID_JOYPAD_A
                    return 1 if (
                        15 <= cgear_step_frame < 25 or
                        50 <= cgear_step_frame < 62 or
                        75 <= cgear_step_frame < 88 or
                        98 <= cgear_step_frame < 110
                    ) else 0
                return 0

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
    lib.retro_get_memory_data.restype = ctypes.c_void_p
    lib.retro_get_memory_data.argtypes = [ctypes.c_uint]
    lib.retro_get_memory_size.restype = ctypes.c_size_t
    lib.retro_get_memory_size.argtypes = [ctypes.c_uint]

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
        # Sincronizzazione Save RAM Live (Indice 28 = flush RAM su disco, Indice 29 = reload disco in RAM)
        if control_arr[28] == 1:
            try:
                save_ptr = lib.retro_get_memory_data(0)
                save_sz = lib.retro_get_memory_size(0)
                if save_ptr and save_sz == 524288:
                    ram_data = ctypes.string_at(save_ptr, save_sz)
                    with open(save_path, 'wb') as sf:
                        sf.write(ram_data)
                    # Mirror su saves/ se cartella profiles
                    try:
                        p_save = Path(save_path)
                        mirror_sav = p_save.parent.parent.parent / "saves" / p_save.name
                        if mirror_sav.parent.exists():
                            with open(mirror_sav, 'wb') as mf:
                                mf.write(ram_data)
                    except Exception:
                        pass
                    print("[EngineWorker] 💾 Save RAM flushato su disco!", flush=True)
            except Exception as e:
                print(f"[EngineWorker] Errore flush save RAM: {e}", flush=True)
            finally:
                control_arr[28] = 0

        if control_arr[29] == 1:
            try:
                save_ptr = lib.retro_get_memory_data(0)
                save_sz = lib.retro_get_memory_size(0)
                if save_ptr and save_sz == 524288 and os.path.exists(save_path):
                    with open(save_path, 'rb') as sf:
                        new_bytes = sf.read()
                    ctypes.memmove(save_ptr, new_bytes, min(len(new_bytes), save_sz))
                    print("[EngineWorker] ⚡ Save RAM aggiornata LIVE per melonDS!", flush=True)
            except Exception as e:
                print(f"[EngineWorker] Errore sync live save RAM: {e}", flush=True)
            finally:
                control_arr[29] = 0

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
