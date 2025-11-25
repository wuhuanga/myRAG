import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import uvicorn

# 1. 配置模型路径 (或者使用 HuggingFace Hub ID)
MODEL_NAME = "Qwen/Qwen3-Reranker-0.6B"

app = FastAPI()

print("正在加载模型到 CPU...")
# 强制使用 CPU
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

# ✅ 修复：设置 padding token (解决 batch size > 1 的错误)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    trust_remote_code=True,
    torch_dtype=torch.float32 # CPU 上建议用 float32
).to("cpu")
model.eval()
print("模型加载完成！")

class RerankRequest(BaseModel):
    model: str = None
    query: str
    documents: list[str]
    top_n: int = None

@app.post("/v1/rerank")
async def rerank(request: RerankRequest):
    if not request.documents:
        return {"results": []}

    # 构造 Pairs
    pairs = [[request.query, doc] for doc in request.documents]

    # 推理
    with torch.no_grad():
        inputs = tokenizer(pairs, padding=True, truncation=True, return_tensors='pt', max_length=512).to("cpu")
        scores = model(**inputs, return_dict=True).logits.view(-1,).float()

    # 格式化输出
    results = []
    for i, score in enumerate(scores):
        results.append({
            "index": i,
            "relevance_score": float(score),
            "document": request.documents[i]
        })

    # 排序 (按分数降序)
    results.sort(key=lambda x: x["relevance_score"], reverse=True)

    # 截取 top_n
    if request.top_n:
        results = results[:request.top_n]

    return {
        "id": "rerank-cpu",
        "results": results,
        "meta": {"tokens": inputs.input_ids.shape[1]}
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7777)
