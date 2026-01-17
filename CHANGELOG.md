# Changelog

## [Unreleased]

### Improved
- **Better error messages for shared backends** (2026-01-18)
  - CEP rule creation now hints when rules already exist due to shared Perseo backend
  - IoT device registration now hints when devices already exist due to shared IoT Agent
  - STH-Comet queries now explain when empty results are normal (no subscriptions configured)
  - All hints guide users to list/delete commands for resolution

### Context
These improvements came from comprehensive testing that revealed users may encounter:
- Shared Perseo CEP backends (rules visible across multiple FIWARE instances)
- Shared IoT Agent backends (devices visible across multiple instances)
- Empty STH-Comet results (normal for new deployments without subscriptions)

The new error messages help users understand these scenarios without requiring deep FIWARE knowledge.
