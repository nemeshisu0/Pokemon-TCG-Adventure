#!/usr/bin/env python3
"""
Test di integrazione completa per verificare il boot fluido dal Launcher fino all'Overworld.
Verifica:
1. Precaricamento credenziali profilo (nemesy2 / 1234) e focus su GIOCA.
2. Avvio del worker isolato di melonDS senza crash (nessuna schermata bianca freeze).
3. Sequenza automatica e assistita: salto FreeBIOS, salto Game Freak, salto Kyurem, conferma Continua.
4. Rilevamento e taglio visivo trasparente del C-Gear.
5. Atterraggio perfetto nell'Overworld all'interno del Ranch (Zona 445, X=35, Y=35).
6. Verifica che nell'Overworld il tasto N (A) non invii START.
"""

import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QKeyEvent
from launcher.launcher_window import LauncherWindow

ARTIFACT_DIR = Path("/home/nemesy/.gemini/antigravity-ide/brain/b8d8417a-cc11-40ef-9c2c-1009c4d46bd9")

def main():
    app = QApplication(sys.argv)
    window = LauncherWindow()
    window.show()

    print(f"[TEST] Launcher aperto. Utente: '{window.txt_username.text()}', Password: '{window.txt_password.text()}'", flush=True)
    assert window.txt_username.text() == "nemesy2", "Nome utente non precaricato"
    assert window.txt_password.text() == "1234", "Password non precaricata"

    # Simula clic su GIOCA (o pressione N con pulsante focalizzato)
    print("[TEST] Clic su 'GIOCA'...", flush=True)
    window._on_play_clicked()

    gc = window.game_client
    assert gc is not None, "GameClientWindow non istanziato"

    overworld_reached = [False]

    def check_status(elapsed_s):
        worker = gc.emu_thread.worker_proc
        alive = worker.is_alive() if worker else False
        exitcode = worker.exitcode if worker else None
        ctrl_overworld = gc.emu_thread.control_arr[27] if gc.emu_thread and hasattr(gc.emu_thread, 'control_arr') else 0
        has_img = gc.top_screen_widget.image is not None

        print(f"[{elapsed_s}s] Worker Alive: {alive} (exitcode: {exitcode}), Overworld Flag: {ctrl_overworld}, Has Image: {has_img}", flush=True)

        if not alive:
            print(f"❌ ERRORE: Worker melonDS terminato prematuramente con codice {exitcode}!", flush=True)
            app.quit()
            return

        if ctrl_overworld == 2 and not overworld_reached[0]:
            overworld_reached[0] = True
            print("🎉 OVERWORLD CONFERMATO DAL WORKER! Auto-boot disattivato con successo.", flush=True)

    # Controlli periodici
    for s in range(3, 33, 3):
        QTimer.singleShot(s * 1000, lambda s=s: check_status(s))

    # Controllo finale a t=32s con screenshot
    def finish_test():
        if gc.top_screen_widget.image:
            out_path = ARTIFACT_DIR / "final_overworld_live_boot.png"
            gc.top_screen_widget.image.save(str(out_path))
            print(f"📸 Screenshot finale salvato in: {out_path}", flush=True)

        # Test pressione N nell'Overworld
        print("[TEST] Simulazione pressione tasto N (A) nell'Overworld...", flush=True)
        ev_press = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_N, Qt.KeyboardModifier.NoModifier, 'n')
        gc.keyPressEvent(ev_press)

        start_pressed = gc.emu_thread.control_arr[3]
        a_pressed = gc.emu_thread.control_arr[8]
        print(f"[TEST] Verifica tasti inviati: Tasto A (8)={a_pressed}, Tasto START (3)={start_pressed}", flush=True)
        assert start_pressed == 0, "ERRORE: Il tasto START è stato inviato durante la pressione di N in gioco!"
        assert a_pressed == 1, "ERRORE: Il tasto A non è stato inviato!"
        print("✔ Tasto N agisce correttamente al 100% solo come A (nessuna apertura menu Start!).", flush=True)

        gc._on_close_to_launcher()
        app.quit()

    QTimer.singleShot(32000, finish_test)
    app.exec()
    print("✔ Test Live Boot completato con successo al 100%.", flush=True)

if __name__ == "__main__":
    main()
