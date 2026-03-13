import sys
import os
import csv
import math
import time
import threading
from datetime import datetime
from collections import Counter

try:
    import dearpygui.dearpygui as dpg
except ImportError:
    print("[ERRORE] DearPyGui non installato. Esegui: pip install dearpygui")
    sys.exit(1)

CSV_FILE = sys.argv[1] if len(sys.argv) > 1 else "dati_arduino.csv"
REFRESH_RATE = 3.0
MAX_PUNTI_GRAFICO = 100

SOGLIA_ALTA = 26.0
SOGLIA_MEDIA = 25.0

COL_SFONDO = (15, 17, 21, 255)
COL_PANNELLO = (22, 26, 34, 255)
COL_BORDO = (45, 55, 72, 255)
COL_TESTO = (220, 225, 235, 255)
COL_TESTO_DIM = (130, 140, 160, 255)
COL_VERDE = (72, 199, 142, 255)
COL_GIALLO = (251, 189, 35, 255)
COL_ROSSO = (255, 82, 82, 255)
COL_BLU = (66, 153, 225, 255)
COL_VIOLA = (159, 122, 234, 255)
COL_ARANCIO = (237, 137, 54, 255)
COL_GRAFICO_T1 = (66, 153, 225, 255)
COL_GRAFICO_T2 = (159, 122, 234, 255)
COL_GRAFICO_MED = (72, 199, 142, 255)
COL_GRAFICO_U = (237, 137, 54, 255)

dati_globali = {
    "timestamp": [],
    "uptime": [],
    "s1_temp": [],
    "s1_umid": [],
    "s2_temp": [],
    "s2_umid": [],
    "media_temp": [],
    "media_umid": [],
    "stato": [],
    "buzzer_muto": [],
    "n_righe": 0,
    "ultimo_update": None,
}
lock_dati = threading.Lock()

