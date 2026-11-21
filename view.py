"""Ansichtsebene (View) des Studien-Dashboards im Layout des Phase-1-Entwurfs.

Setzt das Kachel-Layout, den dreigeteilten ECTS-Fortschrittsbalken sowie die
farbcodierten Trend-Badges mittels tkinter und ttk um.
"""

from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
from controller import DashboardController
from domain import ModulStatus
from dto import DashboardDatenDTO
from repository import DATUMS_FORMAT


class DashboardView:
    """Grafische Benutzeroberfläche für das Studien-Dashboard."""

    BG_MAIN = "#f4f6f9"
    BG_CARD = "#ffffff"
    BORDER_COLOR = "#dce1e7"
    TEXT_PRIMARY = "#111827"
    TEXT_MUTED = "#6b7280"

    COLOR_GREEN = "#1f7a4c"
    COLOR_AMBER = "#df9f2e"
    COLOR_GRAY = "#dce1e7"

    BADGE_GREEN_BG = "#e6f4ea"
    BADGE_GREEN_FG = "#1e7e34"
    BADGE_RED_BG = "#fce8e6"
    BADGE_RED_FG = "#c5221f"
    BADGE_NEUTRAL_BG = "#f1f5f9"
    BADGE_NEUTRAL_FG = "#475569"

    BTN_DARK_BG = "#1f2937"
    BTN_DARK_FG = "#ffffff"

    def __init__(self, root: tk.Tk, controller: DashboardController) -> None:
        """Initialisiert das Hauptfenster, Stile und Layout-Komponenten."""
        self.root = root
        self.controller = controller
        self.root.title("Studien-Dashboard")
        self.root.geometry("1160x760")
        self.root.minsize(1020, 680)
        self.root.configure(bg=self.BG_MAIN)

        self._aktuelle_daten: DashboardDatenDTO | None = None
        self._konfiguriere_styles()
        self._baue_oberflaeche()

    def _konfiguriere_styles(self) -> None:
        """Konfiguriert das Erscheinungsbild der ttk-Komponenten."""
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=self.BG_CARD,
            fieldbackground=self.BG_CARD,
            foreground=self.TEXT_PRIMARY,
            rowheight=32,
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background="#f1f5f9",
            foreground="#334155",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padding=(8, 6),
        )
        style.map(
            "Treeview",
            background=[("selected", "#e2e8f0")],
            foreground=[("selected", self.TEXT_PRIMARY)],
        )

    def _erstelle_karte(
        self, parent: tk.Widget, padding: int = 16
    ) -> tuple[tk.Frame, tk.Frame]:
        """Erzeugt einen weißen Karten-Container mit feinem grauen Rahmen."""
        outer = tk.Frame(
            parent,
            bg=self.BG_CARD,
            highlightbackground=self.BORDER_COLOR,
            highlightthickness=1,
        )
        inner = tk.Frame(outer, bg=self.BG_CARD, padx=padding, pady=padding)
        inner.pack(fill=tk.BOTH, expand=True)
        return outer, inner

    def _baue_oberflaeche(self) -> None:
        """Baut die Oberfläche mit Header, KPI-Kacheln, Filtern und Modultabelle auf."""
        # 1. Weißer Header-Bereich
        header_bar = tk.Frame(
            self.root,
            bg=self.BG_CARD,
            highlightbackground=self.BORDER_COLOR,
            highlightthickness=1,
            padx=24,
            pady=14,
        )
        header_bar.pack(fill=tk.X)

        header_left = tk.Frame(header_bar, bg=self.BG_CARD)
        header_left.pack(side=tk.LEFT, fill=tk.Y)

        self.lbl_titel = tk.Label(
            header_left,
            text="Studien-Dashboard",
            font=("Segoe UI", 16, "bold"),
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
        )
        self.lbl_titel.pack(anchor=tk.W)

        tk.Label(
            header_left,
            text="Persönliche Studienorganisation & KPI-Monitoring",
            font=("Segoe UI", 10),
            bg=self.BG_CARD,
            fg=self.TEXT_MUTED,
        ).pack(anchor=tk.W, pady=(2, 0))

        self.lbl_ects_badge = tk.Label(
            header_bar,
            text="180 ECTS Gesamt",
            font=("Segoe UI", 10, "bold"),
            bg="#f8fafc",
            fg=self.TEXT_PRIMARY,
            padx=12,
            pady=6,
            highlightbackground=self.BORDER_COLOR,
            highlightthickness=1,
        )
        self.lbl_ects_badge.pack(side=tk.RIGHT, anchor=tk.CENTER)

        content = tk.Frame(self.root, bg=self.BG_MAIN, padx=24, pady=16)
        content.pack(fill=tk.BOTH, expand=True)

        # 2. Obere Karte: Gesamtfortschritt ECTS
        card_prog_outer, card_prog = self._erstelle_karte(content, padding=16)
        card_prog_outer.pack(fill=tk.X, pady=(0, 14))

        prog_top = tk.Frame(card_prog, bg=self.BG_CARD)
        prog_top.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            prog_top,
            text="Gesamtfortschritt ECTS",
            font=("Segoe UI", 11, "bold"),
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
        ).pack(side=tk.LEFT)

        self.lbl_ects_rechts = tk.Label(
            prog_top,
            text="0 / 180 ECTS (0.0 % absolviert)",
            font=("Segoe UI", 11, "bold"),
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
        )
        self.lbl_ects_rechts.pack(side=tk.RIGHT)

        self.canvas_bar = tk.Canvas(
            card_prog, height=26, bg=self.COLOR_GRAY, highlightthickness=0
        )
        self.canvas_bar.pack(fill=tk.X, pady=(2, 10))
        self.canvas_bar.bind(
            "<Configure>", lambda _e: self._zeichne_fortschrittsbalken()
        )

        prog_legend = tk.Frame(card_prog, bg=self.BG_CARD)
        prog_legend.pack(fill=tk.X)

        self.lbl_leg_abgeschl = tk.Label(
            prog_legend,
            text="■ Abgeschlossen & Anerkannt (0 ECTS)",
            font=("Segoe UI", 9),
            bg=self.BG_CARD,
            fg=self.COLOR_GREEN,
        )
        self.lbl_leg_abgeschl.pack(side=tk.LEFT, padx=(0, 20))

        self.lbl_leg_arbeit = tk.Label(
            prog_legend,
            text="■ In Bearbeitung (0 ECTS)",
            font=("Segoe UI", 9),
            bg=self.BG_CARD,
            fg="#b47b15",
        )
        self.lbl_leg_arbeit.pack(side=tk.LEFT, padx=(0, 20))

        self.lbl_leg_offen = tk.Label(
            prog_legend,
            text="■ Offen (0 ECTS)",
            font=("Segoe UI", 9),
            bg=self.BG_CARD,
            fg=self.TEXT_MUTED,
        )
        self.lbl_leg_offen.pack(side=tk.LEFT)

        # 3. Mittlere Reihe: 3 KPI-Karten
        kpi_row = tk.Frame(content, bg=self.BG_MAIN)
        kpi_row.pack(fill=tk.X, pady=(0, 16))
        kpi_row.columnconfigure((0, 1, 2), weight=1, uniform="kpi")

        # Karte 3a: Notendurchschnitt
        c_note_out, c_note = self._erstelle_karte(kpi_row)
        c_note_out.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(
            c_note,
            text="Notendurchschnitt",
            font=("Segoe UI", 10, "bold"),
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
        ).pack(anchor=tk.W)

        self.lbl_note_haupt = tk.Label(
            c_note,
            text="–",
            font=("Segoe UI", 22, "bold"),
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
        )
        self.lbl_note_haupt.pack(anchor=tk.W, pady=(6, 6))

        self.lbl_note_trend = tk.Label(
            c_note,
            text="Trend: –",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=3,
            bg=self.BADGE_NEUTRAL_BG,
            fg=self.BADGE_NEUTRAL_FG,
        )
        self.lbl_note_trend.pack(anchor=tk.W, pady=(0, 8))

        tk.Label(
            c_note,
            text="Nur regulär benotete Fächer (ohne Anerkennungen)",
            font=("Segoe UI", 9),
            bg=self.BG_CARD,
            fg=self.TEXT_MUTED,
        ).pack(anchor=tk.W)

        # Karte 3b: Ø Bearbeitungszeit pro Fach
        c_dauer_out, c_dauer = self._erstelle_karte(kpi_row)
        c_dauer_out.grid(row=0, column=1, sticky="nsew", padx=8)

        tk.Label(
            c_dauer,
            text="Ø Bearbeitungszeit pro Fach",
            font=("Segoe UI", 10, "bold"),
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
        ).pack(anchor=tk.W)

        self.lbl_dauer_haupt = tk.Label(
            c_dauer,
            text="–",
            font=("Segoe UI", 22, "bold"),
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
        )
        self.lbl_dauer_haupt.pack(anchor=tk.W, pady=(6, 6))

        self.lbl_dauer_trend = tk.Label(
            c_dauer,
            text="Trend: –",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=3,
            bg=self.BADGE_NEUTRAL_BG,
            fg=self.BADGE_NEUTRAL_FG,
        )
        self.lbl_dauer_trend.pack(anchor=tk.W, pady=(0, 8))

        tk.Label(
            c_dauer,
            text="Mittlere Durchlaufzeit abgeschlossener Module",
            font=("Segoe UI", 9),
            bg=self.BG_CARD,
            fg=self.TEXT_MUTED,
        ).pack(anchor=tk.W)

        # Karte 3c: Status & Vorleistungen
        c_stat_out, c_stat = self._erstelle_karte(kpi_row)
        c_stat_out.grid(row=0, column=2, sticky="nsew", padx=(8, 0))

        tk.Label(
            c_stat,
            text="Status & Vorleistungen",
            font=("Segoe UI", 10, "bold"),
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
        ).pack(anchor=tk.W, pady=(0, 8))

        self.lbl_status_zeile1 = tk.Label(
            c_stat,
            text="0 Abgeschlossen  |  0 Angerechnet (ohne Note)",
            font=("Segoe UI", 10),
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
        )
        self.lbl_status_zeile1.pack(anchor=tk.W, pady=(2, 2))

        self.lbl_status_zeile2 = tk.Label(
            c_stat,
            text="0 In Bearbeitung  |  0 Offen",
            font=("Segoe UI", 10),
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
        )
        self.lbl_status_zeile2.pack(anchor=tk.W, pady=(0, 10))

        tk.Frame(c_stat, bg=self.BORDER_COLOR, height=1).pack(
            fill=tk.X, pady=(2, 8)
        )

        self.lbl_aktive_belastung = tk.Label(
            c_stat,
            text="Aktive Belastung: 0 ECTS parallel",
            font=("Segoe UI", 9),
            bg=self.BG_CARD,
            fg=self.TEXT_MUTED,
        )
        self.lbl_aktive_belastung.pack(anchor=tk.W)

        # 4. Filter- und Aktionsleiste
        filter_bar = tk.Frame(content, bg=self.BG_MAIN)
        filter_bar.pack(fill=tk.X, pady=(0, 12))

        sem_box = tk.Frame(filter_bar, bg=self.BG_MAIN)
        sem_box.pack(side=tk.LEFT, padx=(0, 16))
        tk.Label(
            sem_box,
            text="Semester",
            font=("Segoe UI", 9, "bold"),
            bg=self.BG_MAIN,
            fg="#374151",
        ).pack(anchor=tk.W, pady=(0, 3))
        self.cmb_semester = ttk.Combobox(
            sem_box, state="readonly", width=18, font=("Segoe UI", 10)
        )
        self.cmb_semester.pack(anchor=tk.W)
        self.cmb_semester.bind("<<ComboboxSelected>>", self._on_filter_geandert)

        stat_box = tk.Frame(filter_bar, bg=self.BG_MAIN)
        stat_box.pack(side=tk.LEFT, padx=(0, 16))
        tk.Label(
            stat_box,
            text="Status",
            font=("Segoe UI", 9, "bold"),
            bg=self.BG_MAIN,
            fg="#374151",
        ).pack(anchor=tk.W, pady=(0, 3))
        self.cmb_status = ttk.Combobox(
            stat_box, state="readonly", width=20, font=("Segoe UI", 10)
        )
        self.cmb_status["values"] = ["Alle Status"] + [
            s.value for s in ModulStatus
        ]
        self.cmb_status.current(0)
        self.cmb_status.pack(anchor=tk.W)
        self.cmb_status.bind("<<ComboboxSelected>>", self._on_filter_geandert)

        reset_box = tk.Frame(filter_bar, bg=self.BG_MAIN)
        reset_box.pack(side=tk.LEFT)
        tk.Label(reset_box, text="", font=("Segoe UI", 9), bg=self.BG_MAIN).pack(
            pady=(0, 3)
        )
        tk.Button(
            reset_box,
            text="Filter zurücksetzen",
            font=("Segoe UI", 9),
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=10,
            pady=4,
            highlightbackground=self.BORDER_COLOR,
            highlightthickness=1,
            cursor="hand2",
            command=self._on_filter_reset,
        ).pack()

        btn_box = tk.Frame(filter_bar, bg=self.BG_MAIN)
        btn_box.pack(side=tk.RIGHT)
        tk.Label(btn_box, text="", font=("Segoe UI", 9), bg=self.BG_MAIN).pack(
            pady=(0, 3)
        )
        tk.Button(
            btn_box,
            text="+ Status / Note bearbeiten",
            font=("Segoe UI", 10, "bold"),
            bg=self.BTN_DARK_BG,
            fg=self.BTN_DARK_FG,
            activebackground="#374151",
            activeforeground=self.BTN_DARK_FG,
            relief=tk.FLAT,
            padx=14,
            pady=5,
            cursor="hand2",
            command=self._oeffne_bearbeiten_dialog,
        ).pack()

        # 5. Tabellenüberschrift + Modultabelle
        tbl_hdr = tk.Frame(content, bg=self.BG_MAIN)
        tbl_hdr.pack(fill=tk.X, pady=(0, 4))
        tk.Label(
            tbl_hdr,
            text="Modulübersicht",
            font=("Segoe UI", 11, "bold"),
            bg=self.BG_MAIN,
            fg=self.TEXT_PRIMARY,
        ).pack(side=tk.LEFT)

        tabellen_frame = tk.Frame(
            content,
            bg=self.BG_CARD,
            highlightbackground=self.BORDER_COLOR,
            highlightthickness=1,
        )
        tabellen_frame.pack(fill=tk.BOTH, expand=True)

        spalten = (
            "code",
            "titel",
            "semester",
            "ects",
            "status",
            "note",
            "start",
            "ende",
            "dauer",
        )
        self.tree = ttk.Treeview(
            tabellen_frame, columns=spalten, show="headings", selectmode="browse"
        )

        ueberschriften = {
            "code": ("Code", 120),
            "titel": ("Modul", 330),
            "semester": ("Sem.", 60),
            "ects": ("ECTS", 60),
            "status": ("Status", 130),
            "note": ("Note", 95),
            "start": ("Beginn", 100),
            "ende": ("Abschluss", 100),
            "dauer": ("Dauer", 85),
        }
        for spalte, (text, breite) in ueberschriften.items():
            self.tree.heading(spalte, text=text, anchor=tk.W)
            self.tree.column(spalte, width=breite, anchor=tk.W)

        scrollbar = ttk.Scrollbar(
            tabellen_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self._on_auswahl_geandert)

        # 6. Fußzeile
        footer = tk.Frame(content, bg=self.BG_MAIN)
        footer.pack(fill=tk.X, pady=(6, 0))

        self.lbl_footer_links = tk.Label(
            footer,
            text="0 Module angezeigt · Keine Auswahl",
            font=("Segoe UI", 9),
            bg=self.BG_MAIN,
            fg=self.TEXT_MUTED,
        )
        self.lbl_footer_links.pack(side=tk.LEFT)

        tk.Label(
            footer,
            text="Kennzahlen beziehen sich auf das gesamte Studium.",
            font=("Segoe UI", 9),
            bg=self.BG_MAIN,
            fg=self.TEXT_MUTED,
        ).pack(side=tk.RIGHT)

    def zeige(self, daten: DashboardDatenDTO) -> None:
        """Aktualisiert sämtliche Kacheln, Balken und die Tabelle anhand des DTOs."""
        self._aktuelle_daten = daten

        self.lbl_titel.config(
            text=f"Studien-Dashboard  |  {daten.studiengang_titel}"
        )
        self.lbl_ects_badge.config(text=f"{daten.gesamt_ects} ECTS Gesamt")

        prozent_fertig = (
            round((daten.erreichte_ects / daten.gesamt_ects) * 100, 1)
            if daten.gesamt_ects
            else 0.0
        )
        self.lbl_ects_rechts.config(
            text=f"{daten.erreichte_ects} / {daten.gesamt_ects} ECTS ({prozent_fertig} % absolviert)"
        )
        self.lbl_leg_abgeschl.config(
            text=f"■ Abgeschlossen & Anerkannt ({daten.erreichte_ects} ECTS)"
        )
        self.lbl_leg_arbeit.config(
            text=f"■ In Bearbeitung ({daten.in_bearbeitung_ects} ECTS)"
        )
        self.lbl_leg_offen.config(text=f"■ Offen ({daten.offene_ects} ECTS)")
        self._zeichne_fortschrittsbalken()

        self.lbl_note_haupt.config(
            text=f"Ø {daten.gesamtnote:.2f}"
            if daten.gesamtnote is not None
            else "–"
        )
        self._aktualisiere_trend_badge(
            self.lbl_note_trend,
            daten.noten_trend,
            einheit="",
            positiv_text="Verbessert",
            negativ_text="Verschlechtert",
        )

        self.lbl_dauer_haupt.config(
            text=f"{daten.durchschnitts_dauer:.1f} Wochen"
            if daten.durchschnitts_dauer is not None
            else "–"
        )
        self._aktualisiere_trend_badge(
            self.lbl_dauer_trend,
            daten.dauer_trend,
            einheit=" W.",
            positiv_text="Schneller",
            negativ_text="Verzögert",
        )

        anz = daten.status_anzahl
        self.lbl_status_zeile1.config(
            text=(
                f"{anz.get('Abgeschlossen', 0)} Abgeschlossen   |   "
                f"{anz.get('Angerechnet', 0)} Angerechnet (ohne Note)"
            )
        )
        self.lbl_status_zeile2.config(
            text=(
                f"{anz.get('In Bearbeitung', 0)} In Bearbeitung   |   "
                f"{anz.get('Offen', 0)} Offen"
            )
        )
        self.lbl_aktive_belastung.config(
            text=f"Aktive Belastung: {daten.in_bearbeitung_ects} ECTS parallel"
        )

        sem_werte = ["Alle Semester"] + [
            f"Semester {nr}" for nr in daten.semester_nummern
        ]
        if list(self.cmb_semester["values"]) != sem_werte:
            self.cmb_semester["values"] = sem_werte
            self.cmb_semester.current(0)

        for item in self.tree.get_children():
            self.tree.delete(item)

        for eintrag in daten.modul_eintraege:
            dauer_anzeige = (
                f"{eintrag.dauer_wochen} W."
                if eintrag.dauer_wochen != "-"
                else (
                    "Laufend"
                    if eintrag.status == ModulStatus.IN_BEARBEITUNG.value
                    else "–"
                )
            )
            self.tree.insert(
                "",
                tk.END,
                values=(
                    eintrag.code,
                    eintrag.titel,
                    eintrag.semester,
                    eintrag.ects,
                    f"● {eintrag.status}",
                    eintrag.note_oder_anerkannt,
                    eintrag.start_datum,
                    eintrag.end_datum,
                    dauer_anzeige,
                ),
            )

        self._on_auswahl_geandert()

    def _zeichne_fortschrittsbalken(self) -> None:
        """Zeichnet den dreigeteilten Fortschrittsbalken (Grün / Gelb / Grau) auf das Canvas."""
        self.canvas_bar.delete("all")
        if not self._aktuelle_daten or self._aktuelle_daten.gesamt_ects <= 0:
            return

        breite = self.canvas_bar.winfo_width()
        hoehe = self.canvas_bar.winfo_height()
        if breite <= 10:
            return

        gesamt = self._aktuelle_daten.gesamt_ects
        ect_fertig = self._aktuelle_daten.erreichte_ects
        ect_arbeit = self._aktuelle_daten.in_bearbeitung_ects
        ect_offen = max(0, gesamt - ect_fertig - ect_arbeit)

        w_fertig = int((ect_fertig / gesamt) * breite)
        w_arbeit = int((ect_arbeit / gesamt) * breite)

        if w_fertig > 0:
            self.canvas_bar.create_rectangle(
                0, 0, w_fertig, hoehe, fill=self.COLOR_GREEN, width=0
            )
            prz = round((ect_fertig / gesamt) * 100)
            if w_fertig > 40:
                self.canvas_bar.create_text(
                    w_fertig / 2,
                    hoehe / 2,
                    text=f"{prz} %",
                    fill="#ffffff",
                    font=("Segoe UI", 9, "bold"),
                )

        if w_arbeit > 0:
            x1, x2 = w_fertig, w_fertig + w_arbeit
            self.canvas_bar.create_rectangle(
                x1, 0, x2, hoehe, fill=self.COLOR_AMBER, width=0
            )
            prz = round((ect_arbeit / gesamt) * 100)
            if w_arbeit > 40:
                self.canvas_bar.create_text(
                    (x1 + x2) / 2,
                    hoehe / 2,
                    text=f"{prz} %",
                    fill=self.TEXT_PRIMARY,
                    font=("Segoe UI", 9, "bold"),
                )

        x_offen = w_fertig + w_arbeit
        w_offen = breite - x_offen
        if w_offen > 0:
            self.canvas_bar.create_rectangle(
                x_offen, 0, breite, hoehe, fill=self.COLOR_GRAY, width=0
            )
            prz = round((ect_offen / gesamt) * 100)
            if w_offen > 45:
                self.canvas_bar.create_text(
                    x_offen + w_offen / 2,
                    hoehe / 2,
                    text=f"{prz} %",
                    fill="#475569",
                    font=("Segoe UI", 9, "bold"),
                )

    def _aktualisiere_trend_badge(
        self,
        label: tk.Label,
        trend: float | None,
        einheit: str,
        positiv_text: str,
        negativ_text: str,
    ) -> None:
        """Formatiert das Trend-Label als farbiges Badge."""
        if trend is None:
            label.config(
                text="Noch keine Vergleichsdaten",
                bg=self.BADGE_NEUTRAL_BG,
                fg=self.BADGE_NEUTRAL_FG,
            )
        elif trend <= 0:
            label.config(
                text=f"▲ {positiv_text} ({trend}{einheit})",
                bg=self.BADGE_GREEN_BG,
                fg=self.BADGE_GREEN_FG,
            )
        else:
            label.config(
                text=f"▼ {negativ_text} (+{trend}{einheit})",
                bg=self.BADGE_RED_BG,
                fg=self.BADGE_RED_FG,
            )

    def _on_auswahl_geandert(self, _event: object = None) -> None:
        """Aktualisiert die Statuszeile links unten bei Auswahl einer Tabellenzeile."""
        anzahl = len(self.tree.get_children())
        auswahl = self.tree.selection()
        if auswahl:
            werte = self.tree.item(auswahl[0], "values")
            auswahl_text = f"Ausgewählt: {werte[0]}"
        else:
            auswahl_text = "Keine Auswahl"
        self.lbl_footer_links.config(
            text=f"{anzahl} Module angezeigt · {auswahl_text}"
        )

    def _on_filter_geandert(self, _event: object = None) -> None:
        """Liest die aktiven Combobox-Filter aus und lädt das DTO neu."""
        sem_text = self.cmb_semester.get()
        stat_text = self.cmb_status.get()

        sem_filter = (
            int(sem_text.replace("Semester ", ""))
            if sem_text and sem_text.startswith("Semester ")
            else None
        )
        stat_filter = (
            stat_text if stat_text and stat_text != "Alle Status" else None
        )

        neues_dto = self.controller.lade_dashboard_daten(
            semester_filter=sem_filter, status_filter=stat_filter
        )
        self.zeige(neues_dto)

    def _on_filter_reset(self) -> None:
        """Setzt die Filter auf den Ausgangszustand zurück."""
        self.cmb_semester.current(0)
        self.cmb_status.current(0)
        self._on_filter_geandert()

    def _oeffne_bearbeiten_dialog(self) -> None:
        """Öffnet den modalen Dialog zum Bearbeiten des ausgewählten Moduls."""
        auswahl = self.tree.selection()
        if not auswahl:
            messagebox.showinfo(
                "Hinweis", "Bitte wähle zuerst ein Modul in der Tabelle aus."
            )
            return

        werte = self.tree.item(auswahl[0], "values")
        code = str(werte[0])
        titel = str(werte[1])
        note_str = str(werte[5])
        start_str = str(werte[6])
        ende_str = str(werte[7])

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Modul bearbeiten: {code}")
        dialog.configure(bg=self.BG_CARD)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        frame = tk.Frame(dialog, bg=self.BG_CARD, padx=20, pady=18)
        frame.pack(fill=tk.BOTH, expand=True)

        # Zeile 0: Modultitel
        tk.Label(
            frame,
            text=f"{code} – {titel}",
            font=("Segoe UI", 10, "bold"),
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
            wraplength=380,
            justify=tk.LEFT,
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 14))

        # Zeile 1: Startdatum
        tk.Label(
            frame,
            text="Startdatum (TT.MM.JJJJ):",
            font=("Segoe UI", 9),
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
        ).grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        ent_start = ttk.Entry(frame, width=24)
        if start_str not in ("-", "–"):
            ent_start.insert(0, start_str)
        ent_start.grid(row=1, column=1, sticky=tk.W, pady=5)

        # Zeile 2: Enddatum
        tk.Label(
            frame,
            text="Enddatum (TT.MM.JJJJ):",
            font=("Segoe UI", 9),
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
        ).grid(row=2, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        ent_ende = ttk.Entry(frame, width=24)
        if ende_str not in ("-", "–"):
            ent_ende.insert(0, ende_str)
        ent_ende.grid(row=2, column=1, sticky=tk.W, pady=5)

        # Zeile 3: Prüfungsnote
        tk.Label(
            frame,
            text="Prüfungsnote (1.0 – 5.0):",
            font=("Segoe UI", 9),
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
        ).grid(row=3, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        ent_note = ttk.Entry(frame, width=24)
        if note_str not in ("-", "–", "Anerkannt"):
            ent_note.insert(0, note_str)
        ent_note.grid(row=3, column=1, sticky=tk.W, pady=5)

        # Zeile 4: Checkbox (tk.Checkbutton unterstützt bg und font direkt)
        var_anerkannt = tk.BooleanVar(
            master=dialog, value=(note_str == "Anerkannt")
        )
        chk_anerkannt = tk.Checkbutton(
            frame,
            text="Als Vorleistung angerechnet (ohne Note)",
            variable=var_anerkannt,
            bg=self.BG_CARD,
            activebackground=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
            font=("Segoe UI", 9),
        )
        chk_anerkannt.grid(
            row=4, column=0, columnspan=2, sticky=tk.W, pady=(10, 16)
        )

        # Zeile 5: Aktionsbuttons
        def _speichern() -> None:
            self.on_modul_bearbeiten(
                code=code,
                start_text=ent_start.get().strip(),
                ende_text=ent_ende.get().strip(),
                note_text=ent_note.get().strip(),
                anerkannt=var_anerkannt.get(),
                dialog=dialog,
            )

        btn_frame = tk.Frame(frame, bg=self.BG_CARD)
        btn_frame.grid(row=5, column=0, columnspan=2, sticky=tk.E, pady=(4, 0))

        tk.Button(
            btn_frame,
            text="Abbrechen",
            font=("Segoe UI", 9),
            bg="#f1f5f9",
            fg=self.TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=12,
            pady=4,
            command=dialog.destroy,
        ).pack(side=tk.RIGHT, padx=(8, 0))

        tk.Button(
            btn_frame,
            text="Speichern",
            font=("Segoe UI", 9, "bold"),
            bg=self.BTN_DARK_BG,
            fg=self.BTN_DARK_FG,
            activebackground="#374151",
            activeforeground=self.BTN_DARK_FG,
            relief=tk.FLAT,
            padx=14,
            pady=4,
            command=_speichern,
        ).pack(side=tk.RIGHT)

        dialog.update_idletasks()
        dialog.minsize(430, dialog.winfo_reqheight())

    def on_modul_bearbeiten(
        self,
        code: str,
        start_text: str,
        ende_text: str,
        note_text: str,
        anerkannt: bool,
        dialog: tk.Toplevel,
    ) -> None:
        """Konvertiert die Benutzereingaben (TT.MM.JJJJ) und übergibt sie an den Controller."""
        try:
            start_dt = (
                datetime.strptime(start_text, DATUMS_FORMAT).date()
                if start_text
                else None
            )
            ende_dt = (
                datetime.strptime(ende_text, DATUMS_FORMAT).date()
                if ende_text
                else None
            )
        except ValueError:
            messagebox.showerror(
                "Ungültiges Datum",
                "Bitte gib Datumsangaben im deutschen Format TT.MM.JJJJ (z. B. 15.10.2026) ein.",
                parent=dialog,
            )
            return

        try:
            note_val = (
                float(note_text.replace(",", "."))
                if note_text and not anerkannt
                else None
            )
        except ValueError:
            messagebox.showerror(
                "Ungültige Note",
                "Bitte gib eine gültige Dezimalzahl für die Note ein (z. B. 1,7 oder 1.7).",
                parent=dialog,
            )
            return

        try:
            self.controller.speichere_modul_update(
                code=code,
                start_datum=start_dt,
                end_datum=ende_dt,
                note=note_val,
                anerkannt=anerkannt,
            )
        except ValueError as err:
            messagebox.showerror("Validierungsfehler", str(err), parent=dialog)
            return

        dialog.destroy()
        self._on_filter_geandert()