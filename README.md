# solar-mini4-jev

Upstage **Solar Mini4**를 TypeSafe Jev System One API 형태로 감싼 드롭인 wrapper.

```
POST /v1/systemone
{ "model": "solar-mini4-jev", "state": "...", "questions": { ... } }
```

지원 질문 타입: `noul` | `choice` | `score` (Jev와 동일 스키마).

## Official gold: Grok 4.6 Judge

**Jev는 gold가 아닙니다.** Jev도 비교 대상 모델입니다.  
공식 채점 기준은 **Grok 4.6 Judge** 루브릭 라벨입니다 (`bench/gold_grok46_judge_test400.json`).

## Results at a glance

**독립 판정자(Grok 4.6 Judge) 기준, Solar Mini4가 Jev보다 더 자주 맞았다.**
448개 답변 필드 중 Solar Mini4는 6개, Jev는 26개를 틀렸다. 판정이 갈린 30필드에서는 Solar 25 : Jev 5.

![Solar Mini4 vs Jev · Grok 4.6 Judge 스코어카드](bench/infographic_grok46_judge.png)

Jev의 오답은 두 패턴(생명·안전 상황 저평가, 사소한 일 과잉 긴급도)에 몰려 있고, Solar의 오답은 대부분 "너무 신중한" 방향이다.

![지표별 정확도와 갈리는 케이스](bench/infographic_grok46_judge_detail.png)

Interactive scorecard: [view on GitHub Pages](https://hunkim.github.io/solar-mini4-jev/) · [source](docs/index.html)

### test400 @ Grok 4.6 Judge (`solar-mini4` → `solar-mini4-260922`)

| model | field_acc | noul≤0.25 | sign@0.5 | choice | score≤1 | miss | avg latency |
|-------|----------:|----------:|---------:|-------:|--------:|-----:|------------:|
| **Solar Mini4** | **98.7%** | **97.6%** | **98.8%** | **100%** | **100%** | **6** | 1.41s |
| Jev | 94.2% | 95.2% | 92.3% | 100% | 85.0% | 26 | **0.38s** |

Language field_acc:

| | KO (n=70) | EN (n=330) |
|--|----------:|-----------:|
| **Solar Mini4** | **98.8%** | **98.6%** |
| Jev | 93.9% | 94.3% |

**Takeaway:** Judge 품질은 Solar Mini4, 속도는 Jev (~3.7×).

## Quick start

```bash
export UPSTAGE_API_KEY=...
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8080
```

```python
from engine import system_one

out = system_one(
    state="결제 성공률이 12%로 떨어졌다.",
    questions={"urgent": {"type": "noul", "instructions": "온콜을 즉시 호출해야 하는가?"}},
)
print(out["answers"])
```

환경변수:
- `UPSTAGE_API_KEY` — Solar Mini4 (필수). `solar-mini4`는 현재 `solar-mini4-260922`로 resolve.
- `TYPESAFE_API_KEY` — 벤치마크용 실제 Jev 호출 시에만 (`jev_ref.py`)
- `SOLAR_MINI_MODEL` — 선택적 모델 오버라이드

## Layout

| path | 설명 |
|------|------|
| `engine.py` | Solar Mini4 + Jev-호환 휴리스틱 |
| `server.py` | FastAPI `POST /v1/systemone` |
| `jev_ref.py` | 실제 Jev 클라이언트 (비교용) |
| `bench/gold_grok46_judge_test400.json` | **공식 gold** (Grok 4.6 Judge) |
| `bench/gold_jev_test400.json` | Jev 응답 스냅샷 (비교 모델) |
| `bench/results_test400_rerun_260922.jsonl` | Solar Mini4 재채점 결과 |
| `docs/index.html` | 인터랙티브 스코어카드 (GitHub Pages) |
| `bench/infographic_grok46_judge*.png` | README용 스코어카드 PNG |

## License

실험/연구 코드. API 키는 커밋하지 마세요.
