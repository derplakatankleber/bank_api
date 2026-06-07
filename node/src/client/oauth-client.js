const { ComdirectAPIError } = require("./errors");

class OAuthClient {
  constructor(options = {}) {
    this.oauthUrl = normalizeOAuthUrl(options.oauthUrl || "https://api.comdirect.de");
    this.fetchImpl = options.fetchImpl || globalThis.fetch;
    this.timeout = options.timeout || 30000;

    if (typeof this.fetchImpl !== "function") {
      throw new Error("A fetch implementation is required");
    }
  }

  async passwordGrant(credentials) {
    requireCredential(credentials.client_id, "client_id");
    requireCredential(credentials.client_secret, "client_secret");
    requireCredential(credentials.username, "username");
    requireCredential(credentials.password, "password");

    const tokenUrl = new URL("/oauth/token", normalizeOAuthUrl(credentials.oauth_url || this.oauthUrl));

    const body = new URLSearchParams({
      client_id: credentials.client_id,
      client_secret: credentials.client_secret,
      grant_type: "password",
      username: credentials.username,
      password: credentials.password
    });

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);
    let response;

    try {
      response = await this.fetchImpl(tokenUrl, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/x-www-form-urlencoded"
        },
        body,
        signal: controller.signal
      });
    } finally {
      clearTimeout(timeoutId);
    }

    const payload = await readJsonOrText(response);
    if (!response.ok) {
      throw new ComdirectAPIError("HTTP " + response.status + " error calling comdirect OAuth API", {
        statusCode: response.status,
        response: payload
      });
    }

    return payload;
  }
}

function requireCredential(value, name) {
  if (!value) {
    throw new Error(`Missing comdirect OAuth credential: ${name}`);
  }
}

async function readJsonOrText(response) {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch (_error) {
    return text;
  }
}

function normalizeOAuthUrl(oauthUrl) {
  return oauthUrl.replace(/\/+$/, "") + "/";
}

module.exports = {
  OAuthClient
};
