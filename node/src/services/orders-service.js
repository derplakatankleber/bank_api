const { createOrderRepository } = require("../persistence/repositories");

const ALLOWED_STATUSES = new Set(["pending", "placed", "executed", "cancelled"]);

class OrderService {
  constructor(db) {
    this.db = db;
  }

  listOrders() {
    return createOrderRepository(this.db).listOrders().map(toOrderRecord);
  }

  createOrder(orderData) {
    validateOrder(orderData);
    const order = createOrderRepository(this.db).create({
      instrument: orderData.instrument.trim(),
      side: orderData.side,
      orderType: orderData.order_type || orderData.orderType,
      quantity: Number(orderData.quantity),
      limitPrice: optionalNumber(orderData.limit_price ?? orderData.limitPrice),
      notes: orderData.notes || null
    });
    return toOrderRecord(order);
  }

  updateOrderStatus(orderId, status) {
    const normalized = String(status || "").toLowerCase();
    if (!ALLOWED_STATUSES.has(normalized)) {
      throw new Error(`Unsupported order status '${status}'`);
    }
    const order = createOrderRepository(this.db).updateStatus(Number(orderId), normalized);
    return order ? toOrderRecord(order) : null;
  }
}

function validateOrder(orderData) {
  if (!orderData.instrument || !String(orderData.instrument).trim()) {
    throw new Error("Instrument is required");
  }
  if (!["buy", "sell"].includes(orderData.side)) {
    throw new Error("Side must be buy or sell");
  }
  const orderType = orderData.order_type || orderData.orderType;
  if (!["market", "limit"].includes(orderType)) {
    throw new Error("Order type must be market or limit");
  }
  const quantity = Number(orderData.quantity);
  if (!Number.isFinite(quantity) || quantity <= 0) {
    throw new Error("Quantity must be greater than zero");
  }
}

function optionalNumber(value) {
  if (value === undefined || value === null || value === "") {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function toOrderRecord(order) {
  return {
    id: order.id,
    instrument: order.instrument,
    side: order.side,
    order_type: order.order_type,
    quantity: order.quantity,
    limit_price: order.limit_price,
    status: order.status,
    notes: order.notes,
    created_at: order.created_at
  };
}

module.exports = {
  OrderService,
  toOrderRecord
};
