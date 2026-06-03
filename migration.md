# Migrationskonzept: Python nach JavaScript/Node.js

Dieses Dokument beschreibt eine pragmatische Migration des bestehenden Python-Projekts nach JavaScript auf Node.js. Ziel ist keine automatische 1:1-Uebersetzung, sondern ein kontrollierter Neuaufbau mit gleichem fachlichen Verhalten, moeglichst wenigen Abhaengigkeiten und ohne TypeScript.

## Ziele

- Bestehende Funktionen aus Python nach Node.js uebernehmen.
- Plain JavaScript verwenden, kein TypeScript-Build-Schritt.
- Abhaengigkeiten klein halten und nur dort einsetzen, wo sie echten Nutzen bringen.
- Python-Projekt waehrend der Migration lauffaehig lassen.
- Migration in kleinen, testbaren Schritten durchfuehren.
- comdirect-API-Verhalten, Datenhaltung, CLI und Weboberflaeche schrittweise nachbilden.

## Nicht-Ziele

- Keine automatische Code-Konvertierung.
- Kein grosser Framework-Wechsel zu einem komplexen Fullstack-System.
- Keine gleichzeitige fachliche Neuentwicklung.
- Keine direkte Loeschung der Python-Implementierung zu Beginn.
- Keine TypeScript-, Babel- oder Transpiler-Pipeline.

## Empfohlener Node-Stack

Um die Abhaengigkeiten klein zu halten, sollte Node.js selbst moeglichst viel uebernehmen.

| Bereich | Empfehlung | Begruendung |
| --- | --- | --- |
| Runtime | Node.js 22 LTS oder neuer | Stabiles `fetch`, moderne JavaScript-Features, kein Transpiler notwendig |
| HTTP-Server | `express` | Klein, bekannt, ausreichend fuer REST und HTML-Routen |
| Templates | `ejs` | Einfacher Ersatz fuer Jinja2 |
| SQLite | `better-sqlite3` | Schlank, synchron, gut fuer lokale Service-Datenbanken |
| CLI | Node-Bordmittel oder `commander` | Bei wenigen Kommandos reicht ggf. `process.argv`; sonst `commander` |
| Scheduler | Node-Bordmittel oder `node-cron` | Fuer einfache periodische Jobs reicht oft `setInterval` |
| Tests | `node:test` | In Node enthalten, keine Jest/Vitest-Abhaengigkeit notwendig |
| Konfiguration | `.env` optional mit `dotenv` | Kann auch rein ueber Umgebungsvariablen laufen |

Minimale Start-Abhaengigkeiten:

```json
{
  "dependencies": {
    "better-sqlite3": "^11.0.0",
    "ejs": "^3.1.0",
    "express": "^4.19.0"
  }
}
```

Optionale Abhaengigkeiten, nur bei echtem Bedarf:

```json
{
  "dependencies": {
    "commander": "^12.0.0",
    "dotenv": "^16.0.0",
    "node-cron": "^3.0.0"
  }
}
```

## Zielstruktur

Die neue Node-Implementierung sollte zunaechst neben der Python-Version liegen.

```text
.
├── src/                    # bestehende Python-Version bleibt unveraendert
├── node/
│   ├── bin/
│   │   └── bank-api.js     # CLI-Einstieg
│   ├── public/
│   │   └── styles.css
│   ├── views/
│   │   ├── base.ejs
│   │   ├── login.ejs
│   │   ├── dashboard.ejs
│   │   ├── orders.ejs
│   │   ├── order-form.ejs
│   │   ├── configuration.ejs
│   │   └── depot.ejs
│   ├── src/
│   │   ├── api/
│   │   │   ├── app.js
│   │   │   ├── auth.js
│   │   │   ├── accounts.routes.js
│   │   │   ├── transactions.routes.js
│   │   │   └── web.routes.js
│   │   ├── client/
│   │   │   ├── base-client.js
│   │   │   ├── banking-client.js
│   │   │   └── session-client.js
│   │   ├── models/
│   │   │   ├── banking.js
│   │   │   ├── common.js
│   │   │   └── session.js
│   │   ├── persistence/
│   │   │   ├── database.js
│   │   │   ├── schema.sql
│   │   │   └── repositories.js
│   │   ├── services/
│   │   │   ├── accounts-service.js
│   │   │   ├── transactions-service.js
│   │   │   ├── orders-service.js
│   │   │   └── configuration-service.js
│   │   └── jobs/
│   │       └── scheduler.js
│   └── test/
│       ├── clients.test.js
│       └── services.test.js
├── package.json
└── migration.md
```

