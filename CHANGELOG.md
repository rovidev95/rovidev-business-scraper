# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres
to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-06-27

### Added
- Selector-based scraping of prices and availability from public pages.
- `robots.txt` awareness and a per-host rate limiter (polite by default).
- Change detection between runs (price drops, stock changes, new/removed items).
- JSON / CSV / Google Sheets export sinks and a FastAPI HTTP API.
