

int sensorPin = A2;   // select the input pin for the battery sensor
int r1 = 560;         // resistance of the first resistor
int r2 = 1500;       // resistance of the second resistor
float voltage = 0;   // variable to store the value read

void setup() {
    Serial.begin(115200);
}

void loop() {
    // read the value from the sensor:
    voltage = analogRead(sensorPin);
    voltage = voltage * (5.0 / 1023.0)*((r1+r2)/r1);
    // print the value to the serial port:
    Serial.print("NiMh battery voltage: ");
    Serial.println(voltage);
}
