const browserHost = typeof window !== 'undefined' ? window.location.hostname : '127.0.0.1'
const configuredApiUrl = import.meta.env.VITE_API_URL?.trim()
const defaultApiUrl = `http://${browserHost === 'localhost' ? 'localhost' : '127.0.0.1'}:8000/api`
function resolveApiUrl(value) {
  const url = new URL(value || defaultApiUrl)
  const loopbackHosts = new Set(['localhost', '127.0.0.1'])
  if (loopbackHosts.has(url.hostname) && loopbackHosts.has(browserHost)) url.hostname = browserHost
  return url.toString().replace(/\/$/, '')
}

const API_URL = resolveApiUrl(configuredApiUrl)

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  })

  if (!response.ok) {
    let detail = 'Request failed'
    try {
      const payload = await response.json()
      detail = payload.detail || detail
    } catch {
      // Keep the public error generic when the API does not return JSON.
    }
    const error = new Error(typeof detail === 'string' ? detail : 'Request failed')
    error.status = response.status
    throw error
  }

  return response.json()
}

export function submitEnquiry(payload) {
  return request('/enquiries', { method: 'POST', body: JSON.stringify(payload) })
}

export function submitAdmissionEnquiry(payload) {
  return request('/admissions/enquiry', { method: 'POST', body: JSON.stringify(payload) })
}

export function submitContact(payload) {
  return request('/contact', { method: 'POST', body: JSON.stringify(payload) })
}

export function getNews() {
  return request('/news')
}

export function getGallery() {
  return request('/gallery')
}

export function getFAQ() {
  return request('/faq')
}

export function getSchool() {
  return request('/school')
}

export function getHealth() {
  return request('/health')
}

export function adminLogin(payload) {
  return request('/admin/login', { method: 'POST', body: JSON.stringify(payload) })
}

export function adminLogout() {
  return request('/admin/logout', { method: 'POST' })
}

export function getAdminStats() {
  return request('/admin/stats')
}

export function getAdminEnquiries({ search = '', status = '', grade = '', page = 1, pageSize = 20 } = {}) {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  if (search) params.set('search', search)
  if (status) params.set('status', status)
  if (grade) params.set('grade', grade)
  return request(`/admin/enquiries?${params.toString()}`)
}

export function getAdminEnquiry(id) {
  return request(`/admin/enquiries/${id}`)
}

export function updateAdminEnquiry(id, payload) {
  return request(`/admin/enquiries/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
}

export function deleteAdminEnquiry(id) {
  return request(`/admin/enquiries/${id}`, { method: 'DELETE' })
}
