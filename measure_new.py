import csv
import time
from datetime import datetime

import serial

SERIAL_PORT = "COM3"
BAUD_RATE = 9600
FILE_NAME = "tmp.csv"
MEASURE_INTERVALL = 2  # Sekunden

ADC_MAX = 1023.0  # sketch_old.ino nutzt default 10-bit ADC
"""
RL = 10000.0  # Lastwiderstand in Ohm
R0 = 150.0  # Fallback-Wert, kann per Kalibrierung ersetzt werden
A = 116.6020682
B = -2.769034857306923
"""
# Constants
A = 116.6020682
B = -2.769034857306923

# Fallback
R0 = 1000

RL = 1000  # R zw. GND u. A0 [OHM]
FRESH_AIR_PPM = 420.0
CALIBRATION_FILE = "calibration.txt"

AUTO_KALIBRIERUNG = True
CALIBRATION_LENGTH = 60


def load_r0_from_file(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            reading: str = f.readline().strip()

        r0 = float(reading)

        if r0 <= 0:
            return None

        return r0
    except (FileNotFoundError, ValueError):
        return None


def calculate_rs_from_adc(adc_value):
    if adc_value <= 5 or adc_value >= ADC_MAX:
        return None

    return RL * (ADC_MAX - adc_value) / adc_value


def calculate_r0_from_adc(adc_value, reference_ppm=FRESH_AIR_PPM):
    rs = calculate_rs_from_adc(adc_value=adc_value)

    if rs is None:
        return None

    ratio = (reference_ppm / A) ** (1.0 / B)

    if ratio <= 0:
        return None

    return rs / ratio


def calibrate_r0(ser, len_sec=CALIBRATION_LENGTH):
    print(f"R0-Kalibrierung: {len_sec}s in Frischluft (~{int(FRESH_AIR_PPM)} ppm)...")

    samples = []
    start = time.time()

    while time.time() - start < len_sec:
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
    r0_new = calculate_r0_from_adc(adc_mittel)

    if r0_new is None or r0_new <= 0:
        raise RuntimeError("R0 konnte aus den Samples nicht berechnet werden.")

    print(
        f"Kalibrierung abgeschlossen: ADC-Mittel={adc_mittel:.2f}, R0={r0_new:.2f} Ohm ({len(samples)} Samples)"
    )
    with open(CALIBRATION_FILE, "w", encoding="utf-8") as f:
        f.write(f"{r0_new}\n")

    return r0_new


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


def main():
    ser = None
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)

        r0_active = R0
        if AUTO_KALIBRIERUNG:
            r0_active = calibrate_r0(ser)
        else:
            r0_gespeichert = load_r0_from_file()
            if r0_gespeichert is not None:
                r0_active = r0_gespeichert
                print(f"Gespeichertes R0 aus {CALIBRATION_FILE} geladen.")
            else:
                print(
                    f"Kein gueltiges R0 in {CALIBRATION_FILE} gefunden - nutze Fallback R0={R0:.2f} Ohm."
                )

        print(f"Aktives R0: {r0_active:.2f} Ohm")

        print(f"Logging gestartet - speichere in {FILE_NAME}")

        with open(FILE_NAME, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            # Header nur schreiben, wenn Datei neu/leer ist
            if file.tell() == 0:
                writer.writerow(["Datum", "Uhrzeit", "ADC_Wert", "PPM"])

            last_measured_val = time.time() - MEASURE_INTERVALL

            while True:
                if ser.in_waiting > 0:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()

                    # Nur echte Zahlen akzeptieren
                    if not line.isdigit():
                        continue

                    aktueller_zeitpunkt = time.time()
                    if aktueller_zeitpunkt - last_measured_val < MEASURE_INTERVALL:
                        continue

                    adc_val = int(line)
                    ppm = adc_to_ppm(adc_val, r0_active)

                    jetzt = datetime.now()
                    datum = jetzt.strftime("%Y-%m-%d")
                    uhrzeit = jetzt.strftime("%H:%M:%S")

                    writer.writerow([datum, uhrzeit, adc_val, ppm])
                    file.flush()

                    print(f"{uhrzeit} | ADC: {adc_val} | {ppm} ppm")
                    last_measured_val = aktueller_zeitpunkt

    except serial.SerialException:
        print("Error: Port nicht gefunden oder belegt.")
    except KeyboardInterrupt:
        print("\nBeendet durch Benutzer.")
    finally:
        if ser is not None and ser.is_open:
            ser.close()


if __name__ == "__main__":
    main()
