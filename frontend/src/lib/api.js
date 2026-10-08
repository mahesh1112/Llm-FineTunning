import { initialWorkspace } from '../mocks/mockData'

let workspace = structuredClone(initialWorkspace)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, '')

async function request(path, { body, ...options } = {}) {
  const headers = new Headers(options.headers)
  const requestOptions = { ...options, headers }

  if (body instanceof FormData) {
    requestOptions.body = body
  } else if (body !== undefined) {
    headers.set('Content-Type', 'application/json')
    requestOptions.body = JSON.stringify(body)
  }

  const response = await fetch(`${API_BASE_URL}/api${path}`, requestOptions)
  const data = response.status === 204 ? null : await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(data?.detail || data?.message || `API request failed (${response.status}).`)
  }
  return data
}

function delay(value) {
  return new Promise((resolve) => window.setTimeout(() => resolve(value), 180))
}

export const api = {
  isPreviewMode: !API_BASE_URL,

  getWorkspace() {
    return API_BASE_URL ? request('/workspace') : delay(structuredClone(workspace))
  },

  listModels({ query = '', cursor = '' } = {}) {
    if (API_BASE_URL) {
      const params = new URLSearchParams({ query, limit: '20' })
      if (cursor) params.set('cursor', cursor)
      return request(`/models?${params}`).then((data) => Array.isArray(data) ? { items: data, nextCursor: null } : data)
    }

    const normalizedQuery = query.trim().toLowerCase()
    const items = workspace.models.filter((model) => `${model.name} ${model.family}`.toLowerCase().includes(normalizedQuery))
    return delay({ items, nextCursor: null })
  },

  getHardwareProfile() {
    return API_BASE_URL ? request('/hardware-profile') : delay(workspace.machine)
  },

  estimateTraining(payload) {
    if (API_BASE_URL) return request('/estimates', { method: 'POST', body: payload })

    const baselineMinutes = {
      instructional_finetuning: 35,
      continued_pretraining: 90,
      distillation: 60,
      quantization: 8,
    }[payload.workflow] || 35
    const techniqueFactor = payload.technique?.toLowerCase().includes('full') ? 1.8 : 1
    const fileFactor = payload.datasetSizeBytes ? 1 + Math.min(payload.datasetSizeBytes / 500_000_000, 1) : 1
    const minimum = Math.round(baselineMinutes * techniqueFactor * fileFactor * 60)
    return delay({
      minSeconds: minimum,
      maxSeconds: Math.round(minimum * 1.7),
      confidence: 'illustrative',
      hardware: workspace.machine,
      assumptions: ['Preview range based on sample hardware; configure the Python API for a measured estimate.'],
    })
  },

  async uploadDataset(file, workflow) {
    if (API_BASE_URL) {
      const body = new FormData()
      body.set('file', file)
      body.set('workflow', workflow)
      return request('/datasets/import', { method: 'POST', body })
    }

    await delay(null)
    return { id: `dataset-${crypto.randomUUID()}`, name: file.name, sizeBytes: file.size, previewOnly: true }
  },

  async createProject(projectDetails) {
    if (API_BASE_URL) return request('/projects', { method: 'POST', body: projectDetails })

    const project = {
      id: `project-${crypto.randomUUID()}`,
      ...projectDetails,
      model: projectDetails.modelName,
      runCount: 0,
      lastRunStatus: 'Draft',
      updatedLabel: 'Created just now',
    }
    workspace = { ...workspace, projects: [project, ...workspace.projects] }
    await delay(null)
    return project
  },
}