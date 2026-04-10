from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ntu_rag_week4 import build_provider_config
from ntu_rag_week4.live_rag import Week4LiveRAGPipeline, build_evidence_prompt, live_answer_to_payload
from ntu_rag_week4.llm import OpenAICompatibleChatClient
from ntu_rag_week4.models import ChatCompletionResult, ChatMessage


class ProviderConfigTest(unittest.TestCase):
    def test_build_provider_config_uses_provider_defaults(self) -> None:
        config = build_provider_config(provider="siliconflow", model="Qwen/Qwen3-32B")

        self.assertEqual(config.base_url, "https://api.siliconflow.com/v1")
        self.assertEqual(config.api_key_env, "SILICONFLOW_API_KEY")

    def test_custom_provider_requires_base_url(self) -> None:
        with self.assertRaises(ValueError):
            build_provider_config(provider="custom", model="demo-model")


class OpenAICompatibleChatClientTest(unittest.TestCase):
    def test_client_posts_chat_completion_request(self) -> None:
        config = build_provider_config(provider="openrouter", model="openai/gpt-4o-mini")
        client = OpenAICompatibleChatClient(config)

        with (
            patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}, clear=False),
            patch("ntu_rag_week4.llm._post_json") as post_json,
        ):
            post_json.return_value = {
                "model": "openai/gpt-4o-mini",
                "choices": [
                    {
                        "message": {
                            "content": "结论：开通后 24 小时内完成第一次复核。"
                        }
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 12},
            }
            result = client.complete(
                messages=[ChatMessage(role="user", content="测试")],
                temperature=0.1,
                max_tokens=200,
            )

        self.assertEqual(result.content, "结论：开通后 24 小时内完成第一次复核。")
        _, kwargs = post_json.call_args
        self.assertEqual(kwargs["url"], "https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(kwargs["payload"]["model"], "openai/gpt-4o-mini")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(kwargs["headers"]["X-Title"], "NTU RAG Teaching Repo")


class Week4LiveRAGPipelineTest(unittest.TestCase):
    def test_live_pipeline_retrieves_evidence_and_returns_payload(self) -> None:
        payload = {
            "source_id": "web_access_review",
            "title": "临时访问复核流程",
            "source_ref": "internal://access-review",
            "published_at": "2025-02-03",
            "format": "html",
            "authority_type": "process",
            "parser_used": "trafilatura+beautifulsoup",
            "clean_text": (
                "临时访问权限在开通后必须进入复核队列。"
                "开通后 24 小时内完成第一次复核。"
                "超过 7 天仍未关闭的访问申请需要升级。"
            ),
            "sections": [
                {
                    "heading": "复核时点",
                    "text": (
                        "临时访问权限在开通后必须进入复核队列。"
                        "开通后 24 小时内完成第一次复核。"
                        "超过 7 天仍未关闭的访问申请需要升级。"
                    ),
                    "order": 1,
                    "page": None,
                }
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "parsed_documents.jsonl"
            input_path.write_text(
                json.dumps(payload, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            config = build_provider_config(
                provider="siliconflow",
                model="Qwen/Qwen3-32B",
            )
            fake_completion = ChatCompletionResult(
                provider="siliconflow",
                model="Qwen/Qwen3-32B",
                content="结论：第一次复核时点是开通后 24 小时内。[web_access_review]",
                raw_response={"choices": [{"message": {"content": "x"}}]},
                usage={"prompt_tokens": 20, "completion_tokens": 18},
            )

            with patch(
                "ntu_rag_week4.live_rag.OpenAICompatibleChatClient.complete",
                return_value=fake_completion,
            ):
                pipeline = Week4LiveRAGPipeline(
                    provider_config=config,
                    chunk_strategy="structure-aware",
                    input_path=input_path,
                )
                result = pipeline.ask(
                    question="临时访问权限开通后多久要完成第一次复核？",
                    top_k=1,
                )

        self.assertEqual(result.provider, "siliconflow")
        self.assertIn("24 小时", result.answer)
        self.assertEqual(len(result.evidence), 1)
        self.assertIn("source_id=web_access_review", result.prompt_preview)

        payload = live_answer_to_payload(result)
        self.assertEqual(payload["provider"], "siliconflow")
        self.assertEqual(payload["evidence"][0]["chunk"]["source_id"], "web_access_review")

    def test_build_evidence_prompt_mentions_source_ids(self) -> None:
        config = build_provider_config(provider="siliconflow", model="Qwen/Qwen3-32B")
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "parsed_documents.jsonl"
            input_path.write_text(
                json.dumps(
                    {
                        "source_id": "doc-1",
                        "title": "制度",
                        "source_ref": "internal://doc-1",
                        "published_at": "2025-01-01",
                        "format": "md",
                        "authority_type": "policy",
                        "parser_used": "markdown-normalizer",
                        "clean_text": "访问审批要记录申请人。",
                        "sections": [
                            {
                                "heading": "正文",
                                "text": "访问审批要记录申请人。",
                                "order": 1,
                                "page": 1,
                            }
                        ],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            with patch(
                "ntu_rag_week4.live_rag.OpenAICompatibleChatClient.complete",
                return_value=ChatCompletionResult(
                    provider="siliconflow",
                    model="Qwen/Qwen3-32B",
                    content="ok",
                    raw_response={"choices": [{"message": {"content": "ok"}}]},
                    usage={},
                ),
            ):
                pipeline = Week4LiveRAGPipeline(
                    provider_config=config,
                    chunk_strategy="structure-aware",
                    input_path=input_path,
                )
                evidence = pipeline.retriever.query("申请人", top_k=1)

        prompt = build_evidence_prompt("要记录什么", evidence)
        self.assertIn("source_id=doc-1", prompt)
        self.assertIn("text=访问审批要记录申请人。", prompt)


if __name__ == "__main__":
    unittest.main()
