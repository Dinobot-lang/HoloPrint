# 04 – Riferimento protocollo Bambu Lab (LAN)

> Il protocollo locale è stato ricostruito dalla community e **non è supportato ufficialmente** da Bambu Lab. Verifica sempre sul tuo modello/firmware. Riferimento comunitario principale: progetto **OpenBambuAPI** (vedi `05-fonti.md`). I punti marcati ⚠️ sono da confermare sul tuo hardware.

## 1. Prerequisiti sulla stampante
- LAN-only Mode **ON** e Developer Mode **ON** (sul firmware recente senza Developer Mode le scritture di terze parti sono bloccate).
- Dati necessari: IP, **access code** (display → impostazioni WLAN), **numero di serie**.

## 2. Servizi esposti

| Servizio | Porta | Note |
|----------|-------|------|
| MQTT (TLS) | 8883 | utente `bblp`, password = access code, certificato autofirmato |
| Camera MJPEG (TLS) | 6000 | tipica P1/A1; autenticazione con pacchetto binario |
| Camera RTSPS | 322 | tipica X1; URL `rtsps://bblp:<access_code>@<ip>:322/streaming/live/1` |
| FTPS | 990 | file su scheda SD |

## 3. MQTT

- Lettura: topic `device/<seriale>/report`
- Scrittura: topic `device/<seriale>/request`
- Richiesta stato completo: `{"pushing":{"sequence_id":"0","command":"pushall"}}`
- Alcuni modelli (serie P1) inviano nei report **solo i valori cambiati**: mantenere una cache e filtrare i messaggi parziali (un messaggio completo contiene `gcode_state`).
- Limite connessioni contemporanee: circa 4 su P1/X1, una su A1 → chiudere altri client (Home Assistant, ecc.) durante i test, oppure usare un proxy/gateway.

### Campi di stato di interesse ⚠️ (nomi usati dalla community, verificare)
`gcode_state`, `mc_percent`, `mc_remaining_time`, `layer_num`, `total_layer_num`, `nozzle_temper`, `nozzle_target_temper`, `bed_temper`, `bed_target_temper`, `spd_lvl`, `subtask_name`, struttura `ams`, codici errore/HMS.

### Comandi tipici ⚠️ (formato indicativo, verificare su OpenBambuAPI)
```json
{"print":{"sequence_id":"0","command":"pause"}}
{"print":{"sequence_id":"0","command":"resume"}}
{"print":{"sequence_id":"0","command":"stop"}}
{"print":{"sequence_id":"0","command":"print_speed","param":"2"}}
{"system":{"sequence_id":"0","command":"ledctrl","led_node":"chamber_light","led_mode":"on","led_on_time":500,"led_off_time":500,"loop_times":0,"interval_time":0}}
```
Il comando `gcode_line` esiste ma **non va esposto nella v1**.

## 4. Camera MJPEG su porta 6000 (riassunto dal lavoro della community)
Connessione TLS (verifica certificato disattivata), invio di un pacchetto di autenticazione di 80 byte (tipo e dimensione in little-endian, utente `bblp` e access code in posizioni fisse), poi lettura ripetuta di intestazioni da 16 byte seguite dai dati JPEG. Dettagli esatti in OpenBambuAPI.

## 5. Regole di sicurezza
1. **Mai** pubblicare access code, seriale o IP nel repository.
2. Stampante su rete domestica protetta o VLAN dedicata; nessuna esposizione a internet.
3. Con Developer Mode la responsabilità della sicurezza di rete è tua.
4. Validare ogni comando prima dell'invio (stato ammesso, range, frequenza).
5. Nessun bypass delle protezioni del firmware: usare solo il percorso Developer Mode.
6. Registrare localmente i comandi inviati.
7. Rispettare i termini di servizio di Bambu Lab, soprattutto se in futuro si usasse il cloud.
