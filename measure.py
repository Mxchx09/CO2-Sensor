import serial
import csv
import time
from datetime import datetime

# --- KONFIGURATION ---
# Ersetze 'COM3' durch deinen Port (z.B. 'COM4' bei Windows oder '/dev/ttyUSB0' bei Linux/Mac)
SERIAL_PORT = "COM3"
BAUD_RATE = 9600
DATEI_NAME = "co2_messdaten.csv"
INTERVALL = 10  # Intervall in Sekunden (10 Minuten)


def start_logging():
    try:
        # Verbindung zum Arduino herstellen
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Kurz warten, bis der Arduino nach dem Verbinden neu startet
        print(
            f"Verbindung hergestellt mit {SERIAL_PORT}. Logge Daten in {DATEI_NAME}..."
        )

        # Datei öffnen (Modul 'a' steht für Append = Anhängen)
        with open(DATEI_NAME, mode="a", newline="") as file:
            writer = csv.writer(file)

            # Falls die Datei neu ist, Kopfzeile schreiben
            if file.tell() == 0:
                writer.writerow(["Datum", "Uhrzeit", "CO2_Wert_ppm"])

            letzte_messung = 0

            while True:
                if ser.in_waiting > 0:
                    # Daten vom Arduino lesen und säubern
                    line = ser.readline().decode("utf-8").strip()
                    aktueller_zeitpunkt = time.time()

                    if aktueller_zeitpunkt - letzte_messung >= INTERVALL:
                        jetzt = datetime.now()
                        if line:
                            # Aktuelles Datum und Uhrzeit holen
                            jetzt = datetime.now()
                            datum = jetzt.strftime("%Y-%m-%d")
                            uhrzeit = jetzt.strftime("%H:%M:%S")

                            # In Datei schreiben
                            writer.writerow([datum, uhrzeit, line])
                            file.flush()  # Sofort auf Festplatte speichern (wichtig bei Absturz)

                            print(f"Gespeichert: {datum} {uhrzeit} -> {line} ppm")
                            letzte_messung = aktueller_zeitpunkt

    except serial.SerialException:
        print("Fehler: Konnte keine Verbindung zum Arduino finden. Port prüfen!")
    except KeyboardInterrupt:
        print("\nLogging durch Benutzer beendet.")
    finally:
        if "ser" in locals():
            ser.close()


if __name__ == "__main__":
    start_logging()
