"""Repository-Schicht zur Entkopplung der Domänenlogik von der Datenpersistenz.

Implementiert das Dependency-Inversion-Prinzip über die abstrakte Basisklasse
'ModulRepository' und stellt mit 'JsonModulRepository' eine konkrete Speicherung
in einer lokalen JSON-Datei (Datumsformat TT.MM.JJJJ) bereit.
Zudem werden beim ersten Programmstart initiale Beispieldaten erzeugt, um die Anwendung
testen zu können.
"""

from abc import ABC, abstractmethod
from datetime import date, datetime
import json
from pathlib import Path
from domain import (
    Abschlussart,
    AnerkannteLeistung,
    Modul,
    Pruefungsleistung,
    RegulaerePruefung,
    Semester,
    Studiengang,
)

DATUMS_FORMAT = "%d.%m.%Y"


class ModulRepository(ABC):
    """Abstrakte Schnittstelle für den Datenzugriff auf Studiengang-Objekte."""

    @abstractmethod
    def lade_studiengang(self) -> Studiengang:
        """Lädt den vollständigen Studiengang aus dem Speichermedium."""
        pass

    @abstractmethod
    def speichere_studiengang(self, sg: Studiengang) -> None:
        """Persistiert den aktuellen Zustand des Studiengangs im Speichermedium."""
        pass


