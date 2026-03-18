Here is a complete, detailed Markdown file compiling **all the information** from our conversation about using the **MQ-135** sensor with an **Arduino UNO R4** to calculate CO₂ ppm — including your specific hardware measurements (RL = 1 kΩ), warnings, formulas, calibration steps, code examples, and recommendations.

You can copy the entire content below and save it as `MQ-135_CO2_Arduino_R4_Guide.md` (or any name you like).

```markdown
# MQ-135 CO₂ Measurement with Arduino UNO R4 – Complete Guide

**Current date reference**: March 18, 2026
**Sensor module**: Generic MQ-135 breakout board
**Measured resistances**:
- Between **A0** (analog output) and **GND**: **1 kΩ** → this is the **load resistor (RL)**
- Between **D0** (digital output) and **GND**: **10 kΩ** → pull-down for comparator (ignore for analog CO₂ calculation)

**Microcontroller**: Arduino UNO R4 (WiFi or Minima variant) – 5 V logic, supports up to 14-bit ADC resolution

**Important disclaimer**
The MQ-135 is **not** a reliable or accurate CO₂ sensor. It is a broad-spectrum metal-oxide gas sensor with strong cross-sensitivity to alcohol, ammonia, benzene, CO, smoke, perfumes, cleaning agents, etc. CO₂ readings are **approximate at best** and often deviate by hundreds or thousands of ppm from true values. For serious CO₂ monitoring (e.g. indoor air quality, ventilation control), use **NDIR** sensors such as:

- SCD40 / SCD41 (Sensirion)
- MH-Z19E
- SenseAir S8

Use MQ-135 mainly for **relative air quality trends** (e.g. "air is getting worse/better").

## 1. Hardware Overview & Wiring

### Typical MQ-135 Breakout Pinout
- **VCC** → Arduino 5V
- **GND** → Arduino GND
- **AOUT** (analog) → Arduino analog pin, e.g. A0
- **D0** (digital) → optional; threshold-based output (not used for PPM calculation)

### Load Resistor (RL) Issue
- Datasheet recommendation: **10–47 kΩ** (ideally ~20 kΩ)
- Your module: **1 kΩ** (SMD marked "102")
- Consequences of 1 kΩ RL:
  - Low output voltage in clean air (0.1–0.5 V → small ADC range)
  - Noisy Rs calculation
  - PPM estimates deviate from standard curve fits

**Recommended fix** (best accuracy):
Replace the 1 kΩ SMD resistor with **10 kΩ**, **20 kΩ**, or **22 kΩ** (0805/0603 size).
After replacement → re-measure resistance between A0 and GND = new RL value.

**Alternative**: Keep 1 kΩ and compensate in code (less accurate absolute PPM).

### Preheat Requirement
- Power the sensor continuously with **5 V** for **24–48 hours** (or up to 72 h for first use) before calibration or measurement.
- Heater resistance ~30–35 Ω → current ~150–170 mA at 5 V.

## 2. ADC on Arduino UNO R4

- Default: **10-bit** → 0–1023 (ADC_MAX = 1023)
- Recommended: **12-bit** → 0–4095 (ADC_MAX = 4095)
  → Add in `setup()`: `analogReadResolution(12);`
- Optional: **14-bit** → 0–16383 (even better granularity)

Reference voltage ≈ 5 V (same as VCC), so voltage formulas hold.

## 3. Core Formulas

### Step 1: Calculate Sensor Resistance Rs

Voltage divider:
Vout = VCC × RL / (Rs + RL)
→ Rs = RL × (VCC – Vout) / Vout

With ADC:
adc_value = (Vout / VCC) × ADC_MAX
→ Vout = adc_value × VCC / ADC_MAX

Assuming VCC ≈ Vref ≈ 5 V:
**Rs = RL × (ADC_MAX – adc_value) / adc_value**

Your case (RL = 1 kΩ = 1000 Ω):
Rs = 1000 × (ADC_MAX – adc_value) / adc_value    (result in Ω)

### Step 2: Calibration – Find R0 (clean air resistance)

In clean outdoor air (~400–430 ppm CO₂ in 2026):
Rs_air ≈ measured average Rs after preheat

From typical MQ-135 CO₂ curve:
Rs / R0 ≈ 3.6–3.8 in clean air (20 °C, 50% RH)
→ **R0 = Rs_air / 3.6** (or use library calibration function)

### Step 3: Ratio and PPM Calculation

ratio = Rs / R0

Common power-law fit for CO₂ (from popular libraries / curve digitization):
**PPM = 116.602 × ratio^(-2.769)**

Other close variants:
- PPM ≈ 110.47 × ratio^(-2.862)
- a = 120, b = -2.3 to -2.8 (approximate)

**Temperature & humidity correction** (strongly recommended):
Use DHT22/AM2302 or BME280 + library correction function.

## 4. Recommended Software Approach

Use **MQ135 library by GeorgK** (Arduino Library Manager → search "MQ135")

### Library Adjustments for Your Module

Edit `MQ135.h` or define in sketch:

```cpp
#define RLOAD 1.0          // your measured RL in kΩ
// After calibration:
// #define RZERO your_calibrated_value_here
```

### Step 1: Calibrate RZERO (clean air – outdoors)

```cpp
#include <MQ135.h>
#define PIN_MQ135 A0

