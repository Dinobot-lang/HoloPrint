# 06 – Mappa dei campi reali (dump di stato e log di stampa, ottobre 2026)

Ricavata dal primo dump MQTT ottenuto dalla stampante di prova (stato **IDLE**, con AMS collegato).
Il dump originale **non va committato** (contiene seriale, IP e UID delle bobine): è escluso dal `.gitignore`.

## 1. Modello

Stampante: **Bambu Lab X2D** (confermato dal proprietario). Il dump è coerente con una macchina a **doppio estrusore** (due voci in `device.extruder.info` e `device.nozzle.info`), con `ventobox`, `airduct` e predisposizioni laser/quarto asse.

Note specifiche per l'X2D:
- Nel menu della stampante la voce LAN Only si trova nelle impostazioni, ma il wiki ufficiale per questo modello è ancora poco documentato; l'ultimo menu coincide con quello degli altri modelli recenti.
- Un utente del forum Bambu Lab segnalava di non essere sicuro che l'X2D offrisse Developer Mode. Nel nostro caso la **lettura MQTT funziona**; resta da verificare con un comando di prova (es. luce camera) che anche la **scrittura** sia accettata.
- In LAN Only non arrivano aggiornamenti firmware automatici: tenere traccia della versione installata.

## 2. Campi utili per l'interfaccia

Legenda: ✅ presente nel dump · ⚠️ significato da confermare durante una stampa

| Dato da mostrare | Campo | Esempio nel dump | Note |
|------------------|-------|------------------|------|
| Stato | `gcode_state` | `"IDLE"`, `"RUNNING"` | ✅ campo. Visti: IDLE, RUNNING. Pausa/fine/errore ⚠️ da rilevare |
| Nome lavoro | `subtask_name` | `"3D Benchy by CreativeTools"` | ✅ |
| Avanzamento % | `mc_percent` (anche `percent`) | `27` → `99` | ✅ ma **non coincide con i layer** (vedi §6) |
| Tempo residuo | `mc_remaining_time` (anche `remain_time`) | `16` → `13` | ✅ **minuti** (confermato in stampa) |
| Layer | `layer_num` / `total_layer_num` | `31` / `192` | ✅ |
| Temp. ugello (generale) | `nozzle_temper` / `nozzle_target_temper` | `31.0` / `0.0` | ✅ |
| Temp. per estrusore | `device.extruder.info[i].temp` (i = 0, 1) | `38`, `14418137` | ✅ valore **codificato**: vedi §6 |
| Diametro / tipo ugello | `nozzle_diameter`, `device.nozzle.info[i].diameter`, `.type` | `0.4`, `HS01` | ✅ |
| Temp. piano | `bed_temper` / `bed_target_temper` | `27.0` / `0.0` | ✅ |
| Temp. camera | `device.ctc.info.temp` | `27` → `32` | ✅ sale durante la stampa, coerente con la camera; da confrontare con il display |
| Velocità | `spd_lvl` (livello), `spd_mag` (%) | `2`, `100` | ✅ campi · ⚠️ mappa livello→nome |
| Luci | `lights_report[]` (`node`, `mode`) | `chamber_light: on`, `work_light: flashing` | ✅ |
| Errori | `print_error`, `mc_print_error_code`, `err`, `hms[]` | `0`, `[]` | ✅ campi |
| Segnale Wi-Fi | `wifi_signal` | `"-68dBm"` | ✅ (segnale non ottimo) |
| Camera | `ipcam.rtsp_url`, `ipcam.resolution` | `rtsps://<ip>:322/streaming/live/1`, `1080p` | ✅ **RTSPS, non MJPEG** |
| Ispezione AI | `xcam.*` (spaghetti_detector, first_layer_inspector…) | tutti attivi | ✅ |

## 3. AMS (filamenti)

Percorso: `ams.ams[0].tray[0..3]`.

| Dato | Campo | Note |
|------|-------|------|
| Colore | `tray_color` | formato RRGGBBAA (es. `5F6367FF`) |
| Materiale | `tray_type`, `tray_sub_brands` | es. PLA / "PLA Silk+", ABS |
| Residuo | `remain` | percentuale; `-1` = sconosciuto (bobina non Bambu) |
| Range temp. | `nozzle_temp_min` / `nozzle_temp_max` | |
| Bobina originale | `tag_uid` ≠ zeri | RFID riconosciuto |
| Umidità | `ams.ams[0].humidity` (indice 1–5), `humidity_raw` | |
| Temperatura AMS | `ams.ams[0].temp` | |
| Slot attivo | `ams.tray_now` | `255` = nessuno |
| Presenza slot | `ams.tray_exist_bits` | maschera di bit |
| Bobina esterna | `vir_slot[]` | slot esterno |

Nel dump: 1 AMS con 4 slot (PLA Silk+ grigio 75%, ABS nero 58%, due slot PLA generici senza dati di residuo).

## 4. Decisioni che cambiano per questo modello

1. **Video:** la stampante espone solo **RTSPS (porta 322)**. Unity su Quest non lo riproduce direttamente → per la Fase 6 serve un **gateway** (PC/Raspberry con ffmpeg) che lo converta in MJPEG/WebRTC. Il gateway passa da "opzionale" a **necessario per il video**.
2. **Dati a due ugelli:** il modello dati (`PrinterState`) deve prevedere una **lista di estrusori**, non un solo ugello.
3. **Messaggi:** `pushall` restituisce lo stato completo; i report successivi possono essere parziali → mantenere la cache unita con fusione ricorsiva (già fatto nello script).

## 5. Da completare

