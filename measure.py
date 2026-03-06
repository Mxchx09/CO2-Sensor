import serial
import csv
import time
from datetime import datetime

SERIAL_PORT = "COM3"
BAUD_RATE = 9600
DATEI_NAME = "Aufheizdaten.csv"
INTERVALL = 2  # Sekunden

ADC_MAX = 1023.0  # sketch_old.ino nutzt default 10-bit ADC
RL = 10000.0  # Lastwiderstand in Ohm
R0 = 150.0  # Fallback-Wert, kann per Kalibrierung ersetzt werden
A = 116.6020682
B = -2.769034857306923
FRESH_AIR_PPM = 420.0

AUTO_KALIBRIERUNG = True
KALIBRIER_DAUER_SEKUNDEN = 60


def calculate_rs_from_adc(adc_value):
    if adc_value <= 5 or adc_value >= ADC_MAX:
        return None

    return RL * (ADC_MAX - adc_value) / adc_value


def calculate_r0_from_adc(adc_value, reference_ppm=FRESH_AIR_PPM):
    rs = calculate_rs_from_adc(adc_value)
    if rs is None:
        return None

    ratio = (reference_ppm / A) ** (1.0 / B)
    if ratio <= 0:
        return None

    return rs / ratio


def kalibriere_r0(ser, dauer_sekunden=KALIBRIER_DAUER_SEKUNDEN):
    print(
        f"R0-Kalibrierung läuft {dauer_sekunden}s in Frischluft (~{int(FRESH_AIR_PPM)} ppm)..."
    )

    samples = []
    start = time.time()

    while time.time() - start < dauer_sekunden:
        if ser.in_waiting > 0:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if line.isdigit():
                adc_val = int(line)
                if 5 < adc_val < ADC_MAX:
                    samples.append(adc_val)

        time.sleep(0.05)

    if not samples:
        raise RuntimeError("Keine gültigen ADC-Samples für R0-Kalibrierung erhalten.")

    adc_mittel = sum(samples) / len(samples)
    r0_neu = calculate_r0_from_adc(adc_mittel)

    if r0_neu is None or r0_neu <= 0:
        raise RuntimeError("R0 konnte aus den Samples nicht berechnet werden.")

    print(
        f"Kalibrierung abgeschlossen: ADC-Mittel={adc_mittel:.2f}, R0={r0_neu:.2f} Ohm ({len(samples)} Samples)"
    )
    return r0_neu


def adc_to_ppm(adc_value, r0_value):
    try:
        # Schutz gegen kaputte oder extrem kleine Werte
        if adc_value <= 5:
            return 0

        rs = calculate_rs_from_adc(adc_value)
        if rs is None or r0_value <= 0:
            return 0

        ppm = A * ((rs / r0_value) ** B)

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

        r0_aktiv = R0
        if AUTO_KALIBRIERUNG:
            r0_aktiv = kalibriere_r0(ser)

        print(f"Aktives R0: {r0_aktiv:.2f} Ohm")

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
                    ppm = adc_to_ppm(adc_val, r0_aktiv)

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
