class OAuthTokenService {
  constructor(configurationService, oauthClient) {
    this.configurationService = configurationService;
    this.oauthClient = oauthClient;
    this.cachedToken = null;
  }

  async getAccessToken() {
    if (this.cachedToken && Date.now() < this.cachedToken.expiresAt) {
      return this.cachedToken.accessToken;
    }

    const token = await this.oauthClient.passwordGrant(this.configurationService.getComdirectCredentials());
    if (!token.access_token) {
      throw new Error("comdirect OAuth response did not contain access_token");
    }

    const expiresInSeconds = Number(token.expires_in || 600);
    this.cachedToken = {
      accessToken: token.access_token,
      expiresAt: Date.now() + Math.max(1, expiresInSeconds - 60) * 1000
    };
    return this.cachedToken.accessToken;
  }

  clear() {
    this.cachedToken = null;
  }
}

module.exports = {
  OAuthTokenService
};
