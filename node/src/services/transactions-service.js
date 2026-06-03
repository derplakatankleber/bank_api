const { createTransactionRepository } = require("../persistence/repositories");

class TransactionService {
  constructor(client, db) {
    this.client = client;
    this.db = db;
  }

  async refreshTransactions(accountId, options = {}) {
    const response = await this.client.getAccountTransactions(accountId, {
      headers: options.headers,
      transactionState: options.transactionState,
      transactionDirection: options.transactionDirection,
      pagingFirst: options.pagingFirst,
      withAttr: options.withAttr
    });
    createTransactionRepository(this.db).upsertTransactions(response.values || [], accountId);
    return response;
  }

  listCachedTransactions(accountId) {
    return createTransactionRepository(this.db).listTransactions(accountId);
  }
}

function toTransactionRecord(transaction) {
  const amount = transaction.amount || {};
  return {
    reference: transaction.reference || null,
    booking_date: parseDate(transaction.bookingDate),
    valuta_date: parseDate(transaction.valutaDate),
    remittance_info: transaction.remittanceInfo || null,
    transaction_type: transaction.transactionType ? transaction.transactionType.text || null : null,
    amount: {
      value: amount.value === undefined || amount.value === null ? null : Number(amount.value),
      currency: amount.unit || null
    }
  };
}

function parseDate(value) {
  if (!value) {
    return null;
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return parsed.toISOString().slice(0, 10);
}

module.exports = {
  TransactionService,
  toTransactionRecord
};
