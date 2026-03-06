"""
Requisiti:
    pip install pyserial

Uso:
    python serial_to_csv.py              # usa porta default e 9600
    python serial_to_csv.py COM3 9600    # Windows
    python serial_to_csv.py /dev/ttyUSB0 9600  # Linux/Mac
"""

import serial
import csv
import os
import sys
import time
from datetime import datetime

SERIAL_PORT  = sys.argv[1] if len(sys.argv) > 1 else "COM3"
SYNC_PORT    = int(sys.argv[2]) if len(sys.argv) > 2 else 9600
CSV_FILE     = "dati_arduino.csv"
SEPARATOR    = "============================================"

CSV_HEADER = [
    "timestamp",
    "uptime",
    "sensore1_temp",
    "sensore1_umid",
    "sensore2_temp",
    "sensore2_umid",
    "media_temp",
    "media_umid",
    "stato",
    "buzzer_muto"
]

def crea_csv_se_non_esiste():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)
        print(f"[INFO] File CSV creato: {CSV_FILE}")
    else:
        print(f"[INFO] File CSV esistente trovato: {CSV_FILE} — i dati verranno aggiunti.")

def parse_valore(riga, chiave):
    try:
        parts = riga.split(":", 1)
        if len(parts) < 2:
            return None
        valore = parts[1].strip()
        for unita in [" C", " %", "C", "%"]:
            valore = valore.replace(unita, "").strip()
        return valore
    except Exception:
        return None

def leggi_blocco(righe_blocco):
    dati = {
        "timestamp":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "uptime":         None,
        "sensore1_temp":  None,
        "sensore1_umid":  None,
        "sensore2_temp":  None,
        "sensore2_umid":  None,
        "media_temp":     None,
        "media_umid":     None,
        "stato":          None,
        "buzzer_muto":    None,
    }

    for riga in righe_blocco:
        riga = riga.strip()

        if riga.startswith("Uptime"):
            dati["uptime"] = parse_valore(riga, "Uptime")

        elif riga.startswith("Sensore 1 Temp"):
            dati["sensore1_temp"] = parse_valore(riga, "Sensore 1 Temp")

        elif riga.startswith("Sensore 1 Umid"):
            dati["sensore1_umid"] = parse_valore(riga, "Sensore 1 Umid")

        elif riga.startswith("Sensore 2 Temp"):
            dati["sensore2_temp"] = parse_valore(riga, "Sensore 2 Temp")

        elif riga.startswith("Sensore 2 Umid"):
            dati["sensore2_umid"] = parse_valore(riga, "Sensore 2 Umid")

        elif riga.startswith("Media Temp"):
            dati["media_temp"] = parse_valore(riga, "Media Temp")

        elif riga.startswith("Media Umid"):
            dati["media_umid"] = parse_valore(riga, "Media Umid")

        elif riga.startswith("Stato"):
            dati["stato"] = parse_valore(riga, "Stato")

        elif riga.startswith("Buzzer Muto"):
            dati["buzzer_muto"] = parse_valore(riga, "Buzzer Muto")

    return dati

def salva_riga_csv(dati):
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            dati["timestamp"],
            dati["uptime"],
            dati["sensore1_temp"],
            dati["sensore1_umid"],
            dati["sensore2_temp"],
            dati["sensore2_umid"],
            dati["media_temp"],
            dati["media_umid"],
            dati["stato"],
            dati["buzzer_muto"],
        ])

def stampa_dati(dati, contatore):
    print(f"\n[#{contatore:04d}] {dati['timestamp']}  |  Uptime: {dati['uptime']}")
    print(f"  Temp  -> S1: {dati['sensore1_temp']}°C  |  S2: {dati['sensore2_temp']}°C  |  Media: {dati['media_temp']}°C")
    print(f"  Umid  -> S1: {dati['sensore1_umid']}%   |  S2: {dati['sensore2_umid']}%   |  Media: {dati['media_umid']}%")
    print(f"  Stato -> {dati['stato']}  |  Buzzer muto: {dati['buzzer_muto']}")

def main():
    print("=" * 55)
    print("       ARDUINO SERIAL → CSV RECORDER")
    print("=" * 55)
    print(f"  Porta    : {SERIAL_PORT}")
    print(f"  Baudrate : {SYNC_PORT}")
    print(f"  Output   : {CSV_FILE}")
    print("  Premi CTRL+C per fermare.")
    print("=" * 55)

    crea_csv_se_non_esiste()

    ser = None
    while ser is None:
        try:
            ser = serial.Serial(SERIAL_PORT, SYNC_PORT, timeout=2)
            print(f"\n[OK] Connesso a {SERIAL_PORT}")
        except serial.SerialException as e:
            print(f"[ATTESA] Porta non disponibile: {e}. Riprovo tra 3 secondi...")
            time.sleep(3)

    buffer_blocco = []
    in_blocco     = False
    contatore     = 0

    try:
        while True:
            try:
                linea_raw = ser.readline()
                if not linea_raw:
                    continue

                linea = linea_raw.decode("utf-8", errors="ignore").strip()

                if linea == SEPARATOR:
                    if in_blocco and buffer_blocco:
                        dati = leggi_blocco(buffer_blocco)

                        if dati["media_temp"] is not None and dati["stato"] is not None:
                            contatore += 1
                            salva_riga_csv(dati)
                            stampa_dati(dati, contatore)
                        else:
                            print("[WARN] Blocco incompleto, saltato.")

                        buffer_blocco = []
                        in_blocco = False
                    else:
                        in_blocco     = True
                        buffer_blocco = []

                elif in_blocco:
                    buffer_blocco.append(linea)

                elif linea.startswith("[EVENTO]") or linea.startswith("[ERRORE]") or linea.startswith("[IR]"):
                    print(f"[ARDUINO] {linea}")

            except UnicodeDecodeError:
                pass

    except KeyboardInterrupt:
        print(f"\n\n[STOP] Registrazione interrotta. {contatore} righe salvate in '{CSV_FILE}'.")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("[INFO] Porta seriale chiusa.")

if __name__ == "__main__":
    main()