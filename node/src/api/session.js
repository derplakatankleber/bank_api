const crypto = require("node:crypto");

const COOKIE_NAME = "bank_api_session";

function sessionMiddleware(options = {}) {
  const secret = options.secret || process.env.BANK_API_SESSION_SECRET || "insecure-development-secret";

  return (req, res, next) => {
    req.session = readSession(req, secret);
    req.saveSession = (session) => {
      writeSession(res, session, secret);
    };
    req.clearSession = () => {
      res.setHeader("Set-Cookie", `${COOKIE_NAME}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0`);
    };
    next();
  };
}

function readSession(req, secret) {
  const cookies = parseCookies(req.headers.cookie || "");
  const value = cookies[COOKIE_NAME];
  if (!value) {
    return {};
  }
  const [payload, signature] = value.split(".");
  if (!payload || !signature || sign(payload, secret) !== signature) {
    return {};
  }
  try {
    return JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
  } catch (_error) {
    return {};
  }
}

function writeSession(res, session, secret) {
  const payload = Buffer.from(JSON.stringify(session), "utf8").toString("base64url");
  const signature = sign(payload, secret);
  res.setHeader("Set-Cookie", `${COOKIE_NAME}=${payload}.${signature}; Path=/; HttpOnly; SameSite=Lax`);
}

function sign(payload, secret) {
  return crypto.createHmac("sha256", secret).update(payload).digest("base64url");
}

function parseCookies(header) {
  const cookies = {};
  for (const part of header.split(";")) {
    const [key, ...value] = part.trim().split("=");
    if (key) {
      cookies[key] = value.join("=");
    }
  }
  return cookies;
}

module.exports = {
  sessionMiddleware
};
