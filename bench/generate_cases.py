#!/usr/bin/env python3
"""Generate ~200 Jev-style decision cases for Solar-Mini4 vs Jev comparison."""
from __future__ import annotations

import json
from pathlib import Path

CASES: list[dict] = []


def add(cid: str, kind: str, state: str, questions: dict):
    CASES.append({"id": cid, "kind": kind, "state": state, "questions": questions})


# --- noul: clear yes/no ---
noul_yes = [
    ("The password reset email bounced and the user cannot log in for 2 hours.", "Is this an authentication outage worth paging on-call?"),
    ("A production payment webhook has failed for 40 minutes; money is not settling.", "Is immediate engineering escalation required?"),
    ("Customer says their card was charged twice and shows two bank lines.", "Is a refund investigation warranted?"),
    ("Server CPU is at 98% for 15 minutes and error rate jumped 10x.", "Should we page the SRE team now?"),
    ("User pasted an API secret in a public GitHub issue.", "Should we rotate the secret immediately?"),
]
noul_no = [
    ("User asks how to change their profile picture color.", "Is this a P0 production incident?"),
    ("Newsletter subscriber wants to update their email address.", "Should we escalate to the CEO?"),
    ("Customer asks for documentation link for the SDK.", "Is a security incident response needed?"),
    ("A blog comment says the product logo looks outdated.", "Should engineering stop the release train?"),
    ("User likes a tweet about our product.", "Is legal action required?"),
]
for i, (s, q) in enumerate(noul_yes, 1):
    add(f"noul_yes_{i}", "noul", s, {"yes": {"type": "noul", "instructions": q}})
for i, (s, q) in enumerate(noul_no, 1):
    add(f"noul_no_{i}", "noul", s, {"yes": {"type": "noul", "instructions": q}})

# expand noul with Korean + English variants
ko_noul = [
    ("고객이 같은 주문에 두 번 결제됐다고 항의하며 오늘 환불을 요구한다.", "지금 상담원을 즉시 에스컬레이션해야 하는가?", True),
    ("사용자가 비밀번호를 잊었다고 문의했다.", "보안 사고 대응팀을 호출해야 하는가?", False),
    ("프로덕션 DB 디스크가 5분 내 가득 찰 예정이다.", "즉시 장애 대응이 필요한가?", True),
    ("마케팅 팀이 새 배너 색상을 바꾸고 싶어한다.", "법적 검토가 즉시 필요한가?", False),
    ("공개 채널에 AWS 키가 노출된 것이 확인됐다.", "키를 즉시 폐기·재발급해야 하는가?", True),
    ("고객이 FAQ 링크를 요청했다.", "CTO에게 즉시 보고해야 하는가?", False),
    ("결제 성공률이 정상 99%에서 12%로 떨어졌다.", "페이먼트 온콜을 호출해야 하는가?", True),
    ("앱 아이콘을 약간 더 둥글게 바꾸고 싶다.", "핫픽스 배포가 필요한가?", False),
    ("랜섬웨어 협박 메일이 운영 메일로 왔다.", "보안 인시던트로 분류해야 하는가?", True),
    ("사용자가 다크모드 지원 여부를 물었다.", "데이터센터를 차단해야 하는가?", False),
]
for i, (s, q, expect_high) in enumerate(ko_noul, 1):
    add(f"noul_ko_{i}", "noul", s, {"yes": {"type": "noul", "instructions": q}})
    # store expected band in meta via id prefix already; bench will use Jev as gold

# more synthetic noul
templates_yes = [
    "API latency p99 exceeded 5s for {n} minutes with rising 5xx.",
    "Data pipeline stopped writing for {n} minutes; dashboards are stale.",
    "Fraud model flagged {n} suspicious refunds in 10 minutes.",
    "Kubernetes node NotReady count rose to {n}; pods are pending.",
    "SSL certificate expires in {n} hours on the public domain.",
]
templates_no = [
    "Intern asks how to set up local docker for day {n}.",
    "Design wants to A/B test button copy for experiment #{n}.",
    "Sales asks for one-pager PDF version {n}.",
    "User requests feature upvote on idea #{n}.",
    "Someone thanked support agent #{n} in chat.",
]
for i, t in enumerate(templates_yes, 1):
    for n in (3, 12, 30):
        add(f"noul_syn_yes_{i}_{n}", "noul", t.format(n=n),
            {"yes": {"type": "noul", "instructions": "Is this an urgent production issue requiring immediate action?"}})
