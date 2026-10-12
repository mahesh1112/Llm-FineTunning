from datasets import load_dataset
from transformers import AutoTokenizer
from transformers import AutoModelForCausalLM
from peft import LoraConfig
from trl import SFTTrainer
from transformers import TrainingArguments

model_name = "Qwen/Qwen2.5-0.5B-Instruct"

dataset = load_dataset(
    "json",
    data_files="data/train.jsonl",
    split="train"
)

tokenizer = AutoTokenizer.from_pretrained(model_name)

tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_name
)

def formatting_func(example):

    return (
        f"Instruction: {example['instruction']}\n"
        f"Input: {example['input']}\n"
        f"Answer: {example['output']}"
    )

peft_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules="all-linear",
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

training_args = TrainingArguments(

    output_dir="outputs",

    per_device_train_batch_size=1,

    gradient_accumulation_steps=4,

    num_train_epochs=5,

    learning_rate=2e-4,

    logging_steps=1,

    save_strategy="epoch",

    bf16=False,

    fp16=True

)

trainer = SFTTrainer(

    model=model,

    train_dataset=dataset,

    formatting_func=formatting_func,

    peft_config=peft_config,

    args=training_args

)

trainer.train() 

trainer.save_model("outputs/final")