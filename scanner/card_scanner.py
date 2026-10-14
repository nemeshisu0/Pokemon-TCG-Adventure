#!/usr/bin/env python3
"""
Scanner Webcam per Carte Pokémon TCG con riconoscimento ottico (OpenCV + OCR)
e modulo di aggancio per iniezione in Pokémon Bianco 2.
"""

import sys
import os
import time
import json
import difflib
from pathlib import Path
import numpy as np
import cv2

# Import modulo injector locale
from injector import PokemonInjector

BASE_DIR = Path(__file__).resolve().parent
POKEDEX_FILE = BASE_DIR / "pokedex.json"

# Verifica disponibilità pytesseract
try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False

# Verifica se il binario tesseract è installato nel sistema
import shutil
TESSERACT_AVAILABLE = HAS_PYTESSERACT and (shutil.which("tesseract") is not None)


class PokemonCardScanner:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        self.pokedex = self._load_pokedex()
        self.pokemon_names = [p["name"] for p in self.pokedex]
        self.name_to_data = {p["name"].lower(): p for p in self.pokedex}
        self.injector = PokemonInjector()

        # Stato del rilevamento
        self.current_match = None
        self.current_confidence = 0.0
        self.match_counter = 0
        self.stable_match = None
        self.last_ocr_time = 0
        self.ocr_interval = 0.35  # Intervallo tra chiamate OCR in secondi
        self.show_debug_crop = True
        self.last_injected_message = ""
        self.message_timer = 0
        self.latest_ocr_text = ""

    def _load_pokedex(self):
        if not POKEDEX_FILE.exists():
            print(f"⚠️ File Pokédex non trovato in {POKEDEX_FILE}. Caricamento fallback di base...")
            return [
                {"id": 1, "name": "Bulbasaur"},
                {"id": 4, "name": "Charmander"},
                {"id": 7, "name": "Squirtle"},
                {"id": 25, "name": "Pikachu"},
                {"id": 494, "name": "Victini"},
                {"id": 495, "name": "Snivy"},
                {"id": 498, "name": "Tepig"},
                {"id": 501, "name": "Oshawott"},
                {"id": 643, "name": "Reshiram"},
                {"id": 644, "name": "Zekrom"},
                {"id": 646, "name": "Kyurem"}
            ]
        with open(POKEDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def init_camera(self):
        print(f"📷 Apertura webcam (indice {self.camera_index})...")
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            # Prova fallback indice 1
            print(f"⚠️ Dispositivo {self.camera_index} non disponibile, provo indice 1...")
            self.cap = cv2.VideoCapture(1)
        
        if not self.cap.isOpened():
            print("❌ Impossibile aprire la fotocamera!")
            return False

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        return True

    def preprocess_header(self, crop):
        """Ottimizza l'immagine dell'intestazione per il riconoscimento OCR."""
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        
        # Ridimensiona 2x per migliorare l'OCR su testo piccolo
        resized = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        
        # Filtro per rimuovere rumore conservando i bordi
        denoised = cv2.bilateralFilter(resized, 9, 75, 75)
        
        # Miglioramento contrasto CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast = clahe.apply(denoised)
        
        # Binarizzazione con soglia Otsu
        _, thresh = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Se lo sfondo è scuro e il testo è chiaro, inverti
        white_pixels = np.sum(thresh == 255)
        total_pixels = thresh.size
        if white_pixels < total_pixels * 0.5:
            thresh = cv2.bitwise_not(thresh)
            
        return thresh

    def match_pokemon(self, text):
        """Trova il Pokémon corrispondente con fuzzy matching."""
        if not text:
            return None, 0.0
            
        # Pulisci il testo da parole tipiche delle carte (es. Basic, Stage, HP, etc.)
        cleaned = text.upper()
        for token in ["BASIC", "STAGE", "STAGE 1", "STAGE 2", "HP", "VMAX", "VSTAR", "EX", "GX", "LV."]:
            cleaned = cleaned.replace(token, " ")
        cleaned = "".join([c if c.isalnum() or c.isspace() else " " for c in cleaned])
        words = cleaned.split()

        best_match = None
        best_ratio = 0.0

        for word in words:
            if len(word) < 3:
                continue
            matches = difflib.get_close_matches(word.capitalize(), self.pokemon_names, n=1, cutoff=0.68)
            if matches:
                matched_name = matches[0]
                ratio = difflib.SequenceMatcher(None, word.lower(), matched_name.lower()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = self.name_to_data[matched_name.lower()]

        # Prova anche la combinazione delle prime due parole (per nomi composti come "Mime Jr.")
        if len(words) >= 2:
            combined = f"{words[0]} {words[1]}".capitalize()
            matches = difflib.get_close_matches(combined, self.pokemon_names, n=1, cutoff=0.75)
            if matches:
                matched_name = matches[0]
                ratio = difflib.SequenceMatcher(None, combined.lower(), matched_name.lower()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = self.name_to_data[matched_name.lower()]

        return best_match, best_ratio

    def draw_hud(self, frame, card_box, header_box, thresh_crop):
        h, w = frame.shape[:2]

        # Sfondo scuro semitrasparente per la barra superiore
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 65), (20, 20, 25), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Titolo HUD
        cv2.putText(frame, "POKEMON BIANCO 2 - TCG CARD SCANNER", (25, 30),
                    cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 230, 255), 2)
        cv2.putText(frame, "Inquadra la carta | [SPAZIO] Inietta | [T] Test | [C] Debug Crop | [Q] Esci",
                    (25, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

        # Stato Tesseract
        if not TESSERACT_AVAILABLE:
            cv2.rectangle(frame, (w - 420, 10), (w - 20, 55), (0, 0, 180), -1)
            cv2.putText(frame, "OCR DISATTIVO (tesseract mancante)", (w - 405, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            cv2.putText(frame, "Esegui: sudo pacman -S tesseract", (w - 405, 48),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (220, 220, 220), 1)

        # Riquadro Guida Carta (Verde se stabile, Ciano se cerca)
        cx1, cy1, cx2, cy2 = card_box
        color = (0, 255, 120) if (self.stable_match and self.current_confidence >= 0.75) else (255, 200, 0)
        
        # Angoli mirino
        line_len = 35
        thick = 3
        # Top-left
        cv2.line(frame, (cx1, cy1), (cx1 + line_len, cy1), color, thick)
        cv2.line(frame, (cx1, cy1), (cx1, cy1 + line_len), color, thick)
        # Top-right
        cv2.line(frame, (cx2, cy1), (cx2 - line_len, cy1), color, thick)
        cv2.line(frame, (cx2, cy1), (cx2, cy1 + line_len), color, thick)
        # Bottom-left
        cv2.line(frame, (cx1, cy2), (cx1 + line_len, cy2), color, thick)
        cv2.line(frame, (cx1, cy2), (cx1, cy2 - line_len), color, thick)
        # Bottom-right
        cv2.line(frame, (cx2, cy2), (cx2 - line_len, cy2), color, thick)
        cv2.line(frame, (cx2, cy2), (cx2, cy2 - line_len), color, thick)

        # Riquadro del Nome/Header
        hx1, hy1, hx2, hy2 = header_box
        cv2.rectangle(frame, (hx1, hy1), (hx2, hy2), (0, 220, 255), 1)
        cv2.putText(frame, "ZONA NOME", (hx1 + 5, hy1 - 7),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 220, 255), 1)

        # Banner informativo inferiore
        bottom_y = h - 90
        overlay2 = frame.copy()
        cv2.rectangle(overlay2, (0, bottom_y), (w, h), (15, 15, 20), -1)
        cv2.addWeighted(overlay2, 0.85, frame, 0.15, 0, frame)

        if self.stable_match:
            poke_id = self.stable_match["id"]
            poke_name = self.stable_match["name"]
            conf = int(self.current_confidence * 100)
            cv2.putText(frame, f"POKEMON: #{poke_id:03d} {poke_name.upper()} (Match: {conf}%)",
                        (30, bottom_y + 35), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 255, 120), 2)
            cv2.putText(frame, "Premi [SPAZIO] o [INVIO] per iniettare nel salvataggio di Bianco 2!",
                        (30, bottom_y + 65), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        else:
            cv2.putText(frame, "Avvicina una carta Pokémon e centra il nome nel riquadro giallo",
                        (30, bottom_y + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)
            if self.latest_ocr_text:
                cv2.putText(frame, f"Lettura OCR: '{self.latest_ocr_text.strip()}'",
                            (30, bottom_y + 65), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (130, 130, 130), 1)

        # Messaggio flash iniezione completata
        if time.time() - self.message_timer < 3.0:
            msg_overlay = frame.copy()
            cv2.rectangle(msg_overlay, (w//2 - 320, h//2 - 50), (w//2 + 320, h//2 + 50), (0, 160, 60), -1)
            cv2.addWeighted(msg_overlay, 0.9, frame, 0.1, 0, frame)
            cv2.putText(frame, self.last_injected_message, (w//2 - 290, h//2 + 8),
                        cv2.FONT_HERSHEY_DUPLEX, 0.75, (255, 255, 255), 2)

        # Picture-in-picture debug crop
        if self.show_debug_crop and thresh_crop is not None:
            dw, dh = 240, 70
            pip_x = w - dw - 25
            pip_y = h - dh - 110
            pip_img = cv2.resize(thresh_crop, (dw, dh))
            pip_bgr = cv2.cvtColor(pip_img, cv2.COLOR_GRAY2BGR)
            frame[pip_y:pip_y+dh, pip_x:pip_x+dw] = pip_bgr
            cv2.rectangle(frame, (pip_x, pip_y), (pip_x+dw, pip_y+dh), (0, 220, 255), 1)
            cv2.putText(frame, "Filtro OCR", (pip_x + 5, pip_y - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 220, 255), 1)

    def run(self):
        if not self.init_camera():
            print("❌ Scanner terminato: webcam non disponibile.")
            return

        print("🚀 Scanner avviato! Premi 'q' nella finestra video per uscire.")

        window_name = "Pokemon Bianco 2 - Card Scanner"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("⚠️ Errore di lettura frame dalla webcam.")
                break

            h, w = frame.shape[:2]

            # Coordinate mirino carta (proporzione 2.5:3.5)
            card_h = int(h * 0.72)
            card_w = int(card_h * (2.5 / 3.5))
            cx1 = (w - card_w) // 2
            cy1 = (h - card_h) // 2
            cx2 = cx1 + card_w
            cy2 = cy1 + card_h

            # Coordinate zona nome (top 20% della carta, escludendo il margine estremo)
            hx1 = cx1 + int(card_w * 0.08)
            hy1 = cy1 + int(card_h * 0.04)
            hx2 = cx2 - int(card_w * 0.18)
            hy2 = cy1 + int(card_h * 0.17)

            header_crop = frame[hy1:hy2, hx1:hx2]
            thresh_crop = None

            if header_crop.size > 0:
                thresh_crop = self.preprocess_header(header_crop)

                # Esegui OCR se è passato l'intervallo stabilito
                now = time.time()
                if TESSERACT_AVAILABLE and (now - self.last_ocr_time > self.ocr_interval):
                    self.last_ocr_time = now
                    try:
                        # PSM 7: Treat the image as a single text line
                        text = pytesseract.image_to_string(thresh_crop, config="--psm 7")
                        self.latest_ocr_text = text
                        matched, conf = self.match_pokemon(text)

                        if matched and conf >= 0.70:
                            if self.current_match and self.current_match["id"] == matched["id"]:
                                self.match_counter += 1
                            else:
                                self.current_match = matched
                                self.match_counter = 1
                            self.current_confidence = conf

                            # Conferma match stabile dopo 2 rilevamenti consecutivi
                            if self.match_counter >= 2:
                                self.stable_match = matched
                        else:
                            if self.match_counter > 0:
                                self.match_counter -= 1
                            if self.match_counter == 0:
                                self.stable_match = None
                                self.current_match = None
                    except Exception as e:
                        print(f"Errore OCR: {e}")

            # Disegna l'interfaccia HUD
            self.draw_hud(frame, (cx1, cy1, cx2, cy2), (hx1, hy1, hx2, hy2), thresh_crop)

            cv2.imshow(window_name, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # 'q' o ESC
                break
            elif key == ord('c'):  # Toggle Picture-in-picture
                self.show_debug_crop = not self.show_debug_crop
            elif key == ord('r'):  # Reset
                self.stable_match = None
                self.current_match = None
                self.match_counter = 0
            elif key == ord('t'):  # Modalità simulazione test
                print("\n🧪 [MODALITA TEST] Inserisci il nome di un Pokémon (es. Pikachu, Snivy, Zekrom):")
                sys.stdout.flush()
                # Esegui test rapido con Victini se input vuoto
                test_name = "Victini"
                matched, conf = self.match_pokemon(test_name)
                if matched:
                    self.stable_match = matched
                    self.current_confidence = 1.0
                    print(f"✅ Rilevato Pokémon di test: #{matched['id']} {matched['name']}")
            elif key == 32 or key == 13:  # SPAZIO o INVIO
                if self.stable_match:
                    res = self.injector.queue_injection(self.stable_match, frame)
                    self.last_injected_message = f"#{self.stable_match['id']} {self.stable_match['name']} INIETTATO!"
                    self.message_timer = time.time()
                    print(f"\n✨ [INIEZIONE] Pokémon #{self.stable_match['id']} {self.stable_match['name']} registrato con successo!")
                    if res.get("backup"):
                        print(f"📦 Backup salvataggio creato in: {res['backup']}")

        self.cap.release()
        cv2.destroyAllWindows()
        print("👋 Scanner chiuso con successo.")


if __name__ == "__main__":
    scanner = PokemonCardScanner()
    scanner.run()
