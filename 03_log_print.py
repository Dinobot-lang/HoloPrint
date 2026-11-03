"""Test 3 v2 - Registra i dati durante una stampa e segnala i BUCHI di dati.
Scrive status_log.jsonl e status_dump.json. Ctrl+C per fermare."""
import json, time, threading
from common import load_config, make_client, merge, report_topic, pushall as _pushall

cfg = load_config()

GAP_S = 45          # piu' di cosi' senza messaggi = buco di dati
HEARTBEAT_S = 30    # ogni quanto chiediamo lo stato completo

state = {}
last = None
seen_states = set()
last_rx = time.time()


def split_temp(v):
    """Temperatura estrusori: (obiettivo << 16) | attuale."""
    v = int(v or 0)
    return v & 0xFFFF, v >> 16        # (attuale, obiettivo)


def summary(s):
    dev = s.get("device", {})
    ext = dev.get("extruder", {}).get("info", [])
    return {
        "gcode_state": s.get("gcode_state"),
        "job": s.get("subtask_name"),
        "pct": s.get("mc_percent"),
        "remain": s.get("mc_remaining_time"),
        "layer": s.get("layer_num"),
        "layers": s.get("total_layer_num"),
        "nozzle": s.get("nozzle_temper"),
        "nozzle_target": s.get("nozzle_target_temper"),
        "ext_temps": [split_temp(e.get("temp")) for e in ext],
        "bed": s.get("bed_temper"),
        "bed_target": s.get("bed_target_temper"),
        "chamber?": dev.get("ctc", {}).get("info", {}).get("temp"),
        "spd_lvl": s.get("spd_lvl"),
        "spd_mag": s.get("spd_mag"),
        "print_error": s.get("print_error"),
        "hms": s.get("hms"),
    }


def log_event(evento, **extra):
    line = {"t": time.strftime("%H:%M:%S"), "evento": evento, **extra}
    print(">>>", line)
    with open("status_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


def pushall(client):
    _pushall(client, cfg)


def on_connect(client, userdata, flags, reason_code, properties):
    print("Connessione:", reason_code)
    if reason_code.is_failure:
        print("Rifiutata. Controlla access code (display) e Developer Mode.")
        client.disconnect()
        return
    client.subscribe(report_topic(cfg))
    pushall(client)


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    log_event("disconnesso", motivo=str(reason_code))


def on_message(client, userdata, msg):
    global last, last_rx
    now = time.time()
    gap = now - last_rx
    last_rx = now
    if gap > GAP_S:
        log_event("buco_dati", secondi=int(gap))
        pushall(client)           # rinfresca subito lo stato
    data = json.loads(msg.payload)
    if "print" not in data:
        return
    merge(state, data["print"])
    cur = summary(state)
    st = cur["gcode_state"]
    if st and st not in seen_states:
        seen_states.add(st)
        print(">>> NUOVO gcode_state:", st)
        with open("status_dump.json", "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    if cur != last:
        last = cur
        line = {"t": time.strftime("%H:%M:%S"), **cur}
        print(line)
        with open("status_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")


def heartbeat():
    """Chiede lo stato completo ogni HEARTBEAT_S: se non arriva nulla, c'e' un problema."""
    while True:
        time.sleep(HEARTBEAT_S)
        try:
            pushall(c)
        except Exception as e:
            print("heartbeat errore:", e)


c = make_client(cfg, on_connect, on_message)
c.on_disconnect = on_disconnect
c.connect(cfg["host"], 8883, keepalive=60)
threading.Thread(target=heartbeat, daemon=True).start()

try:
    c.loop_forever()
except KeyboardInterrupt:
    with open("status_dump.json", "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    print("\nInterrotto. Stati visti:", sorted(seen_states))
