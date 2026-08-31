# 📚 OpenMc888 — Riferimenti Tecnici

> Documentazione di riferimento pensata per permettere a chiunque di personalizzare,
> estendere o modificare lo script. Trovi qui tutte le variabili goform, i goformId,
> le strutture dei payload e le note di parsing essenziali.
>
> **Sorgenti:** script `888.js` originale di *miononno* · GUI `OpenMF258A01.js` · reverse engineering by *mix_max111*
> **Ringraziamenti:** miononno · community FibraForum

---

## 1 · Endpoint API Goform

| Endpoint | Metodo | Uso |
|---|---|---|
| `/goform/goform_get_cmd_process` | `GET` | Lettura parametri modem |
| `/goform/goform_set_cmd_process` | `POST` | Scrittura / esecuzione comandi |

**Parametri GET obbligatori:**
```
cmd=campo1,campo2,...   (lista campi separati da virgola)
multi_data=1            (obbligatorio per risposta JSON multipla)
```

---

## 2 · Variabili Goform — Lettura (GET)

### 2.1 · Segnale LTE

| Campo | Tipo | Note |
|---|---|---|
| `lte_rsrp` | `string` (int) | RSRP LTE in dBm. Scala: -130 → -60 |
| `lte_rsrq` | `string` (int) | RSRQ LTE in dB. Scala: -16 → -3 |
| `lte_snr` | `string` (int) | SINR LTE in dB. Scala: 0 → 24 |
| `lte_rssi` | `string` (int) | RSSI LTE in dBm |
| `lte_pci` | `string` (hex) | PCI cella LTE — **convertire con** `parseInt(val, 16)` |
| `lte_pci_lock` | `string` | PCI attualmente in lock (vuoto = nessun lock) |
| `lte_earfcn_lock` | `string` | EARFCN attualmente in lock |
| `wan_active_channel` | `string` | EARFCN della banda principale |
| `wan_active_band` | `string` | Banda principale (es. `"B3"`) |

### 2.2 · Segnale 5G NR

| Campo | Tipo | Note |
|---|---|---|
| `Z5g_rsrp` | `string` (int) | RSRP NR5G in dBm. Scala: -130 → -60 |
| `Z5g_SINR` | `string` (int) | SINR NR5G in dB. Scala: 0 → 24 |
| `nr5g_pci` | `string` (hex) | PCI NR5G — **convertire con** `parseInt(val, 16)` |
| `nr5g_action_band` | `string` | Banda NR5G agganciata (es. `"n78"`). Vuoto = no 5G |
| `nr5g_action_channel` | `string` | EARFCN NR5G |

> **Visibilità NR5G:** mostrare il blocco 5G solo se `nr5g_action_band !== ""`

### 2.3 · Carrier Aggregation

| Campo | Tipo | Note |
|---|---|---|
| `wan_lte_ca` | `string` | `"ca_activated"` se CA attiva, altrimenti vuoto |
| `lte_ca_pcell_band` | `string` | Numero banda PCell (es. `"3"`) |
| `lte_ca_pcell_bandwidth` | `string` | Larghezza PCell in MHz (es. `"20"`) |
| `lte_ca_scell_band` | `string` | Banda SCell (single CA) |
| `lte_ca_scell_bandwidth` | `string` | Larghezza SCell (single CA) |
| `lte_ca_pcell_arfcn` | `string` | ARFCN PCell |
| `lte_ca_scell_arfcn` | `string` | ARFCN SCell |
| `lte_multi_ca_scell_info` | `string` | Tutte le SCell (multi-CA) — vedere §2.3.1 |

#### 2.3.1 · Parse `lte_multi_ca_scell_info`

Formato raw: `pci,earfcn,?,band,earfcn2,bw;pci,earfcn,...;`

```javascript
var scells = d.lte_multi_ca_scell_info.slice(0, -1).split(";");
for (var i = 0; i < scells.length; i++) {
    var p = scells[i].split(",");
    var pci  = p[1];  // indice 1
    var band = p[3];  // indice 3
    var bw   = p[5];  // indice 5 — larghezza in MHz
}
```

### 2.4 · Cella e Rete

| Campo | Tipo | Note |
|---|---|---|
| `cell_id` | `string` (hex) | Cell ID globale — **convertire con** `parseInt(val, 16)` |
| `network_type` | `string` | Tipo rete (es. `"LTE"`, `"NR"`) |
| `rmcc` | `string` | MCC operatore (es. `"222"`) |
| `rmnc` | `string` | MNC operatore (es. `"88"`) |

