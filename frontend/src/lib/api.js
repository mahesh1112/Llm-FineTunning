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
    const error = new Error(data?.detail || data?.message || `API request failed (${response.status}).`)
    error.status = response.status
    throw error
  }
  return data
}

function delay(value) {
  return new Promise((resolve) => window.setTimeout(() => resolve(value), 180))
}

export const api = {
  isPreviewMode: !API_BASE_URL,

  checkHealth() {
    if (!API_BASE_URL) return Promise.resolve({ status: 'preview' })
    return request('/health')
  },

  getWorkspace() {
    if (!API_BASE_URL) return delay(structuredClone(workspace))
    return request('/workspace').catch((error) => {
      if (error.status !== 404) throw error
      return delay({ ...structuredClone(workspace), previewOnly: true })
    })
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

  async startEvaluation({ runId, datasetId }) {
    if (API_BASE_URL) {
      return request('/evaluations', { method: 'POST', body: { runId, datasetId } })
    }

    const run = workspace.runs.find((item) => item.id === runId)
    const dataset = workspace.datasets.find((item) => item.id === datasetId)
    if (!run || !dataset) throw new Error('Select an available trained run and evaluation dataset.')
    if (run.datasetId === datasetId) throw new Error('Choose a held-out dataset that was not used for training.')

    const evaluation = {
      id: `evaluation-${crypto.randomUUID()}`,
      status: 'completed',
      runId,
      datasetId,
      modelName: run.model,
      datasetName: dataset.name,
      samplesEvaluated: Number(dataset.rows?.replaceAll(',', '')) || 256,
      completedAt: new Date().toISOString(),
      metrics: [
        { name: 'Exact match', value: 0.824, formatted: '82.4%', direction: 'higher' },
        { name: 'Token F1', value: 0.891, formatted: '89.1%', direction: 'higher' },
        { name: 'Validation loss', value: 0.638, formatted: '0.638', direction: 'lower' },
      ],
      previewOnly: true,
    }
    workspace.evaluations = [evaluation, ...(workspace.evaluations || [])]
    await delay(null)
    return evaluation
  },

  getEvaluation(evaluationId) {
    if (API_BASE_URL) return request(`/evaluations/${encodeURIComponent(evaluationId)}`)
    const evaluation = workspace.evaluations?.find((item) => item.id === evaluationId)
    return evaluation ? delay(evaluation) : Promise.reject(new Error('Evaluation result was not found.'))
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