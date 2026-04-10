from __future__ import annotations

import json
import os
from urllib import error, request

from .models import ChatCompletionResult, ChatMessage, ProviderConfig


PROVIDER_DEFAULTS = {
    "siliconflow": {
        "base_url": "https://api.siliconflow.com/v1",
        "api_key_env": "SILICONFLOW_API_KEY",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
    },
}


def build_provider_config(
    provider: str,
    model: str,
    base_url: str | None = None,
    api_key_env: str | None = None,
    timeout_seconds: int = 60,
    app_name: str = "NTU RAG Teaching Repo",
    referer: str | None = None,
) -> ProviderConfig:
    provider_key = provider.lower()
    if provider_key == "custom":
        if not base_url:
            raise ValueError("custom provider requires --base-url")
        return ProviderConfig(
            provider=provider_key,
            model=model,
            api_key_env=api_key_env or "OPENAI_COMPATIBLE_API_KEY",
            base_url=base_url.rstrip("/"),
            timeout_seconds=timeout_seconds,
            app_name=app_name,
            referer=referer,
        )

    if provider_key not in PROVIDER_DEFAULTS:
        raise ValueError(f"Unsupported provider: {provider}")

    defaults = PROVIDER_DEFAULTS[provider_key]
    return ProviderConfig(
        provider=provider_key,
        model=model,
        api_key_env=api_key_env or str(defaults["api_key_env"]),
        base_url=(base_url or str(defaults["base_url"])).rstrip("/"),
        timeout_seconds=timeout_seconds,
        app_name=app_name,
        referer=referer,
    )


class OpenAICompatibleChatClient:
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int = 600,
    ) -> ChatCompletionResult:
        api_key = os.getenv(self.config.api_key_env)
        if not api_key:
            raise RuntimeError(
                f"Environment variable {self.config.api_key_env} is required for provider {self.config.provider}."
            )

        payload = {
            "model": self.config.model,
            "messages": [message.__dict__ for message in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        response_payload = _post_json(
            url=self.config.base_url + "/chat/completions",
            payload=payload,
            headers=_build_headers(self.config, api_key),
            timeout_seconds=self.config.timeout_seconds,
        )
        content = _extract_message_content(response_payload)
        usage = response_payload.get("usage")
        return ChatCompletionResult(
            provider=self.config.provider,
            model=str(response_payload.get("model") or self.config.model),
            content=content,
            raw_response=response_payload,
            usage=usage if isinstance(usage, dict) else {},
        )


def _build_headers(config: ProviderConfig, api_key: str) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if config.provider == "openrouter":
        headers["X-Title"] = config.app_name
        if config.referer:
            headers["HTTP-Referer"] = config.referer
    return headers


def _post_json(
    url: str,
    payload: dict[str, object],
    headers: dict[str, str],
    timeout_seconds: int,
) -> dict[str, object]:
    api_request = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with request.urlopen(api_request, timeout=timeout_seconds) as response:
            raw_payload = response.read().decode("utf-8")
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"LLM provider returned HTTP {exc.code}: {details.strip() or exc.reason}"
        ) from exc
    except error.URLError as exc:
        raise RuntimeError(f"LLM provider request failed: {exc.reason}") from exc

    try:
        response_payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError("LLM provider did not return JSON.") from exc

    if not isinstance(response_payload, dict):
        raise RuntimeError("LLM provider returned a non-object JSON payload.")
    return response_payload


def _extract_message_content(response_payload: dict[str, object]) -> str:
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("LLM provider response is missing choices.")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise RuntimeError("LLM provider choice format is invalid.")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise RuntimeError("LLM provider response is missing assistant message.")

    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        text_parts = [
            str(item.get("text", ""))
            for item in content
            if isinstance(item, dict) and item.get("type") in {None, "text"}
        ]
        joined = "".join(text_parts).strip()
        if joined:
            return joined
    raise RuntimeError("LLM provider response is missing text content.")
