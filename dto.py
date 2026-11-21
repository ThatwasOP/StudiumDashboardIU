"""Datenübertragungsobjekte (Data Transfer Objects) für die Kommunikation zwischen Controller und View.

Die DTOs sind durch 'frozen=True' schreibgeschützt und stellen sicher, dass die
grafische Benutzeroberfläche alle anzuzeigenden Daten (KPIs, Filterwerte und
Tabellenzeilen) fertig aufbereitet und typsicher erhält.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModulTabellenEintragDTO:
    """Repräsentiert eine fertig formatierte Tabellenzeile für die Modulübersicht in der GUI."""

    semester: int
    code: str
    titel: str
    ects: int
    status: str
    start_datum: str
    end_datum: str
    dauer_wochen: str
    note_oder_anerkannt: str


@dataclass(frozen=True)
class DashboardDatenDTO:
    """Bündelt sämtliche Kennzahlen, Statusanzahlen und Tabellendaten für die DashboardView."""

    studiengang_titel: str
    gesamt_ects: int
    erreichte_ects: int
    in_bearbeitung_ects: int
    offene_ects: int
    status_anzahl: dict[str, int]
    gesamtnote: float | None
    noten_trend: float | None
    durchschnitts_dauer: float | None
    dauer_trend: float | None
    semester_nummern: list[int]
    modul_eintraege: list[ModulTabellenEintragDTO]