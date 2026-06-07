const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");
const { openDatabase } = require("../src/persistence/database");
const { createSyncLogRepository } = require("../src/persistence/repositories");
const { ConfigurationService } = require("../src/services/configuration-service");
const { OrderService } = require("../src/services/orders-service");

test("ConfigurationService creates an app key on first use", () => {
  const db = temporaryDatabase();
  const service = new ConfigurationService(db);

  const configuration = service.getConfiguration();

  assert.equal(typeof configuration.app_key, "string");
  assert.ok(configuration.app_key.length >= 32);
  assert.equal(service.getAppKey(), configuration.app_key);
  db.close();
});

test("ConfigurationService stores and returns allowed settings", () => {
  const db = temporaryDatabase();
  const service = new ConfigurationService(db);

  service.updateConfiguration({
    app_key: "secret",
    client_id: "client",
    client_secret: "client-secret",
    username: "user",
    password: "pin",
    account_id: "account-1",
    oauth_url: "https://oauth.example",
    ignored: "nope"
  });

  assert.deepEqual(service.getConfiguration(), {
    app_key: "secret",
    client_id: "client",
    client_secret: "client-secret",
    username: "user",
    password: "pin",
    account_id: "account-1",
    oauth_url: "https://oauth.example"
  });
  assert.deepEqual(service.getComdirectCredentials(), {
    client_id: "client",
    client_secret: "client-secret",
    username: "user",
    password: "pin",
    oauth_url: "https://oauth.example"
  });
  assert.equal(service.getOAuthUrl(), "https://oauth.example");
  db.close();
});

test("OrderService creates and updates local orders", () => {
  const db = temporaryDatabase();
  const service = new OrderService(db);

  const created = service.createOrder({
    instrument: "ETF",
    side: "buy",
    order_type: "limit",
    quantity: "2.5",
    limit_price: "99.95",
    notes: "rebalance"
  });

  assert.equal(created.instrument, "ETF");
  assert.equal(created.status, "pending");
  assert.equal(created.quantity, 2.5);

  const updated = service.updateOrderStatus(created.id, "executed");
  assert.equal(updated.status, "executed");
  assert.equal(service.listOrders().length, 1);
  db.close();
});

test("OrderService rejects unsupported status values", () => {
  const db = temporaryDatabase();
  const service = new OrderService(db);

  assert.throws(() => service.updateOrderStatus(1, "weird"), /Unsupported order status/);
  db.close();
});

test("SyncLogRepository lists recent logs", () => {
  const db = temporaryDatabase();
  const repository = createSyncLogRepository(db);

  const first = repository.create("first-job", "running");
  repository.update(first.id, "succeeded", "done");
  const second = repository.create("second-job", "failed", "boom");

  const logs = repository.listRecent(1);

  assert.equal(logs.length, 1);
  assert.equal(logs[0].id, second.id);
  assert.equal(logs[0].detail, "boom");
  db.close();
});

function temporaryDatabase() {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "bank-api-node-"));
  return openDatabase({ filename: path.join(directory, "test.db") });
}
