# Bug dossier: lockout state reset after expiry

## Author
Copilot (AI assistant using Copilot SDK in VS Code)

## Summary
The lockout state stored for a username was not reliably reset once the lockout duration expired. The next failed-login event could re-use stale state, preventing the account from returning to a normal retry cycle.

## Version
8e52a2eeb3b76c998d32611b2ef1bcaf0e1633bf7d9d69792a2b4f5a6be52bad

## Impact
- Accounts could remain effectively locked even after the configured lockout window had elapsed.
- The failed-attempt counter could continue propagating stale values and bypass the expected reset flow.
- A user hitting the login endpoint after expiry would see a state that did not match the real lockout timeline.

## Root cause
`RateLimiter.record_failed_login()` increased the failure count without checking whether a previous lockout had already expired. When the session had a stale `locked_until` value, the method continued to use previous state rather than resetting the counter and timestamp.

## Fix
The code now resets expired lockout metadata before incrementing the failure counter and clears stale lockout values before the next failed attempt is recorded.

## Evidence
See the lockout regression tests in `tests/test_ratelimiter.py` for the expired-lockout reset scenario.
