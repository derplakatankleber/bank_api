const { setTimeout: sleep } = require("node:timers/promises");
const { ComdirectAPIError } = require("./errors");

const DEFAULT_RETRY_CONFIG = {
  maxAttempts: 3,
  backoffFactor: 0.5,
  statusForcelist: [429, 500, 502, 503, 504]
};

class BaseComdirectClient {
  constructor(options = {}) {
    this.baseUrl = normalizeBaseUrl(options.baseUrl || "https://api.comdirect.de/api/");
    this.fetchImpl = options.fetchImpl || globalThis.fetch;
    this.retryConfig = {
      ...DEFAULT_RETRY_CONFIG,
      ...(options.retryConfig || {})
    };
    this.timeout = options.timeout || 30000;
    this.getAccessToken = options.getAccessToken;

    if (typeof this.fetchImpl !== "function") {
      throw new Error("A fetch implementation is required");
    }
  }

  prepareParams(params) {
    const cleaned = {};
    for (const [key, value] of Object.entries(params || {})) {
      if (value !== undefined && value !== null) {
        cleaned[key] = String(value);
      }
    }
    return cleaned;
  }

  buildUrl(path, params) {
    const url = new URL(path.replace(/^\/+/, ""), this.baseUrl);
    for (const [key, value] of Object.entries(this.prepareParams(params))) {
      url.searchParams.set(key, value);
    }
    return url;
  }

  async request(method, path, options = {}) {
    const url = this.buildUrl(path, options.params);
    let lastResponse;

    for (let attempt = 1; attempt <= this.retryConfig.maxAttempts; attempt += 1) {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      try {
        lastResponse = await this.fetchImpl(url, {
          method,
          headers: await this.prepareHeaders(options),
          body: options.json === undefined ? undefined : JSON.stringify(options.json),
          signal: controller.signal
        });
      } finally {
        clearTimeout(timeoutId);
      }

      if (!this.shouldRetry(lastResponse) || attempt === this.retryConfig.maxAttempts) {
        break;
      }

      await sleep(this.calculateDelay(lastResponse, attempt) * 1000);
    }

    if (!lastResponse.ok) {
      throw await this.buildError(lastResponse);
    }

    return lastResponse;
  }

  async prepareHeaders(options = {}) {
    const headers = { ...(options.headers || {}) };
    if (options.auth !== false && this.getAccessToken && !headers.Authorization) {
      headers.Authorization = `Bearer ${await this.getAccessToken()}`;
    }
    return headers;
  }

  async requestJson(method, path, options = {}) {
    const response = await this.request(method, path, options);
    return response.json();
  }

  shouldRetry(response) {
    return this.retryConfig.statusForcelist.includes(response.status);
  }

  calculateDelay(response, attempt) {
    if (response.status === 429) {
      const retryAfter = response.headers.get("Retry-After");
      if (retryAfter !== null) {
        const parsed = Number.parseFloat(retryAfter);
        if (!Number.isNaN(parsed)) {
          return parsed;
        }
      }
    }
    return this.retryConfig.backoffFactor * (2 ** (attempt - 1));
  }

  async buildError(response) {
    let payload;
    try {
      payload = await response.json();
    } catch (_error) {
      payload = await response.text();
    }

    return new ComdirectAPIError("HTTP " + response.status + " error calling comdirect API", {
      statusCode: response.status,
      response: payload
    });
  }
}

function normalizeBaseUrl(baseUrl) {
  return baseUrl.replace(/\/+$/, "") + "/";
}

module.exports = {
  BaseComdirectClient,
  DEFAULT_RETRY_CONFIG
};
