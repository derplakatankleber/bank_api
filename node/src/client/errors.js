class ComdirectAPIError extends Error {
  constructor(message, options = {}) {
    super(message);
    this.name = "ComdirectAPIError";
    this.statusCode = options.statusCode;
    this.response = options.response;
    this.request = options.request;
  }
}

module.exports = {
  ComdirectAPIError
};