def leggi_csv():
    if not os.path.exists(CSV_FILE):
        return False

    ts, up = [], []
    s1t, s1u = [], []
    s2t, s2u = [], []
    mt, mu = [], []
    stati = []
    buzzer = []

    try:
        with open(CSV_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for riga in reader:
                try:
                    ts.append(riga.get("timestamp", ""))
                    up.append(riga.get("uptime", ""))
                    s1t.append(float(riga.get("sensore1_temp", 0) or 0))
                    s1u.append(float(riga.get("sensore1_umid", 0) or 0))
                    s2t.append(float(riga.get("sensore2_temp", 0) or 0))
                    s2u.append(float(riga.get("sensore2_umid", 0) or 0))
                    mt.append(float(riga.get("media_temp", 0) or 0))
                    mu.append(float(riga.get("media_umid", 0) or 0))
                    stati.append(riga.get("stato", "?").strip())
                    buzzer.append(riga.get("buzzer_muto", "NO").strip())
                except (ValueError, TypeError):
                    continue

        with lock_dati:
            dati_globali["timestamp"] = ts
            dati_globali["uptime"] = up
            dati_globali["s1_temp"] = s1t
            dati_globali["s1_umid"] = s1u
            dati_globali["s2_temp"] = s2t
            dati_globali["s2_umid"] = s2u
            dati_globali["media_temp"] = mt
            dati_globali["media_umid"] = mu
            dati_globali["stato"] = stati
            dati_globali["buzzer_muto"] = buzzer
            dati_globali["n_righe"] = len(ts)
            dati_globali["ultimo_update"] = datetime.now().strftime("%H:%M:%S")
        return True

    except Exception as e:
        print(f"[ERRORE] Lettura CSV: {e}")
        return False

def calcola_stats(valori):
    if not valori:
        return {"min": 0, "max": 0, "media": 0, "ultimo": 0, "dev_std": 0}
    n = len(valori)
    media = sum(valori) / n
    dev_std = math.sqrt(sum((x - media) ** 2 for x in valori) / n) if n > 1 else 0
    return {
        "min": round(min(valori), 2),
        "max": round(max(valori), 2),
        "media": round(media, 2),
        "ultimo": round(valori[-1], 2),
        "dev_std": round(dev_std, 2),
    }

def conta_stati(stati):
    c = Counter(stati)
    return {
        "NORMALE": c.get("NORMALE", 0),
        "ATTENZIONE": c.get("ATTENZIONE", 0),
        "ALLARME": c.get("ALLARME", 0),
    }

def stato_corrente_colore(stato):
    if stato == "ALLARME":
        return COL_ROSSO
    elif stato == "ATTENZIONE":
        return COL_GIALLO
    return COL_VERDE

def interpreta_trend(valori, n=5):
    if len(valori) < 2:
        return "-"
    ultimi = valori[-min(n, len(valori)):]
    delta = ultimi[-1] - ultimi[0]
    if delta > 0.5:
        return f"In salita (+{delta:.1f})"
    elif delta < -0.5:
        return f"In discesa ({delta:.1f})"
    return "Stabile"

def aggiorna_ui():
    with lock_dati:
        n = dati_globali["n_righe"]
        s1t = dati_globali["s1_temp"][:]
        s1u = dati_globali["s1_umid"][:]
        s2t = dati_globali["s2_temp"][:]
        s2u = dati_globali["s2_umid"][:]
        mt = dati_globali["media_temp"][:]
        mu = dati_globali["media_umid"][:]
        stati = dati_globali["stato"][:]
        ts = dati_globali["timestamp"][:]
        upd = dati_globali["ultimo_update"]

    if n == 0:
        dpg.set_value("lbl_status_bar", f"  Nessun dato in {CSV_FILE} — in attesa...")
        return

    st_s1t = calcola_stats(s1t)
    st_s2t = calcola_stats(s2t)
    st_mt = calcola_stats(mt)
    st_mu = calcola_stats(mu)
    st_s1u = calcola_stats(s1u)
    st_s2u = calcola_stats(s2u)
    cnt_stati = conta_stati(stati)
    stato_now = stati[-1] if stati else "-"
    trend_t = interpreta_trend(mt)
    trend_u = interpreta_trend(mu)

    dpg.set_value("lbl_stato_now", stato_now)
    dpg.configure_item("lbl_stato_now", color=stato_corrente_colore(stato_now))
    dpg.set_value("lbl_temp_now", f"{st_mt['ultimo']} C")
    dpg.set_value("lbl_umid_now", f"{st_mu['ultimo']} %")
    dpg.set_value("lbl_trend_t", trend_t)
    dpg.set_value("lbl_trend_u", trend_u)
    dpg.set_value("lbl_n_campioni", f"{n} campioni")

    dpg.set_value("stat_t_min", f"{st_mt['min']} C")
    dpg.set_value("stat_t_max", f"{st_mt['max']} C")
    dpg.set_value("stat_t_media", f"{st_mt['media']} C")
    dpg.set_value("stat_t_std", f"+/- {st_mt['dev_std']} C")
    dpg.set_value("stat_s1_min", f"{st_s1t['min']} C")
    dpg.set_value("stat_s1_max", f"{st_s1t['max']} C")
    dpg.set_value("stat_s1_media", f"{st_s1t['media']} C")
    dpg.set_value("stat_s2_min", f"{st_s2t['min']} C")
    dpg.set_value("stat_s2_max", f"{st_s2t['max']} C")
    dpg.set_value("stat_s2_media", f"{st_s2t['media']} C")

    dpg.set_value("stat_u_min", f"{st_mu['min']} %")
    dpg.set_value("stat_u_max", f"{st_mu['max']} %")
    dpg.set_value("stat_u_media", f"{st_mu['media']} %")
    dpg.set_value("stat_u_std", f"+/- {st_mu['dev_std']} %")
    dpg.set_value("stat_u1_media", f"{st_s1u['media']} %")
    dpg.set_value("stat_u2_media", f"{st_s2u['media']} %")

    tot = max(n, 1)
    dpg.set_value("cnt_normale", f"{cnt_stati['NORMALE']}  ({cnt_stati['NORMALE']*100//tot}%)")
    dpg.set_value("cnt_attenzione", f"{cnt_stati['ATTENZIONE']}  ({cnt_stati['ATTENZIONE']*100//tot}%)")
    dpg.set_value("cnt_allarme", f"{cnt_stati['ALLARME']}  ({cnt_stati['ALLARME']*100//tot}%)")

    analisi = genera_analisi_testo(st_mt, st_mu, cnt_stati, n, stato_now, trend_t, trend_u)
    dpg.set_value("lbl_analisi", analisi)

    xs = list(range(len(mt)))
    if len(xs) > MAX_PUNTI_GRAFICO:
        step = len(xs) // MAX_PUNTI_GRAFICO
        xs = xs[::step]
        s1t_g = s1t[::step]
        s2t_g = s2t[::step]
        mt_g = mt[::step]
        s1u_g = s1u[::step]
        s2u_g = s2u[::step]
        mu_g = mu[::step]
    else:
        s1t_g, s2t_g, mt_g = s1t, s2t, mt
        s1u_g, s2u_g, mu_g = s1u, s2u, mu

    xs_f = [float(x) for x in xs]

    dpg.set_value("serie_s1_temp", [xs_f, [float(v) for v in s1t_g]])
    dpg.set_value("serie_s2_temp", [xs_f, [float(v) for v in s2t_g]])
    dpg.set_value("serie_med_temp", [xs_f, [float(v) for v in mt_g]])
    dpg.set_value("serie_s1_umid", [xs_f, [float(v) for v in s1u_g]])
    dpg.set_value("serie_s2_umid", [xs_f, [float(v) for v in s2u_g]])
    dpg.set_value("serie_med_umid", [xs_f, [float(v) for v in mu_g]])

    if xs_f:
        for ax_tag in ["ax_x_temp", "ax_x_umid"]:
            dpg.set_axis_limits(ax_tag, xs_f[0], xs_f[-1])
        dpg.set_axis_limits("ax_y_temp",
            min(min(s1t_g), min(s2t_g)) - 2,
            max(max(s1t_g), max(s2t_g)) + 2)
        dpg.set_axis_limits("ax_y_umid",
            min(min(s1u_g), min(s2u_g)) - 5,
            max(max(s1u_g), max(s2u_g)) + 5)

    dpg.set_value("lbl_status_bar",
        f"  {CSV_FILE}  |  {n} campioni  |  Aggiornato: {upd}  |  Auto-refresh: {REFRESH_RATE}s")

def genera_analisi_testo(st_mt, st_mu, cnt_stati, n, stato_now, trend_t, trend_u):
    lines = []

    lines.append(f"ANALISI SU {n} CAMPIONI RACCOLTI")
    lines.append("-" * 44)

    lines.append("\nTEMPERATURA MEDIA")
    lines.append(f"  Valore attuale: {st_mt['ultimo']} C  ({trend_t})")
    lines.append(f"  Range osservato: {st_mt['min']} C  ->  {st_mt['max']} C")
    lines.append(f"  Media storica: {st_mt['media']} C  |  Dev. std: {st_mt['dev_std']} C")

    if st_mt['media'] > SOGLIA_ALTA:
        lines.append(f"  [!] Media sopra soglia alta ({SOGLIA_ALTA} C)!")
    elif st_mt['media'] >= SOGLIA_MEDIA:
        lines.append(f"  [~] Media in zona attenzione ({SOGLIA_MEDIA}-{SOGLIA_ALTA} C).")
    else:
        lines.append(f"  [OK] Media nella norma (sotto {SOGLIA_MEDIA} C).")

    lines.append("\nUMIDITA' MEDIA")
    lines.append(f"  Valore attuale: {st_mu['ultimo']} %  ({trend_u})")
    lines.append(f"  Range osservato: {st_mu['min']} %  ->  {st_mu['max']} %")
    lines.append(f"  Media storica: {st_mu['media']} %  |  Dev. std: {st_mu['dev_std']} %")

    if st_mu['media'] > 70:
        lines.append("  [!] Umidita' elevata (> 70%). Rischio condensa.")
    elif st_mu['media'] < 30:
        lines.append("  [~] Umidita' bassa (< 30%). Aria secca.")
    else:
        lines.append("  [OK] Umidita' nella norma (30-70%).")

    tot = max(n, 1)
    lines.append("\nDISTRIBUZIONE STATI")
    lines.append(f"  Normale: {cnt_stati['NORMALE']} campioni ({cnt_stati['NORMALE']*100//tot}%)")
    lines.append(f"  Attenzione: {cnt_stati['ATTENZIONE']} campioni ({cnt_stati['ATTENZIONE']*100//tot}%)")
    lines.append(f"  Allarme: {cnt_stati['ALLARME']} campioni ({cnt_stati['ALLARME']*100//tot}%)")

    lines.append(f"\nSTATO CORRENTE: {stato_now}")
    if stato_now == "ALLARME":
        lines.append("  [!!] Temperatura critica - intervenire!")
    elif stato_now == "ATTENZIONE":
        lines.append("  [~] Monitorare l'andamento nelle prossime letture.")
    else:
        lines.append("  [OK] Sistema operativo nella norma.")

    lines.append("\nSTABILITA' SISTEMA")
    if st_mt['dev_std'] < 0.5:
        lines.append("  [OK] Temperatura molto stabile.")
    elif st_mt['dev_std'] < 1.5:
        lines.append("  [~] Variazioni moderate di temperatura.")
    else:
        lines.append("  [!] Alta variabilita' termica rilevata.")

    return "\n".join(lines)

def thread_refresh():
    while True:
        time.sleep(REFRESH_RATE)
        if leggi_csv():
            aggiorna_ui()

def _serie_theme(colore, spessore=2):
    with dpg.theme() as t:
        with dpg.theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line, colore, category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, spessore, category=dpg.mvThemeCat_Plots)
    return t

