import { useEffect, useState } from 'react'
import {
  Activity,
  ArrowUpRight,
  Box,
  Check,
  Cpu,
  FlaskConical,
  Database,
  HardDrive,
  LayoutDashboard,
  Menu,
  Plus,
  X,
} from 'lucide-react'
import { api } from './lib/api'
import './App.css'

const navigation = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'projects', label: 'Projects', icon: Box },
  { id: 'datasets', label: 'Datasets', icon: Database },
  { id: 'runs', label: 'Training runs', icon: Activity },
  { id: 'evaluation', label: 'Evaluation', icon: FlaskConical },
  { id: 'models', label: 'Model catalog', icon: Cpu },
]

const pageDetails = {
  overview: ['Overview', 'Your local training workspace at a glance.'],
  projects: ['Projects', 'Keep datasets, runs, and artifacts organized.'],
  datasets: ['Datasets', 'Review imported data and validation status.'],
  runs: ['Training runs', 'Monitor recent experiments and their outcomes.'],
  evaluation: ['Evaluation', 'Run a trained model against a held-out dataset.'],
  models: ['Model catalog', 'Browse models available in this preview.'],
}

const workflowOptions = [
  {
    id: 'instructional_finetuning',
    label: 'Instructional fine-tuning',
    detail: 'Teach a model a response style or task.',
    techniques: ['LoRA', 'QLoRA'],
    accept: '.jsonl,application/jsonl,application/json',
    format: 'JSONL with instruction/input/output fields or a messages array.',
  },
  {
    id: 'continued_pretraining',
    label: 'Continued pretraining',
    detail: 'Adapt a model to domain-specific text.',
    techniques: ['Full fine-tuning', 'LoRA', 'QLoRA'],
    accept: '.txt,.text,.jsonl,text/plain,application/jsonl',
    format: 'UTF-8 .txt corpus, or JSONL with one text field per record.',
  },
  {
    id: 'distillation',
    label: 'Distillation',
    detail: 'Train a smaller student from teacher examples.',
    techniques: ['LoRA student', 'Full fine-tuning'],
    accept: '.jsonl,application/jsonl,application/json',
    format: 'JSONL with prompt and teacher_response fields.',
  },
  {
    id: 'quantization',
    label: 'Quantization',
    detail: 'Reduce model size for deployment or inference.',
    techniques: ['4-bit (NF4)', '8-bit', '4-bit (GPTQ / AWQ)'],
    accept: '',
    format: '',
  },
]

function formatDuration(seconds) {
  if (!Number.isFinite(seconds)) return '—'
  const minutes = Math.max(1, Math.round(seconds / 60))
  if (minutes < 60) return `${minutes} min`
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return remainingMinutes ? `${hours} hr ${remainingMinutes} min` : `${hours} hr`
}

function Status({ children, tone = 'neutral' }) {
  return <span className={`status status-${tone}`}><i />{children}</span>
}

function PageHeading({ title, description, onCreate }) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">WORKSPACE / {title.toUpperCase()}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {onCreate && <button className="button button-primary" onClick={onCreate}><Plus size={17} /> New project</button>}
    </div>
  )
}

