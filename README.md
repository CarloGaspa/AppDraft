# AppDraft

Applicazione desktop locale per compilare questionari definiti in Markdown, salvare bozze e generare specifiche condivisibili con persone e AI. Usa Python, PySide6, PyYAML e Pydantic; non richiede server, cloud o database.

## Aprire l'app pronta

- **Windows:** doppio clic su `AppDraft.exe`.
- **macOS:** estrai l'eventuale ZIP e fai doppio clic su `AppDraft.app`.

I template iniziali sono inclusi. Non servono installer, Python, VS Code, terminale o cartelle di supporto da preparare. Le bozze vengono gestite automaticamente nella cartella dati personale del sistema; gli export sono salvati dove scegli tu.

La build Windows viene prodotta in `dist/AppDraft.exe`; quella macOS viene prodotta in `dist/AppDraft.app`. Con `pnpm version:patch --release`, GitHub Actions costruisce Windows x64, macOS Apple Silicon e macOS Intel e pubblica i tre download nella stessa release; serve prima configurare il workflow come descritto nella [guida release](docs/releases.md). Gli artefatti `dist/` non sono inclusi in Git. Vedi [uso dell'app su Windows e macOS](docs/usage.md) e [packaging](docs/packaging.md).

## Avvio rapido dai sorgenti

Serve **Python 3.12+**. Apri il terminale nella radice della repo, quella che contiene `app.py` e `pyproject.toml`, e segui i comandi per il tuo sistema. Per i dettagli vedi il [setup Windows o macOS](docs/development.md).

### macOS (Terminale: zsh o bash)

Su macOS usa `python3` per creare l'ambiente; `python` diventa disponibile dopo l'attivazione della `.venv`.

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python app.py
```

Per gli avvii successivi, dalla radice della repo:

```bash
source .venv/bin/activate
python app.py
```

### Windows (PowerShell)

Con Python 3.12+ disponibile come `python`:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe app.py
```

Per gli avvii successivi, dalla radice della repo:

```powershell
.\.venv\Scripts\python.exe app.py
```

Su Windows questi comandi usano direttamente l'interprete della `.venv`, senza dover attivare script PowerShell. Se il comando `python` non è disponibile ma hai il launcher `py`, usa `py -3 --version` e `py -3 -m venv .venv`, verificando che la versione sia almeno 3.12.

### Verificare il progetto

L'extra `dev` include pytest e PyInstaller. Esegui i test con l'interprete del progetto:

macOS:

```bash
./.venv/bin/python -m pytest -q
```

Windows (PowerShell):

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Funzioni principali

- Form dinamici da template Markdown con frontmatter YAML.
- Bozze JSON, autosalvataggio, ripristino e progresso dei campi obbligatori.
- Preview testuale, copia negli appunti ed export Markdown con istruzioni AI.
- Template iniziali incorporati e importazione di questionari personali.

Il questionario **Technology Stack Assessment** comprende 20 sezioni, 39 domande e 11 campi obbligatori. La V1 conserva una bozza per template e non sincronizza dati tra computer.

## Documentazione

| Guida | Contenuto |
| --- | --- |
| [Uso](docs/usage.md) | Avvio su Windows/macOS, compilazione, bozze, export, backup e problemi comuni |
| [Sviluppo](docs/development.md) | Requisiti, setup per entrambi i sistemi, comandi, test e debug |
| [Architettura](docs/architecture.md) | Struttura della repo, responsabilità, flusso dei dati e limiti |
| [Template](docs/templates.md) | Formato YAML/Markdown, tipi di domanda, validazione e versioni |
| [Packaging](docs/packaging.md) | Build del singolo `.exe` o della `.app`, distribuzione e verifica |
| [Release](docs/releases.md) | Versioni, controlli, build, commit, tag, push e GitHub Release con allegati |

Ogni guida contiene i dettagli del proprio argomento. Aggiorna la documentazione insieme alle modifiche che cambiano comandi, formati o comportamento dell'app.