void setup() {
  Serial.begin(9600);
  analogReadResolution(12);           // better precision on R4
  Serial.println("MQ-135 RZERO calibration – keep in clean outdoor air");
}

void loop() {
  MQ135 gasSensor = MQ135(PIN_MQ135);
  float rzero = gasSensor.getRZero(); // internal averaging
  Serial.print("RZERO = ");
  Serial.println(rzero, 3);
  delay(5000);
}
```

- Run for 5–10 minutes, average stable readings (ignore first 30–60 s).
- Typical range with RL = 1 kΩ: **20–120** (varies by sensor)
- Note the average → hard-code as RZERO or use `getCorrectedRZero(temp, hum)` if you have a temp/RH sensor.

### Step 2: Normal Measurement Code

```cpp
#include <MQ135.h>
#define PIN_MQ135 A0

MQ135 gasSensor = MQ135(PIN_MQ135);  // can be global

void setup() {
  Serial.begin(9600);
  analogReadResolution(12);
  Serial.println("MQ-135 CO2 monitor started");
}

void loop() {
  float ppm = gasSensor.getPPM();                    // basic estimate
  // float corrected = gasSensor.getCorrectedPPM(23.5, 48.0);  // temp °C, RH %

  Serial.print("Raw Rs   = "); Serial.print(gasSensor.getResistance()); Serial.println(" Ω");
  Serial.print("Ratio    = "); Serial.println(gasSensor.getRatio());
  Serial.print("CO₂ PPM  = "); Serial.println(ppm);
  // Serial.print("Corrected CO₂ = "); Serial.println(corrected);

  delay(2000);
}
```

**Expected values** (very rough – depends on your sensor & environment):
- Outdoors 2026: **400–480 ppm**
- Well-ventilated room: **500–800 ppm**
- Occupied office/classroom: **800–1800 ppm**
- Crowded room: **2000+ ppm** (but cross-sensitivity may inflate this)

## 5. Troubleshooting & Tips

- Readings jump wildly? → Other gases present (alcohol, cleaning spray, etc.)
- Always <400 ppm? → Bad calibration / wrong RZERO / sensor poisoned
- Always >3000 ppm? → Cross-sensitivity or very low RL causing saturation
- Add temperature + humidity correction → huge improvement
- Log data to Serial Plotter or SD card for trends

## 6. Final Recommendations

| Goal                          | Recommended Sensor       | Why Better than MQ-135          |
|-------------------------------|---------------------------|----------------------------------|
| Rough relative air quality    | MQ-135 (your setup)       | Cheap, already owned             |
| Reliable indoor CO₂           | SCD41, MH-Z19E, SenseAir S8 | True NDIR, ±(30–50) ppm accuracy |
| Scientific / HVAC control     | SCD41 + temp/RH           | Low drift, long-term stable      |

Good luck with your project!

If you replace the RL resistor or get your RZERO value, share it → I can help fine-tune constants or curve parameters.
```

Copy everything between the ```markdown:disable-run

Let me know if you'd like any section expanded, shortened, or if you want to add photos/schematics references later!
```
