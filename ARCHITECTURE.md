# Architecture: React + GitHub Pages + Google Colab GPU for LLM Fine-Tuning

## 1. Goal

Build a web application where a user configures an LLM fine-tuning job
in a React UI hosted on GitHub Pages. Python training code runs on a
Google Colab GPU. The user should not have to edit Python code.

## 2. Important feasibility constraint

**GitHub Pages cannot start or control a new Google Colab GPU runtime
through a supported, general-purpose public HTTP API.** Colab is an
interactive notebook service, not a serverless Python API or a
persistent job server.

Therefore, a website button cannot reliably start a completely new Colab
runtime and run training from a cold start with no Colab interaction at
all using a simple `fetch()` call.

If Colab GPU is a strict requirement, the supported practical baseline
is that the user authorizes and starts the Colab notebook/runtime at
least once. Once a runtime is active, additional integration can submit
jobs to it, but this is a more fragile setup: runtimes disconnect,
sessions expire, quotas vary, and a temporary runtime URL is not a
stable backend endpoint.

Do not build around scraping Colab's private UI endpoints, storing
Google passwords/cookies, or exposing an unauthenticated notebook
runtime to the internet.

## 3. Target architecture

``` text
                         USER'S BROWSER
┌──────────────────────────────────────────────────────────────┐
│ React UI hosted on GitHub Pages                              │
│                                                              │
│ Model / dataset / LoRA settings / Start button / progress UI │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              │ Job configuration
                              ▼
                  Authenticated job bridge
                  available only while the
                  Colab runtime is connected
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ Google Colab runtime                                         │
│                                                              │
│ Notebook bootstrap → clone/pull GitHub repo → install deps   │
│                  → validate job config → run Python trainer  │
│                                                              │
│ Python / PyTorch / Transformers / PEFT / LoRA or QLoRA       │
│                              │                               │
│                              ▼                               │
│                         Colab GPU                            │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
                Save adapter, metrics and logs
                to persistent storage (e.g. Drive
                or user-selected storage)
```

The job bridge is a design component, not a built-in Colab endpoint. It
must be implemented and secured if you want the React page to
communicate with an already-running notebook. It does not remove the
requirement to start the Colab runtime.

## 4. Repository layout

``` text
llm-trainer/
├── frontend/                 # React app deployed to GitHub Pages
├── training/
│   ├── train.py              # Main Python training entry point
│   ├── dataset.py            # Dataset loading and validation
│   ├── model.py              # Model/tokenizer loading
│   ├── config.py             # Training configuration validation
│   ├── evaluate.py           # Optional evaluation
│   └── requirements.txt      # Python dependencies
├── colab/
│   └── train.ipynb           # Colab bootstrap notebook
└── docs/
    └── ARCHITECTURE.md
```

Keep the training logic in normal Python modules so it can be tested
independently from the notebook. The notebook should be a thin bootstrap
layer rather than the place where all training logic lives.

## 5. Training request lifecycle

1.  The user selects a supported model, uploads or selects a dataset,
    and configures LoRA/QLoRA parameters in React.
2.  The frontend validates fields and creates a job configuration.
3.  The frontend checks whether an authorized Colab runtime is
    connected. If not, show a clear message that Colab must be started
    and authorized; do not show fake progress.
4.  When the runtime is connected, the bridge sends the validated job
    configuration to the notebook runtime.
5.  Python validates the configuration again, downloads/loads the model
    and dataset, checks available GPU memory, and starts training.
6.  Training logs and metrics are returned to the UI through the bridge
    while the runtime remains available.
7.  Save checkpoints, adapter weights, logs, and final metrics to
    persistent storage. Colab's runtime disk is temporary and must not
    be treated as durable storage.
8.  If the runtime disconnects, mark the job as interrupted or unknown,
    and allow recovery only from a checkpoint that was actually saved.

## 6. Job configuration example

The frontend should send structured configuration rather than arbitrary
Python source code.