Diese Struktur spiegelt die bestehende Python-Architektur, ohne neue Konzepte einzufuehren.

## Migrationsstrategie

### Phase 1: Node-Grundgeruest

Zuerst wird ein lauffaehiges Node-Projekt neben Python angelegt.

Ergebnis:

- `package.json`
- `node/src/api/app.js`
- Healthcheck unter `/health`
- statische Dateien
- einfache Start-Skripte
- erster Test mit `node:test`

Beispiel-Skripte:

```json
{
  "scripts": {
    "start": "node node/src/api/app.js",
    "test": "node --test"
  }
}
```

### Phase 2: comdirect-Client portieren

Die Client-Schicht ist der wichtigste Kern. Sie sollte vor Weboberflaeche und CLI migriert werden.

Python-Dateien:

- `src/bank_api/client/base.py`
- `src/bank_api/client/banking.py`
- `src/bank_api/client/session.py`

Node-Ziel:

- `node/src/client/base-client.js`
- `node/src/client/banking-client.js`
- `node/src/client/session-client.js`

Vorgehen:

- HTTP-Aufrufe mit globalem `fetch` umsetzen.
- Fehlerbehandlung aus `exceptions.py` nach JavaScript-Error-Klassen uebertragen.
- Query-Parameter zentral bereinigen, damit `null` und `undefined` nicht gesendet werden.
- Antworten zunaechst nur normalisieren, nicht mit grosser Validierungsbibliothek absichern.

Bei Plain JavaScript ersetzen JSDoc-Kommentare einen Teil der Typdokumentation:

```js
/**
 * @param {string} user
 * @param {{ withoutAttr?: string, headers?: Record<string, string> }} [options]
 * @returns {Promise<object>}
 */
async function getAccountBalances(user, options = {}) {
  // ...
}
```

### Phase 3: Datenmodelle schlank halten

Die Python-Version nutzt Pydantic. Ohne TypeScript und mit wenigen Abhaengigkeiten sollte keine schwere Modellschicht nachgebaut werden.

Empfehlung:

- API-Antworten als plain objects behandeln.
- Kleine Normalisierungsfunktionen schreiben.
- Nur sicherheits- oder fachkritische Felder validieren.
- Validierung nahe am Eingang platzieren: HTTP-Body, CLI-Input, comdirect-Response.

Beispiel:

```js
function requireString(value, fieldName) {
  if (typeof value !== "string" || value.length === 0) {
    throw new Error(`${fieldName} is required`);
  }
  return value;
}
```

Das ist weniger komfortabel als Pydantic, aber transparent und dependency-arm.

### Phase 4: SQLite-Persistence

Die SQLAlchemy-Schicht wird durch explizite SQL-Dateien und kleine Repository-Module ersetzt.

Python-Dateien:

- `src/bank_api/persistence/database.py`
- `src/bank_api/persistence/models.py`
- `src/bank_api/persistence/repositories.py`

Node-Ziel:

- `node/src/persistence/database.js`
- `node/src/persistence/schema.sql`
- `node/src/persistence/repositories.js`

Empfehlung:

- `better-sqlite3` verwenden.
- Schema explizit in `schema.sql` halten.
- Migrationen einfach versionieren, z. B. ueber Tabelle `schema_migrations`.
- Repositories als kleine Funktionen statt Klassenmonster schreiben.

Beispiel fuer Migrationsdateien:

```text
node/src/persistence/migrations/
├── 001_initial.sql
├── 002_add_orders.sql
└── 003_add_configuration.sql
```

### Phase 5: Services portieren

Die Service-Schicht sollte nach dem Client und der Persistence migriert werden.

Python-Dateien:

