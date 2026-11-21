"""Serviceschicht für entitätsübergreifende Kennzahlen- und Trendberechnungen.

Lagert komplexe statistische Auswertungen aus den Domänenklassen aus, um das
Single Responsibility Principle (SRP) zu wahren.
"""

from domain import Modul, ModulStatus


class KennzahlenService:
    """Berechnet die zeitlichen Trendindikatoren für Notenschnitt und Bearbeitungsdauer."""

    def berechne_noten_trend(self, module: list[Modul]) -> float | None:
        """Vergleicht den aktuellen Notenschnitt mit dem Schnitt vor dem letzten Modulabschluss.

        Ein negativer Rückgabewert (z. B. -0.15) bedeutet eine Verbesserung des Schnitts.

        Args:
            module: Liste aller Module des Studiengangs.

        Returns:
            Differenz des gewichteten Notenschnitts oder None bei weniger als 2 benoteten Modulen.
        """
        abgeschlossen = [
            m
            for m in module
            if m.pruefungsleistung
            and m.pruefungsleistung.ist_benotet()
            and m.pruefungsleistung.bestanden
            and m.end_datum is not None
        ]
        # Für einen historischen Trendvergleich werden mindestens zwei Abschlüsse benötigt
        if len(abgeschlossen) < 2:
            return None

        # Chronologische Sortierung anhand des Abschlussdatums
        sortiert = sorted(abgeschlossen, key=lambda m: m.end_datum)  # type: ignore[arg-type]
        vorherige = sortiert[:-1]

        schnitt_vorher = sum(
            m.pruefungsleistung.note * m.ects  # type: ignore[attr-defined]
            for m in vorherige
        ) / sum(m.ects for m in vorherige)
        schnitt_aktuell = sum(
            m.pruefungsleistung.note * m.ects  # type: ignore[attr-defined]
            for m in sortiert
        ) / sum(m.ects for m in sortiert)

        return round(schnitt_aktuell - schnitt_vorher, 2)

    def berechne_dauer_trend(self, module: list[Modul]) -> float | None:
        """Vergleicht die aktuelle Durchschnitts-Bearbeitungsdauer mit dem Wert vor dem letzten Abschluss.

        Ein negativer Rückgabewert (z. B. -0.5) bedeutet eine schnellere Bearbeitung.

        Args:
            module: Liste aller Module des Studiengangs.

        Returns:
            Differenz der mittleren Bearbeitungsdauer in Wochen oder None bei < 2 Modulen.
        """
        abgeschlossen = [
            m
            for m in module
            if m.status == ModulStatus.ABGESCHLOSSEN
            and m.dauer_wochen is not None
            and m.end_datum is not None
        ]
        if len(abgeschlossen) < 2:
            return None

        sortiert = sorted(abgeschlossen, key=lambda m: m.end_datum)  # type: ignore[arg-type]
        vorherige = sortiert[:-1]

        schnitt_vorher = sum(m.dauer_wochen for m in vorherige if m.dauer_wochen) / len(vorherige)
        schnitt_aktuell = sum(m.dauer_wochen for m in sortiert if m.dauer_wochen) / len(sortiert)

        return round(schnitt_aktuell - schnitt_vorher, 1)