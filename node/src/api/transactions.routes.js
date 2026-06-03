const express = require("express");
const { collectForwardHeaders } = require("./headers");
const { toTransactionRecord } = require("../services/transactions-service");

function createTransactionsRouter(transactionService) {
  const router = express.Router();

  router.get("/:accountId/transactions", async (req, res, next) => {
    try {
      let refreshed = false;
      let transactions;

      if (req.query.refresh === "true") {
        const response = await refresh(transactionService, req);
        transactions = response.values || [];
        refreshed = true;
      } else {
        transactions = transactionService.listCachedTransactions(req.params.accountId);
        if (transactions.length === 0) {
          const response = await refresh(transactionService, req);
          transactions = response.values || [];
          refreshed = true;
        }
      }

      res.json({ data: transactions.map(toTransactionRecord), refreshed });
    } catch (error) {
      next(error);
    }
  });

  router.post("/:accountId/transactions/refresh", async (req, res, next) => {
    try {
      const response = await refresh(transactionService, req);
      res.json({ data: (response.values || []).map(toTransactionRecord), refreshed: true });
    } catch (error) {
      next(error);
    }
  });

  return router;
}

function refresh(transactionService, req) {
  return transactionService.refreshTransactions(req.params.accountId, {
    headers: collectForwardHeaders(req),
    transactionState: req.query.transaction_state,
    transactionDirection: req.query.transaction_direction,
    pagingFirst: req.query.paging_first,
    withAttr: req.query.with_attr
  });
}

module.exports = {
  createTransactionsRouter
};
