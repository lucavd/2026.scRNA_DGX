---
name: lnbi-scrna-dgx-session
description: "Protocollo di sessione del capitolo Springer LNBI (post-proceedings CIBB 2026) sul benchmark GPU contro CPU per scRNA-seq e spatial (rapids-singlecell su DGX H100, Squidpy su RTX 4090; repo lucavd/2026.scRNA_DGX). Da caricare all'inizio di OGNI sessione quando l'utente dice sessione LNBI, capitolo CIBB, full paper DGX, nomina uno step S0-S7 di questo capitolo o chiede di riprendere / continuare / andare avanti. Fissa regole scientifiche (numeri dai file, risultati grezzi intatti, convenzione unica sulle ripetizioni), attese con intervallo di rilevanza, chiusura dello step senza riserve, il riassunto In breve con cui il PI decide, linguaggio semplice e preciso e documentazione in formato Open Knowledge Format (OKF)."
type: Playbook
title: "Capitolo LNBI scRNA DGX: come si lavora una sessione"
status: draft
tags: [lnbi, cibb2026, benchmark, gpu, protocollo, okf]
generated:
  by: lnbi-agent/skill-v1
  at: '2026-11-03T12:00:00+01:00'
sources:
- id: mmm
  resource: "skill di progetto mmm-session (modello di questo protocollo)"
- id: rev2
  resource: "manuscript/revisione_n2/revisione_n2_report.md (revisione avversariale del 3 novembre 2026)"
- id: okf
  resource: https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md
---

<!-- BOZZA preparata in Cowork il 3 novembre 2026. La sessione Science la legge, la confronta con mmm-session,
     la adatta al proprio host (percorsi, server, strumenti) e la registra come skill di progetto. -->

# Scopo

Portare alla sottomissione su Springer METEOR, entro il 10 novembre 2026, il capitolo LNBI esteso dello short paper CIBB 2026, correggendo i problemi trovati dalla revisione n.2 del 3 novembre. PI: Luca Vedovelli. Ogni regola esiste per un errore preciso già successo in questo progetto; se nel caso concreto non protegge da nulla, la si applica in forma leggera e lo si dice in una riga.

# Dove sta tutto

- Repo `lucavd/2026.scRNA_DGX` (GitHub, pubblico). Manoscritto: `manuscript/full_paper_LNBI.md` (sorgente unica del testo). Revisione n.2: `manuscript/revisione_n2/` e `manuscript/00_LEGGIMI_revisione_n2.md`.
- Risultati grezzi in sola lettura: `results/` (scRNA, DGX H100) e `SPATIAL/results/` (spatial, RTX 4090). Rigenerazioni in `results_v2/` e `SPATIAL/results_v2/`.
- Codice: `scripts/`, `slurm/`, `SPATIAL/scripts/`. Immagine spatial: `lucavd/sc-benchmark-spatial:latest`.
- Il DGX non serve per questo capitolo (decisioni D-02 e D-04). La workstation con la RTX 4090 serve solo per lo step S1.
- Documentazione del progetto: cartella `docs/` in formato OKF, da creare nello step S0.

# Regole scientifiche (non si toccano)

1. **Numeri dai file.** Ogni numero del testo si rilegge dal JSON che l'ha prodotto, con uno script. "Tutti / nessuno / solo" si scrive dopo il calcolo sull'intera tabella. Per ogni numero destinato al testo: calcolo sancito (script e parametri), ricevuta (file, md5, valore) e controllo deterministico che lo rilegge ("attested computation" di OKF).
2. **Risultati grezzi intatti**: md5 di `results/` e `SPATIAL/results/` prima e dopo gli step che li leggono.
3. **Il testo descrive il codice che ha girato.** Prima di scrivere un'affermazione sui Metodi si apre il codice. Questa regola esiste perché la revisione n.2 ha trovato un dataset dichiarato diverso da quello scaricato, un multi-GPU che non distribuiva nulla e uno stress test su dati replicati non dichiarati.
4. **Una sola convenzione sulle ripetizioni**, dichiarata nei Metodi e applicata a ogni tabella, figura e frase. Una ripetizione si esclude solo se c'è una causa dimostrata e se l'esclusione non la rende più favorevole al metodo GPU; ogni eccezione è una decisione registrata.
5. **Dispersione**: media e SD campionaria sulle ripetizioni; speedup = rapporto fra medie. Una differenza fra configurazioni entro 2 SD non si scrive come differenza.
6. **Nessuna affermazione oltre il disegno**: un dataset, un nodo, concordanza misurata dove è stata misurata. Ogni frase della Discussione rimanda alla frase o tabella dei Risultati che la sostiene.
7. **Citazioni**: una fonte si cita solo dopo averne letto in sessione il passaggio pertinente; i metadati si verificano su Crossref o OpenAlex. Nessun autore, titolo o DOI scritto a memoria.
8. **Il manoscritto si modifica solo secondo il piano approvato** (step S2). Un numero sbagliato non si corregge in silenzio: si registra nel diario con valore vecchio, valore nuovo e fonte.

# Attese: cancelli e previsioni

Scritte nel file dello step e committate prima di ogni calcolo; dopo il risultato non si cambiano.

**Cancelli** (al massimo 5): controlli binari che, se falliscono, invalidano lo step (md5 dei grezzi, riproduzione di un numero, completezza del run, ancore del piano univoche, compilazione LaTeX).

