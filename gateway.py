"""HoloPrint gateway.

Si collega alla stampante (MQTT/TLS, come negli script di prova) e rende lo stato
disponibile in modo semplice alla app del visore Quest:

    http://<IP-del-PC>:8080/state     ->  JSON compatto con tutti i dati

Perche': il visore parla HTTP semplice (facile e robusto), il gateway gestisce
TLS autofirmato, riconnessioni, heartbeat e il limite di connessioni della stampante.

Uso:   python gateway.py          (Ctrl+C per fermare)
Config: config.local.json  ->  {"host": "...", "serial": "...", "access_code": "..."}
"""
import json, os, ssl, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import paho.mqtt.client as mqtt

HTTP_PORT = 8080
HEARTBEAT_S = 30

raw = {}                    # stato completo della stampante, unito dai report parziali
lock = threading.Lock()
last_rx = 0.0               # istante dell'ultimo messaggio ricevuto
connected = False
cfg = {}


def load_config():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "config.local.json")
    if not os.path.exists(path):
        raise SystemExit("Manca il file: " + path + "  (copia config.example.json)")
    with open(path, encoding="utf-8") as f:
        c = json.load(f)
    for k in ("host", "serial", "access_code"):
        if not c.get(k) or str(c[k]).startswith(("INSERISCI", "IL_TUO")):
            raise SystemExit("Valore mancante in config.local.json: " + k)
    return c


def merge(dst, src):
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            merge(dst[k], v)
        else:
            dst[k] = v


def split_temp(v):
    """Temperatura estrusori: (obiettivo << 16) | attuale."""
    try:
        v = int(v or 0)
    except (TypeError, ValueError):
        return 0, 0
    return v & 0xFFFF, v >> 16


def num(v, default=0):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else default


def build_view(s, now, is_connected, rx_time):
    """Trasforma lo stato grezzo in un JSON piatto e semplice per Unity."""
    dev = s.get("device", {})
    extruders = []
    for e in dev.get("extruder", {}).get("info", []):
        cur, tar = split_temp(e.get("temp"))
        extruders.append({"id": num(e.get("id")), "temp": cur, "target": tar})

    slots = []
    for unit in s.get("ams", {}).get("ams", []):
        for t in unit.get("tray", []):
            slots.append({
                "unit": str(unit.get("id", "")),
                "slot": str(t.get("id", "")),
                "color": (t.get("tray_color") or "00000000")[:6],
                "type": t.get("tray_type") or "",
                "brand": t.get("tray_sub_brands") or "",
                "remain": num(t.get("remain"), -1),
            })

    lights = {l.get("node"): l.get("mode") for l in s.get("lights_report", [])}

    return {
        "connected": bool(is_connected),
        "age_s": round(now - rx_time, 1) if rx_time else -1,
        "state": s.get("gcode_state") or "",
        "job": s.get("subtask_name") or "",
        "percent": num(s.get("mc_percent")),
        "remain_min": num(s.get("mc_remaining_time")),
        "layer": num(s.get("layer_num")),
        "layers": num(s.get("total_layer_num")),
        "nozzle": num(s.get("nozzle_temper")),
        "nozzle_target": num(s.get("nozzle_target_temper")),
        "extruders": extruders,
        "bed": num(s.get("bed_temper")),
        "bed_target": num(s.get("bed_target_temper")),
        "chamber": num(dev.get("ctc", {}).get("info", {}).get("temp")),
        "speed_level": num(s.get("spd_lvl")),
        "speed_percent": num(s.get("spd_mag")),
        "chamber_light": lights.get("chamber_light") or "",
        "work_light": lights.get("work_light") or "",
        "ams": slots,
        "error": num(s.get("print_error")),
        "wifi": s.get("wifi_signal") or "",
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] in ("/", "/state"):
            with lock:
                body = json.dumps(
                    build_view(raw, time.time(), connected, last_rx), ensure_ascii=False
                ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def log_message(self, *args):   # niente rumore in console
        pass


def pushall(client):
    client.publish(f"device/{cfg['serial']}/request",
                   json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}}))


def on_connect(client, userdata, flags, reason_code, properties):
    global connected
    print("Stampante - connessione:", reason_code)
    if reason_code.is_failure:
        print("Rifiutata. Controlla access code (display) e Developer Mode. Mi fermo.")
        client.disconnect()
        return
    connected = True
    client.subscribe(f"device/{cfg['serial']}/report")
    pushall(client)


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    global connected
    connected = False
    print("Stampante - disconnessa:", reason_code, "(riprovo in automatico)")


def on_message(client, userdata, msg):
    global last_rx
    try:
        data = json.loads(msg.payload)
    except ValueError:
        return
    if "print" not in data:
        return
    with lock:
        merge(raw, data["print"])
        last_rx = time.time()


def heartbeat(client):
    while True:
        time.sleep(HEARTBEAT_S)
        try:
            pushall(client)
        except Exception as e:
            print("heartbeat errore:", e)


def main():
    global cfg
    cfg = load_config()

    srv = ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"Gateway attivo: http://localhost:{HTTP_PORT}/state")

    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv311)
    c.username_pw_set("bblp", cfg["access_code"])
    c.tls_set(cert_reqs=ssl.CERT_NONE)
    c.tls_insecure_set(True)
    c.on_connect, c.on_message, c.on_disconnect = on_connect, on_message, on_disconnect
    c.connect(cfg["host"], 8883, keepalive=60)
    threading.Thread(target=heartbeat, args=(c,), daemon=True).start()
    try:
        c.loop_forever()
    except KeyboardInterrupt:
        print("\nGateway fermato.")


if __name__ == "__main__":
    main()
