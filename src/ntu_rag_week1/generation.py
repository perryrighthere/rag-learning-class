from __future__ import annotations

import re

from .embedding import tokenize
from .models import RagAnswer, RetrievedChunk


def _split_support_sentences(text: str) -> list[str]:
    sentences = [item.strip() for item in re.findall(r"[^。！？!?]+[。！？!?]?", text)]
    return [sentence for sentence in sentences if sentence]


class ExtractiveAnswerGenerator:
    def generate(self, question: str, evidence: list[RetrievedChunk]) -> RagAnswer:
        question_tokens = set(tokenize(question))
        ranked_sentences: list[tuple[int, float, str]] = []

        for index, item in enumerate(evidence):
            for sentence in _split_support_sentences(item.chunk.text):
                sentence_tokens = set(tokenize(sentence))
                overlap = len(question_tokens & sentence_tokens)
                score = overlap + item.score
                ranked_sentences.append((overlap, score, sentence))

        ranked_sentences.sort(key=lambda item: (item[0], item[1]), reverse=True)

        answer_parts: list[str] = []
        seen = set()
        for overlap, _, sentence in ranked_sentences:
            if sentence in seen:
                continue
            if overlap == 0 and answer_parts:
                continue
            answer_parts.append(sentence)
            seen.add(sentence)
            if len(answer_parts) == 2:
                break

        if not answer_parts and evidence:
            answer_parts.append(evidence[0].chunk.text)

        answer = "基于检索到的证据，" + " ".join(answer_parts)
        return RagAnswer(question=question, answer=answer, evidence=evidence)
