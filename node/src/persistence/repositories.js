function createTransactionRepository(db) {
  return {
    upsertTransactions(transactions, accountId) {
      const select = db.prepare("SELECT id FROM transactions WHERE external_id = ?");
      const insert = db.prepare(`
        INSERT INTO transactions (external_id, account_id, booking_date, amount, currency, raw)
        VALUES (@external_id, @account_id, @booking_date, @amount, @currency, @raw)
      `);
      const update = db.prepare(`
        UPDATE transactions
        SET account_id = @account_id,
            booking_date = @booking_date,
            amount = @amount,
            currency = @currency,
            raw = @raw,
            updated_at = CURRENT_TIMESTAMP
        WHERE external_id = @external_id
      `);

      const run = db.transaction((items) => {
        for (const transaction of items || []) {
          const externalId = transaction.reference || transaction.endToEndReference || null;
          const row = mapTransaction(transaction, accountId, externalId);
          if (externalId && select.get(externalId)) {
            update.run(row);
          } else {
            insert.run(row);
          }
        }
      });

      run(transactions);
    },

    listTransactions(accountId) {
      const rows = db
        .prepare("SELECT raw FROM transactions WHERE account_id = ? ORDER BY booking_date DESC, id DESC")
        .all(accountId);
      return rows.map((row) => parseJson(row.raw)).filter(Boolean);
    }
  };
}

function createPositionRepository(db) {
  return {
    upsertBalances(balances) {
      const statement = db.prepare(`
        INSERT INTO positions (account_id, balance_amount, currency, raw, updated_at)
        VALUES (@account_id, @balance_amount, @currency, @raw, CURRENT_TIMESTAMP)
        ON CONFLICT(account_id) DO UPDATE SET
          balance_amount = excluded.balance_amount,
          currency = excluded.currency,
          raw = excluded.raw,
          updated_at = CURRENT_TIMESTAMP
      `);

      const run = db.transaction((items) => {
        for (const balance of items || []) {
          const accountId = balance.accountId || (balance.account && balance.account.accountId);
          if (!accountId) {
            continue;
          }
          statement.run({
            account_id: accountId,
            balance_amount: extractAmount(balance),
            currency: extractCurrency(balance),
            raw: JSON.stringify(balance)
          });
        }
      });

      run(balances);
    },

    listPositions() {
      const rows = db.prepare("SELECT raw FROM positions ORDER BY account_id").all();
      return rows.map((row) => parseJson(row.raw)).filter(Boolean);
    }
  };
}

function createSettingsRepository(db) {
  return {
    get(key) {
      return db.prepare("SELECT key, value, updated_at FROM settings WHERE key = ?").get(key) || null;
    },

    set(key, value) {
      db.prepare(`
        INSERT INTO settings (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET
          value = excluded.value,
          updated_at = CURRENT_TIMESTAMP
      `).run(key, value === undefined ? null : value);
      return this.get(key);
    },

    listAll() {
      return db.prepare("SELECT key, value, updated_at FROM settings ORDER BY key").all();
    }
  };
}

function createOrderRepository(db) {
  return {
    listOrders() {
      return db.prepare("SELECT * FROM orders ORDER BY created_at DESC, id DESC").all();
    },

    get(orderId) {
      return db.prepare("SELECT * FROM orders WHERE id = ?").get(orderId) || null;
    },

    create(orderData) {
      const result = db.prepare(`
        INSERT INTO orders (instrument, side, order_type, quantity, limit_price, notes)
        VALUES (?, ?, ?, ?, ?, ?)
      `).run(
        orderData.instrument,
        orderData.side,
        orderData.orderType,
        orderData.quantity,
        orderData.limitPrice === undefined ? null : orderData.limitPrice,
        orderData.notes || null
      );
      return this.get(result.lastInsertRowid);
    },

    updateStatus(orderId, status) {
      db.prepare("UPDATE orders SET status = ? WHERE id = ?").run(status, orderId);
      return this.get(orderId);
    }
  };
}

function createSyncLogRepository(db) {
  return {
    create(jobName, status, detail = null) {
      const result = db.prepare(`
        INSERT INTO sync_logs (job_name, status, detail, started_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
      `).run(jobName, status, detail);
      return this.get(result.lastInsertRowid);
    },

    update(logId, status, detail = null) {
      db.prepare(`
        UPDATE sync_logs
        SET status = ?, detail = ?, finished_at = CURRENT_TIMESTAMP
        WHERE id = ?
      `).run(status, detail, logId);
      return this.get(logId);
    },

    get(logId) {
      return db.prepare("SELECT * FROM sync_logs WHERE id = ?").get(logId) || null;
    }
  };
}

function mapTransaction(transaction, accountId, externalId) {
  const amount = transaction.amount || {};
  return {
    external_id: externalId,
    account_id: accountId,
    booking_date: transaction.bookingDate || null,
    amount: amount.value === undefined || amount.value === null ? null : Number(amount.value),
    currency: amount.unit || null,
    raw: JSON.stringify(transaction)
  };
}

function extractAmount(balance) {
  if (balance.balance && balance.balance.value !== undefined && balance.balance.value !== null) {
    return Number(balance.balance.value);
  }
  if (
    balance.availableCashAmount &&
    balance.availableCashAmount.value !== undefined &&
    balance.availableCashAmount.value !== null
  ) {
    return Number(balance.availableCashAmount.value);
  }
  return null;
}

function extractCurrency(balance) {
  if (balance.balance && balance.balance.unit) {
    return balance.balance.unit;
  }
  if (balance.availableCashAmount && balance.availableCashAmount.unit) {
    return balance.availableCashAmount.unit;
  }
  return null;
}

function parseJson(value) {
  if (!value) {
    return null;
  }
  try {
    return JSON.parse(value);
  } catch (_error) {
    return null;
  }
}

module.exports = {
  createOrderRepository,
  createPositionRepository,
  createSettingsRepository,
  createSyncLogRepository,
  createTransactionRepository
};
