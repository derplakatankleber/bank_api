const express = require("express");
const { collectForwardHeaders } = require("./headers");
const { toBalanceSummary } = require("../services/accounts-service");

function createAccountsRouter(accountService) {
  const router = express.Router();

  router.get("/:userId/balances", async (req, res, next) => {
    try {
      let refreshed = false;
      let balances;

      if (req.query.refresh === "true") {
        const response = await accountService.refreshAccountBalances(req.params.userId, {
          headers: collectForwardHeaders(req)
        });
        balances = response.values || [];
        refreshed = true;
      } else {
        balances = accountService.listCachedBalances();
        if (balances.length === 0) {
          const response = await accountService.refreshAccountBalances(req.params.userId, {
            headers: collectForwardHeaders(req)
          });
          balances = response.values || [];
          refreshed = true;
        }
      }

      res.json({ data: balances.map(toBalanceSummary), refreshed });
    } catch (error) {
      next(error);
    }
  });

  router.post("/:userId/balances/refresh", async (req, res, next) => {
    try {
      const response = await accountService.refreshAccountBalances(req.params.userId, {
        headers: collectForwardHeaders(req)
      });
      res.json({ data: (response.values || []).map(toBalanceSummary), refreshed: true });
    } catch (error) {
      next(error);
    }
  });

  return router;
}

module.exports = {
  createAccountsRouter
};
