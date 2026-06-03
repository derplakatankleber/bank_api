function collectForwardHeaders(req) {
  const headers = {};
  const authorization = req.get("Authorization");
  const requestInfo = req.get("x-http-request-info");
  const sessionInfo = req.get("x-http-session-info");

  if (authorization) {
    headers.Authorization = authorization;
  }
  if (requestInfo) {
    headers["x-http-request-info"] = requestInfo;
  }
  if (sessionInfo) {
    headers["x-http-session-info"] = sessionInfo;
  }

  return Object.keys(headers).length === 0 ? undefined : headers;
}

module.exports = {
  collectForwardHeaders
};
