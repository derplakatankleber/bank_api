const express = require("express");
const { toBalanceSummary } = require("../services/accounts-service");

function createWebRouter(services) {
  const router = express.Router();
  const { accountService, configurationService, orderService, syncLogRepository, tokenService } = services;

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

  router.get("/", requireAuthenticated, (req, res) => {
    res.render("dashboard", {
      configuration: configurationService.getConfiguration(),
      balances: accountService.listCachedBalances().map(toBalanceSummary),
      orders: orderService.listOrders().slice(0, 5),
      refreshed: req.query.refreshed === "true",
      error: req.query.error || null
    });
  });

  router.post("/balances/refresh", requireAuthenticated, async (req, res, next) => {
    const redirectPath = sanitizeRedirectPath(req.body.redirect_to) || "/";
    const log = syncLogRepository.create("manual-balance-refresh", "running");
    try {
      await accountService.refreshAccountBalances("user");
      syncLogRepository.update(log.id, "succeeded", "Fetched account balances for user");
      res.redirect(303, appendQuery(redirectPath, { refreshed: "true" }));
    } catch (error) {
      const detail = formatRefreshError(error);
      syncLogRepository.update(log.id, "failed", detail);
      res.redirect(303, appendQuery(redirectPath, { error: detail }));
    }
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

  router.get("/logs", requireAuthenticated, (req, res) => {
    const limit = normalizeLogLimit(req.query.limit);
    res.render("logs", {
      logs: syncLogRepository.listRecent(limit),
      limit
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

  router.get("/depot", requireAuthenticated, (req, res) => {
    const balances = accountService.listCachedBalances().map(toBalanceSummary);
    const totals = {};
    for (const balance of balances) {
      if (balance.amount === null || !balance.currency) {
        continue;
      }
      totals[balance.currency] = (totals[balance.currency] || 0) + Number(balance.amount);
    }
    res.render("depot", {
      balances,
      totals,
      refreshed: req.query.refreshed === "true",
      error: req.query.error || null
    });
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

function sanitizeRedirectPath(value) {
  if (!value || !value.startsWith("/") || value.startsWith("//")) {
    return null;
  }
  return value.split("?")[0];
}

function appendQuery(path, params) {
  const query = new URLSearchParams(params);
  return path + "?" + query.toString();
}

function normalizeLogLimit(value) {
  const limit = Number.parseInt(value || "100", 10);
  if (Number.isNaN(limit)) {
    return 100;
  }
  return Math.min(500, Math.max(25, limit));
}

function formatRefreshError(error) {
  if (error.statusCode && error.response !== undefined && error.response !== null) {
    return "HTTP " + error.statusCode + ": " + formatComdirectResponse(error.response, error.message);
  }
  if (error.response !== undefined && error.response !== null) {
    return formatComdirectResponse(error.response, error.message);
  }
  return error.message || "Unable to refresh balances";
}

function formatComdirectResponse(response, fallback) {
  if (typeof response === "string") {
    return truncate(response.trim()) || fallback || "Unable to refresh balances";
  }
  if (Array.isArray(response.messages) && response.messages.length > 0) {
    const message = response.messages[0];
    return truncate([message.key, message.message].filter(Boolean).join(" - ")) || fallback;
  }
  const directMessage = response.message || response.detail || response.error || response.error_description;
  if (directMessage) {
    return truncate(String(directMessage));
  }
  try {
    return truncate(JSON.stringify(response)) || fallback || "Unable to refresh balances";
  } catch (_error) {
    return fallback || "Unable to refresh balances";
  }
}

function truncate(value) {
  if (!value) {
    return null;
  }
  return value.length > 500 ? value.slice(0, 497) + "..." : value;
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
