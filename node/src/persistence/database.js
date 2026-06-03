const fs = require("node:fs");
const path = require("node:path");

function openDatabase(options = {}) {
  const Database = require("better-sqlite3");
  const filename = options.filename || process.env.BANK_API_DB || "bank_data.db";
  const db = new Database(filename);
  const schemaPath = path.join(__dirname, "schema.sql");
  db.exec(fs.readFileSync(schemaPath, "utf8"));
  return db;
}

module.exports = {
  openDatabase
};
