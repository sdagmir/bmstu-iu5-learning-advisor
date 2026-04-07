# Diploma Project — Intelligent System

## Architecture
Three backend modules:
- LLM Orchestrator — chat via OpenRouter API
- Expert System — rule-based inference (Mivar or Python)
- RAG Recommender — Qdrant vector search to augment LLM answers

## Stack
- Backend: Python 3.12, FastAPI, SQLAlchemy 2.x async, PostgreSQL, Qdrant, OpenRouter
- Frontend: (TBD)

## Rules
- `from __future__ import annotations` in every Python file
- Router → Service separation, business logic only in services
- `except BaseException` (not Exception) in async generators
- `expire_on_commit=False` on async session factory
- Full patterns: /backend and /frontend

## Docs
- docs/ inside each subproject for architecture, API, deploy notes