``` json
{
  "model_id": "org-or-user/model-name",
  "dataset_reference": "user-selected-dataset",
  "method": "qlora",
  "epochs": 3,
  "batch_size": 1,
  "gradient_accumulation_steps": 8,
  "learning_rate": 0.0002,
  "max_seq_length": 1024
}
```

This is an illustrative schema. Validate model IDs, dataset references,
numeric ranges, and supported methods on the Python side before
training. Do not accept arbitrary shell commands or Python code from the
browser.

## 7. Security requirements

-   Never place Google credentials, access tokens, Hugging Face tokens,
    or other secrets in the React bundle or public GitHub repository.
-   Authenticate and authorize every job request.
-   Do not expose a notebook runtime or tunnel to the public internet
    without strong authentication and request validation.
-   Apply strict limits to model IDs, dataset size, epochs, sequence
    length, and other resource-intensive parameters.
-   Treat uploaded datasets and model metadata as untrusted input.
-   Do not use browser-supplied paths as unrestricted filesystem paths.
-   Avoid private or undocumented Colab endpoints and browser-cookie
    reuse.

## 8. GPU and session constraints

-   GPU type and availability depend on the Colab plan and current
    capacity; do not promise a particular GPU.
-   Free-tier sessions can be limited, interrupted, or disconnected, and
    usage limits can change.
-   Large models may not fit in the available GPU memory. Check GPU
    memory before training and provide actionable errors.
-   Save checkpoints periodically to persistent storage if recovery is
    required.
-   Installing dependencies and downloading model weights can take
    significant time.

## 9. Implementation milestones

### Milestone 1 --- Make training work in Colab

-   Add `training/requirements.txt`.
-   Make `training/train.py` accept a configuration file or command-line
    arguments.
-   Create `colab/train.ipynb` to install dependencies, obtain the
    repository, verify `torch.cuda.is_available()`, and run a test job.
-   Save output artifacts to persistent storage.

### Milestone 2 --- Build the React training UI

-   Add model, dataset, method, and hyperparameter controls.
-   Add form validation and explicit job states: `idle`, `connecting`,
    `queued`, `running`, `completed`, `failed`, and `interrupted`.
-   Do not claim that a job has started until the runtime confirms it.

### Milestone 3 --- Decide how the UI connects to Colab

-   For a reliable, fully automatic click-to-train experience, a stable
    authenticated job API and managed execution environment are normally
    required.
-   Colab does not provide a supported general-purpose API for a GitHub
    Pages app to cold-start a GPU runtime and run a notebook without
    user interaction.
-   If Colab must remain the only compute environment, accept the
    notebook/runtime startup requirement and only automate job
    submission after a runtime is connected.
-   Do not promise end-to-end automatic startup until the runtime
    connection and authentication design has been proven in a prototype.

## 10. Acceptance criteria

-   [ ] React app remains deployable as a static GitHub Pages site.
-   [ ] Python training code lives in version control and runs in Colab.
-   [ ] The notebook verifies GPU availability before training.
-   [ ] The UI clearly distinguishes an unavailable runtime from an
    active training job.
-   [ ] Job configuration is validated on both frontend and Python
    sides.
-   [ ] Training logs and actual status are shown; no simulated success
    states.
-   [ ] Artifacts and checkpoints are saved outside the temporary Colab
    runtime disk.
-   [ ] Secrets are not committed to GitHub or embedded in frontend
    assets.
-   [ ] The documentation clearly states that a completely cold-start,
    zero-interaction Colab launch is not a supported assumption.

## Final recommendation

Keep React on GitHub Pages and the training code in GitHub, and use
Colab as the GPU execution environment. First prove that the Python
training script runs successfully in a Colab notebook. Then prototype
the authenticated bridge to an already-running runtime.

**Important:** the exact requirement "click Train on GitHub Pages and
Colab automatically starts from cold with no manual notebook
interaction" cannot be guaranteed with Colab alone through a supported
public API. Resolve that constraint before building the frontend around
it.
