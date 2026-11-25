# Changelog

All notable changes to this project will be documented in this file.

## [0.1.4] - 2026-11-25

### Fixed
- Refactored `sensor`, `select`, `number`, and `light` platforms to share a single `RecuairDataUpdateCoordinator` (`recuair/coordinator.py`), reducing polling from 4 concurrent HTTP requests (including 30s control entity polls) to 1 request per `scan_interval` and eliminating ESP32 timeout warnings.
- Added a 15-second `aiohttp.ClientTimeout` to `GET` and `POST` requests in `recuair/api.py`.
- Raised `UpdateFailed` in the coordinator when fetching device data fails.
- Preserved current RGB color when changing light intensity through the `number` entity (falling back to white only if RGB is unavailable).
- Honored `entry.options[CONF_HOST]` when building device `configuration_url`.

### Added
- Unit test suite (`tests/test_coordinator.py`) covering shared coordinator polling, entity synchronization, backwards-compatible `unique_id` preservation, and error handling.
- `.github/CODEOWNERS` for automatic PR review notifications.

## [0.1.2] - 2026-06-21

### Added
- Control entities (`select` for mode, `number` for light intensity, `light` for RGB/brightness control).
- Options flow and configurable scan interval.
