# 03 – Sviluppo e roadmap

## 1. Ambiente di sviluppo

| Strumento | Note |
|-----------|------|
| Unity 6 (6000.0.38f1 o successivo) + modulo Android | Versione minima indicata dagli esempi Meta |
| Meta XR All-in-One SDK + **MRUK** (v81 o superiore) | Include Passthrough Camera Access, QR, ancore |
| Unity Inference Engine (v2.2.1 per l'esempio YOLO) | Solo se userai il riconoscimento ML |
| Meta Quest Developer Hub (MQDH) | Installazione APK, log, screenshot |
| Python 3 + `paho-mqtt` | Prototipo di fase 1 |
| Git + GitHub (repo privato) | Documentazione e codice |
| Bambu Studio | Per leggere access code e seriale |

Esempi ufficiali da clonare come riferimento: **Unity-PassthroughCameraApiSamples** (camera, object detection) e il sample **QRCodeDetection** di MRUK.

## 2. Roadmap per fasi

### Fase 0 – Verifiche e setup (2–4 giorni)
- [ ] Individuare modello esatto e versione firmware della stampante.
- [ ] Attivare **LAN-only + Developer Mode** sul display (il menu varia per modello: A1 in Impostazioni → WLAN, X1/H2/P2 in Impostazioni → LAN Mode). Al primo attivo di LAN-only riavviare la stampante.
- [ ] Annotare IP, **access code** e **seriale** (solo in file locale).
- [ ] Impostare IP fisso/riserva DHCP per la stampante.
- [ ] Creare account sviluppatore Meta e attivare modalità sviluppatore sul Quest.
- [ ] Creare il repo GitHub privato e caricare questa documentazione.

**Criterio di uscita:** la stampante risponde in LAN e il visore è installabile da MQDH.

### Fase 1 – Prototipo Python, sola lettura (2–3 giorni)
Obiettivo: vedere in console i dati live. Se non funziona qui, inutile procedere.

```python
# prototype-python/read_status.py  (esempio minimale, da adattare)
import json, ssl, os
import paho.mqtt.client as mqtt

HOST   = os.environ["BAMBU_IP"]
SERIAL = os.environ["BAMBU_SERIAL"]
CODE   = os.environ["BAMBU_ACCESS_CODE"]

def on_connect(client, userdata, flags, reason_code, properties):
    client.subscribe(f"device/{SERIAL}/report")
    # chiede lo stato completo
    client.publish(f"device/{SERIAL}/request",
        json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}}))

def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    print(json.dumps(data.get("print", data), indent=2)[:1500])

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv311)
c.username_pw_set("bblp", CODE)
c.tls_set(cert_reqs=ssl.CERT_NONE)
c.tls_insecure_set(True)          # certificato autofirmato della stampante
c.on_connect, c.on_message = on_connect, on_message
c.connect(HOST, 8883, keepalive=60)
c.loop_forever()
```

**Criterio di uscita:** vedi temperature, progresso e stato aggiornarsi. Documenta in `04-protocollo-bambu.md` i campi che il **tuo** modello invia davvero.

### Fase 2 – App Quest minima (3–5 giorni)
- [ ] Progetto Unity con Camera Rig + Passthrough (Building Blocks Meta).
- [ ] Build e installazione su Quest via MQDH.
- [ ] Pannello di prova con testo statico in mixed reality.

**Uscita:** vedi un pannello fluttuante sopra l'ambiente reale.

### Fase 3 – Dati live nel visore (1–2 settimane)
- [ ] `IPrinterService` + `BambuMqttService` con MQTTnet (TLS, `bblp`, access code).
- [ ] Parser dello stato: gestire il fatto che alcuni modelli inviano solo i campi cambiati → mantenere una **cache di stato** e rinviare `pushall` a ogni (ri)connessione.
- [ ] Riconnessione automatica con backoff.
- [ ] `StatusPanel` con progresso, temperature, tempo residuo, stato, AMS.
- [ ] Schermata di configurazione (IP, seriale, access code) salvata solo sul visore.

**Uscita:** i dati reali della stampante compaiono nel visore.

### Fase 4 – Riconoscimento e ancoraggio (1 settimana)
- [ ] Abilitare QR Code Tracking in MRUK; richiedere Spatial Data.
- [ ] Alla lettura del QR: creare e salvare `OVRSpatialAnchor`.
- [ ] Ricaricare l'ancora all'avvio; fallback con posizionamento manuale.
- [ ] Associare payload QR → configurazione stampante.

**Uscita:** il pannello appare sempre accanto alla stampante, anche dopo il riavvio dell'app.

### Fase 5 – Controlli con sicurezza (1–2 settimane)
Ordine consigliato, dal più innocuo al più delicato:
1. Luce camera.
2. Profilo di velocità.
3. Pausa / Riprendi.
4. Stop (con conferma forte).
5. Temperature (slider con limiti, conferma).

- [ ] `CommandValidator` (range e stati ammessi: es. "riprendi" solo se in pausa).
- [ ] `RateLimiter` per evitare raffiche di comandi.
- [ ] Feedback visivo: "inviato" → "confermato" confrontando il nuovo stato ricevuto.
- [ ] Log locale di tutti i comandi inviati.

**Uscita:** ogni comando ha effetto reale ed è sempre confermato dallo stato letto.

### Fase 6 – Video camera (1 settimana, opzionale)
- P1/A1: stream MJPEG su TLS porta 6000 con pacchetto di autenticazione (vedi doc protocollo).
- X1: stream RTSPS porta 322 → di norma conviene un **gateway** che lo trasforma in MJPEG/WebRTC per Quest.
- Mostrare il video in una finestra fluttuante separata.

### Fase 7 – Extra (aperta)
- Riconoscimento ML personalizzato.
- Più stampanti.
- Notifiche (fine stampa, errore HMS) con audio spaziale.
- Cronologia stampe, grafici temperature.

## 3. Strategia di test

| Livello | Cosa si verifica |
|---------|------------------|
| Unit test (C#/Python) | Parser dello stato, builder dei comandi, validatore |
| Simulatore | Un finto broker MQTT con messaggi registrati, per sviluppare senza stampare |
| Su stampante, a vuoto | Luce, velocità, pausa con stampante ferma o con stampa di prova economica |
| Su visore | Tracking QR in varie condizioni di luce, ricarica ancora, prestazioni (fps), temperatura visore |
| Rete | Caduta Wi-Fi, riavvio stampante, due client connessi insieme |

**Regola d'oro:** mai testare comandi di temperatura/stop su stampe di valore finché la catena "comando → conferma" non è collaudata.

## 4. Backlog iniziale (issue GitHub)

1. Verificare Developer Mode e firmware sul proprio modello
2. Prototipo Python di lettura
3. Documentare i campi reali del `report`
4. Progetto Unity + passthrough
5. Servizio MQTT in Unity (TLS autofirmato)
6. Pannello stato
7. QR + ancora persistente
8. Comandi base (luce, velocità)
9. Pausa/riprendi/stop con conferma
10. Camera video
11. Gateway opzionale
12. Test su perdita di rete

##TEST
** Codice per il test aggiornato(se il primo non funziona usate questo):
```python
import json, ssl
import paho.mqtt.client as mqtt

HOST   = "192.168.1.77"
SERIAL = "20P5BJ661500193"
CODE   = "8582B62F"

state = {}

def merge(dst, src):
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            merge(dst[k], v)
        else:
            dst[k] = v

KEYS = ["gcode_state", "subtask_name", "mc_percent", "mc_remaining_time",
        "layer_num", "total_layer_num", "nozzle_temper", "nozzle_target_temper",
        "bed_temper", "bed_target_temper", "chamber_temper", "spd_lvl"]

def on_connect(client, userdata, flags, reason_code, properties):
    print("Connessione:", reason_code)
    client.subscribe(f"device/{SERIAL}/report")
    client.publish(f"device/{SERIAL}/request",
        json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}}))

def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    if "print" in data:
        merge(state, data["print"])
        with open("status_dump.json", "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        riepilogo = {k: state[k] for k in KEYS if k in state}
        print(riepilogo)

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv311)
c.username_pw_set("bblp", CODE)
c.tls_set(cert_reqs=ssl.CERT_NONE)
c.tls_insecure_set(True)
c.on_connect, c.on_message = on_connect, on_message
c.connect(HOST, 8883, keepalive=60)
c.loop_forever()
```