for i, t in enumerate(templates_no, 1):
    for n in (1, 7, 42):
        add(f"noul_syn_no_{i}_{n}", "noul", t.format(n=n),
            {"yes": {"type": "noul", "instructions": "Is this an urgent production issue requiring immediate action?"}})

# --- choice routing ---
teams = {
    "billing": "payments, invoices, refunds, charges",
    "technical": "bugs, crashes, API errors, performance",
    "sales": "pricing, upgrades, enterprise quotes",
    "account": "login, password, email change, MFA",
}
routing = [
    ("I was charged twice this month on Visa.", "billing"),
    ("The /v1/search endpoint returns 500 intermittently.", "technical"),
    ("We want an enterprise plan for 200 seats.", "sales"),
    ("I cannot reset my password; emails never arrive.", "account"),
    ("App freezes on iOS when opening settings.", "technical"),
    ("Please refund the accidental Pro upgrade.", "billing"),
    ("What discounts do you offer for annual billing?", "sales"),
    ("Enable MFA for my workspace admin.", "account"),
    ("Invoice PDF is missing VAT ID.", "billing"),
    ("SDK throws timeout after 30s on file upload.", "technical"),
    ("두 번 결제됐어요. 환불해주세요.", "billing"),
    ("로그인이 안 되고 인증 메일이 안 와요.", "account"),
    ("엔터프라이즈 견적 가능할까요?", "sales"),
    ("API가 간헐적으로 502를 냅니다.", "technical"),
    ("요금제 업그레이드 비용이 궁금합니다.", "sales"),
]
for i, (s, _) in enumerate(routing, 1):
    add(f"choice_route_{i}", "choice", s, {
        "team": {"type": "choice", "instructions": "Which support team should handle this ticket?", "criteria": teams}
    })

# language / topic choice
langs = {"ko": "Korean", "en": "English", "ja": "Japanese", "zh": "Chinese"}
for i, (text, _) in enumerate([
    ("안녕하세요, 환불 문의드립니다.", "ko"),
    ("Hello, I need a refund please.", "en"),
    ("こんにちは、返金をお願いします。", "ja"),
    ("你好，我想申请退款。", "zh"),
    ("결제 영수증 좀 보내주세요.", "ko"),
    ("Can you resend the invoice?", "en"),
]*3, 1):
    add(f"choice_lang_{i}", "choice", text, {
        "lang": {"type": "choice", "instructions": "Primary language of the message?", "criteria": langs}
    })

# sentiment / intent
intents = {
    "complaint": "unhappy, refund, broken, angry",
    "question": "how to, what is, where, docs",
    "praise": "thanks, love, great, awesome",
    "churn_risk": "cancel, switching, leaving forever",
}
intent_cases = [
    "This is the third outage this month. I'm canceling.",
    "How do I rotate an API key?",
    "Love the new UI, great work!",
    "Your support is useless. Moving to a competitor.",
    "Where is the Python SDK docs?",
    "Thanks for fixing the bug so quickly!",
    "앱이 또 죽었어요. 해지할 겁니다.",
    "파일 업로드 제한이 얼마인가요?",
    "정말 빠른 대응 감사해요!",
    "환불이 안 돼서 너무 화가 납니다.",
]
for i, s in enumerate(intent_cases, 1):
    add(f"choice_intent_{i}", "choice", s, {
        "intent": {"type": "choice", "instructions": "Best intent label?", "criteria": intents}
    })

# --- score ---
sev_levels = [
    "cosmetic / no user impact",
    "minor annoyance for few users",
    "degraded experience for many",
    "major feature broken",
    "full outage / data loss risk",
]
sev_cases = [
    "Typo in footer copyright year.",
    "Search results slightly reordered for 2% of users.",
    "Image CDN slow; pages load in 8s for APAC.",
    "Checkout button does nothing for all users.",
    "Primary database is down; writes fail globally.",
    "푸터 오탈자 하나.",
    "일부 사용자 검색이 느림.",
    "결제 버튼이 전원에게 동작하지 않음.",
    "메인 DB 장애로 쓰기 실패.",
    "다크모드 아이콘 색이 조금 연함.",
]
for i, s in enumerate(sev_cases, 1):
    add(f"score_sev_{i}", "score", s, {
        "severity": {"type": "score", "instructions": "Rate production severity.", "criteria": sev_levels}
    })