- [ ] Secondo dump **durante una stampa breve** per confermare avanzamento, layer, tempo residuo, nome lavoro, stati.
- [ ] Rilevare i valori di `gcode_state` (pausa, fine, errore).
- [ ] Confermare la mappa `spd_lvl` → profilo velocità cambiandolo dal display.
- [ ] Confermare quale sensore è la temperatura della camera.
- [ ] Testare un comando innocuo (luce camera) e osservare la variazione in `lights_report`.


## 6. Scoperte dal log di stampa (Benchy, 192 layer)

### 6.1 Temperatura degli estrusori: valore codificato
Su questo modello `device.extruder.info[i].temp` contiene **due valori in uno**:

```python
def split_temp(v):
    v = int(v)
    return v & 0xFFFF, v >> 16      # (attuale, obiettivo)

split_temp(38)        # (38, 0)     -> ugello inattivo, a 38 °C
split_temp(14418137)  # (217, 220)  -> ugello attivo a 217 °C, obiettivo 220 °C
```

Verificato sul log: il valore decodificato (attuale) coincide con `nozzle_temper` di primo livello. Il campo `nozzle_temper` / `nozzle_target_temper` riguarda quindi **l'ugello attivo**; per mostrare entrambi gli ugelli si decodifica `extruder.info[i].temp`. Nel log l'estrusore con indice 1 era quello in uso.

### 6.2 Avanzamento e layer sono indipendenti
All'inizio del log `mc_percent` era già 27 con `layer_num` = 1 su 192. La percentuale **include le fasi preparatorie** (riscaldamento, calibrazioni) e non è layer/totale. Nell'interfaccia: mostrare la percentuale ufficiale e i layer come due dati separati, senza calcolare l'uno dall'altro.

### 6.3 Tempo residuo in minuti
`mc_remaining_time` scende di 1 ogni circa 60–70 secondi (16 → 13 in tre minuti): l'unità è **minuti**.

### 6.4 Velocità
`spd_lvl` è rimasto 2 per tutta la stampa e `spd_mag` 100. A fine lavoro `spd_lvl` è tornato a 0. Mappa livello → profilo **non ancora verificata** (nessun cambio manuale di velocità nel log).

### 6.5 Buchi nei dati: tre tipi diversi
Il log registra **solo i cambiamenti**, quindi un'assenza di righe può voler dire cose diverse.

| Tipo | Esempio | Spiegazione |
|------|---------|-------------|
| Buchi brevi (1–35 s) | 22:52:49 → 22:53:24 | Normale: la stampante invia solo ciò che cambia. In quel tratto (calibrazione) nessun campo tracciato variava. |
| Buco di ~15 min | 22:56:54 → 23:11:35 | **Dati non ricevuti dal PC.** La prima riga dopo il buco è ancora "layer 31" e 3 secondi dopo il layer è 192: 161 layer in 3 s sono impossibili, quindi il tratto intermedio è andato perso. |
| Buco di ~4 ore | 23:17:07 → 03:13:44 | Come sopra: riga con ugello a 101 °C e un secondo dopo 30 °C. La stampante si è raffreddata mentre il PC non riceveva, e le temperature cambiano di continuo, quindi la stampante stava inviando dati. |
| Buco di ~4 ore e 20 | 03:13:45 → 07:32:37 | **Ambiguo:** a stampante fredda e ferma i cambiamenti sono rari (1 °C ogni tanto). Può essere silenzio reale o PC sospeso. |

Causa più probabile dei due buchi certi: **sospensione del PC (sleep) o perdita del Wi-Fi**. I messaggi inviati dalla stampante mentre nessuno ascolta non vengono conservati. Da verificare con la cronologia di sospensione di Windows (Visualizzatore eventi → Sistema → Power-Troubleshooter).

**Conseguenze di progetto (valide anche per il visore, che si sospende quando viene tolto):**
1. Dopo ogni (ri)connessione o ripresa: inviare **`pushall`** e considerare i primi messaggi **non attendibili** finché non arriva la risposta.
2. Registrare l'istante dell'ultimo messaggio ricevuto e mostrare **"dati non aggiornati"** oltre una soglia.
3. Il silenzio non basta come segnale di connessione persa (a macchina ferma la stampante tace): serve un **heartbeat**, cioè un `pushall` periodico (es. ogni 30 s, frequenza da testare) e il controllo che arrivi sempre una risposta.
4. Gestire e registrare gli eventi di disconnessione del client MQTT.

### 6.6 Ciclo di vita di una stampa (osservato)
| Ora | Stato | Evento |
|-----|-------|--------|
| 22:47:14 | `IDLE` → `PREPARE` | avvio dal display/Studio, nome lavoro compare |
| 22:47:16 | `RUNNING` | `total_layer_num` = 192, `layer_num` = 0 |
| 22:47:18 | | tempo residuo 22 min, piano obiettivo 55 °C |
| 22:48:45–22:50 | | l'estrusore 1 viene portato a vari obiettivi (140–250 °C): pre-riscaldamenti/pulizia |
| 22:52:17 → 22:53:24 | | avanzamento 6% → 27% (fase preparatoria: calibrazioni) |
| 22:53:34 | | l'ugello "attivo" passa dall'estrusore 0 al 1: `nozzle_temper` prima seguiva l'estrusore 0, poi l'1 |
| 22:53:51 | | `layer_num` = 1 |
| 23:11:38 | | layer 192/192, 99%, residuo 0, `spd_lvl` = 0 |
| 23:14:42 | `FINISH` | 100%, obiettivi a 0, `spd_lvl` torna 2 |

Stati osservati: **IDLE, PREPARE, RUNNING, FINISH**. Ancora da rilevare: pausa e errore.

Nota: `nozzle_temper` / `nozzle_target_temper` seguono l'**estrusore attivo**, che può cambiare durante il lavoro: per mostrare sempre entrambi gli ugelli usare `device.extruder.info[i].temp` decodificato (§6.1).
