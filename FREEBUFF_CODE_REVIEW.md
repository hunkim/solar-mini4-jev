# FREEBUFF_CODE_REVIEW — Jev System One request-shape compatibility

**대상 저장소**: this repo  
**검토자**: Buffy (Freebuff coding agent)  
**실행 모델 확인**: freebuffModel = **Solar Pro 4** (이 세션의 실행 모델)  
**리뷰 범위**: compat.py, server.py(Pydantic Noul/Choice/Score 스키마), engine.py(instructions_text 사용부), tests/test_request_compat.py, docs/llms.txt  
**기준 OpenAPI**: TypeSafe Jev System One — NoulCriteria.true/false, instructions 등이 `string|object|array|null`을 허용  
**컨텍스트 요약**: 이전 engine.py는 list/dict instructions에 `.strip()`을 호출해 `AttributeError`로 502가 발생하던 문제를 수정했고, 현재는 compat.py에서 정규화/평면화 후 사용한다.

---

## 1) 전체 코드 리뷰 요약

### 1-1. 호환성 확인 (TypeSafe OpenAPI 대비)
- **대체로 잘 맞음**. compat.py는 `instructions_text()`/`description_text()`/`legend_value()`로 `string|object|array|null`을 받아들이고, server.py는 `FlexibleText = Union[str, dict[str, Any], list[Any], None]`로 같은 분포를 Pydantic union으로 받고 있다(서버 스키마는 `extra='allow'`도 유지).  
- `NoulCriteria.true/false`도 `FlexibleText`로 설정해 중첩 객체/배열/문자열을 허용한다.
- 테스트(test_request_compat.py)는 실제 첨부 payload(fd399..., a09e..., 9e3a...)를 Pydantic 검증에 통과시키며, 중첩 기준(true=object, false=array 등)이 엔진까지 도달하는지 mocked integration test로 확인한다.

### 1-2. 이전 크래시 재발 방지
- `compat.py: instructions_text()`는 `str`, `list`, `dict`, `None`, 그 외 fallback `str(...)`를 분기 처리하고, `.strip()`을 string에만 쓴다. 따라서 **list/dict instructions에서 이전 스타일 AttributeError가 재발할 가능성은 낮다**.
- engine.py `_prompt()`는 `instructions_text()` 결과를 그대로 프롬프트에 사용하고, 재강화 문구(abstain/hallucin)를 덧붙일 때도 string임을 전제로 `+=` 한다. 이 흐름이 현재 구조상 안전하다.

### 1-3. 보안/식별자 관련
- **BYOK 키 처리 자체는 적절**. 서버 측 장기 저장 키가 없고, 요청 헤더에서 추출해 Upstage 호출에만 쓴다.  
- **명령어 인젝션 관점에서는 현재는 낮은 위험도**. 파이프라인은 LLM 호출 + JSON 파싱 + 수치 정규화 위주이고, OS 명령어 실행, shell, 템플릿 렌더링 같은 공격 표면은 코드에서 보이지 않는다.  
- **프롬프트 삽입(prompt injection) 관점**은 존재함. `state`와 `instructions`가 프롬프트에 그대로 들어가며, `state`가 클라이언트가 임의로 큰 JSON을 넣을 수 있다. 현재는 `_prompt()`가 `state`를 JSON 직렬화하거나 string로 쓰며, 특수 제어문자를 별도로 이스케이프하지 않는다. 악의적/방대한 state로 토큰 급증 또는 프롬프트 구조 혼란 가능성이 이론적으로 있다. (이 부분은 아래 P1/P2로 정리)

### 1-4. 유효성 검증(Validation) 갭
- **강otyp 안전 측면**: 요청 스키마 검증은 잘 되어 있다. 다만 엔진 내부에서는 Pydantic 모델을 거친 후에도 다시 `dict` 기반 로직(`q.get(...)`, `isinstance(...)`)으로 처리한다. Pydantic을 통과한 값이라면 괜찮지만, **기준(criteria) 값에 대한 심층 타입 검증은 거의 없다**. 예: `criteria`가 dict여도 그 내부의 모든 값이 `string|object|array|null`인지 검사하지 않는다. 현재 `FlexibleText` union이 서버 모델에 적용되어 있으므로 클라이언트 요청 단계에서는 허용 분포가 지켜지지만, 엔진 내부에서 criteria를 순회할 때 `description_text()`/`instructions_text()`가 방어적으로 처리하므로 크래시까지 이어지지는 않는다.
- **중요 갭 하나**: server.py에서 `ChoiceQuestion.criteria: dict[str, Any]`와 `ScoreQuestion.criteria: list[Any]`는 **nested flexible value의 분포를 강제하지 않는다**. 즉 기준은 dict/list라는 것만 보장하고, 그 안의 값(예: `{"label": ..., "description": ...}`, `[1, 2]`, `null`)이 OpenAPI 분포와 완전히 일치하는지는 검증하지 않는다. 현재 문서(docs/llms.txt)와 compat.py 주석에서는 nested shapes도 허용한다고 기술하고 있으므로, 의도적으로는 수용한 것으로 보인다. 다만 **최소 일관성 유지 관점에서는 dict/list 내부의 값도 동일한 flexible union으로 검증할지 검토 가치가 있다**.

