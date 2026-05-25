import {
  apiFetch,
  clearTokens,
  getApiBaseUrl,
  parseErrorMessage,
  setTokens,
} from "@/lib/apiClient"

async function publicFetch(path, options) {
  return fetch(`${getApiBaseUrl()}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  })
}

export async function checkEmail(email) {
  const response = await publicFetch("/auth/check-email", {
    method: "POST",
    body: JSON.stringify({ email: email.trim().toLowerCase() }),
  })
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }
  return response.json()
}

export async function register({ email, password, fullName, timezone }) {
  const response = await publicFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify({
      email,
      password,
      full_name: fullName || "",
      timezone: timezone || "Asia/Kolkata",
    }),
  })

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  const data = await response.json()
  setTokens({
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
  })
  return data
}

export async function login({ email, password }) {
  const response = await publicFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  })

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  const data = await response.json()
  setTokens({
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
  })
  return data
}

export async function requestPasswordReset(email) {
  const response = await publicFetch("/auth/password-reset/request", {
    method: "POST",
    body: JSON.stringify({ email: email.trim().toLowerCase() }),
  })
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }
  return response.json()
}

export async function confirmPasswordReset({ email, otp, newPassword }) {
  const response = await publicFetch("/auth/password-reset/confirm", {
    method: "POST",
    body: JSON.stringify({
      email: email.trim().toLowerCase(),
      otp: otp.trim(),
      new_password: newPassword,
    }),
  })
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }
  return response.json()
}

export async function logout(refreshToken) {
  try {
    await apiFetch("/auth/logout", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken || null }),
    })
  } finally {
    clearTokens()
  }
}

export async function fetchMe() {
  const response = await apiFetch("/auth/me")
  if (response.status === 401) return null
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }
  return response.json()
}

export async function updateProfile({ fullName, timezone }) {
  const response = await apiFetch("/auth/me", {
    method: "PATCH",
    body: JSON.stringify({
      full_name: fullName,
      timezone,
    }),
  })
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }
  return response.json()
}

export async function changePassword({ currentPassword, newPassword }) {
  const response = await apiFetch("/auth/password", {
    method: "PATCH",
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  })
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }
  return response.json()
}
