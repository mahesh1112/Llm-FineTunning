# Frontend Implementation Plan

This plan describes how to build the React frontend for the local LLM fine-tuning platform. It is written for someone who is new to React, so each phase explains the React idea being used, the user-visible feature to build, the files involved, and the code responsibilities.

The implementation should be completed in the order below. Each phase should leave the application running and testable before the next phase begins.

## 1. Understand the Frontend's Job

The frontend is a browser interface for a local fine-tuning application. It should help a user:

1. Create or open a project.
2. Inspect the local machine and available models.
3. Add and validate a dataset.
4. Configure a training method such as LoRA.
5. Review preflight warnings before starting.
6. Start a run and watch its progress and logs.
7. Review evaluation metrics and sample outputs.
8. Export, compare, or delete generated artifacts.

The frontend does not train models itself. It calls a future local control API. During UI development, a mock API with realistic data should be used so that every screen can be built before the backend is complete.

### React concepts to learn first

- A component is a reusable JavaScript function that returns JSX, which looks like HTML.
- Props are values passed from a parent component to a child component.
- State is data that can change while the user interacts with the page. Use `useState` for local state.
- An effect is work that happens after rendering, such as loading data. Use `useEffect` only for external work such as an API call.
- Events such as `onClick` and `onChange` respond to user actions.
- A controlled form input gets its value from React state and updates state in its `onChange` handler.
- Conditional rendering uses JavaScript expressions such as `{isLoading && <Spinner />}`.
- Lists use `.map()` and require a stable `key` for each item.

Do not put all application logic in `App.jsx`. `App.jsx` should eventually assemble the shell and route-like views; individual components and service modules should own their local responsibilities.

## 2. Confirm the Starting Project and Install UI Dependencies

The `frontend` folder already contains a React 19 and Vite application. Tailwind CSS 4 and `@tailwindcss/vite` are already listed in `package.json`, but the Vite plugin and CSS entry still need to be configured.

### Files to modify

#### `frontend/package.json`

Keep the existing scripts and dependencies. Add these UI dependencies:

```json
{
  "dependencies": {
    "lucide-react": "latest",
    "react": "^19.2.8",
    "react-dom": "^19.2.8",
    "react-router-dom": "latest"
  }
}
```

Run `npm install` after changing the file. `lucide-react` provides accessible interface icons. `react-router-dom` provides browser navigation without manually checking `window.location`.

#### `frontend/vite.config.js`

Configure Tailwind alongside the React plugin:

```js
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
})
```

#### `frontend/index.html`

Change the document title to `Local LLM Studio`. Keep the `root` element because React mounts into it.

### First validation

Run:

```powershell
npm run lint
npm run build
```

The empty scaffold must pass before application work begins.

## 3. Create the Frontend Folder Structure

Create the following files and directories as features require them. Do not create empty files just to match the tree.

```text
frontend/
  src/
    app/
      AppShell.jsx
      routes.jsx
    components/
      ui/
      layout/
      feedback/
      forms/
      data-display/
    features/
      dashboard/
      projects/
      datasets/
      models/
      training/
      runs/
      evaluation/
      artifacts/
      settings/
    hooks/
    lib/
      api.js
      formatters.js
      validators.js
    mocks/
      mockData.js
      mockApi.js
    styles/
      tokens.css
      globals.css
    App.jsx
    main.jsx
```

Purpose of the main areas:

- `app`: application shell and URL-to-screen mapping.
- `components/ui`: small reusable controls such as buttons, badges, inputs, tabs, dialogs, and progress bars.
- `components/layout`: navigation, page header, content regions, and responsive layout.
- `components/feedback`: loading, empty, error, and confirmation states.
- `components/forms`: shared form field wrappers and validation messages.
- `components/data-display`: tables, metric cards, status badges, and log viewers.
- `features`: components and state that belong to one product area.
- `hooks`: reusable React hooks for fetching, polling, and form state.
- `lib`: framework-independent functions that are easy to test.
- `mocks`: temporary local API behavior used before the backend exists.
- `styles`: global design tokens and application-wide CSS.

## 4. Replace the Vite Demo with the Application Shell

Build the navigation and page frame before building individual screens. This gives every later feature a consistent home.

### Files to create

#### `src/app/AppShell.jsx`

This component renders the sidebar, top bar, main content area, and an outlet for the active screen.

