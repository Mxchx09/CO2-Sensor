
int apin = 34; // Analog Pin für Poti
int val;
int mval;

void setup()
{
    Serial.begin(9600);
}

void loop()
{
    val = analogRead(apin);
    mval = map(val, 0, 4095, 0, 1024);
    Serial.println(mval);
}