### 1-5. 테스트 검토
- **좋음**: `InstructionsTextTests`, `DescriptionTextTests`는 flat/nested 혼합에 대한 회귀 커버리지 확보가 잘 되어 있다.  
- **좋음**: `PromptCompatTests`는 리스트/객체 instructions, 중첩 noul/choice/score criteria가 프롬프트 텍스트에 적절히 포함되는지 검증한다.  
- **좋음**: `ApiValidationTests`는 401/422 스키마와 mocked integration으로 nested 값이 엔진에 도달하는지 확인한다.  
- **덧붙일 수 있는 커버리지(강력 권장 P2)**:  
  - `score` criteria가 `list[Any]`로 비어 있을 때 422가 나는지 이미 확인됨.  
  - `noul.criteria`에 **배열이나 문자열**을 보냈을 때 422가 나는지 현재 `test_noul_criteria_string_rejected`는 문자열만 체크한다. `criteria: "bad"`가 아니라 `criteria: ["a"]`, `criteria: 123` 같은 형태도 명시적으로 테스트하면 더 안전하다.  
  - state/instructions에 매우 큰 payload를 넣었을 때의 동작(한도, 로그, 오류)은 별도 테스트나 문서가 없다.

---

## 2) P0 / P1 / P2 (파일:라인)

### P0 — 즉시 수정이 필요한 명확한 버그
- **현재 코드만으로는 명확한 P0 버그를 찾지 못함**. 이전에 보고된 `strip()` AttributeError 계열은 compat.py 분기 처리로 재발 가능성이 낮고, 테스트도 이를 커버한다.  
- 현재 상태에서 **서비스 중단/보안 침해를 바로 유발한다고 볼 수 있는 코드 결함은 식별되지 않았다**.

### P1 — 공격 표면/안정성/정합성에 영향을 주는 중간 위험
1. **P1-1. `engine.py: _prompt()`에서 state/instructions의 큰 값 또는 비정상 값에 대한 가드 부족**  
   - `state`가 클 경우 JSON 직렬화 문자열이 커져 프롬프트 토큰 급증 가능.  
   - 위치: `engine.py`의 `_prompt` 함수 전체(특히 `state_s` 생성부와 `parts` 누적부).  
   - 권장: 실용적인 최대 길이/크기 제한 또는 truncate 정책, 과도한 payload에 대한 명확한 400/413 거절, 로그 기록.

2. **P1-2. `engine.py: _heuristic_overrides()` 및 `_lang_override()`가 `instructions_text()`를 여러 차례 호출해, 동일한 instructions를 반복 평면화할 수 있음**  
   - 경로 자체는 안전하지만, instructions가 매우 큰 객체/배열이면 필터/키워드 검사 구간마다 동일 평면화가 반복될 수 있어 CPU 비용 증가 가능.  
   - 위치: `engine.py` 내 `_lang_override`, `_heuristic_overrides`에서 `instructions_text(q.get("instructions"))` 호출부들.  
   - 권장: question당 instructions_text 결과를 한 번 캐싱하거나, 최소한 큰 payload에서 비용이 급증하지 않도록 점검.

3. **P1-3. `engine.py: _normalize_answers()`의 score 점수 추론 로직에서 문자열 키를 정수처럼 다루는 부분**  
   - `probs.get(str(i)) or probs.get(i)` 패턴은 방어적이지만, `int(k)` 기반의 기댓값 계산(`sum(int(k) * v ...)`)은 키가 순수 정수가 아닐 때 예외 가능성이 남아 있다.  
   - 위치: `engine.py` `_normalize_answers` score 분기.  
   - 권장: 실제 운영에서 키가 비정수 문자열로 들어올 가능성을 고려해 방어 코드/테스트 보강.

### P2 — 문서, 테스트, 유지보수성, 경미한 정합성 개선
1. **P2-1. `server.py: ChoiceQuestion.criteria` / `ScoreQuestion.criteria` 내부 값의 flexible 분포 미검증**  
   - 위치: `server.py` ChoiceQuestion, ScoreQuestion 클래스 정의부.  
   - 권장: criteria 안의 값도 TypeSafe 분포(string|object|array|null)와 정합하도록 검증할지 결정. 현재 동작을 유지하더라도 주석/문서에 의도를 명시.

