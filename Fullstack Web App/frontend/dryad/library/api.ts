let csrfToken: string | null = null;

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS", "TRACE"]);

async function getCsrfToken(): Promise<string> {
  if (csrfToken) {
    return csrfToken;
  }

  const response = await fetch(`${API_URL}/csrf/`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Unable to initialize CSRF protection.");
  }

  const data: { csrfToken: string } = await response.json();
  csrfToken = data.csrfToken;
  return data.csrfToken;
}

export function updateCsrfToken(token: string): void {
  csrfToken = token;
}

export async function apiRequest(
  url: string,
  options: RequestInit = {},
): Promise<Response> {
  const method = (options.method ?? "GET").toUpperCase();
  const headers = new Headers(options.headers);

  if (!SAFE_METHODS.has(method)) {
    headers.set("X-CSRFToken", await getCsrfToken());
  }

  if (
    options.body &&
    !(typeof FormData !== "undefined" && options.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }

  return fetch(`${API_URL}/${url}`, {
    ...options,
    method,
    credentials: "include",
    headers,
  });
}

export async function logoutRequest(): Promise<void> {
  try {
    const response = await apiRequest("logout/", { method: "POST" });
    if (!response.ok) {
      throw new Error("Unable to clear the authentication cookies.");
    }
  } finally {
    csrfToken = null;
    localStorage.removeItem("userID");
  }
}

export async function apiFetch(
  url: string,
  options: RequestInit = {},
): Promise<Response> {
  const response = await apiRequest(url, options);
  if (response.status !== 401) {
    return response;
  }

  const refreshResponse = await apiRequest("token/refresh/", {
    method: "POST",
  });
  if (!refreshResponse.ok) {
    try {
      await logoutRequest();
    } catch (error) {
      console.error("Session cleanup failed:", error);
    }

    window.location.href = "/login";
    throw new Error("Session expired");
  }

  return apiRequest(url, options);
}
