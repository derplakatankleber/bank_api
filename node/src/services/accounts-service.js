const { createPositionRepository } = require("../persistence/repositories");

class AccountService {
  constructor(client, db, configurationService = null) {
    this.client = client;
    this.db = db;
    this.configurationService = configurationService;
  }

  async refreshAccountBalances(userId = "user", options = {}) {
    const response = await this.client.getAccountBalances(userId || "user", {
      headers: options.headers,
      withoutAttr: options.withoutAttr
    });
    const balances = response.values || [];
    createPositionRepository(this.db).upsertBalances(balances);
    this.storeFirstAccountIdIfMissing(balances);
    return response;
  }

  listCachedBalances() {
    return createPositionRepository(this.db).listPositions();
  }

  storeFirstAccountIdIfMissing(balances) {
    if (!this.configurationService) {
      return;
    }
    const configuration = this.configurationService.getConfiguration();
    if (configuration.account_id) {
      return;
    }
    const firstAccountId = balances.map(extractAccountId).find(Boolean);
    if (firstAccountId) {
      this.configurationService.updateConfiguration({ account_id: firstAccountId });
    }
  }
}

function toBalanceSummary(balance) {
  const amount = deriveBalanceAmount(balance);
  const accountId = extractAccountId(balance);
  return {
    account_id: accountId,
    amount: amount.value,
    currency: amount.currency
  };
}

function extractAccountId(balance) {
  return balance.accountId || (balance.account && balance.account.accountId) || null;
}

function deriveBalanceAmount(balance) {
  if (balance.balance && balance.balance.value !== undefined && balance.balance.value !== null) {
    return {
      value: Number(balance.balance.value),
      currency: balance.balance.unit || null
    };
  }
  if (
    balance.availableCashAmount &&
    balance.availableCashAmount.value !== undefined &&
    balance.availableCashAmount.value !== null
  ) {
    return {
      value: Number(balance.availableCashAmount.value),
      currency: balance.availableCashAmount.unit || null
    };
  }
  return {
    value: null,
    currency: null
  };
}

module.exports = {
  AccountService,
  toBalanceSummary
};
