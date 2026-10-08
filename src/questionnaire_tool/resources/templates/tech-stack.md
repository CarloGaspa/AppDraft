---
id: tech-stack
name: "Technology Stack Assessment"
version: 1
description: "Descrivi requisiti e vincoli per scegliere un'architettura e uno stack semplici e sostenibili. Compila prima i campi obbligatori, poi gli approfondimenti utili."
sections:
  - id: product
    title: "1. Prodotto"
    questions:
      - id: project_name
        label: "Nome del progetto"
        type: text
        required: true
        placeholder: "Es. Soldoni"
      - id: product_description
        label: "Quale problema risolve, per chi e con quale flusso principale?"
        type: textarea
        required: true
        placeholder: "Problema, utenti, flusso e 3–5 funzionalità fondamentali"
      - id: domain_complexity
        label: "Complessità della business logic"
        type: select
        options: [Semplice, Media, Complessa, Molto complessa, Da definire]
  - id: application_type
    title: "2. Tipo di applicazione"
    questions:
      - id: product_type
        label: "Quali categorie descrivono il prodotto?"
        type: multi_select
        required: true
        options: [Web app / SaaS, Sito / contenuti, Mobile, Desktop, Backend / API, CLI / Developer tool, AI / Data, Embedded / IoT, Browser extension, Altro]
  - id: platforms
    title: "3. Piattaforme"
    questions:
      - id: platforms
        label: "Quali piattaforme deve supportare?"
        type: multi_select
        required: true
        options: [Web, iOS, Android, Windows, macOS, Linux, Hardware dedicato]
      - id: platform_strategy
        label: "Strategia tra piattaforme"
        type: select
        options: [Massima condivisione del codice, Migliore esperienza per piattaforma, Compromesso, Da definire]
      - id: platform_priorities
        label: "Priorità e versioni minime delle piattaforme"
        type: text
        placeholder: "Es. Windows subito, macOS dopo; Windows 11+"
  - id: ux
    title: "4. UI/UX"
    questions:
      - id: ui_kind
        label: "Quali caratteristiche deve avere l'interfaccia?"
        type: multi_select
        options: [Form standard, Dashboard / gestionale, UI molto personalizzata, Grafici, Editor complesso, Canvas / diagrammi, Animazioni, 3D, Multimedia, Nessuna UI]
      - id: native_importance
        label: "Importanza dell'esperienza nativa"
        type: scale
        min: 1
        max: 5
        help: "1 = poco importante; 5 = requisito fondamentale."
  - id: device
    title: "5. Integrazione OS/device"
    questions:
      - id: integrations
        label: "Quali integrazioni servono realmente?"
        type: multi_select
        options: [Filesystem / file picker, Drag and drop / clipboard, System tray / menu, Shortcut globali, Notifiche / background, Camera / microfono, GPS, Bluetooth / NFC, Biometria, USB / seriale, Hardware proprietario, Widget / share extensions, Pagamenti device]
      - id: integration_notes
        label: "Vincoli hardware e integrazioni particolari"
        type: text
  - id: offline
    title: "6. Offline e dati locali"
    questions:
      - id: offline_mode
        label: "Quanto deve funzionare senza connessione?"
        type: select
        required: true
        options: [Non necessario, Parzialmente, Completamente, Da definire]
      - id: data_strategy
        label: "Strategia dei dati"
        type: select
        options: [Solo locale, Local-first, Offline-first, Cloud-first, Da definire]
      - id: data_needs
        label: "Dati, volume locale e sincronizzazione necessari"
        type: textarea
        placeholder: "File, dati relazionali, documenti; quantità; sync tra dispositivi, conflitti o collaborazione"
  - id: backend
    title: "7. Backend"
    questions:
      - id: backend_need
        label: "Serve un backend?"
        type: select
        required: true
        options: ["No", Leggero, Importante, Centrale al prodotto, Da definire]
      - id: backend_features
        label: "Funzionalità backend richieste"
        type: multi_select
        options: [Auth / utenti, API / business logic, Pagamenti, Email / push, Storage, Job / queue, Realtime / collaborazione, Webhook / integrazioni, Report / elaborazioni pesanti]
      - id: hosting_constraints
        label: "Vincoli di hosting e gestione infrastruttura"
        type: text
        placeholder: "Es. nessun server; on-premise; managed cloud; regione UE"
  - id: performance
    title: "8. Performance"
    questions:
      - id: workloads
        label: "Workload principali"
        type: multi_select
        options: [CRUD, I/O intensive, CPU intensive, Networking, Realtime, Streaming, Data processing, Video / audio / immagini, Machine learning]
      - id: performance_targets
        label: "Obiettivi misurabili e colli di bottiglia previsti"
        type: text
        placeholder: "Latenza, avvio, memoria, richieste/sec, connessioni o dimensione dati"
  - id: ai_data
    title: "9. AI/Data"
    questions:
      - id: ai_features
        label: "Componenti AI o dati previste"
        type: multi_select
        options: [Nessuna, AI generativa / LLM, Machine learning, Computer vision, NLP, Data analysis / statistica, Scientific computing, Data pipelines, Elaborazione massiva]
      - id: ai_constraints
        label: "Peso delle componenti AI e vincoli di esecuzione"
        type: text
        placeholder: "Centrali o accessorie? Modelli locali/cloud, GPU, privacy, costo per richiesta"
  - id: security
    title: "10. Sicurezza"
    questions:
      - id: security_level
        label: "Livello di sicurezza richiesto"
        type: select
        options: [Standard, Elevato, Critico, Da definire]
      - id: sensitive_data
        label: "Dati sensibili trattati"
        type: multi_select
        options: [Nessuno, Personali, Finanziari, Sanitari, Credenziali / segreti, Pagamenti, Informazioni aziendali]
      - id: security_constraints
        label: "Requisiti normativi e di sicurezza obbligatori"
        type: text
        placeholder: "Es. GDPR, cifratura, audit, ruoli, MFA, SSO, residenza dei dati"
  - id: scale
    title: "11. Scala prevista"
    questions:
      - id: initial_users
        label: "Utenti previsti al lancio"
        type: number
        min: 1
        max: 1000000000
      - id: growth
        label: "Crescita a 1–3 anni e distribuzione geografica"
        type: text
        placeholder: "Es. 100 al lancio, 10.000 a 3 anni, Italia; picchi attesi"
  - id: team
    title: "12. Team"
    questions:
      - id: team_size
        label: "Numero iniziale di sviluppatori"
        type: number
        min: 1
        max: 10000
      - id: team_skills
        label: "Competenze già disponibili e crescita del team"
        type: textarea
        required: true
        placeholder: "Linguaggi, framework, esperienza desktop/mobile/backend, DevOps; assunzioni previste"
  - id: budget
    title: "13. Budget"
    questions:
      - id: budget_level
        label: "Budget iniziale"
        type: select
        required: true
        options: [Minimo, Limitato, Medio, Alto, Da definire]
      - id: budget_limits
        label: "Limiti economici concreti"
        type: text
        placeholder: "Budget sviluppo, infrastruttura/mese, licenze e manutenzione"
  - id: time
    title: "14. Time-to-market"
    questions:
      - id: delivery
        label: "Quando deve uscire la prima versione?"
        type: select
        required: true
        options: [Prototipo immediato, Meno di 1 mese, 1–3 mesi, 3–6 mesi, Oltre 6 mesi, Da definire]
  - id: lifetime
    title: "15. Vita prevista"
    questions:
      - id: lifetime
        label: "Durata attesa del prodotto"
        type: select
        options: [Meno di 1 anno, 1–3 anni, 3–5 anni, 5–10 anni, Oltre 10 anni, Da definire]
  - id: lock_in
    title: "16. Vendor lock-in"
    questions:
      - id: lock_in_tolerance
        label: "Quanto è accettabile dipendere da un fornitore?"
        type: select
        options: [Alto, Medio, Basso, Nessuno, Da definire]
      - id: portability
        label: "Requisiti di portabilità e migrazione"
        type: text
        placeholder: "Es. export completo, standard aperti, sostituzione cloud, deploy on-premise"
  - id: priorities
    title: "17. Priorità"
    questions:
      - id: priorities
        label: "Seleziona le tre priorità principali"
        type: multi_select
        required: true
        options: [Velocità di sviluppo, UX, Performance, Manutenibilità, Sicurezza, Costi, Condivisione codice, Hiring, Scalabilità, Longevità, Portabilità]
        help: "Indica l'ordine di importanza nelle note finali se utile."
  - id: constraints
    title: "18. Vincoli obbligatori"
    questions:
      - id: mandatory_constraints
        label: "Quali vincoli non possono essere negoziati?"
        type: textarea
        required: true
        placeholder: "Tecnologie imposte, sistemi esistenti, licenze, distribuzione, accessibilità; scrivi Nessuno se non presenti"
      - id: open_source_only
        label: "È obbligatorio utilizzare esclusivamente componenti open source?"
        type: boolean
  - id: avoid
    title: "19. Tecnologie da evitare"
    questions:
      - id: avoid_technologies
        label: "Quali tecnologie vuoi escludere e per quale motivo?"
        type: textarea
        placeholder: "Distinguere divieti reali da preferenze del team"
  - id: context
    title: "20. Contesto aggiuntivo"
    questions:
      - id: additional_context
        label: "Alternative già considerate, rischi, esempi e altre informazioni utili"
        type: textarea
        placeholder: "Prototipi, dipendenze esistenti, criteri di successo e dubbi da risolvere"
---

# Technology Stack Assessment

Questionario ispirato alla specifica allegata per la scelta dello stack tecnologico.
Descrivi il problema e i vincoli prima di scegliere tecnologie: l'export include istruzioni per una valutazione architetturale da parte di un'AI.