2. **P2-2. `docs/llms.txt`에 호환 예시와 실제 요청 스키마 불일치 가능성**  
   - 문서에는 `options`, `levels` 같은 비표준 필드가 예시에 보임. 현재 서버 스키마는 `criteria` 중심이므로, 문서를 보고 보낸 요청이 422가 될 수 있음.  
   - 위치: `docs/llms.txt` 예제 섹션.  
   - 권장: 문서를 실제 server.py 스키마와 맞춰 정리.

3. **P2-3. 테스트 보강: noul.criteria에 배열/숫자/객체-아닌-문자열 외 형태 거부 확인**  
   - 위치: `tests/test_request_compat.py` `SystemOneRequestTests` / `QuestionSchemaTests`.  
   - 권장: `criteria: ["a"]`, `criteria: 123`, `criteria: null` 등이 스키마에 따라 어떻게 처리되는지 명시 테스트.

4. **P2-4. `_prompt()` 및 엔진 진입부에서 state 유형/크기 문서화 및 경계 동작 명시**  
   - 위치: `engine.py` `system_one` 및 `_prompt`.  
   - 권장: 예외 발생 시 502로 묻히지 않도록 경계 조건(너무 큰 state, 비JSON state 직렬화 문제 등)을 문서화하거나 처리.

5. **P2-5. `docs/llms.txt`와 `server.py` 응답 필드 표기 정합성**  
   - 문서에서는 score 응답에 `legend`가 안 보이는 예시도 있고, 실제 engine.py는 legend를 넣는다. 문서와 실제 응답 형태가 어긋나면 클라이언트 파싱에 혼동이 생길 수 있음.  
   - 위치: `docs/llms.txt` example responses.

---

## 3) 결론 및 권고

- **이 변경셋의 핵심은 regressions 방지와 request-shape 호환성 확보**이며, 그 목적은 compat.py + 테스트 + 서버 스키마로 대체로 달성되었다고 본다.  
- **P0로 분류할 명백한 버그는 현재 코드에서는 확인되지 않았다**.  
- 다만 **프롬프트로 주입되는 state/instructions의 크기/비정상 값에 대한 경계 방어**와 **criteria 내부 값의 분포 정합성**, 그리고 **문서-스키마 불일치**는 P1/P2로 정리할 가치가 충분하다.  
- 지금 단계에서는 애플리케이션 코드를 크게 바꾸기보다 **위 findings를 문서화하고, 필요한 경우 P2 수준의 테스트/문서 보강을 먼저 진행**하는 방향이 적절하다.

---

*본 리뷰는 제공된 구현 파일과 테스트, 문서를 기준으로 한 정적 검토이며, 실제 런타임 공격/성능 테스트가 병행되지 않았으므로 운영 환경에 반영 전 필요시 추가 검증이 권장된다.*


---

## 5) 재리뷰 (follow-up delta only)

검토 대상: `server.py`(`ChoiceQuestion.criteria`, `ScoreQuestion.criteria`), `engine.py` `_normalize_answers` score 분기(`int(k)` 방어), `tests/test_request_compat.py`(추가 거부/허용 테스트).

- **server.py delta**: `ChoiceQuestion.criteria`가 `dict[str, FlexibleText]`로, `ScoreQuestion.criteria`가 `list[ScoreLevel]`로 좁혀졌고, 이는 TypeSafe의 criteria 값 분포(string|object|array|null / score item은 string|object|array)와 정합성이 더 좋아짐. 기존 flexible 객체/배열/문자열 기준은 여전히 통과하고, number/bool 같은 비분포 값이 스키메 단계에서 더 일찍 걸러짐.
- **engine.py delta**: score 점수 계산에서 비정수 키(`int(k)` 실패)를 마주칠 때 예외가 아니라 skip 하도록 변경되어,운용사 응답 스키마/키 변형에 대한 방어성이 올라감.
- **tests delta**: noul.criteria array/number 거부, null 허용, choice criteria 내 non-flexible scalar(number) 거부가 명시적 테스트로 추가되어, 스키마 강화의 회귀 방지 커버리지가 보완됨.

**결론**: 이번 delta에 새 P0/P1은 식별되지 않음. 기존 문서 기준(P1-1 payload 경계, P1-2 반복 평면화 비용)은 여전히 남아 있지만, 이번 작업은 그 범위를 벗어나므로 보류로 볼 수 있음. pytest 통과 및 기존 compat/프롬프트 회귀 커버리지도 유지됨.

### 재리뷰 OK

- 범위(dserver.py score/choice criteria 타입 강화 + engine.py score int(k) 방어 + tests 보강)만 보면 **새 버그 없음, 새 P0/P1 없음**.
- P0 조건(서비스 중단/직접 보안 침해/명확한 크래시 재발)이 delta에서 나타나지 않으므로 **애플리케이션 코드 추가 변경 불필요**.
- 필요하면 다음 단계에서 P1-1/P1-2 또는 문서 정합성(P2-2/P2-5)을 별도 작업으로 분리 가능.