- `src/bank_api/services/accounts.py`
- `src/bank_api/services/transactions.py`
- `src/bank_api/services/orders.py`
- `src/bank_api/services/configuration.py`

Node-Ziel:

- `node/src/services/accounts-service.js`
- `node/src/services/transactions-service.js`
- `node/src/services/orders-service.js`
- `node/src/services/configuration-service.js`

Regel:

- Services enthalten Fachlogik.
- HTTP-Routen enthalten nur Request/Response-Handling.
- Repositories enthalten nur Datenbankzugriff.
- comdirect-Client enthaelt nur externe API-Aufrufe.

Diese Trennung sollte aus dem Python-Projekt uebernommen werden.

### Phase 6: REST-API und Weboberflaeche

FastAPI wird durch Express ersetzt.

Python-Dateien:

- `src/bank_api/api/app.py`
- `src/bank_api/api/auth.py`
- `src/bank_api/api/dependencies.py`
- `src/bank_api/api/routers/accounts.py`
- `src/bank_api/api/routers/transactions.py`
- `src/bank_api/api/web/routes.py`
- `src/bank_api/api/templates/*.html`
- `src/bank_api/api/static/styles.css`

Node-Ziel:

- `node/src/api/app.js`
- `node/src/api/auth.js`
- `node/src/api/accounts.routes.js`
- `node/src/api/transactions.routes.js`
- `node/src/api/web.routes.js`
- `node/views/*.ejs`
- `node/public/styles.css`

Um Abhaengigkeiten klein zu halten:

- API-Key-Pruefung selbst implementieren.
- Sessions nur verwenden, wenn die HTML-Oberflaeche sie wirklich braucht.
- Falls Sessions gebraucht werden: `express-session` waere eine zusaetzliche Abhaengigkeit.
- Alternativ fuer den ersten Schritt einfache signierte Cookies vermeiden und Web-Login spaeter portieren.

Empfohlene Reihenfolge:

1. `/health`
2. REST-Endpunkte `/accounts` und `/transactions`
3. statische Dateien
4. Login-Seite
5. Dashboard
6. Orders, Configuration, Depot

### Phase 7: CLI portieren

Die Typer-CLI kann klein starten.

Python-Datei:

- `src/bank_api/cli/app.py`

Node-Ziel:

- `node/bin/bank-api.js`

Bei wenigen Befehlen reicht eine kleine eigene Argumentauswertung. Wenn die CLI wachsen soll, ist `commander` sinnvoll.

Startumfang:

- `login`
- `balances <USER_ID>`
- `export-transactions <ACCOUNT_ID>`

Die lokale CLI-Konfiguration kann wie bisher unter einem OS-spezifischen Konfigurationspfad liegen. Ohne Extra-Abhaengigkeit kann fuer Linux zunaechst `~/.config/bank_api/config.json` verwendet werden.

### Phase 8: Scheduler

Der APScheduler-Ersatz sollte erst nach den Services kommen.

Python-Datei:

- `src/bank_api/jobs/scheduler.py`

Node-Ziel:

- `node/src/jobs/scheduler.js`

Empfehlung:

- Fuer einfache Intervalle `setInterval` verwenden.
- Fuer Cron-Ausdruecke optional `node-cron` einsetzen.
- Jobs als Funktionen schreiben, die Services aufrufen.

### Phase 9: Tests

Die vorhandenen Python-Tests sollten in Node mit `node:test` nachgebaut werden.

Python-Dateien:

- `tests/test_clients.py`
- `tests/conftest.py`
- `tests/live/test_sandbox_accounts.py`

Node-Ziel:

- `node/test/clients.test.js`
- `node/test/services.test.js`
- `node/test/live/sandbox-accounts.test.js`

Empfehlung:

- Unit-Tests zuerst fuer den comdirect-Client.
- `fetch` in Tests mocken, ohne grosse Mocking-Bibliothek.
- Live-Tests nur ausfuehren, wenn Sandbox-Umgebungsvariablen gesetzt sind.
- Python- und Node-Tests waehrend der Migration parallel behalten.

## Umgang mit Abhaengigkeiten

Jede neue Abhaengigkeit sollte eine klare Aufgabe haben.