urgency = [
    "can wait a week",
    "this week is fine",
    "today",
    "within an hour",
    "drop everything now",
]
urg_cases = [
    "Update README badges.",
    "Sales wants pricing sheet before Friday demo.",
    "CEO keynote demo fails tomorrow morning.",
    "Active data exfiltration alert firing.",
    "Customer asks for logo PNG.",
    "결제 웹훅 장애 진행 중.",
    "블로그 오탈자 수정.",
    "랜섬웨어 탐지 알람.",
    "다음 주 컨퍼런스 슬라이드 색 변경.",
    "프로덕션 인증 전면 실패.",
]
for i, s in enumerate(urg_cases, 1):
    add(f"score_urg_{i}", "score", s, {
        "urgency": {"type": "score", "instructions": "How urgently must this be handled?", "criteria": urgency}
    })

# --- multi-question (guard-like) ---
guard_states = [
    {
        "question": "What is the GPU allocation per company in year 1?",
        "context": "Year 1 provides B200 256 or 128 GPUs per selected company. 2 or 3 companies may be selected.",
        "answer": "Each selected company gets B200 256 or 128 GPUs in year 1.",
    },
    {
        "question": "What is the exact matching fund ratio?",
        "context": "Self-funding match is required. Details are in the full guide. Exact percentage is not listed in this excerpt.",
        "answer": "The matching fund ratio is exactly 30%.",
    },
    {
        "question": "Who is the named evaluation committee chair?",
        "context": "Evaluation includes written and presentation rounds. Committee member names are not disclosed in this document.",
        "answer": "The committee chair is Dr. Kim Min-soo.",
    },
    {
        "question": "Can sole proprietors apply?",
        "context": "Only corporate business entities may apply. Individual (sole proprietor) businesses cannot apply.",
        "answer": "No. Only corporations may apply; sole proprietors are not eligible.",
    },
    {
        "question": "Is parking reimbursed for the briefing?",
        "context": "Parking fee is not supported. Please use public transit.",
        "answer": "No, parking is not reimbursed.",
    },
    {
        "question": "Must the free chatbot remain free forever?",
        "context": "A free general-purpose AI chatbot for the public must launch within the year. Later monetization details are not specified.",
        "answer": "Yes, it must remain free forever with no exceptions.",
    },
    {
        "question": "신청 마감일은?",
        "context": "전산 접수 마감: 2026. 8. 11.(화) 17:00. 접수 시작: 2026. 7. 13.(월) 17:00.",
        "answer": "2026년 8월 11일 화요일 17시까지입니다.",
    },
    {
        "question": "총 사업예산은 얼마인가?",
        "context": "본 발췌에는 총 사업예산 금액이 명시되어 있지 않다.",
        "answer": "총 예산은 1,200억 원이다.",
    },
]
for i, st in enumerate(guard_states, 1):
    state = (
        f"QUESTION:\n{st['question']}\n\n"
        f"RETRIEVED CONTEXT:\n{st['context']}\n\n"
        f"MODEL ANSWER:\n{st['answer']}"
    )
    add(f"multi_guard_{i}", "multi", state, {
        "grounded": {"type": "noul", "instructions": "Is the model answer supported by the retrieved context? Correct refusals count as grounded."},
        "hallucinated": {"type": "noul", "instructions": "Does the answer invent material facts not in the context?"},
        "abstain": {"type": "noul", "instructions": "Does the answer correctly refuse because info is missing from context?"},
        "decision": {
            "type": "choice",
            "instructions": "Release decision for this candidate answer.",
            "criteria": {
                "pass": "Safe to send",
                "rewrite": "Needs regeneration",
                "block": "Must not send",
            },
        },
    })

# pad to >=200 with mixed paraphrases if short
base = list(CASES)
i = 0
while len(CASES) < 200:
    b = base[i % len(base)]
    add(f"pad_{len(CASES)+1}", b["kind"], b["state"] + "\n\n(Evaluate carefully.)", b["questions"])
    i += 1

CASES = CASES[:200]
# renumber stable ids
for idx, c in enumerate(CASES, 1):
    c["idx"] = idx

out = Path(__file__).resolve().parent / "cases.json"
out.write_text(json.dumps(CASES, ensure_ascii=False, indent=2), encoding="utf-8")
print(len(CASES), "cases ->", out)
from collections import Counter
print(Counter(c["kind"] for c in CASES))