def build_ui():
    dpg.create_context()

    W, H = 1400, 900

    with dpg.theme() as tema_globale:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, COL_SFONDO, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, COL_PANNELLO, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (30, 36, 46, 255), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (30, 36, 50, 255), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (22, 26, 34, 255), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Border, COL_BORDO, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Text, COL_TESTO, category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Button, (45, 55, 80, 255), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (66, 80, 115, 255), category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 6, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 12, 10, category=dpg.mvThemeCat_Core)

    dpg.bind_theme(tema_globale)

    with dpg.window(tag="MainWindow", label="", no_title_bar=True,
                    no_resize=True, no_move=True,
                    width=W, height=H, pos=(0, 0)):

        with dpg.child_window(height=58, border=False, tag="header"):
            dpg.add_spacer(height=6)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=10)
                dpg.add_text("ARDUINO TEMP MONITOR", color=COL_BLU)
                dpg.add_spacer(width=20)
                dpg.add_text("-" * 60, color=COL_BORDO)
                dpg.add_spacer(width=20)
                dpg.add_text(f"File: {CSV_FILE}", color=COL_TESTO_DIM)
            dpg.add_spacer(height=4)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=10)
                dpg.add_text("Stato:", color=COL_TESTO_DIM)
                dpg.add_text("-", tag="lbl_stato_now", color=COL_VERDE)
                dpg.add_spacer(width=30)
                dpg.add_text("Temp:", color=COL_TESTO_DIM)
                dpg.add_text("-", tag="lbl_temp_now", color=COL_TESTO)
                dpg.add_spacer(width=30)
                dpg.add_text("Umid:", color=COL_TESTO_DIM)
                dpg.add_text("-", tag="lbl_umid_now", color=COL_TESTO)
                dpg.add_spacer(width=30)
                dpg.add_text("Trend T:", color=COL_TESTO_DIM)
                dpg.add_text("-", tag="lbl_trend_t", color=COL_ARANCIO)
                dpg.add_spacer(width=30)
                dpg.add_text("Trend U:", color=COL_TESTO_DIM)
                dpg.add_text("-", tag="lbl_trend_u", color=COL_ARANCIO)
                dpg.add_spacer(width=30)
                dpg.add_text("-", tag="lbl_n_campioni", color=COL_TESTO_DIM)
                dpg.add_spacer(width=20)
                dpg.add_button(label="Aggiorna ora", callback=lambda: (leggi_csv(), aggiorna_ui()))

        dpg.add_separator()

        with dpg.group(horizontal=True):

            with dpg.child_window(width=320, height=H - 110, border=True, tag="pannello_sx"):

                dpg.add_text("  TEMPERATURA", color=COL_BLU)
                dpg.add_separator()
                dpg.add_spacer(height=4)

                def stat_row(label, tag, col=COL_TESTO):
                    with dpg.group(horizontal=True):
                        dpg.add_text(f"  {label:<16}", color=COL_TESTO_DIM)
                        dpg.add_text("-", tag=tag, color=col)

                stat_row("Media Media", "stat_t_media", COL_VERDE)
                stat_row("Min Media", "stat_t_min", COL_BLU)
                stat_row("Max Media", "stat_t_max", COL_ROSSO)
                stat_row("Dev. Std", "stat_t_std", COL_TESTO_DIM)
                stat_row("S1 media", "stat_s1_media", COL_GRAFICO_T1)
                stat_row("S1 min", "stat_s1_min", COL_TESTO_DIM)
                stat_row("S1 max", "stat_s1_max", COL_TESTO_DIM)
                stat_row("S2 media", "stat_s2_media", COL_GRAFICO_T2)
                stat_row("S2 min", "stat_s2_min", COL_TESTO_DIM)
                stat_row("S2 max", "stat_s2_max", COL_TESTO_DIM)

                dpg.add_spacer(height=10)
                dpg.add_text("  UMIDITA'", color=COL_ARANCIO)
                dpg.add_separator()
                dpg.add_spacer(height=4)

                stat_row("Media Media", "stat_u_media", COL_VERDE)
                stat_row("Min Media", "stat_u_min", COL_BLU)
                stat_row("Max Media", "stat_u_max", COL_ROSSO)
                stat_row("Dev. Std", "stat_u_std", COL_TESTO_DIM)
                stat_row("S1 media", "stat_u1_media", COL_GRAFICO_T1)
                stat_row("S2 media", "stat_u2_media", COL_GRAFICO_T2)

                dpg.add_spacer(height=10)
                dpg.add_text("  STATI SISTEMA", color=COL_VIOLA)
                dpg.add_separator()
                dpg.add_spacer(height=4)

                stat_row("Normale", "cnt_normale", COL_VERDE)
                stat_row("Attenzione", "cnt_attenzione", COL_GIALLO)
                stat_row("Allarme", "cnt_allarme", COL_ROSSO)

                dpg.add_spacer(height=14)
                dpg.add_text("  ANALISI AUTOMATICA", color=COL_VERDE)
                dpg.add_separator()
                dpg.add_spacer(height=4)
                dpg.add_text("In attesa dati...", tag="lbl_analisi", color=COL_TESTO, wrap=296)

            with dpg.child_window(width=W - 340, height=H - 110, border=True, tag="pannello_dx"):

                dpg.add_text("  GRAFICO TEMPERATURA (C)", color=COL_BLU)
                dpg.add_separator()

                with dpg.plot(label="", height=340, width=-1, tag="plot_temp", anti_aliased=True):
                    dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
                    dpg.add_plot_axis(dpg.mvXAxis, label="Campione", tag="ax_x_temp")
                    with dpg.plot_axis(dpg.mvYAxis, label="C", tag="ax_y_temp"):
                        dpg.add_line_series([], [], label="Sensore 1", tag="serie_s1_temp", parent="ax_y_temp")
                        dpg.add_line_series([], [], label="Sensore 2", tag="serie_s2_temp", parent="ax_y_temp")
                        dpg.add_line_series([], [], label="Media", tag="serie_med_temp", parent="ax_y_temp")
                    dpg.bind_item_theme("serie_s1_temp", _serie_theme(COL_GRAFICO_T1))
                    dpg.bind_item_theme("serie_s2_temp", _serie_theme(COL_GRAFICO_T2))
                    dpg.bind_item_theme("serie_med_temp", _serie_theme(COL_GRAFICO_MED, 3))

                dpg.add_spacer(height=8)
                dpg.add_text("  GRAFICO UMIDITA' (%)", color=COL_ARANCIO)
                dpg.add_separator()

                with dpg.plot(label="", height=340, width=-1, tag="plot_umid", anti_aliased=True):
                    dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
                    dpg.add_plot_axis(dpg.mvXAxis, label="Campione", tag="ax_x_umid")
                    with dpg.plot_axis(dpg.mvYAxis, label="%", tag="ax_y_umid"):
                        dpg.add_line_series([], [], label="Sensore 1", tag="serie_s1_umid", parent="ax_y_umid")
                        dpg.add_line_series([], [], label="Sensore 2", tag="serie_s2_umid", parent="ax_y_umid")
                        dpg.add_line_series([], [], label="Media", tag="serie_med_umid", parent="ax_y_umid")
                    dpg.bind_item_theme("serie_s1_umid", _serie_theme(COL_GRAFICO_T1))
                    dpg.bind_item_theme("serie_s2_umid", _serie_theme(COL_GRAFICO_T2))
                    dpg.bind_item_theme("serie_med_umid", _serie_theme(COL_GRAFICO_U, 3))

        dpg.add_separator()
        with dpg.child_window(height=28, border=False):
            dpg.add_text("  Caricamento...", tag="lbl_status_bar", color=COL_TESTO_DIM)

    dpg.create_viewport(title="Arduino Temp Monitor", width=W, height=H, resizable=False)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("MainWindow", True)

    return W, H

def main():
    print("=" * 55)
    print("       ARDUINO DASHBOARD - DearPyGui")
    print("=" * 55)
    print(f"  File CSV: {CSV_FILE}")
    print(f"  Refresh: ogni {REFRESH_RATE} secondi")
    print("=" * 55)

    if not os.path.exists(CSV_FILE):
        print(f"[WARN] {CSV_FILE} non trovato. La dashboard aspettera' il file.")

    build_ui()

    if leggi_csv():
        aggiorna_ui()

    t = threading.Thread(target=thread_refresh, daemon=True)
    t.start()

    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()

    dpg.destroy_context()
    print("[INFO] Dashboard chiusa.")

if __name__ == "__main__":
    main()