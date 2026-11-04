# Registro

## 2026-11-04

- [piano di implementazione (S2)](steps/S2.md): il PI approva il piano e le raccomandazioni; registrate [Convenzione unica sulle ripetizioni: media e SD di tutte e 5 (D-15)](decisions/D-15.md) e [Vicini CPU a 1 thread: si dichiara e si misura (D-16)](decisions/D-16.md); attese della misura dei vicini pre-registrate.

- [piano di implementazione (S2)](steps/S2.md): piano generato in `manuscript/revisione_n2/piano/` (269 voci da 424 righe del registro, 6 mappe, revisione con tre revisori, avversariale e ultima passata), registrata la decisione tecnica [Piano di implementazione generato da codice, con arbitrati (D-14)](decisions/D-14.md); analisi P1-P3 in `results_v2/S2/`; trovata la ricerca dei vicini CPU a 1 thread numba (pynndescent con `n_jobs = 1`); `script_e_calcoli.zip` della revisione n.2 ora tracciato; dubbi rinviati ai file di [correzioni di sostanza (S3)](steps/S3.md) e [integrazione spatial (S5)](steps/S5.md); report `reports/S2.html`. Step non chiuso: mancano tre decisioni del PI.

- [nuovo riferimento spatial (S1)](steps/S1.md) chiuso: il PI ha letto il riassunto senza dubbi nuovi (approvazione nel file dello step).

- [piano di implementazione (S2)](steps/S2.md): attese pre-registrate (5 cancelli, 3 previsioni, criterio della convenzione sulle ripetizioni fissato prima di vederne le conseguenze); aggiunto `tools/check_manifest.py`, che confronta i risultati grezzi con il manifest md5.

## 2026-11-03

- [nuovo riferimento spatial (S1)](steps/S1.md): registrata [Co-occorrenza GPU: difetto riportato, esclusa dagli speedup a HD, verifica con rapids-singlecell 0.15.1 (D-13)](decisions/D-13.md); verifica con rapids-singlecell 0.15.1 fatta a server libero (19:31-19:36): co-occorrenza GPU uguale alla CPU su 49 distanze su 49, tempo invariato; report aggiornato; riassunto finale al PI.

- [nuovo riferimento spatial (S1)](steps/S1.md): rerun completato (DGX `poddgx02` per la CPU di riferimento, RTX 4090 e controllo CPU a 128 thread sul server libero); 5 cancelli superati; trovato e spiegato l'overflow della co-occorrenza GPU in rapids-singlecell 0.14.1 a Visium HD 8 µm; risultati in `SPATIAL/results_v2/`, report `reports/S1.html`; dubbi rinviati ai file di [piano delle correzioni (S2)](steps/S2.md), [correzioni di sostanza (S3)](steps/S3.md) e [integrazione spatial (S5)](steps/S5.md). Step non chiuso: manca la decisione del PI sulla co-occorrenza.

- [nuovo riferimento spatial (S1)](steps/S1.md): attese pre-registrate (5 cancelli, 6 previsioni, criterio della prova termica) e anomalie viste all'apertura; registrata la decisione tecnica [Come gira il nuovo riferimento spatial (D-12)](decisions/D-12.md); aggiunto `tools/s1_march_reference.py`, che rilegge i valori di marzo usati nelle previsioni.

- [basi del lavoro (S0)](steps/S0.md) chiuso: registrata [CPU dello spatial: DGX come riferimento, server come controllo (D-11)](decisions/D-11.md) (CPU dello spatial sul DGX come riferimento, server come controllo); accesso dal server al DGX con chiave dedicata; approvazione del PI nel file dello step.

- [basi del lavoro (S0)](steps/S0.md), risposte del PI al riassunto: registrate [Il riferimento spatial gira a server libero, quando lo dice il PI (D-09)](decisions/D-09.md) (finestra del calcolo spatial scelta dal PI) e [Effetto del cambio di driver GPU: si misura (D-10)](decisions/D-10.md) (effetto del driver GPU da misurare); temperatura e macchina della CPU annotate nei file di [basi del lavoro (S0)](steps/S0.md) e [nuovo riferimento spatial (S1)](steps/S1.md).

- [basi del lavoro (S0)](steps/S0.md): server allineato a `origin/main` (a4b9b9e) e materiale della revisione n.2 copiato dal Mac (19 file, md5 identici). Creati la skill di progetto `lnbi-scrna-dgx-session`, il bundle `docs/`, lo script `tools/okf.py` (adattato da MMM) e il manifest md5 dei risultati grezzi. Registrate le decisioni del PI [Nuovo riferimento CPU per lo spatial (D-01)](decisions/D-01.md)...[Si lavora solo sul server (D-07)](decisions/D-07.md) e la decisione tecnica [Integrità dei risultati grezzi con un manifest md5 (D-08)](decisions/D-08.md).
