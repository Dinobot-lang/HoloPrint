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

### 6.5 Buco di 15 minuti nei dati
Tra le 22:56:54 e le 23:11:35 il log non contiene righe, poi il messaggio successivo mostra ancora layer 31 e subito dopo layer 192. Possibili cause: il PC si è sospeso o ha perso il Wi-Fi (segnale della stampante -68 dBm), oppure messaggi non arrivati. Il log registra solo i cambiamenti, quindi un periodo senza righe non si distingue da una caduta di connessione.
**Conseguenza di progetto:** l'app deve conservare l'istante dell'ultimo messaggio, mostrare "dati non aggiornati" se passano più di ~10 s e disabilitare i controlli finché la connessione non torna.

### 6.6 Stati ancora da rilevare
Il log si chiude con `gcode_state` ancora `RUNNING` (layer 192/192, 99%, tempo residuo 0). Non abbiamo visto **fine stampa**, **pausa** e **errore**: vanno catturati nel prossimo test.
