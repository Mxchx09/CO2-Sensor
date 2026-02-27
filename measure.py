import serial
import csv
import time
from datetime import datetime

SERIAL_PORT = "COM3"
BAUD_RATE = 9600
DATEI_NAME = "Aufheizdaten.csv"
INTERVALL = 10  # Intervall in Sekunden


def start_logging():
    try:
        # verbindung zu serial port herstellen
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        print(
            f"Verbindung hergestellt mit {SERIAL_PORT}. Speichere Daten in {DATEI_NAME}..."
        )

        with open(DATEI_NAME, mode="a", newline="") as file:
            writer = csv.writer(file)

            if file.tell() == 0:
                writer.writerow(["Datum", "Uhrzeit", "ADC_Wert"])

            letzte_messung = 0

            while True:
                if ser.in_waiting > 0:
                    # Daten von Port lesen und säubern
                    line = ser.readline().decode("utf-8").strip()
                    aktueller_zeitpunkt = time.time()

                    if aktueller_zeitpunkt - letzte_messung >= INTERVALL:
                        jetzt = datetime.now()
                        if line:
                            # Aktuelles Datum und Uhrzeit holen
                            jetzt = datetime.now()
                            datum = jetzt.strftime("%Y-%m-%d")
                            uhrzeit = jetzt.strftime("%H:%M:%S")

                            # CSV header schreiben
                            writer.writerow([datum, uhrzeit, line])
                            file.flush()  # Sofort speichern falls absturz

                            print(f"Saved: {datum} {uhrzeit} | {line} ppm")
                            letzte_messung = aktueller_zeitpunkt

    except serial.SerialException:
        print("Error: Keine Verbindung zu Serial Port möglich!")
    except KeyboardInterrupt:
        print("\nLogging durch Benutzer beendet")
    finally:
        if "ser" in locals():
            ser.close()  #  Serial port schließen


if __name__ == "__main__":
    start_logging()