Erlaubte Start-Abhaengigkeiten:

- `express`: HTTP-Server und Routing
- `ejs`: HTML-Templates
- `better-sqlite3`: SQLite-Zugriff

Erst spaeter entscheiden:

- `commander`: wenn CLI-Argumente unuebersichtlich werden
- `dotenv`: wenn lokale `.env`-Dateien gewuenscht sind
- `express-session`: wenn die HTML-Session sauber portiert werden soll
- `node-cron`: wenn echte Cron-Syntax gebraucht wird

Nicht empfohlen:

- ORM wie Prisma oder Sequelize, wenn das Ziel wenige Abhaengigkeiten ist
- TypeScript, Babel oder Build-Systeme
- grosse Validierungsbibliotheken fuer den ersten Port
- Frontend-Frameworks fuer die bestehende serverseitige Weboberflaeche

## Parallelbetrieb waehrend der Migration

Python und Node sollten temporaer parallel laufen.

Beispiel:

```text
Python FastAPI: http://localhost:8000
Node Express:  http://localhost:3000
```

Vorteile:

- Verhalten kann endpointweise verglichen werden.
- Die Python-Version bleibt als Referenz erhalten.
- Fehler in der Node-Version blockieren die bestehende Nutzung nicht.
- Migration kann pro Modul abgeschlossen werden.

## Abnahmekriterien

Ein Modul gilt als migriert, wenn:

- die Node-Implementierung denselben fachlichen Zweck erfuellt,
- relevante Tests vorhanden sind,
- Fehlerfaelle bewusst behandelt werden,
- keine unnoetigen Abhaengigkeiten eingefuehrt wurden,
- README oder Betriebsdokumentation angepasst wurde,
- Python- und Node-Verhalten fuer die wichtigsten Beispiele verglichen wurde.

Das Gesamtprojekt gilt als migriert, wenn:

- REST-API laeuft,
- HTML-Oberflaeche laeuft,
- CLI laeuft,
- SQLite-Datenhaltung funktioniert,
- comdirect-Sandbox-Tests oder gleichwertige Smoke-Tests erfolgreich sind,
- Docker-Start fuer Node dokumentiert ist,
- Python-Code entweder entfernt oder klar als Legacy markiert ist.

## Risiken

### Weniger automatische Validierung

Ohne Pydantic und TypeScript gibt es weniger Schutz durch Typen und Schemas.

Gegenmassnahme:

- Eingaben explizit validieren.
- Kritische comdirect-Antworten normalisieren.
- Tests fuer typische und fehlerhafte API-Antworten schreiben.

### Datenbankmigration

SQLAlchemy versteckt aktuell Details, die in Node expliziter werden.

Gegenmassnahme:

- Schema in SQL-Dateien pflegen.
- Migrationsreihenfolge versionieren.
- Vorhandene SQLite-Datei nicht direkt veraendern, bevor ein Backup existiert.

### Unterschiedliches HTTP-Verhalten

`requests` und `fetch` behandeln Fehler unterschiedlich. `fetch` wirft bei HTTP 4xx/5xx nicht automatisch.

Gegenmassnahme:

- Gemeinsame Request-Hilfsfunktion schreiben.
- Nicht-2xx-Statuscodes explizit in Fehler uebersetzen.
- Response-Body bei Fehlern kontrolliert auslesen.

### Session-Verhalten

FastAPI/Starlette-Sessions und Express-Sessions sind nicht identisch.

Gegenmassnahme:

- Web-Session als eigene Teilmigration behandeln.
- Login-Flow separat testen.
- Session-Cookies bewusst konfigurieren.

## Empfohlener erster Umsetzungsschritt

Der beste erste Schritt ist ein kleiner, lauffaehiger Node-Schnitt:

1. `package.json` anlegen.
2. Express-App mit `/health` erstellen.
3. `base-client.js` und `banking-client.js` portieren.
4. Tests fuer Client-URL, Header, Query-Parameter und Fehlerfaelle schreiben.
5. Danach erst Persistence und Weboberflaeche angehen.

Damit entsteht schnell ein pruefbarer Kern, ohne das bestehende Python-Projekt zu gefaehrden.
