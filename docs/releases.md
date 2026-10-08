# Versioni e rilascio

[README](../README.md) · [Sviluppo](development.md) · [Packaging](packaging.md)

`scripts/release.py` è uno strumento di sviluppo riutilizzabile, separato dall'app distribuita. Richiede Python 3.11+ e Git, senza librerie Python aggiuntive. AppDraft richiede comunque Python 3.12+ e l'ambiente di sviluppo per test e build.

## AppDraft: una release per Windows e macOS

Esegui dalla radice del progetto, dopo aver committato tutte le modifiche. La versione proviene da `[project].version` in `pyproject.toml`; anche il bundle macOS legge questa fonte durante la build.

### Configurazione iniziale su GitHub

1. Porta `.github/workflows/release.yml` e gli script aggiornati nel branch predefinito del repository GitHub. Il workflow deve essere presente su quel branch per poterlo avviare con `workflow_dispatch`.
2. Verifica che GitHub Actions sia abilitato per il repository e che le policy consentano al job di pubblicazione di usare `contents: write`.
3. Completa il [setup Python](development.md) con l'extra `dev`. Per i comandi brevi servono anche Node.js e pnpm oppure npm; non occorre `pnpm install`.
4. Installa GitHub CLI (`gh`) e autenticala con `gh auth login`. L'account deve poter fare push, avviare workflow e pubblicare release nel repository. Il workflow usa il `GITHUB_TOKEN` automatico di GitHub, senza un token personale nei file del progetto.

Su macOS con Homebrew puoi installare GitHub CLI così:

```bash
brew install gh
```

L'autenticazione è uguale su macOS (Terminale: zsh/bash) e Windows (PowerShell):

```text
gh auth login
```

### Pubblicare con pnpm o npm

I comandi sono identici su macOS e Windows. Scegli un solo livello:

```text
pnpm version:patch --release
pnpm version:minor --release
pnpm version:major --release
```

Lo script incrementa la versione, esegue i test locali, crea commit e tag, fa push atomico del branch e del tag, poi avvia `release.yml` sul tag appena creato. Con `--release` la build locale viene saltata: tutte le build di distribuzione vengono prodotte su GitHub Actions.

Il comando termina quando GitHub accetta l'avvio del workflow; **la release non è ancora pubblicata**. GitHub esegue i test e PyInstaller su tre macchine e prepara questi download:

| Sistema | Allegato |
| --- | --- |
| Windows x64 | `AppDraft-Windows-x64.exe` |
| macOS Apple Silicon (arm64) | `AppDraft-macOS-arm64.zip` |
| macOS Intel (x64) | `AppDraft-macOS-x64.zip` |

Ogni ZIP macOS contiene l'intera `AppDraft.app`, preservata con `ditto`. Il workflow usa Python 3.12 e runner `windows-2022`, `macos-15` e `macos-15-intel`; le versioni minime dei sistemi supportati devono essere verificate sui computer target. Le build non sono firmate né notarizzate: vedi [packaging](packaging.md).

La pubblicazione parte solo se **tutti e tre i job di build riescono**. Il job finale controlla che gli allegati esistano e non siano vuoti, crea una release in bozza, carica tutti i download e pubblica la release. Le prerelease vengono marcate come tali e non diventano Latest. Le release già pubblicate non vengono modificate.

Per seguire l'esecuzione, apri la scheda **Actions** del repository oppure usa:

```text
gh run list --workflow release.yml
gh run watch RUN_ID
```

Sostituisci `RUN_ID` con l'identificativo mostrato dal primo comando. Questi comandi assumono il repository GitHub della cartella corrente; se usi un altro remoto aggiungi `--repo HOST/OWNER/REPO` indicato dallo script.

Con npm l'equivalente è `npm run version:patch -- --release`. Per vedere il piano e verificare accesso e disponibilità del workflow senza modifiche, build o pubblicazione:

```text
pnpm version:patch --release --dry-run
```

L'anteprima richiede una working tree pulita e fa controlli di lettura su GitHub. Se il workflow non è ancora sul branch predefinito o è disabilitato, lo script si ferma prima di modificare la versione.

### Build e rilascio locali

Senza `--release`, i comandi brevi mantengono la build locale:

```text
pnpm version:patch
pnpm version:minor
pnpm version:major
```

Ogni comando esegue test e build del sistema corrente e crea commit e tag locali. `--push` invia anche branch e tag, ma **non avvia il workflow**. Questi comandi sono alternative a `--release`: eseguirli di nuovo incrementa nuovamente la versione.

### Comandi Python diretti

Usano l'interprete della `.venv`, senza richiedere di attivarla o avere Node.js/pnpm.

macOS (Terminale):

```bash
# Anteprima della release multipiattaforma
./.venv/bin/python scripts/release.py patch --release --dry-run

# In alternativa: test locali, versione, commit/tag/push e avvio GitHub Actions
./.venv/bin/python scripts/release.py patch --release

# In alternativa: test e build locali, commit e tag senza pubblicazione
./.venv/bin/python scripts/release.py patch --build
```

Windows (PowerShell):

