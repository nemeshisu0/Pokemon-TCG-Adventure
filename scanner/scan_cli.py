#!/usr/bin/env python3
"""
Interfaccia da terminale interattiva per la scansione e iniezione delle carte Pokémon TCG.
Permette ricerca rapida tra oltre 20.000 carte ufficiali, selezione finitura (Normale/Holo/Reverse),
visualizzazione regole (Tier IV, Grado Pokéball, Nerf Leggendari, Double Shiny) e
iniezione immediata nel salvataggio di Pokémon Bianco 2.
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scanner.tcg_core import TCGCore
from scanner.injector import PokemonInjector

# ANSI Colors
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_MAGENTA = "\033[95m"
C_CYAN = "\033[96m"
C_GOLD = "\033[38;5;220m"


def print_banner():
    print(f"{C_BOLD}{C_CYAN}╔══════════════════════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}║     POKÉMON BIANCO 2 — TCG SCANNER & INJECTION ENGINE (STRADA B)║{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}╚══════════════════════════════════════════════════════════════════╝{C_RESET}")


def format_iv(val):
    if val == 31:
        return f"{C_BOLD}{C_GOLD}31 ★{C_RESET}"
    return f"{val:2d}"


def display_evaluation(eval_res):
    print(f"\n{C_BOLD}--- SCHEDA CARTA SCANSIONATA ---{C_RESET}")
    print(f" Pokémon       : {C_BOLD}{eval_res['species_name']}{C_RESET} (Pokédex #{eval_res['species_id']})")
    print(f" Espansione    : {eval_res['set_name']} #{eval_res['card_number']} ({eval_res['release_year']})")
    print(f" Finitura      : {C_BOLD}{eval_res['finish']}{C_RESET}")
    print(f" Livello       : Lv. {C_BOLD}{eval_res['level']}{C_RESET}")
    print(f" Categoria     : {C_CYAN}{eval_res['tier_name']}{C_RESET}")
    print(f" Era Storica   : {C_MAGENTA}{eval_res['era_name']}{C_RESET}")
    print(f" Pokéball      : {C_GREEN}{eval_res['pokeball_name']} (ID {eval_res['pokeball_id']}){C_RESET}")
    
    if eval_res.get('particles'):
        print(f" Effetto Entrata: {eval_res['particles']}")
    if eval_res.get('title'):
        print(f" Titolo PokeMMO : «{eval_res['title']}»")
    if eval_res.get('ribbon'):
        print(f" Fiocco         : {eval_res['ribbon']}")
    if eval_res.get('hidden_ability'):
        print(f" Abilità        : {C_GOLD}ABILITÀ NASCOSTA (DREAM WORLD){C_RESET}")
    if eval_res.get('is_double_shiny'):
        print(f" {C_BOLD}{C_GOLD}★★★ RISONANZA COSMICA (DOUBLE SHINY - SQUARE LASER) ★★★{C_RESET}")
    elif eval_res.get('is_shiny'):
        print(f" {C_YELLOW}★ SHINY (Cromia della Carta / Vault) ★{C_RESET}")
    if eval_res.get('is_legendary_sealed'):
        print(f" {C_RED}⚠ NERF LEGGENDARIO: {eval_res['legendary_notes']}{C_RESET}")

    ivs = eval_res['ivs']
    print(f"\n Statistiche IV:")
    print(f"   PS  : {format_iv(ivs['hp'])}   |   ATT : {format_iv(ivs['atk'])}   |   DIF : {format_iv(ivs['def'])}")
    print(f"   AT.S: {format_iv(ivs['spa'])}   |   DF.S: {format_iv(ivs['spd'])}   |   VEL : {format_iv(ivs['spe'])}")
    print(f" Origine Met   : {eval_res['met_location']}")


def interactive_scan():
    core = TCGCore()
    injector = PokemonInjector()

    print_banner()
    while True:
        try:
            query = input(f"\n{C_BOLD}Cerca Pokémon o Carta (es. 'Charizard', 'Lucario', 'q' per uscire): {C_RESET}").strip()
            if not query or query.lower() in ['q', 'quit', 'exit']:
                print("Uscita dal programma.")
                break

            results = core.search_cards(query, limit=15)
            if not results:
                print(f"{C_RED}Nessuna carta trovata per '{query}'. Riprova.{C_RESET}")
                continue

            print(f"\n{C_BOLD}Carte TCG trovate nel database:{C_RESET}")
            for idx, r in enumerate(results, 1):
                gen_flag = f"{C_GREEN}[Gen 1-5]{C_RESET}" if r['dex_id'] <= 649 else f"{C_MAGENTA}[Gen 6-9]{C_RESET}"
                print(f" [{idx:2d}] {gen_flag} {C_BOLD}{r['name']}{C_RESET} — {r['set_name']} #{r['card_number']} ({r['release_year']}) | Raritá: {r['rarity']}")

            choice = input(f"\nSeleziona numero carta (1-{len(results)}) o 'c' per annullare: ").strip()
            if choice.lower() == 'c':
                continue

            try:
                card_idx = int(choice) - 1
                if not (0 <= card_idx < len(results)):
                    print(f"{C_RED}Selezione non valida.{C_RESET}")
                    continue
            except ValueError:
                print(f"{C_RED}Inserisci un numero valido.{C_RESET}")
                continue

            selected_card = results[card_idx]

            print(f"\nSeleziona finitura della carta:")
            print(f" [1] Normale (Standard)")
            print(f" [2] Holo / Olografica")
            print(f" [3] Reverse Holo")
            f_choice = input(f"Scelta (1/2/3, default 1): ").strip()
            finish_map = {'1': 'normale', '2': 'holo', '3': 'reverse holo'}
            finish = finish_map.get(f_choice, 'normale')

            # Valutazione con regole
            eval_res = core.evaluate_card(selected_card, finish=finish, register=False)
            if not eval_res.get('success'):
                print(f"\n{C_RED}❌ {eval_res.get('message')}{C_RESET}")
                continue

            display_evaluation(eval_res)

            confirm = input(f"\n{C_BOLD}Confermi iniezione nel gioco? (s/n, default s): {C_RESET}").strip().lower()
            if confirm in ['n', 'no']:
                print("Operazione annullata.")
                continue

            # Registra la carta per anti-duplicazione
            eval_res = core.evaluate_card(selected_card, finish=finish, register=True)
            inject_res = injector.inject_pokemon(eval_res)

            if inject_res.get('success'):
                if inject_res.get('status') == 'INJECTED':
                    print(f"\n{C_BOLD}{C_GREEN}✔ INIEZIONE COMPLETATA CON SUCCESSO!{C_RESET}")
                    print(f" Destinazione: {C_BOLD}{inject_res.get('target')}{C_RESET}")
                    print(f" Salvataggio : Backup salvato in {inject_res.get('backup')}")
                elif inject_res.get('status') == 'PENDING_EXPANSION':
                    print(f"\n{C_BOLD}{C_MAGENTA}ℹ {inject_res.get('message')}{C_RESET}")
            else:
                print(f"\n{C_RED}❌ Errore durante l'iniezione: {inject_res.get('error')}{C_RESET}")

        except KeyboardInterrupt:
            print("\nInterrotto dall'utente.")
            break


def main():
    parser = argparse.ArgumentParser(description="Pokémon B2W2 TCG Scanner & Injection Engine")
    parser.add_argument('--search', type=str, help="Cerca carta per nome Pokémon")
    parser.add_argument('--finish', type=str, default='normale', choices=['normale', 'holo', 'reverse holo'], help="Finitura della carta")
    parser.add_argument('--card-index', type=int, default=1, help="Indice della carta nei risultati di ricerca")
    parser.add_argument('--list-scanned', action='store_true', help="Mostra tutte le carte già registrate (Anti-Duplicazione)")
    parser.add_argument('--pending', action='store_true', help="Mostra i Pokémon di Gen 6-9 in attesa di Strada A")
    parser.add_argument('--history', action='store_true', help="Mostra cronologia iniezioni effettuate")

    args = parser.parse_args()
    core = TCGCore()
    injector = PokemonInjector()

    if args.list_scanned:
        print_banner()
        print(f"\n{C_BOLD}CARTE GIÀ SCANSIONATE ({len(core.scanned_cards)} registrate):{C_RESET}")
        for key, item in core.scanned_cards.items():
            print(f" • [{key}] {item['species']} (#{item['dex_id']}) — {item['set']} #{item['number']} ({item['finish']}) | Scansionato: {item['date']}")
        return

    if args.pending:
        print_banner()
        if not (BASE_DIR / 'scanner' / 'pending_expanded_pokemon.json').exists():
            print("Nessun Pokémon in attesa.")
            return
        with open(BASE_DIR / 'scanner' / 'pending_expanded_pokemon.json', 'r', encoding='utf-8') as f:
            pending = json.load(f)
        print(f"\n{C_BOLD}RACCOGLITORE VIRTUALE GEN 6-9 ({len(pending)} pronti per Strada A):{C_RESET}")
        for p in pending:
            print(f" • [#{p['species_id']}] {p['species_name']} — Lv.{p['level']} | {p['era_name']} ({p['pokeball_name']}) | Scansionato: {p['date_scanned']}")
        return

    if args.history:
        print_banner()
        hist_file = BASE_DIR / 'scanner' / 'scans_history.json'
        if not hist_file.exists():
            print("Nessuna iniezione registrata.")
            return
        with open(hist_file, 'r', encoding='utf-8') as f:
            hist = json.load(f)
        print(f"\n{C_BOLD}CRONOLOGIA INIEZIONI NEL GIOCO:{C_RESET}")
        for h in hist:
            print(f" • [{h['timestamp']}] {h['species_name']} Lv.{h['level']} -> {h['target']} ({h.get('pokeball', 'Poké Ball')})")
        return

    if args.search:
        results = core.search_cards(args.search, limit=10)
        if not results:
            print(f"Nessuna carta trovata per '{args.search}'.")
            return
        idx = max(0, min(len(results) - 1, args.card_index - 1))
        selected_card = results[idx]
        eval_res = core.evaluate_card(selected_card, finish=args.finish, register=True)
        if not eval_res.get('success'):
            print(f"Errore: {eval_res.get('message')}")
            return
        display_evaluation(eval_res)
        inject_res = injector.inject_pokemon(eval_res)
        print("\nEsito Iniezione:", inject_res)
        return

    # Modalità interattiva predefinita
    interactive_scan()


if __name__ == '__main__':
    main()
