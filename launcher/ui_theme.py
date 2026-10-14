#!/usr/bin/env python3
"""
Stili grafici moderni (QSS) per il Launcher e il Client di Gioco.
Ispirato all'estetica dark-gaming, neon cyan, emerald e glassmorphism
dei moderni client per PC (PokeMMO, Riot Games).
"""

STYLE_SHEET = """
QMainWindow, QDialog {
    background-color: #0b0f19;
    color: #e2e8f0;
    font-family: 'Segoe UI', 'Ubuntu', 'Helvetica Neue', sans-serif;
}

QWidget#CentralWidget {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #070a12, stop:0.5 #0d1527, stop:1 #060911);
}

QFrame#CardFrame {
    background-color: rgba(19, 27, 46, 0.85);
    border: 1px solid #1e293b;
    border-radius: 16px;
}

QFrame#InnerPanel {
    background-color: rgba(13, 20, 36, 0.9);
    border: 1px solid #233554;
    border-radius: 12px;
}

QLabel {
    color: #cbd5e1;
}

QLabel#TitleLabel {
    color: #ffffff;
    font-size: 26px;
    font-weight: 800;
    letter-spacing: 2px;
}

QLabel#SubtitleLabel {
    color: #00e5ff;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1px;
}

QLabel#HeaderLabel {
    color: #f8fafc;
    font-size: 15px;
    font-weight: 700;
}

QLineEdit {
    background-color: #0a1120;
    border: 1.5px solid #1e2e4a;
    border-radius: 8px;
    padding: 10px 14px;
    color: #ffffff;
    font-size: 14px;
    selection-background-color: #00e5ff;
}

QLineEdit:focus {
    border: 1.5px solid #00e5ff;
    background-color: #0d172c;
}

QLineEdit::placeholder {
    color: #475569;
}

QPushButton#PlayButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00e676, stop:1 #00c853);
    color: #041f0e;
    font-size: 18px;
    font-weight: 800;
    letter-spacing: 2px;
    border: none;
    border-radius: 10px;
    padding: 14px 28px;
}

QPushButton#PlayButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #69f0ae, stop:1 #00e676);
}

QPushButton#PlayButton:pressed {
    background-color: #00b248;
}

QPushButton#SecondaryButton {
    background-color: #17253d;
    border: 1px solid #2a3d5e;
    border-radius: 8px;
    color: #94a3b8;
    font-size: 13px;
    font-weight: 600;
    padding: 8px 16px;
}

QPushButton#SecondaryButton:hover {
    background-color: #1f3354;
    border-color: #00e5ff;
    color: #ffffff;
}

QPushButton#TabButtonActive {
    background-color: #1e293b;
    border: 1px solid #00e5ff;
    border-radius: 8px;
    color: #00e5ff;
    font-size: 13px;
    font-weight: 700;
    padding: 6px 16px;
}

QPushButton#TabButtonInactive {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    color: #64748b;
    font-size: 13px;
    font-weight: 600;
    padding: 6px 16px;
}

QPushButton#TabButtonInactive:hover {
    color: #cbd5e1;
    background-color: #131b2e;
}

QComboBox {
    background-color: #0a1120;
    border: 1px solid #1e2e4a;
    border-radius: 8px;
    padding: 6px 12px;
    color: #cbd5e1;
    font-size: 13px;
}

QComboBox:hover {
    border-color: #00e5ff;
}

QComboBox QAbstractItemView {
    background-color: #0d172c;
    border: 1px solid #1e2e4a;
    selection-background-color: #1e293b;
    color: #ffffff;
}

QCheckBox {
    color: #94a3b8;
    font-size: 13px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #334155;
    border-radius: 4px;
    background-color: #0a1120;
}

QCheckBox::indicator:checked {
    background-color: #00e5ff;
    border-color: #00e5ff;
}

QFrame#RomBadgeActive {
    background-color: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    border-radius: 10px;
}

QFrame#RomBadgeMissing {
    background-color: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    border-radius: 10px;
}

QScrollArea {
    border: none;
    background: transparent;
}
"""
