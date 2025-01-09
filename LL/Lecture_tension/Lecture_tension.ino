

int sensorPin_Lipo = A2;   // select the input pin for the battery sensor
int sensorPin_NiMh = A3;   // select the input pin for the battery sensor
float r1_LiPo = 560;         // resistance of the first resistor
float r1_NiMh = 560;       // resistance of the second resistor
float r2_LiPo = 1500;       // resistance of the second resistor
float r2_NiMh = 1000;     // resistance of the second resistor
float voltage_LiPo = 0;   // variable to store the value read
float voltage_NiMh = 0;   // variable to store the value read

void setup() {
    Serial.begin(115200);
}

void loop() {
    // read the value from the sensor:
    voltage_LiPo = analogRead(sensorPin_Lipo);
    voltage_NiMh = analogRead(sensorPin_NiMh);
    voltage_LiPo = voltage_LiPo * (5.0 / 1023.0) * ((r1_LiPo+r2_LiPo)/r1_LiPo);
    voltage_NiMh = voltage_NiMh * (5.0 / 1023.0) * ((r1_NiMh+r2_NiMh)/r1_NiMh);
    // print the value to the serial port:
    Serial.print("Lipo voltage: ");
    Serial.print(voltage_LiPo);
    Serial.print("  ");
    Serial.print("NiMh voltage: ");
    Serial.println(voltage_NiMh);

    delay(100);
}