function ProjectDialog({ onClose, onCreate }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [workflow, setWorkflow] = useState(workflowOptions[0].id)
  const [technique, setTechnique] = useState(workflowOptions[0].techniques[0])
  const [modelSearch, setModelSearch] = useState('')
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState('')
  const [nextCursor, setNextCursor] = useState(null)
  const [modelLoading, setModelLoading] = useState(true)
  const [modelError, setModelError] = useState('')
  const [hardware, setHardware] = useState(null)
  const [hardwareError, setHardwareError] = useState('')
  const [estimate, setEstimate] = useState(null)
  const [estimateState, setEstimateState] = useState('idle')
  const [datasetFile, setDatasetFile] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const selectedWorkflow = workflowOptions.find((option) => option.id === workflow)
  const selectedModelDetails = models.find((model) => model.id === selectedModel)

  useEffect(() => {
    let current = true
    api.getHardwareProfile().then((profile) => {
      if (current) setHardware(profile)
    }).catch((requestError) => {
      if (current) setHardwareError(requestError.message)
    })
    return () => { current = false }
  }, [])

  useEffect(() => {
    let current = true
    const timeout = window.setTimeout(() => {
      setModelLoading(true)
      setModelError('')
      api.listModels({ query: modelSearch }).then((result) => {
        if (!current) return
        const items = result.items || []
        setModels(items)
        setNextCursor(result.nextCursor || null)
        setSelectedModel((selected) => items.some((model) => model.id === selected) ? selected : items[0]?.id || '')
      }).catch((requestError) => {
        if (current) setModelError(requestError.message)
      }).finally(() => {
        if (current) setModelLoading(false)
      })
    }, modelSearch ? 250 : 0)
    return () => {
      current = false
      window.clearTimeout(timeout)
    }
  }, [modelSearch])

  useEffect(() => {
    if (!selectedModel || !hardware) return undefined
    let current = true
    const timeout = window.setTimeout(() => {
      setEstimateState('loading')
      api.estimateTraining({
        workflow,
        modelId: selectedModel,
        technique,
        datasetSizeBytes: datasetFile?.size || 0,
        hardwareProfile: hardware,
      }).then((result) => {
        if (!current) return
        setEstimate(result)
        setEstimateState('ready')
      }).catch((requestError) => {
        if (!current) return
        setEstimate(null)
        setEstimateState(requestError.message)
      })
    }, 300)
    return () => {
      current = false
      window.clearTimeout(timeout)
    }
  }, [workflow, selectedModel, technique, datasetFile?.size, hardware])

  async function loadMoreModels() {
    if (!nextCursor || modelLoading) return
    setModelLoading(true)
    try {
      const result = await api.listModels({ query: modelSearch, cursor: nextCursor })
      setModels((current) => [...current, ...(result.items || [])])
      setNextCursor(result.nextCursor || null)
    } catch (requestError) {
      setModelError(requestError.message)
    } finally {
      setModelLoading(false)
    }
  }

  async function submit(event) {
    event.preventDefault()
    const cleanName = name.trim()
    if (!cleanName) {
      setError('Enter a project name to continue.')
      return
    }
    if (cleanName.length > 60) {
      setError('Project names must be 60 characters or fewer.')
      return
    }
    if (!selectedModel) {
      setError('Select a base model to continue.')
      return
    }
    if (workflow !== 'quantization' && !datasetFile) {
      setError('Choose a dataset for this training workflow.')
      return
    }

    setSubmitting(true)
    setError('')
    try {
      const dataset = datasetFile ? await api.uploadDataset(datasetFile, workflow) : null
      await onCreate({
        name: cleanName,
        description: description.trim(),
        workflow,
        technique,
        modelId: selectedModel,
        modelName: selectedModelDetails?.name || selectedModel,
        dataset,
        estimate,
      })
    } catch (requestError) {
      setError(requestError.message || 'Could not create the project. Check the Python API and try again.')
      setSubmitting(false)
    }
  }

  return (
    <div className="dialog-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="dialog project-dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title">
        <div className="dialog-top"><span className="dialog-mark"><Plus size={19} /></span><button className="icon-button" aria-label="Close dialog" onClick={onClose} disabled={submitting}><X size={18} /></button></div>
        <h2 id="dialog-title">Configure a project</h2>
        <p className="dialog-copy">Choose a workflow, model, and training setup. Jobs run through your connected Python service.</p>
        <form onSubmit={submit}>
          <label className="field-label" htmlFor="project-name">Project name</label>
          <input id="project-name" autoFocus value={name} maxLength={60} onChange={(event) => { setName(event.target.value); setError('') }} placeholder="e.g. Support assistant" required />
          <label className="field-label" htmlFor="project-description">Description <span>Optional</span></label>
          <textarea id="project-description" value={description} onChange={(event) => setDescription(event.target.value)} placeholder="What are you tuning this model to do?" rows={3} />
          <fieldset className="workflow-fieldset">
            <legend className="field-label">Workflow</legend>
            <div className="workflow-grid">{workflowOptions.map((option) => <button key={option.id} type="button" className={`workflow-option ${workflow === option.id ? 'workflow-option-active' : ''}`} aria-pressed={workflow === option.id} onClick={() => { setWorkflow(option.id); setTechnique(option.techniques[0]); setDatasetFile(null); setError('') }}><strong>{option.label}</strong><span>{option.detail}</span></button>)}</div>
          </fieldset>

          <label className="field-label" htmlFor="model-search">Base model <span>{api.isPreviewMode ? 'Preview catalog' : 'Hugging Face catalog'}</span></label>
          <input id="model-search" className="model-search" value={modelSearch} onChange={(event) => setModelSearch(event.target.value)} placeholder="Search model name or author" autoComplete="off" />
          <select id="base-model" value={selectedModel} onChange={(event) => setSelectedModel(event.target.value)} disabled={modelLoading && models.length === 0} aria-label="Select a base model">
            {!models.length && <option value="">{modelLoading ? 'Loading models…' : 'No models found'}</option>}
            {models.map((model) => <option key={model.id} value={model.id}>{model.name} {model.parameters ? `· ${model.parameters}` : ''}</option>)}
          </select>
          {modelError && <p className="field-error" role="alert">Could not load models: {modelError}</p>}
          {nextCursor && <button type="button" className="load-more-models" onClick={loadMoreModels} disabled={modelLoading}>{modelLoading ? 'Loading…' : 'Load more model results'}</button>}

          {workflow !== 'quantization' && <>
            <div className="dataset-heading"><span className="field-label">Training dataset</span><span className="required-label">Required</span></div>
            <label className={`upload-field ${datasetFile ? 'upload-field-selected' : ''}`} htmlFor="training-dataset">
              <input id="training-dataset" type="file" accept={selectedWorkflow.accept} onChange={(event) => { setDatasetFile(event.target.files?.[0] || null); setError('') }} />
              <span className="upload-symbol"><Database size={17} /></span>
              <span className="upload-copy"><strong>{datasetFile ? datasetFile.name : 'Choose a dataset file'}</strong><small>{datasetFile ? `${(datasetFile.size / (1024 * 1024)).toFixed(2)} MB` : 'Select a file from your device'}</small></span>
              <span className="button button-subtle">Browse</span>
            </label>
            <p className="format-hint"><strong>Recommended:</strong> {selectedWorkflow.format}</p>
            {api.isPreviewMode && <p className="preview-upload-note">Preview mode does not transmit the selected file.</p>}
          </>}

          <label className="field-label" htmlFor="technique">Technique</label>
          <select id="technique" value={technique} onChange={(event) => setTechnique(event.target.value)}>{selectedWorkflow.techniques.map((option) => <option key={option} value={option}>{option}</option>)}</select>

          <section className="estimate-panel" aria-live="polite">
            <div className="estimate-top"><span className="estimate-icon"><Activity size={17} /></span><span><strong>Estimated time</strong><small>{api.isPreviewMode ? 'Illustrative preview' : 'Based on current hardware'}</small></span><span className="estimate-value">{estimateState === 'loading' ? 'Updating…' : estimateState === 'ready' ? `${formatDuration(estimate.minSeconds)}–${formatDuration(estimate.maxSeconds)}` : '—'}</span></div>
            <div className="estimate-hardware"><Cpu size={14} /><span>{hardware?.gpu || hardware?.gpuName || hardware?.device || (api.isPreviewMode ? 'Sample hardware profile' : 'Hardware profile unavailable')}</span><span>{hardware?.vram || hardware?.gpuMemory || hardware?.memory || ''}</span></div>
            {hardwareError && <p className="estimate-note" role="status">Could not read hardware profile: {hardwareError}</p>}
            {estimateState !== 'ready' && estimateState !== 'loading' && estimateState !== 'idle' && <p className="field-error" role="alert">Estimate unavailable: {estimateState}</p>}
            {estimate?.assumptions?.length > 0 && <p className="estimate-note">{estimate.assumptions[0]}</p>}
          </section>

          {error && <p className="field-error" role="alert">{error}</p>}
          <div className="dialog-actions"><button type="button" className="button button-subtle" onClick={onClose} disabled={submitting}>Cancel</button><button type="submit" className="button button-primary" disabled={submitting || modelLoading || !selectedModel || (workflow !== 'quantization' && !datasetFile)}><Plus size={16} /> {submitting ? 'Submitting…' : 'Create project'}</button></div>
        </form>
      </section>
    </div>
  )
}

