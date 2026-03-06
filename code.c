#include <DHT.h>
#include <LiquidCrystal.h>
#include <IRremote.h>

#define DHTPIN1 13
#define DHTPIN2 7
#define DHTTYPE DHT11

#define BUZZER 9

#define LED_BLU 8
#define LED_VERDE 6
#define LED_ROSSO 10

#define SOGLIA_ALTA 26.0
#define SOGLIA_MEDIA 25.0

#define LETTURA_INTERVALLO 2000
#define LCD_SWAP_INTERVALLO 3000

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);
DHT dht1(DHTPIN1, DHTTYPE);
DHT dht2(DHTPIN2, DHTTYPE);
decode_results results;

bool buzzerMuto = false;
bool mostraUmidita = false;
float ultimaMedia = 0.0;
float ultimaUmidita1 = 0.0;
float ultimaUmidita2 = 0.0;

unsigned long ultimaLettura = 0;
unsigned long ultimoSwapLCD = 0;
unsigned long ultimoBuzzer = 0;
unsigned long tempoAvvio = 0;

const int NORMALE = 0;
const int ATTENZIONE = 1;
const int ALLARME = 2;

int statoCorrente = NORMALE;
int statoPrecedente = NORMALE;

byte iconaTemp[8] = {
 0b00100, 0b01010, 0b01010, 0b01110,
 0b11111, 0b11111, 0b01110, 0b00000
};

void setup() {
 Serial.begin(9600);
 tempoAvvio = millis();

 Serial.println(F("############################################"));
 Serial.println(F("# SISTEMA MONITORAGGIO TEMPERATURA #"));
 Serial.println(F("############################################"));
 Serial.println(F("Avvio in corso..."));
 Serial.println();

 dht1.begin();
 dht2.begin();

 pinMode(BUZZER, OUTPUT);
 pinMode(LED_BLU, OUTPUT);
 pinMode(LED_VERDE, OUTPUT);
 pinMode(LED_ROSSO, OUTPUT);

 lcd.begin(16, 2);
 lcd.createChar(0, iconaTemp);
 lcd.clear();
 lcd.setCursor(0, 0);
 lcd.print(F(" Monitor Temp "));
 lcd.setCursor(0, 1);
 lcd.print(F(" Inizializ... "));

 tone(BUZZER, 1000); delay(100);
 tone(BUZZER, 1500); delay(100);
 tone(BUZZER, 2000); delay(100);
 noTone(BUZZER);

 delay(1500);
 lcd.clear();

 Serial.println(F("Sistema pronto. Invio dati ogni 2 secondi."));
 Serial.println(F("--------------------------------------------"));
 Serial.println();
}

void aggiornaLED(int s) {
 if (s == ALLARME) {
  digitalWrite(LED_ROSSO, HIGH);
  digitalWrite(LED_VERDE, LOW);
  digitalWrite(LED_BLU, LOW);
 } else if (s == ATTENZIONE) {
  digitalWrite(LED_ROSSO, HIGH);
  digitalWrite(LED_VERDE, HIGH);
  digitalWrite(LED_BLU, LOW);
 } else {
  digitalWrite(LED_ROSSO, LOW);
  digitalWrite(LED_VERDE, HIGH);
  digitalWrite(LED_BLU, LOW);
 }
}

void aggiornaBuzzer(int s) {
 if (buzzerMuto) { noTone(BUZZER); return; }

 unsigned long ora = millis();

 if (s == ALLARME) {
  if (ora - ultimoBuzzer >= 200) {
    static bool buzzerOn = false;
    buzzerOn = !buzzerOn;
    buzzerOn ? tone(BUZZER, 2000) : noTone(BUZZER);
    ultimoBuzzer = ora;
  }
 } else if (s == ATTENZIONE) {
  if (ora - ultimoBuzzer >= 1000) {
    static bool buzzerOn = false;
    buzzerOn = !buzzerOn;
    buzzerOn ? tone(BUZZER, 1000) : noTone(BUZZER);
    ultimoBuzzer = ora;
  }
 } else {
  noTone(BUZZER);
 }
}

