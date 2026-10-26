async function refreshAccessToken(): Promise<string | null> {
  const refresh = localStorage.getItem("refresh");

  if (!refresh) {
    return null;
  }

  const response = await fetch("token/refresh/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ refresh }),
  });

  if (!response.ok) {
    return null;
  }

  const data = await response.json();

  localStorage.setItem("access", data.access);

  return data.access;
}

export async function apiFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  let access = localStorage.getItem("access");
  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  // First attempt
  const response = await fetch(`${API_URL}/${url}`, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${access}`,
      "Content-Type": "application/json",
    },
  });

  // Success or other error
  if (response.status !== 401) {
    return response;
  }

  // Try refreshing the access token
  access = await refreshAccessToken();

  if (!access) {
    // Refresh token is invalid/expired
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");

    window.location.href = "/login";

    throw new Error("Session expired");
  }

  // Retry original request with the new access token
  return fetch(`${API_URL}/${url}`, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${access}`,
      "Content-Type": "application/json",
    },
  });
}