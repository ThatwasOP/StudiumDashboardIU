"""Domänenschicht (Domain Model) des Studien-Dashboards.

Dieses Modul kapselt die Kerndatenstrukturen (Studiengang, Semester, Modul,
Pruefungsleistung) sowie die zugehörigen Enumerationen und abgeleiteten
Fachlogik-Eigenschaften. Es besitzt keinerlei Abhängigkeiten zur UI oder
zur Datenpersistenz.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class Abschlussart(Enum):
    """Definiert die zulässigen akademischen Abschlussgrade eines Studiengangs."""

    BACHELOR_OF_SCIENCE = "B.Sc."
    BACHELOR_OF_ARTS = "B.A."
    MASTER_OF_SCIENCE = "M.Sc."


class ModulStatus(Enum):
    """Definiert die möglichen Bearbeitungszustände eines Studienmoduls."""

    OFFEN = "Offen"
    IN_BEARBEITUNG = "In Bearbeitung"
    ABGESCHLOSSEN = "Abgeschlossen"
    ANGERECHNET = "Angerechnet"


@dataclass
class Pruefungsleistung(ABC):
    """Abstrakte Basisklasse für alle Arten von Prüfungsleistungen.

    Gibt die gemeinsame Schnittstelle für regulär benotete Prüfungen und
    unbenotete Anerkennungen vor, um eine polymorphe Auswertung zu ermöglichen.
    """

    titel: str

    @property
    @abstractmethod
    def bestanden(self) -> bool:
        """Gibt zurück, ob die Prüfungsleistung erfolgreich absolviert wurde."""
        pass

    @abstractmethod
    def ist_benotet(self) -> bool:
        """Gibt an, ob die Leistung eine numerische Note für den Schnitt besitzt."""
        pass


@dataclass
class RegulaerePruefung(Pruefungsleistung):
    """Repräsentiert eine regulär abgelegte, benotete Prüfungsleistung."""

    note: float

    def __post_init__(self) -> None:
        """Validiert den zulässigen Notenbereich direkt bei der Instanziierung.

        Raises:
            ValueError: Wenn die Note außerhalb des Bereichs 1.0 bis 5.0 liegt.
        """
        if not (1.0 <= self.note <= 5.0):
            raise ValueError(
                f"Ungültige Note ({self.note}). Erlaubt sind Werte zwischen 1.0 und 5.0."
            )

    @property
    def bestanden(self) -> bool:
        """Eine reguläre Prüfung gilt im deutschen Notensystem bis 4.0 als bestanden."""
        return 1.0 <= self.note <= 4.0

    def ist_benotet(self) -> bool:
        """Reguläre Prüfungen fließen in die Berechnung der Gesamtnote ein."""
        return True


@dataclass
class AnerkannteLeistung(Pruefungsleistung):
    """Repräsentiert eine angerechnete Vorleistung ohne numerische Note."""

    anerkennungsdatum: date

    @property
    def bestanden(self) -> bool:
        """Angerechnete Leistungen sind per Definition immer bestanden."""
        return True

    def ist_benotet(self) -> bool:
        """Anerkennungen besitzen keine Note und werden beim Notenschnitt ignoriert."""
        return False


@dataclass
class Modul:
    """Repräsentiert ein einzelnes Lehrveranstaltungsmodul innerhalb eines Semesters."""

    code: str
    titel: str
    ects: int
    start_datum: date | None = None
    end_datum: date | None = None
    pruefungsleistung: Pruefungsleistung | None = None

    @property
    def status(self) -> ModulStatus:
        """Leitet den aktuellen Modulstatus dynamisch aus Prüfungsleistung und Startdatum ab.

        Verhindert inkonsistente Objektzustände (z. B. Status 'Offen' trotz bestandener Prüfung).
        """
        if isinstance(self.pruefungsleistung, AnerkannteLeistung):
            return ModulStatus.ANGERECHNET
        if self.pruefungsleistung and self.pruefungsleistung.bestanden:
            return ModulStatus.ABGESCHLOSSEN
        return ModulStatus.IN_BEARBEITUNG if self.start_datum else ModulStatus.OFFEN

    @property
    def dauer_wochen(self) -> float | None:
        """Berechnet die Bearbeitungsdauer in Wochen auf eine Nachkommastelle gerundet.

        Returns:
            Bearbeitungsdauer in Wochen oder None, falls Start-/Enddatum fehlen.
        """
        if self.start_datum and self.end_datum and self.end_datum >= self.start_datum:
            tage = (self.end_datum - self.start_datum).days
            return round(tage / 7.0, 1)
        return None

    def ist_abgeschlossen(self) -> bool:
        """Prüft, ob das Modul erfolgreich erledigt ist (regulär oder angerechnet)."""
        return self.status in (ModulStatus.ABGESCHLOSSEN, ModulStatus.ANGERECHNET)


@dataclass
class Semester:
    """Gruppiert die einem Fachsemester zugeordneten Module."""

    nummer: int
    ziel_ects: float = 22.5
    # default_factory erzeugt pro Semester-Instanz eine eigene, unabhängige Liste
    module: list[Modul] = field(default_factory=list)

    @property
    def erreichte_semester_ects(self) -> int:
        """Summiert die ECTS-Punkte aller abgeschlossenen Module dieses Semesters."""
        return sum(m.ects for m in self.module if m.ist_abgeschlossen())


@dataclass
class Studiengang:
    """Wurzel-Entität des Domänenmodells; bündelt alle Semester und Gesamtkennzahlen."""

    name: str
    abschluss: Abschlussart
    regelstudienzeit_monate: int = 48
    gesamt_ects: int = 180
    semester_liste: list[Semester] = field(default_factory=list)

    @property
    def alle_module(self) -> list[Modul]:
        """Liefert eine flache Liste sämtlicher Module über alle Semester hinweg."""
        return [m for s in self.semester_liste for m in s.module]

    @property
    def erreichte_ects(self) -> int:
        """Berechnet die Gesamtsumme aller bislang erreichten ECTS-Punkte."""
        return sum(s.erreichte_semester_ects for s in self.semester_liste)

    @property
    def gesamtnote(self) -> float | None:
        """Berechnet den mit den ECTS-Punkten gewichteten Notendurchschnitt.

        Unbenotete Anerkennungen sowie nicht bestandene Prüfungen werden über
        die polymorphen Eigenschaften 'ist_benotet()' und 'bestanden' herausgefiltert.
        """
        benotete = [
            m
            for m in self.alle_module
            if m.pruefungsleistung
            and m.pruefungsleistung.ist_benotet()
            and m.pruefungsleistung.bestanden
        ]
        if not benotete:
            return None

        # Gewichtung jeder Note mit den zugehörigen ECTS-Punkten des Moduls
        gewichtete_summe = sum(
            m.pruefungsleistung.note * m.ects  # type: ignore[attr-defined]
            for m in benotete
        )
        ects_summe = sum(m.ects for m in benotete)
        return round(gewichtete_summe / ects_summe, 2) if ects_summe else None

    @property
    def durchschnittliche_bearbeitungszeit(self) -> float | None:
        """Berechnet die durchschnittliche Bearbeitungsdauer abgeschlossener Module in Wochen.

        Anerkannte Leistungen fließen nicht ein, da für sie keine reale Bearbeitungszeit
        im Studium angefallen ist.
        """
        dauern = [
            m.dauer_wochen
            for m in self.alle_module
            if m.status == ModulStatus.ABGESCHLOSSEN and m.dauer_wochen is not None
        ]
        if not dauern:
            return None
        return round(sum(dauern) / len(dauern), 1)