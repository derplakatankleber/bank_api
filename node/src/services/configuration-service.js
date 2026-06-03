const crypto = require("node:crypto");
const { createSettingsRepository } = require("../persistence/repositories");

const CONFIG_KEYS = [
  "app_key",
  "client_id",
  "client_secret",
  "username",
  "password",
  "account_id",
  "oauth_url"
];

class ConfigurationService {
  constructor(db) {
    this.db = db;
    this.ensureAppKey();
  }

  getConfiguration() {
    const entries = {};
    for (const setting of createSettingsRepository(this.db).listAll()) {
      entries[setting.key] = setting.value;
    }
    return {
      app_key: entries.app_key || null,
      client_id: entries.client_id || null,
      client_secret: entries.client_secret || null,
      username: entries.username || null,
      password: entries.password || null,
      account_id: entries.account_id || null,
      oauth_url: entries.oauth_url || "https://api.comdirect.de"
    };
  }

  updateConfiguration(values = {}) {
    const repository = createSettingsRepository(this.db);
    for (const key of CONFIG_KEYS) {
      if (Object.prototype.hasOwnProperty.call(values, key)) {
        repository.set(key, values[key] || null);
      }
    }
    return this.getConfiguration();
  }

  ensureAppKey() {
    const repository = createSettingsRepository(this.db);
    const existing = repository.get("app_key");
    if (existing && existing.value) {
      return existing.value;
    }

    const generated = crypto.randomBytes(32).toString("base64url");
    repository.set("app_key", generated);
    return generated;
  }

  getAppKey() {
    return process.env.BANK_APP_KEY || this.ensureAppKey();
  }

  getComdirectCredentials() {
    const configuration = this.getConfiguration();
    return {
      client_id: process.env.COMDIRECT_CLIENT_ID || configuration.client_id,
      client_secret: process.env.COMDIRECT_CLIENT_SECRET || configuration.client_secret,
      username: process.env.COMDIRECT_USERNAME || configuration.username,
      password: process.env.COMDIRECT_PASSWORD || configuration.password,
      oauth_url: process.env.COMDIRECT_OAUTH_URL || configuration.oauth_url || "https://api.comdirect.de"
    };
  }

  getOAuthUrl() {
    const configuration = this.getConfiguration();
    return process.env.COMDIRECT_OAUTH_URL || configuration.oauth_url || "https://api.comdirect.de";
  }
}

module.exports = {
  ConfigurationService
};
