import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

DATEI_NAME =  "co2_messungen.csv"


def plot_all_data():
    try:
        # 1. Daten laden
        df = pd.read_csv(DATEI_NAME)

        # 2. Datum und Uhrzeit zu einem echten Zeit-Objekt zusammenführen
        df["Zeitstempel"] = pd.to_datetime(df["Datum"] + " " + df["Uhrzeit"])

        # CO2-Werte in Zahlen umwandeln (falls nötig)
        df["PPM_CO2"] = pd.to_numeric(df["PPM_CO2"], errors="coerce")

        # 3. Sortieren nach Zeitstempel
        df = df.sort_values("Zeitstempel")

        # 4. Diagramm erstellen
        plt.figure(figsize=(14, 7))

        # Linie mit allen Datenpunkten zeichnen
        plt.plot(
            df["Zeitstempel"],
            df["PPM_CO2"],
            label="CO2 Gehalt (ppm)",
            color="teal",
            linewidth=1.5,
            marker="o",
            markersize=4,
            alpha=0.8,
        )

        # Formatierung der X-Achse (Zeit)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%d.%m. %H:%M"))
        plt.gcf().autofmt_xdate()  # Schräge Beschriftung

        # Diagramm-Details
        plt.title("CO2-Verlauf")
        plt.xlabel("Zeitpunkt")
        plt.ylabel("CO2 Konzentration (ppm)")
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.legend()
        plt.tight_layout()

        # Optional: Speichern statt nur Anzeigen
        # plt.savefig("CO2_alle_messungen.png")

        plt.show()

    except FileNotFoundError:
        print(f"Fehler: Die Datei {DATEI_NAME} wurde noch nicht erstellt.")
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")


if __name__ == "__main__":
    plot_all_data()
