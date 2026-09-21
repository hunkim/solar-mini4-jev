# Hanna Gold Rubric (v1) — human/assistant judgment labels

**Purpose:** Independent gold for `cases_test400.json`. Not Jev. Labels are produced offline from **case state + question text** only (id hints are weak priors; state overrides).

**Model tag:** `hanna-rubric-v1`

---

## 공통 / Common principles

- Prefer **calibrated mid** values for investigate-first / limited-scope protective actions (**0.55–0.75**), not 0.95.
- Reserve **≥0.85** for clear life-safety, major multi-customer outage, active fire+injury, confirmed pathogen hold, structural collapse / confined-space O2 emergency, medical AED/no-pulse, or equivalent.
- Cosmetic / FAQ / comfort / routine scheduling → **0.05–0.20**, even if the question mentions emergencies (mismatch state).
- Soft fraud / anti-cheat without confirmed life-safety or infrastructure outage → **0.40–0.60**.
- Korean and English use the **same numeric thresholds**.

---

## noul (0–1)

| Band | EN | KO | Typical value |
|------|----|----|---------------|
| Catastrophic / life-safety / major outage | clear fire+injury, O2 confined rescue, collapse risk, confirmed pathogen hold (Listeria PCR / allergen recall), cascading blackout / BGP national loss, AED/no-pulse | 화재+부상, 밀폐공간 O2, 붕괴, 병원체 홀드, 대규모 정전, 심정지 | **0.85–0.95** |
| Protective but investigate-first / limited | N-1 margin, bridge strain pending inspection, freezer/RH alarms, CAT staffing, fiber splice, privacy breach notify, stadium vibration *assessment*, payments Sev escalation | 조사 선행, 제한 범위 보호조치 | **0.55–0.75** |
| Soft fraud / anti-cheat pattern | memory injector / wallhack mass-ban ask, SIU soft-tissue identical claims (no confirmed exploit impact on infra/life) | 치팅·연조직 SIU 패턴 | **0.40–0.60** |
| Cosmetic / FAQ / comfort | dashboard colors, emote, trash schedule, PDF download, coffee, Grafana theme, splash font | 장식·FAQ·편의 | **0.05–0.20** |

### Domain notes (noul)

- **Anti-cheat / esports integrity:** mass-ban + queue lock on injector/wallhack → mid-soft **~0.50–0.55**. Overlay leak / integrity halt → **~0.60–0.65**.
- **Insurance fire FNOL:** active flames + injured → high **~0.90** (life-safety present even if question is claims protocol). Soft-tissue SIU freeze → **~0.48**.
- **Archives RH / sprinkler soak / scanner overheat:** protective conservation → mid **~0.60–0.70**, not catastrophic.
- **Cyber CAT / ransomware on clinic EHR (claims desk ask):** mid-high **~0.70–0.78** unless encrypting life-critical care described as active patient harm.
- **Id hint:** `*_yes_*` / `*_no_*` is a weak prior only. If id says yes but state is cosmetic → **low**. If id says no but state is life-safety → **high**.

---

## choice (exact label)

Pick the **single best** criterion key using state keywords.

Priority when two fit: **safety > ops**, **cat > fnol** for landfall/wildfire/태풍, **labeling** for allergen mislabel, **biosafety** for autoclave/exposure, **anticheat** for cheats vs **community** for hate-raid/slurs, **shipping** for reefer/dock cold-chain.

Language choice (`ko`/`en`/`ja`/`zh`): detect script of the user utterance in state.

Severity choice (`sev1`…`sev4`): map impact — citywide SCADA/BGP/MES down → sev1; regional elevated FP / limited slow → sev2–sev3; typo/1px → sev4. (Criteria order in question defines meaning; match by label semantics.)

---

## score (0–4 continuous)

Map to criteria length (typically 5 bands ≈ 0…4):

| Impact | Score |
|--------|-------|
| Cosmetic / no user impact / deferrable tidy | **0.0–1.0** |
| Minor / few users / limited sensor | **1.0–2.0** |
| Degraded many / board demo tomorrow / partial outage | **2.0–3.0** |
| Major feature / plant-wide / vault write fail | **3.0–3.6** |
| Full outage / data loss / life-safety / ransomware encrypting / fiber 50k | **3.7–4.0** |

Urgency criteria use the same numeric mapping (drop-everything ≈4, next-month cosmetic ≈1).

---

## multi (RAG guard)

Parse `QUESTION` / `RETRIEVED CONTEXT` / `MODEL ANSWER` from state.

| Field | High when |
|-------|-----------|
| **grounded** | Answer supported by context **OR** correct refusal for missing info |
| **hallucinated** | Invented material facts (names, exact numbers, forever/always bans not in context) |
| **abstain** | Correct refusal because info missing |
| **decision** | `pass` if grounded & not hallucinated; `rewrite` if soft overclaim; `block` if hard invent (fabricated person/number/policy forever) |

Typical numeric pairs:

- Hard invent (chair name, 12.5 min, 18% SOC, forever ban): grounded **~0.05**, hallucinated **~0.95**, abstain **~0.05**, decision **block**
- Faithful paraphrase / correct “no”: grounded **~0.90**, hallucinated **~0.05**, abstain **~0.05**, decision **pass**
- Correct refusal (if present): grounded **~0.90**, hallucinated **~0.05**, abstain **~0.90**, decision **pass**

---

## Honesty

- Do **not** copy Jev answers when building gold.
- Gold must be regenerable from this rubric + `build_hanna_gold_test400.py`.
