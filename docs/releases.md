# Versioni e rilascio

[README](../README.md) · [Sviluppo](development.md) · [Packaging](packaging.md)

`scripts/release.py` è uno strumento di sviluppo riutilizzabile, separato dall'app distribuita. Richiede Python 3.11+ e Git, senza librerie Python aggiuntive. AppDraft richiede comunque Python 3.12+ e l'ambiente di sviluppo per test e build.

## AppDraft

Esegui dalla radice del progetto, dopo aver committato tutte le modifiche. La versione proviene da `[project].version` in `pyproject.toml`; anche il bundle macOS legge questa fonte durante la build.

### Comandi brevi con pnpm o npm

Se hai Node.js e pnpm, usa uno dei seguenti comandi dalla radice. I comandi pnpm/npm e GitHub CLI (`gh`) in questa guida sono identici su macOS (Terminale: zsh/bash) e Windows (PowerShell); sono riportati in blocchi di testo comuni:

```text
pnpm version:patch
pnpm version:minor
pnpm version:major
```

Ogni comando incrementa la versione, esegue i test, produce la build per il sistema corrente e crea commit e tag locali. Esegui soltanto quello del livello desiderato. Non occorre `pnpm install`: questi alias non hanno dipendenze Node e usano direttamente l'interprete della `.venv`, senza richiedere di attivarla.

Puoi aggiungere le opzioni dello script:

```text
pnpm version:minor --dry-run
pnpm version:minor --push
pnpm version:minor --release
```

Il primo mostra soltanto il piano; il secondo esegue il rilascio e invia anche commit e tag; il terzo pubblica anche una GitHub Release con la build allegata. Sono alternative, non passaggi da ripetere dopo un rilascio locale: per inviare una release già creata usa Git e GitHub CLI, senza incrementare nuovamente la versione.

Con npm gli equivalenti sono `npm run version:minor` e `npm run version:minor -- --push`. Per vedere tutte le opzioni: `pnpm version:minor --help`. Il launcher `scripts/release.mjs` funziona anche su macOS/Linux, selezionando `.venv/bin/python`.

`package.json` contiene solo questi comandi di sviluppo, senza una versione dell'app. Python e `pyproject.toml` restano la fonte della versione; Node.js/pnpm sono opzionali e non entrano nella build distribuita.

### Comandi Python diretti

Windows (PowerShell):

```powershell
# Anteprima: controlli preliminari e piano, nessuna modifica né test/build
.\.venv\Scripts\python.exe scripts/release.py patch --dry-run

# Incremento, test, build per il sistema corrente, commit e tag locali
.\.venv\Scripts\python.exe scripts/release.py patch --build

# In alternativa: stessi passaggi con pubblicazione su origin
.\.venv\Scripts\python.exe scripts/release.py patch --build --push
```

macOS (Terminale):

```bash
# Anteprima: controlli preliminari e piano, nessuna modifica né test/build
./.venv/bin/python scripts/release.py patch --dry-run

# Incremento, test, build per il sistema corrente, commit e tag locali
./.venv/bin/python scripts/release.py patch --build

# In alternativa: stessi passaggi con pubblicazione su origin
./.venv/bin/python scripts/release.py patch --build --push
```

Per ciascun sistema, i due comandi di rilascio sono alternative: eseguirli entrambi incrementa due volte la versione. I percorsi espliciti della `.venv` funzionano senza attivarla.

`--build` usa il comando configurato in `[tool.release].build`; i test in `[tool.release].checks` vengono eseguiti anche senza `--build`. `{python}` indica l'interprete con cui esegui lo script, quindi usa quello della `.venv`. I comandi vengono eseguiti dopo l'aggiornamento dei file di versione, prima del commit. Test e build devono lasciare invariati i sorgenti; gli artefatti devono essere esclusi da Git.

`--push` pubblica il branch corrente e soltanto il tag appena creato, con un unico push atomico. Il server deve supportarlo: non c'è un ripiego su due push separati. Per creare anche una GitHub Release e allegare la build usa `--release`. Non vengono prodotti installer. Per verificare gli artefatti sul sistema target vedi [packaging](packaging.md).

### Pubblicare su GitHub con un solo comando

Installa GitHub CLI (`gh`) e autenticala una volta con:

```text
gh auth login
```

