import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

DATEI_NAME = "co2_messdaten.csv"

def plot_weekly_data():
    try:
        # 1. Daten laden
        df = pd.read_csv(DATEI_NAME)
        
        # 2. Datum und Uhrzeit zu einem echten Zeit-Objekt zusammenführen
        df['Zeitstempel'] = pd.to_datetime(df['Datum'] + ' ' + df['Uhrzeit'])
        
        # CO2-Werte in Zahlen umwandeln (falls nötig)
        df['CO2_Wert_ppm'] = pd.to_numeric(df['CO2_Wert_ppm'], errors='coerce')
        
        # 3. Kalenderwoche und Jahr extrahieren
        df['Woche'] = df['Zeitstempel'].dt.isocalendar().week
        df['Jahr'] = df['Zeitstempel'].dt.year
        
        # 4. Über jede Woche iterieren und ein Diagramm erstellen
        gruppen = df.groupby(['Jahr', 'Woche'])
        
        for (jahr, woche), daten in gruppen:
            plt.figure(figsize=(12, 6))
            
            # Linie zeichnen
            plt.plot(daten['Zeitstempel'], daten['CO2_Wert_ppm'], label=f'CO2 Gehalt (ppm)', color='teal')
            
            # Formatierung der X-Achse (Zeit)
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d.%m. %H:%M'))
            plt.gcf().autofmt_xdate() # Schräge Beschriftung
            
            # Diagramm-Details
            plt.title(f"CO2-Verlauf - KW {woche} ({jahr})")
            plt.xlabel("Zeitpunkt")
            plt.ylabel("CO2 Konzentration (ppm)")
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.legend()
            
            # Optional: Speichern statt nur Anzeigen
            # plt.savefig(f"CO2_KW_{woche}_{jahr}.png")
            
            plt.show()

    except FileNotFoundError:
        print(f"Fehler: Die Datei {DATEI_NAME} wurde noch nicht erstellt.")
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")

if __name__ == "__main__":
    plot_weekly_data()