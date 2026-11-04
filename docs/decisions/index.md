# Decisioni del PI (3 novembre 2026)

* [Nuovo riferimento CPU per lo spatial (D-01)](D-01.md) - Lo spatial si rifà con ogni ripetizione in un processo nuovo e con gli stessi gruppi di cellule per CPU e GPU negli step spaziali.
* [Multi-GPU ridotto a ciò che è stato misurato (D-02)](D-02.md) - La parte multi-GPU diventa un paragrafo: la matrice restava su una GPU e le schede aggiuntive non partecipavano al calcolo; nessun nuovo run sul DGX.
* [Lunghezza del capitolo: circa 15 pagine LNCS (D-03)](D-03.md) - Il capitolo punta a circa 15 pagine in formato Springer LNCS.
* [Espressione differenziale come confronto di tempi (D-04)](D-04.md) - L'espressione differenziale si presenta solo come confronto di tempi, senza dire che lo pseudo-bulk usato sia l'approccio statisticamente più rigoroso.
* [CUP corretto del progetto DARE (D-05)](D-05.md) - Il codice CUP del progetto DARE nei ringraziamenti è B53C22006440001; quello nel capitolo è un refuso.
* [Lo short paper è chiuso (D-06)](D-06.md) - Si lavora solo sul capitolo LNBI; lo short paper CIBB non si modifica più.
* [Si lavora solo sul server (D-07)](D-07.md) - Dal 3 novembre 2026 il repo di lavoro è il clone sul server lesexp-server; il clone sul Mac è fermo e non si aggiorna.
* [Il riferimento spatial gira a server libero, quando lo dice il PI (D-09)](D-09.md) - Il nuovo calcolo spatial parte solo in una finestra indicata dal PI, con i calcoli degli altri progetti sospesi.
* [Effetto del cambio di driver GPU: si misura (D-10)](D-10.md) - Il cambio di driver GPU fra marzo e oggi si quantifica confrontando i tempi GPU nuovi con quelli di marzo; se coincidono, nei Metodi basta una frase breve.
* [CPU dello spatial: DGX come riferimento, server come controllo (D-11)](D-11.md) - Il riferimento CPU dello spatial si misura sul nodo DGX del gruppo, riservato per intero, con 100 CPU come lo scRNA; la stessa misura sul server serve da controllo.
* [Co-occorrenza GPU: difetto riportato, esclusa dagli speedup a HD, verifica con rapids-singlecell 0.15.1 (D-13)](D-13.md) - La co-occorrenza GPU a Visium HD 8 µm (overflow in rapids-singlecell 0.14.1) si riporta come risultato, si toglie dagli speedup a Visium HD e si verifica la correzione della versione 0.15.1 con un calcolo di circa 20 minuti.

# Decisioni tecniche

* [Integrità dei risultati grezzi con un manifest md5 (D-08)](D-08.md) - I risultati grezzi si controllano con il manifest md5 del 3 novembre 2026, perché la maggior parte dei file non è tracciata da git.
* [Come gira il nuovo riferimento spatial (D-12)](D-12.md) - Scelte tecniche del calcolo spatial di S1: processi freddi, gruppi dal DGX, passo SLURM da 100 CPU, ramo separato, file grandi fuori da git.
* [Piano di implementazione generato da codice, con arbitrati (D-14)](D-14.md) - Il piano delle correzioni della revisione n.2 sta in manuscript/revisione_n2/piano/, si rigenera con tools/s2_mkplan.py dagli ingressi versionati e registra ogni correzione decisa dopo la scrittura in arbitrati.csv.
