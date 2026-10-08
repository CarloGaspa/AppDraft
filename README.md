# AppDraft

Applicazione desktop locale per compilare questionari definiti in Markdown, conservare bozze JSON e generare documenti leggibili da persone e AI. Non usa rete, server o database. UI in italiano, tema e dialog file nativi Qt.

## Requisiti

Python 3.12 o successivo, PySide6, PyYAML e Pydantic 2. Windows è il target iniziale; il codice usa API cross-platform anche per macOS e Linux.

## Setup e avvio

Dalla cartella del progetto:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
python app.py
```

Se PowerShell impedisce l'attivazione, esegui direttamente:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe app.py
```

Su macOS/Linux attiva con `source .venv/bin/activate`. Per il solo utilizzo è sufficiente `pip install -e .`; l'extra `dev` installa pytest e PyInstaller. È disponibile anche il comando `appdraft` nell'ambiente virtuale.

Le cartelle `templates/`, `drafts/`, `exports/` vengono risolte dalla radice del progetto, indipendentemente dalla directory corrente. Per un'altra cartella scrivibile: `python app.py --data-dir "D:\Dati\AppDraft"`. Questa deve contenere i template in `templates/`.

## Utilizzo

1. Seleziona **Technology Stack Assessment** nella sidebar.
2. Compila il questionario scrollabile: `*` indica un campo obbligatorio. Il template iniziale contiene 20 sezioni, 39 domande e 11 campi obbligatori.
3. Numeri e scale senza default richiedono la spunta **Risposta**. I booleani hanno tre stati: intermedio = non compilato, spuntato = sì, vuoto = no. No e zero contano come risposte valide.
4. Le modifiche sono salvate dopo 650 ms senza ulteriori cambiamenti; cambio template e chiusura salvano immediatamente. **Salva bozza** permette anche un salvataggio manuale.
5. **Preview** mostra Markdown testuale e permette di copiarlo. **Esporta .md** apre il dialog di sistema. L'export è consentito anche se incompleto: i valori assenti sono indicati come *Non compilato*.

Le bozze sono in `drafts/<template-id>.json`, con ID, versione, data UTC e risposte. Una bozza compatibile viene ripristinata automaticamente. Una bozza corrotta o incompatibile viene conservata e l'autosalvataggio sospeso; il salvataggio manuale chiede se sostituirla. Se un salvataggio fallisce, l'app resta aperta per consentire di correggere il problema e riprovare.

QSettings conserva solo geometria della finestra, ultimo questionario e ultima directory di export. Il progresso misura i campi obbligatori; con zero obbligatori indica 100%.

## Creare un nuovo template

Copia un file `.md` UTF-8 in `templates/`, quindi riavvia l'app o premi **Ricarica template**. Non servono modifiche Python. Il frontmatter YAML deve iniziare alla prima riga ed essere delimitato da `---`. Il corpo Markdown viene letto come introduzione del modello; la UI mostra `name` e `description`, e l'export contiene domande e risposte ordinate.

```yaml
---
id: nuovo-progetto
name: "Nuovo questionario"
version: 1
description: "Una breve descrizione"
sections:
  - id: prodotto
    title: "Prodotto"
    description: "Descrivi cosa vuoi costruire."
    questions:
      - id: project_name
        label: "Nome progetto"
        type: text
        required: true
        placeholder: "Es. AppDraft"
      - id: piattaforme
        label: "Piattaforme"
        type: multi_select
        options: [Windows, macOS, Linux]
      - id: importanza
        label: "Importanza"
        type: scale
        min: 1
        max: 5
        default: 3
        help: "1 = bassa, 5 = alta"
---
# Nuovo questionario
```

Gli ID devono iniziare con una lettera minuscola e contenere solo lettere minuscole, numeri, `_` o `-`. ID di template e ID di domande devono essere unici, rispettivamente nella directory e nel questionario; anche gli ID di sezione devono essere unici. `version` è un intero positivo: aumentala se cambi la struttura o il significato delle domande. Le versioni incompatibili non vengono migrate automaticamente. Le chiavi sconosciute e duplicate sono errori, così gli errori di battitura non sono ignorati.

Con PyYAML, i testi `No`, `Yes`, `On` e `Off` devono essere tra virgolette se utilizzati come opzioni o risposte testuali, per evitare che vengano interpretati come booleani.

### Tipi supportati

| Tipo | Widget | Configurazione |
| --- | --- | --- |
| `text` | QLineEdit | Testo breve, placeholder opzionale |
| `textarea` | QTextEdit | Testo multilinea semplice |
| `number` | QDoubleSpinBox | `min`, `max` opzionali; fino a 6 decimali |
| `select` | QComboBox | `options` obbligatorie, uniche e non vuote |
| `multi_select` | QCheckBox per opzione | `options` obbligatorie, risposta lista |
| `boolean` | QCheckBox a tre stati | `default: true` / `false`, oppure assente |
| `scale` | QSlider e valore | `min` e `max` interi obbligatori |

Tutti supportano `id`, `label`, `required`, `help` e un `default` del tipo corretto. `placeholder` serve ai campi testuali. `min/max` sono ammessi solo per numeri e scale; i numeri supportano valori assoluti fino a 10^12, le scale l'intervallo intero Qt a 32 bit. Un default valorizzato conta come risposta. Non ci sono dipendenze condizionali, wizard o vincoli sul numero di opzioni selezionate nella V1.

`project_name`, se presente, determina il nome suggerito per l'export, altrimenti viene usato il nome questionario con la data locale. L'export include metadata YAML, tutte le sezioni/domande in ordine e le istruzioni AI fisse. Il contenuto degli editor testuali viene mantenuto come Markdown: può includere liste e formattazione.

## Architettura

`models/` valida template e risposte; `parser/` estrae il YAML; `services/` gestisce discovery, bozze ed export; `renderer/` costruisce editor dai modelli; `ui/` coordina sidebar, form e preview. La UI non analizza il formato del template. Nessun servizio dipende da Qt.

## Test

```powershell
python -m pytest
```

I test coprono parsing, configurazioni non valide, discovery con file errati e ID duplicati, bozze, progresso ed export. Per un controllo operativo: modifica risposte, attendi autosalvataggio, riapri l'app, verifica valori/progresso, apri preview, esporta e aggiungi un secondo template con ID nuovo.

## Packaging standalone

Costruisci su ciascun sistema operativo target. Su Windows:

```powershell
python -m PyInstaller --noconfirm --clean --windowed --onedir --name AppDraft --paths src app.py
Copy-Item -Recurse templates dist\AppDraft\templates
```

Distribuisci l'intera cartella `dist/AppDraft`, comprensiva dei template, e avvia `AppDraft.exe`. Non richiede Python installato. Su macOS/Linux usa lo stesso comando PyInstaller e `cp -R templates dist/AppDraft/templates`, quindi avvia `dist/AppDraft/AppDraft`. La build `onedir` è semplice da diagnosticare e permette di aggiungere template accanto all'eseguibile senza ricompilare.

Bozze ed export sono creati accanto all'eseguibile: scegli una directory scrivibile (non `Program Files`) oppure passa `--data-dir`. Firma digitale, installer e notarizzazione macOS sono passaggi di distribuzione successivi, non inclusi. La V1 è per un solo processo/utente: non gestisce scritture concorrenti, cifratura delle bozze o migrazioni tra versioni dei template.
