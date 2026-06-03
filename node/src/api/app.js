const express = require("express");
const path = require("node:path");
const { BankingClient, ComdirectAPIError, OAuthClient } = require("../client");
const { openDatabase } = require("../persistence/database");
const { AccountService } = require("../services/accounts-service");
const { ConfigurationService } = require("../services/configuration-service");
const { OAuthTokenService } = require("../services/oauth-token-service");
const { OrderService } = require("../services/orders-service");
const { TransactionService } = require("../services/transactions-service");
const { createRequireAppKey } = require("./auth");
const { createAccountsRouter } = require("./accounts.routes");
const { createTransactionsRouter } = require("./transactions.routes");
const { sessionMiddleware } = require("./session");
const { createWebRouter } = require("./web.routes");

function createApp(options = {}) {
  const app = express();
  const db = options.db || openDatabase();
  const configurationService = options.configurationService || new ConfigurationService(db);
  const oauthClient = options.oauthClient || new OAuthClient({
    oauthUrl: configurationService.getOAuthUrl()
  });
  const tokenService = options.tokenService || new OAuthTokenService(configurationService, oauthClient);
  const client = options.client || new BankingClient({
    baseUrl: process.env.BANK_API_URL || "https://api.comdirect.de/api/",
    getAccessToken: () => tokenService.getAccessToken()
  });

  const accountService = new AccountService(client, db, configurationService);
  const transactionService = new TransactionService(client, db);
  const orderService = new OrderService(db);

  app.set("view engine", "ejs");
  app.set("views", path.join(__dirname, "..", "..", "views"));
  app.locals.capitalize = capitalize;
  app.use(express.urlencoded({ extended: false }));
  app.use(express.json());
  app.use("/static", express.static(path.join(__dirname, "..", "..", "public")));

  app.get("/health", (_req, res) => {
    res.json({ status: "ok" });
  });

  const requireAppKey = createRequireAppKey(configurationService);
  app.use("/accounts", requireAppKey, createAccountsRouter(accountService));
  app.use("/accounts", requireAppKey, createTransactionsRouter(transactionService));
  app.use(sessionMiddleware(), createWebRouter({ accountService, configurationService, orderService, tokenService }));
  app.use(errorHandler);

  return app;
}

function capitalize(value) {
  const text = String(value || "");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function errorHandler(error, _req, res, _next) {
  if (error instanceof ComdirectAPIError) {
    return res.status(error.statusCode || 502).json({
      detail: error.message,
      response: error.response
    });
  }

  console.error(error);
  return res.status(500).json({ detail: error.message || "Internal server error" });
}

if (require.main === module) {
  const port = Number.parseInt(process.env.PORT || "3000", 10);
  createApp().listen(port, () => {
    console.log(`bank-api Node server listening on http://localhost:${port}`);
  });
}

module.exports = {
  createApp
};
