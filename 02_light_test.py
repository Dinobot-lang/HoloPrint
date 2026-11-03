"""Test 2 - Scrittura: accende/spegne luce camera e luce di lavoro.
Esito atteso: le luci cambiano davvero (VERIFICATO su X2D) e compare 'LUCI:'.
Esegui:  python 02_light_test.py
"""
import json, time
from common import load_config, make_client, report_topic, request_topic, pushall

cfg = load_config()


def on_connect(client, userdata, flags, reason_code, properties):
    print("Connessione:", reason_code)
    if reason_code.is_failure:
        client.disconnect()
        return
    client.subscribe(report_topic(cfg))
    pushall(client, cfg)


def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    p = data.get("print", {})
    if p.get("command") == "push_status":
        luci = p.get("lights_report")
        if luci:
            print("LUCI:", luci)
        return
    print("RISPOSTA:", json.dumps(data, ensure_ascii=False)[:800])


def luce(node, on):
    cmd = {"system": {"sequence_id": "1", "command": "ledctrl",
                      "led_node": node,
                      "led_mode": "on" if on else "off",
                      "led_on_time": 500, "led_off_time": 500,
                      "loop_times": 0, "interval_time": 0}}
    info = c.publish(request_topic(cfg), json.dumps(cmd), qos=1)
    print(f"Invio {node} {'ON' if on else 'OFF'}, esito invio:", info.rc)


c = make_client(cfg, on_connect, on_message)
c.connect(cfg["host"], 8883, keepalive=60)
c.loop_start()
try:
    time.sleep(6)
    for node in ("chamber_light", "work_light"):
        luce(node, False); time.sleep(6)
        luce(node, True);  time.sleep(6)
finally:
    c.loop_stop()
