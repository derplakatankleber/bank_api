class ComdirectAPIError extends Error {
  constructor(message, options = {}) {
    super(message);
    this.name = "ComdirectAPIError";
    this.statusCode = options.statusCode;
    this.response = options.response;
  }
}

module.exports = {
  ComdirectAPIError
};
