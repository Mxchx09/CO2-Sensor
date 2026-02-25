int apin = 34;
int val;

void setup()
{
    Serial.begin(9600);
}

void loop()
{
    val = analogRead(apin);
    Serial.println(val);
}