```jsx
import { NavLink, Outlet } from 'react-router-dom'
import { Activity, Database, FolderKanban, Gauge, Settings } from 'lucide-react'

const navigation = [
  { to: '/', label: 'Overview', icon: Gauge, end: true },
  { to: '/projects', label: 'Projects', icon: FolderKanban },
  { to: '/datasets', label: 'Datasets', icon: Database },
  { to: '/runs', label: 'Runs', icon: Activity },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export default function AppShell() {
  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <a className="brand" href="/">Local LLM Studio</a>
        <nav>
          {navigation.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end}>
              <Icon size={18} aria-hidden="true" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
```

Use `NavLink` so the active navigation item is styled from route state. Use real buttons for actions and links for navigation. Every icon-only button added later must have an `aria-label` and a tooltip.

#### `src/app/routes.jsx`

Define the screens in one place:

```jsx
import { createBrowserRouter } from 'react-router-dom'
import AppShell from './AppShell'
import DashboardPage from '../features/dashboard/DashboardPage'
import ProjectsPage from '../features/projects/ProjectsPage'
import ProjectPage from '../features/projects/ProjectPage'
import DatasetsPage from '../features/datasets/DatasetsPage'
import RunsPage from '../features/runs/RunsPage'
import RunPage from '../features/runs/RunPage'
import SettingsPage from '../features/settings/SettingsPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'projects', element: <ProjectsPage /> },
      { path: 'projects/:projectId', element: <ProjectPage /> },
      { path: 'datasets', element: <DatasetsPage /> },
      { path: 'runs', element: <RunsPage /> },
      { path: 'runs/:runId', element: <RunPage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },
])
```

#### `src/App.jsx`

Replace the Vite counter with the router provider:

```jsx
import { RouterProvider } from 'react-router-dom'
import { router } from './app/routes'

export default function App() {
  return <RouterProvider router={router} />
}
```

#### `src/main.jsx`

Keep `StrictMode`, but import the new global stylesheet after the router setup:

```jsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import './styles/globals.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

### Files to create for the first visual system

#### `src/styles/tokens.css`

Define named colors, spacing, typography, borders, shadows, and status colors. Use a distinctive but restrained palette rather than default Vite purple. Example:

```css
:root {
  --color-ink: #17211f;
  --color-muted: #66736f;
  --color-paper: #f4f6f1;
  --color-panel: #ffffff;
  --color-line: #dbe2dc;
  --color-accent: #d25b38;
  --color-accent-soft: #f8dfd5;
  --color-success: #237a57;
  --color-warning: #a36b12;
  --color-danger: #b33b48;
  --font-body: 'DM Sans', sans-serif;
  --font-display: 'Space Grotesk', sans-serif;
  --font-mono: 'IBM Plex Mono', monospace;
  --radius-sm: 6px;
  --radius-md: 10px;
  --shadow-panel: 0 12px 32px rgb(23 33 31 / 8%);
}
```

Use a local fallback if the chosen fonts cannot be loaded. Do not use viewport-scaled font sizes.

#### `src/styles/globals.css`

Import Tailwind and tokens, reset the document, and define global focus behavior:

```css
@import 'tailwindcss';
@import './tokens.css';

