# Registro

## 2026-11-04

- [figure scRNA (S4)](steps/S4.md) chiuso: il PI ha letto il riassunto senza dubbi nuovi (approvazione nel file dello step).

- [figure scRNA (S4)](steps/S4.md): figure 1, 2, 5 e 6 rifatte da `scripts/generate_figures.py` in PDF vettoriale alle specifiche LNCS (al massimo 12,2 cm, testo di almeno 7 pt, leggibili in scala di grigi); figure multi-GPU 3 e 4 tolte e spostate in `figures/retired/` ([Multi-GPU ridotto a ciò che è stato misurato (D-02)](decisions/D-02.md)); didascalie di Fig. 1, 2, 5, 6 e Table 4 corrette (16 voci del piano nel diario); 2 righe in `arbitrati.csv` (R0351, R0373) e piano rigenerato; cancelli G1-G5 superati; P3 e P4 confermate, P1 e P2 indeterminate e spiegate, P5 smentita e rinviata al taglio; report `reports/S4.html`. Step in attesa della lettura del PI.

- [correzioni di sostanza (S3)](steps/S3.md) chiuso: il PI sceglie titolo A e abstract A ([Titolo e abstract nuovi del capitolo: opzione A (D-18)](decisions/D-18.md)) e approva le altre 21 raccomandazioni ([Scelte di contenuto di S3: approvate le 21 raccomandazioni (D-19)](decisions/D-19.md)); 127 modifiche applicate al manoscritto (md5 09df07d2b8713da7385612991fb1d7df, identico all'anteprima) e alla bibliografia; cancelli G1-G5 superati; diario `IMPL_diario.csv` con 190 voci; rinvii a [figure scRNA (S4)](steps/S4.md), [taglio e stile (S6)](steps/S6.md) e [LaTeX e pacchetto METEOR (S7)](steps/S7.md).

- [correzioni di sostanza (S3)](steps/S3.md): preparate le 190 voci del piano per regione del testo ([Correzioni di S3 preparate per regione e applicate da script (D-17)](decisions/D-17.md)): 127 modifiche (81 senza scelta del PI, 46 in attesa), 483 ricevute rilette da script; anteprima con le raccomandazioni e confronto parola per parola in `manuscript/revisione_n2/S3/`; prove dal DGX e dal web in `results_v2/S3/evidence/`; cancelli G3 e G4 superati sull'anteprima, P1 e P4 confermate, P2 e P5 smentite e spiegate, P3 indeterminata senza effetto su conclusioni; dubbi rinviati a [figure scRNA (S4)](steps/S4.md), [taglio e stile (S6)](steps/S6.md) e [preparazione per Springer (S7)](steps/S7.md); report `reports/S3.html`. Step non chiuso: mancano le scelte del PI (titolo, abstract, altre 21 raccomandazioni); manoscritto ufficiale invariato.

- [correzioni di sostanza (S3)](steps/S3.md) aperto: attese pre-registrate (5 cancelli, 5 previsioni) prima di ogni modifica al manoscritto; registrata la decisione tecnica [Correzioni di S3 preparate per regione e applicate da script (D-17)](decisions/D-17.md); manifest dei grezzi all'apertura: 921 file, 0 differenze.

- [piano di implementazione (S2)](steps/S2.md) chiuso: misura dei vicini CPU con 1 e 100 thread sui dati del benchmark copiati dal DGX (cancelli superati; rapporto 1,16, 1,91, 2,48 a 10.000, 50.000, 100.000 cellule; tempi del DGX uguali a quelli a 1 thread); copia temporanea su micron cancellata; approvazione del PI nel file dello step; dubbi per [correzioni di sostanza (S3)](steps/S3.md) aggiornati.

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
