const express = require("express");
const { toBalanceSummary } = require("../services/accounts-service");

function createWebRouter(services) {
  const router = express.Router();
  const { accountService, configurationService, orderService, tokenService } = services;

  router.get("/login", (_req, res) => {
    res.render("login", {
      configuration: configurationService.getConfiguration(),
      error: null
    });
  });

  router.post("/login", async (req, res, next) => {
    try {
      const configuration = configurationService.updateConfiguration(readConfigurationBody(req));
      if (tokenService) {
        tokenService.clear();
      }
      req.saveSession({
        authenticated: true,
        account_id: configuration.account_id
      });
      res.redirect(303, "/");
    } catch (error) {
      next(error);
    }
  });

  router.post("/logout", (req, res) => {
    req.clearSession();
    res.redirect(303, "/login");
  });

  router.get("/", requireAuthenticated, (_req, res) => {
    res.render("dashboard", {
      configuration: configurationService.getConfiguration(),
      balances: accountService.listCachedBalances().map(toBalanceSummary),
      orders: orderService.listOrders().slice(0, 5)
    });
  });

  router.get("/configuration", requireAuthenticated, (req, res) => {
    res.render("configuration", {
      configuration: configurationService.getConfiguration(),
      saved: req.query.saved
    });
  });

  router.post("/configuration", requireAuthenticated, (req, res, next) => {
    try {
      const configuration = configurationService.updateConfiguration(readConfigurationBody(req));
      if (tokenService) {
        tokenService.clear();
      }
      req.saveSession({
        ...req.session,
        account_id: configuration.account_id
      });
      res.redirect(303, "/configuration?saved=true");
    } catch (error) {
      next(error);
    }
  });

  router.get("/orders", requireAuthenticated, (_req, res) => {
    res.render("orders", {
      orders: orderService.listOrders()
    });
  });

  router.get("/orders/new", requireAuthenticated, (_req, res) => {
    res.render("order-form");
  });

  router.post("/orders", requireAuthenticated, (req, res, next) => {
    try {
      orderService.createOrder({
        instrument: req.body.instrument,
        side: req.body.side,
        order_type: req.body.order_type,
        quantity: req.body.quantity,
        limit_price: req.body.limit_price,
        notes: req.body.notes
      });
      res.redirect(303, "/orders");
    } catch (error) {
      next(error);
    }
  });

  router.post("/orders/:orderId/status", requireAuthenticated, (req, res, next) => {
    try {
      orderService.updateOrderStatus(req.params.orderId, req.body.status);
      res.redirect(303, "/orders");
    } catch (error) {
      next(error);
    }
  });

  router.get("/depot", requireAuthenticated, (_req, res) => {
    const balances = accountService.listCachedBalances().map(toBalanceSummary);
    const totals = {};
    for (const balance of balances) {
      if (balance.amount === null || !balance.currency) {
        continue;
      }
      totals[balance.currency] = (totals[balance.currency] || 0) + Number(balance.amount);
    }
    res.render("depot", { balances, totals });
  });

  return router;
}

function readConfigurationBody(req) {
  return {
    app_key: req.body.app_key,
    client_id: req.body.client_id,
    client_secret: req.body.client_secret,
    username: req.body.username,
    password: req.body.password,
    account_id: req.body.account_id,
    oauth_url: req.body.oauth_url
  };
}

function requireAuthenticated(req, res, next) {
  if (!req.session.authenticated) {
    return res.redirect(303, "/login");
  }
  return next();
}

module.exports = {
  createWebRouter
};