```powershell
# Anteprima della release multipiattaforma
.\.venv\Scripts\python.exe scripts/release.py patch --release --dry-run

# In alternativa: test locali, versione, commit/tag/push e avvio GitHub Actions
.\.venv\Scripts\python.exe scripts/release.py patch --release

# In alternativa: test e build locali, commit e tag senza pubblicazione
.\.venv\Scripts\python.exe scripts/release.py patch --build
```

`[tool.release].github-workflow = "release.yml"` seleziona la pubblicazione tramite Actions per AppDraft. I test in `[tool.release].checks` vengono eseguiti localmente anche in questa modalità. Le opzioni `--asset` e `--build-command` non sono ammesse insieme a una release tramite workflow: modifica il workflow per cambiare le build pubblicate. Il workflow verifica che il tag sia `v` seguito dalla versione del progetto; per AppDraft conserva il prefisso predefinito `v`.

### Recuperare un errore senza incrementare la versione

Se i test locali falliscono prima del commit, lo script ripristina i file di versione. Dopo commit e tag, conserva il lavoro già creato e mostra come riprendere.

Se il push riesce ma l'avvio del workflow fallisce, verifica le esecuzioni esistenti e avvia il workflow **sullo stesso tag**, usando il repository indicato dallo script:

```text
gh workflow run release.yml --repo HOST/OWNER/REPO --ref TAG
```

Se una build o un upload fallisce su GitHub, consulta i log in Actions. Puoi rieseguire **tutti i job** della stessa esecuzione, senza creare un'altra versione:

```text
gh run rerun RUN_ID --repo HOST/OWNER/REPO
```

Le build intermedie sono conservate come artifact per sette giorni; rieseguire tutti i job le ricrea anche dopo la scadenza. Se un upload era riuscito solo in parte, il job di pubblicazione riusa la bozza e sostituisce gli allegati di quella bozza prima di pubblicarla. Se la release è già pubblicata, il workflow si ferma e conserva i download esistenti.

Non rieseguire `pnpm version:patch/minor/major` per recuperare una pubblicazione fallita: produrrebbe una nuova versione.

Il workflow usa [runner GitHub Windows e macOS](https://docs.github.com/en/actions/reference/runners/github-hosted-runners), [avvio tramite GitHub CLI sul tag](https://cli.github.com/manual/gh_workflow_run) e [GitHub CLI per creare le release](https://cli.github.com/manual/gh_release_create).

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

Per altri progetti senza `github-workflow`, `--release` mantiene la pubblicazione locale e richiede un comando di build in `[tool.release].build` oppure `--build-command`, e almeno un allegato via `--asset` o configurazione. `assets` può essere un array comune a tutti i sistemi sotto `[tool.release]`, oppure una tabella `[tool.release.assets]` con array per `win32`, `darwin` e `linux`. I percorsi degli allegati sono relativi a `--root` e devono rimanervi dentro. Gli allegati devono essere file non vuoti, con nomi distinti; l'unica directory supportata è una `.app` su macOS, compressa automaticamente. Non sono supportati pattern glob o etichette `#` nei percorsi.

## Errori e recupero dello script generico

Le istruzioni di upload manuale qui sotto riguardano la pubblicazione locale di altri progetti senza `github-workflow`. Per AppDraft usa il recupero tramite Actions descritto sopra.

Lo script rifiuta una working tree sporca, HEAD scollegata da un branch, file ambigui, versioni non supportate, lock npm incoerenti e tag già esistenti. Con `--push` controlla anche il tag remoto e che il branch remoto sia antenato di HEAD. Se il commit remoto non è disponibile localmente o il branch è divergente, aggiorna e riconcilia manualmente il repository prima di riprovare. Non vengono eseguiti fetch, merge o force push automatici.

Prima del commit, un errore ripristina i file di versione originali e li rimuove dallo staging. Eventuali altri file creati o modificati dai controlli e gli artefatti di build restano disponibili per la verifica. I comandi personalizzati e gli hook Git devono essere fidati e non spostare HEAD.

Dopo un commit, un errore conserva il commit e l'eventuale tag per permetterne l'ispezione. Se il push fallisce, controlla il tag e riprova il comando di push riportato nell'errore: non eseguire nuovamente il bump. Lo script non cancella commit o tag e non sovrascrive la cronologia remota.

Se il push è riuscito ma la creazione/upload/pubblicazione GitHub fallisce, non rilanciare `version:patch/minor/major`. Controlla lo stesso tag con `gh release view TAG --repo HOST/OWNER/REPO` e continua la pubblicazione:

- Se non esiste una release, creala con `gh release create TAG --repo HOST/OWNER/REPO --verify-tag --generate-notes --draft`.
- Se esiste una bozza, carica soltanto gli allegati mancanti con `gh release upload TAG dist/AppDraft.exe --repo HOST/OWNER/REPO` (su macOS usa lo ZIP).
- Dopo aver verificato note e allegati, pubblica la bozza con `gh release edit TAG --repo HOST/OWNER/REPO --draft=false --latest`.

Sostituisci `TAG` e `HOST/OWNER/REPO` con quelli riportati nell'errore. Per una prerelease usa `--prerelease` durante la creazione e `--latest=false` durante la pubblicazione. Se la release risulta già pubblicata, verifica il suo contenuto prima di qualsiasi intervento. Lo script non sovrascrive allegati esistenti e non modifica release precedenti.
