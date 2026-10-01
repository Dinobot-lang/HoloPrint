# 02 – Architettura e lavoro sul visore Quest 3

## 1. Architettura

### Opzione A – Diretta (consigliata per l'MVP)

```
Quest 3 (app Unity)  ──MQTT/TLS 8883──►  Stampante Bambu Lab
        │             ──MJPEG/RTSPS (video, opzionale)──►
        └─ QR + ancora spaziale per posizionare l'interfaccia
```

Pro: nessun hardware aggiuntivo, latenza minima. Contro: l'app deve gestire direttamente TLS autofirmato, riconnessioni e il limite di connessioni della stampante.

### Opzione B – Con gateway (consigliata se crescono i requisiti)

```
Quest 3 ──WebSocket/REST (rete locale)──► Gateway (PC/Raspberry Pi) ──MQTT──► Stampante
                                                 └─ transcodifica video, cache stato,
                                                    validazione comandi, più stampanti
```

Pro: una sola connessione verso la stampante (importante per il limite client), video trasformato in un formato facile per Quest, validazione di sicurezza centralizzata, supporto a più stampanti. Contro: un componente in più da mantenere.

**Scelta pratica:** scrivere il codice Unity con un'interfaccia `IPrinterService` così da poter passare da A a B senza riscrivere la UI.

## 2. Preparazione del visore (cosa "modificare" sul Quest 3)

Il Quest non va modificato nel sistema: si abilitano le funzioni per sviluppatori ufficiali.

1. **Account sviluppatore Meta** e creazione di un'organizzazione (necessaria per la modalità sviluppatore).
2. **Modalità sviluppatore** attivata dall'app mobile Meta Horizon sul visore.
3. Visore aggiornato a **Horizon OS v74 o superiore** (la risoluzione 1280×1280 della camera richiede una versione più recente; il default è 1280×960).
4. **Passthrough abilitato** nell'app (requisito esplicito della Passthrough Camera API).
5. **Permessi** nell'app:
   - `horizonos.permission.HEADSET_CAMERA` (camera passthrough) e `android.permission.CAMERA` se usi `WebCamTexture`;
   - permesso **Spatial Data** per Scene/QR/ancore.
6. **Installazione**: build APK da Unity e installazione tramite **Meta Quest Developer Hub** (anche via Wi-Fi). L'installazione via MQDH evita anche le restrizioni parentali sugli account teen/youth per la camera.
7. **Rete**: visore e stampante sulla stessa rete locale, senza "client isolation" sul router.
8. **Anteprima**: la Passthrough Camera API non funziona nel simulatore XR; servono il visore fisico o Meta Horizon Link v2.1+.

## 3. Come far "riconoscere" la stampante al visore

### Strategia consigliata: QR code + ancora persistente

1. Stampa (o applica) un **QR code** sulla stampante. Il payload può essere l'identificativo, es. `bambu:SERIALE` oppure un nome logico `stampante-1`.
2. Con MRUK abiliti *QR Code Tracking* (Scene Settings → Tracker Configuration). Il callback `TrackableAdded` fornisce `MarkerPayloadString` e la posa 3D. Sono supportati QR fino alla versione 10.
3. Alla prima rilevazione l'app **crea una `OVRSpatialAnchor`** nella posizione del QR e la **salva** (persistente). Nelle sessioni successive l'ancora si ricarica senza dover riguardare il QR.
4. La UI si posiziona con un offset rispetto all'ancora (es. pannello a destra della macchina, leggermente sopra).
5. Il payload fa da **mappa verso la configurazione**: seriale → IP/access code salvati localmente nel visore (mai nel repository).

Nota: il tracking QR di MRUK aggiorna la posa nel tempo ma non è pensato per oggetti in rapido movimento: va bene per un oggetto fermo come la stampante.

### Fallback senza stampare nulla: posizionamento manuale
Al primo avvio l'utente punta con controller/mano il punto in cui vuole il pannello e conferma: si crea un'ancora a mano. Utile come piano B.

### Opzione avanzata: riconoscimento visivo (ML)
- Esiste un esempio ufficiale (Multi Object Detection) basato su Passthrough Camera API + Unity Inference Engine (modello YOLO), che converte il riquadro 2D in posizione 3D con raycast sulla mappa di profondità.
- I modelli generici riconoscono classi comuni, **non "la tua Bambu Lab"**: servirebbe addestrare un modello su foto della tua stampante.
- Limiti noti: una sola camera (sinistra o destra) alla volta, risoluzione limitata, accuratezza non totale. Per questi motivi è una **fase opzionale**, non la base.

## 4. Sfruttare le funzionalità del Quest 3

| Funzione | Uso nel progetto |
|----------|------------------|
| Passthrough (mixed reality) | Vedere la stampante reale con l'interfaccia sovrapposta |
| Passthrough Camera API | Visione artificiale opzionale; lettura frame |
| MRUK + Trackables | Lettura QR e posa 3D |
| Spatial Anchors | Pannello fisso nel mondo, persistente tra sessioni |
| Depth API / Scene API | Occlusione e posizionamento 3D coerente (opzionale) |
| Hand tracking / controller | Interazione con la UI (poke, ray, pinch) |
| Meta XR Interaction SDK | Pulsanti, slider, pannelli già pronti |
| Audio spaziale | Avvisi sonori (errore, fine stampa) |

## 5. Progettazione dell'interfaccia (UI/UX)

**Pannello principale** (ancorato alla stampante, sempre rivolto verso l'utente o fisso con lieve inclinazione):

- Stato (in stampa / in pausa / pronta / errore) con colore
- Nome del file, **barra di avanzamento %**, layer corrente/totale, tempo residuo
- Temperature ugello e piano (attuale → obiettivo)
- Velocità attuale
- AMS: slot con colore e tipo di filamento
- Pulsante camera (apre una finestra video separata)

**Pannello controlli** (si apre su richiesta):

- Luce camera on/off
- Profilo velocità (silenzioso / standard / sport / ludicrous)
- Pausa / Riprendi / Stop
- Temperature obiettivo (slider con limiti di sicurezza)

**Regole di sicurezza UI:**
- Azioni distruttive (Stop, cambio temperatura) richiedono **conferma** (pressione prolungata o slider "scorri per confermare").
- Valori limitati a range ragionevoli per il materiale.
- Indicatore chiaro di "comando inviato → confermato dalla stampante".
- Se la connessione cade, la UI passa a stato **"dati non aggiornati"** e disabilita i controlli.
- Niente G-code libero nella v1.

## 6. Struttura del codice Unity (proposta)

```
Assets/
├── Scripts/
│   ├── Core/            IPrinterService, PrinterState, PrinterCommand
│   ├── Bambu/           BambuMqttService (MQTTnet), BambuParser, BambuCommandBuilder
│   ├── Tracking/        QrAnchorManager, AnchorStorage
│   ├── UI/              StatusPanel, ControlPanel, ConfirmSlider
│   └── Safety/          CommandValidator, RateLimiter
├── Prefabs/
├── Scenes/
└── Settings/            config locale (non versionata)
```

Libreria MQTT in Unity: **MQTTnet** (richiede attenzione a TLS autofirmato e a IL2CPP/Android).