* { box-sizing: border-box; }
html { background: var(--color-paper); }
body { margin: 0; color: var(--color-ink); font-family: var(--font-body); }
button, input, select, textarea { font: inherit; }
button, a { -webkit-tap-highlight-color: transparent; }
:focus-visible { outline: 3px solid var(--color-accent); outline-offset: 3px; }
```

Delete the Vite demo rules from `src/App.css`, or delete the import once no component uses that file.

## 5. Build Reusable UI Primitives

Create these before feature screens so styling and behavior stay consistent:

- `src/components/ui/Button.jsx`: primary, secondary, ghost, danger, and icon variants; disabled and loading states.
- `src/components/ui/Badge.jsx`: `neutral`, `success`, `warning`, `danger`, and `running` statuses.
- `src/components/ui/Card.jsx`: a simple framed surface for a single repeated item or tool.
- `src/components/ui/ProgressBar.jsx`: determinate progress with an accessible label.
- `src/components/ui/Tabs.jsx`: keyboard-accessible tabs for run detail sections.
- `src/components/ui/Modal.jsx`: dialog with focus-safe close behavior and Escape handling.
- `src/components/forms/FormField.jsx`: label, hint, input, and validation error association.
- `src/components/feedback/LoadingState.jsx`: loading message and spinner.
- `src/components/feedback/EmptyState.jsx`: explanation and one primary next action.
- `src/components/feedback/ErrorState.jsx`: safe error message and retry button.
- `src/components/layout/PageHeader.jsx`: title, description, breadcrumbs, and page actions.

Example `Button.jsx` API:

```jsx
export default function Button({ variant = 'primary', loading = false, children, ...props }) {
  return (
    <button className={`button button-${variant}`} disabled={loading || props.disabled} {...props}>
      {loading ? 'Working...' : children}
    </button>
  )
}
```

Do not use a text-filled rounded rectangle where a familiar icon is sufficient. Use Lucide icons for refresh, delete, download, play, pause, and navigation actions, with accessible labels.

## 6. Add Mock Data and an API Boundary

Build the interface against an API-shaped boundary so replacing mock data with the local control API later does not require rewriting components.

### Files to create

#### `src/mocks/mockData.js`

Define realistic objects for projects, datasets, models, machine capability, runs, metrics, logs, and artifacts. Each object needs stable IDs, timestamps, and statuses.

```js
export const projects = [
  {
    id: 'project-support-bot',
    name: 'Support Bot',
    description: 'Customer support instruction tuning',
    model: 'Qwen/Qwen2.5-1.5B-Instruct',
    lastRunStatus: 'completed',
    updatedAt: '2026-09-18T11:30:00Z',
  },
]
```

#### `src/mocks/mockApi.js`

Export async functions such as `listProjects`, `getProject`, `listDatasets`, `getModels`, `getMachineProfile`, `createProject`, `uploadDataset`, `startRun`, `getRun`, and `getRunLogs`. Add a small delay with `setTimeout` so loading states are exercised. Keep the return shape close to the eventual API response.

#### `src/lib/api.js`

Expose the application API from one module. Initially delegate to `mockApi`; later replace the implementation with `fetch` calls without changing feature components.

```js
import * as mockApi from '../mocks/mockApi'

