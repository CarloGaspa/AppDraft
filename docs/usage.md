# Usare AppDraft

[README](../README.md) · [Sviluppo e avvio dai sorgenti](development.md)

AppDraft compila questionari definiti in Markdown e produce una specifica condivisibile con persone e AI. L'app funziona localmente: non usa server, rete, account o database.

## Aprire l'app su Windows

1. Procurati `AppDraft.exe`, oppure usa `dist/AppDraft.exe` se hai creato la build dalla repo.
2. Se ricevuto in uno ZIP, estrailo prima di aprirlo.
3. Fai doppio clic su `AppDraft.exe`.

Non servono installer, Python, VS Code o terminale. Puoi spostare l'eseguibile in una cartella a tua scelta: i template iniziali sono già inclusi. Al primo avvio non devi preparare file o cartelle di supporto.

## Aprire l'app su macOS

1. Procurati la build macOS `AppDraft.app`, eventualmente dentro `AppDraft-macOS.zip`.
2. Estrai lo ZIP con Finder, preservando l'intera `.app`.
3. Fai doppio clic su `AppDraft.app`. Puoi anche spostarla in Applicazioni, ma non è necessario.

Finder mostra la `.app` come un singolo elemento, anche se contiene internamente un bundle di file. Non servono Python o terminale. L'eseguibile Windows non funziona su Mac: occorre una build per il sistema e l'architettura del Mac.

La configurazione macOS è presente nella repo, ma la build deve essere prodotta e verificata su un Mac: vedi [packaging](packaging.md). Se non hai ancora una `.app`, puoi eseguire l'app [dai sorgenti](development.md).

## Compilare un questionario

1. Seleziona **Technology Stack Assessment** nella sidebar. Il template iniziale contiene 20 sezioni, 39 domande e 11 campi obbligatori.
2. Compila le sezioni nell'area scrollabile. L'asterisco `*` indica i campi obbligatori.
3. Per numeri e scale senza default, spunta **Risposta** prima di impostare un valore. Togliendo la spunta, il campo torna senza risposta.
4. Nei booleani, lo stato intermedio indica nessuna risposta, la spunta indica sì e la casella vuota indica no.
5. Segui il conteggio delle domande obbligatorie e la barra di progresso in fondo alla finestra.

La rotella scorre il form anche quando il puntatore è sopra dropdown, numeri, scale o testi multilinea; non cambia le risposte. Puoi modificare i valori con clic, tastiera e controlli dell'editor. Nei testi multilinea la barra interna consente di raggiungere eventuali righe fuori dall'area visibile.

## Salvare e riprendere una bozza

Le modifiche vengono salvate automaticamente dopo 650 ms senza ulteriori cambiamenti. Cambio questionario e chiusura salvano subito le modifiche in attesa. **Salva bozza** forza un salvataggio manuale.

Alla riapertura, l'app ripristina la bozza se ID e versione del template sono compatibili e le risposte sono valide. Esiste una sola bozza per ID di questionario: la V1 non gestisce più progetti compilati con lo stesso template.

Una risposta conta come compilata quando non è `null`, una stringa vuota o fatta solo di spazi, oppure una lista vuota. `false` e zero sono validi. Anche i default valorizzati contano. Con zero domande obbligatorie il progresso è 100%.

## Preview, copia ed export

- **Preview** apre il Markdown finale come testo, senza creare un file di export.
- **Copia negli appunti**, nella preview, copia l'intero documento.
- **Esporta .md** apre il dialog di sistema per scegliere nome e posizione del file.

Il nome suggerito usa la risposta `project_name`, se presente, e il nome del questionario. Altrimenti usa il nome del questionario e la data locale. La prima posizione proposta è Documenti; le successive usano l'ultima cartella di export.

L'export mantiene l'ordine di sezioni e domande, include metadata YAML e termina con istruzioni fisse per una valutazione architetturale da parte di un'AI. Le liste sono elenchi Markdown, i booleani sono Sì/No e le scale mostrano valore/massimo. Puoi esportare anche un questionario incompleto: le risposte assenti diventano `_Non compilato._`.

## Aggiungere un questionario

Premi **Importa template…** e scegli un file `.md`. L'app lo valida, lo copia nello spazio personale e lo seleziona. Non occorre modificare Python né mettere cartelle accanto all'eseguibile. Per scriverne uno, vedi [formato dei template](templates.md).

Un template personale ha precedenza su un template incorporato con lo stesso ID. Se un file personale con quell'ID esiste già nella destinazione dell'importazione, l'app chiede conferma prima di sostituirlo. Le bozze restano conservate e vengono controllate quando riapri il questionario.

Puoi anche copiare manualmente un `.md` nella sottocartella personale `templates/`, poi premere **Ricarica template** o riavviare l'app. I file non validi producono un messaggio e non bloccano quelli validi.

## Dove sono i dati e come fare un backup

L'app usa la cartella personale fornita dal sistema tramite Qt `AppLocalDataLocation`:

- Windows: normalmente `%LOCALAPPDATA%\AppDraft\AppDraft`. Puoi incollare questo percorso nella barra di Esplora file.
- macOS: sotto `~/Library/Application Support/`, nella sottocartella determinata da Qt per AppDraft. In Finder usa **Vai → Vai alla cartella…** per raggiungere Application Support.

In questa cartella trovi:

| Contenuto | Scopo |
| --- | --- |
| `drafts/<template-id>.json` | Una bozza per questionario |
| `templates/*.md` | Questionari personali importati |
| `appdraft.log` | Log di avvio ed errori non gestiti |

Le impostazioni semplici, come dimensione finestra e ultimo questionario, sono conservate separatamente da Qt QSettings nel profilo utente. I template iniziali sono dentro l'app; gli export restano nelle posizioni scelte dall'utente.

Per un backup, chiudi AppDraft e copia la cartella dati personale; copia separatamente gli export che vuoi conservare. Su un altro computer, dopo aver chiuso l'app, puoi ripristinare bozze e template nello spazio personale corrispondente, conservando prima eventuali dati già presenti. Non c'è sincronizzazione automatica tra computer.

Spostare o aggiornare l'app sullo stesso computer non sposta né cancella le bozze. Spostare il solo eseguibile su un altro computer non trasferisce le risposte.

## Problemi comuni

| Problema | Cosa fare |
| --- | --- |
| Template rifiutato | Leggi il campo/riga segnalato e correggi il YAML; consulta [templates.md](templates.md) |
| Bozza corrotta o incompatibile | L'app conserva il file e sospende l'autosalvataggio. Fai un backup; **Salva bozza** permette di sostituirlo con conferma |
| Salvataggio non riuscito | Verifica permessi e spazio nella cartella dati, poi riprova. L'app impedisce la chiusura con modifiche non salvate |
| Export non riuscito | Scegli una destinazione scrivibile e verifica spazio e permessi |
| Errore non gestito | Il dialog indica il percorso di `appdraft.log`; consulta il log per i dettagli |

Se una bozza protetta ha modifiche in attesa, anche cambiare template o chiudere l'app richiede una decisione sul salvataggio. Non vengono convertite automaticamente bozze di versioni diverse.