class JsonModulRepository(ModulRepository):
    """Konkrete Repository-Implementierung für die Speicherung in einer JSON-Datei."""

    def __init__(self, dateipfad: Path) -> None:
        """Initialisiert das Repository mit dem Pfad zur JSON-Datei."""
        self.dateipfad = dateipfad

    def lade_studiengang(self) -> Studiengang:
        """Liest den Studiengang aus der JSON-Datei oder legt initiale Beispieldaten an."""
        if not self.dateipfad.exists():
            sg = self._erstelle_beispiel_studiengang()
            self.speichere_studiengang(sg)
            return sg

        raw = json.loads(self.dateipfad.read_text(encoding="utf-8"))
        semester_liste: list[Semester] = []

        for sem_data in raw["semester_liste"]:
            module: list[Modul] = []
            for m_data in sem_data["module"]:
                pruefung = self._deserialisiere_pruefung(
                    m_data.get("pruefungsleistung")
                )
                module.append(
                    Modul(
                        code=m_data["code"],
                        titel=m_data["titel"],
                        ects=m_data["ects"],
                        start_datum=self._parse_datum(
                            m_data.get("start_datum")
                        ),
                        end_datum=self._parse_datum(m_data.get("end_datum")),
                        pruefungsleistung=pruefung,
                    )
                )
            semester_liste.append(
                Semester(
                    nummer=sem_data["nummer"],
                    ziel_ects=sem_data["ziel_ects"],
                    module=module,
                )
            )

        return Studiengang(
            name=raw["name"],
            abschluss=Abschlussart[raw["abschluss"]],
            regelstudienzeit_monate=raw["regelstudienzeit_monate"],
            gesamt_ects=raw["gesamt_ects"],
            semester_liste=semester_liste,
        )

    def speichere_studiengang(self, sg: Studiengang) -> None:
        """Serialisiert die Domänenobjekte mit deutschem Datumsformat (TT.MM.JJJJ) in JSON."""
        daten = {
            "name": sg.name,
            "abschluss": sg.abschluss.name,
            "regelstudienzeit_monate": sg.regelstudienzeit_monate,
            "gesamt_ects": sg.gesamt_ects,
            "semester_liste": [
                {
                    "nummer": s.nummer,
                    "ziel_ects": s.ziel_ects,
                    "module": [
                        {
                            "code": m.code,
                            "titel": m.titel,
                            "ects": m.ects,
                            "start_datum": m.start_datum.strftime(DATUMS_FORMAT)
                            if m.start_datum
                            else None,
                            "end_datum": m.end_datum.strftime(DATUMS_FORMAT)
                            if m.end_datum
                            else None,
                            "pruefungsleistung": self._serialisiere_pruefung(
                                m.pruefungsleistung
                            ),
                        }
                        for m in s.module
                    ],
                }
                for s in sg.semester_liste
            ],
        }
        self.dateipfad.write_text(
            json.dumps(daten, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    @staticmethod
    def _parse_datum(wert: str | None) -> date | None:
        """Liest einen Datumsstring im Format TT.MM.JJJJ ein."""
        if not wert:
            return None
        try:
            return datetime.strptime(wert, DATUMS_FORMAT).date()
        except ValueError:
            # Fallback, falls noch eine ältere JSON-Datei im ISO-Format existiert
            return date.fromisoformat(wert)

    @staticmethod
    def _serialisiere_pruefung(p: Pruefungsleistung | None) -> dict | None:
        """Wandelt ein Pruefungsleistung-Objekt anhand seines Typs in ein Dictionary um."""
        if isinstance(p, RegulaerePruefung):
            return {"typ": "regulaer", "titel": p.titel, "note": p.note}
        if isinstance(p, AnerkannteLeistung):
            return {
                "typ": "anerkannt",
                "titel": p.titel,
                "anerkennungsdatum": p.anerkennungsdatum.strftime(
                    DATUMS_FORMAT
                ),
            }
        return None

    @classmethod
    def _deserialisiere_pruefung(
        cls, data: dict | None
    ) -> Pruefungsleistung | None:
        """Rekonstruiert die passende Pruefungsleistung-Unterklasse aus einem JSON-Dictionary."""
        if not data:
            return None
        if data["typ"] == "regulaer":
            return RegulaerePruefung(
                titel=data["titel"], note=float(data["note"])
            )
        if data["typ"] == "anerkannt":
            datum = cls._parse_datum(data["anerkennungsdatum"]) or date.today()
            return AnerkannteLeistung(
                titel=data["titel"],
                anerkennungsdatum=datum,
            )
        return None

    @staticmethod
    def _erstelle_beispiel_studiengang() -> Studiengang:
        """Erzeugt einen realistischen Initialbestand für den ersten Programmstart.
        Füge hier weitere Semester und Module hinzu, um die Anwendung zu testen. 
        Dabei reicht es aus, wie im 2. Semester nur die Pflichtmodule zu definieren, ohne Start- und Enddatum oder Prüfungsleistung. 
        Den Rest der Daten kann man dann in der GUI eintragen."""
        s1 = Semester(
            nummer=1,
            module=[
                Modul(
                    "DLBISIC01",
                    "Einführung in Datenschutz und Informationssicherheit",
                    5,
                    date(2026, 3, 1),
                    date(2026, 4, 12),
                    RegulaerePruefung("Klausur", 1.7),
                ),
                Modul(
                    "DLBWIRITT01",
                    "Einführung in das wissenschaftliche Arbeiten",
                    5,
                    pruefungsleistung=AnerkannteLeistung(
                        "Anerkennung", date(2026, 3, 1)
                    ),
                ),
                Modul(
                    "DLBDSIPWP01_D",
                    "Einführung in die Programmierung mit Python",
                    5,
                    date(2026, 4, 15),
                    date(2026, 6, 10),
                    RegulaerePruefung("Klausur", 2.0),
                ),
            ],
        )
        s2 = Semester(
            nummer=2,
            module=[
                Modul(
                    "DLBDSOOFPP01_D",
                    "Objektorientierte und funktionale Programmierung mit Python",
                    5,
                    date(2026, 9, 1),
                ),
                Modul("DLBCSEINF01_D", "Einführung in die Netzwerkforensik", 5),
                Modul("IREN01", "Requirements Engineering", 5),
            ],
        )
        return Studiengang(
            name="Cyber Security",
            abschluss=Abschlussart.BACHELOR_OF_SCIENCE,
            regelstudienzeit_monate=48,
            gesamt_ects=180,
            semester_liste=[s1, s2],
        )