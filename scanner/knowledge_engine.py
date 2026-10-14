#!/usr/bin/env python3
"""
Modulo Knowledge Engine per Pokémon TCG Card Scanner.
Gestisce:
1. Conoscenza condivisa e pre-addestrata (database/card_knowledge.json)
2. Impronte visive (perceptual hashing + color profile)
3. Matching ibrido (Memoria Visiva + OCR Avanzato + Fuzzy Search su cards.db)
4. Apprendimento attivo continuo (ogni scansione confermata arricchisce la memoria)
5. Archiviazione delle foto scattate in scanner/captures/
"""

import os
import sys
import json
import time
import re
import difflib
import sqlite3
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
import cv2

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"
KNOWLEDGE_FILE = DATABASE_DIR / "card_knowledge.json"
CARDS_DB_FILE = DATABASE_DIR / "cards.db"
CAPTURES_DIR = BASE_DIR / "scanner" / "captures"
CARDS_CACHE_DIR = BASE_DIR / "scanner" / "cache" / "cards"

# Configurazione Tesseract portatile
TESSERACT_BIN_DIR = BASE_DIR / "scanner" / ".tesseract_bin"
if TESSERACT_BIN_DIR.exists():
    os.environ['LD_LIBRARY_PATH'] = f"{TESSERACT_BIN_DIR}/usr/lib:" + os.environ.get('LD_LIBRARY_PATH', '')
    os.environ['TESSDATA_PREFIX'] = f"{TESSERACT_BIN_DIR}/usr/share/tessdata"
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_BIN_DIR / "usr" / "bin" / "tesseract")
        HAS_TESSERACT = True
    except ImportError:
        HAS_TESSERACT = False
else:
    try:
        import pytesseract
        HAS_TESSERACT = True
    except ImportError:
        HAS_TESSERACT = False


def compute_dhash(image, hash_size=16):
    """Calcola il difference hash percettivo a 256 bit."""
    if image is None or image.size == 0:
        return ""
    resized = cv2.resize(image, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)
    if len(resized.shape) == 3:
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    else:
        gray = resized
    diff = gray[:, 1:] > gray[:, :-1]
    return "".join(["1" if b else "0" for b in diff.flatten()])


def hamming_distance(h1, h2):
    """Calcola la distanza di Hamming tra due hash di uguale lunghezza."""
    if not h1 or not h2 or len(h1) != len(h2):
        return 999
    return sum(c1 != c2 for c1, c2 in zip(h1, h2))


def compute_color_fingerprint(image):
    """Estrae l'istogramma cromatico normalizzato della parte centrale dell'immagine (artwork)."""
    if image is None or image.size == 0:
        return []
    h, w = image.shape[:2]
    # Ritaglia la parte centrale (illustrazione principale)
    center = image[int(h * 0.18):int(h * 0.70), int(w * 0.10):int(w * 0.90)]
    if center.size == 0:
        center = image
    hsv = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)
    # Istogramma su Tonalità (Hue) a 16 canali
    hist = cv2.calcHist([hsv], [0], None, [16], [0, 180])
    cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    return [round(float(v), 3) for v in hist.flatten()]


