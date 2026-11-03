# 01 – Studio di fattibilità

## 1. Obiettivo

Indossando un Meta Quest 3, l'utente guarda la propria stampante Bambu Lab e vede:

1. un pannello di **dati in tempo reale** (temperature, avanzamento, tempo residuo, layer, filamento/AMS, stato, errori);
2. opzionalmente il **video della camera** interna;
3. dei **controlli** per modificare parametri (velocità, luce, temperature, pausa/riprendi/stop) con effetto reale sulla macchina.

## 2. Verdetto

**Fattibile**, con tre condizioni:

| Condizione | Perché |
|-----------|--------|
| La stampante deve essere in **modalità LAN-only + Developer Mode** | Sul firmware attuale è l'unico modo "legittimo" per leggere e scrivere in locale senza passare dal cloud. |
| Il "riconoscimento" della stampante va affrontato con **marker (QR) + ancora spaziale**, non con puro riconoscimento visivo | È molto più robusto e impreciso-tollerante del riconoscimento di oggetti con ML. |
| Il progetto è **uso personale/sperimentale** | Il protocollo locale non è supportato ufficialmente da Bambu Lab e può cambiare con gli aggiornamenti firmware. |

Nessuna componente richiede tecnologie inesistenti: ogni blocco ha già esempi pubblici funzionanti (vedi `05-fonti.md`).

## 3. I tre blocchi del progetto

### 3.1 Lato stampante (dati e controllo)
- Comunicazione locale via **MQTT su TLS (porta 8883)**, utente `bblp`, password = *access code* mostrato sul display. Si legge sul topic `device/<seriale>/report` e si scrive su `device/<seriale>/request`.
- **Camera**: stream MJPEG su TLS porta 6000 (famiglie P1/A1) oppure RTSPS porta 322 (famiglia X1).
- **File**: FTPS porta 990 (utile solo se un giorno vorrai inviare stampe dal visore).
- Dal 2025 il firmware ha introdotto un sistema di **autorizzazione** che limita le azioni di terze parti; la **Developer Mode** lascia aperti MQTT, streaming e FTP, ma Bambu Lab non offre supporto per questa modalità e la sicurezza della rete diventa responsabilità dell'utente.
- Effetto collaterale: con LAN-only attivo il cloud (app Bambu Handy, accesso remoto) non è disponibile per quella stampante.

### 3.2 Lato visore (visione e interfaccia)
- Quest 3/3S con **Horizon OS v74 o superiore** permette l'accesso alle camere frontali (Passthrough Camera API) per visione artificiale e ML.
- **Mixed Reality Utility Kit (MRUK)** tratta i **QR code come "trackable"**: payload letto e posa 3D aggiornata nel tempo (richiede Scene/Anchor attivi e il permesso *Spatial Data*).
- Le **Spatial Anchor** (OVRSpatialAnchor) permettono di agganciare il pannello a una posizione fissa del mondo reale.
- Meta fornisce un esempio completo di **object detection** (Unity Inference Engine + YOLO) con posizionamento 3D tramite Depth API.

### 3.3 Lato software (da sviluppare)
- App Unity per Quest: connessione MQTT, modello dati, UI in mixed reality, logica di sicurezza dei comandi.
- (Opzionale) gateway su PC/Raspberry Pi che si interpone tra Quest e stampante.

## 4. Requisiti

**Hardware**: Meta Quest 3 o 3S; stampante Bambu Lab compatibile (famiglie P1, X1, A1, H2, P2: verificare il modello esatto); PC per sviluppo (Windows consigliato per Unity + Quest Link); Wi-Fi comune (consigliato 5/6 GHz).

**Software**: account sviluppatore Meta e modalità sviluppatore sul visore; Unity 6 (6000.0.38f1 o successivo) con Meta XR SDK e MRUK; Meta Quest Developer Hub (MQDH); Bambu Studio per ricavare/controllare access code e seriale; Python 3 per il prototipo.

## 5. Rischi e mitigazioni

| # | Rischio | Probabilità | Impatto | Mitigazione |
|---|---------|-------------|---------|-------------|
| R1 | Bambu Lab cambia/limita il protocollo locale con un aggiornamento firmware | Media | Alto | Non aggiornare il firmware alla cieca; isolare il livello protocollo dietro un'interfaccia; tenere traccia della versione firmware testata. |
| R2 | Developer Mode non disponibile o diverso sul tuo modello | Bassa/Media | Alto | Verificare **prima di tutto** sul display della tua stampante (Fase 0). |
| R3 | Limite di connessioni MQTT contemporanee (circa 4 su P1/X1, una sola su A1) | Alta | Medio | Chiudere altri client (HA, app, ecc.) durante i test; valutare un gateway/proxy. |
| R4 | Il riconoscimento ML non distingue "la tua stampante" da oggetti simili | Alta | Medio | Usare QR/marker + ancora persistente; ML solo come extra. |
| R5 | Il tracking QR non è pensato per oggetti che si muovono velocemente | Certa | Basso | La stampante è ferma: si usa il QR solo per l'allineamento iniziale, poi l'ancora. |
| R6 | Comandi pericolosi (G-code, temperature) inviati per errore da UI in VR | Media | Alto | Conferma esplicita, limiti min/max, lista di comandi consentiti, niente G-code libero in v1. |
| R7 | Rete locale non sicura con Developer Mode attivo | Media | Alto | VLAN/rete separata, nessuna esposizione a internet, access code non committato. |
| R8 | Latenza/qualità del video camera su Quest | Media | Basso | Il video è facoltativo: parti dai soli dati. |
| R9 | Permesso camera/passthrough (privacy) e regole dello store | Bassa | Medio | Per uso personale si installa via MQDH; per eventuale pubblicazione verificare le policy Meta. |
| R10 | Surriscaldamento/batteria del visore in sessioni lunghe | Media | Basso | UI leggera, framerate stabile, sessioni brevi. |

## 6. Cosa NON è nel perimetro della v1

- Avvio di nuove stampe e caricamento file dal visore.
- G-code libero.
- Accesso remoto fuori casa.
- Riconoscimento automatico di più stampanti diverse senza marker.

## 7. Decisione consigliata

Procedere con un **MVP in sola lettura** (dati live ancorati alla stampante), poi aggiungere i controlli uno alla volta (luce → velocità → pausa/riprendi/stop → temperature). La camera e il riconoscimento ML restano fasi opzionali.

## 8. Stima di impegno (indicativa, un solo sviluppatore part-time)

| Fase | Durata stimata |
|------|----------------|
| 0 – Verifiche e setup | 2–4 giorni |
| 1 – Prototipo Python (lettura dati) | 2–3 giorni |
| 2 – App Quest "hello world" + passthrough | 3–5 giorni |
| 3 – MQTT in Unity + HUD dati | 1–2 settimane |
| 4 – QR + ancora spaziale | 1 settimana |
| 5 – Controlli con sicurezza | 1–2 settimane |
| 6 – Camera video | 1 settimana |
| 7 – Rifinitura / ML opzionale | aperta |

Le stime dipendono molto dall'esperienza con Unity: vanno riviste dopo la Fase 2.
