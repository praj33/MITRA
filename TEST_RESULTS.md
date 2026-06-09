# Mitra Unified System Test Results

Date: June 9, 2026
Version: 3.0.0 unified control plane
Result: PASS

## Automated Verification

Backend command:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -m pytest tests -q --disable-warnings
```

Backend result:

```text
60 passed, 849 warnings in 8.69s
```

The warnings are existing dependency and `datetime.utcnow()` deprecation warnings. There were no test failures.

Frontend command:

```powershell
npm run build
```

Frontend result:

```text
Compiled successfully.
The build folder is ready to be deployed.
```

## Verified Behavior

| Area | Verified result |
| --- | --- |
| Entry authority | `POST /api/mitra/evaluate` is the only public decision entrypoint |
| Retired parallel routes | Old decision, RL, intent, and external-app entrypoints return `404` |
| Policy runtime | Clean, rewrite, sexual-risk, self-harm, and harmful inputs are classified |
| RL interpretation | Correction, refinement, positive, and negative signals are deterministic |
| Conflict guard | RL can adjust confidence but cannot change the policy decision |
| Enforcement | Only Mitra can open enforcement scope; direct bypass is rejected |
| Trace continuity | Policy, RL, enforcement, response, and bucket use one `trace_id` |
| Bucket failure | Mongo unavailability fails closed; no in-memory or JSONL fallback exists |
| API contract | The universal Mitra response fields are schema-tested |
| Assistant integration | Authenticated assistant context reaches the same Mitra pipeline |
| Inbound channels | Telegram, WhatsApp, email, and telephony integration tests pass |
| Frontend | Production React build compiles against the unified response contract |

## Real Persistence Proof

A live control-plane execution used the Mongo configuration from `backend/.env`.

```text
trace_id: trace_dc1df4f632ee5ee0
Mongo connected: true
Persisted records: 8
```

Persisted stages:

```text
request_received
mitra_policy_runtime
mitra_rl_interpretation
mitra_conflict_guard
mitra_enforcement_runtime
mitra_enforcement_telemetry
mitra_response_contract
mitra_request_log
```

Mongo record IDs:

```text
6a27ec9c2ecf4ec55feac45a
6a27ec9c2ecf4ec55feac45b
6a27ec9d2ecf4ec55feac45c
6a27ec9d2ecf4ec55feac45d
6a27ec9d2ecf4ec55feac45e
6a27ec9d2ecf4ec55feac45f
6a27ec9d2ecf4ec55feac460
6a27ec9d2ecf4ec55feac461
```

The full captured output is in `backend/MITRA_CONTROL_PLANE_LIVE_JSON.json`.
