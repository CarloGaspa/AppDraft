# Build e distribuzione senza installazione

[README](../README.md) · [Setup di sviluppo](development.md) · [Avvio dell'app pronta](usage.md)

L'obiettivo è distribuire un solo elemento: `AppDraft.exe` su Windows oppure `AppDraft.app` su macOS. Python, Qt e i template iniziali sono inclusi; l'utente apre l'app con doppio clic.

La configurazione è in [AppDraft.spec](../AppDraft.spec). Costruisci su ciascun sistema target: una build Windows non è una build macOS. La build Windows è stata generata e verificata in questa repo; quella macOS va eseguita e verificata su un Mac.

## Prima della build

Completa il [setup](development.md) con l'extra `dev`, che installa anche PyInstaller. Esegui i comandi dalla radice della repo. Inserisci gli eventuali template da distribuire in `src/questionnaire_tool/resources/templates/` prima della build.

Non vengono inclusi i tuoi draft, template personali o export. Le risorse raccolte dalla spec provengono dal pacchetto Python, mentre i dati dell'utente sono conservati separatamente.

## Icona dell'app

`Icon.png` nella radice della repo è il sorgente grafico. Le versioni pronte per l'uso sono incluse in `src/questionnaire_tool/resources/icons/`: PNG per la finestra Qt, ICO multi-risoluzione per l'eseguibile Windows e ICNS per il bundle macOS.

Se sostituisci `Icon.png`, rigenera gli asset con la `.venv` attivata, poi ricostruisci l'app:

```bash
python scripts/generate_icons.py
```

Lo script usa PySide6 e la libreria standard, conserva la trasparenza e richiede un'immagine quadrata. Non servono convertitori esterni. Gli asset generati vanno conservati nella repo e sono inclusi nel pacchetto: l'utente finale non deve avere `Icon.png` accanto all'app.

## Windows: creare il singolo eseguibile

In PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean AppDraft.spec
```

Il risultato da condividere è **`dist/AppDraft.exe`**. Puoi aprirlo da Esplora file con doppio clic. Non distribuire `build/`, `.venv/`, il codice sorgente o cartelle di template accanto all'eseguibile.

La build usa il bootloader senza console e la modalità `onefile`: a ogni avvio PyInstaller estrae le proprie risorse in una cartella temporanea. Le bozze vengono salvate nella cartella dati personale del sistema, non in questa cartella temporanea.

Il singolo file comprende Python e Qt: non elimina il peso delle dipendenze. Il primo avvio può richiedere più tempo rispetto all'avvio dai sorgenti.

## macOS: creare la singola applicazione

Sul Mac, in Terminale:

```bash
./.venv/bin/python -m pytest -q
./.venv/bin/python -m PyInstaller --noconfirm --clean AppDraft.spec
```

La spec usa `EXE`, `COLLECT` e `BUNDLE` e produce **`dist/AppDraft.app`**. Finder la mostra come un solo elemento; distribuisci l'intero bundle, senza separarne i file interni. Puoi aprirla con doppio clic oppure, per una prova da Terminale:

```bash
open dist/AppDraft.app
```

Per condividerla in uno ZIP che conservi struttura e permessi:

```bash
ditto -c -k --sequesterRsrc --keepParent dist/AppDraft.app dist/AppDraft-macOS.zip
```

L'utente estrae lo ZIP e apre `AppDraft.app`; può spostarla in Applicazioni, ma non è richiesto. Non occorre distribuire separatamente la directory intermedia `dist/AppDraft`.

La configurazione usa l'architettura dell'ambiente di build. Produci e verifica pacchetti distinti per Intel e Apple Silicon se vuoi supportare entrambi: la spec attuale non configura un binario universale. La compatibilità con versioni specifiche di Windows/macOS va verificata sulle macchine target, in relazione anche a Python e PySide6 utilizzati.

## Verificare la distribuzione

1. Copia solo l'artefatto finale in un'altra cartella, priva di sorgenti e template esterni; su macOS verifica anche il bundle estratto dallo ZIP.
2. Aprilo con doppio clic e controlla che **Technology Stack Assessment** sia disponibile.
3. Compila campi diversi, attendi il salvataggio, chiudi e riapri.
4. Controlla risposte, progresso, preview, copia ed export con i dialog reali.
5. Importa un template personale e verifica che venga ripristinato al successivo avvio.
6. Ripeti la prova su una macchina target senza l'ambiente Python di sviluppo.

I test Qt simulano alcuni dialog per verificare il comportamento; non sostituiscono il controllo dei file picker e dell'avvio sul sistema finale.

## Dati, aggiornamenti e compatibilità

Puoi sostituire l'eseguibile o la `.app` lasciando i dati personali nel profilo utente. I template incorporati seguono la nuova build; i template personali con lo stesso ID continuano ad avere precedenza.

Prima di un aggiornamento conserva un backup delle bozze e dei template personali. Se cambia la versione di un template, l'app conserva la bozza precedente e ne segnala l'incompatibilità, senza convertirla. Per i percorsi e la copia iniziale dei dati della vecchia V1 vedi [uso](usage.md) e [sviluppo](development.md).

## Firma e stato della release

La spec corrente non configura firma Windows, firma macOS o notarizzazione. Le build locali sono quindi non firmate e il sistema può mostrarne avvisi o impedirne l'apertura secondo le proprie impostazioni. La firma/notarizzazione è un passaggio di release successivo per distribuire pubblicamente l'app.

Lo [script di rilascio](releases.md) coordina versione, test, build opzionale, commit e tag, con push opzionale. Con `pnpm version:minor --release` pubblica anche una GitHub Release con la build del sistema corrente allegata (richiede GitHub CLI autenticata). Non sono inclusi installer o aggiornamenti automatici. `build/` e `dist/` sono artefatti generati ed esclusi da Git; chi clona la repo deve costruire la propria app oppure scaricarla dalla release.
