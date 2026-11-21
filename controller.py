"""Controller-Schicht zur Steuerung der Anwendungslogik und Datenaufbereitung.

Verbindet die Persistenzschicht (Repository) und die Berechnungslogik (Service)
mit der grafischen Benutzeroberfläche (View), ohne dass die View direkt auf
Domänenobjekte zugreifen muss.
"""

from datetime import date
from domain import (
    AnerkannteLeistung,
    Modul,
    ModulStatus,
    RegulaerePruefung,
)
from dto import DashboardDatenDTO, ModulTabellenEintragDTO
from repository import ModulRepository
from services import KennzahlenService


class DashboardController:
    """Koordiniert das Laden, Filtern und Aktualisieren der Studiengangsdaten."""

    def __init__(
        self, repository: ModulRepository, service: KennzahlenService
    ) -> None:
        """Initialisiert den Controller mit Repository- und Service-Abhängigkeiten."""
        self.repository = repository
        self.service = service

    def lade_dashboard_daten(
        self,
        semester_filter: int | None = None,
        status_filter: str | None = None,
    ) -> DashboardDatenDTO:
        """Lädt den Studiengang, berechnet alle Kennzahlen und erstellt das DTO für die View."""
        sg = self.repository.lade_studiengang()
        alle_module = sg.alle_module

        in_bearbeitung_ects = sum(
            m.ects
            for m in alle_module
            if m.status == ModulStatus.IN_BEARBEITUNG
        )
        offene_ects = sum(
            m.ects for m in alle_module if m.status == ModulStatus.OFFEN
        )

        status_anzahl = {status.value: 0 for status in ModulStatus}
        for m in alle_module:
            status_anzahl[m.status.value] += 1

        noten_trend = self.service.berechne_noten_trend(alle_module)
        dauer_trend = self.service.berechne_dauer_trend(alle_module)

        eintraege: list[ModulTabellenEintragDTO] = []
        for sem in sg.semester_liste:
            if semester_filter is not None and sem.nummer != semester_filter:
                continue
            for m in sem.module:
                if status_filter and m.status.value != status_filter:
                    continue
                eintraege.append(self._erstelle_tabellen_eintrag(sem.nummer, m))

        semester_nummern = [s.nummer for s in sg.semester_liste]
        studiengang_titel = f"{sg.abschluss.value} {sg.name} ({sg.regelstudienzeit_monate} Monate)"

        return DashboardDatenDTO(
            studiengang_titel=studiengang_titel,
            gesamt_ects=sg.gesamt_ects,
            erreichte_ects=sg.erreichte_ects,
            in_bearbeitung_ects=in_bearbeitung_ects,
            offene_ects=offene_ects,
            status_anzahl=status_anzahl,
            gesamtnote=sg.gesamtnote,
            noten_trend=noten_trend,
            durchschnitts_dauer=sg.durchschnittliche_bearbeitungszeit,
            dauer_trend=dauer_trend,
            semester_nummern=semester_nummern,
            modul_eintraege=eintraege,
        )

    def speichere_modul_update(
        self,
        code: str,
        start_datum: date | None,
        end_datum: date | None,
        note: float | None,
        anerkannt: bool,
    ) -> None:
        """Aktualisiert die Bearbeitungs- und Prüfungsdaten eines Moduls und speichert sie."""
        if start_datum and end_datum and end_datum < start_datum:
            raise ValueError(
                "Das Enddatum darf nicht vor dem Startdatum liegen."
            )

        sg = self.repository.lade_studiengang()
        ziel_modul = next((m for m in sg.alle_module if m.code == code), None)
        if ziel_modul is None:
            raise ValueError(f"Modul mit Code '{code}' wurde nicht gefunden.")

        ziel_modul.start_datum = start_datum
        ziel_modul.end_datum = end_datum

        if anerkannt:
            anerkennungs_tag = end_datum or start_datum or date.today()
            ziel_modul.pruefungsleistung = AnerkannteLeistung(
                titel="Anerkennung", anerkennungsdatum=anerkennungs_tag
            )
        elif note is not None:
            ziel_modul.pruefungsleistung = RegulaerePruefung(
                titel="Prüfung", note=note
            )
        else:
            ziel_modul.pruefungsleistung = None

        self.repository.speichere_studiengang(sg)

    @staticmethod
    def _erstelle_tabellen_eintrag(
        semester_nr: int, modul: Modul
    ) -> ModulTabellenEintragDTO:
        """Formatiert ein Domänen-Modul in ein Tabellen-DTO mit deutschem Datumsformat (TT.MM.JJJJ)."""
        if isinstance(modul.pruefungsleistung, RegulaerePruefung):
            note_text = f"{modul.pruefungsleistung.note:.1f}"
        elif isinstance(modul.pruefungsleistung, AnerkannteLeistung):
            note_text = "Anerkannt"
        else:
            note_text = "-"

        return ModulTabellenEintragDTO(
            semester=semester_nr,
            code=modul.code,
            titel=modul.titel,
            ects=modul.ects,
            status=modul.status.value,
            start_datum=modul.start_datum.strftime("%d.%m.%Y")
            if modul.start_datum
            else "-",
            end_datum=modul.end_datum.strftime("%d.%m.%Y")
            if modul.end_datum
            else "-",
            dauer_wochen=f"{modul.dauer_wochen:.1f}"
            if modul.dauer_wochen is not None
            else "-",
            note_oder_anerkannt=note_text,
        )