export const api = {
  listProjects: mockApi.listProjects,
  getProject: mockApi.getProject,
  getModels: mockApi.getModels,
  getMachineProfile: mockApi.getMachineProfile,
  getRun: mockApi.getRun,
}
```

#### `src/hooks/useAsync.js`

Create a small hook returning `{ data, loading, error, reload }`. It should handle cancellation or ignore stale results when a component unmounts. Do not put API calls directly in every page component.

#### `src/hooks/usePolling.js`

Create a polling hook for an active run. It should poll only while the run is in a live state such as `queued`, `preparing`, or `training`, and stop when the run reaches a terminal state.

## 7. Implement the Overview Dashboard

The dashboard is the first usable screen and should answer: what is happening, what needs attention, and how do I start?

### Files to create

- `src/features/dashboard/DashboardPage.jsx`: load projects and recent runs; compose the page.
- `src/features/dashboard/StatStrip.jsx`: show project count, active runs, available disk, and last evaluation result.
- `src/features/dashboard/RecentRuns.jsx`: show recent runs with model, method, status, and updated time.
- `src/features/dashboard/QuickActions.jsx`: links to create a project, add a dataset, and inspect machine readiness.

The page should use `PageHeader`, `Card`, `Badge`, `LoadingState`, `ErrorState`, and `EmptyState`. Every loading, empty, and failed API state must be designed rather than left blank.

Example page structure:

```jsx
export default function DashboardPage() {
  const { data, loading, error, reload } = useAsync(api.getDashboard)

  if (loading) return <LoadingState label="Loading workspace" />
  if (error) return <ErrorState message={error.message} onRetry={reload} />

  return (
    <>
      <PageHeader title="Overview" description="Your local training workspace" />
      <StatStrip stats={data.stats} />
      <div className="dashboard-grid">
        <RecentRuns runs={data.recentRuns} />
        <QuickActions />
      </div>
    </>
  )
}
```

Validate that the dashboard works with populated data, no projects, a delayed response, and a rejected response.

## 8. Implement Projects and Project Creation

Projects are the main organizing unit for datasets, runs, evaluations, and artifacts.

### Files to create

- `src/features/projects/ProjectsPage.jsx`: list projects and provide the create action.
- `src/features/projects/ProjectCard.jsx`: display project name, selected model, last run, and updated time.
- `src/features/projects/CreateProjectModal.jsx`: controlled form for name and description.
- `src/features/projects/ProjectPage.jsx`: project workspace with tabs or links to dataset, training, evaluation, and artifacts.
- `src/lib/validators.js`: pure validation functions such as `validateProjectName` and `validateRequired`.

The create form should keep field values in `useState`, validate on submit, show field-specific messages, disable submit while saving, and redirect to `/projects/:projectId` after success. The project name must be safe for local storage and must not be treated as a file path by the UI.

Use a confirmation dialog before archive or delete actions. Archiving should be visually different from deletion, and the UI must explain that artifacts are preserved when a project is archived.

## 9. Implement Dataset Upload, Preview, and Validation

This is a high-value workflow because invalid data should be caught before a training job starts.

### Files to create

- `src/features/datasets/DatasetsPage.jsx`: dataset list and upload entry point.
- `src/features/datasets/UploadDatasetModal.jsx`: file selection, type selection, and upload progress.
- `src/features/datasets/DatasetCard.jsx`: status, size, row count, fingerprint, and validation summary.
- `src/features/datasets/DatasetDetail.jsx`: preview rows, statistics, schema, and validation issues.
- `src/features/datasets/ValidationIssueList.jsx`: grouped blocking errors and warnings.
- `src/features/datasets/SchemaMappingForm.jsx`: map instruction/input/output or messages fields.

The browser should use `File` metadata and send the file to the local API. It should not parse a huge file entirely into browser memory. The UI should show upload progress, cancellation, retry, supported extensions, and the local storage location returned by the API.

Important states:

- No datasets yet: show an upload action.
- Uploading: show determinate progress.
- Uploaded but validating: show an indeterminate state.
- Valid with warnings: allow continuation while making warnings visible.
- Invalid: disable training until blocking issues are resolved.
- Missing file or deleted file: show a recovery action rather than success.

## 10. Implement Model Catalog and Machine Readiness

The user must understand whether a model can run before configuring training.

### Files to create

- `src/features/models/ModelCatalog.jsx`: searchable allowlisted model list.
- `src/features/models/ModelCard.jsx`: model size, context length, license, methods, and cache status.
- `src/features/models/ModelSelector.jsx`: controlled selection component for the training wizard.
- `src/features/models/MachineReadinessCard.jsx`: CPU, RAM, GPU/VRAM, disk, runtime, and collection time.
- `src/features/models/CapabilityBadge.jsx`: supported, constrained, or unavailable display.
- `src/features/models/ResourceAssumptions.jsx`: expandable explanation of estimator assumptions.

Model data should include model ID, pinned revision, architecture, parameter count, context limit, download size, supported methods, quantization options, license, and compatibility reasons. Never show an unavailable field as zero; display `Unknown` and explain why.

The model selector should filter or clearly label unsupported entries. A user may acknowledge a warning, but a blocking incompatibility must prevent the next step.

## 11. Build the Training Configuration Wizard

Use a step-by-step wizard because the user is configuring a high-cost operation. Keep the simple path focused and place advanced controls behind an explicit section.

### Files to create

- `src/features/training/TrainingWizard.jsx`: owns current step and draft configuration.
- `src/features/training/StepIndicator.jsx`: shows current and completed steps.
- `src/features/training/MethodStep.jsx`: choose LoRA or another enabled method.
- `src/features/training/ModelStep.jsx`: select a compatible model and revision.
- `src/features/training/DatasetStep.jsx`: select a validated dataset and split.
- `src/features/training/ParametersStep.jsx`: epochs/steps, learning rate, sequence length, batch size, and gradient accumulation.
- `src/features/training/AdvancedParameters.jsx`: rank, alpha, dropout, target modules, dtype, and quantization when supported.
- `src/features/training/EstimatePanel.jsx`: estimated duration, memory, disk, confidence, and assumptions.
- `src/features/training/ReviewStep.jsx`: complete configuration summary and acknowledgement checkboxes.
- `src/features/training/trainingDefaults.js`: versioned, safe defaults.
- `src/features/training/trainingSchema.js`: field limits and validation rules.

Keep the draft configuration in the wizard parent and pass values plus event handlers to child steps:

```jsx
const [draft, setDraft] = useState(trainingDefaults)

