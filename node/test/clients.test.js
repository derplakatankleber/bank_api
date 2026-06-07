const assert = require("node:assert/strict");
const test = require("node:test");
const { BankingClient, ComdirectAPIError, OAuthClient, SessionClient } = require("../src/client");

test("getAccountBalances builds the expected request", async () => {
  const calls = [];
  const client = new BankingClient({
    fetchImpl: async (url, options) => {
      calls.push({ url, options });
      return jsonResponse(200, {
        paging: { index: 0, matches: 1 },
        aggregated: { total: "1" },
        values: [{ accountId: "account-1", balance: { value: "100.50", unit: "EUR" } }]
      });
    }
  });

  const result = await client.getAccountBalances("user", { withoutAttr: "account" });

  assert.equal(result.values[0].accountId, "account-1");
  assert.equal(calls[0].options.method, "GET");
  assert.equal(calls[0].url.pathname, "/api/banking/clients/user/v2/accounts/balances");
  assert.equal(calls[0].url.searchParams.get("without-attr"), "account");
});

test("retries on rate limits", async () => {
  const responses = [
    jsonResponse(429, { message: "slow down" }, { "Retry-After": "0" }),
    jsonResponse(200, { paging: {}, values: [] })
  ];
  let calls = 0;
  const client = new BankingClient({
    fetchImpl: async () => {
      calls += 1;
      return responses.shift();
    }
  });

  const result = await client.getAccountBalances("user");

  assert.deepEqual(result.values, []);
  assert.equal(calls, 2);
});

test("raises a ComdirectAPIError after retries", async () => {
  const client = new BankingClient({
    retryConfig: { maxAttempts: 2, backoffFactor: 0 },
    fetchImpl: async () => jsonResponse(500, { error: "fail" })
  });

  await assert.rejects(
    () => client.getAccountBalances("user"),
    (error) => {
      assert.ok(error instanceof ComdirectAPIError);
      assert.equal(error.statusCode, 500);
      assert.deepEqual(error.response, { error: "fail" });
      return true;
    }
  );
});


test("raises API errors with non-JSON response bodies", async () => {
  const client = new BankingClient({
    retryConfig: { maxAttempts: 1 },
    fetchImpl: async () => textResponse(500, "upstream exploded")
  });

  await assert.rejects(
    () => client.getAccountBalances("user"),
    (error) => {
      assert.ok(error instanceof ComdirectAPIError);
      assert.equal(error.statusCode, 500);
      assert.equal(error.response, "upstream exploded");
      assert.ok(error.message.includes("GET /banking/clients/user/v2/accounts/balances"));
      assert.ok(error.message.includes("upstream exploded"));
      return true;
    }
  );
});

test("OAuthClient raises OAuth errors with non-JSON response bodies", async () => {
  const client = new OAuthClient({
    fetchImpl: async () => textResponse(401, "invalid credentials")
  });

  await assert.rejects(
    () => client.passwordGrant({
      client_id: "client",
      client_secret: "secret",
      username: "user",
      password: "pin"
    }),
    (error) => {
      assert.ok(error instanceof ComdirectAPIError);
      assert.equal(error.statusCode, 401);
      assert.equal(error.response, "invalid credentials");
      return true;
    }
  );
});

test("BankingClient adds a bearer token from the token provider", async () => {
  const calls = [];
  const client = new BankingClient({
    getAccessToken: async () => "access-token",
    fetchImpl: async (url, options) => {
      calls.push({ url, options });
      return jsonResponse(200, { paging: {}, values: [] });
    }
  });

  await client.getAccountBalances("user");

  assert.equal(calls[0].options.headers.Authorization, "Bearer access-token");
});

test("BankingClient adds comdirect request info headers", async () => {
  const calls = [];
  const client = new BankingClient({
    sessionId: "session-1",
    fetchImpl: async (url, options) => {
      calls.push({ url, options });
      return jsonResponse(200, { paging: {}, values: [] });
    }
  });

  await client.getAccountBalances("user");

  const requestInfo = JSON.parse(calls[0].options.headers["x-http-request-info"]);
  assert.equal(requestInfo.clientRequestId.sessionId, "session-1");
  assert.match(requestInfo.clientRequestId.requestId, /^\d+$/);
});

test("SessionClient returns the session payload", async () => {
  const client = new SessionClient({
    fetchImpl: async () => jsonResponse(200, [
      { id: 1, identifier: "abc", sessionTanActive: true, activated2FA: false },
      { id: 2, identifier: "def", sessionTanActive: false, activated2FA: true }
    ])
  });

  const result = await client.getSessions("user");

  assert.deepEqual(result.map((item) => item.identifier), ["abc", "def"]);
});

function jsonResponse(status, payload, headers = {}) {
  return {
    status,
    ok: status >= 200 && status < 400,
    headers: {
      get(name) {
        return headers[name] || headers[name.toLowerCase()] || null;
      }
    },
    async json() {
      return payload;
    },
    async text() {
      return JSON.stringify(payload);
    }
  };
}

function textResponse(status, payload, headers = {}) {
  let consumed = false;
  return {
    status,
    ok: status >= 200 && status < 400,
    headers: {
      get(name) {
        return headers[name] || headers[name.toLowerCase()] || null;
      }
    },
    async json() {
      if (consumed) {
        throw new TypeError("Body is unusable");
      }
      consumed = true;
      return JSON.parse(payload);
    },
    async text() {
      if (consumed) {
        throw new TypeError("Body is unusable");
      }
      consumed = true;
      return payload;
    }
  };
}
