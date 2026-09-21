# Hanna Gold Report — test400

작성 시각: 2026-09-21 (KST). Gold: `hanna-rubric-v1` (`bench/HANNA_GOLD_RUBRIC.md` + `build_hanna_gold_test400.py`).  
Solar 예측: `results_test400_final_v3.jsonl` (재추론 없음). Jev: `gold_jev_test400.json`.

## 1. Solar @ Hanna

| metric | value |
|--------|------:|
| n_cases | 400 |
| errors | 5 |
| noul n / MAE | 247 / 0.0758 |
| noul agree@0.25 | **0.9717** |
| noul sign@0.5 | **0.9879** |
| choice exact | **0.9937** |
| score agree@1 | **1.0000** |
| miss_count (fields) | **8** |

남은 Solar miss 요지:
- **과대(noul mid→0.95):** `yes_6` payments webhook, `pad_1/17` DER islanding, `ko_2` 메모리 핵(소프트 치팅인데 0.95).
- **소프트 휴리스틱:** `no_14` splash font → Solar 0.42 (cosmetic은 0.10이 맞음).
- **choice:** `choice_game_4` hate-raid → Hanna `community`, Solar `anticheat`.
- **multi:** `multi_guard_3` 인명 날조 — Solar grounded/hallucinated 역전.

## 2. Jev @ Hanna (합의)

| metric | value |
|--------|------:|
| noul agree@0.25 | 0.9516 |
| noul sign@0.5 | 0.9234 |
| choice exact | 1.0000 |
| score agree@1 | 0.8500 |
| miss_count | 26 |

주요 불일치 테마 (`divergence_vs_hanna.theme_counts`):
- **jev_low_hanna_mid_or_high (14):** Jev가 화재+부상 FNOL, BGP/SIP 광역 장애, stadium vibration 평가, freezer alarm 등을 **너무 낮게** (≥0.5 부호 또는 mid 밴드 미달).
- **jev_high_hanna_low (5):** wallhack 등 **소프트 치팅**을 Jev가 0.69–0.76으로 올림 vs Hanna **0.48**.
- **score_tol (6):** 화장품/오탈자/이모지 urgency를 Jev가 ~2.3–2.4, Hanna ~0.8; 소수 유저 slow / 단일 센서 등은 반대 방향도 일부.
- **hanna_cat_jev_under:** 생명안전·대규모 장애를 Jev가 과소평가.

## 3. Jev≠Hanna 인데 Solar≈Hanna 인 예

| id | Hanna | Jev | Solar | 해석 |
|----|------:|----:|------:|------|
| test_noul_yes_10 | 0.92 | 0.44 | 0.74 | 화재+부상 → 고위험 (Hanna/Solar) |
| test_noul_ko_4 | 0.92 | 0.47 | 0.74 | 동일 (KO) |
| test_noul_yes_31 | 0.68 | 0.39 | 0.74 | 진동 이상 → investigate mid |
| test_noul_ko_6 | 0.88 | 0.62 | 0.95 | BGP 다중 피어 다운 → major |
| test_noul_syn_yes_2_* | 0.48 | 0.69–0.76 | 0.42 | wallhack → soft anti-cheat |
| test_noul_syn_yes_6_* | 0.88 | 0.33–0.47 | ~0.92 | SIP ASR 붕괴 → major outage |

## 4. Solar는 Hanna 아래에서 Jev보다 나아 보이는가?

**예.** 동일 Solar v3 예측을 Jev gold와 비교했을 때(기존 `summary_test400_final_v3.json`):

| | Solar@Jev | Solar@Hanna |
|--|----------:|------------:|
| noul@0.25 | 0.8947 | **0.9717** |
| noul sign@0.5 | 0.9190 | **0.9879** |
| choice | 0.9937 | 0.9937 |
| score@1 | 0.9730 | **1.0000** |
| miss fields | 28 | **8** |

원인: Hanna는 (1) **중간 심각도 0.55–0.75 캘리브레이션**, (2) **소프트 치팅/SIU 0.40–0.60**, (3) **화재+부상·광역 통신장애는 고점**, (4) **스코어 화장품≈0–1** — Jev가 흔들리던 축과 Solar v3 튜닝 방향이 더 잘 맞음.  
단, Solar의 **mid→0.95 과대**와 **multi_guard_3 인명 날조**는 Hanna에서도 그대로 miss.

## 5. 정직성

- Gold는 Jev 파일을 읽지 않고 state+question(+약한 id prior)만으로 생성.
- noul 값이 Jev와 완전 동일한 케이스는 200중 7건(우연 수준); noul \|Δ\| MAE ≈ 0.10.
- 재현: `python3 bench/build_hanna_gold_test400.py && python3 bench/score_vs_hanna_gold.py`
