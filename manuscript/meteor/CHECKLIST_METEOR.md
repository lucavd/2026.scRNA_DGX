# Lista di controllo per la sottomissione su METEOR

Capitolo LNBI esteso dello short paper CIBB 2026, scadenza 10 novembre 2026 (https://meteor.springer.com/CIBB2026). Preparata il 5 novembre 2026 nello step S7. Fonti delle regole: email dei General Chairs CIBB 2026 del 2 e del 23 ottobre 2026 e guida METEOR per gli autori, riassunte in `manuscript/revisione_n2/PROMPT_claude_science.md` (sezione «Regole di sottomissione»); classe `llncs.cls` 2.26 (ambiente `credits`, `\ackname`, `\discintname`).

Stato: **fatto** = pronto nel repository; **PI** = azione del PI, che fa la sottomissione.

## File da caricare

| voce | stato | file |
|---|---|---|
| PDF del capitolo (sottomissione iniziale: basta questo) | fatto | `manuscript/meteor/full_paper_LNBI.pdf` (14 pagine LNCS) |
| Sorgente LaTeX (sottomissione finale) | fatto | `manuscript/meteor/full_paper_LNBI_source.zip`: `.tex`, `.bbl`, `.bib`, `llncs.cls` 2.26, `splncs04.bst`, `aliascnt.sty`, `figures/fig1.pdf`-`fig4.pdf`; compila da zero in una cartella vuota (`manuscript/meteor/package.json`, `clean_build`) |
| File delle figure con il nome del loro numero | fatto | `manuscript/meteor/figures/fig1.pdf` ... `fig4.pdf`, vettoriali, identici (md5) ai PDF prodotti dagli script delle figure |
| Testi alternativi delle figure (Excel esportato dall'assistente di METEOR, controllato a mano) | PI | bozza da confrontare: `manuscript/meteor/alt_text_draft.md` |
| Disclosure of Interests (quella inserita in METEOR sostituisce quella del testo) | PI, testo pronto | incollare `manuscript/meteor/disclosure_of_interests.txt`, uguale alla frase del `.tex` |
| Dichiarazione sui contenuti di terzi | PI | nessuna figura o tabella di terzi: tutte le figure sono prodotte dagli script del repository |
| Licenza firmata dall'autore corrispondente | PI | modulo di METEOR |

## Contenuto

| voce | stato | nota |
|---|---|---|
| Titolo e abstract diversi da quelli dello short paper | fatto | approvati nello step S3; abstract di 247 parole (limite LNCS 150-250) |
| Stessa lista e ordine degli autori dello short paper | fatto | Vedovelli, Lanera, Sabbatini, Gregori, come in `manuscript/manuscript_short_cameraready.md` |
| Autore corrispondente | PI | nello short paper è Luca Vedovelli; in METEOR si indica nel sistema |
| ORCID degli autori (`\orcidID`, raccomandato da Springer) | PI, facoltativo | da fornire se si vogliono nel capitolo; non scritti a memoria |
| Almeno un aspetto esteso rispetto allo short paper | fatto | nuovo riferimento CPU spatial (step S1) |
| Almeno 8 pagine, formato LNCS | fatto | 14 pagine, riferimenti da pagina 12 |
| Acknowledgements e Disclosure of Interests nell'ambiente `credits` | fatto | Funding come secondo paragrafo dei ringraziamenti |
| Ringraziamento CONVECS per i run su UPSCALE | PI | formula da `https://convecs.it/projects-and-ack/` letta il 4 novembre 2026; da confermare con `hpc@unipd.it` |
| Strumento di LLM nominato nei ringraziamenti | PI, facoltativo | oggi la frase non lo nomina |
| Release del repository con DOI Zenodo, citata in Availability | PI | supplemento pronto per la release: `manuscript/meteor/zenodo/supplementary_LNBI.pdf` (24 pagine); dopo la release il DOI entra nel testo e il LaTeX si rigenera con `python3 -B tools/s7_md2lncs.py` |
| Supplemento non caricato su SpringerLink | fatto | scelta del PI (decisione D-21): solo nella release Zenodo |