function ProjectList({ projects, onCreate }) {
  return (
    <>
      <PageHeading title="Projects" description="A focused home for each fine-tuning goal." onCreate={onCreate} />
      {projects.length ? <div className="project-grid">{projects.map((project, index) => (
        <article className="project-card" key={project.id}>
          <div className={`project-symbol symbol-${index % 4}`}><Box size={20} /></div>
          <div className="project-card-title"><h2>{project.name}</h2></div>
          <p>{project.description || 'No description added.'}</p>
          <div className="project-card-meta"><span>{project.model || 'No model selected'}</span><span>{project.runCount} runs</span></div>
          <div className="project-card-foot"><Status tone={project.lastRunStatus === 'Passed' ? 'success' : 'neutral'}>{project.lastRunStatus || 'Draft'}</Status><span>{project.updatedLabel}</span></div>
        </article>
      ))}</div> : <div className="empty-state"><Box size={25} /><h2>No projects yet</h2><p>Create a project to keep your fine-tuning work together.</p><button className="button button-primary" onClick={onCreate}><Plus size={16} /> Create project</button></div>}
    </>
  )
}

function DataTable({ rows, columns, emptyLabel }) {
  if (!rows.length) return <div className="empty-table">{emptyLabel}</div>
  return <div className="table-wrap"><table><thead><tr>{columns.map((column) => <th key={column.key}>{column.label}</th>)}</tr></thead><tbody>{rows.map((row) => <tr key={row.id}>{columns.map((column) => <td key={column.key}>{column.render ? column.render(row) : row[column.key]}</td>)}</tr>)}</tbody></table></div>
}

