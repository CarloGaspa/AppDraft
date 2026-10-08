# AppDraft

Applicazione desktop locale per compilare questionari definiti in Markdown, salvare bozze e generare specifiche condivisibili con persone e AI. Usa Python, PySide6, PyYAML e Pydantic; non richiede server, cloud o database.

## Aprire l'app pronta

- **Windows:** doppio clic su `AppDraft.exe`.
- **macOS:** estrai l'eventuale ZIP e fai doppio clic su `AppDraft.app`.

I template iniziali sono inclusi. Non servono installer, Python, VS Code, terminale o cartelle di supporto da preparare. Le bozze vengono gestite automaticamente nella cartella dati personale del sistema; gli export sono salvati dove scegli tu.

La build Windows viene prodotta in `dist/AppDraft.exe`; quella macOS in `dist/AppDraft.app` va costruita e verificata su un Mac. Gli artefatti `dist/` non sono inclusi in Git. Vedi [uso dell'app su Windows e macOS](docs/usage.md) e [packaging](docs/packaging.md).

## Avvio rapido dai sorgenti

Serve **Python 3.12+**. Dalla radice della repo crea un ambiente virtuale e installa le dipendenze seguendo il [setup Windows o macOS](docs/development.md). Con l'ambiente attivato:

```bash
python -m pip install -e ".[dev]"
python app.py
```

L'extra `dev` include pytest e PyInstaller. Per verificare il progetto:

```bash
python -m pytest -q
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

Ogni guida contiene i dettagli del proprio argomento. Aggiorna la documentazione insieme alle modifiche che cambiano comandi, formati o comportamento dell'app.
