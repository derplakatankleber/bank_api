const { BaseComdirectClient } = require("./base-client");

class BankingClient extends BaseComdirectClient {
  getAccountBalances(user, options = {}) {
    return this.requestJson("GET", `/banking/clients/${encodeURIComponent(user)}/v2/accounts/balances`, {
      params: {
        "without-attr": options.withoutAttr
      },
      headers: options.headers
    });
  }

  getAccountTransactions(accountId, options = {}) {
    return this.requestJson("GET", `/banking/v1/accounts/${encodeURIComponent(accountId)}/transactions`, {
      params: {
        transactionState: options.transactionState,
        transactionDirection: options.transactionDirection,
        "paging-first": options.pagingFirst,
        "with-attr": options.withAttr
      },
      headers: options.headers
    });
  }
}

module.exports = {
  BankingClient
};
