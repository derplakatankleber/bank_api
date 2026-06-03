#!/usr/bin/env node
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const DEFAULT_API_URL = "http://localhost:3000";
const CONFIG_PATH = path.join(os.homedir(), ".config", "bank_api", "config.json");

async function main(argv) {
  const [command, ...args] = argv;

  if (command === "login") {
    return login(args);
  }
  if (command === "balances") {
    return balances(args);
  }
  if (command === "export-transactions") {
    return exportTransactions(args);
  }

  printUsage();
}

async function login(args) {
  const options = parseOptions(args);
  const apiUrl = options.apiUrl || options["api-url"] || DEFAULT_API_URL;
  const appKey = options.appKey || options["app-key"];
  if (!appKey) {
    throw new Error("Missing --app-key. Interactive prompts are intentionally avoided in the dependency-light CLI.");
  }
  saveConfig({ api_url: apiUrl.replace(/\/+$/, ""), app_key: appKey });
  console.log(`Credentials saved to ${CONFIG_PATH}`);
}

async function balances(args) {
  const options = parseOptions(args);
  const userId = options._[0];
  if (!userId) {
    throw new Error("Missing USER_ID");
  }
  const payload = await requestJson("GET", `/accounts/${encodeURIComponent(userId)}/balances`, {
    refresh: options.refresh ? "true" : undefined
  }, options);
  printTable(payload.data || [], ["account_id", "amount", "currency"]);
  if (options.outputCsv || options["output-csv"]) {
    writeCsv(options.outputCsv || options["output-csv"], payload.data || []);
  }
}

async function exportTransactions(args) {
  const options = parseOptions(args);
  const accountId = options._[0];
  if (!accountId) {
    throw new Error("Missing ACCOUNT_ID");
  }
  const payload = await requestJson("GET", `/accounts/${encodeURIComponent(accountId)}/transactions`, {
    refresh: options.refresh ? "true" : undefined
  }, options);
  const rows = (payload.data || []).map((item) => ({
    booking_date: item.booking_date,
    reference: item.reference,
    remittance_info: item.remittance_info,
    transaction_type: item.transaction_type,
    amount: item.amount ? item.amount.value : null,
    currency: item.amount ? item.amount.currency : null
  }));
  printTable(rows, ["booking_date", "reference", "amount", "currency"]);
  writeCsv(options.outputCsv || options["output-csv"] || "transactions.csv", rows);
}

async function requestJson(method, endpoint, params, options) {
  const apiUrl = resolveApiUrl(options).replace(/\/+$/, "");
  const appKey = resolveAppKey(options);
  const url = new URL(endpoint, apiUrl);
  for (const [key, value] of Object.entries(params || {})) {
    if (value !== undefined && value !== null) {
      url.searchParams.set(key, value);
    }
  }
  const response = await fetch(url, {
    method,
    headers: { "X-App-Key": appKey }
  });
  const text = await response.text();
  const payload = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new Error(`Request failed with HTTP ${response.status}: ${JSON.stringify(payload)}`);
  }
  return payload;
}

function parseOptions(args) {
  const options = { _: [] };
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (!arg.startsWith("--")) {
      options._.push(arg);
      continue;
    }
    const key = toCamelCase(arg.slice(2));
    const next = args[index + 1];
    if (!next || next.startsWith("--")) {
      options[key] = true;
    } else {
      options[key] = next;
      index += 1;
    }
  }
  return options;
}

function toCamelCase(value) {
  return value.replace(/-([a-z])/g, (_match, char) => char.toUpperCase());
}

function loadConfig() {
  if (!fs.existsSync(CONFIG_PATH)) {
    return {};
  }
  return JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
}

function saveConfig(config) {
  fs.mkdirSync(path.dirname(CONFIG_PATH), { recursive: true });
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2), { mode: 0o600 });
}

function resolveApiUrl(options) {
  return options.apiUrl || process.env.BANK_API_URL || loadConfig().api_url || DEFAULT_API_URL;
}

function resolveAppKey(options) {
  const key = options.appKey || options["app-key"] || process.env.BANK_APP_KEY || loadConfig().app_key;
  if (!key) {
    throw new Error("No app key configured. Run `bank-api-node login --app-key <key>` or set BANK_APP_KEY.");
  }
  return key;
}

function printTable(rows, columns) {
  if (!rows.length) {
    console.log("No data.");
    return;
  }
  console.log(columns.join("\t"));
  for (const row of rows) {
    console.log(columns.map((column) => row[column] ?? "").join("\t"));
  }
}

function writeCsv(filename, rows) {
  const columns = rows.length ? Object.keys(rows[0]) : [];
  const lines = [columns.join(",")];
  for (const row of rows) {
    lines.push(columns.map((column) => csvValue(row[column])).join(","));
  }
  fs.writeFileSync(filename, lines.join("\n") + "\n");
  console.log(`Exported data to ${filename}`);
}

function csvValue(value) {
  if (value === undefined || value === null) {
    return "";
  }
  const text = String(value);
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function printUsage() {
  console.log("Usage:");
  console.log("  bank-api-node login --app-key <key> [--api-url http://localhost:3000]");
  console.log("  bank-api-node balances <USER_ID> [--refresh] [--output-csv balances.csv]");
  console.log("  bank-api-node export-transactions <ACCOUNT_ID> [--refresh] [--output-csv transactions.csv]");
}

main(process.argv.slice(2)).catch((error) => {
  console.error(error.message || error);
  process.exitCode = 1;
});
