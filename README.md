# 📡 OpenMc888 / OpenMC889

> **WebGUI avanzata per ZTE MC888 e MC889 — Bookmarklet JavaScript**

[![Status](https://img.shields.io/badge/Stato-Alpha%201.0-orange?style=flat-square)](https://github.com/mixmax111/OpenMc888-889-Alpha-)
[![Modem](https://img.shields.io/badge/Modem-ZTE%20MC888%20%2F%20MC889-blue?style=flat-square)](https://github.com/mixmax111/OpenMc888-889-Alpha-)
[![Licenza](https://img.shields.io/badge/Licenza-MIT-green?style=flat-square)](LICENSE)
[![Tipo](https://img.shields.io/badge/Tipo-Bookmarklet-blueviolet?style=flat-square)](https://github.com/mixmax111/OpenMc888-889-Alpha-)


---

**OpenMc888-889-Alpha-** è una WebGUI potenziata sotto forma di *Bookmarklet* (Segnalibro del browser) progettata per sbloccare le funzionalità avanzate dei modem/router 5G **ZTE MC888** e **MC889**, tipicamente distribuiti da operatori **FWA**.

Nato dal lavoro e dalla divulgazione di **miononno** — che ha sviluppato e pubblicato script di controllo per i router ZTE della serie 888/889 — questo progetto porta quelle funzionalità in una **interfaccia grafica moderna**, con cruscotto dark-modal, grafici del segnale in tempo reale e **assistente guidato al puntamento dell'antenna**, senza dover craccare o flashare il dispositivo.

Sviluppato da **mix_max111** con il supporto di AI.

---

## ⚠️ Avvisi Importanti

> **🚨 PROGETTO SPERIMENTALE — ALPHA 1.0**
>
> Script in fase di test attivo. Non è un prodotto finito. Alcune funzioni potrebbero non funzionare su tutti i firmware o su router con firmware operatore modificato. **Usalo a tuo rischio e pericolo.**

> **⚖️ DISCLAIMER — NESSUNA RESPONSABILITÀ**
>
> Gli autori non si assumono **alcuna responsabilità** per danni al dispositivo, interruzioni del servizio, violazioni dei Termini di Servizio del tuo operatore, o qualsiasi altra conseguenza derivante dall'uso di questo strumento. Il progetto è pubblicato a scopo **educativo e di ricerca**.

> **⚡ CELL LOCK — ATTENZIONE**
>
> L'utilizzo del Cell Lock blocca il modem su una cella specifica. Per rimuoverlo è **necessario fare il RESET di fabbrica** del router. Usalo consapevolmente.

---

## ✅ Funzionalità

### 📊 Cruscotto Radio in Tempo Reale

Aggiornamento automatico ogni **1.5 secondi** di tutti i parametri radio:

| Parametro | Descrizione |
|---|---|
| **RSRP** | Potenza del segnale ricevuto LTE (dBm) |
| **RSRQ** | Qualità del segnale LTE (dB) |
| **SINR** | Rapporto segnale/rumore LTE (dB) |
| **NR RSRP** | Potenza segnale 5G NR (dBm) — visibile solo se agganciato |
| **NR SINR** | SINR 5G NR (dB) — visibile solo se agganciato |
| **Rete / Banda** | Tipo rete (4G/5G) e banda principale agganciata |
| **NR Banda / PCI** | Banda e PCI 5G NR |
| **Carrier Aggregation** | PCell + tutte le SCell aggregate con larghezza di banda |
| **ENB ID** | ID eNodeB con link diretto a **LTE Italy** |
| **Sector ID** | ID numerico della cella (Cell ID decimale) |
| **PCI / EARFCN** | Identificatori fisici della cella LTE |
| **IP WAN** | Indirizzo IP pubblico assegnato |
| **Temp 4G / 5G** | Temperatura moduli modem in °C |
| **Cell Lock** | Mostra il lock PCI/EARFCN attivo (se presente) |
| **DNS** | DNS correntemente configurati |

Tutti i parametri di segnale includono un **bar-graph SVG** con storico circolare delle ultime misurazioni.

---

### 📈 Statistiche & Grafici Live in Tempo Reale

Pannello grafico dedicato per l'analisi avanzata e dettagliata del segnale in tempo reale (aggiornamento ogni 1.5s):

- **Grafici Timeline SVG Dettagliati:** Mostrano l'andamento temporale continuo per **LTE RSRP** (Potenza 4G), **LTE SINR** (Qualità/Disturbo 4G), **LTE RSRQ** (Qualità 4G) e, se agganciato, **5G NR RSRP** e **5G NR SINR**.
- **Indicatori Statistici Live:** Per ogni metrica calcola in tempo reale **Valore Attuale**, **Minimo**, **Massimo** e **Media** registrati sul buffer storico (fino alle ultime ~120 misurazioni, circa 3 minuti di campionamento continuo).
- **Tracciamento Grafico con Griglia:** Area riempita con trasparenza e linee guida tratteggiate per individuare subito micro-interruzioni, sbalzi di qualità o instabilità di segnale.

---

### 🎯 Assistente Puntamento Antenna (Wizard Guidato)

Sistema professionale di allineamento a più fasi con **misurazioni statistiche** (media su 30 secondi per ogni posizione). Traccia il **PCI** (torre fisica agganciata) per rilevare cambi di cella durante il puntamento.

- **🧭 Primo Puntamento (Quadranti):** Scansiona i 4 punti cardinali (N/S/E/O), individua il settore migliore, raffina a ±45°. 8 step totali.
- **↕️ Ottimizzazione Altezza:** Testa la posizione ottimale del palo (Base / Su / Giù).
- **📐 Ottimizzazione Inclinazione (Tilt):** Testa l'angolazione verticale (Neutro / +5° / -5°).
- **🎯 Fine-Tuning Micrometrico:** Rifinitura sinistra/destra di 5–10°.

**Score di valutazione:** `RSRP + (SINR × 2)` — più alto = migliore.

---

### 🔒 Cell Lock

Blocca il modem su una cella specifica tramite PCI + EARFCN. I campi vengono **pre-compilati** con i valori della cella attualmente agganciata.

- **goformId:** `LTE_LOCK_CELL_SET`
- ⚠️ Richede RESET per rimuovere il lock.

---

### 📶 Selezione Bande LTE e 5G NR

Pannello dedicato per scegliere le bande attive:

| Tipo | Metodo | Esempio |
|---|---|---|
| **LTE 4G** | Numeri separati da `+`, oppure `AUTO` | `1+3+20` |
| **5G NR** | Numeri separati da `+`, oppure `AUTO` | `78` o `3+78` |

- LTE usa **bitmask hex** (`BAND_SELECT`)
- 5G usa **CSV** (`WAN_PERFORM_NR5G_BAND_LOCK`) — formato diverso!

---

### 🌐 Configurazione DNS

Imposta DNS personalizzati direttamente nel profilo APN attivo:

- DNS primario + secondario con campi pre-compilati dai valori correnti
- Pulsante **AUTO** per ripristinare i DNS del provider
- **goformId:** `APN_PROC_EX` (doppia chiamata sequenziale)

---

### ℹ️ Info Firmware

Visualizza le versioni Hardware, Web, WA Inner e CR del firmware installato.

---

### 🔄 Reboot Rapido

Riavvio del modem con un click e doppia conferma.

---

## 🚀 Installazione

Non serve installare nulla. Funziona tutto tramite il browser in modo **non invasivo e non permanente**.

1. Apri il tuo browser — **Firefox** consigliato (altri browser come Brave possono limitare la lunghezza degli URL nei bookmark).
2. Vai alla pagina dell'interfaccia del modem (es. `http://192.168.0.1`) ed **effettua il login**.
3. Crea un nuovo **Segnalibro** sulla barra in alto (⭐).
4. Clic destro → **Modifica** sul segnalibro appena creato.
5. Nel campo **URL / Indirizzo**, cancella tutto e incolla il contenuto del file **`OpenMC888_889.bookmarklet.txt`**.
6. Salva. Ogni volta che vuoi aprire il tool, clicca sul segnalibro mentre sei sulla pagina del modem.

> **💡 Nota:** Il file `build_OpenMC888_889.py` contiene il sorgente completo leggibile (JS dentro la raw string Python). Per rigenerare il `.txt` dopo modifiche: `python3 build_OpenMC888_889.py > OpenMC888_889.bookmarklet.txt`

---

## 📁 Struttura del Progetto

```
OpenMC888-889-Alpha-/
├── OpenMC888_889.bookmarklet.txt    # 📋 Bookmarklet pronto da copiare nel browser
├── build_OpenMC888_889.py           # ⭐ Sorgente completo + build script (Python)
├── RIFERIMENTI.md                   # 📚 Riferimento rapido variabili, API, goformId
├── README.md                        # Questo file
```

---

## 🔬 Come Funziona (Note Tecniche)

Lo script si inietta nella WebGUI originale del modem (già autenticata) e comunica con gli endpoint **goform** del firmware ZTE:

- **Lettura:** `GET /goform/goform_get_cmd_process?cmd=campo1,campo2,...&multi_data=1` → risposta JSON
- **Scrittura:** `POST /goform/goform_set_cmd_process` con `goformId` + token `AD`

Il token `AD` si calcola tramite `cookWithRequest()`, funzione già presente nella pagina del modem — non viene replicata ma chiamata direttamente.

Non viene aperta nessuna connessione di rete esterna. **Tutto avviene in locale**, sulla rete LAN/WiFi del modem.

---

## 🤝 Contributi

Il progetto è aperto a contributi! Se hai un firmware diverso, hai testato su MC889, o riesci a sbloccare funzioni non ancora implementate, apri una **Issue** o una **Pull Request**.

Il file `RIFERIMENTI.md` contiene tutte le variabili goform, i goformId e le strutture payload — pensato appositamente per chi vuole estendere lo script.

---

## 🙏 Crediti, Sorgenti e Ringraziamenti

Questo progetto non sarebbe nato senza il lavoro di **miononno**, che ha sviluppato e reso pubblico lo script **[Link del video originale](https://www.youtube.com/watch?v=Pb0FkrpshXc)** — il bookmark originale per il controllo avanzato dei modem ZTE MC888/889. Il reverse engineering delle API goform, la logica del polling e l'identificazione di tutti i `goformId` provengono dal suo script e da [FibraClick](https://forum.fibra.click/) (Purtroppo non ho la lista degli utenti singoli mi dispiace).

> Il codice di questo progetto è stato scritto in modo indipendente, adattando e ampliando il lavoro originale con una UI grafica moderna. Il **metodo**, le **API** e la **comprensione del funzionamento** vengono dal suo contributo e dagli utenti di Fibraclick.

📺 **[Canale YouTube di miononno](https://www.youtube.com/@miononno)** — *Grazie di cuore!*

Grazie anche alla community di **[FibraForum](https://www.fibraforum.it/)** per le discussioni tecniche sui modem FWA, i test sui firmware operatore e la condivisione di informazioni sulle API ZTE.

---

<div align="center">

Made with ❤️ by **[mix_max111](https://github.com/mixmax111)**

*Progetto non affiliato con ZTE, WindTre, TIM o qualsiasi altro operatore.*

*Script originale by **miononno** — utilizzato come base di riferimento e ispirazione.*

</div>

