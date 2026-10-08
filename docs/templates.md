# Formato e gestione dei template

[README](../README.md) · [Uso dell'app](usage.md) · [Architettura](architecture.md)

Un questionario è un file `.md` UTF-8 con frontmatter YAML alla prima riga, delimitato da `---`. La configurazione definisce sezioni e domande; non servono modifiche Python per aggiungere questionari.

## Esempio completo

```markdown
---
id: nuovo-progetto
name: "Nuovo questionario"
version: 1
description: "Descrivi il progetto e le piattaforme richieste."
sections:
  - id: prodotto
    title: "Prodotto"
    description: "Parti dai requisiti principali."
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
        label: "Importanza dell'integrazione nativa"
        type: scale
        min: 1
        max: 5
        default: 3
        help: "1 = bassa, 5 = alta"
      - id: offline
        label: "Deve funzionare offline?"
        type: boolean
---

# Nuovo questionario

Eventuali note Markdown sul questionario.
```

## Campi di questionario e sezione

| Livello | Obbligatori | Facoltativi |
| --- | --- | --- |
| Questionario | `id`, `name`, `version`, `sections` | `description` |
| Sezione | `id`, `title`, `questions` | `description` |
| Domanda | `id`, `label`, `type` | Campi della tabella seguente |

`sections` e `questions` non possono essere liste vuote. Nomi, titoli e label devono contenere testo. `version` è un intero positivo, non una stringa.

Gli ID rispettano `^[a-z][a-z0-9_-]*$`: lettera minuscola iniziale, poi lettere minuscole, numeri, `_` o `-`. Gli ID di domanda devono essere unici nell'intero questionario, non solo nella propria sezione; anche gli ID di sezione devono essere unici. Gli ID dei template sono unici per cartella, con la precedenza personale descritta più avanti.

Il corpo dopo il frontmatter viene conservato dal parser come `introduction`. Attualmente il form mostra `name`, `description` e le sezioni, mentre l'export viene generato dai modelli e dalle risposte: il corpo Markdown originale non viene riportato automaticamente in UI o export.

## Configurazione delle domande

| Campo | Significato | Default |
| --- | --- | --- |
| `required` | Conta nel progresso delle domande obbligatorie | `false` |
| `placeholder` | Suggerimento nell'editor testuale | Assente |
| `help` | Testo di aiuto sotto l'editor e tooltip | Assente |
| `default` | Risposta iniziale valida per il tipo | `null` |
| `options` | Opzioni testuali per le domande a scelta | Lista vuota |
| `min`, `max` | Limiti per numero o scala | Assenti |

`required` non impedisce di salvare o esportare un questionario incompleto. Un default valorizzato conta come risposta già compilata.

## Tipi supportati

| Tipo | Editor | Risposta e vincoli |
| --- | --- | --- |
| `text` | QLineEdit | Stringa breve |
| `textarea` | QTextEdit | Stringa multilinea; testo semplice che può contenere Markdown |
| `number` | QDoubleSpinBox con spunta Risposta | Numero, `min/max` opzionali, editor con 6 decimali |
| `select` | QComboBox | Una stringa presente in `options` |
| `multi_select` | QCheckBox per opzione | Lista di stringhe presenti in `options`, senza duplicati |
| `boolean` | QCheckBox a tre stati | `true`, `false` oppure `null` |
| `scale` | QSlider e label, con spunta Risposta | Intero, con `min` e `max` interi obbligatori |

Per `select` e `multi_select`, `options` deve essere non vuota, con elementi testuali non vuoti e unici. Su altri tipi, opzioni non vuote sono un errore. `min/max` sono ammessi solo per `number` e `scale`, con `min <= max`.

I numeri devono essere finiti e avere valore assoluto non superiore a `10^12`. Le scale devono rientrare nell'intervallo intero Qt da `-2147483648` a `2147483647`. Il default deve rispettare tipo, opzioni e limiti della domanda; per i numeri scegli valori rappresentabili con i 6 decimali dell'editor.

Esempi di default:

```yaml
# text o textarea
default: "Testo iniziale"

# number o scale, se nei limiti
default: 3

# multi_select, se le opzioni esistono
default: [Windows, macOS]

# boolean: false è una risposta, non un valore assente
default: false
```

Le chiavi sconosciute o duplicate vengono rifiutate. Per testi come `No`, `Yes`, `On` e `Off` usa le virgolette: PyYAML può interpretarli come booleani. `required` e i default booleani usano invece `true`/`false` senza virgolette.

## Importare o incorporare un template

Per usarlo nella propria app, premi **Importa template…** e scegli il `.md`. L'app lo valida prima di copiarlo in `<cartella-dati>/templates/<id>.md`. Una sostituzione di un template personale già importato richiede conferma.

La discovery legge i `.md`, anche con estensione maiuscola, dai template incorporati e dalla cartella personale. La versione personale valida ha precedenza se l'ID coincide con quella incorporata. File non validi vengono segnalati; gli altri restano disponibili.

Per includere un nuovo questionario nella distribuzione, aggiungilo a `src/questionnaire_tool/resources/templates/` e ricostruisci l'app seguendo [packaging.md](packaging.md). Il template reale di riferimento è [tech-stack.md](../src/questionnaire_tool/resources/templates/tech-stack.md).

## Versioni e compatibilità delle bozze

Aumenta `version` quando cambi struttura o significato delle domande. Il caricamento delle bozze verifica ID/versione del template e validità delle risposte; non migra automaticamente da una versione all'altra.

Cambiare un ID di domanda, le opzioni o i limiti può rendere non leggibili le risposte precedenti anche se dimentichi di incrementare la versione. Conserva una copia dei dati prima di sostituire un template già utilizzato.

## Convenzioni di export

La domanda con ID `project_name`, se valorizzata con testo, determina il nome suggerito del file. L'ordine di sezioni e domande è quello dichiarato nel YAML. I valori testuali mantengono il contenuto Markdown, le scelte multiple diventano elenchi e le risposte assenti sono indicate come non compilate.

Le istruzioni AI finali sono fisse nel servizio di export, non configurabili nel template nella V1. Non sono supportati campi condizionali, wizard o un vincolo sul numero di opzioni selezionate.
