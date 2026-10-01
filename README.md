# Bambu Quest AR

Applicazione di realtà mista per **Meta Quest 3** che riconosce una stampante 3D **Bambu Lab** nell'ambiente reale, mostra i suoi dati in tempo reale in un'interfaccia sospesa accanto alla macchina e permette all'utente di **modificare i parametri** con effetto reale sulla stampante.

> Stato del progetto: **fase di studio** (nessun codice ancora scritto).
> Ultimo aggiornamento documentazione: 1 ottobre 2026.

## Indice della documentazione

| File | Contenuto |
|------|-----------|
| [docs/01-studio-di-fattibilita.md](docs/01-studio-di-fattibilita.md) | Verdetto di fattibilità, requisiti, rischi, decisioni |
| [docs/02-architettura-e-quest.md](docs/02-architettura-e-quest.md) | Architettura, cosa configurare/usare sul visore, riconoscimento della stampante, UI |
| [docs/03-sviluppo-e-roadmap.md](docs/03-sviluppo-e-roadmap.md) | Ambiente di sviluppo, fasi di lavoro, backlog, test |
| [docs/04-protocollo-bambu.md](docs/04-protocollo-bambu.md) | Riferimento tecnico MQTT / camera / FTP e regole di sicurezza |
| [docs/05-fonti.md](docs/05-fonti.md) | Fonti consultate e punti da verificare |

## Struttura prevista del repository

```
bambu-quest-ar/
├── README.md
├── docs/                 # documentazione (questa cartella)
├── prototype-python/     # fase 1: client MQTT di prova
├── gateway/              # (opzionale) servizio intermedio PC/Raspberry Pi
└── unity-quest-app/      # app Unity per Quest 3
```

## Regole di lavoro suggerite

- Mai committare **access code**, numeri di serie o IP reali: usare un file `.env` o `config.local.json` e inserirlo nel `.gitignore`.
- Ogni decisione tecnica importante va annotata in `docs/` (una riga di motivazione basta).
- Branch `main` stabile, lavoro su branch `feat/...`.
