"""
AI layer. Everything that calls an external LLM provider lives here -
nowhere else in the codebase imports an AI SDK or holds AI_API_KEY.

resume_analyzer.py: resume analysis provider abstraction (Phase 7).
interview_generator.py: interview question generation provider abstraction (Phase 9).
answer_evaluator.py: interview answer evaluation provider abstraction (Phase 10).
schemas.py / interview_schemas.py: structured Pydantic contracts AI providers must satisfy.
exceptions.py: AI-specific errors (configuration, provider, validation) - shared by every provider.
"""