class CardKnowledgeEngine:
    def __init__(self):
        CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
        self.knowledge = self._load_knowledge()

    def _load_knowledge(self):
        """Carica la knowledge base condivisa o la inizializza."""
        if KNOWLEDGE_FILE.exists():
            try:
                with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Errore caricamento {KNOWLEDGE_FILE}: {e}")
        
        # Struttura iniziale
        return {
            "version": "1.0",
            "description": "Pokémon TCG Distributed Knowledge Base",
            "cards": {}
        }

    def save_knowledge(self):
        """Salva la knowledge base su disco in modo persistente e distribuibile."""
        try:
            DATABASE_DIR.mkdir(parents=True, exist_ok=True)
            with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.knowledge, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Errore salvataggio knowledge base: {e}")
            return False

    def learn_card(self, card_item, front_img=None, header_img=None, footer_img=None, ocr_tokens=None):
        """
        Apprende e arricchisce la conoscenza del bot con un nuovo campione confermato.
        Questo metodo migliora continuamente il bot e la conoscenza viene salvata nel pacchetto di distribuzione.
        """
        card_id = card_item.get("card_id")
        if not card_id:
            return False

        known = self.knowledge["cards"].get(card_id, {
            "card_id": card_id,
            "name": card_item.get("name"),
            "set_name": card_item.get("set_name"),
            "card_number": str(card_item.get("card_number", "")),
            "release_year": card_item.get("release_year"),
            "artist": card_item.get("artist"),
            "rarity": card_item.get("rarity"),
            "dex_id": card_item.get("dex_id"),
            "visual_hashes": [],
            "color_fingerprints": [],
            "ocr_aliases": [],
            "times_scanned": 0,
            "first_learned": time.strftime("%Y-%m-%d %H:%M:%S")
        })

        # Assicura aggiornamento attributi mancanti se forniti
        for attr in ["name", "set_name", "card_number", "release_year", "artist", "rarity", "dex_id"]:
            if (attr not in known or not known[attr]) and card_item.get(attr):
                known[attr] = card_item[attr]

        # Aggiorna contatore
        known["times_scanned"] = known.get("times_scanned", 0) + 1
        known["last_seen"] = time.strftime("%Y-%m-%d %H:%M:%S")

        # Memorizza impronta percettiva se disponibile
        if front_img is not None and front_img.size > 0:
            v_hash = compute_dhash(front_img, hash_size=16)
            if v_hash and v_hash not in known.get("visual_hashes", []):
                hashes = known.get("visual_hashes", [])
                if len(hashes) < 10:  # Conserva fino a 10 varianti di luce
                    hashes.append(v_hash)
                known["visual_hashes"] = hashes

            color_fp = compute_color_fingerprint(front_img)
            if color_fp:
                fps = known.get("color_fingerprints", [])
                if len(fps) < 5:
                    fps.append(color_fp)
                known["color_fingerprints"] = fps

        # Memorizza SOLO alias pertinenti (nome carta effettivo e numero carta)
        aliases = set(known.get("ocr_aliases", []))
        if card_item.get("name"):
            aliases.add(card_item["name"].upper())
        if card_item.get("card_number"):
            aliases.add(str(card_item["card_number"]).upper())
        if ocr_tokens:
            c_name = card_item.get("name", "").upper()
            for tok in ocr_tokens:
                # Accetta come alias solo se è una variante vicina al nome effettivo della carta
                if len(tok) >= 4 and difflib.SequenceMatcher(None, tok.upper(), c_name).ratio() >= 0.80:
                    aliases.add(tok.upper())
        known["ocr_aliases"] = sorted(list(aliases))

        self.knowledge["cards"][card_id] = known
        self.save_knowledge()
        print(f"🧠 [KNOWLEDGE ENGINE] Appresa/Aggiornata con successo carta {card_id} ({card_item.get('name')})! Totale apprese: {len(self.knowledge['cards'])}")
        return True

    def find_by_visual_memory(self, front_img, max_distance=35):
        """Cerca corrispondenze dirette nella memoria visiva appresa."""
        if front_img is None or front_img.size == 0 or not self.knowledge["cards"]:
            return None, 0.0

        query_hash = compute_dhash(front_img, hash_size=16)
        query_fp = compute_color_fingerprint(front_img)
        if not query_hash:
            return None, 0.0

        best_card = None
        best_score = 0.0

        for card_id, data in self.knowledge["cards"].items():
            hashes = data.get("visual_hashes", [])
            for h in hashes:
                dist = hamming_distance(query_hash, h)
                if dist <= max_distance:
                    # Somiglianza percentuale: 0 dist = 1.0, 35 dist = ~0.86
                    sim = 1.0 - (dist / 256.0)
                    if sim > best_score:
                        best_score = sim
                        best_card = dict(data)

        # Arricchisci con i metadati aggiornati da cards.db (es. artist, hp, total_set_cards)
        if best_card and CARDS_DB_FILE.exists():
            try:
                conn = sqlite3.connect(CARDS_DB_FILE)
                cur = conn.cursor()
                cur.execute(
                    'SELECT card_id, name, set_name, card_number, total_set_cards, release_year, rarity, dex_id, hp, artist '
                    'FROM cards WHERE card_id = ?',
                    (best_card['card_id'],)
                )
                row = cur.fetchone()
                if row:
                    best_card.update({
                        'card_id': row[0], 'name': row[1], 'set_name': row[2],
                        'card_number': row[3], 'total_set_cards': row[4],
                        'release_year': row[5], 'rarity': row[6], 'dex_id': row[7],
                        'hp': row[8], 'artist': row[9]
                    })
                conn.close()
            except Exception:
                pass

        return best_card, best_score

    def extract_clean_ocr(self, img, is_number=False):
        """Esegue filtri ottici ad alto contrasto per massimizzare la leggibilità Tesseract."""
        if not HAS_TESSERACT or img is None or img.size == 0:
            return ""

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        # Ridimensiona 2.5x
        scaled = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
        denoised = cv2.bilateralFilter(scaled, 7, 50, 50)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        contrast = clahe.apply(denoised)

        # Binarizzazione Otsu e Inversa
        _, otsu = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        otsu_inv = cv2.bitwise_not(otsu)

        candidates = [scaled, contrast, otsu, otsu_inv]
        psms = [6, 7, 8] if is_number else [6, 7, 11]

        extracted_texts = []
        for c_img in candidates:
            for psm in psms:
                try:
                    cfg = f"--psm {psm}"
                    if is_number:
                        cfg += " -c tessedit_char_whitelist=0123456789/#"
                    txt = pytesseract.image_to_string(c_img, lang="eng", config=cfg).strip()
                    if txt:
                        extracted_texts.append(txt)
                except Exception:
                    pass

        return " ".join(extracted_texts)

    def extract_year_from_images(self, image_list):
        """Estrae l'anno di rilascio a 4 cifre (1995-2026) tramite filtri OCR mirati su copyright/data."""
        if not HAS_TESSERACT:
            return None

        years_found = []
        for img in image_list:
            if img is None or img.size == 0:
                continue

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            scaled = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(scaled)
            _, otsu = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            candidates = [clahe, scaled, otsu]
            img_year_found = False
            for c_img in candidates:
                for psm in [6, 11, 7]:
                    try:
                        cfg = f"--psm {psm}"
                        txt = pytesseract.image_to_string(c_img, lang="eng", config=cfg).strip()
                        if txt:
                            # Sostituzioni di lettere che Tesseract confonde spesso con cifre
                            cleaned = txt.replace('O', '0').replace('o', '0').replace('I', '1').replace('l', '1').replace('S', '5').replace('B', '8')
                            matches = re.findall(r'\b(199[5-9]|20[01]\d|202[0-6])\b', cleaned)
                            for m in matches:
                                years_found.append(int(m))
                                img_year_found = True
                            # Cerca anche con simbolo copyright © o (c) o c
                            m_c = re.findall(r'(?:©|\(c\)|c)[^\d]{0,2}(199[5-9]|20[01]\d|202[0-6])', cleaned, re.IGNORECASE)
                            for m in m_c:
                                years_found.append(int(m))
                                img_year_found = True
                    except Exception:
                        pass
                if img_year_found:
                    break
            if years_found:
                break

        if years_found:
            # Sulle carte Pokémon con copyright multipli l'anno ufficiale del set corrisponde all'anno MASSIMO
            return max(years_found)
        return None

    def extract_author_from_images(self, image_list):
        """Estrae l'autore/illustratore ('Illus. <Nome>') confrontandolo con il database degli artisti."""
        if not HAS_TESSERACT or not CARDS_DB_FILE.exists():
            return None

        try:
            conn = sqlite3.connect(CARDS_DB_FILE)
            cur = conn.cursor()
            cur.execute('SELECT DISTINCT artist FROM cards WHERE artist IS NOT NULL')
            all_artists = [r[0] for r in cur.fetchall()]
            conn.close()
        except Exception:
            return None

        patterns = [
            r'(?:Illus|IIlus|llus|Ilus|Ill|lll|Il)[\.\:\s]+([A-Za-z0-9\s\.\-]+?)(?:\s+(?:©|\(c\)|c|\d{1,3}/|\d{4}|$)|$)',
            r'(?:Illustrator|Illustratore)[\.\:\s]+([A-Za-z0-9\s\.\-]+)'
        ]

        for img in image_list:
            if img is None or img.size == 0:
                continue

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            scaled = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(scaled)
            _, otsu = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            candidates = [clahe, scaled, otsu]
            img_texts = []
            for c_img in candidates:
                for psm in [6, 11]:
                    try:
                        cfg = f"--psm {psm}"
                        txt = pytesseract.image_to_string(c_img, lang="eng", config=cfg).strip()
                        if txt:
                            img_texts.append(txt)
                    except Exception:
                        pass

            sub_txt = " ".join(img_texts)
            if not sub_txt:
                continue

            # 1. Cerca pattern "Illus. <Nome>"
            for pat in patterns:
                m = re.search(pat, sub_txt, re.IGNORECASE)
                if m:
                    cand = m.group(1).strip()
                    matches = difflib.get_close_matches(cand, all_artists, n=1, cutoff=0.60)
                    if matches:
                        return matches[0]

            # 2. Ricerca per chunk di parole tra gli artisti ufficiali (solo >= 5 caratteri per evitare falsi positivi come 'DOM')
            words = sub_txt.split()
            for i in range(len(words)):
                for j in range(i + 1, min(i + 4, len(words) + 1)):
                    chunk = ' '.join(words[i:j])
                    if len(chunk) >= 5:
                        matches = difflib.get_close_matches(chunk, all_artists, n=1, cutoff=0.75)
                        if matches and len(matches[0]) >= 5:
                            return matches[0]

        return None

    def visual_sift_match(self, front_img, candidates, max_candidates=100):
        """
        Motore di Ricerca Fotografica Visuale (Stile Google Lens).
        Confronta i descrittori d'immagine SIFT (artwork centrale e layout carta)
        con le immagini ufficiali di riferimento delle carte candidate.
        Risolve ogni ambiguità visiva anche con foto di webcam a bassa risoluzione.
        """
        if front_img is None or front_img.size == 0 or not candidates:
            return {}

        CARDS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

        try:
            sift = cv2.SIFT_create(nfeatures=1500)
            kp_u, des_u = sift.detectAndCompute(front_img, None)
            if des_u is None or len(des_u) < 10:
                return {}
        except Exception:
            return {}

        flann = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))

        def fetch_candidate_image(cand):
            cid = cand.get('card_id')
            if not cid:
                return cid, None
            local_path = CARDS_CACHE_DIR / f"{cid}.png"
            if local_path.exists() and local_path.stat().st_size > 1000:
                return cid, local_path

            img_url = cand.get('image_url')
            if not img_url:
                set_id = cand.get('set_id')
                num = cand.get('card_number')
                if set_id and num:
                    img_url = f"https://images.pokemontcg.io/{set_id}/{num}.png"

            if img_url:
                try:
                    req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                    with urllib.request.urlopen(req, timeout=4) as resp:
                        with open(local_path, 'wb') as f:
                            f.write(resp.read())
                    return cid, local_path
                except Exception:
                    pass
            return cid, None

        to_check = candidates[:max_candidates]
        with ThreadPoolExecutor(max_workers=12) as executor:
            local_images = dict(executor.map(fetch_candidate_image, to_check))

        visual_scores = {}
        for cand in to_check:
            cid = cand['card_id']
            img_path = local_images.get(cid)
            if not img_path:
                continue
            ref_img = cv2.imread(str(img_path))
            if ref_img is None:
                continue

            try:
                kp_r, des_r = sift.detectAndCompute(ref_img, None)
                if des_r is None or len(des_r) < 10:
                    continue
                knn = flann.knnMatch(des_u, des_r, k=2)
                good = [m for m, n in knn if m.distance < 0.75 * n.distance]
                visual_scores[cid] = len(good)
            except Exception:
                pass

        return visual_scores

    def identify_card_from_captures(self, shots):
        """
        Analisi centrale del bot a 6 FASI:
        1. Fronte, Retro, Zoom Nome, Zoom Numero, Zoom Anno, Zoom Autore.
        2. Estrae Anno di rilascio, Numero carta (#X/Y), Autore, PV e Nome Pokémon.
        3. Interroga 'cards.db' con scoring multi-criterio ad altissima precisione.
        4. Restituisce il miglior match e arricchisce la memoria.
        """
        front_img = shots.get("front")
        back_img = shots.get("back")
        header_img = shots.get("header")
        header_crop = shots.get("header_crop")
        footer_img = shots.get("footer")
        footer_crop = shots.get("footer_crop")
        year_img = shots.get("year")
        year_crop = shots.get("year_crop")
        author_img = shots.get("author")
        author_crop = shots.get("author_crop")

        # Salva le 6 foto scattate su disco in modo persistente
        self.archive_captures(shots)

        # 1. ESTRAZIONE ANNO DI RILASCIO (Fase 5 mirata + fallback)
        year_sources = []
        for s in [year_crop, year_img, author_crop, author_img, footer_crop, footer_img]:
            if s is not None and s.size > 0:
                year_sources.append(s)
        if front_img is not None and front_img.size > 0:
            fh = front_img.shape[0]
            year_sources.append(front_img[int(fh * 0.85):, :])

        card_year = self.extract_year_from_images(year_sources)
        if card_year:
            print(f"📅 [KNOWLEDGE ENGINE] Anno di rilascio rilevato (Fase 5): {card_year}")

        # 2. ESTRAZIONE AUTORE / ILLUSTRATORE (Fase 6 mirata + fallback)
        author_sources = []
        for s in [author_crop, author_img, year_crop, year_img, footer_crop, footer_img]:
            if s is not None and s.size > 0:
                author_sources.append(s)
        if front_img is not None and front_img.size > 0:
            fh = front_img.shape[0]
            author_sources.append(front_img[int(fh * 0.70):, :])

        card_author = self.extract_author_from_images(author_sources)
        if card_author:
            print(f"🎨 [KNOWLEDGE ENGINE] Autore/Illustratore rilevato (Fase 6): {card_author}")

        # 3. ESTRAZIONE NUMERO CARTA E TOTALE SET (Fase 4 mirata + fallback)
        footer_sources = []
        for s in [footer_crop, footer_img, year_crop, year_img, author_crop, author_img]:
            if s is not None and s.size > 0:
                footer_sources.append(s)
        if front_img is not None and front_img.size > 0:
            fh = front_img.shape[0]
            footer_sources.append(front_img[int(fh * 0.72):, :])

        txt_footer = ""
        for f_src in footer_sources:
            t = self.extract_clean_ocr(f_src, is_number=True)
            if t:
                txt_footer += " " + t

        card_num = None
        total_set_cards = None

        # Regex per frazione: es. 31/147, 47/82, TG05/TG30
        num_match = re.search(r'([A-Za-z]{0,3}\d{1,3})\s*/\s*([A-Za-z]{0,3}\d{1,3})', txt_footer)
        if num_match:
            card_num = num_match.group(1).strip().upper()
            tot_cand = num_match.group(2).strip()
            if tot_cand.isdigit():
                total_set_cards = int(tot_cand)
        else:
            single_match = re.search(r'\b(\d{1,3})\b', txt_footer)
            if single_match:
                card_num = single_match.group(1).strip()

        if card_num:
            print(f"🔢 [KNOWLEDGE ENGINE] Numero carta rilevato: #{card_num}" + (f"/{total_set_cards}" if total_set_cards else ""))

        # 4. ESTRAZIONE NOME POKÉMON E PV / HP (Fase 3 mirata + fallback)
        header_sources = []
        for s in [header_crop, header_img]:
            if s is not None and s.size > 0:
                header_sources.append(s)
        if front_img is not None and front_img.size > 0:
            fh = front_img.shape[0]
            header_sources.append(front_img[:int(fh * 0.28), :])

        txt_header = ""
        for h_src in header_sources:
            t = self.extract_clean_ocr(h_src, is_number=False)
            if t:
                txt_header += " " + t

        # Estrazione PV / HP (supporta HP, PV francese, PS italiano, KP tedesco)
        hp_match = re.search(r'\b(30|40|50|60|70|80|90|100|110|120|130|140|150|160|170|180|190|200|210|220|230|240|250|260|270|280|300|310|320|330|340)(?:\s*(?:HP|PV|PS|KP)|\b)', txt_header, re.IGNORECASE)
        card_hp = int(hp_match.group(1)) if hp_match else None
        if not card_hp and front_img is not None and front_img.size > 0:
            txt_front = self.extract_clean_ocr(front_img, is_number=False)
            hp_m2 = re.search(r'\b(30|40|50|60|70|80|90|100|110|120|130|140|150|160|170|180|190|200|210|220|230|240|250|260|270|280|300|310|320|330|340)(?:\s*(?:HP|PV|PS|KP)|\b)', txt_front, re.IGNORECASE)
            card_hp = int(hp_m2.group(1)) if hp_m2 else None

        if card_hp:
            print(f"❤️ [KNOWLEDGE ENGINE] PV / HP rilevati: {card_hp} PV/PS")

        # Pulizia testo per parole chiave nome Pokémon
        cleaned_h = txt_header.upper()
        for token in [
            "BASIC", "BASE", "STAGE", "FASE", "STAGE 1", "STAGE 2", "HP", "PV", "PS",
            "VMAX", "VSTAR", "EX", "GX", "LV.", "LEGEND", "PESO", "LANCIA", "MONETA",
            "TESTA", "DANNI", "DEBOLEZZA", "RESISTENZA", "RITIRATA"
        ]:
            cleaned_h = cleaned_h.replace(token, " ")
        cleaned_h = "".join([c if c.isalnum() or c.isspace() else " " for c in cleaned_h])
        words = [w for w in cleaned_h.split() if len(w) >= 3]

        # 5. VERIFICA MEMORIA VISIVA CONDIVISA
        learned_card, visual_score = self.find_by_visual_memory(front_img)
        if learned_card and visual_score >= 0.90:
            # Assicurati che non vi sia contraddizione con anno o numero rilevati con certezza
            year_conflict = (card_year and learned_card.get("release_year") and int(learned_card["release_year"]) != card_year)
            num_conflict = (card_num and learned_card.get("card_number") and str(learned_card["card_number"]).lstrip('0') != card_num.lstrip('0'))
            if not year_conflict and not num_conflict:
                print(f"🎯 [KNOWLEDGE HIT] Carta riconosciuta istantaneamente dalla memoria visiva! ID: {learned_card['card_id']} (Fiducia: {visual_score*100:.1f}%)")
                self.learn_card(learned_card, front_img=front_img)
                return learned_card, visual_score, "memoria_visiva"

        # 6. RICERCA E SCORING NEL DATABASE CARDS.DB
        if not CARDS_DB_FILE.exists():
            return None, 0.0, "db_non_trovato"

        conn = sqlite3.connect(CARDS_DB_FILE)
        cur = conn.cursor()

        cur.execute('SELECT DISTINCT name FROM cards WHERE supertype = "Pokémon"')
        all_pokemon_names = [r[0] for r in cur.fetchall()]

        # Rilevamento e ranking pesato dei Pokémon dal testo OCR (deduplicazione per massima velocità)
        word_counts = {}
        for w in words:
            word_counts[w] = word_counts.get(w, 0) + 1

        pokemon_scores = {}
        for w, count in word_counts.items():
            matches = difflib.get_close_matches(w.capitalize(), all_pokemon_names, n=3, cutoff=0.65)
            for m in matches:
                r = difflib.SequenceMatcher(None, w.upper(), m.upper()).ratio()
                w_score = ((r * 3.0) if r >= 0.90 else r) * count
                pokemon_scores[m] = pokemon_scores.get(m, 0.0) + w_score

        if len(words) >= 2:
            comb = f"{words[0]} {words[1]}".capitalize()
            matches = difflib.get_close_matches(comb, all_pokemon_names, n=1, cutoff=0.70)
            for m in matches:
                r = difflib.SequenceMatcher(None, comb.upper(), m.upper()).ratio()
                pokemon_scores[m] = pokemon_scores.get(m, 0.0) + (r * 3.0 if r >= 0.90 else r)

        ranked_pokemons = sorted(pokemon_scores.items(), key=lambda x: x[1], reverse=True)
        candidate_pokemons = []
        if ranked_pokemons:
            top_score = ranked_pokemons[0][1]
            for p_name, s in ranked_pokemons:
                if s >= top_score * 0.35:
                    candidate_pokemons.append(p_name)

        db_candidates = []
        for p_name in candidate_pokemons:
            clean_p = ''.join(c for c in p_name.lower() if c.isalnum())
            cur.execute(
                'SELECT card_id, name, set_id, set_name, card_number, total_set_cards, release_year, rarity, dex_id, hp, artist, image_url '
                'FROM cards WHERE clean_name LIKE ?',
                (f'%{clean_p}%',)
            )
            for row in cur.fetchall():
                db_candidates.append({
                    'card_id': row[0], 'name': row[1], 'set_id': row[2], 'set_name': row[3],
                    'card_number': row[4], 'total_set_cards': row[5],
                    'release_year': row[6], 'rarity': row[7], 'dex_id': row[8],
                    'hp': row[9], 'artist': row[10], 'image_url': row[11], 'matched_pokemon': p_name
                })

        # Se nessun Pokémon candidato trovato per nome, ma abbiamo numero ed anno o autore, cerca direttamente
        if not db_candidates and card_num and (card_year or total_set_cards or card_author):
            query = 'SELECT card_id, name, set_id, set_name, card_number, total_set_cards, release_year, rarity, dex_id, hp, artist, image_url FROM cards WHERE (card_number = ? OR card_number = ?)'
            params = [card_num, card_num.lstrip('0')]
            if card_year:
                query += ' AND release_year = ?'
                params.append(card_year)
            if total_set_cards:
                query += ' AND total_set_cards = ?'
                params.append(total_set_cards)
            if card_author:
                query += ' AND artist LIKE ?'
                params.append(f'%{card_author}%')
            cur.execute(query, tuple(params))
            for row in cur.fetchall():
                db_candidates.append({
                    'card_id': row[0], 'name': row[1], 'set_id': row[2], 'set_name': row[3],
                    'card_number': row[4], 'total_set_cards': row[5],
                    'release_year': row[6], 'rarity': row[7], 'dex_id': row[8],
                    'hp': row[9], 'artist': row[10], 'image_url': row[11], 'matched_pokemon': row[1]
                })

        conn.close()

        # Ordina i candidati dando precedenza a quelli con HP o numero compatibile
        if card_hp or card_num:
            db_candidates.sort(key=lambda c: (
                1 if (card_hp and c.get('hp') == card_hp) else 0,
                1 if (card_num and str(c.get('card_number')).lstrip('0') == card_num.lstrip('0')) else 0
            ), reverse=True)

        # 7. RICERCA FOTOGRAFICA VISUALE SIFT (STILE GOOGLE LENS) SUI CANDIDATI
        visual_sift_scores = {}
        if front_img is not None and db_candidates:
            visual_sift_scores = self.visual_sift_match(front_img, db_candidates, max_candidates=100)
            if visual_sift_scores:
                best_sift_id = max(visual_sift_scores, key=visual_sift_scores.get)
                print(f"🔍 [VISUAL LENS] Confronto fotografico SIFT completato su {len(visual_sift_scores)} carte! Top match visivo: {best_sift_id} ({visual_sift_scores[best_sift_id]} corrispondenze)")

        # SCORING RIGOROSO MULTI-CRITERIO
        best_candidate = None
        best_score = -1.0

        for cand in db_candidates:
            score = 0.0

            # 1. Punteggio Nome Pokémon (max 35 punti)
            name_ratio = 0.0
            for w in words:
                r = difflib.SequenceMatcher(None, w.lower(), cand['name'].lower()).ratio()
                if r > name_ratio:
                    name_ratio = r
            score += name_ratio * 35.0

            # 2. Punteggio Ricerca Fotografica SIFT (fino a 150 punti)
            sift_cnt = visual_sift_scores.get(cand['card_id'], 0)
            if sift_cnt > 0:
                cand['visual_sift_matches'] = sift_cnt
                visual_pts = min(150.0, sift_cnt * 0.8)
                score += visual_pts

            # 3. Punteggio Numero Carta (45 punti se esatto)
            if card_num:
                c_num_str = str(cand['card_number']).strip()
                if c_num_str.upper() == card_num.upper() or c_num_str.lstrip('0') == card_num.lstrip('0'):
                    score += 45.0
                elif card_num in c_num_str:
                    score += 20.0

            # 4. Punteggio Totale Set (30 punti)
            if total_set_cards and cand.get('total_set_cards'):
                if cand['total_set_cards'] == total_set_cards:
                    score += 30.0

            # 5. Punteggio Anno di Rilascio (FASE 5) (40 punti)
            if card_year and cand.get('release_year'):
                cand_y = int(cand['release_year'])
                if cand_y == card_year:
                    score += 40.0
                elif abs(cand_y - card_year) == 1:
                    score += 15.0

            # 6. Punteggio Autore / Illustratore (FASE 6) (30 punti)
            if card_author and cand.get('artist'):
                cand_art = cand['artist'].lower()
                req_art = card_author.lower()
                if cand_art == req_art:
                    score += 30.0
                elif difflib.SequenceMatcher(None, cand_art, req_art).ratio() >= 0.75:
                    score += 20.0

            # 7. Punteggio PV / HP (25 punti)
            if card_hp and cand.get('hp'):
                if cand['hp'] == card_hp:
                    score += 25.0

            if score > best_score:
                best_score = score
                best_candidate = cand

        if best_candidate and best_score >= 45.0:
            confidence = min(0.99, max(0.55, best_score / 150.0))
            if best_candidate.get('visual_sift_matches', 0) >= 45:
                confidence = max(confidence, 0.95)

            art_str = f" [🎨 {best_candidate.get('artist')}]" if best_candidate.get('artist') else ""
            sift_info = f" [📷 SIFT: {best_candidate.get('visual_sift_matches', 0)}]" if best_candidate.get('visual_sift_matches') else ""
            print(f"🎯 [MATCH IDENTIFICATO] {best_candidate['name']} #{best_candidate['card_number']} ({best_candidate['set_name']} {best_candidate.get('release_year')}){art_str}{sift_info} — Punteggio: {best_score:.1f} (Fiducia: {confidence*100:.1f}%)")

            # Apprendimento attivo: salva nella memoria visiva solo se fiducia elevata (>= 0.85)
            if confidence >= 0.85:
                self.learn_card(best_candidate, front_img=front_img, header_img=header_img, footer_img=footer_img, ocr_tokens=[best_candidate['name']])
            return best_candidate, confidence, "ricerca_fotografica_ibrida"

        # Fallback parziale memoria visiva
        if learned_card and visual_score >= 0.75:
            return learned_card, visual_score, "memoria_visiva_parziale"

        return None, 0.0, "non_identificata"

    def archive_captures(self, shots):
        """Salva in modo permanente e pulito le 6 foto scattate."""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            session_meta = {"timestamp": timestamp, "files": {}}

            if shots.get("front") is not None:
                p = CAPTURES_DIR / "step1_front.png"
                cv2.imwrite(str(p), shots["front"])
                session_meta["files"]["front"] = str(p.name)

            if shots.get("back") is not None:
                p = CAPTURES_DIR / "step2_back.png"
                cv2.imwrite(str(p), shots["back"])
                session_meta["files"]["back"] = str(p.name)

            if shots.get("header") is not None:
                p = CAPTURES_DIR / "step3_header.png"
                cv2.imwrite(str(p), shots["header"])
                session_meta["files"]["header"] = str(p.name)

            if shots.get("footer") is not None:
                p = CAPTURES_DIR / "step4_footer.png"
                cv2.imwrite(str(p), shots["footer"])
                session_meta["files"]["footer"] = str(p.name)

            if shots.get("year") is not None:
                p = CAPTURES_DIR / "step5_year.png"
                cv2.imwrite(str(p), shots["year"])
                session_meta["files"]["year"] = str(p.name)

            if shots.get("author") is not None:
                p = CAPTURES_DIR / "step6_author.png"
                cv2.imwrite(str(p), shots["author"])
                session_meta["files"]["author"] = str(p.name)

            with open(CAPTURES_DIR / "latest_session.json", "w", encoding="utf-8") as f:
                json.dump(session_meta, f, indent=2)

        except Exception as e:
            print(f"⚠️ Errore archiviazione scatti: {e}")

