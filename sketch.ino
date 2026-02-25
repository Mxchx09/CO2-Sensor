int ppin = 21; // Piezo pin
int apin = 34; // Analog pin for Poty
int val;

void setup()
{
    Serial.begin(9600);
    pinMode(21, OUTPUT);
}

void loop()
{

    val = analogRead(apin);

    tone(21, val);

    Serial.println(val);
}