function Overview({ workspace }) {
  const { runs, datasets, machine } = workspace
  return (
    <div className="overview-grid">
      <section className="content-panel recent-panel">
        <div className="section-heading"><div><span className="section-index">ACTIVITY</span><h2>Recent runs</h2></div><button className="text-link" onClick={() => window.dispatchEvent(new CustomEvent('navigate', { detail: 'runs' }))}>All runs <ArrowUpRight size={15} /></button></div>
        <DataTable rows={runs.slice(0, 5)} emptyLabel="No runs yet." columns={[
          { key: 'name', label: 'RUN', render: (row) => <div className="run-name"><span className="run-marker" /><span><strong>{row.name}</strong><small>{row.project}</small></span></div> },
          { key: 'model', label: 'BASE MODEL' },
          { key: 'method', label: 'METHOD' },
          { key: 'status', label: 'STATUS', render: (row) => <Status tone={row.tone}>{row.status}</Status> },
        ]} />
      </section>
      <aside className="side-stack">
        <section className="machine-panel">
          <div className="section-heading compact"><div><span className="section-index">HARDWARE</span><h2>Machine profile</h2></div></div>
          <div className="machine-name"><span className="machine-icon"><Cpu size={18} /></span><span><strong>{machine.gpu}</strong><small>{machine.runtime}</small></span></div>
          <div className="resource-line"><div><span><Cpu size={14} /> VRAM</span><strong>{machine.vram}</strong></div><div className="meter"><i style={{ width: machine.vramUsage }} /></div></div>
          <div className="resource-line"><div><span><HardDrive size={14} /> Storage free</span><strong>{machine.storage}</strong></div><div className="meter meter-green"><i style={{ width: machine.storageUsage }} /></div></div>
          <p className="machine-foot">{api.isPreviewMode || workspace.previewOnly ? 'Sample hardware profile' : 'Reported by Python API'}</p>
        </section>
        <section className="dataset-panel">
          <div className="section-heading compact"><div><span className="section-index">DATASETS</span><h2>Latest dataset</h2></div></div>
          <div className="dataset-row"><span className="file-icon"><Database size={17} /></span><span className="dataset-name"><strong>{datasets[0]?.name || 'No datasets added'}</strong><small>{datasets[0]?.detail || 'No dataset details'}</small></span><Status tone={datasets[0]?.status === 'Validated' ? 'success' : 'warning'}>{datasets[0]?.status || 'Empty'}</Status></div>
          {datasets[0]?.status === 'Validated' && <div className="validation-note"><Check size={14} /> Validated <span>{datasets[0].rows} rows</span></div>}
        </section>
      </aside>
    </div>
  )
}

