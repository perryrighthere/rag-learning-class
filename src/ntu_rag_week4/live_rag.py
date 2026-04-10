from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from ntu_rag_week1.embedding import HashingEmbedder, cosine_similarity

from .llm import OpenAICompatibleChatClient
from .models import (
    ChatMessage,
    ChunkHit,
    ChunkRecord,
    ChunkingRequest,
    ProviderConfig,
    Week4LiveAnswer,
)
from .pipeline import build_week4_chunking_report, default_week4_input_path


class SimpleChunkRetriever:
    def __init__(self, chunks: list[ChunkRecord]) -> None:
        self.embedder = HashingEmbedder()
        self.chunks = chunks
        self.chunk_vectors = [self.embedder.embed(chunk.text) for chunk in chunks]

    def query(self, question: str, top_k: int = 3) -> list[ChunkHit]:
        query_vector = self.embedder.embed(question)
        scored = [
            ChunkHit(chunk=chunk, score=cosine_similarity(query_vector, vector))
            for chunk, vector in zip(self.chunks, self.chunk_vectors)
        ]
        ranked = sorted(scored, key=lambda item: item.score, reverse=True)
        return ranked[:top_k]


class Week4LiveRAGPipeline:
    def __init__(
        self,
        provider_config: ProviderConfig,
        chunk_strategy: str = "structure-aware",
        input_path: Path | None = None,
        fixed_chunk_size: int = 3,
        fixed_overlap: int = 1,
        structure_max_chars: int = 220,
        structure_min_chunk_chars: int = 80,
        langchain_chunk_size: int = 90,
        langchain_chunk_overlap: int = 20,
    ) -> None:
        report = build_week4_chunking_report(
            ChunkingRequest(
                input_path=input_path or default_week4_input_path(),
                strategies=[chunk_strategy],
                fixed_chunk_size=fixed_chunk_size,
                fixed_overlap=fixed_overlap,
                structure_max_chars=structure_max_chars,
                structure_min_chunk_chars=structure_min_chunk_chars,
                langchain_chunk_size=langchain_chunk_size,
                langchain_chunk_overlap=langchain_chunk_overlap,
            )
        )
        strategy_result = report.strategy_results[0]
        if not strategy_result.chunks:
            raise ValueError("No chunks available for live RAG.")

        self.provider_config = provider_config
        self.chunk_strategy = chunk_strategy
        self.input_path = report.input_path
        self.retriever = SimpleChunkRetriever(strategy_result.chunks)
        self.client = OpenAICompatibleChatClient(provider_config)

    def ask(
        self,
        question: str,
        top_k: int = 3,
        temperature: float = 0.2,
        max_tokens: int = 600,
    ) -> Week4LiveAnswer:
        evidence = self.retriever.query(question=question, top_k=top_k)
        if not evidence:
            raise RuntimeError("No evidence was retrieved for the question.")

        prompt_preview = build_evidence_prompt(question, evidence)
        completion = self.client.complete(
            messages=[
                ChatMessage(
                    role="system",
                    content=(
                        "你是一个证据优先的 RAG 助手。"
                        "只能依据给定证据回答。"
                        "如果证据不足，必须明确说明证据不足。"
                        "回答中尽量引用 source_id。"
                    ),
                ),
                ChatMessage(role="user", content=prompt_preview),
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return Week4LiveAnswer(
            question=question,
            answer=completion.content,
            provider=completion.provider,
            model=completion.model,
            chunk_strategy=self.chunk_strategy,
            evidence=evidence,
            prompt_preview=prompt_preview,
            usage=completion.usage,
        )


def build_evidence_prompt(question: str, evidence: list[ChunkHit]) -> str:
    lines = [
        "请根据下面证据回答问题。",
        "输出要求：",
        "1. 先给结论。",
        "2. 再给依据，使用 source_id 标注。",
        "3. 如果证据不足，直接说“证据不足”，不要补充常识。",
        "",
        f"问题：{question}",
        "",
        "证据：",
    ]
    for index, item in enumerate(evidence, start=1):
        lines.extend(
            [
                f"[{index}] source_id={item.chunk.source_id}",
                f"title={item.chunk.document_title}",
                f"score={item.score:.4f}",
                f"sections={','.join(item.chunk.section_headings) or '正文'}",
                f"pages={item.chunk.page_numbers}",
                f"text={item.chunk.text}",
                "",
            ]
        )
    return "\n".join(lines).strip()


def render_live_answer(result: Week4LiveAnswer) -> str:
    lines = [
        f"provider: {result.provider}",
        f"model: {result.model}",
        f"chunk_strategy: {result.chunk_strategy}",
        f"question: {result.question}",
        "",
        "answer:",
        result.answer,
        "",
        "evidence:",
    ]
    for index, item in enumerate(result.evidence, start=1):
        lines.append(
            f"  [{index}] {item.chunk.source_id} | score={item.score:.4f} | sections={item.chunk.section_headings}"
        )
        lines.append(f"      {item.chunk.text}")
    if result.usage:
        lines.extend(["", f"usage: {result.usage}"])
    return "\n".join(lines)


def live_answer_to_payload(result: Week4LiveAnswer) -> dict[str, object]:
    return {
        "question": result.question,
        "answer": result.answer,
        "provider": result.provider,
        "model": result.model,
        "chunk_strategy": result.chunk_strategy,
        "prompt_preview": result.prompt_preview,
        "usage": result.usage,
        "evidence": [
            {
                "score": round(item.score, 4),
                "chunk": asdict(item.chunk),
            }
            for item in result.evidence
        ],
    }
