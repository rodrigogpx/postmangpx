export { COOKIE_NAME, ONE_YEAR_MS } from "@shared/const";

// Environment variables - with fallbacks for missing values
const OAUTH_PORTAL_URL = import.meta.env.VITE_OAUTH_PORTAL_URL || "";
const APP_ID = import.meta.env.VITE_APP_ID || "";

// Check if OAuth is configured
export const isOAuthConfigured = () => {
  return OAUTH_PORTAL_URL.length > 0 && APP_ID.length > 0;
};

// Generate login URL at runtime so redirect URI reflects the current origin.
export const getLoginUrl = () => {
  if (!isOAuthConfigured()) {
    console.error(
      "[Auth] OAuth not configured. Missing VITE_OAUTH_PORTAL_URL or VITE_APP_ID.",
      "\nVITE_OAUTH_PORTAL_URL:", OAUTH_PORTAL_URL || "(not set)",
      "\nVITE_APP_ID:", APP_ID || "(not set)"
    );
    return "#oauth-not-configured";
  }

  const redirectUri = `${window.location.origin}/api/oauth/callback`;
  const state = btoa(redirectUri);

  const url = new URL(`${OAUTH_PORTAL_URL}/app-auth`);
  url.searchParams.set("appId", APP_ID);
  url.searchParams.set("redirectUri", redirectUri);
  url.searchParams.set("state", state);
  url.searchParams.set("type", "signIn");

  return url.toString();
};