#### 2.4.1 · Calcolo ENB ID e link LTEItaly

```javascript
var cellDec = parseInt(d.cell_id, 16);
var enbId   = Math.trunc(cellDec / 256);
var plmn    = d.rmcc + d.rmnc;

// Mapping PLMN italiani
if (plmn === "22201") plmn = "2221";   // TIM
if (plmn === "22299") plmn = "22288";  // WindTre (ex H3G)
if (plmn === "22250" && enbId.toString().length === 6) plmn = "22288"; // MVNO su WindTre

var link = "https://lteitaly.it/internal/map.php#bts=" + plmn + "." + enbId;
```

### 2.5 · Connessione e APN

| Campo | Tipo | Note |
|---|---|---|
| `wan_ipaddr` | `string` | IP WAN pubblico |
| `static_wan_ipaddr` | `string` | IP WAN statico (se configurato) |
| `wan_apn` | `string` | APN correntemente attivo |
| `ppp_status` | `string` | Stato connessione PPP |
| `dns_mode` | `string` | `"manual"` o `"auto"` |
| `prefer_dns_manual` | `string` | DNS primario (se manual) |
| `standby_dns_manual` | `string` | DNS secondario (se manual) |

### 2.6 · Temperature e Stato

| Campo | Tipo | Note |
|---|---|---|
| `pm_sensor_mdm` | `string` | Temperatura modulo 4G in °C |
| `pm_modem_5g` | `string` | Temperatura modulo 5G in °C |
| `loginfo` | `string` | Log interno firmware |
| `opms_wan_mode` | `string` | Modalità WAN |

---

## 3 · GoformId — Scrittura (POST)

### Pattern comune per tutte le chiamate POST

```javascript
// Step 1: Recupera seed per token AD
$.ajax({
    type: "GET",
    url: "/goform/goform_get_cmd_process",
    data: { cmd: "wa_inner_version,cr_version,RD", multi_data: "1" },
    dataType: "json",
    success: function(data) {
        // Step 2: Calcola token (funzione già nella pagina del modem)
        var ad = cookWithRequest(
            cookWithRequest(data.wa_inner_version + data.cr_version) + data.RD
        );
        // Step 3: POST con token
        $.ajax({
            type: "POST",
            url: "/goform/goform_set_cmd_process",
            data: { isTest: "false", goformId: "...", /* payload */, AD: ad }
        });
    }
});
```

---

### 3.1 · `LTE_LOCK_CELL_SET` — Cell Lock

```javascript
{
    isTest:          "false",
    goformId:        "LTE_LOCK_CELL_SET",
    lte_pci_lock:    "116",   // PCI intero decimale (non hex)
    lte_earfcn_lock: "3350",  // EARFCN
    AD:              ad
}
```

> ⚠️ Per rimuovere il lock è necessario il RESET di fabbrica del router.

---

### 3.2 · `BAND_SELECT` — Selezione Bande LTE

```javascript
{
    isTest:       "false",
    goformId:     "BAND_SELECT",
    is_gw_band:   0,
    gw_band_mask: 0,
    is_lte_band:  1,
    lte_band_mask: "0x80084",  // bitmask hex — AUTO = "0xA3E2AB0908DF"
    AD:           ad
}
```

**Calcolo bitmask:**
```javascript
var sum = 0;
["1", "3", "20"].forEach(function(b) { sum += Math.pow(2, parseInt(b) - 1); });
var mask = "0x" + sum.toString(16);
```

**Maschera AUTO (tutte le bande supportate mczte/889):**
```
0xA3E2AB0908DF
```

---

### 3.3 · `WAN_PERFORM_NR5G_BAND_LOCK` — Selezione Bande 5G NR

> ⚠️ **5G NR usa CSV** — diverso dalla bitmask hex usata per LTE!

```javascript
{
    isTest:        "false",
    goformId:      "WAN_PERFORM_NR5G_BAND_LOCK",
    nr5g_band_mask: "3,78",  // CSV — AUTO = tutte le bande sotto
    AD:            ad
}
```

**Valore AUTO (tutte le bande NR):**
```
1,2,3,5,7,8,20,28,38,41,50,51,66,70,71,74,75,76,77,78,79,80,81,82,83,84
```

---

### 3.4 · `APN_PROC_EX` — DNS / APN (doppia chiamata)

