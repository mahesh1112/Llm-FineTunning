from transformers import AutoTokenizer
from transformers import AutoModelForCausalLM
from peft import PeftModel

base_model = "Qwen/Qwen2.5-0.5B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(base_model)

model = AutoModelForCausalLM.from_pretrained(base_model)

model = PeftModel.from_pretrained(
    model,
    "outputs/final"
)

prompt = "Instruction: What is AI?\nInput:\nAnswer:"

inputs = tokenizer(
    prompt,
    return_tensors="pt"
)

output = model.generate(
    **inputs,
    max_new_tokens=100
)

print(
    tokenizer.decode(
        output[0],
        skip_special_tokens=True
    )
)