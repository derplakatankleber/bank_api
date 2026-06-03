const { BaseComdirectClient } = require("./base-client");

class SessionClient extends BaseComdirectClient {
  getSessions(user, options = {}) {
    return this.requestJson("GET", `/session/clients/${encodeURIComponent(user)}/v1/sessions`, {
      headers: options.headers
    });
  }
}

module.exports = {
  SessionClient
};
