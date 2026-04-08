import csv
import time
from datetime import datetime

import serial

SERIAL_PORT = "COM3"
BAUD_RATE = 9600
FILE_NAME = "co2_messungen.csv"
MEASURE_INTERVAL = 2  # Sekunden zwischen Messungen

ADC_MAX = 1023.0  # 10-bit ADC Arduino

RL = 1000.0  # Lastwiderstand

FRESH_AIR_PPM = 420.0
CALIBRATION_FILE = "calibration.txt"
AUTO_KALIBRIERUNG = False
CALIBRATION_LENGTH = 120

# Konstanten
A = 116.6020682
B = -2.769034857306923

# Fallback-Wert
R0_FALLBACK = 1000.0


def load_r0_from_file():
    try:
        with open(CALIBRATION_FILE, "r", encoding="utf-8") as f:
            r0 = float(f.readline().strip())
        if r0 > 0:
            print(f"Gespeichertes R0 aus {CALIBRATION_FILE} geladen: {r0:.2f} Ohm")
            return r0
    except (FileNotFoundError, ValueError):
        pass
    return None


def calculate_rs_from_adc(adc_value):
    if adc_value <= 5 or adc_value >= ADC_MAX:
        return None

    return (RL * (ADC_MAX / adc_value - 1.0)) / 2.5
    # return RL * (ADC_MAX / adc_value - 1.0)


def calculate_r0_from_rs(rs, reference_ppm=FRESH_AIR_PPM):
    if rs is None or rs <= 0:
        return None

    return rs * (A / reference_ppm) ** (-1.0 / B)


def calibrate_r0(ser):
    print(
        f"R0-Kalibrierung gestartet: {CALIBRATION_LENGTH} Sekunden in Frischluft (~{int(FRESH_AIR_PPM)} ppm)"
    )

    samples = []
    start_time = time.time()

    while time.time() - start_time < CALIBRATION_LENGTH:
        if ser.in_waiting > 0:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if line.isdigit():
                adc_val = int(line)
                if 5 < adc_val < ADC_MAX:
                    samples.append(adc_val)

        time.sleep(0.05)

    if not samples:
        raise RuntimeError(
            "Keine gültigen ADC-Werte während der Kalibrierung erhalten."
        )

    adc_avg = sum(samples) / len(samples)
    rs_avg = calculate_rs_from_adc(adc_avg)
    r0_new = calculate_r0_from_rs(rs_avg)

    if r0_new is None or r0_new <= 0:
        raise RuntimeError("R0 konnte nicht berechnet werden.")

    print(f"ADC Mittelwert : {adc_avg:.1f}")
    print(f"Rs Mittelwert  : {rs_avg:.1f} Ohm")
    print(f"Neuer R0-Wert  : {r0_new:.2f} Ohm  ({len(samples)} Samples)")

    with open(CALIBRATION_FILE, "w", encoding="utf-8") as f:
        f.write(f"{r0_new}\n")

    return r0_new


def adc_to_ppm(adc_value, r0_value):
    try:
        if adc_value <= 5:
            return 0.0

        rs = calculate_rs_from_adc(adc_value)
        if rs is None or r0_value <= 0:
            return 0.0

        ratio = rs / r0_value
        ppm = A * (ratio**B)

        if ppm < 0 or ppm > 25000:
            return 0.0

        return round(ppm, 2)

    except Exception as e:
        print(f"Berechnungsfehler: {e}")
        return 0.0


def main():
    ser = None
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)

        if AUTO_KALIBRIERUNG:
            r0_active = calibrate_r0(ser)
        else:
            r0_active = load_r0_from_file()
            if r0_active is None:
                r0_active = R0_FALLBACK
                print(f"Kein gespeichertes R0 gefunden. Fallback: {r0_active:.2f} Ohm")

        print(
            f"\nR0: {r0_active:.2f} | RL = {RL:.0f} | Intervall = {MEASURE_INTERVAL}s\n"
        )
        print(f"Speichern gestartet\nDatei: {FILE_NAME}")

        with open(FILE_NAME, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            if file.tell() == 0:
                writer.writerow(["Datum", "Uhrzeit", "ADC", "Rs_Ohm", "PPM_CO2"])

            last_measure_time = time.time() - MEASURE_INTERVAL

            while True:
                if ser.in_waiting > 0:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()

                    if not line.isdigit():
                        continue

                    now = time.time()
                    if now - last_measure_time < MEASURE_INTERVAL:
                        continue

                    adc_val = int(line)
                    ppm = adc_to_ppm(adc_val, r0_active)
                    rs_val = calculate_rs_from_adc(adc_val) or 0.0

                    jetzt = datetime.now()
                    datum = jetzt.strftime("%Y-%m-%d")
                    uhrzeit = jetzt.strftime("%H:%M:%S")

                    writer.writerow([datum, uhrzeit, adc_val, round(rs_val, 1), ppm])
                    file.flush()

                    print(
                        f"{uhrzeit} | ADC: {adc_val:4d} | Rs: {rs_val:6.1f} | {ppm:6.1f} ppm"
                    )

                    last_measure_time = now

    except serial.SerialException:
        print("Fehler: Serieller Port nicht gefunden oder bereits belegt.")
    except KeyboardInterrupt:
        print("\n\nMessung durch Benutzer beendet.")
    except Exception as e:
        print(f"Unerwarteter Fehler: {e}")
    finally:
        if ser is not None and ser.is_open:
            ser.close()
        print("Programm beendet.")


if __name__ == "__main__":
    main()
