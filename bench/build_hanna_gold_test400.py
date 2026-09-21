#!/usr/bin/env python3
"""Build Hanna gold for cases_test400.json from HANNA_GOLD_RUBRIC.md principles.

Offline, no API. Labels from state + questions only (id hints = weak priors).
Does NOT read gold_jev_*.json.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

BENCH = Path(__file__).resolve().parent
CASES = BENCH / "cases_test400.json"
OUT = BENCH / "gold_hanna_test400.json"
MODEL = "hanna-rubric-v1"


def _norm(s: str) -> str:
    return (s or "").lower()


def _has_any(text: str, needles: list[str]) -> bool:
    t = _norm(text)
    return any(_norm(n) in t for n in needles)


def _id_prior(cid: str) -> str | None:
    """Weak prior from id: 'yes' | 'no' | None."""
    if re.search(r"_no_\d|_syn_no_|_pad_(1[3-6]|$)", cid):
        # pad 13-16 are cosmetic in generator; also catch *_no_*
        pass
    if "_syn_no_" in cid or re.search(r"noul_no_", cid) or re.search(r"_ko_(1[3-9]|20)\b", cid):
        return "no"
    if "_syn_yes_" in cid or re.search(r"noul_yes_", cid) or re.search(r"_ko_([1-9]|1[0-2])\b", cid):
        return "yes"
    # pads: 1-12 and 17-28 are protective; 13-16 cosmetic
    m = re.search(r"noul_pad_(\d+)", cid)
    if m:
        n = int(m.group(1))
        n = ((n - 1) % 16) + 1  # 17->1 pattern in generator
        return "no" if 13 <= n <= 16 else "yes"
    return None


# ---------------------------------------------------------------------------
# noul
# ---------------------------------------------------------------------------

COSMETIC = [
    "prettier", "emote", "color", "colors", "trash", "pickup", "pdf", "download",
    "pipette", "grafana", "theme", "cilantro", "coffee", "lunch", "widget", "rename",
    "larger-print", "nachos", "jalapeño", "jalapenos", "annual report", "icon",
    "splash-screen", "font weight", "pothole map", "sticky notes", "visitor badge",
    "feature flag", "pastel", "salad bar", "csv", "sticker", "recycling schedule",
    "address change", "notebook section", "runbook markdown", "tray label",
    "led bulb", "nacho", "cover photo", "crop", "legend font", "palette suggestion",
    "leaf collection", "policy jacket",
    # KO
    "아이콘", "색을 바꾸", "응원봉", "쓰레기 수거", "약관 pdf", "피펫", "그라파나",
    "고수를", "커피", "점심", "대시보드",
]

LIFE_SAFETY = [
    "injured", "injury", "flames", "active fire", "no pulse", "aed", "oxygen", "o2 at 16",
    "o2 at 16%", "산소농도 16", "산소가 16", "confined-space", "밀폐공간",
    "structural collapse", "cave-in", "deck collapse",
    "evacuate bay", "section evacuation", "pyrotechnics", "ignited",
    "unresponsive athlete", "심정지", "부상자", "emergency rescue",
]

MAJOR_OUTAGE = [
    "42k customers dark", "cascading feeder", "packet loss 40%", "bgp sessions down",
    "national packet", "fiber cut", "sev-1", "voice+data", "asr collapsed",
    "sip trunk", "변전소 과열", "피더가 동시에", "bgp가 다중", "백본 라우터",
]

PATHOGEN_HOLD = [
    "listeria", "pcr positive", "allergen mislabel", "peanut oil", "nut-free",
    "consumer recall", "리스테리아", "생산을 멈추", "allergen swab positive",
]

SOFT_FRAUD_CHEAT = [
    "memory injector", "wallhack", "soft-tissue", "identical soft-tissue",
    "mass-ban", "ranked queues", "메모리 핵", "랭크 큐", "연조직",
    "anti-cheat flagged",
]

MID_PROTECTIVE = [
    "n-1", "de-energization review", "shed non-critical", "bridge strain",
    "sinkhole", "freezer", "quarantine", "cold room", "poultry", "ss7",
    "scrub", "vault", "humidity", "78% rh", "rh above", "sprinkler", "microfilm",
    "ransomware", "cyber", "vibration", "egress assessment", "privacy breach",
    "ssn", "caseworker", "storm surge", "cat desk", "hail fnol", "payment webhook",
    "overlay leaked", "integrity", "hydrant", "incubator", "ran site", "battery below",
    "digitization scanner", "lightning delay", "donor crm", "islanding", "microgrid",
    "tournament bracket", "metal detector", "fall-protection", "flash-flood",
    "phishing", "subaward", "wire of", "grant portal exposed", "water main",
    "gas odor", "pm2.5", "landslide", "tower crane", "scaffold", "flood sensor",
    "습도", "서고", "관중석", "구조 센서", "보조금", "유출", "냉동고", "창고 화재",
    "가스 냄새", "하천", "대피",
]


def label_noul(state: str, instructions: str, cid: str) -> float:
    text = f"{state}\n{instructions}"
    prior = _id_prior(cid)

    # State-driven cosmetic mismatch (even if question is dramatic)
    if _has_any(state, COSMETIC) and not _has_any(state, LIFE_SAFETY + MAJOR_OUTAGE + PATHOGEN_HOLD + MID_PROTECTIVE + SOFT_FRAUD_CHEAT):
        return 0.10

    # Explicit no-prior with weak cosmetic/routine language
    if prior == "no" and _has_any(state, COSMETIC + [
        "asks", "wants", "intern", "volunteer", "fan asks", "gamer wants",
        "물어", "문의", "바꾸고", "원합니다",
    ]):
        return 0.10

    # Life-safety / catastrophic
    if _has_any(text, LIFE_SAFETY) or _has_any(state, [
        "autoclave interlock", "biohazard load", "door opened mid-cycle",
        "coolant leak", "high-voltage rack", "crane load cell", "scaffold tie-in",
        "excavation cave-in", "player collapsed", "pyrotechnics",
    ]):
        # warehouse fire + injured / FNOL flames
        return 0.92

    if _has_any(state, PATHOGEN_HOLD) or _has_any(text, ["production halt and product hold", "initiate consumer recall"]):
        return 0.90

    if _has_any(state, [
        "cascading trips", "42k customers", "packet loss 40%",
        "fiber cut on metro", "sip trunk asr", "asr collapsed",
        "bgp sessions down", "national packet", "변전소 과열", "bgp가 다중", "백본 라우터",
    ]) or (_has_any(state, MAJOR_OUTAGE) and not _has_any(state, ["ss7"])):
        return 0.88

    # SS7 scrub — protective mid-high (not life-safety)
    if _has_any(state, ["ss7", "signaling storm", "signaling firewall"]):
        return 0.78

    # Gas odor / flood evacuation / wildfire perimeter / landslide — high
    if _has_any(state, [
        "gas odor", "가스 냄새", "evacuation alerts", "shelter-in-place",
        "wildfire perimeter", "flash-flood", "river stage", "landslide",
        "highway closure", "대피 경보", "주민 대피",
    ]):
        return 0.86

    # Soft fraud / anti-cheat
    if _has_any(state, SOFT_FRAUD_CHEAT):
        if _has_any(state, ["wallhack", "memory injector", "메모리 핵"]):
            return 0.48
        if _has_any(state, ["soft-tissue", "siu"]):
            return 0.48
        return 0.50

    # Esports overlay / payments / integrity mid
    if _has_any(state, ["overlay leaked", "spectator overlay", "payment webhook", "battle-pass"]):
        return 0.65

    # Archives / RH / sprinkler / scanner — mid
    if _has_any(state, [
        "vault", "humidity", "rh", "sprinkler", "microfilm", "parchment",
        "digitization scanner", "conservat", "서고", "습도",
    ]):
        return 0.64

    # Freezer / incubator / cold room — mid investigate
    if _has_any(state, [
        "freezer", "incubator", "cold room", "samples rose", "qa quarantine",
        "cold chain", "냉동고", "시료",
    ]):
        return 0.66

    # Bridge strain / stadium vibration assessment — mid (investigate-first)
    if _has_any(state, ["bridge strain", "vibration anomaly", "egress assessment", "관중석 구조"]):
        return 0.68

    # CAT staffing / hail spike / storm surge — mid
    if _has_any(state, ["cat desk", "storm surge", "hail fnol", "cyber claim", "cyber cat", "보험"]):
        if _has_any(state, ["warehouse fire", "화재", "injured"]):
            return 0.90
        return 0.68

    # Privacy / phishing wires — mid-high
    if _has_any(state, [
        "privacy", "ssn", "ein", "phishing", "wire of", "subaward", "caseworker",
        "donor crm", "minors", "유출", "주민번호", "보조금 포털",
    ]):
        if _has_any(state, ["$1.8m", "1.8m", "$410k", "$270k", "redirected"]):
            return 0.82
        return 0.72

    # Construction trench / hydrant / lightning clear field
    if _has_any(state, ["hydrant shear", "lightning delay", "cave-in", "trench"]):
        return 0.80

    # DER islanding / RAN battery / tournament API — mid
    if _has_any(state, ["islanding", "microgrid", "ran site", "battery below", "tournament bracket", "5xx"]):
        return 0.68

    # Allergen swab / metal detector — mid-high protective
    if _has_any(state, ["allergen swab", "metal detector", "re-sanitation", "line hold"]):
        return 0.72

    # N-1 / transformer oil / water main — mid-high
    if _has_any(state, ["n-1", "transformer oil", "water main", "sinkhole", "gas relay"]):
        return 0.74

    # Fall-protection harness failures
    if _has_any(state, ["fall-protection", "harness"]):
        return 0.78

    # Default protective yes prior
    if prior == "yes":
        return 0.70
    if prior == "no":
        return 0.10

    # Fallback: if instructions ask protective and state has urgency keywords
    if _has_any(instructions, ["urgent", "immediate", "must", "should", "required", "즉시", "해야"]):
        if _has_any(state, MID_PROTECTIVE):
            return 0.68
    return 0.50


# ---------------------------------------------------------------------------
# choice
# ---------------------------------------------------------------------------

def _pick_by_keywords(state: str, criteria: dict[str, str], rules: list[tuple[str, list[str]]]) -> str | None:
    for label, kws in rules:
        if label in criteria and _has_any(state, kws):
            return label
    return None


def label_choice(state: str, q: dict) -> str:
    criteria = q.get("criteria") or {}
    keys = list(criteria.keys())

    # Language detect
    if set(keys) >= {"ko", "en", "ja", "zh"}:
        if re.search(r"[\u3040-\u30ff]", state):
            return "ja"
        if re.search(r"[\u4e00-\u9fff]", state) and not re.search(r"[\uac00-\ud7a3]", state):
            return "zh"
        if re.search(r"[\uac00-\ud7a3]", state):
            return "ko"
        return "en"

    # Severity labels
    if set(keys) >= {"sev1", "sev2", "sev3", "sev4"}:
        if _has_any(state, [
            "citywide", "national", "total failure", "전면", "bgp total", "mes 전면",
            "valve control lost", "광코어", "routing 전면",
        ]):
            return "sev1"
        if _has_any(state, ["typo", "1px", "오탈자", "misaligned", "copyright year", "faq footer"]):
            return "sev4"
        if _has_any(state, [
            "false-positive", "12%", "slow", "cache miss", "일부 피더", "우회",
            "redundant unit healthy", "one climate sensor", "neighbors still",
        ]):
            # limited / regional → sev3 per tuning (sev3 = mid in their criteria)
            # Check criteria descriptions
            return "sev3"
        if _has_any(state, ["elevated", "region only"]):
            return "sev3"
        return "sev2"

    # Intent
    if set(keys) >= {"emergency", "policy_question", "complaint", "praise"}:
        if _has_any(state, [
            "o2", "oxygen", "rescue", "vibration crossed red", "밀폐공간", "위험",
            "confined", "mid-game",
        ]):
            return "emergency"
        if _has_any(state, [
            "thank", "love", "brilliant", "훌륭", "감동", "praise", "so clear",
        ]):
            return "praise"
        if _has_any(state, [
            "furious", "unacceptable", "ignored", "화가", "미뤄", "banned me wrongly",
        ]):
            return "complaint"
        if _has_any(state, ["how do i", "what documents", "apply", "어디서", "신청"]):
            return "policy_question"
        return "policy_question"

    # Energy
    if "transmission" in criteria:
        hit = _pick_by_keywords(state, criteria, [
            ("transmission", ["345kv", "cascading", "intertie", "n-1", "선로", "breaker failure"]),
            ("der", ["battery", "inverter", "microgrid", "pv", "derms", "rooftop", "마이크로그리드", "soc"]),
            ("market", ["bid", "settlement", "lmp", "iso", "정산", "virtual bid"]),
            ("distribution", ["feeder", "meter", "transformer", "suburb", "변압기", "정전", "neighborhood"]),
        ])
        if hit:
            return hit
        return "distribution"

    # Game
    if "anticheat" in criteria:
        hit = _pick_by_keywords(state, criteria, [
            ("community", ["hate", "slur", "chat", "혐오", "도배", "raid"]),
            ("anticheat", ["cheat", "injector", "wallhack", "dma", "월핵", "ban", "vpn", "false ban"]),
            ("payments", ["charge", "wallet", "refund", "battle-pass", "결제", "환불", "duplicated"]),
            ("liveops", ["tournament", "bracket", "matchmaking", "mmr", "503", "대진표", "토너먼트"]),
        ])
        if hit:
            return hit
        return "liveops"

    # Municipal
    if "utilities" in criteria:
        hit = _pick_by_keywords(state, criteria, [
            ("utilities", ["water main", "gas odor", "상수", "가스", "flooding intersection", "manhole"]),
            ("streets", ["traffic signal", "pothole", "신호등", "highway", "stuck red"]),
            ("sanitation", ["dumping", "recycling", "debris", "폐기물", "missed recycling"]),
            ("parks", ["playground", "swing", "trail", "tree", "공원", "놀이터", "그네"]),
        ])
        if hit:
            return hit
        return "streets"

    # Insurance
    if "fnol" in criteria:
        hit = _pick_by_keywords(state, criteria, [
            ("cat", ["hurricane", "wildfire", "태풍", "landfall", "smoke damage", "wind claims", "폭증"]),
            ("siu", ["identical", "staging", "soft-tissue", "클리닉", "유사", "billing patterns"]),
            ("policy", ["cover", "endorsement", "특약", "보장", "explain rental", "sump-pump"]),
            ("fnol", ["collision", "deer", "claim", "추돌", "접수", "windshield", "rear-end"]),
        ])
        if hit:
            return hit
        return "fnol"

    # Biotech
    if "biosafety" in criteria:
        hit = _pick_by_keywords(state, criteria, [
            ("biosafety", ["autoclave", "biohazard", "needle stick", "exposure", "생물안전", "누출", "cabinet"]),
            ("facilities", ["freezer", "compressor", "coolant", "초저온", "냉동고", "alarm"]),
            ("informatics", ["lims", "fastq", "pipeline", "accession", "시퀀싱", "파이프라인", "data"]),
            ("qa", ["deviation", "capa", "lot", "assay", "로트", "일탈", "em fail"]),
        ])
        if hit:
            return hit
        return "qa"

    # Telecom
    if "ipcore" in criteria:
        hit = _pick_by_keywords(state, criteria, [
            ("field", ["fiber cut", "splice", "manhole", "truck", "광케이블", "절체", "현장"]),
            ("voice", ["sip", "ss7", "asr", "signaling", "호 완료"]),
            ("access", ["olt", "ont", "cpe", "pon", "가입자", "firmware brick"]),
            ("ipcore", ["bgp", "mpls", "core router", "packet", "lsp", "코어", "라우터"]),
        ])
        if hit:
            return hit
        return "ipcore"

    # Food
    if "qa_hold" in criteria:
        hit = _pick_by_keywords(state, criteria, [
            ("labeling", ["allergen", "peanut", "nut-free", "label", "lot code printer", "표시"]),
            ("shipping", ["reefer", "dock", "trailer", "warm air", "12c", "poultry load"]),
            ("sanitation", ["cip", "pest", "filler", "청소", "위생"]),
            ("qa_hold", ["listeria", "pcr", "metal detector", "hold", "reject"]),
        ])
        if hit:
            return hit
        return "qa_hold"

    # Sports
    if "ticketing" in criteria:
        hit = _pick_by_keywords(state, criteria, [
            ("safety", ["egress", "lightning", "collapse", "medical", "aed", "fire", "안전", "대피"]),
            ("ticketing", ["ticket", "scanner", "gate", "티켓"]),
            ("broadcast", ["overlay", "broadcast", "camera", "중계"]),
            ("hospitality", ["concession", "nacho", "hospitality", "vip"]),
        ])
        if hit:
            return hit
        # sports_pad all ticket scanner → ticketing
        if _has_any(state, ["ticket scanner", "gate"]):
            return "ticketing"
        return "safety"

    # Fallback: first criterion
    return keys[0] if keys else "unknown"


# ---------------------------------------------------------------------------
# score
# ---------------------------------------------------------------------------

def label_score(state: str, q: dict) -> float:
    text = state
    criteria = q.get("criteria") or []
    n = max(len(criteria) - 1, 4)  # usually 0..4

    # Catastrophic / drop-everything
    if _has_any(text, [
        "ransomware", "encrypting", "fiber cut", "50k", "bgp down", "national packet",
        "mes write path down", "all lines stopped", "scada 쓰기 전면", "valve",
        "autoclave interlock", "wildfire perimeter crossing", "funds moving",
        "payment rails failing globally", "sms failing for entire", "fnol intake rejects all",
        "ticketing scanners offline stadium-wide", "structural monitoring 쓰기 전면",
        "보조금 포털 결제가 모든", "법정 제출 마감", "냉동 식품 콜드체인 알람",
    ]):
        return 3.9

    # Major
    if _has_any(text, [
        "citywide", "most users", "double-writes", "reconciliation", "scada read-only",
        "submit fail", "전면 실패", "생산 중단",
    ]):
        return 3.2

    # Limited / few users / single sensor
    if _has_any(text, [
        "3 users", "one sensor", "rh logging silent", "few users",
        "sometime this season",
    ]):
        return 1.3

    # Mid / board demo / degraded many
    if _has_any(text, [
        "board demo", "tomorrow", "false positives", "~1%", "12%",
        "일부 피더", "갱신이 느림", "read-only for one",
    ]):
        return 2.3

    # Cosmetic / low urgency
    if _has_any(text, [
        "copyright", "1px", "2px", "font weight", "pastel", "emoji", "cover photo",
        "next month", "next sprint", "quiet-hours", "typo", "tooltip", "changelog tidy",
        "오탈자", "로고 정렬", "아이콘 색", "약간 연함", "학회 포스터", "차트 색",
        "wayfinding", "swing chain sometime", "help tooltip",
    ]):
        return 0.8

    # Default mid-low
    return 1.8


# ---------------------------------------------------------------------------
# multi RAG guard
# ---------------------------------------------------------------------------

def _split_rag(state: str) -> tuple[str, str, str]:
    q = c = a = ""
    m = re.search(
        r"QUESTION:\s*(.*?)\s*RETRIEVED CONTEXT:\s*(.*?)\s*MODEL ANSWER:\s*(.*)",
        state,
        re.S | re.I,
    )
    if m:
        q, c, a = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        # strip trailing markers
        a = re.sub(r"\[TEST[^\]]*\]\s*$", "", a).strip()
    return q, c, a


def _context_missing(ctx: str) -> bool:
    return _has_any(ctx, [
        "not stated", "not listed", "not disclosed", "not specified", "not described",
        "not permitted",  # careful
        "수치가 없다", "명시되어 있지", "없다", "confidential and not",
        "not in this excerpt", "not listed here", "not described in this excerpt",
    ])


def _answer_is_refusal(ans: str) -> bool:
    return _has_any(ans, [
        "i don't know", "not provided", "cannot determine", "missing from",
        "정보가 없", "확인할 수 없", "명시되어 있지 않",
    ])


def _hard_invent(ctx: str, ans: str) -> bool:
    """Material invent: novel person names, exact numbers, forever/always policy."""
    if _has_any(ans, ["forever", "permanently", "always free", "no exceptions", "영구", "영원히"]):
        if not _has_any(ctx, ["forever", "permanently", "always", "no exceptions"]):
            return True
    # Named person invent when context says confidential / not disclosed
    if re.search(r"\b(Dr\.|Director|Maya|Ortiz|Samuel|Rhee)\b", ans):
        if _has_any(ctx, ["confidential", "not disclosed", "not listed", "PI name is not"]):
            return True
    # Numeric invent: answer has number not in context
    ans_nums = set(re.findall(r"\d+(?:\.\d+)?", ans))
    ctx_nums = set(re.findall(r"\d+(?:\.\d+)?", ctx))
    # filter trivial
    novel = {n for n in ans_nums if n not in ctx_nums and n not in {"1", "2", "7"}}
    if novel and _context_missing(ctx):
        return True
    if novel and _has_any(ans, ["exactly", "minutes", "msu", "%", "days", "SOC", "상대습도"]):
        # if context has the same numbers, ok — already filtered
        if not novel.issubset(ctx_nums):
            # check if answer claims a specific value for missing limit
            if _context_missing(ctx):
                return True
    return False


def _faithful(ctx: str, ans: str) -> bool:
    if _answer_is_refusal(ans):
        return True
    # Soft check: key phrases from context appear in answer, no hard invent
    if _hard_invent(ctx, ans):
        return False
    # If context asserts a clear rule and answer agrees
    if not _context_missing(ctx):
        # answer shouldn't contradict with forever invent
        if _has_any(ans, ["forever", "permanently"]) and not _has_any(ctx, ["forever", "permanently"]):
            return False
        return True
    return False


def label_multi(state: str, questions: dict) -> dict:
    _q, ctx, ans = _split_rag(state)
    out = {}

    invent = _hard_invent(ctx, ans)
    refusal = _answer_is_refusal(ans)
    missing = _context_missing(ctx)
    faithful = _faithful(ctx, ans) and not invent

    # Soft overclaim: invent mild without forever/name — still treat as invent if novel number
    soft = False
    if not invent and not faithful and not refusal:
        soft = True

    if invent:
        grounded, hall, abstain, decision = 0.05, 0.95, 0.05, "block"
    elif refusal and missing:
        grounded, hall, abstain, decision = 0.90, 0.05, 0.90, "pass"
    elif faithful:
        grounded, hall, abstain, decision = 0.90, 0.05, 0.05, "pass"
    elif soft:
        grounded, hall, abstain, decision = 0.25, 0.70, 0.10, "rewrite"
    else:
        grounded, hall, abstain, decision = 0.50, 0.50, 0.20, "rewrite"

    for name, qq in questions.items():
        t = qq.get("type")
        if t == "noul":
            if name == "grounded":
                val = grounded
            elif name == "hallucinated":
                val = hall
            elif name == "abstain":
                val = abstain
            else:
                val = 0.5
            out[name] = {"type": "noul", "noul": round(val, 2)}
        elif t == "choice":
            out[name] = {"type": "choice", "choice": decision, "confidence": 0.85}
    return out


# ---------------------------------------------------------------------------
# per-case
# ---------------------------------------------------------------------------

def label_case(case: dict) -> dict:
    answers = {}
    kind = case.get("kind")
    state = case.get("state", "")
    cid = case.get("id", "")
    qs = case.get("questions") or {}

    if kind == "multi":
        return label_multi(state, qs)

    for name, q in qs.items():
        t = q.get("type")
        if t == "noul":
            v = label_noul(state, q.get("instructions", ""), cid)
            answers[name] = {"type": "noul", "noul": round(float(v), 2)}
        elif t == "choice":
            ch = label_choice(state, q)
            answers[name] = {"type": "choice", "choice": ch, "confidence": 0.85}
        elif t == "score":
            sc = label_score(state, q)
            # clamp to criteria range
            crit = q.get("criteria") or []
            hi = float(max(len(crit) - 1, 4))
            sc = max(0.0, min(hi, sc))
            answers[name] = {"type": "score", "score": round(float(sc), 2)}
    return answers


def main():
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    gold = {}
    band = {"cat": 0, "mid": 0, "soft": 0, "low": 0, "other": 0}
    for c in cases:
        ans = label_case(c)
        gold[str(c["idx"])] = {"model": MODEL, "answers": ans, "latency_s": 0}
        if c["kind"] == "noul":
            v = list(ans.values())[0]["noul"]
            if v >= 0.85:
                band["cat"] += 1
            elif v >= 0.55:
                band["mid"] += 1
            elif v >= 0.40:
                band["soft"] += 1
            elif v <= 0.20:
                band["low"] += 1
            else:
                band["other"] += 1
    OUT.write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT} n={len(gold)} noul_bands={band}", flush=True)


if __name__ == "__main__":
    main()
