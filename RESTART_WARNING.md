# ⚠️ Restart Warning — Integrations with Session or Rate Limits

When performing repeated Home Assistant restarts — for example during HACS updates,
integration development, or debug sessions — certain cloud integrations can exhaust
their API session quota or trigger rate limiting blocks.

Disable the integrations listed below **before** starting a multi-restart session.

---

## 🔴 Always disable before repeated restarts

| Integration | Issue | Recovery time |
|---|---|---|
| **HomematicIP Cloud** | Each HA restart opens a new REST API connection. Too many connections trigger an immediate block — visible in both HA logs and the HomematicIP app as *"Restriction rest active — due to unusually high server load"* | 15 minutes with no connection attempts |
| **Home Connect** | OAuth sessions are consumed on every restart. Repeated restarts exhaust the session pool, causing the integration to fail until tokens expire | Hours; re-authentication may be required |

---

## 🟡 Use caution during intensive sessions

| Integration | Issue | Notes |
|---|---|---|
| **Tado** | Strict daily API quota introduced in late 2025. Heavy HA restarts consume quota rapidly; once exhausted, the integration stops functioning until midnight reset | Disable if expecting 5+ restarts |
| **Spotify** | OAuth token refresh on every restart — generally tolerant, but may throttle under rapid cycling | Low risk; monitor if issues arise |
| **Nest / Google Home** | OAuth sessions with a daily quota per project | Disable if expecting 5+ restarts |

---

## 🟢 Safe to restart freely

| Integration | Notes |
|---|---|
| **EcoFlow Cloud** *(this integration)* | MQTT reconnects cleanly on every HA restart. No known rate limits on the EcoFlow cloud side. |

> **EcoFlow-specific:** always use a **full HA restart** rather than reloading the integration.
> A reload (without full restart) creates two simultaneous MQTT clients, which causes duplicate
> updates and can freeze sensor values.

---

## Recommended procedure for development sessions

```
1. Settings → Integrations → HomematicIP Cloud → ⋮ → Disable
2. Settings → Integrations → Home Connect      → ⋮ → Disable
3. (optional) Disable Tado if expecting 5+ restarts
4. Perform all development work, HACS updates, or debug cycles
5. Do one final clean restart
6. Re-enable all disabled integrations
```

> Use **Disable** — not **Delete** — to preserve the integration configuration.
