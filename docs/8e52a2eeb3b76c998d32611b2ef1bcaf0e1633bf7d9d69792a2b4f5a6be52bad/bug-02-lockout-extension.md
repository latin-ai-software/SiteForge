# Bug dossier: active lockout extended on repeated failures

## Author
Copilot (AI assistant using Copilot SDK in VS Code)

## Summary
While a user was already locked out, repeated failed-login calls could continue to update the lockout state and extend the expiry window. This changed a temporary lockout into a longer, more punitive block than intended.

## Version
8e52a2eeb3b76c998d32611b2ef1bcaf0e1633bf7d9d69792a2b4f5a6be52bad

## Impact
- A blocked account could be penalized repeatedly even though it was already under lockout.
- The lockout duration could drift past the configured value, causing unnecessary login denial.
- The account state no longer matched the rule of "lockout for X seconds after the threshold".

## Root cause
`record_failed_login()` did not short-circuit if `locked_until` was still in the future. Every subsequent failed login wrote a new timestamp instead of leaving the current lockout unchanged.

## Fix
The method now exits early while the account is already locked and leaves the existing lockout metadata untouched until expiry.

## Evidence
See the regression tests in `tests/test_ratelimiter.py` covering repeated attempts while a lockout is active.
