# Rifare il benchmark spatial con un riferimento CPU valido

Brief dello step S1 della skill di progetto `lnbi-scrna-dgx-session` (decisione D-01). Si esegue sulla workstation con la RTX 4090, la macchina dei run spatial del 27 marzo 2026, dentro il clone del repo `lucavd/2026.scRNA_DGX`.

## Perché
La revisione del capitolo LNBI ha trovato due difetti nei risultati spatial (`SPATIAL/results/`):

1. **La CPU rallenta dopo la prima ripetizione.** Visium HD 8 um, co-occorrenza su CPU: 73,47 s nella ripetizione 1, 3.570-3.574 s nelle ripetizioni 2-5, con matrici di output identiche bit per bit. Anche Moran passa da 35,7 a circa 48 s. Lo script CPU esegue tutte le ripetizioni nello stesso processo (`for repeat in range(...)` in `benchmark_spatial_cpu.py`). Ipotesi da verificare, letta nel sorgente di Squidpy 1.8.1: `sq.gr.nhood_enrichment`, che gira dopo la co-occorrenza, lascia numba a 1 thread nel processo, e le ripetizioni successive girano a un thread. Il paper ha escluso proprio la ripetizione 1 come "warmup JIT".
2. **CPU e GPU calcolano la co-occorrenza su gruppi diversi.** Ognuna usa il proprio Leiden (CPU igraph con `n_iterations=2`, GPU cuGraph): a HD 8 um la matrice CPU è 7x7x49 e quella GPU 3x3x49. Per lo stesso motivo il confronto della co-occorrenza in `compare_spatial_results.py` finisce in `shape_mismatch`.

## Cosa fare
Non toccare `SPATIAL/results/` né il manoscritto. Lavora su un ramo `rerun-spatial-v2` e scrivi i risultati in `SPATIAL/results_v2/`.

1. **Un processo per ripetizione.** Aggiungi agli script CPU e GPU un argomento `--repeat-id` e lancia ogni ripetizione con un `docker run` separato (stessa immagine di `run_all_benchmarks.sh`, `lucavd/sc-benchmark-spatial:latest`; registra il digest dell'immagine).
2. **Thread registrati.** All'inizio di ogni step salva nei metadati del JSON `numba.get_num_threads()` e l'output di `threadpoolctl.threadpool_info()` (numero di thread per libreria). Registra anche hostname, numero di CPU, modello e driver della GPU, commit git.
3. **Stessi gruppi per gli step spaziali.** Aggiungi `--labels-from <csv>` a entrambi gli script. Leiden si esegue e si cronometra come oggi, ma co-occorrenza, nhood enrichment e ligand-receptor usano le etichette lette dal file. Per ogni piattaforma usa le etichette della ripetizione 1 CPU del nuovo run. Salva nel JSON il numero di gruppi effettivamente usato.
4. **Nient'altro cambia**: parametri, semi, sottocampionamento di HD 2 um a 400.000 bin, regole di skip, versioni.
5. **Ordine**: per ogni piattaforma (Visium v1, Visium HD 8 um, Visium HD 2 um) prima CPU ripetizioni 1-5, poi GPU 1-5, poi `compare_spatial_results.py` sui nuovi file. Durata stimata: circa 3 ore, quasi tutta CPU su HD 2 um e HD 8 um.
6. **Verifica del meccanismo, a costo minimo**: su Visium v1 esegui anche 2 ripetizioni nello stesso processo con lo script originale, registrando `numba.get_num_threads()` prima e dopo `nhood_enrichment`. Se il numero scende a 1, il meccanismo è confermato.
7. **Registra la provenienza del dataset Visium HD**: nome del dataset 10x, URL e file scaricati da `download_spatial_data.py`. La revisione sospetta che sia il "Visium HD Tiny 3'" e non l'FFPE descritto nei Metodi.

## Controlli prima di chiudere
- `numba.get_num_threads()` uguale in tutte le ripetizioni CPU e uguale al numero di CPU disponibili.
- Tempo CPU della co-occorrenza a HD 8 um: ripetizioni 1-5 entro il 20% l'una dall'altra. Se no, fermati e riporta.
- Matrici di co-occorrenza CPU identiche fra ripetizioni; matrici CPU e GPU con la stessa forma; concordanza della co-occorrenza calcolata.

## Cosa restituire
Un file `SPATIAL/results_v2/RERUN_REPORT.md` con, per piattaforma:
- tempo totale e per step (co-occorrenza, nhood, Moran, Geary, vicini spaziali, UMAP), media e SD su ripetizioni 1-5 e 2-5, per CPU e GPU;
- speedup end-to-end e per step con entrambe le convenzioni;
- thread registrati, numero di gruppi usati, provenienza del dataset;
- esito dei controlli e del test del meccanismo.

Poi commit e push del ramo `rerun-spatial-v2`: script modificati, launcher, `results_v2/` e report.
