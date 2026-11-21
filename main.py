"""Anwendungsschicht (Composition Root) des Studien-Dashboards.

Erstellt die konkreten Instanzen von Repository, Service, Controller und View,
verbindet deren Abhängigkeiten und startet die grafische Benutzeroberfläche.
"""

from pathlib import Path
import tkinter as tk
from controller import DashboardController
from repository import JsonModulRepository
from services import KennzahlenService
from view import DashboardView


class DashboardApp:
    """Zentraler Einstiegspunkt (Composition Root) der Anwendung."""

    def __init__(self, daten_datei: Path | None = None) -> None:
        """Initialisiert den Dateipfad für die JSON-Persistenz."""
        self.daten_datei = daten_datei or Path(__file__).with_name(
            "studium_daten.json"
        )

    def start(self) -> None:
        """Instanziiert alle Schichten, lädt die Initialdaten und startet die GUI."""
        repository = JsonModulRepository(self.daten_datei)
        service = KennzahlenService()
        controller = DashboardController(repository=repository, service=service)

        root = tk.Tk()
        view = DashboardView(root=root, controller=controller)

        initiale_daten = controller.lade_dashboard_daten()
        view.zeige(initiale_daten)

        root.mainloop()


if __name__ == "__main__":
    app = DashboardApp()
    app.start()