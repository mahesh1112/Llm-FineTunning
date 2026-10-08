export const initialWorkspace = {
  projects: [
    { id: 'project-support', name: 'Support copilot', description: 'A helpful first-line assistant for product support.', model: 'Qwen2.5 1.5B', runCount: 4, lastRunStatus: 'Passed', updatedLabel: 'Updated 2h ago' },
    { id: 'project-docs', name: 'Documentation Q&A', description: 'Grounded answers from internal product guides.', model: 'Llama 3.2 3B', runCount: 2, lastRunStatus: 'In review', updatedLabel: 'Updated yesterday' },
    { id: 'project-classifier', name: 'Ticket triage', description: 'Consistent intent and priority classification.', model: 'Qwen2.5 0.5B', runCount: 1, lastRunStatus: 'Draft', updatedLabel: 'Updated Oct 4' },
  ],
  runs: [
    { id: 'run-104', name: 'Support tone v3', project: 'Support copilot', model: 'Qwen2.5 1.5B', method: 'LoRA SFT', status: 'Passed', tone: 'success', updated: 'Today, 10:42' },
    { id: 'run-103', name: 'Docs retrieval baseline', project: 'Documentation Q&A', model: 'Llama 3.2 3B', method: 'LoRA SFT', status: 'Evaluating', tone: 'running', updated: 'Today, 09:16' },
    { id: 'run-102', name: 'Intent labels v1', project: 'Ticket triage', model: 'Qwen2.5 0.5B', method: 'LoRA SFT', status: 'Warning', tone: 'warning', updated: 'Yesterday' },
    { id: 'run-101', name: 'Support tone v2', project: 'Support copilot', model: 'Qwen2.5 1.5B', method: 'LoRA SFT', status: 'Failed', tone: 'danger', updated: 'Oct 5' },
  ],
  datasets: [
    { id: 'dataset-support', name: 'support_conversations_v3.jsonl', detail: '4.8 MB · Fingerprint 7c91…e2a4', format: 'JSONL', rows: '2,480', status: 'Validated' },
    { id: 'dataset-docs', name: 'product_guides.txt', detail: '1.2 MB · Fingerprint 3fa1…cb08', format: 'Plain text', rows: '—', status: 'Validated' },
    { id: 'dataset-intent', name: 'ticket_intents.jsonl', detail: '860 KB · 3 validation notes', format: 'JSONL', rows: '1,120', status: 'Warnings' },
  ],
  machine: { gpu: 'NVIDIA GeForce RTX 4060', runtime: 'CUDA 12.4 · PyTorch 2.6', vram: '6.2 / 8 GB', vramUsage: '68%', storage: '184 GB', storageUsage: '72%' },
  lastEvaluation: '82.4%',
  models: [
    { id: 'qwen-15', family: 'QWEN FAMILY', name: 'Qwen2.5 1.5B Instruct', description: 'Compact instruction model suited to local experimentation and focused assistants.', parameters: '1.5B', context: '32K', download: '3.1 GB', methods: 'LoRA SFT · Continued pretraining', capability: 'Supported', tone: 'success' },
    { id: 'llama-3b', family: 'LLAMA FAMILY', name: 'Llama 3.2 3B Instruct', description: 'A capable small language model for summarization and general assistant tasks.', parameters: '3B', context: '128K', download: '6.4 GB', methods: 'LoRA SFT', capability: 'Constrained', tone: 'warning' },
    { id: 'qwen-05', family: 'QWEN FAMILY', name: 'Qwen2.5 0.5B Instruct', description: 'Fast, low-resource model for lightweight classification and prototyping.', parameters: '0.5B', context: '32K', download: '1.1 GB', methods: 'LoRA SFT · Continued pretraining', capability: 'Supported', tone: 'success' },
  ],
}