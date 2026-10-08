# Architettura della repo

[README](../README.md) · [Sviluppo](development.md) · [Formato template](templates.md)

AppDraft è un'applicazione desktop locale per un singolo utente. Il codice separa modelli, parsing, editor e operazioni su file. Usa Python e Qt, senza backend, database, networking applicativo, async o framework di dependency injection.

## Flusso dei dati

```text
Markdown incorporati + Markdown personali
                    ↓
             TemplateService
                    ↓
             TemplateParser
                    ↓
       QuestionnaireTemplate / Section / Question
                    ↓
    QuestionnaireView + FormRenderer
                    ↓
            dict di risposte
              ↙           ↘
      DraftService      ExportService
          ↓               ↓
       JSON locale    Markdown → preview / file .md
```

La UI riceve modelli Python e non interpreta il frontmatter. Preview ed export condividono la stessa generazione Markdown; non c'è un renderer HTML.

## Struttura e responsabilità

| Percorso | Responsabilità |
| --- | --- |
| `app.py` | Avvio dal checkout |
| `pyproject.toml` | Dipendenze, entry point, package data e configurazione pytest |
| `AppDraft.spec` | Packaging Windows e macOS con risorse incluse |
| `src/questionnaire_tool/application.py` | Argomenti, QApplication, percorsi, log e finestra principale |
| `models/template.py` | Modelli Pydantic e validazione di configurazione e risposte |
| `models/answers.py` | Modello Draft, risposte iniziali e calcolo del progresso |
| `parser/markdown_template.py` | Estrazione frontmatter, YAML sicuro, chiavi duplicate e diagnostica |
| `services/template_service.py` | Discovery e importazione dei template |
| `services/data_service.py` | Preparazione della cartella personale e copia iniziale della vecchia V1 |
| `services/draft_service.py` | Caricamento e salvataggio delle bozze |
| `services/export_service.py` | Markdown, nome suggerito e scrittura dell'export |
| `renderer/form_renderer.py` | Editor Qt costruiti in base al tipo di domanda |
| `renderer/widgets/scroll_safe.py` | Editor che inoltrano la rotella al form |
| `ui/` | Sidebar, form scrollabile, preview e coordinamento della finestra |
| `resources/templates/` | Questionari iniziali inclusi nel pacchetto Python |
| `resources/icons/` | Icone PNG, ICO e ICNS incluse nel pacchetto |
| `scripts/generate_icons.py` | Generazione degli asset dall'icona sorgente `Icon.png` |
| `tests/` | Verifiche del core, della distribuzione e dei flussi Qt |
| `docs/` | Documentazione del progetto |

I percorsi da `models/` a `resources/` sono relativi a `src/questionnaire_tool/`. I servizi usano Python e librerie di parsing/validazione; non dipendono da Qt.

Lo script di generazione delle icone è invece relativo alla radice della repo. QApplication usa l'icona PNG globale, ereditata dalle finestre; la spec associa ICO all'eseguibile Windows e ICNS al bundle macOS.

## Template e risposte sono separati

`QuestionnaireTemplate` descrive nome, versione e sezioni. Ogni `Section` contiene domande `Question`, con ID, tipo e configurazione. Pydantic rifiuta tipi sconosciuti, chiavi extra, ID duplicati e configurazioni incoerenti.

Le risposte sono un dizionario separato, indicizzato dall'ID di domanda. `FormRenderer` inizializza gli editor con questi valori e collega i loro cambiamenti a una callback. `QuestionnaireView` emette `answer_changed`; `MainWindow` aggiorna il dizionario, il progresso e il timer di autosalvataggio.

Una risposta assente è `None`. I booleani usano tre stati; numeri e scale hanno una spunta per distinguere assenza da zero o da un valore minimo. I default del template inizializzano le risposte prima del ripristino della bozza.

## Risorse incluse e dati personali

`application.py` trova i template incorporati rispetto al proprio `__file__`: lo stesso percorso relativo funziona nel checkout, nel pacchetto Python e nelle risorse della build PyInstaller. Non dipende dalla directory corrente.

I file Markdown sono dichiarati come package data in `pyproject.toml`; la spec PyInstaller li raccoglie con `collect_data_files`. Le risorse incorporate non vengono usate come destinazione delle bozze.

Qt `AppLocalDataLocation` determina la cartella personale. `--data-dir` consente di sostituirla. I percorsi e le istruzioni di backup sono documentati in [usage.md](usage.md).

`TemplateService` carica prima i template incorporati, poi quelli personali. Un ID personale valido sostituisce quello incorporato in memoria. ID duplicati nella stessa cartella sono errori; un file personale non valido non elimina il corrispondente template incorporato valido.

## Persistenza

Ogni ID di template ha un file `drafts/<id>.json`, con `template_id`, `template_version`, `updated_at` UTC e `answers`. Il caricamento controlla identità, versione, ID delle domande e validità delle risposte.

Il salvataggio scrive un file temporaneo nella stessa directory e lo sostituisce con `os.replace`, per evitare JSON troncati durante una normale scrittura. L'autosalvataggio usa un QTimer di 650 ms, riavviato a ogni cambiamento. Cambio template e chiusura salvano prima di proseguire.

Una bozza non leggibile o incompatibile resta sul disco; la UI ne protegge la sostituzione con una conferma. Il programma non converte automaticamente i dati tra versioni del questionario.

QSettings conserva soltanto geometria, ultimo template e cartella di export. Non contiene le risposte e resta separato anche quando si usa `--data-dir`.

## Export e gestione errori

`ExportService.generate` valida le risposte e le dispone nell'ordine del template. Produce metadata YAML, sezioni, domande, valori e istruzioni AI fisse. `MainWindow` presenta il testo in `PreviewDialog` oppure sceglie un percorso con QFileDialog e richiama la scrittura del servizio.

Parser e servizi espongono errori comprensibili, mostrati nei dialog della UI. I template non validi non bloccano la discovery degli altri. Il bootstrap gestisce l'impossibilità di preparare la cartella dati; l'exception hook registra gli errori non gestiti nel log.

## Estensione e limiti V1

Per aggiungere un questionario bastano dati Markdown. Un nuovo tipo di domanda richiede invece di aggiornare modello, validazione, renderer ed eventualmente export, insieme ai relativi test.

La V1 mantiene una bozza per template e non include scritture concorrenti, sync tra computer, cifratura dei dati, campi condizionali, wizard, migrazioni di versione o aggiornamenti automatici. Queste funzioni vanno introdotte quando esiste un requisito concreto.
