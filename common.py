"""Funzioni condivise dagli script di prova (HoloPrint, Fase 1)."""
import json, os, ssl
import paho.mqtt.client as mqtt


def load_config(name="config.local.json"):
    """Legge IP, seriale e access code da config.local.json (NON versionato)."""
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, name)
    if not os.path.exists(path):
        raise SystemExit(
            "Manca config.local.json: copia config.example.json, "
            "rinominalo e inserisci i tuoi dati."
        )
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    for key in ("host", "serial", "access_code"):
        if not cfg.get(key) or str(cfg[key]).startswith("INSERISCI"):
            raise SystemExit(f"Valore mancante in config.local.json: {key}")
    return cfg


def report_topic(cfg):
    return f"device/{cfg['serial']}/report"


def request_topic(cfg):
    return f"device/{cfg['serial']}/request"


def make_client(cfg, on_connect, on_message):
    """Client MQTT verso la stampante (TLS autofirmato, utente 'bblp')."""
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv311)
    c.username_pw_set("bblp", cfg["access_code"])
    c.tls_set(cert_reqs=ssl.CERT_NONE)
    c.tls_insecure_set(True)
    c.on_connect = on_connect
    c.on_message = on_message
    return c


def pushall(client, cfg):
    """Chiede alla stampante lo stato completo."""
    client.publish(
        request_topic(cfg),
        json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}}),
    )


def merge(dst, src):
    """Unisce ricorsivamente i report parziali nello stato completo."""
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            merge(dst[k], v)
        else:
            dst[k] = v
