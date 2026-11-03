# Prompt per Claude Science: capitolo LNBI CIBB 2026, dalla revisione n.2 alla sottomissione

Incolla tutto il testo sotto la riga in una nuova chat di Claude Science, nel progetto che vede il repo `lucavd/2026.scRNA_DGX`.

---

Sono Luca Vedovelli, PI. Dobbiamo sottomettere entro il **10 novembre 2026** su Springer METEOR (https://meteor.springer.com/CIBB2026) il capitolo LNBI esteso del nostro short paper CIBB 2026 sul benchmark GPU contro CPU (rapids-singlecell su DGX H100 per lo scRNA-seq, Squidpy su RTX 4090 per lo spatial). Il 3 novembre una revisione avversariale completa ha trovato problemi che cambiano tesi centrali del capitolo. Le correzioni le facciamo qui, step per step, come nel progetto MMM.

## Per prima cosa: la skill di progetto

Prima di qualunque altro lavoro crea la skill di progetto che governerà tutte le sessioni di questo capitolo, sul modello di `mmm-session`.

1. Leggi integralmente `mmm-session` (`host.skills.read("mmm-session")` ed `esempi/in_breve_S5.md`), poi `revisione-e-piano-implementazione` e `manuscript-style-review`.
2. Leggi la bozza già pronta `manuscript/revisione_n2/SKILL_bozza_lnbi_scrna_dgx.md`. L'ho fatta preparare partendo da `mmm-session` e dagli esiti della revisione. Confrontala con `mmm-session`, adattala al tuo host (percorsi reali del repo, server, strumenti disponibili, comandi di controllo OKF) e correggi ciò che non torna. Le regole scientifiche, le attese, la chiusura degli step, il formato «In breve» e la roadmap restano nella sostanza.
3. Registrala come skill di progetto con il nome `lnbi-scrna-dgx-session`, poi mostrami in 10 righe cosa hai cambiato rispetto alla bozza.
4. Da lì in poi segui la skill. Questa chat è lo **step S0**: crea il bundle `docs/` in formato OKF, registra le decisioni elencate sotto (una per file, `decided_by` PI, data 2026-11-03), verifica gli md5 dei risultati grezzi e lo stato del repo, chiudi lo step con il riassunto «In breve».

## Decisioni già prese da me (da registrare in S0)

- **D-01** Rifacciamo il riferimento CPU dello spatial: ogni ripetizione in un processo nuovo, stessi gruppi di cellule per CPU e GPU negli step spaziali. Il brief operativo è `manuscript/revisione_n2/PROMPT_rerun_spatial.md` (step S1, sulla workstation con la RTX 4090).
- **D-02** La parte multi-GPU si riduce a un paragrafo che dice cosa è stato misurato: nella configurazione usata la matrice restava su una GPU e le schede aggiuntive non partecipavano al calcolo. Tolte le due figure multi-GPU e la discussione su Amdahl. Nessun nuovo run sul DGX.
- **D-03** Obiettivo di lunghezza: circa 15 pagine LNCS.
- **D-04** L'espressione differenziale si presenta come confronto di tempi. Si toglie l'affermazione che lo pseudo-bulk usato sia l'approccio statisticamente più rigoroso, perché è stato calcolato su valori log-normalizzati. Nessun nuovo run.
- **D-05** Il CUP corretto del progetto DARE è **B53C22006440001** (nel capitolo c'è un refuso).
- **D-06** Lo short paper è chiuso: si lavora solo sul capitolo.

## Dove sta tutto

- Manoscritto: `manuscript/full_paper_LNBI.md` (md5 al 3 novembre: 4587032be8d2905007687e0bb50d848e). È la sorgente unica; il `.tex` in `manuscript/lncs_latex/` è fermo a luglio e va rigenerato in S7.
- Revisione n.2: `manuscript/00_LEGGIMI_revisione_n2.md` e `manuscript/revisione_n2/`:
  - `revisione_n2_report.md`: riassunto, conformità, problemi raggruppati P1-P14 con le prove, peer-review sintetica, errori introdotti nelle modifiche del 2 settembre, appendice con la fonte di ogni numero;
  - `revisione_n2_log.csv`: 736 esiti su 339 asserzioni (valore dichiarato, valore ricalcolato, fonte, gravità; colonna `verificato_dal_capo` per i problemi ricalcolati due volte);
  - `peer_review.md`: confronto con la letteratura (Nolet 2022, Gardner 2025, ScaleSC, Dicks 2026, Billato 2025), punti che un revisore chiederebbe, PoW proposti ed eseguiti, 17 frasi da riformulare con proposta;
  - `stile/`: copia rivista per lo stile del testo **attuale** (da non applicare così: lo stile si rifà in S6 sul testo corretto), tabella delle modifiche, segnalazioni;
  - `tracce/`: esiti per traccia in JSON e inventario delle asserzioni;
  - `script_e_calcoli.zip`: gli script che riproducono ogni ricalcolo dai JSON del repo;
  - `PROMPT_rerun_spatial.md`: brief dello step S1.
  Se questa cartella non è nel repo, fermati e chiedimela: la trovo nella cartella `manuscript` del mio Mac.

## Regole di sottomissione (fonti: email dei General Chairs CIBB 2026 del 2 e del 23 ottobre 2026; guida METEOR per gli autori)

- Titolo e abstract **leggermente diversi** da quelli dello short paper; stessa lista autori (Vedovelli, Lanera, Sabbatini, Gregori); almeno un aspetto esteso rispetto allo short paper (D-01 lo fornisce: nuovo riferimento CPU spatial con controllo dei thread e stessi gruppi di cellule); minimo 8 pagine; formato Springer LNCS; nuova revisione fra pari; non open access, gratuito.
- Oggi titolo e abstract sono **identici** allo short paper: bloccante.
- METEOR, sottomissione iniziale: basta il PDF. Sottomissione finale: sorgenti (LaTeX), PDF, file delle figure con nomi che corrispondono alla numerazione nel manoscritto, Excel dei testi alternativi generati con l'assistente di METEOR e controllati a mano, dichiarazioni su contenuti di terzi e Disclosure of Interests (quella nel sistema sostituisce quella nel testo), licenza firmata dall'autore corrispondente.
- LaTeX: classe llncs 2.26 (già nel repo), Acknowledgements e Disclosure of Interests nell'ambiente `credits`, bibliografia splncs04 con DOI.

## Cosa c'è da correggere (dettaglio e prove nel report)

1. Dataset scRNA: è un campione casuale di 1,3M cellule da CELLxGENE Census (versione 2025-11-08), non il 10x E18 di Zheng 2017; stress test oltre 3.436.470 cellule su copie concatenate dello stesso dataset (a 11,9M Leiden trova circa 140 mila cluster).
2. Multi-GPU (D-02): PCA e vicini su una sola GPU (17,23 contro 17,01 s con 2 e 8 GPU a 1,3M); il 12% viene dal caricamento dati su nodi diversi; 2 GPU più lente di 1 fra 10k e 100k; i 134,2 GB di VRAM sono pool RMM inattivi.
3. Spatial (D-01): CPU rallentata circa 50 volte dopo la ripetizione 1 con output identico; 51,6x e 3.272x non reggono; co-occorrenza CPU su 7 gruppi contro 3 della GPU; concordanza della co-occorrenza mai calcolata; Moran calcolato sui 2.000 HVG; dataset HD probabilmente il "Tiny 3'" e non l'FFPE.
4. 120x: il 93,5% del tempo CPU a 1,3M è il Wilcoxon di Scanpy; senza, lo speedup è 9,2x. Va detto e confrontato con Dicks 2026.
5. Ripetizione 1 trattata in modo opposto fra scRNA (inclusa: normalizzazione 329x che senza diventa 115x; Leiden 0,36x che diventa 1,12x) e spatial (esclusa). Proponimi una convenzione unica in S2.
6. Espressione differenziale (D-04): pseudo-bulk su valori log, Wilcoxon GPU scritto a mano senza pareggi né p-value, 3-7x contro il t-test e non a parità di test, disegno di 6 righe e non 7 strategie.
7. Concordanza solo a 10k e da un run dell'11 marzo; GPU non deterministica da 50k; Gardner 2025 e Nolet 2022 trovano ARI intorno a 0,5: via "interchangeable". Leiden CPU con `n_iterations=2` contro il default GPU.
8. Bibliografia: Palla2022 e Marconato2024 con autori inesistenti (verifica tutto il .bib su OpenAlex); citazione di Zheng2017 da sostituire con quella del Census; posizionamento rispetto a Nolet 2022, Dicks 2026, ScaleSC.
9. Discussione e conclusioni: "well under one dollar", "a single H100 captures nearly all the benefit" (non misurato a 1,3M), "largest speedup reported for any spatial operation", estrapolazione 20M e 4M, "without improving the cell limit", "high arithmetic intensity" per la normalizzazione.
10. Ambiente: nodo non dedicato (due driver, job contemporanei, CPU allocate diverse); workstation con 128 CPU e driver 580.126.09; il downgrade del container a RAPIDS 24.06 risulta riuscito nella storia git (commit d65ff4d), al contrario di quanto dicono Metodi e Limitations.
11. Figure: 7 su 9 con caratteri sotto 6 punti a 12,2 cm; Fig. 1 a 291 dpi; nomi dei file non coerenti con la numerazione; nessuno script per le figure 7-9; `generate_figures.py` va in errore sui risultati attuali.
12. Quattro frasi introdotte nelle modifiche del 2 settembre sono sbagliate e vanno corrette: Metodi riga 88 (solo PCA e vicini avevano un percorso distribuito); il "+302 GB non attribuiti" attribuito al duplicato di `adata.raw` (è la replicazione del dataset); la frase delle Limitations sul downgrade impossibile; nelle note della talk il 13% attribuito alle sei GPU in più.

## Come voglio lavorare

- Uno step per chat, come in MMM; S1 (calcolo sulla workstation, circa 3 ore) parte appena chiuso S0 e gira mentre si fanno S2, S3 e S4.
- Alla fine di ogni step il riassunto «In breve» e al massimo 3 decisioni per me, con una raccomandazione.
- Titolo e abstract nuovi me li proponi in S3: due o tre alternative ciascuno, poi scelgo io.
- La scadenza è il 10 novembre. Se a metà percorso vedi che non ci stiamo, dimmelo subito con una stima onesta, così chiedo una proroga agli organizzatori.
