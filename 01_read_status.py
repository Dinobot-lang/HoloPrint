"""Test 1 - Lettura dati live. Salva lo stato completo in status_dump.json.
Esegui:  python 01_read_status.py     (Ctrl+C per fermare)
"""
import json
from common import load_config, make_client, merge, report_topic, pushall

cfg = load_config()
state = {}

KEYS = ["gcode_state", "subtask_name", "mc_percent", "mc_remaining_time",
        "layer_num", "total_layer_num", "nozzle_temper", "nozzle_target_temper",
        "bed_temper", "bed_target_temper", "spd_lvl", "spd_mag"]


def on_connect(client, userdata, flags, reason_code, properties):
    print("Connessione:", reason_code)
    if reason_code.is_failure:
        print("Rifiutata. Controlla access code (display) e Developer Mode.")
        client.disconnect()
        return
    client.subscribe(report_topic(cfg))
    pushall(client, cfg)


def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    if "print" not in data:
        return
    merge(state, data["print"])
    with open("status_dump.json", "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    print({k: state[k] for k in KEYS if k in state})


c = make_client(cfg, on_connect, on_message)
c.connect(cfg["host"], 8883, keepalive=60)
try:
    c.loop_forever()
except KeyboardInterrupt:
    print("\nInterrotto.")