**Previsioni con intervallo di rilevanza**: quantità, valore atteso e scarto oltre il quale cambierebbe una frase del capitolo. Si giudica la stima con 2 SD: tutta dentro = confermata; tutta fuori = smentita, è un risultato e apre un dubbio; a cavallo = indeterminata, apre un dubbio solo se tocca una conclusione.

Margini di default se lo step non ne motiva altri:

| misura | intervallo di rilevanza |
|---|---|
| tempo di uno step fra ripetizioni dello stesso run | entro il 20% della mediana |
| speedup riportato nel testo | variazione relativa entro il 10% |
| numero di pagine LNCS | da 13 a 17 |
| parole dell'abstract | da 150 a 250 |

# Chi decide

Il PI decide tutto ciò che cambia cosa il capitolo afferma: titolo, abstract, tesi, tagli, convenzioni, figure tolte, nuove analisi, testo finale. Gli si portano al massimo 3 opzioni, con una raccomandazione. Il resto lo decide l'agente e lo registra come decisione tecnica.

# Chiusura dello step

- Verdetto: **chiuso** o **non chiuso**. "Chiuso con riserve" non esiste.
- Lo step è chiuso quando non resta alcun dubbio aperto e il PI ha letto il riassunto «In breve» senza sollevarne di nuovi. Dubbio: cancello fallito, previsione smentita, previsione indeterminata che tocca una conclusione, anomalia vista durante il lavoro, scelta che spetta al PI.
- L'agente prova per primo a chiudere ogni dubbio; porta al PI solo le scelte che gli spettano.
- Rinvio: tollerato come ultima opzione, scritto nel file dello step che lo riceve.

# Linguaggio

Come in mmm-session: semplice ma preciso, prima la conclusione, nessun riferimento muto (un codice interno si scrive sempre con cosa è), sigle solo se servono, contesto che il lettore non può ricordare. Chat, report e documenti in italiano; manoscritto, codice, tabelle e figure in inglese. Niente lineette em o en come punteggiatura, nemmeno nel manoscritto.

# Il riassunto «In breve»

Stessa forma di mmm-session (esempio approvato: `host.skills.read("mmm-session", "esempi/in_breve_S5.md")`): titolo con la domanda dello step; A cosa serviva; Cosa abbiamo trovato (al massimo 5 punti con frase in grassetto); Cosa devi decidere (0-3, domanda e raccomandazione in grassetto, ragioni, alternative); Comunque; riga di chiusura. Nessun codice, file o nome interno; metodi con il nome per esteso; numeri solo se servono a decidere. In appendice al report, la tabella "Da dove vengono i numeri del riassunto".

# Documentazione in formato OKF

Come in mmm-session: bundle `docs/` con frontmatter (`type`, `title`, `description`, `status`, `generated`, `sources`), decisioni una per file in `docs/decisions/D-nn.md` con indice, step in `docs/steps/Sn.md` con `pi_approval`, `docs/log.md` con le modifiche per data, indici generati da script. Gli agenti firmano `lnbi-agent/skill-v1`.

# Come si lavora uno step (uno step per chat)

1. **Apertura**: `git fetch && git status -sb && git log --oneline -n 5`; lavoro non committato vuol dire un'altra chat attiva: fermarsi e chiedere. Leggere `docs/index.md`, il file dello step e il riassunto del precedente. Dire in chat, in 5 righe, dove siamo e cosa fa questo step.
2. **Pre-registrazione** di cancelli e previsioni nel file dello step, commit.
3. **Lavoro**, poi chiusura dei dubbi.
4. **Report** dello step con il riassunto «In breve» in testa.
5. **Chiusura**: file dello step, decisioni nuove, indici, `docs/log.md`, commit e push.
6. **Messaggio al PI**: il riassunto «In breve» così com'è; se lo step è chiuso, ultima riga: "Step <id> chiuso: per il successivo apri una nuova chat nel progetto e scrivi «sessione LNBI, step <id successivo>»."

# Roadmap

Scadenza di sottomissione: 10 novembre 2026. S1 gira in parallelo agli step S2-S4.

| Step | Cosa fa | Chiude quando |
|---|---|---|
| S0 | Registra questa skill, crea `docs/`, registra le decisioni D-01...D-06, verifica md5 e stato del repo | indici e decisioni committati |
| S1 | Nuovo riferimento CPU spatial sulla workstation (`manuscript/revisione_n2/PROMPT_rerun_spatial.md`) | controlli del brief superati e `SPATIAL/results_v2/` nel repo |
| S2 | Piano di implementazione dal registro della revisione n.2 (fase 3 di `revisione-e-piano-implementazione`), con la proposta di convenzione unica sulle ripetizioni | piano approvato dal PI |
| S3 | Correzioni di sostanza che non dipendono dallo spatial; proposte di titolo e abstract nuovi | testo approvato dal PI |
| S4 | Figure 1-6 alle specifiche LNCS (via le due figure multi-GPU), con script nel repo | figure rigenerate da script |
| S5 | Integrazione dei risultati spatial nuovi; figure 7-9 con script | numeri spatial riletti dai nuovi JSON |
| S6 | Taglio a circa 15 pagine LNCS e revisione di stile (`manuscript-style-review`) sul testo nuovo | conteggio pagine nell'intervallo |
| S7 | Sorgente LaTeX llncs 2.26, compilazione, verifica finale di ogni numero, pacchetto METEOR | checklist METEOR completa; la sottomissione la fa il PI |

# Skill collegate

`mmm-session` (modello di questo protocollo), `revisione-e-piano-implementazione` (piano S2 e verifica finale S7), `manuscript-style-review` (S6), `zotero-library` (citazioni).
