# 05 – Fonti e punti da verificare

Consultate il 1 ottobre 2026.

## Bambu Lab
- Guida SimplyPrint su LAN-only e Developer Mode: https://help.simplyprint.io/en/article/bambu-lab-lan-only-mode-and-developer-mode-how-to-enable-xa0hch/
- 3D Printing Industry – firmware con controllo autorizzazioni e Developer Mode: https://3dprintingindustry.com/news/bambu-lab-responds-to-backlash-over-new-firmware-update-235771/
- Comunicazione Bambu Lab sul Developer Mode: https://www.voxelmatters.com/bambu-lab-clarifies-issues-related-to-latest-secutiry-update/
- Libreria Go (MQTT 8883, camera 6000, RTSPS 322): https://pkg.go.dev/github.com/gonzalop/bambulan
- BambooMobile (note di protocollo camera/MQTT): https://github.com/joel-sgc/BambooMobile/wiki
- bambu-mqtt-proxy (limiti di connessione): https://github.com/bradsjm/bambu-mqtt-proxy
- Binding openHAB (comportamento report parziali serie P1): https://www.openhab.org/addons/bindings/bambulab
- BambuHelper (note su H2 e Developer Mode): https://github.com/beegee-tokyo/BambuHelper
- Riferimento protocollo community: progetto **OpenBambuAPI** su GitHub (da consultare direttamente)

## Meta Quest
- Panoramica Passthrough Camera API (Unity): https://developers.meta.com/horizon/documentation/unity/unity-pca-overview/
- Getting started PCA in Unity: https://developers.meta.com/horizon/documentation/unity/unity-pca-documentation/
- Esempio Multi Object Detection: https://developers.meta.com/horizon/documentation/unity/unity-sample-camera-object-detection/
- Tracciamento QR in MRUK: https://developers.meta.com/horizon/documentation/unity/unity-mr-utility-kit-qrcode-detection/
- Repository esempi: https://github.com/oculus-samples/Unity-PassthroughCameraApiSamples
- QuestCameraKit (esempi community): https://github.com/xrdevrob/QuestCameraKit

## Da verificare personalmente (non confermato dalle fonti)
1. Menu esatto e disponibilità di Developer Mode sul tuo modello/firmware (alcune fonti indicano differenze tra famiglie, incluso P2).
2. Nomi dei campi e formato dei comandi MQTT sul tuo firmware.
3. Versione minima attuale di Horizon OS / MRUK / Unity al momento dello sviluppo.
4. Eventuali novità Meta sul riconoscimento di oggetti nativo (le API cambiano rapidamente).
5. Segnalazioni aperte sull'integrazione GitHub–Claude per repository privati (vedi conversazione).
