# Registro

## 2026-11-03

- [nuovo riferimento spatial (S1)](steps/S1.md): attese pre-registrate (5 cancelli, 6 previsioni, criterio della prova termica) e anomalie viste all'apertura; registrata la decisione tecnica [Come gira il nuovo riferimento spatial (D-12)](decisions/D-12.md); aggiunto `tools/s1_march_reference.py`, che rilegge i valori di marzo usati nelle previsioni.

- [basi del lavoro (S0)](steps/S0.md) chiuso: registrata [CPU dello spatial: DGX come riferimento, server come controllo (D-11)](decisions/D-11.md) (CPU dello spatial sul DGX come riferimento, server come controllo); accesso dal server al DGX con chiave dedicata; approvazione del PI nel file dello step.

- [basi del lavoro (S0)](steps/S0.md), risposte del PI al riassunto: registrate [Il riferimento spatial gira a server libero, quando lo dice il PI (D-09)](decisions/D-09.md) (finestra del calcolo spatial scelta dal PI) e [Effetto del cambio di driver GPU: si misura (D-10)](decisions/D-10.md) (effetto del driver GPU da misurare); temperatura e macchina della CPU annotate nei file di [basi del lavoro (S0)](steps/S0.md) e [nuovo riferimento spatial (S1)](steps/S1.md).

- [basi del lavoro (S0)](steps/S0.md): server allineato a `origin/main` (a4b9b9e) e materiale della revisione n.2 copiato dal Mac (19 file, md5 identici). Creati la skill di progetto `lnbi-scrna-dgx-session`, il bundle `docs/`, lo script `tools/okf.py` (adattato da MMM) e il manifest md5 dei risultati grezzi. Registrate le decisioni del PI [Nuovo riferimento CPU per lo spatial (D-01)](decisions/D-01.md)...[Si lavora solo sul server (D-07)](decisions/D-07.md) e la decisione tecnica [Integrità dei risultati grezzi con un manifest md5 (D-08)](decisions/D-08.md).
