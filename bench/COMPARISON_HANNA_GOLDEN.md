# Hanna Golden Set 기준: Jev vs SolarMini4 (test400)

**Golden set:** `gold_hanna_test400.json` (hanna-rubric-v1) — **공식 채점 기준**  
**예측:** SolarMini4 = `results_test400_final_v3.jsonl` · Jev = 동일 파일의 jev 응답  
**임계값:** noul ≤0.25 & sign@0.5 · choice exact · score ≤1 · field_acc = 필드 단위 합격률

---

## 1. 전체

| 모델 | noul≤0.25 | noul sign@0.5 | choice | score≤1 | field_acc | miss 필드 |
|------|----------:|--------------:|-------:|--------:|----------:|----------:|
| **SolarMini4** | **97.2%** | **98.8%** | 99.4% | **100%** | **98.2%** | **8** |
| Jev | 95.1% | 92.3% | **100%** | 89.2% | 94.6% | 24 |

→ Hanna golden 기준으로 **SolarMini4가 전반 우위** (특히 noul sign·score).

---

## 2. 언어별

| 언어 | n | 모델 | noul≤0.25 | sign@0.5 | choice | score≤1 | field_acc |
|------|--:|------|----------:|---------:|-------:|--------:|----------:|
| **KO** | 70 | **SolarMini4** | **96.9%** | **96.9%** | **100%** | **100%** | **98.8%** |
| **KO** | 70 | Jev | 93.8% | 93.8% | 100% | 88.9% | 95.0% |
| EN | 330 | **SolarMini4** | **97.2%** | **99.1%** | 99.2% | **100%** | **98.1%** |
| EN | 330 | Jev | 95.3% | 92.1% | **100%** | 89.3% | 94.5% |

→ 한·영 모두 SolarMini4 우위. KO에서 Solar miss 필드 1 vs Jev 4.

---

## 3. 분야별 (field_acc)

| 분야 | n | SolarMini4 | Jev | Δ (S−J) |
|------|--:|-----------:|----:|--------:|
| noul_clear (명확 yes/no) | 56 | 96.4% | 96.4% | 0 |
| **noul_ko** | 20 | **95.0%** | 85.0% | **+10.0** |
| noul_pad | 28 | 92.6% | **100%** | −7.4 |
| **noul_syn** (합성) | 96 | **100%** | 84.4% | **+15.6** |
| choice_energy | 12 | 100% | 100% | 0 |
| choice_game | 12 | 91.7% | **100%** | −8.3 |
| choice_muni | 12 | 100% | 100% | 0 |
| choice_ins | 12 | 100% | 100% | 0 |
| choice_bio | 12 | 100% | 100% | 0 |
| choice_tel | 12 | 100% | 100% | 0 |
| choice_intent | 12 | 100% | 100% | 0 |
| choice_sev | 12 | 100% | 100% | 0 |
| choice_food | 8 | 100% | 100% | 0 |
| choice_sports | 24 | 100% | 100% | 0 |
| choice_lang | 16 | 100% | 100% | 0 |
| score_sev | 20 | 100% | 100% | 0 |
| **score_urg** | 20 | **100%** | 80.0% | **+20.0** |
| multi_rag | 16 | 96.9% | **100%** | −3.1 |

---

## 4. 한 줄 해석

| 구간 | 승자 | 메모 |
|------|------|------|
| 전체 / KO / EN | **SolarMini4** | field_acc·noul·score |
| noul_syn, noul_ko, score_urg | **SolarMini4** | Jev가 과소/과대 칼라브레이션 |
| choice 대부분 | 동률 ~100% | game만 Jev +1건 |
| noul_pad, multi_rag | Jev 근소 | Solar 소수 overshoot |

