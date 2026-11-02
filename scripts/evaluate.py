"""Retrieval and optional answer smoke evaluation.

    python -m scripts.evaluate
    python -m scripts.evaluate --answers
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.config import PROJECT_ROOT, load_settings
from src.embeddings import FastEmbedder
from src.generation import OpenAICompatibleLLM, answer_question
from src.retrieval import retrieve
from src.vector_store import IndexFormatError, IndexNotFoundError, IndexStore, StaleIndexError

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

EVAL_FILE = PROJECT_ROOT / "eval" / "student_handbook_questions.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval and optional answers.")
    parser.add_argument("--questions", type=Path, default=EVAL_FILE)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--answers", action="store_true", help="Also call the configured LLM.")
    args = parser.parse_args()

    settings = load_settings()
    top_k = args.top_k or settings.top_k
    questions = json.loads(Path(args.questions).read_text(encoding="utf-8"))["questions"]

    try:
        store = IndexStore.load(settings.index_dir)
        store.ensure_compatible(
            settings.embedding_model, settings.chunk_size, settings.chunk_overlap
        )
        store.validate_source(settings.document_path)
    except (IndexNotFoundError, IndexFormatError, StaleIndexError) as exc:
        raise SystemExit(f"Index problem: {exc}") from exc

    embedder = FastEmbedder(settings.embedding_model)
    retrieval_hits = 0
    retrieval_total = 0
    answer_hits = 0
    answer_total = 0
    llm = (
        OpenAICompatibleLLM(
            settings.llm_base_url,
            settings.llm_model,
            settings.llm_api_key,
            settings.llm_timeout,
        )
        if args.answers
        else None
    )

    for item in questions:
        question = item["question"]
        results = retrieve(question, embedder, store, top_k=top_k, min_score=settings.min_score)
        print(f"\nQ: {question}")
        print("   Sources: " + ("; ".join(result.citation() for result in results) or "none"))

        if item["answerable"]:
            retrieval_total += 1
            sections = {result.section for result in results}
            pages = {result.page for result in results}
            expected_sections = set(item.get("expected_sections", []))
            expected_pages = set(item.get("expected_pages", []))
            section_hit = not expected_sections or bool(sections & expected_sections)
            page_hit = not expected_pages or bool(pages & expected_pages)
            combined = " ".join(result.text for result in results).lower()
            term_hit = all(term.lower() in combined for term in item.get("expected_terms", []))
            passed = section_hit and page_hit and term_hit
            retrieval_hits += int(passed)
            print(
                f"   Retrieval: {'PASS' if passed else 'FAIL'} "
                f"(section={section_hit}, page={page_hit}, facts={term_hit})"
            )
            if llm:
                answer_total += 1
                answer = answer_question(question, results, llm)
                answer_ok = all(
                    term.lower() in answer.text.lower() for term in item.get("expected_terms", [])
                )
                answer_hits += int(answer_ok)
                print(f"   Answer: {'PASS' if answer_ok else 'FAIL'} - {answer.text}")
        elif llm:
            answer_total += 1
            answer = answer_question(question, results, llm)
            answer_ok = "couldn't find" in answer.text.lower() or "could not find" in answer.text.lower()
            answer_hits += int(answer_ok)
            print(f"   Abstention: {'PASS' if answer_ok else 'FAIL'} - {answer.text}")
        else:
            print("   Not scored (abstention requires --answers).")

    if retrieval_total:
        print(f"\nRecall@{top_k}: {retrieval_hits}/{retrieval_total} = {retrieval_hits / retrieval_total:.0%}")
    if llm and answer_total:
        print(f"Answer/abstention check: {answer_hits}/{answer_total} = {answer_hits / answer_total:.0%}")
        print("Note: this is a keyword smoke check, not an LLM-as-judge score.")
    if retrieval_hits < retrieval_total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