function EvaluationPage({ workspace }) {
  const trainedRuns = workspace.runs.filter((run) => ['passed', 'warning', 'completed', 'complete', 'succeeded', 'success'].includes(run.status?.toLowerCase()))
  const evaluationDatasets = workspace.datasets.filter((dataset) => dataset.status === 'Validated' && ['evaluation', 'validation', 'test', 'held-out', 'held_out'].includes((dataset.role || dataset.split || '').toLowerCase()))
  const [runId, setRunId] = useState(trainedRuns[0]?.id || '')
  const [datasetId, setDatasetId] = useState(evaluationDatasets[0]?.id || '')
  const [evaluation, setEvaluation] = useState(null)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState('')
  const pending = evaluation && ['queued', 'preparing', 'running', 'evaluating'].includes(evaluation.status?.toLowerCase())

  useEffect(() => {
    if (!pending || !evaluation?.id) return undefined
    let current = true
    let timeout
    async function refresh() {
      try {
        const result = await api.getEvaluation(evaluation.id)
        if (!current) return
        setEvaluation(result)
        if (['queued', 'preparing', 'running', 'evaluating'].includes(result.status?.toLowerCase())) {
          timeout = window.setTimeout(refresh, 1500)
        }
      } catch (requestError) {
        if (current) {
          setError(requestError.message)
          setEvaluation((previous) => ({ ...previous, status: 'failed', message: requestError.message }))
        }
      }
    }
    timeout = window.setTimeout(refresh, 1000)
    return () => {
      current = false
      window.clearTimeout(timeout)
    }
  }, [evaluation?.id, evaluation?.status, pending])

  async function submit(event) {
    event.preventDefault()
    if (!runId || !datasetId) return
    setStarting(true)
    setError('')
    setEvaluation(null)
    try {
      const result = await api.startEvaluation({ runId, datasetId })
      setEvaluation(result)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setStarting(false)
    }
  }

  const completed = evaluation && ['completed', 'complete', 'passed', 'succeeded'].includes(evaluation.status?.toLowerCase())
  const failed = evaluation && ['failed', 'error'].includes(evaluation.status?.toLowerCase())

  return (
    <>
      <PageHeading title="Evaluation" description="Measure a trained model on a held-out dataset." />
      <div className="evaluation-layout">
        <section className="content-panel evaluation-setup">
          <div className="section-heading"><div><span className="section-index">NEW EVALUATION</span><h2>Choose model and dataset</h2></div></div>
          <form onSubmit={submit}>
            <label className="field-label" htmlFor="evaluation-run">Trained model</label>
            <select id="evaluation-run" value={runId} onChange={(event) => { setRunId(event.target.value); setEvaluation(null) }} disabled={!trainedRuns.length}>
              {!trainedRuns.length && <option value="">No completed training runs</option>}
              {trainedRuns.map((run) => <option key={run.id} value={run.id}>{run.name} · {run.model}</option>)}
            </select>
            <label className="field-label" htmlFor="evaluation-dataset">Evaluation dataset</label>
            <select id="evaluation-dataset" value={datasetId} onChange={(event) => { setDatasetId(event.target.value); setEvaluation(null) }} disabled={!evaluationDatasets.length}>
              {!evaluationDatasets.length && <option value="">No held-out datasets available</option>}
              {evaluationDatasets.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name} · {dataset.rows} rows</option>)}
            </select>
            <p className="evaluation-hint">Use a validation or test split that was not used during training.</p>
            {api.isPreviewMode && <p className="preview-upload-note">Preview results are sample metrics, not model inference.</p>}
            {error && <p className="field-error" role="alert">{error}</p>}
            <button className="button button-primary" type="submit" disabled={starting || pending || !runId || !datasetId || !evaluationDatasets.length}>
              <FlaskConical size={16} /> {starting ? 'Starting…' : pending ? 'Evaluating…' : 'Run evaluation'}
            </button>
            {!trainedRuns.length && <p className="empty-hint">A completed training run is required.</p>}
            {!evaluationDatasets.length && <p className="empty-hint">Mark a validated dataset as an evaluation split to use it here.</p>}
          </form>
        </section>
        <section className="content-panel evaluation-results" aria-live="polite">
          <div className="section-heading"><div><span className="section-index">RESULTS</span><h2>{completed ? 'Evaluation metrics' : pending ? 'Evaluation in progress' : failed ? 'Evaluation failed' : 'No results yet'}</h2></div>{completed && <Status tone="success">Complete</Status>}</div>
          {pending && <div className="evaluation-progress"><span className="loading-mark"><FlaskConical size={20} /></span><p>Evaluation is running. Results will appear here when the backend finishes.</p></div>}
          {completed && <>
            <div className="evaluation-context"><span><strong>Model</strong>{evaluation.modelName || trainedRuns.find((run) => run.id === runId)?.model}</span><span><strong>Dataset</strong>{evaluation.datasetName || evaluationDatasets.find((dataset) => dataset.id === datasetId)?.name}</span><span><strong>Samples</strong>{evaluation.samplesEvaluated ?? evaluation.sampleCount ?? '—'}</span></div>
            <div className="metric-grid">{(evaluation.metrics || []).map((metric) => <article className="metric-card" key={metric.name || metric.key}><span>{metric.name || metric.label || metric.key}</span><strong>{metric.formatted ?? (typeof metric.value === 'number' ? metric.value.toFixed(3) : metric.value ?? '—')}</strong>{metric.direction && <small>{metric.direction === 'lower' ? 'Lower is better' : 'Higher is better'}</small>}</article>)}</div>
            {!evaluation.metrics?.length && <div className="empty-hint">The evaluator returned no metrics.</div>}
            {evaluation.previewOnly && <p className="preview-upload-note">Illustrative preview metrics</p>}
          </>}
          {failed && <p className="evaluation-failure">{evaluation.message || 'The evaluation job failed. Check the run logs and try again.'}</p>}
          {!evaluation && !pending && !error && <p className="evaluation-placeholder">Select a trained model and held-out dataset, then run an evaluation.</p>}
        </section>
      </div>
    </>
  )
}

