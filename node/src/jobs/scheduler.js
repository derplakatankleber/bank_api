const { createSyncLogRepository } = require("../persistence/repositories");

class DataRefreshScheduler {
  constructor(db) {
    this.db = db;
    this.jobs = new Map();
  }

  scheduleAccountBalanceRefresh(options) {
    const jobName = options.jobId || `account-balance-refresh-${options.userId}`;
    return this.schedule(jobName, options.intervalMinutes, () => {
      return options.service.refreshAccountBalances(options.userId, {
        headers: options.headers,
        withoutAttr: options.withoutAttr
      });
    });
  }

  scheduleTransactionRefresh(options) {
    const jobName = options.jobId || `transaction-refresh-${options.accountId}`;
    return this.schedule(jobName, options.intervalMinutes, () => {
      return options.service.refreshTransactions(options.accountId, {
        headers: options.headers,
        transactionState: options.transactionState,
        transactionDirection: options.transactionDirection,
        pagingFirst: options.pagingFirst,
        withAttr: options.withAttr
      });
    });
  }

  schedule(jobName, intervalMinutes, task) {
    this.cancel(jobName);
    const intervalMs = Math.max(1, Number(intervalMinutes)) * 60 * 1000;
    const timer = setInterval(() => {
      this.runWithLogging(jobName, task);
    }, intervalMs);
    timer.unref();
    this.jobs.set(jobName, timer);
    return jobName;
  }

  cancel(jobName) {
    const timer = this.jobs.get(jobName);
    if (timer) {
      clearInterval(timer);
      this.jobs.delete(jobName);
    }
  }

  shutdown() {
    for (const jobName of this.jobs.keys()) {
      this.cancel(jobName);
    }
  }

  async runWithLogging(jobName, task) {
    const repository = createSyncLogRepository(this.db);
    const log = repository.create(jobName, "running");
    try {
      await task();
      repository.update(log.id, "succeeded");
    } catch (error) {
      repository.update(log.id, "failed", error.message);
      throw error;
    }
  }
}

module.exports = {
  DataRefreshScheduler
};
