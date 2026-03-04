import serial
import csv
import time
from datetime import datetime

SERIAL_PORT = "COM3"
BAUD_RATE = 9600
DATEI_NAME = "Aufheizdaten.csv"
INTERVALL = 10  # Sekunden


def adc_to_ppm(adc_value):
    try:
        # Schutz gegen kaputte oder extrem kleine Werte
        if adc_value <= 5:
            return 0

        RL = 10.0  # Lastwiderstand in Ohm
        R0 = 150.0  # Sensor-Widerstand bei 400ppm nach Kalibrierung in Ohm
        A = 116.6020682  # Konstante
        B = -2.7690348573069232096715545  # Konstante

        rs = RL * (1023 - adc_value) / adc_value
        ppm = A * ((rs / R0) ** B)

        # Plausibilitäts-Clamp
        if ppm < 0 or ppm > 25000:
            return 0

        return round(ppm, 2)

    except Exception as e:
        print(f"Fehler in der Berechnung: {e}")
        return 0


def start_logging():
    ser = None
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)

        print(f"Logging gestartet - speichere in {DATEI_NAME}")

        with open(DATEI_NAME, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            # Header nur schreiben, wenn Datei neu/leer ist
            if file.tell() == 0:
                writer.writerow(["Datum", "Uhrzeit", "ADC_Wert", "PPM"])

            letzte_messung = time.time() - INTERVALL

            while True:
                if ser.in_waiting > 0:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()

                    # Nur echte Zahlen akzeptieren
                    if not line.isdigit():
                        continue

                    aktueller_zeitpunkt = time.time()
                    if aktueller_zeitpunkt - letzte_messung < INTERVALL:
                        continue

                    adc_val = int(line)
                    ppm = adc_to_ppm(adc_val)

                    jetzt = datetime.now()
                    datum = jetzt.strftime("%Y-%m-%d")
                    uhrzeit = jetzt.strftime("%H:%M:%S")

                    writer.writerow([datum, uhrzeit, adc_val, ppm])
                    file.flush()

                    print(f"{uhrzeit} | ADC: {adc_val} | {ppm} ppm")
                    letzte_messung = aktueller_zeitpunkt

    except serial.SerialException:
        print("Error: Port nicht gefunden oder belegt.")
    except KeyboardInterrupt:
        print("\nBeendet durch Benutzer.")
    finally:
        if ser is not None and ser.is_open:
            ser.close()


if __name__ == "__main__":
    start_logging()
