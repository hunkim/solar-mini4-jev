#!/usr/bin/env python3
"""Generate 200 DISTINCT holdout cases (v2) — no overlap with cases.json states/ids."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

EXISTING = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))
EXISTING_STATES = {c["state"] for c in EXISTING}
EXISTING_IDS = {c["id"] for c in EXISTING}

CASES: list[dict] = []


def add(cid: str, kind: str, state: str, questions: dict):
    assert cid not in EXISTING_IDS, cid
    assert cid not in {c["id"] for c in CASES}, cid
    assert state not in EXISTING_STATES, f"state overlap: {state[:80]!r}"
    assert state not in {c["state"] for c in CASES}, f"dup state in v2: {state[:80]!r}"
    CASES.append({"id": cid, "kind": kind, "state": state, "questions": questions})


# =============================================================================
# NOUL (~100): healthcare, airline, ecommerce fraud, education, legal, devops,
# content mod, HR leave, logistics, fintech KYC — clear yes/no
# =============================================================================

noul_yes = [
    ("ER triage: patient SpO2 82% and cyanotic after asthma attack.", "Should a rapid-response airway team be activated now?"),
    ("Inbound flight reports smoke in cabin at FL310; oxygen masks deployed.", "Is this an airborne emergency requiring priority landing?"),
    ("Fraud system: 47 chargebacks from one BIN in 8 minutes and stolen-card signatures.", "Should we freeze the merchant MID immediately?"),
    ("Student portal leaked midterm answer keys to a public Discord.", "Should academic integrity + IT security respond urgently?"),
    ("Opposing counsel filed a TRO hearing for tomorrow 9am; we have no brief yet.", "Is same-day legal war-room staffing required?"),
    ("Prod k8s: CrashLoopBackOff on payment-ingress; checkout 5xx at 94%.", "Should SRE page the payments on-call right now?"),
    ("Moderation queue: livestream showing real-world doxxing of a minor.", "Must this stream be taken down immediately?"),
    ("Employee reports workplace violence threat from a terminated coworker on-site.", "Should security lock down the floor and call authorities?"),
    ("Cold-chain truck temp rose to 18C for 90 minutes on vaccine shipment.", "Is this a product-quarantine event requiring QA hold?"),
    ("KYC: newly onboarded account wired $2.4M to a sanctioned jurisdiction shell.", "Should compliance freeze the account and file SAR review?"),
]

noul_no = [
    ("Clinic patient asks to reschedule a routine dental cleaning next month.", "Is a Code Blue medical emergency declaration required?"),
    ("Passenger wants a window seat change on a non-delayed domestic hop.", "Should ATC declare an aircraft emergency?"),
    ("Shopper asks if free shipping applies to a $12 mug.", "Should we freeze all card rails company-wide?"),
    ("Student wants office hours to discuss a B+ grade on homework 3.", "Must campus police open a criminal investigation?"),
    ("Client asks for a PDF of our standard NDA template.", "Is an emergency TRO response needed tonight?"),
    ("Dev wants prettier colors on the staging Grafana dashboard.", "Should we page the CEO for a production outage?"),
    ("User reports a mildly annoying typo in a blog comment section.", "Must we permanently ban the entire platform?"),
    ("Employee requests one extra PTO day for a cousin's wedding.", "Should we activate workplace violence protocols?"),
    ("Warehouse picker asks where spare barcode scanners are stored.", "Is a FDA product recall mandatory this hour?"),
    ("Applicant uploaded a slightly blurry selfie for ID verification retry.", "Should we file a sanctions SAR immediately?"),
]

for i, (s, q) in enumerate(noul_yes, 1):
    add(f"holdout_noul_yes_{i}", "noul", s, {"yes": {"type": "noul", "instructions": q}})
for i, (s, q) in enumerate(noul_no, 1):
    add(f"holdout_noul_no_{i}", "noul", s, {"yes": {"type": "noul", "instructions": q}})

ko_noul = [
    ("응급실 환자 혈압이 70/40이고 의식 저하가 진행 중이다.", "트래우마 팀 활성화를 즉시 해야 하는가?", True),
    ("승객이 기내식 메뉴를 비건으로 바꾸고 싶어한다.", "비상착륙을 선언해야 하는가?", False),
    ("동일 카드로 분당 30건의 해외 고액 결제가 발생했다.", "사기 탐지팀이 계좌를 즉시 정지해야 하는가?", True),
    ("학생이 출석 확인 방법을 문의했다.", "학교 전체를 봉쇄해야 하는가?", False),
    ("소송 상대가 증거인멸 정황을 이메일로 보냈다.", "변호사에게 즉시 보고해야 하는가?", True),
    ("스테이징 서버 로그 포맷을 JSON으로 바꾸고 싶다.", "프로덕션을 즉시 롤백해야 하는가?", False),
    ("아동 성착취 이미지가 업로드된 것이 자동 탐지됐다.", "콘텐츠를 즉시 차단하고 신고해야 하는가?", True),
    ("직원이 육아휴직 서류 작성법을 물었다.", "보안팀을 호출해야 하는가?", False),
    ("냉장 배송 상자가 공항에서 분실됐다.", "고객과 QA에 즉시 알려 리콜 검토를 시작해야 하는가?", True),
    ("신규 가입자가 이름 철자 오타를 수정해 달라고 했다.", "자금세탁 신고를 즉시 제출해야 하는가?", False),
]
for i, (s, q, _) in enumerate(ko_noul, 1):
    add(f"holdout_noul_ko_{i}", "noul", s, {"yes": {"type": "noul", "instructions": q}})

# synthetic noul across new domains
syn_yes = [
    "ICU ventilator alarm silenced incorrectly for {n} minutes on bed 4.",
    "Airline ops: gate agent reports unattended bag for {n} minutes near jetway.",
    "Fraud graph linked {n} mule accounts sharing one device fingerprint today.",
    "LMS outage: exam submissions failing for {n} minutes during finals week.",
    "Privilege escalation CVE actively exploited on bastion for {n} minutes.",
    "Hate-raid bot farm posting slurs at {n} msgs/sec in a teen community.",
    "HR: anonymous tip alleges pay discrimination spanning {n} departments.",
    "Last-mile courier GPS went dark for {n} minutes on high-value pharma parcel.",
    "KYC liveness check bypassed via deepfake in {n} consecutive attempts.",
    "Legal hold mailbox retention job failed for {n} minutes during discovery.",
]
syn_no = [
    "Nurse asks where extra blankets are stored on ward day {n}.",
    "Flyer wants Miles status match FAQ link version {n}.",
    "Buyer asks if gift wrap is available for SKU-{n}.",
    "TA wants to rename homework set #{n} in the syllabus PDF.",
    "Intern reformats runbook markdown heading level {n}.",
    "Creator asks how to enable creator-fund tip jar option {n}.",
    "Manager wants team lunch catering menu option #{n}.",
    "Dispatcher asks for warehouse aisle map revision {n}.",
    "Applicant asks whether middle name is required on form page {n}.",
    "Paralegal wants blue binder tabs for exhibit set {n}.",
]
for i, t in enumerate(syn_yes, 1):
    for n in (4, 15, 28):
        add(
            f"holdout_noul_syn_yes_{i}_{n}",
            "noul",
            t.format(n=n),
            {"yes": {"type": "noul", "instructions": "Is urgent escalation or immediate protective action required?"}},
        )
for i, t in enumerate(syn_no, 1):
    for n in (2, 9, 33):
        add(
            f"holdout_noul_syn_no_{i}_{n}",
            "noul",
            t.format(n=n),
            {"yes": {"type": "noul", "instructions": "Is urgent escalation or immediate protective action required?"}},
        )

# =============================================================================
# CHOICE (~72): domain routing, language, intent
# =============================================================================

# Healthcare triage routing
hc_teams = {
    "triage": "vitals, acuity, ER queue, chief complaint",
    "pharmacy": "meds, refill, dose, interaction",
    "billing_hc": "insurance, claim, copay, invoice",
    "records": "records request, ROI, chart copy",
}
hc_route = [
    ("Chest pain radiating to left arm, BP 90/60.", "triage"),
    ("Need a 90-day refill on atorvastatin 20mg.", "pharmacy"),
    ("Insurance denied claim #88421 for MRI.", "billing_hc"),
    ("Please send my last 2 years of visit notes.", "records"),
    ("Sudden confusion and facial droop started 10 minutes ago.", "triage"),
    ("Does this antibiotic interact with warfarin?", "pharmacy"),
    ("Copay charged twice for yesterday's visit.", "billing_hc"),
    ("I need a HIPAA release form for my specialist.", "records"),
    ("숨이 차고 산소포화도가 떨어집니다.", "triage"),
    ("처방전 재발급이 필요합니다.", "pharmacy"),
    ("실손보험 청구가 거절됐어요.", "billing_hc"),
    ("진료기록 사본을 받고 싶습니다.", "records"),
]
for i, (s, _) in enumerate(hc_route, 1):
    add(f"holdout_choice_hc_{i}", "choice", s, {
        "team": {"type": "choice", "instructions": "Which hospital desk should handle this?", "criteria": hc_teams}
    })

# Airline ops routing
air_teams = {
    "ops": "delay, diversion, MEL, crew timeout, gate",
    "baggage": "lost bag, damaged luggage, PIR",
    "loyalty": "miles, status, companion pass",
    "safety": "smoke, medical, security threat, turbulence injury",
}
air_route = [
    ("Flight 442 will time out crew legality in 35 minutes.", "ops"),
    ("My suitcase never arrived in NRT; tag is JE123456.", "baggage"),
    ("Please reinstate my Gold status after partner credit.", "loyalty"),
    ("Passenger passed out mid-cabin; CPR in progress.", "safety"),
    ("Weather diversion to alternate; fuel critical.", "ops"),
    ("Wheel broke off checked bag on carousel 3.", "baggage"),
    ("Can I transfer 20k miles to my spouse?", "loyalty"),
    ("Unattended backpack in lavatory with wires visible.", "safety"),
    ("게이트 지연으로 승무원 근무시간이 초과됩니다.", "ops"),
    ("위탁수하물이 안 왔어요.", "baggage"),
    ("마일리지 적립이 누락됐습니다.", "loyalty"),
    ("기내에서 연기가 납니다.", "safety"),
]
for i, (s, _) in enumerate(air_route, 1):
    add(f"holdout_choice_air_{i}", "choice", s, {
        "team": {"type": "choice", "instructions": "Which airline team should own this?", "criteria": air_teams}
    })

# Ecommerce / fraud routing
ecom_teams = {
    "fraud": "stolen card, ATO, chargeback ring, mule",
    "fulfillment": "ship delay, wrong item, inventory",
    "returns": "RMA, refund, exchange",
    "seller": "marketplace seller KYC, listing policy",
}
ecom_route = [
    ("10 high-value phones bought with mismatched AVS and VPN.", "fraud"),
    ("Order #9912 says shipped but tracking never moved.", "fulfillment"),
    ("Shoes arrived wrong size; need free exchange.", "returns"),
    ("New seller uploaded counterfeit luxury handbags.", "seller"),
    ("Password reset then $3k gift-card drain in 2 minutes.", "fraud"),
    ("Warehouse sent blue mug instead of red kettle.", "fulfillment"),
    ("I want a refund; item unused in original box.", "returns"),
    ("Seller tax ID failed TIN match three times.", "seller"),
    ("도난 카드로 의심되는 결제가 있습니다.", "fraud"),
    ("배송이 일주째 멈춰 있어요.", "fulfillment"),
    ("반품 접수하고 환불해주세요.", "returns"),
    ("판매자 계정이 위조품을 올리고 있습니다.", "seller"),
]
for i, (s, _) in enumerate(ecom_route, 1):
    add(f"holdout_choice_ecom_{i}", "choice", s, {
        "team": {"type": "choice", "instructions": "Which ecommerce ops team?", "criteria": ecom_teams}
    })

# Language detection (new phrases)
langs = {"ko": "Korean", "en": "English", "ja": "Japanese", "zh": "Chinese"}
lang_texts = [
    ("내일 진료 예약 변경하고 싶어요.", "ko"),
    ("Please rebook my connecting flight to Osaka.", "en"),
    ("荷物が届きません。確認してください。", "ja"),
    ("我想取消这张保险理赔单。", "zh"),
    ("출석 인정 기준이 어떻게 되나요?", "ko"),
    ("Can you escalate this KYC review?", "en"),
    ("返品ラベルを再送してください。", "ja"),
    ("请帮我重置商户后台密码。", "zh"),
    ("연차 잔여일수 확인 부탁드립니다.", "ko"),
    ("The cold-chain logger alarm keeps beeping.", "en"),
    ("モデレーションポリシーを教えてください。", "ja"),
    ("这个包裹需要冷链运输吗？", "zh"),
]
for i, (text, _) in enumerate(lang_texts, 1):
    add(f"holdout_choice_lang_{i}", "choice", text, {
        "lang": {"type": "choice", "instructions": "Primary language of the message?", "criteria": langs}
    })

# Intent / risk labels across domains
intents = {
    "emergency": "life safety, smoke, assault, cardiac, active threat",
    "policy_question": "how to, what is allowed, docs, eligibility",
    "complaint": "angry, refund, unfair, broken promise",
    "praise": "thanks, excellent, love, great service",
}
intent_cases = [
    "Someone collapsed in gate B12; not breathing.",
    "What documents are required for student leave of absence?",
    "Your courier smashed my pharma cooler. Unacceptable.",
    "Brilliant bedside manner from Dr. Park today—thank you!",
    "Active shooter reported near the west loading dock.",
    "How do I appeal a content strike under adult-content rules?",
    "KYC took 3 weeks and still rejected with no reason. Furious.",
    "Love the new logistics tracking UI—so clear!",
    "기내에 연기 냄새와 Sparks가 납니다.",
    "육아휴직 신청 서류는 어디서 받나요?",
    "위조 상품 환불이 안 돼서 정말 화가 납니다.",
    "상담원 응대가 너무 친절해서 감동입니다.",
]
for i, s in enumerate(intent_cases, 1):
    add(f"holdout_choice_intent_{i}", "choice", s, {
        "intent": {"type": "choice", "instructions": "Best intent label?", "criteria": intents}
    })

# DevOps / runbook severity choice
sev_choice = {
    "sev1": "total outage or data loss in progress",
    "sev2": "major feature degraded for many users",
    "sev3": "limited impact / workaround exists",
    "sev4": "cosmetic or documentation only",
}
sev_cases_choice = [
    ("Primary auth IdP down; all logins failing globally.", "sev1"),
    ("Search latency elevated for EU region only; cache miss spike.", "sev2"),
    ("One secondary replica lagging 30s; reads still succeed.", "sev3"),
    ("Docs typo in runbook step numbering.", "sev4"),
    ("Ransomware encryption progressing on file servers.", "sev1"),
    ("Checkout A/B flag flipped wrong variant for 8% users.", "sev2"),
    ("Canary pod OOM once; auto-restarted healthy.", "sev3"),
    ("Changelog date format inconsistent.", "sev4"),
    ("결제 DB 마스터 장애로 전체 쓰기 실패.", "sev1"),
    ("푸터 저작권 연도 오타.", "sev4"),
    ("알림 이메일이 일부 지연되지만 앱은 정상.", "sev3"),
    ("모바일 푸시가 전 세계적으로 전송 실패.", "sev1"),
]
for i, (s, _) in enumerate(sev_cases_choice, 1):
    add(f"holdout_choice_sev_{i}", "choice", s, {
        "severity": {"type": "choice", "instructions": "Assign incident severity.", "criteria": sev_choice}
    })

# =============================================================================
# SCORE (~20)
# =============================================================================
sev_levels = [
    "cosmetic / no user impact",
    "minor annoyance for few users",
    "degraded experience for many",
    "major feature broken",
    "full outage / data loss risk",
]
score_sev = [
    "Misaligned icon on HR leave calendar widget.",
    "Airline app shows wrong gate for 0.5% of domestic flights.",
    "Hospital patient portal login succeeds but labs page times out for most users.",
    "Ecommerce checkout refuses all cards after payment gateway cutover.",
    "Fintech ledger double-writes balances; reconciliation diverging.",
    "물류 대시보드 아이콘 색이 조금 연함.",
    "일부 학생만 성적 PDF 다운로드가 느림.",
    "콘텐츠 신고 버튼이 모든 사용자에게 동작하지 않음.",
    "전자의무기록 쓰기 전면 실패.",
    "법률 포털 로고 정렬이 1px 어긋남.",
]
for i, s in enumerate(score_sev, 1):
    add(f"holdout_score_sev_{i}", "score", s, {
        "severity": {"type": "score", "instructions": "Rate production severity.", "criteria": sev_levels}
    })

urgency = [
    "can wait a week",
    "this week is fine",
    "today",
    "within an hour",
    "drop everything now",
]
score_urg = [
    "Update employee handbook PDF cover photo.",
    "Airline needs new meal-preference sheet before Friday charter.",
    "CEO hospital board demo of triage UI fails tomorrow morning.",
    "Active KYC deepfake bypass draining customer wallets.",
    "Creator asks for pastel theme on moderation queue.",
    "백신 콜드체인 알람 진행 중.",
    "블로그 오탈자 하나 수정.",
    "법정 제출 마감 2시간 전 증거 파일 손상.",
    "다음 주 학회 포스터 색상 변경.",
    "응급실 EMR 전면 다운.",
]
for i, s in enumerate(score_urg, 1):
    add(f"holdout_score_urg_{i}", "score", s, {
        "urgency": {"type": "score", "instructions": "How urgently must this be handled?", "criteria": urgency}
    })

# =============================================================================
# MULTI RAG-guard (~8) — new invented facts
# =============================================================================
guard_states = [
    {
        "question": "What is the maximum cold-chain excursion allowed for VaxNova vials?",
        "context": "VaxNova vials may remain between 2C and 8C. Excursions above 8C for up to 30 minutes are allowed once per shipment if logged. Excursions above 15C require quarantine.",
        "answer": "Excursions above 8C for up to 30 minutes are allowed once per shipment if logged.",
    },
    {
        "question": "What is the exact airline crew duty extension limit under Policy AR-9?",
        "context": "Policy AR-9 discusses fatigue reporting. The numeric duty extension limit is not stated in this excerpt.",
        "answer": "Crew may extend duty by exactly 4.5 hours under AR-9.",
    },
    {
        "question": "Who chairs the university academic integrity board?",
        "context": "The board reviews plagiarism cases within 10 business days. Member names are confidential and not listed here.",
        "answer": "Professor Elena Vargas chairs the academic integrity board.",
    },
    {
        "question": "Are sole traders eligible for FinPay KYC tier-3 limits?",
        "context": "Tier-3 limits require a registered corporation with two directors. Sole traders are limited to tier-1.",
        "answer": "No. Sole traders cannot obtain tier-3; they are capped at tier-1.",
    },
    {
        "question": "Is parking reimbursed for the legal intake clinic?",
        "context": "Parking is not reimbursed. Use the metro stop at Courthouse Square.",
        "answer": "No, parking is not reimbursed.",
    },
    {
        "question": "Must the moderated teen community ban all political speech forever?",
        "context": "Hate speech and doxxing are prohibited. Ordinary political discussion is allowed if civil. Lifetime ban rules are not specified for politics alone.",
        "answer": "Yes, all political speech must be permanently banned with no exceptions.",
    },
    {
        "question": "육아휴직 최소 근속 요건은?",
        "context": "연속 근속 6개월 이상인 정규직에 한해 육아휴직을 신청할 수 있다. 수습 기간은 제외한다.",
        "answer": "연속 근속 6개월 이상 정규직이어야 하며 수습 기간은 제외됩니다.",
    },
    {
        "question": "물류 허브 H7의 일일 처리 용량은?",
        "context": "본 발췌에는 허브 H7의 일일 처리 용량 수치가 없다. 다른 허브 예시만 언급된다.",
        "answer": "허브 H7은 하루 12만 건을 처리합니다.",
    },
]
for i, st in enumerate(guard_states, 1):
    state = (
        f"QUESTION:\n{st['question']}\n\n"
        f"RETRIEVED CONTEXT:\n{st['context']}\n\n"
        f"MODEL ANSWER:\n{st['answer']}"
    )
    add(f"holdout_multi_guard_{i}", "multi", state, {
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

# Pad/trim to exactly 200 if needed (prefer unique paraphrases from new domains)
if len(CASES) < 200:
    pad_bank = [
        ("holdout_pad_hr_1", "noul",
         "Manager asks whether Juneteenth is a paid holiday this year for remote staff.",
         {"yes": {"type": "noul", "instructions": "Is this a workplace violence emergency?"}}),
        ("holdout_pad_log_1", "noul",
         "Dispatcher notes pallet jack squeaks in aisle C; maintenance ticket filed.",
         {"yes": {"type": "noul", "instructions": "Is FDA recall action required immediately?"}}),
        ("holdout_pad_edu_1", "noul",
         "Librarian wants quieter LED bulbs in study room 2.",
         {"yes": {"type": "noul", "instructions": "Should campus lockdown begin now?"}}),
        ("holdout_pad_fin_1", "noul",
         "Analyst wants a prettier color for the AML dashboard chart series.",
         {"yes": {"type": "noul", "instructions": "Should we freeze all customer wires globally?"}}),
        ("holdout_pad_mod_1", "noul",
         "Moderator asks how to pin community guidelines to channel top.",
         {"yes": {"type": "noul", "instructions": "Must we call law enforcement for this tip?"}}),
        ("holdout_pad_legal_1", "noul",
         "Paralegal wants blue sticky flags for deposition binders.",
         {"yes": {"type": "noul", "instructions": "Is an emergency TRO hearing required tonight?"}}),
        ("holdout_pad_air_1", "noul",
         "Passenger asks if pretzel snacks are still complimentary in economy.",
         {"yes": {"type": "noul", "instructions": "Should ATC declare an airborne emergency?"}}),
        ("holdout_pad_hc_1", "noul",
         "Outpatient asks where the cafeteria is on floor 2.",
         {"yes": {"type": "noul", "instructions": "Should a Code Blue be called?"}}),
        ("holdout_pad_dev_1", "noul",
         "Engineer wants to rename a staging feature flag for clarity.",
         {"yes": {"type": "noul", "instructions": "Is this a Sev-1 production outage?"}}),
        ("holdout_pad_ecom_1", "noul",
         "Shopper asks whether gift receipts omit prices.",
         {"yes": {"type": "noul", "instructions": "Should we freeze the merchant MID for fraud?"}}),
    ]
    for cid, kind, state, qs in pad_bank:
        if len(CASES) >= 200:
            break
        if state not in EXISTING_STATES and state not in {c["state"] for c in CASES}:
            add(cid, kind, state, qs)

# If somehow over 200, keep first 200 of balanced kinds preference
if len(CASES) > 200:
    # Prefer keeping all multi, then score, then fill
    multi = [c for c in CASES if c["kind"] == "multi"]
    score = [c for c in CASES if c["kind"] == "score"]
    choice = [c for c in CASES if c["kind"] == "choice"]
    noul = [c for c in CASES if c["kind"] == "noul"]
    kept = multi[:8] + score[:20] + choice[:72] + noul
    CASES = kept[:200]

CASES = CASES[:200]
for idx, c in enumerate(CASES, 1):
    c["idx"] = idx

assert len(CASES) == 200
assert len({c["id"] for c in CASES}) == 200
assert len({c["state"] for c in CASES}) == 200
assert not ({c["state"] for c in CASES} & EXISTING_STATES)
assert not ({c["id"] for c in CASES} & EXISTING_IDS)

out = Path(__file__).resolve().parent / "cases_v2.json"
out.write_text(json.dumps(CASES, ensure_ascii=False, indent=2), encoding="utf-8")
print(len(CASES), "cases ->", out)
print(Counter(c["kind"] for c in CASES))
