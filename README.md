# solar-mini4-jev

Upstage **Solar Mini4**를 [TypeSafe Jev](https://typesafe.ai) System One API 형태로 감싼 드롭인 wrapper.

```
POST /v1/systemone
{ "model": "solar-mini4-jev", "state": "...", "questions": { ... } }
```

지원 질문 타입: `noul` | `choice` | `score` (Jev와 동일 스키마).

## Quick start

```bash
export UPSTAGE_API_KEY=...
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8080
```

Python에서 바로:

```python
from engine import system_one

out = system_one(
    state="결제 성공률이 12%로 떨어졌다.",
    questions={"urgent": {"type": "noul", "instructions": "온콜을 즉시 호출해야 하는가?"}},
)
print(out["answers"])
```

환경변수:
- `UPSTAGE_API_KEY` — Solar Mini4 (필수)
- `TYPESAFE_API_KEY` — 벤치마크용 실제 Jev 호출 시에만 필요 (`jev_ref.py`)

## Layout

| path | 설명 |
|------|------|
| `engine.py` | Solar Mini4 + Jev-호환 휴리스틱 / 프롬프트 |
| `server.py` | FastAPI `POST /v1/systemone` |
| `jev_ref.py` | 실제 TypeSafe Jev 클라이언트 (gold 고정용) |
| `bench/` | 케이스 · frozen gold · 결과 · 인포그래픽 |

## Benchmark (Hanna golden set)

**공식 golden**은 Jev가 아니라 Hanna rubric (`bench/gold_hanna_test400.json`)입니다.
test400에서 Solar Mini4 wrapper vs Jev를 같은 golden으로 채점:

| 모델 | noul≤0.25 | sign@0.5 | choice | score≤1 | field_acc | avg latency |
|------|----------:|---------:|-------:|--------:|----------:|------------:|
| **Solar Mini4** | **97.2%** | **98.8%** | 99.4% | **100%** | **98.2%** | 1.77s |
| Jev | 95.1% | 92.3% | **100%** | 89.2% | 94.6% | **0.38s** |

언어별 field_acc:

| | KO (n=70) | EN (n=330) |
|--|----------:|-----------:|
| Solar Mini4 | **98.8%** | **98.1%** |
| Jev | 95.0% | 94.5% |

분야별 하이라이트 (Solar − Jev, field_acc pp): `score_urg +20`, `noul_syn +15.6`, `noul_ko +10` / Jev 우위: `choice_game −8.3`, `noul_pad −7.4`.

자세한 표·인포그래픽:
- [`bench/COMPARISON_HANNA_GOLDEN.md`](bench/COMPARISON_HANNA_GOLDEN.md)
- [`bench/infographic_hanna_golden.html`](bench/infographic_hanna_golden.html)
- [`bench/HANNA_GOLD_RUBRIC.md`](bench/HANNA_GOLD_RUBRIC.md)

### 재현

```bash
# train/test 케이스 생성 · Jev gold freeze · Solar 채점 스크립트는 bench/ 참고
python bench/score_vs_hanna_gold.py
```

## License

개인/연구 실험 코드. API 키는 커밋하지 마세요.