Dopo aver committato le modifiche, scegli uno di questi comandi:

```text
pnpm version:patch --release
pnpm version:minor --release
pnpm version:major --release
```

`--release` implica build e push. Prima di modificare la versione controlla autenticazione, accesso in scrittura al repository e assenza della nuova release, comprese le bozze. Il repository viene ricavato dall'URL di push del remoto scelto, anche usando `--remote`; non dipende dal repository predefinito di `gh`. Il remoto deve avere un solo URL di push HTTPS o SSH. Le credenziali devono consentire anche le operazioni sulle release.

Il flusso è: aggiornamento versione → test → build → verifica artefatti → commit → tag → push atomico → GitHub Release in bozza con note generate → upload degli artefatti → pubblicazione. Le release stabili vengono marcate come Latest; le prerelease vengono marcate come tali e non diventano Latest. Le release precedenti restano disponibili. La bozza è un passaggio automatico: se tutto riesce, il comando la pubblica senza ulteriori operazioni manuali.

Per AppDraft gli allegati sono configurati in `[tool.release.assets]`: `dist/AppDraft.exe` su Windows e `dist/AppDraft.app` su macOS. Il bundle macOS viene compresso con `ditto` in `dist/AppDraft.app.zip` prima del commit. Il comando pubblica la build del sistema corrente; non genera anche quella degli altri sistemi.

Per verificare il piano e l'accesso a GitHub senza build né pubblicazione:

```text
pnpm version:minor --release --dry-run
```

L'anteprima richiede comunque una working tree pulita e fa controlli di lettura sul remoto e su GitHub. Con Python diretto, la stessa anteprima è `./.venv/bin/python scripts/release.py minor --release --dry-run` su macOS e `.\.venv\Scripts\python.exe scripts/release.py minor --release --dry-run` su Windows (PowerShell).

