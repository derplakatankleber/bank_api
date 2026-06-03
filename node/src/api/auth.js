const crypto = require("node:crypto");

function createRequireAppKey(configurationService) {
  return (req, res, next) => {
    const configuredKey = configurationService.getAppKey();
    const providedKey = req.get("X-App-Key") || "";

    if (!providedKey || !safeEqual(providedKey, configuredKey)) {
      return res.status(401).json({ detail: "Invalid or missing app key" });
    }

    return next();
  };
}

function safeEqual(left, right) {
  const leftBuffer = Buffer.from(left);
  const rightBuffer = Buffer.from(right);
  if (leftBuffer.length !== rightBuffer.length) {
    return false;
  }
  return crypto.timingSafeEqual(leftBuffer, rightBuffer);
}

module.exports = {
  createRequireAppKey
};