**Chiamata 1 — Salva profilo APN con DNS:**
```javascript
{
    isTest:              "false",
    goformId:            "APN_PROC_EX",
    wan_apn:             "internet.wind",  // APN corrente (preservare!)
    profile_name:        "NomeProfilo",
    apn_action:          "save",
    apn_mode:            "manual",
    pdp_type:            "IP",
    dns_mode:            "manual",         // oppure "auto"
    prefer_dns_manual:   "1.1.1.1",
    standby_dns_manual:  "1.0.0.1",
    index:               1,
    AD:                  ad
}
```

**Chiamata 2 — Imposta come profilo predefinito:**
```javascript
{
    isTest:           "false",
    goformId:         "APN_PROC_EX",
    apn_mode:         "manual",
    apn_action:       "set_default",
    set_default_flag: 1,
    pdp_type:         "IP",
    pdp_type_roaming: "IP",
    index:            1,
    AD:               ad
}
```

---

### 3.5 · `REBOOT_DEVICE` — Riavvio

```javascript
{
    isTest:   "false",
    goformId: "REBOOT_DEVICE",
    AD:       ad
}
```

---

## 4 · Campi per Token AD (sempre richiesti prima di ogni POST)

| Campo | Descrizione |
|---|---|
| `wa_inner_version` | Versione interna firmware WA |
| `cr_version` | CR version |
| `RD` | Seed random per token |
| `hardware_version` | Versione hardware (solo per info, non per token) |
| `web_version` | Versione WebUI (solo per info) |

---

## 5 · Funzioni JavaScript del Modem (già presenti nella pagina)

| Funzione | Disponibilità | Uso |
|---|---|---|
| `cookWithRequest(str)` | mczte / MC889 | Calcola token AD — **non replicare, chiamare direttamente** |

> Le funzioni OAM (`GetOamMidNodeFromServer`, `SetOamMidNodeToServer` ecc.) sono presenti **solo** nel MF258A e **non** nel mczte/889.

---

## 6 · Parsing Esadecimale — Riepilogo

| Campo goform | Conversione necessaria |
|---|---|
| `lte_pci` | `parseInt(val, 16)` → PCI decimale |
| `nr5g_pci` | `parseInt(val, 16)` → PCI NR decimale |
| `cell_id` | `parseInt(val, 16)` → Cell ID decimale → `/256` per ENB ID |

---

## 7 · Bar-Graph SVG — Parametri

| Metrica | Min | Max | ID DOM sorgente | ID DOM grafico |
|---|---|---|---|---|
| LTE RSRP | -130 | -60 | `lte_rsrp` | `#m8_brsrp` |
| LTE RSRQ | -16 | -3 | `lte_rsrq` | `#m8_brsrq` |
| LTE SINR | 0 | 24 | `lte_snr` | `#m8_bsinr` |
| NR RSRP | -130 | -60 | `Z5g_rsrp` | `#m8_bnr5rsrp` |
| NR SINR | 0 | 24 | `Z5g_SINR` | `#m8_bnr5sinr` |

**Scala colori barre:**
```
< 50%  → giallo  (#facc15)
50–84% → verde   (#10b981)
≥ 85%  → arancio (#fb923c)
```

**Dimensioni grafici mini:** `GW=500px · GH=30px · GT=3px (spessore barra)`

### 7.1 · Grafici Timeline SVG (Modal Statistiche Dettagliate)

Metodo: `Openmczte.drawDetailChart(targetId, key, minScale, maxScale, title, unit, color)`

- **Buffer storico:** `Openmczte.history[key]` (array fino a 125 campioni, ~3 minuti di campionamento)
- **Rendering:** SVG `viewBox="0 0 550 85"` con tracciato sfumato `<path>` + linea continua `<polyline>`
- **Metriche calcolate in tempo reale:**
  - **Attuale:** `hist[0]` (ultimo valore registrato)
  - **Minimo:** `Math.min(...hist)`
  - **Massimo:** `Math.max(...hist)`
  - **Media:** `(sum / hist.length).toFixed(1)`

---

## 8 · AlignWizard — Score Formula

```javascript
score = rsrp + (sinr * 2)
// Più alto = migliore. Baseline: rsrp=-140, sinr=-20 → score=-180
```

---

<div align="center">

📡 **OpenMc888-889** — by **[mix_max111](https://github.com/mixmax111)**

Script originale `888.js` by **miononno** · Ispirazione e discussioni: **[FibraForum](https://www.fibraforum.it/)**

*Documentazione pensata per essere accessibile a tutti — modifica, forka, migliora.*

</div>

