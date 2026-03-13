# Arduino Temp Monitor - Dashboard

Dashboard Python per la visualizzazione in tempo reale dei dati di temperatura e umidita' letti da un sistema Arduino con due sensori DHT11.



## Requisiti

```
pip install dearpygui
```

## Avvio

```bash
python serial_to_csv.py                  # usa salva i dati della porta seriale in dati_arduino.csv
python csv_to_gui.py                  # usa dati_arduino.csv nella cartella
```

## Formato CSV atteso

Il file CSV deve avere le seguenti colonne:

| Colonna | Tipo | Descrizione |
|---|---|---|
| `timestamp` | stringa | Data e ora della lettura |
| `uptime` | stringa | Tempo di attivita' del sistema |
| `sensore1_temp` | float | Temperatura sensore 1 (C) |
| `sensore1_umid` | float | Umidita' sensore 1 (%) |
| `sensore2_temp` | float | Temperatura sensore 2 (C) |
| `sensore2_umid` | float | Umidita' sensore 2 (%) |
| `media_temp` | float | Media temperatura tra i due sensori |
| `media_umid` | float | Media umidita' tra i due sensori |
| `stato` | stringa | `NORMALE`, `ATTENZIONE` o `ALLARME` |
| `buzzer_muto` | stringa | `SI` o `NO` |

## Funzionalita'

**Grafici in tempo reale**
Temperatura e umidita' dei due sensori e della loro media, aggiornati automaticamente ogni 3 secondi. I grafici mostrano al massimo 100 punti per ottimizzare le prestazioni.

**Pannello statistiche**
Per ogni grandezza misurata vengono mostrati: valore minimo, massimo, media storica e deviazione standard.

**Distribuzione degli stati**
Contatore dei campioni per ciascuno stato (NORMALE, ATTENZIONE, ALLARME) con percentuale sul totale.

**Analisi automatica**
Testo generato automaticamente che riassume l'andamento del sistema, segnala superamenti di soglia, valuta la stabilita' termica e il trend in corso.

**Aggiornamento manuale**
Pulsante "Aggiorna ora" per forzare la rilettura del CSV senza aspettare il refresh automatico.

## Soglie

Le soglie di stato sono configurabili direttamente nel codice:

```python
SOGLIA_ALTA  = 26.0
SOGLIA_MEDIA = 25.0
```

## Parametri configurabili

| Parametro | Default | Descrizione |
|---|---|---|
| `CSV_FILE` | `dati_arduino.csv` | File CSV da leggere |
| `REFRESH_RATE` | `3.0` | Secondi tra un aggiornamento e il successivo |
| `MAX_PUNTI_GRAFICO` | `100` | Punti massimi visualizzati nei grafici |

## Hardware Arduino compatibile

Il sistema e' progettato per funzionare con:

- 2x sensore DHT11
- Display LCD 16x2
- LED rosso, verde, blu
- Buzzer
- Ricevitore IR (opzionale)

Il codice Arduino serializza i dati in un formato che uno script separato puo' scrivere nel CSV letto da questa dashboard.

## Struttura del progetto

```
.
├── csv_to_gui.py          # dashboard principale
├── serial_to_csv.py          # dashboard principale
├── code.c                 # codice di arduino
└── dati_arduino.csv       # file dati
```

## Autori
- Enrico Jaupi
- Manuel Bertozzi
- Riccardo Righi Sebastiano
