#!/usr/bin/env python3
"""
Pannello Interno Sovrapposto e Trascinabile (In-Game Floating Matrioska Widget).
Rappresenta una scheda o finestra che vive INTERAMENTE all'interno dei bordi
della finestra principale del gioco o del launcher (stile PokéMMO).
- NON genera finestre separate a livello di desktop / OS (zero piastrelle in Hyprland).
- NON può oltrepassare i bordi del gioco/launcher (movimento rigorosamente vincolato).
- Può essere spostato liberamente trascinando la barra superiore dell'header.
- Si chiude automaticamente quando viene chiuso il gioco.
"""

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QFrame, QPushButton, QLineEdit, QComboBox, QWidget


class DraggableInGamePanel(QFrame):
    def __init__(self, parent: QWidget = None, header_height: int = 60):
        super().__init__(parent)
        self.setObjectName("CardFrame")
        self._dragging = False
        self._drag_start = None
        self._header_height = header_height
        self.raise_()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.pos().y() <= self._header_height:
            child = self.childAt(event.pos())
            # Permetti il drag solo se non si è cliccato su controlli interattivi
            if not isinstance(child, (QPushButton, QLineEdit, QComboBox)):
                self._dragging = True
                self._drag_start = event.pos()
                self.raise_()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_start:
            parent = self.parentWidget()
            if parent:
                delta = event.pos() - self._drag_start
                new_x = self.x() + delta.x()
                new_y = self.y() + delta.y()
                # Vincolo assoluto: non può uscire dai bordi del genitore
                max_x = max(0, parent.width() - self.width())
                max_y = max(0, parent.height() - self.height())
                clamped_x = max(0, min(new_x, max_x))
                clamped_y = max(0, min(new_y, max_y))
                self.move(clamped_x, clamped_y)
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._drag_start = None
        super().mouseReleaseEvent(event)

    def close(self):
        self.hide()
        return True