void aggiornaLCD() {
 unsigned long ora = millis();

 lcd.setCursor(0, 0);

 if (mostraUmidita && (ora - ultimoSwapLCD >= LCD_SWAP_INTERVALLO)) {
  static bool mostraT = true;
  mostraT = !mostraT;
  ultimoSwapLCD = ora;

  if (mostraT) {
    lcd.write(byte(0));
    lcd.print(F(" Media: "));
    lcd.setCursor(0, 1);
    lcd.print(ultimaMedia, 1);
    lcd.print(F(" \337C "));
  } else {
    lcd.print(F("U1:"));
    lcd.print(ultimaUmidita1, 0);
    lcd.print(F("% U2:"));
    lcd.print(ultimaUmidita2, 0);
    lcd.print(F("% "));
    lcd.setCursor(0, 1);
    lcd.print(F("UMed:"));
    lcd.print((ultimaUmidita1 + ultimaUmidita2) / 2.0, 1);
    lcd.print(F("% "));
  }
 } else if (!mostraUmidita) {
  lcd.write(byte(0));
  lcd.print(F(" Temp Media: "));
  lcd.setCursor(0, 1);
  lcd.print(ultimaMedia, 1);
  lcd.print(F(" \337C"));
  lcd.setCursor(12, 1);
  if (statoCorrente == ALLARME) lcd.print(F("ALR!"));
  else if (statoCorrente == ATTENZIONE) lcd.print(F("ATT."));
  else lcd.print(F(" OK "));
 }
}

void inviaSeriale(float t1, float t2, float h1, float h2) {
 unsigned long secondiTotali = (millis() - tempoAvvio) / 1000;
 unsigned int ore = secondiTotali / 3600;
 unsigned int minuti = (secondiTotali % 3600) / 60;
 unsigned int secondi = secondiTotali % 60;

 String stato;
 if (statoCorrente == ALLARME) stato = "ALLARME";
 else if (statoCorrente == ATTENZIONE) stato = "ATTENZIONE";
 else stato = "NORMALE";

 Serial.println(F("============================================"));

 Serial.print(F("Uptime: "));
 if (ore < 10) Serial.print(F("0")); Serial.print(ore);
 Serial.print(F(":"));
 if (minuti < 10) Serial.print(F("0")); Serial.print(minuti);
 Serial.print(F(":"));
 if (secondi < 10) Serial.print(F("0")); Serial.println(secondi);

 Serial.print(F("Sensore 1 Temp: "));
 Serial.print(t1, 2);
 Serial.println(F(" C"));

 Serial.print(F("Sensore 1 Umid: "));
 Serial.print(h1, 2);
 Serial.println(F(" %"));

 Serial.print(F("Sensore 2 Temp: "));
 Serial.print(t2, 2);
 Serial.println(F(" C"));

 Serial.print(F("Sensore 2 Umid: "));
 Serial.print(h2, 2);
 Serial.println(F(" %"));

 Serial.print(F("Media Temp: "));
 Serial.print(ultimaMedia, 2);
 Serial.println(F(" C"));

 Serial.print(F("Media Umid: "));
 Serial.print((h1 + h2) / 2.0, 2);
 Serial.println(F(" %"));

 Serial.print(F("Stato: "));
 Serial.println(stato);

 Serial.print(F("Buzzer Muto: "));
 Serial.println(buzzerMuto ? F("SI") : F("NO"));

 Serial.println(F("============================================"));
 Serial.println();
}

void loop() {
 unsigned long ora = millis();

 if (ora - ultimaLettura >= LETTURA_INTERVALLO) {
  ultimaLettura = ora;

  float t1 = dht1.readTemperature();
  float t2 = dht2.readTemperature();
  float h1 = dht1.readHumidity();
  float h2 = dht2.readHumidity();

  if (isnan(t1) || isnan(t2) || isnan(h1) || isnan(h2)) {
    Serial.println(F("[ERRORE] Lettura sensore fallita! Controllare i collegamenti DHT."));
    lcd.setCursor(0, 0);
    lcd.print(F("!! ERRORE DHT !!"));
    lcd.setCursor(0, 1);
    lcd.print(F("Ricontrollare..."));
    digitalWrite(LED_BLU, HIGH);
    digitalWrite(LED_VERDE, LOW);
    digitalWrite(LED_ROSSO, LOW);
    tone(BUZZER, 500); delay(300); noTone(BUZZER);
    return;
  }

  ultimaMedia = (t1 + t2) / 2.0;
  ultimaUmidita1 = h1;
  ultimaUmidita2 = h2;

  if (ultimaMedia > SOGLIA_ALTA) statoCorrente = ALLARME;
  else if (ultimaMedia >= SOGLIA_MEDIA) statoCorrente = ATTENZIONE;
  else statoCorrente = NORMALE;

  if (statoCorrente != statoPrecedente) {
    Serial.print(F("[EVENTO] Cambio stato: "));
    Serial.print(statoPrecedente == ALLARME ? F("ALLARME") :
    statoPrecedente == ATTENZIONE ? F("ATTENZIONE") : F("NORMALE"));
    Serial.print(F(" -> "));
    Serial.println(statoCorrente == ALLARME ? F("ALLARME") :
    statoCorrente == ATTENZIONE ? F("ATTENZIONE") : F("NORMALE"));
    statoPrecedente = statoCorrente;
  }

  aggiornaLED(statoCorrente);
  inviaSeriale(t1, t2, h1, h2);
 }

 aggiornaBuzzer(statoCorrente);
 aggiornaLCD();
}