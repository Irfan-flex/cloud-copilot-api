# Changelog

## [1.0.0] - 2025-08-14

### Overview

Initial release of **Consume Edge**.

- **API**: This version is derived from `TBG Chat Bot` (https://github.com/speciphic-platform/tbg-ask-nlp-api) (commit `33456dc`), with modifications, improvements, and cleanup for our use case.
- **Internal UI**: This version is derived from the `agents-ui` (https://github.com/speciphic-platform/agents-ui/commit/a7cbefef6cf46d5426b9ca56574465b258c259c5) (commit: `a7cbefef`) , with modifications, improvements, and cleanup for our use case.
- **External UI**: This is the initial version of the project, built from scratch without using any existing codebase.

### Added

- Delmonte specific data files (pkl, xlsx)
- Request Validator Middleware for validating incoming route params
- Stores feature for getting stores in a given zip, state.
- GeoLocation services and nearby stores mapping with Google Maps integration
- Top new feature for analytics.
- Polly feature to generate from text to speech.
- LLM to provide stats from the query and response for each conversation
- Emotion CSS-in-JS support for better styling capabilities
- Ketch CDN integration for privacy compliance

### Improved

- Update Swagger Documentation for API
- Added validation for whisper service input.
- Logging to be handled by aws instead of applogs.log file
- state based conversation replaced with chat history based.
- Analytics to include delta of date range
- Improved response time for Analytics.
- Updated ESLint and build configuration to support Emotion `css` prop and warn on unused variables

### Fixed

- Authentication to use access_token instead of id_token
- Fixes identified in VAPT testing
- Resolved various UI styling inconsistencies

### Contributors

- Irfan Hussain
- Hinesh Miyani
- Sai Charan Kavuri
- Kiran Chaitanya
- Anudeep Metuku
- Krishna Sah Teli
- Devashish Devangan
- Mayuresh Singh