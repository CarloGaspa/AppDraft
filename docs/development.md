# Sviluppo, avvio dai sorgenti e comandi

[README](../README.md) · [Architettura](architecture.md) · [Packaging](packaging.md)

Queste istruzioni servono a chi lavora sulla repo. Per aprire l'app pronta con doppio clic vedi [uso su Windows e macOS](usage.md).

## Requisiti

- Python 3.12 o successivo, con `venv` e `pip`.
- PySide6 6.7–6.x, PyYAML 6.x e Pydantic 2.x, installati tramite `pyproject.toml`.
- Extra `dev` per pytest e PyInstaller.

Windows è il target iniziale. Il codice usa API cross-platform; avvio e packaging macOS richiedono verifica su un Mac. Non sono necessari server, Node.js, Docker o servizi esterni. L'installazione delle dipendenze richiede normalmente accesso al loro indice; l'app in esecuzione non usa la rete.

Esegui i comandi seguenti nella radice della repo, quella che contiene `app.py` e `pyproject.toml`. I nomi `.venv` e `.local/test-data` sono relativi a questa directory.

## Windows: setup e primo avvio

In PowerShell, con Python 3.12+ disponibile come `python`:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe app.py
```

Usare direttamente l'interprete della `.venv` evita di dipendere dall'attivazione e dalle regole di esecuzione degli script PowerShell. Se preferisci attivarla:

```powershell
.\.venv\Scripts\Activate.ps1
python app.py
```

Per gli avvii successivi basta:

```powershell
.\.venv\Scripts\python.exe app.py
```

## macOS: setup e primo avvio

In Terminale, con Python 3.12+ disponibile come `python3`:

```bash
python3 --version
python3 -m venv .venv
./.venv/bin/python -m pip install -e ".[dev]"
./.venv/bin/python app.py
```

Se `python3 --version` indica una versione precedente a 3.12, usa il percorso del tuo interprete 3.12+ per creare la `.venv`. La versione di sistema potrebbe non soddisfare il requisito.

L'attivazione è opzionale:

```bash
source .venv/bin/activate
python app.py
```

Per gli avvii successivi basta:

```bash
./.venv/bin/python app.py
```

## Installazione e punti di ingresso

`pip install -e ".[dev]"` installa il progetto in modalità editable: le modifiche Python sono visibili al successivo avvio. Se vuoi solo eseguire dai sorgenti, usa `pip install -e .` senza l'extra.

Dopo l'attivazione della `.venv` sono equivalenti:

```bash
python app.py
appdraft
```

`app.py` configura il percorso `src/` e richiama `questionnaire_tool.application.main`; `appdraft` è l'entry point dichiarato in `pyproject.toml`.

## Opzioni e dati di sviluppo

Con l'ambiente attivato:

```bash
python app.py --help
python app.py --data-dir .local/test-data
```

`--data-dir` imposta una cartella alternativa per bozze, template personali e log. Le sottocartelle vengono create automaticamente e i template incorporati restano disponibili. È utile per provare l'app senza modificare le proprie risposte. `.local/` è esclusa da Git.

Senza questa opzione, anche l'avvio dai sorgenti usa la cartella personale del sistema, condivisa con la build standalone. `--data-dir` non isola le impostazioni QSettings, come geometria finestra e ultimo template: queste restano nel profilo utente.

Al primo uso della cartella personale, l'app copia eventuali file della vecchia V1 da `drafts/*.json` e `templates/*.md` nella radice del progetto. Copia solo se la rispettiva sottocartella personale non esiste ancora e conserva gli originali. Con `--data-dir` questa copia è disattivata. Gli export precedenti non vengono spostati.

## Eseguire i test

Windows:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

macOS:

```bash
./.venv/bin/python -m pytest -q
```

Con la `.venv` attivata puoi usare `python -m pytest -q` su entrambi. La configurazione pytest include `src/` nel percorso Python.

| File | Copertura |
| --- | --- |
| `tests/test_core.py` | Parser, modelli, discovery, bozze, progresso ed export |
| `tests/test_distribution.py` | Risorse incorporate, importazione e copia iniziale dei dati |
| `tests/test_ui_smoke.py` | Compilazione Qt, autosalvataggio, riapertura, preview, export, rotella e importazione |
| `tests/test_release.py` | Incrementi di versione, ripristino su errore e commit/tag/push in repository temporanei |

I test Qt impostano `QT_QPA_PLATFORM=offscreen` se non è già definita e usano dati temporanei. Non richiedono interazione con finestre durante l'esecuzione. Se nuovi comportamenti coinvolgono la UI, verifica anche il relativo flusso su un desktop reale.

## Debug e controllo operativo

Apri la repo nel tuo editor e avvia `app.py` usando l'interprete della `.venv`. Per isolare le risposte usa gli argomenti `--data-dir .local/test-data`.

Per un controllo manuale:

1. Compila almeno testo, scelta, numero e booleano; verifica che la rotella non modifichi i valori.
2. Attendi l'autosalvataggio, chiudi e riapri con la stessa cartella dati.
3. Controlla risposte e progresso, apri preview e copia il Markdown.
4. Esporta con il dialog reale e apri il file risultante.
5. Importa un secondo template con ID nuovo e verifica che resti disponibile alla riapertura.

L'app scrive `appdraft.log` nella cartella dati in uso. Il log registra i template scoperti, il numero di problemi di discovery e i traceback degli errori non gestiti. Gli errori gestiti vengono mostrati nei dialog; non tutti producono un traceback nel log.

Per modificare il modello di un template vedi [templates.md](templates.md); per produrre un eseguibile vedi [packaging.md](packaging.md); per incrementare la versione e creare commit e tag vedi [releases.md](releases.md). Aggiorna la pagina interessata quando cambi un comando, un formato o un comportamento pubblico.
