# Changelog

All notable changes to the Parent Co-Pilot project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2025-06-13

### Changed
- Updated guardrails prompts from GUARDRAILS_PROMPT_2 to GUARDRAILS_PROMPT
## [1.0.1] - 2025-06-13

### Added
- API versioning system with centralized version information
- New `/api/test-guardrails` endpoint for testing message classification
- Version display in FastAPI documentation

### Changed
- Refactored version information into dedicated module
- Updated health check endpoint to use centralized version

## [1.0.0] - Initial Release

### Added
- FastAPI backend with REST API endpoints
- Conversation handling with guardrails
- Chat history with Supabase
- Chat summarization functionality
- Tip of the day feature
- Activities suggestions
- Reminders extraction
- Vector store for document storage
- Contract to JSON conversion