Il comportamento usa [GitHub CLI per creare le release](https://cli.github.com/manual/gh_release_create), [caricare gli allegati](https://cli.github.com/manual/gh_release_upload) e [pubblicare la bozza](https://cli.github.com/manual/gh_release_edit).

## Riutilizzo in altri progetti

Copia `scripts/release.py` nel progetto e lancialo dalla sua radice, oppure indica `--root`. Funziona su Windows, macOS e Linux; macOS e Linux richiedono una verifica sul sistema target.

Riconosce un solo file tra:

- `pyproject.toml`: versione statica in `[project].version`, con prerelease Python `a`, `b` o `rc`.
- `package.json`: versione SemVer; aggiorna anche `package-lock.json` e `npm-shrinkwrap.json`, se presenti, senza modificare le versioni delle dipendenze. Un `package.json` privo di `version`, usato solo per alias di sviluppo, viene ignorato dal riconoscimento automatico. Non richiede npm e non esegue gli hook npm `preversion`, `version` o `postversion`. I JSON possono essere riformattati, mantenendo indentazione e terminatori di riga.
- `VERSION`: file di testo contenente soltanto una versione SemVer.

Se più file sono presenti, specifica `--version-file`. Per un client annidato, usa il Python del progetto. Esempi con una `.venv` già creata:

macOS (Terminale):

```bash
./.venv/bin/python scripts/release.py minor --version-file recipestudio.client/package.json --dry-run
```

Windows (PowerShell):

```powershell
.\.venv\Scripts\python.exe scripts/release.py minor --version-file recipestudio.client/package.json --dry-run
```

Tutti i file di versione devono essere già tracciati da Git e trovarsi dentro `--root`. Nei monorepo il controllo della working tree riguarda l'intero repository; i comandi di test/build vengono eseguiti dentro `--root`. Versioni dinamiche, workspace npm coordinati e sincronizzazione di lock Python non sono gestiti automaticamente.

Supporta `major`, `minor`, `patch`, `premajor`, `preminor`, `prepatch` e `prerelease`. Ad esempio, partendo da `1.2.3`, `prepatch --preid rc` produce `1.2.4rc1` in Python e `1.2.4-rc.0` in npm o `VERSION`. Un successivo `prerelease` incrementa il contatore; `patch` promuove la prerelease alla versione stabile. `--preid` ammette `alpha`, `beta` e `rc` (predefinito). Usa lo stesso identificatore per incrementare la stessa serie. Sono supportate solo versioni a tre componenti e queste prerelease; versioni Python post/dev/local e metadati SemVer non sono supportati.

Opzioni aggiuntive:

| Opzione | Effetto |
| --- | --- |
| `--branch main` | Richiede il branch indicato, senza cambiarlo |
| `--remote origin` | Sceglie il remoto per `--push` |
| `--release` | Implica build/push e pubblica una GitHub Release con gli allegati |
| `--asset dist/file.zip` | Sceglie un allegato al posto di quelli configurati; ripetibile, ammette `{version}` |
| `--tag-prefix v` | Prefisso del tag; predefinito `v` |
| `--check JSON` | Aggiunge un comando di verifica; ripetibile |
| `--build-command JSON` | Esegue un comando di build al posto di quello configurato |

I comandi sono array JSON di argomenti, senza shell implicita. Sono ammessi i segnaposto `{python}` e `{version}`. Esempio Windows (PowerShell):

```powershell
.\.venv\Scripts\python.exe scripts/release.py patch --check '["{python}", "-m", "pytest", "-q"]'
```

Lo stesso esempio su macOS (Terminale):

```bash
./.venv/bin/python scripts/release.py patch --check '["{python}", "-m", "pytest", "-q"]'
```

Per comandi npm su Windows usa l'eseguibile `npm.cmd`, su macOS/Linux `npm`; il comando deve essere disponibile nel PATH. Se serve una shell per un tuo script, dichiarala esplicitamente nell'array. Non copiare la configurazione di test/build di AppDraft in progetti che usano altri strumenti.

Per altri progetti, `--release` richiede un comando di build in `[tool.release].build` oppure `--build-command`, e almeno un allegato via `--asset` o configurazione. `assets` può essere un array comune a tutti i sistemi sotto `[tool.release]`, oppure una tabella `[tool.release.assets]` con array per `win32`, `darwin` e `linux`. I percorsi degli allegati sono relativi a `--root` e devono rimanervi dentro. Gli allegati devono essere file non vuoti, con nomi distinti; l'unica directory supportata è una `.app` su macOS, compressa automaticamente. Non sono supportati pattern glob o etichette `#` nei percorsi.

## Errori e recupero

Lo script rifiuta una working tree sporca, HEAD scollegata da un branch, file ambigui, versioni non supportate, lock npm incoerenti e tag già esistenti. Con `--push` controlla anche il tag remoto e che il branch remoto sia antenato di HEAD. Se il commit remoto non è disponibile localmente o il branch è divergente, aggiorna e riconcilia manualmente il repository prima di riprovare. Non vengono eseguiti fetch, merge o force push automatici.

Prima del commit, un errore ripristina i file di versione originali e li rimuove dallo staging. Eventuali altri file creati o modificati dai controlli e gli artefatti di build restano disponibili per la verifica. I comandi personalizzati e gli hook Git devono essere fidati e non spostare HEAD.

Dopo un commit, un errore conserva il commit e l'eventuale tag per permetterne l'ispezione. Se il push fallisce, controlla il tag e riprova il comando di push riportato nell'errore: non eseguire nuovamente il bump. Lo script non cancella commit o tag e non sovrascrive la cronologia remota.

Se il push è riuscito ma la creazione/upload/pubblicazione GitHub fallisce, non rilanciare `version:patch/minor/major`. Controlla lo stesso tag con `gh release view TAG --repo HOST/OWNER/REPO` e continua la pubblicazione:

- Se non esiste una release, creala con `gh release create TAG --repo HOST/OWNER/REPO --verify-tag --generate-notes --draft`.
- Se esiste una bozza, carica soltanto gli allegati mancanti con `gh release upload TAG dist/AppDraft.exe --repo HOST/OWNER/REPO` (su macOS usa lo ZIP).
- Dopo aver verificato note e allegati, pubblica la bozza con `gh release edit TAG --repo HOST/OWNER/REPO --draft=false --latest`.

Sostituisci `TAG` e `HOST/OWNER/REPO` con quelli riportati nell'errore. Per una prerelease usa `--prerelease` durante la creazione e `--latest=false` durante la pubblicazione. Se la release risulta già pubblicata, verifica il suo contenuto prima di qualsiasi intervento. Lo script non sovrascrive allegati esistenti e non modifica release precedenti.