function updateDraft(changes) {
  setDraft((current) => ({ ...current, ...changes }))
}
```

Do not use a global state library for this draft until there is a demonstrated need. The wizard owns the state while it is open; the API owns persisted runs after submission.

Each change should validate locally and request a new estimate through the API boundary. Debounce estimate requests so typing does not trigger a request for every keystroke. Display the estimate as a range with assumptions, never as an exact promise.

The review step must show the immutable values that will be recorded in the run manifest, including model revision, dataset fingerprint, method, random seed, runtime version if available, and output location.

## 12. Implement Preflight Review and Run Launch

Preflight is the final safety barrier before resource allocation.

### Files to create

- `src/features/training/PreflightPanel.jsx`: displays checks and severity.
- `src/features/training/PreflightIssue.jsx`: one issue with cause and corrective action.
- `src/features/training/LaunchRunButton.jsx`: disabled until blocking checks pass and required acknowledgements exist.
- `src/features/runs/RunStatusBadge.jsx`: consistent lifecycle status display.

Represent a check as:

```js
{
  id: 'gpu-memory',
  severity: 'warning',
  title: 'VRAM headroom is limited',
  message: 'This configuration may require gradient checkpointing.',
  action: 'Reduce sequence length or enable checkpointing.',
}
```

Blocking errors disable launch. Warnings require an explicit acknowledgement and remain visible in the final review. After a successful `startRun` response, navigate to `/runs/:runId` and never claim that training started until the API reports the run state.

## 13. Implement Run Monitoring

Run monitoring is the core operational screen. It should remain useful during slow training and after a process failure.

### Files to create

- `src/features/runs/RunsPage.jsx`: filterable run history.
- `src/features/runs/RunPage.jsx`: live or completed run detail.
- `src/features/runs/RunOverview.jsx`: status, configuration summary, progress, and timestamps.
- `src/features/runs/RunProgress.jsx`: step/epoch progress, elapsed time, and estimated remaining range.
- `src/features/runs/RunLogs.jsx`: sanitized, auto-following log viewer with pause/follow control.
- `src/features/runs/RunConfiguration.jsx`: immutable configuration and manifest metadata.
- `src/features/runs/CheckpointList.jsx`: checkpoints, sizes, timestamps, and resume actions.
- `src/features/runs/RunActions.jsx`: cancel, resume, clone, archive, or export actions by state.

Use `usePolling` for active runs. Preserve the last known data if a poll fails and show a reconnecting banner. Polling must stop when the run is `passed`, `failed`, `warning`, `cancelled`, or `archived`.

The lifecycle shown by the UI should match the backend contract:

`draft -> preflight -> queued -> preparing -> training -> checkpointing -> evaluating -> passed|failed|warning -> exported|archived`

Never infer success from 100% progress alone. Use the persisted run status returned by the API.

## 14. Implement Evaluation Results

Evaluation must separate automated metrics from human judgment and show enough evidence to understand a result.

### Files to create

- `src/features/evaluation/EvaluationPanel.jsx`: evaluation status and summary.
- `src/features/evaluation/MetricCard.jsx`: value, threshold, direction, and pass/warn/fail state.
- `src/features/evaluation/MetricTable.jsx`: all metric definitions and values.
- `src/features/evaluation/SampleComparison.jsx`: prompt, expected answer, and model output.
- `src/features/evaluation/ThresholdLegend.jsx`: explains configurable thresholds.
- `src/features/evaluation/EvaluationManifest.jsx`: dataset fingerprint, seed, runtime, and evaluator version.

Metrics must display their definition, units, threshold, and whether higher or lower is better. Include a clear distinction between `Automated result` and `Human review required`. Avoid presenting a single benchmark score as proof of production readiness.

## 15. Implement Artifact Management and Export

Users need to understand what was produced and where it is stored locally.

### Files to create

- `src/features/artifacts/ArtifactList.jsx`: adapter, merged model, tokenizer, logs, checkpoints, and manifests.
- `src/features/artifacts/ArtifactRow.jsx`: type, size, location, checksum, and availability.
- `src/features/artifacts/ExportDialog.jsx`: explicit export selection and destination confirmation.
- `src/features/artifacts/ArtifactManifest.jsx`: immutable provenance details.

Exports must require an explicit user action and list included files before starting. Missing or moved files must be shown as unavailable, not silently omitted. Add download or reveal-in-folder actions only when the local API reports that the operation is supported.

## 16. Add Settings, Privacy, and Diagnostics

### Files to create

- `src/features/settings/SettingsPage.jsx`: application settings and local workspace information.
- `src/features/settings/StorageSettings.jsx`: project, cache, checkpoint, and export locations.
- `src/features/settings/PrivacySettings.jsx`: retention and deletion controls.
- `src/features/settings/RuntimeSettings.jsx`: API/agent health and runtime versions.
- `src/features/settings/DiagnosticsExport.jsx`: explicit diagnostic bundle selection.
- `src/components/feedback/ConfirmDialog.jsx`: reusable destructive-action confirmation.

Make it clear that datasets and model files stay local by default. Diagnostic exports must show what is included and exclude raw dataset records, credentials, and secrets. Deletion should explain what the operating system may retain outside the application's control.

## 17. Add Responsive Behavior and Accessibility

Do this after the main workflows exist, then revisit each screen.

- Sidebar collapses into a top navigation or drawer on narrow screens.
- Tables become stacked rows or horizontally scrollable regions without clipping content.
- The training wizard remains usable at mobile widths.
- Every form control has a visible label or an accessible name.
- Dialogs trap focus, close with Escape, and return focus to the opening control.
- Status is not communicated by color alone; include text and an icon where useful.
- Live run updates use an appropriate `aria-live` region without reading every log line aloud.
- Keyboard users can reach every action in a logical order.
- Respect `prefers-reduced-motion` for page transitions and animated progress.

Use browser devtools at mobile and desktop widths and test with keyboard navigation before release.

## 18. Replace Mock API Calls with the Local Control API

Only after all screens work with mock data should the mock implementation be replaced.

### Files to modify

#### `src/lib/api.js`

Read the API base URL from an environment variable and wrap `fetch` in one helper:

```js
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.message ?? `Request failed with ${response.status}`)
  }

  return response.status === 204 ? null : response.json()
}
```

Add API functions for projects, models, machine profile, datasets, preflight, runs, logs, evaluation, artifacts, and settings. Keep response normalization in `api.js` or dedicated adapters, not inside presentational components.

#### `frontend/.env.example`

Document the local variable without committing secrets:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

The frontend should display an API health error with a retry action when the local agent is unavailable.

## 19. Testing and Validation Order

Add tests as each feature is finished. The exact test runner can be selected when the backend and frontend testing conventions are finalized, but the test cases below are required.

### Pure function tests

- Project names reject empty values and unsafe path characters.
- Training defaults satisfy the training schema.
- Training parameters reject values outside supported limits.
- Status and metric formatters handle unknown values.
- Resource estimates display ranges and assumptions.

### Component tests

- Buttons expose disabled and loading states.
- Forms display field-level errors and do not submit invalid data.
- Empty, loading, and error states render for every API-backed page.
- Model selection disables incompatible models.
- Preflight blocks launch on errors and requires acknowledgement for warnings.
- Run polling stops at terminal states.
- Destructive actions require confirmation.

### End-to-end workflow tests

1. Create a project.
2. Select a supported model.
3. Upload a valid JSONL dataset.
4. See validation results.
5. Configure LoRA defaults.
6. Review preflight.
7. Start a run.
8. Observe progress and logs.
9. Review evaluation metrics.
10. Inspect and export an artifact.

### Required commands before considering the frontend complete

```powershell
npm run lint
npm run build
npm run dev
```

Also manually verify desktop and mobile layouts, keyboard navigation, browser refresh on nested routes, API failure handling, and no raw dataset content appearing in logs or error messages.

## 20. Final Frontend Completion Checklist

- The Vite starter screen and unused demo assets are removed.
- `App.jsx` only assembles the router provider.
- The app shell has working navigation and responsive layout.
- All pages have loading, empty, error, and success states.
- Mock API calls are isolated behind `src/lib/api.js`.
- Project, dataset, model, training, run, evaluation, artifact, and settings workflows are represented.
- A run cannot launch with blocking preflight errors.
- Active runs poll and stop polling at terminal states.
- Evaluation shows metric definitions and thresholds.
- Export and deletion are explicit and confirmed.
- Local-first privacy behavior is visible in the UI.
- `npm run lint` and `npm run build` pass.
- The frontend has been checked at desktop and mobile widths.