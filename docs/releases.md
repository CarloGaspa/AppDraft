# Versioni e rilascio

[README](../README.md) · [Sviluppo](development.md) · [Packaging](packaging.md)

`scripts/release.py` è uno strumento di sviluppo riutilizzabile, separato dall'app distribuita. Richiede Python 3.11+ e Git, senza librerie Python aggiuntive. AppDraft richiede comunque Python 3.12+ e l'ambiente di sviluppo per test e build.

## AppDraft

Esegui dalla radice del progetto, dopo aver committato tutte le modifiche. La versione proviene da `[project].version` in `pyproject.toml`; anche il bundle macOS legge questa fonte durante la build.

### Comandi brevi con pnpm o npm

Se hai Node.js e pnpm, usa uno dei seguenti comandi dalla radice:

```powershell
pnpm version:patch
pnpm version:minor
pnpm version:major
```

Ogni comando incrementa la versione, esegue i test, produce la build per il sistema corrente e crea commit e tag locali. Esegui soltanto quello del livello desiderato. Non occorre `pnpm install`: questi alias non hanno dipendenze Node e usano direttamente l'interprete della `.venv`, senza richiedere di attivarla.

Puoi aggiungere le opzioni dello script:

```powershell
pnpm version:minor --dry-run
pnpm version:minor --push
```

Il primo mostra soltanto il piano; il secondo esegue il rilascio e invia anche commit e tag. Sono alternative, non passaggi da ripetere dopo un rilascio locale: per inviare una release già creata usa Git, senza incrementare nuovamente la versione.

Con npm gli equivalenti sono `npm run version:minor` e `npm run version:minor -- --push`. Per vedere tutte le opzioni: `pnpm version:minor --help`. Il launcher `scripts/release.mjs` funziona anche su macOS/Linux, selezionando `.venv/bin/python`.

`package.json` contiene solo questi comandi di sviluppo, senza una versione dell'app. Python e `pyproject.toml` restano la fonte della versione; Node.js/pnpm sono opzionali e non entrano nella build distribuita.

### Comandi Python diretti

In PowerShell:

```powershell
# Anteprima: controlli preliminari e piano, nessuna modifica né test/build
.\.venv\Scripts\python.exe scripts/release.py patch --dry-run

# Incremento, test, build per il sistema corrente, commit e tag locali
.\.venv\Scripts\python.exe scripts/release.py patch --build

# In alternativa: stessi passaggi con pubblicazione su origin
.\.venv\Scripts\python.exe scripts/release.py patch --build --push
```

I due comandi di rilascio sono alternative: eseguirli entrambi incrementa due volte la versione. Su macOS sostituisci `.\.venv\Scripts\python.exe` con `./.venv/bin/python`.

`--build` usa il comando configurato in `[tool.release].build`; i test in `[tool.release].checks` vengono eseguiti anche senza `--build`. `{python}` indica l'interprete con cui esegui lo script, quindi usa quello della `.venv`. I comandi vengono eseguiti dopo l'aggiornamento dei file di versione, prima del commit. Test e build devono lasciare invariati i sorgenti; gli artefatti devono essere esclusi da Git.

`--push` pubblica il branch corrente e soltanto il tag appena creato, con un unico push atomico. Il server deve supportarlo: non c'è un ripiego su due push separati. Non vengono caricate build, create release GitHub o prodotti installer. Per distribuire gli artefatti e verificarli sul sistema target vedi [packaging](packaging.md).

## Riutilizzo in altri progetti

Copia `scripts/release.py` nel progetto e lancialo dalla sua radice, oppure indica `--root`. Funziona su Windows, macOS e Linux; macOS e Linux richiedono una verifica sul sistema target.

Riconosce un solo file tra:

- `pyproject.toml`: versione statica in `[project].version`, con prerelease Python `a`, `b` o `rc`.
- `package.json`: versione SemVer; aggiorna anche `package-lock.json` e `npm-shrinkwrap.json`, se presenti, senza modificare le versioni delle dipendenze. Un `package.json` privo di `version`, usato solo per alias di sviluppo, viene ignorato dal riconoscimento automatico. Non richiede npm e non esegue gli hook npm `preversion`, `version` o `postversion`. I JSON possono essere riformattati, mantenendo indentazione e terminatori di riga.
- `VERSION`: file di testo contenente soltanto una versione SemVer.

Se più file sono presenti, specifica `--version-file`. Per un client annidato:

```powershell
python scripts/release.py minor --version-file recipestudio.client/package.json --dry-run
```

Tutti i file di versione devono essere già tracciati da Git e trovarsi dentro `--root`. Nei monorepo il controllo della working tree riguarda l'intero repository; i comandi di test/build vengono eseguiti dentro `--root`. Versioni dinamiche, workspace npm coordinati e sincronizzazione di lock Python non sono gestiti automaticamente.

Supporta `major`, `minor`, `patch`, `premajor`, `preminor`, `prepatch` e `prerelease`. Ad esempio, partendo da `1.2.3`, `prepatch --preid rc` produce `1.2.4rc1` in Python e `1.2.4-rc.0` in npm o `VERSION`. Un successivo `prerelease` incrementa il contatore; `patch` promuove la prerelease alla versione stabile. `--preid` ammette `alpha`, `beta` e `rc` (predefinito). Usa lo stesso identificatore per incrementare la stessa serie. Sono supportate solo versioni a tre componenti e queste prerelease; versioni Python post/dev/local e metadati SemVer non sono supportati.

Opzioni aggiuntive:

| Opzione | Effetto |
| --- | --- |
| `--branch main` | Richiede il branch indicato, senza cambiarlo |
| `--remote origin` | Sceglie il remoto per `--push` |
| `--tag-prefix v` | Prefisso del tag; predefinito `v` |
| `--check JSON` | Aggiunge un comando di verifica; ripetibile |
| `--build-command JSON` | Esegue un comando di build al posto di quello configurato |

I comandi sono array JSON di argomenti, senza shell implicita. Sono ammessi i segnaposto `{python}` e `{version}`. Esempio PowerShell:

```powershell
python scripts/release.py patch --check '["{python}", "-m", "pytest", "-q"]'
```

Per comandi npm su Windows usa l'eseguibile `npm.cmd`, su macOS/Linux `npm`; il comando deve essere disponibile nel PATH. Se serve una shell per un tuo script, dichiarala esplicitamente nell'array. Non copiare la configurazione di test/build di AppDraft in progetti che usano altri strumenti.

## Errori e recupero

Lo script rifiuta una working tree sporca, HEAD scollegata da un branch, file ambigui, versioni non supportate, lock npm incoerenti e tag già esistenti. Con `--push` controlla anche il tag remoto e che il branch remoto sia antenato di HEAD. Se il commit remoto non è disponibile localmente o il branch è divergente, aggiorna e riconcilia manualmente il repository prima di riprovare. Non vengono eseguiti fetch, merge o force push automatici.

Prima del commit, un errore ripristina i file di versione originali e li rimuove dallo staging. Eventuali altri file creati o modificati dai controlli e gli artefatti di build restano disponibili per la verifica. I comandi personalizzati e gli hook Git devono essere fidati e non spostare HEAD.

Dopo un commit, un errore conserva il commit e l'eventuale tag per permetterne l'ispezione. Se il push fallisce, controlla il tag e riprova il comando di push riportato nell'errore: non eseguire nuovamente il bump. Lo script non cancella commit o tag e non sovrascrive la cronologia remota.
