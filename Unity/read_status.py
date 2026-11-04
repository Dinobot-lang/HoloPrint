"""Test 3 - Registra i dati DURANTE una stampa.
Scrive status_log.jsonl (una riga per ogni cambiamento) e status_dump.json
(stato completo). Avvia lo script, poi lancia una stampa breve.
Ctrl+C a fine prova.
"""
import json, ssl, time
import paho.mqtt.client as mqtt   # libreria client MQTT


# CONFIGURAZIONE
HOST   = "192.168.1.77"        # IP della stampante nella tua rete locale
SERIAL = "20P5BJ661500193"     # numero di serie: fa parte del nome dei "topic" MQTT
CODE   = "8582b62f"            # Access Code mostrato sul display della stampante


state = {}          # stato COMPLETO della stampante, ricostruito pezzo per pezzo
last = None         # ultimo riassunto stampato/salvato (per rilevare i cambiamenti)
seen_states = set() # insieme dei gcode_state già incontrati (IDLE, RUNNING, ...)


def merge(dst, src):
    """Unisce ricorsivamente i report parziali nello stato completo."""
    for k, v in src.items():
        # se il valore è un dizionario ed esiste già un dizionario con
        # la stessa chiave, entra dentro e unisci in profondità
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            merge(dst[k], v)
        else:
            # altrimenti sovrascrivi (o crea) il valore
            dst[k] = v


def summary(s):
    """Estrae dallo stato completo solo i campi che ci interessano."""
    dev = s.get("device", {})
    # lista di informazioni sugli estrusori (utile se ce n'è più di uno)
    ext = dev.get("extruder", {}).get("info", [])
    return {
        "gcode_state": s.get("gcode_state"),          # IDLE / RUNNING / PAUSE / FINISH / FAILED
        "job": s.get("subtask_name"),                 # nome del lavoro in corso
        "pct": s.get("mc_percent"),                   # percentuale di avanzamento
        "remain": s.get("mc_remaining_time"),         # tempo rimanente (minuti)
        "layer": s.get("layer_num"),                  # layer attuale
        "layers": s.get("total_layer_num"),           # layer totali
        "nozzle": s.get("nozzle_temper"),             # temperatura ugello attuale
        "nozzle_target": s.get("nozzle_target_temper"),
        "ext_temps": [e.get("temp") for e in ext],    # temperature per estrusore
        "bed": s.get("bed_temper"),                   # temperatura piatto
        "bed_target": s.get("bed_target_temper"),
        "chamber?": dev.get("ctc", {}).get("info", {}).get("temp"),  # camera (il "?" indica che non sei sicuro del campo)
        "spd_lvl": s.get("spd_lvl"),                  # livello velocità (silent/standard/sport/ludicrous)
        "spd_mag": s.get("spd_mag"),                  # percentuale di velocità
        "print_error": s.get("print_error"),          # codice errore di stampa
        "hms": s.get("hms"),                          # allarmi Health Management System
    }


def on_connect(client, userdata, flags, reason_code, properties):
    """Chiamata quando il client si connette (o fallisce) al broker."""
    print("Connessione:", reason_code)
    if reason_code.is_failure:
        print("Rifiutata. Controlla access code (display) e Developer Mode.")
        client.disconnect()
        return
    # ascolta tutti i report che la stampante pubblica
    client.subscribe(f"device/{SERIAL}/report")
    # chiede alla stampante di inviare subito lo stato completo
    client.publish(f"device/{SERIAL}/request",
        json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}}))


def on_message(client, userdata, msg):
    """Chiamata a ogni messaggio ricevuto."""
    global last
    data = json.loads(msg.payload)       # il payload è JSON
    if "print" not in data:              # ignora messaggi che non riguardano la stampa
        return
    merge(state, data["print"])          # aggiorna lo stato completo
    cur = summary(state)                 # riassunto corrente
    st = cur["gcode_state"]

    # se è la prima volta che vediamo questo gcode_state, avvisa
    # e salva subito un dump completo dello stato
    if st and st not in seen_states:
        seen_states.add(st)
        print(">>> NUOVO gcode_state:", st)
        with open("status_dump.json", "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    # logga solo se qualcosa nel riassunto è cambiato
    if cur != last:
        last = cur
        line = {"t": time.strftime("%H:%M:%S"), **cur}   # aggiunge l'orario
        print(line)
        with open("status_log.jsonl", "a", encoding="utf-8") as f:   # "a" = append
            f.write(json.dumps(line, ensure_ascii=False) + "\n")


# creazione e configurazione del client MQTT
c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv311)
c.username_pw_set("bblp", CODE)          # utente fisso "bblp" + access code come password
c.tls_set(cert_reqs=ssl.CERT_NONE)       # TLS attivo, ma senza verificare il certificato
c.tls_insecure_set(True)                 # accetta anche hostname non corrispondente
c.on_connect, c.on_message = on_connect, on_message
c.connect(HOST, 8883, keepalive=60)      # porta 8883 = MQTT su TLS

try:
    c.loop_forever()                     # resta in ascolto indefinitamente
except KeyboardInterrupt:
    # alla pressione di Ctrl+C salva lo stato finale
    with open("status_dump.json", "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    print("\nInterrotto. Stati visti:", sorted(seen_states))