function App() {
  const [activePage, setActivePage] = useState('overview')
  const [workspace, setWorkspace] = useState(null)
  const [loadError, setLoadError] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [backendStatus, setBackendStatus] = useState(api.isPreviewMode ? 'preview' : 'checking')

  useEffect(() => {
    if (api.isPreviewMode) return undefined
    let current = true
    api.checkHealth().then((result) => {
      if (current) setBackendStatus(result.status === 'ok' ? 'connected' : 'offline')
    }).catch(() => {
      if (current) setBackendStatus('offline')
    })
    return () => { current = false }
  }, [])

  useEffect(() => {
    let current = true
    api.getWorkspace().then((data) => {
      if (current) setWorkspace(data)
    }).catch(() => {
      if (current) setLoadError(true)
    })
    return () => { current = false }
  }, [])

  useEffect(() => {
    function handleNavigate(event) { setActivePage(event.detail) }
    window.addEventListener('navigate', handleNavigate)
    return () => window.removeEventListener('navigate', handleNavigate)
  }, [])

  async function createProject(projectDetails) {
    const project = await api.createProject(projectDetails)
    const savedProject = {
      ...project,
      model: project.model || project.modelName || projectDetails.modelName,
      runCount: project.runCount ?? 0,
      lastRunStatus: project.lastRunStatus || 'Draft',
      updatedLabel: project.updatedLabel || 'Created just now',
    }
    setWorkspace((current) => ({ ...current, projects: [savedProject, ...current.projects] }))
    setDialogOpen(false)
    setActivePage('projects')
  }

  const [title, description] = pageDetails[activePage]

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileMenuOpen ? 'sidebar-open' : ''}`}>
        <a className="brand" href="#overview" onClick={(event) => { event.preventDefault(); setActivePage('overview') }}><span className="brand-mark"><Cpu size={18} /></span><span>Local<span className="brand-light">Foundry</span><small>MODEL WORKSPACE</small></span></a>
        <div className="nav-label">WORKSPACE</div>
        <nav aria-label="Main navigation">{navigation.map(({ id, label, icon: Icon }) => <button key={id} className={`nav-item ${activePage === id ? 'nav-active' : ''}`} onClick={() => { setActivePage(id); setMobileMenuOpen(false) }}><Icon size={17} strokeWidth={1.8} /><span>{label}</span>{id === 'runs' && workspace?.runs.some((run) => run.status === 'Training') && <i className="nav-notice" />}</button>)}</nav>
        <div className="sidebar-bottom"><div className={`sidebar-mode connection-${backendStatus}`}><i />{backendStatus === 'preview' ? 'Preview data' : backendStatus === 'checking' ? 'Checking Python API' : backendStatus === 'connected' ? 'Python API connected' : 'Python API unreachable'}</div></div>
      </aside>
      {mobileMenuOpen && <button className="mobile-scrim" aria-label="Close navigation" onClick={() => setMobileMenuOpen(false)} />}
      <main className="main-area">
        <header className="topbar"><button className="menu-toggle icon-button" aria-label="Open navigation" onClick={() => setMobileMenuOpen(true)}><Menu size={19} /></button><div className="breadcrumbs"><span>Workspace</span><span>/</span><strong>{title}</strong></div><span className={`connection-label connection-${backendStatus}`}><i />{backendStatus === 'preview' ? 'Preview data' : backendStatus === 'checking' ? 'Checking API' : backendStatus === 'connected' ? 'API connected' : 'API unreachable'}</span></header>
        <div className="page-content">
          {loadError && <div className="error-banner" role="alert">Workspace preview could not be loaded. Refresh the page to try again.</div>}
          {!workspace && !loadError ? <div className="loading-state"><span className="loading-mark"><Cpu size={23} /></span><p>Preparing your workspace</p></div> : workspace && activePage === 'overview' ? <><PageHeading title={title} description={description} onCreate={() => setDialogOpen(true)} /><Overview workspace={workspace} /></> : workspace && activePage === 'projects' ? <ProjectList projects={workspace.projects} onCreate={() => setDialogOpen(true)} /> : workspace && activePage === 'datasets' ? <><PageHeading title={title} description={description} /><section className="content-panel list-panel"><div className="section-heading"><div><span className="section-index">DATASETS</span><h2>Dataset library</h2></div></div><DataTable rows={workspace.datasets} emptyLabel="No datasets available." columns={[{ key: 'name', label: 'DATASET', render: (row) => <div className="run-name"><span className="file-icon"><Database size={16} /></span><span><strong>{row.name}</strong><small>{row.detail}</small></span></div> }, { key: 'format', label: 'FORMAT' }, { key: 'rows', label: 'ROWS' }, { key: 'status', label: 'VALIDATION', render: (row) => <Status tone={row.status === 'Validated' ? 'success' : 'warning'}>{row.status}</Status> }]}/></section></> : workspace && activePage === 'runs' ? <><PageHeading title={title} description={description} /><section className="content-panel list-panel"><div className="section-heading"><div><span className="section-index">RUN HISTORY</span><h2>Training runs</h2></div></div><DataTable rows={workspace.runs} emptyLabel="No training runs yet." columns={[{ key: 'name', label: 'RUN', render: (row) => <div className="run-name"><span className="run-marker" /><span><strong>{row.name}</strong><small>{row.project}</small></span></div> }, { key: 'model', label: 'BASE MODEL' }, { key: 'method', label: 'METHOD' }, { key: 'updated', label: 'UPDATED' }, { key: 'status', label: 'STATUS', render: (row) => <Status tone={row.tone}>{row.status}</Status> }]}/></section></> : workspace && activePage === 'models' ? <><PageHeading title={title} description={description} /><div className="model-grid">{workspace.models.map((model) => <article className="model-card" key={model.id}><div className="model-card-top"><span className="model-symbol"><Cpu size={19} /></span><Status tone={model.tone}>{model.capability}</Status></div><span className="section-index">{model.family}</span><h2>{model.name}</h2><p>{model.description}</p><div className="model-specs"><span><small>PARAMETERS</small><strong>{model.parameters}</strong></span><span><small>CONTEXT</small><strong>{model.context}</strong></span><span><small>DOWNLOAD</small><strong>{model.download}</strong></span></div><div className="model-card-foot"><span>{model.methods}</span></div></article>)}</div></> : null}
          {workspace && activePage === 'evaluation' && <EvaluationPage workspace={workspace} />}
        </div>
      </main>
      {dialogOpen && <ProjectDialog onClose={() => setDialogOpen(false)} onCreate={createProject} />}
    </div>
  )
}

export default App