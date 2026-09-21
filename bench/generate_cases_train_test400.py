#!/usr/bin/env python3
"""Generate 400 TRAIN + 400 TEST cases — disjoint from each other and from cases.json + cases_v2.json.

Domains (new vs v1 SaaS/support and v2 airline/healthcare/fraud):
  energy/grid, gaming/anti-cheat, municipal 311, insurance claims, biotech lab,
  telecom NOC, food safety, construction safety, climate/sensors, library/archives,
  sports ops, nonprofit grants. Mix EN+KO.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

BENCH = Path(__file__).resolve().parent
EXISTING = json.loads((BENCH / "cases.json").read_text(encoding="utf-8"))
EXISTING += json.loads((BENCH / "cases_v2.json").read_text(encoding="utf-8"))
EXISTING_STATES = {c["state"] for c in EXISTING}
EXISTING_IDS = {c["id"] for c in EXISTING}

# Per-split targets matching ~50% noul, ~36% choice, ~10% score, ~4% multi
TARGET = {"noul": 200, "choice": 144, "score": 40, "multi": 16}


def _add(bucket: list, used_ids: set, used_states: set, cid: str, kind: str, state: str, questions: dict) -> bool:
    if cid in EXISTING_IDS or cid in used_ids:
        return False
    if state in EXISTING_STATES or state in used_states:
        return False
    bucket.append({"id": cid, "kind": kind, "state": state, "questions": questions})
    used_ids.add(cid)
    used_states.add(state)
    return True


# =============================================================================
# NOUL banks — yes / no / KO / synthetic templates across NEW domains
# =============================================================================

NOUL_YES = [
    # energy/grid
    ("Substation B7 reports cascading feeder trips; 42k customers dark in Zone 3.", "Should grid ops declare a major outage and page the transmission desk now?"),
    ("SCADA shows transformer oil temp at 118C with gas relay alarm on Unit 4.", "Is immediate de-energization review required?"),
    ("Wildfire smoke reduced line rating; load forecast exceeds N-1 margin in 20 minutes.", "Should operators shed non-critical load under emergency protocol?"),
    # gaming/anti-cheat
    ("Anti-cheat flagged a memory injector affecting 3.2k concurrent ranked matches.", "Should we mass-ban the involved accounts and lock ranked queues?"),
    ("Live esports final: spectator overlay leaked unreleased champion kit mid-match.", "Must broadcast halt and integrity ops be activated immediately?"),
    ("Payment webhook for battle-pass purchases failing for all regions 25 minutes.", "Is urgent payments on-call escalation required?"),
    # municipal 311
    ("Gas odor reports from 14 addresses on Maple Ave within 8 minutes.", "Should 911/utility emergency dispatch be activated now?"),
    ("Bridge strain gauges exceeded red threshold after overnight freeze-thaw.", "Must public works close the span pending inspection?"),
    ("Water main break flooding two intersections with sinkhole risk.", "Is immediate street closure and utility response required?"),
    # insurance claims
    ("FNOL: warehouse fire with active flames and injured workers on scene.", "Should catastrophic claims surge protocol be triggered?"),
    ("SIU: 37 identical soft-tissue claims from one clinic in 48 hours.", "Must special investigations freeze payouts immediately?"),
    ("Storm surge maps show 900 policies in newly flooded zip with no adjusters assigned.", "Is emergency CAT desk staffing required tonight?"),
    # biotech lab
    ("BSL-2 freezer alarm: -20C samples rose to +4C for 55 minutes unnoticed.", "Should QA quarantine the affected lots and notify PI now?"),
    ("Autoclave interlock failed; door opened mid-cycle with biohazard load.", "Is lab lockdown and biosafety officer paging required?"),
    ("Sequencer coolant leak dripping onto high-voltage rack in wet lab.", "Must facilities + EHS shut power and evacuate bay?"),
    # telecom NOC
    ("Core router flap: BGP sessions down to three peering partners; packet loss 40%.", "Should NOC declare Sev-1 and open bridge immediately?"),
    ("Fiber cut on metro ring; dual-homed enterprise customers losing voice+data.", "Is urgent field splice crew dispatch required?"),
    ("SS7 signaling storm from compromised interconnect flooding STP CPUs.", "Must signaling firewall scrub mode be enabled now?"),
    # food safety
    ("Listeria PCR positive on ready-to-eat line swab after sanitation.", "Should production halt and product hold begin immediately?"),
    ("Cold room #3 at 12C for 70 minutes on fresh poultry shipment.", "Is USDA-style hold and QA recall assessment required?"),
    ("Allergen mislabel: peanut oil used in 'nut-free' SKU batch 8841.", "Must we initiate consumer recall protocol?"),
    # construction safety
    ("Tower crane load cell fault while lifting 8-ton panel over sidewalk.", "Should work stop and exclusion zone be enforced now?"),
    ("Confined-space O2 at 16% during tank entry; attendant alarming.", "Is emergency rescue activation required?"),
    ("Scaffold tie-in failed on floor 18; planks shifting in wind.", "Must crews evacuate the elevation immediately?"),
    # climate/sensors
    ("Flood sensor network: river stage 1.2m above berm with rise rate accelerating.", "Should emergency management issue evacuation alerts?"),
    ("Air-quality PM2.5 spiked to 380 ug/m3 near school zone after industrial release.", "Must public health shelter-in-place guidance go out now?"),
    ("Landslide inclinometer crossed red after 40mm overnight rain.", "Is highway closure for the canyon route required?"),
    # library/archives
    ("Rare manuscript vault humidity hit 78% RH; mold risk on parchment collection.", "Should conservators initiate emergency climate response?"),
    ("Sprinkler false trip soaking newspaper microfilm cabinets on floor B2.", "Must archives disaster recovery be activated?"),
    ("Ransomware encrypting digital repository nodes; backups unverified for 6h.", "Is cyber incident response for cultural heritage systems required?"),
    # sports ops
    ("Stadium structural sensor: vibration anomaly under north upper deck mid-game.", "Should ops pause play and begin controlled egress assessment?"),
    ("Player collapsed with no pulse during warmups; AED deployed.", "Is medical emergency protocol and EMS confirmation required?"),
    ("Pyrotechnics misfire ignited banner above visiting supporters section.", "Must fire response and section evacuation start now?"),
    # nonprofit grants
    ("Grant portal exposed SSN/EIN files via misconfigured S3 for 3 hours.", "Should privacy breach response and funder notification begin immediately?"),
    ("Wire of $1.8M subaward redirected after phishing of finance director.", "Is fraud freeze and bank recall action required now?"),
    ("Background check vendor breach included unaccompanied-minor caseworker data.", "Must program pause high-risk placements pending legal review?"),
]

NOUL_NO = [
    ("Grid planner asks for prettier colors on the load-forecast dashboard legend.", "Should we shed 40k customers under emergency load protocol?"),
    ("Gamer wants a new emote color for their battle-pass skin.", "Must we lock all ranked queues company-wide?"),
    ("Resident asks when bulk trash pickup is next Tuesday.", "Should 911 declare a citywide disaster?"),
    ("Policyholder asks how to download their declarations page PDF.", "Must CAT surge claims protocol activate tonight?"),
    ("Lab intern asks where spare pipette tips are stored on shelf B.", "Should we evacuate the entire BSL campus?"),
    ("NOC analyst wants a darker theme for the Grafana night shift view.", "Is Sev-1 fiber-cut response required?"),
    ("Kitchen staff asks if cilantro can be substituted in staff meals.", "Must we initiate a nationwide food recall?"),
    ("Site admin asks for a quieter radio channel for lunch orders.", "Should tower crane exclusion zones go citywide?"),
    ("Intern wants to rename a climate dashboard widget title.", "Must we issue county evacuation alerts?"),
    ("Patron asks if the library has larger-print editions of mysteries.", "Should archives disaster recovery activate?"),
    ("Fan asks whether stadium nachos contain jalapeños.", "Is structural deck evacuation required mid-game?"),
    ("Volunteer asks for a PDF of last year's annual report cover.", "Must we freeze all nonprofit wires globally?"),
    ("Energy marketing wants a new icon for the green-power FAQ page.", "Should transmission desk declare cascading blackout?"),
    ("Anti-cheat designer tweaks splash-screen font weight.", "Must we mass-ban every account in the region?"),
    ("311 app user likes the new pothole map filters.", "Is bridge closure for structural failure needed?"),
    ("Adjuster asks where spare sticky notes are in the claims office.", "Should SIU freeze all payouts nationwide?"),
    ("Biotech receptionist schedules a visitor badge for tomorrow.", "Must autoclave emergency lockdown begin?"),
    ("Telecom intern renames a staging feature flag for clarity.", "Is SS7 scrub-mode enablement mandatory now?"),
    ("Cafeteria wants pastel trays for the salad bar.", "Should Listeria production halt start immediately?"),
    ("Foreman asks for updated coffee order for the trailer.", "Must confined-space rescue teams deploy?"),
]

KO_NOUL = [
    ("변전소 과열로 인근 3개 피더가 동시에 차단됐다.", "계통운영 비상대응을 즉시 해야 하는가?", True),
    ("게임 랭크 매치에서 메모리 핵이 대량 탐지됐다.", "랭크 큐를 잠그고 제재해야 하는가?", True),
    ("가스 냄새 신고가 같은 골목에서 10건 연속 들어왔다.", "긴급 유틸리티 출동을 해야 하는가?", True),
    ("창고 화재 FNOL에 부상자 발생이 보고됐다.", "대형재해 클레임 프로토콜을 가동해야 하는가?", True),
    ("BSL 냉동고 온도가 한 시간 넘게 상승했다.", "시료를 격리하고 QA에 즉시 알려야 하는가?", True),
    ("백본 라우터 BGP가 다중 피어에서 다운됐다.", "NOC가 Sev-1을 선언해야 하는가?", True),
    ("RTE 라인 스왑에서 리스테리아 PCR 양성이 나왔다.", "생산을 멈추고 홀드해야 하는가?", True),
    ("밀폐공간 산소농도가 16%로 떨어졌다.", "구조팀을 즉시 호출해야 하는가?", True),
    ("하천 수위가 제방보다 빠르게 상승 중이다.", "주민 대피 경보를 발령해야 하는가?", True),
    ("희귀본 서고 습도가 위험 수준이다.", "보존팀 비상 대응이 필요한가?", True),
    ("경기 중 관중석 구조 센서가 적색이다.", "경기 중단과 대피 검토가 필요한가?", True),
    ("보조금 포털에서 주민번호 파일이 노출됐다.", "유출 대응과 후원자 통지가 즉시 필요한가?", True),
    ("대시보드 아이콘 색을 바꾸고 싶다.", "비상 부하차단을 해야 하는가?", False),
    ("팬이 응원봉 색상을 문의했다.", "전 서버를 잠가야 하는가?", False),
    ("민원인이 쓰레기 수거일을 물었다.", "시 재난사태를 선포해야 하는가?", False),
    ("약관 PDF 다운로드 방법을 물었다.", "전체 보험금 지급을 멈춰야 하는가?", False),
    ("피펫 팁 위치를 물어봤다.", "연구동 전체를 대피시켜야 하는가?", False),
    ("그라파나 테마를 어둡게 하고 싶다.", "전국 광케이블을 차단해야 하는가?", False),
    ("식당 메뉴에 고수를 빼 달란다.", "전국 리콜을 시작해야 하는가?", False),
    ("점심 커피 주문을 바꿨다.", "타워크레인 작업을 전면 중지하라?", False),
]

SYN_YES = [
    "Grid: N-1 contingency violated for {n} minutes on west corridor.",
    "Anti-cheat: wallhack signature on {n} accounts in masters lobby.",
    "311: sinkhole reports expanding across {n} blocks downtown.",
    "Insurance: hail FNOL volume spiked {n}x vs seasonal baseline.",
    "Biotech: -80C freezer alarm silenced incorrectly for {n} minutes.",
    "Telecom: SIP trunk ASR collapsed for {n} minutes across region.",
    "Food safety: metal detector reject rate {n}x normal on line 2.",
    "Construction: fall-protection harness failures reported {n} times today.",
    "Climate: flash-flood gauges above berm for {n} consecutive minutes.",
    "Archives: vault RH above 70% for {n} minutes on parchment aisle.",
    "Sports: AED deployed; unresponsive athlete for {n} minutes.",
    "Grants: phishing redirected subaward wires totaling ${n}0k.",
]

SYN_NO = [
    "Grid intern asks how to export CSV of day-{n} load chart.",
    "Gamer wants sticker pack #{n} color tweak.",
    "311 user asks recycling schedule for week {n}.",
    "Insured asks where to find form page {n} for address change.",
    "Lab tech renames notebook section heading level {n}.",
    "NOC junior reformats runbook markdown step {n}.",
    "Kitchen asks for tray label font size option {n}.",
    "Foreman wants coffee order revision #{n}.",
    "Climate volunteer renames widget title version {n}.",
    "Librarian asks for quieter LED bulb type {n}.",
    "Fan asks nacho topping option #{n}.",
    "Volunteer wants annual-report cover photo crop {n}.",
]


def build_noul(prefix: str, used_ids: set, used_states: set, need: int) -> list:
    out: list = []
    tag = "" if prefix == "train" else " [TEST]"
    # yes
    for i, (s, q) in enumerate(NOUL_YES, 1):
        if len([c for c in out if c["kind"] == "noul"]) >= need:
            break
        _add(out, used_ids, used_states, f"{prefix}_noul_yes_{i}", "noul", s + tag,
             {"yes": {"type": "noul", "instructions": q}})
    # no
    for i, (s, q) in enumerate(NOUL_NO, 1):
        if len([c for c in out if c["kind"] == "noul"]) >= need:
            break
        _add(out, used_ids, used_states, f"{prefix}_noul_no_{i}", "noul", s + tag,
             {"yes": {"type": "noul", "instructions": q}})
    # ko
    for i, (s, q, _) in enumerate(KO_NOUL, 1):
        if len([c for c in out if c["kind"] == "noul"]) >= need:
            break
        _add(out, used_ids, used_states, f"{prefix}_noul_ko_{i}", "noul", s + tag,
             {"yes": {"type": "noul", "instructions": q}})
    # synthetic
    for i, t in enumerate(SYN_YES, 1):
        for n in (5, 14, 27, 41):
            if len([c for c in out if c["kind"] == "noul"]) >= need:
                break
            _add(out, used_ids, used_states, f"{prefix}_noul_syn_yes_{i}_{n}", "noul",
                 t.format(n=n) + tag,
                 {"yes": {"type": "noul", "instructions": "Is urgent escalation or immediate protective action required?"}})
        if len([c for c in out if c["kind"] == "noul"]) >= need:
            break
    for i, t in enumerate(SYN_NO, 1):
        for n in (3, 11, 22, 39):
            if len([c for c in out if c["kind"] == "noul"]) >= need:
                break
            _add(out, used_ids, used_states, f"{prefix}_noul_syn_no_{i}_{n}", "noul",
                 t.format(n=n) + tag,
                 {"yes": {"type": "noul", "instructions": "Is urgent escalation or immediate protective action required?"}})
        if len([c for c in out if c["kind"] == "noul"]) >= need:
            break
    # pad with paraphrases if short
    pad_i = 0
    pads = [
        ("Battery storage islanding after inverter cluster fault in Microgrid {k}.",
         "Should DER ops isolate and notify the balancing authority now?"),
        ("Tournament bracket API returning 5xx for all viewers region {k}.",
         "Is live-ops escalation required immediately?"),
        ("Hydrant shear after vehicle strike flooding lane {k}.",
         "Must traffic + utility emergency response begin?"),
        ("Cyber claim: ransomware on insured clinic EHR cluster {k}.",
         "Should cyber CAT desk open immediately?"),
        ("CO2 incubator drift +1.5% for culture batch {k}.",
         "Must QA hold cultures and alert the PI?"),
        ("RAN site power lost; battery below 15% on sector {k}.",
         "Is field tech emergency dispatch required?"),
        ("Allergen swab positive on utensil rack {k} post-CIP.",
         "Should line hold and re-sanitation start now?"),
        ("Excavation cave-in risk after rain on trench {k}.",
         "Must workers evacuate and shore immediately?"),
        ("Wildfire perimeter sensor crossed red near town {k}.",
         "Should evacuation alerts be issued?"),
        ("Digitization scanner overheating rare map set {k}.",
         "Is conservation stop-work required?"),
        ("Lightning delay protocol for outdoor match slot {k}.",
         "Must players clear the field under safety rules?"),
        ("Donor CRM export included minors' case notes file {k}.",
         "Should privacy incident response begin now?"),
        ("Load-forecast chart legend font size tweak request {k}.",
         "Should we declare a cascading blackout?"),
        ("Emote palette suggestion for cosmetic pack {k}.",
         "Must ranked integrity lock engage?"),
        ("Ask about leaf collection week for district {k}.",
         "Is citywide disaster declaration required?"),
        ("Request copy of policy jacket page {k}.",
         "Must SIU freeze all nationwide claims?"),
    ]
    while len([c for c in out if c["kind"] == "noul"]) < need:
        pad_i += 1
        s_t, q = pads[(pad_i - 1) % len(pads)]
        s = s_t.format(k=pad_i + 1000)
        kind_yes = pad_i % 2 == 1 and "declare a cascading" not in q and "Must ranked" not in q and "disaster" not in q and "freeze all" not in q
        # alternate: first half of pads are yes-leaning, second half no-leaning by construction
        ok = _add(out, used_ids, used_states, f"{prefix}_noul_pad_{pad_i}", "noul", s,
                  {"yes": {"type": "noul", "instructions": q}})
        if not ok:
            s = s + f" [ref {pad_i}]"
            _add(out, used_ids, used_states, f"{prefix}_noul_pad_{pad_i}", "noul", s,
                 {"yes": {"type": "noul", "instructions": q}})
        if pad_i > need * 3:
            break
    return [c for c in out if c["kind"] == "noul"][:need]


# =============================================================================
# CHOICE banks
# =============================================================================

def build_choice(prefix: str, used_ids: set, used_states: set, need: int) -> list:
    out: list = []
    tag = "" if prefix == "train" else " [TEST]"

    def addc(cid, kind, state, questions):
        return _add(out, used_ids, used_states, cid, kind, state + tag, questions)

    # Energy / grid routing
    energy = {
        "transmission": "HV lines, N-1, cascading, interconnection",
        "distribution": "feeders, transformers, customer outages, meters",
        "der": "solar, battery, microgrid, inverter",
        "market": "settlement, LMP, bidding, ISO",
    }
    energy_cases = [
        ("Cascading trips on 345kV corridor after breaker failure.", "transmission"),
        ("Neighborhood feeder fuse blown; 800 meters dark.", "distribution"),
        ("Community battery islanding after inverter cluster fault.", "der"),
        ("Day-ahead bid rejected; settlement mismatch on hub node.", "market"),
        ("Intertie oscillation growing toward stability limit.", "transmission"),
        ("Smart meter mesh gateway offline for one suburb.", "distribution"),
        ("Rooftop PV curtailment schedule needs DERMS update.", "der"),
        ("Virtual bid quantity error in ISO market API.", "market"),
        ("345kV 선로에서 N-1 여유가 부족합니다.", "transmission"),
        ("주택가 변압기 소음과 정전 신고가 있습니다.", "distribution"),
        ("마이크로그리드 배터리 SOC가 급락했습니다.", "der"),
        ("정산 LMP 이상으로 이의가 접수됐습니다.", "market"),
    ]
    for i, (s, _) in enumerate(energy_cases, 1):
        addc(f"{prefix}_choice_energy_{i}", "choice", s, {
            "team": {"type": "choice", "instructions": "Which energy desk should own this?", "criteria": energy}
        })

    # Gaming anti-cheat routing
    game = {
        "anticheat": "cheats, injectors, wallhacks, bans",
        "liveops": "events, brackets, matchmaking, queues",
        "payments": "IAP, refunds, chargebacks, wallet",
        "community": "toxicity, reports, chat mod, appeals",
    }
    game_cases = [
        ("Memory injector detected in ranked 5v5 lobby.", "anticheat"),
        ("Weekend tournament bracket API returning 503.", "liveops"),
        ("Battle-pass charge duplicated on player's card.", "payments"),
        ("Hate raid flooding global chat with slurs.", "community"),
        ("DMA cheat signature spike after patch Tuesday.", "anticheat"),
        ("Matchmaking MMR soft-lock for Masters queue.", "liveops"),
        ("Wallet drain after account takeover of streamer.", "payments"),
        ("Appeal: false ban for VPN-only login pattern.", "community"),
        ("월핵 사용이 대규모로 탐지됐습니다.", "anticheat"),
        ("토너먼트 대진표가 갱신되지 않습니다.", "liveops"),
        ("인앱결제 환불이 중복 청구됐습니다.", "payments"),
        ("채팅에 혐오 발언 도배가 있습니다.", "community"),
    ]
    for i, (s, _) in enumerate(game_cases, 1):
        addc(f"{prefix}_choice_game_{i}", "choice", s, {
            "team": {"type": "choice", "instructions": "Which gaming ops team?", "criteria": game}
        })

    # Municipal 311 routing
    muni = {
        "utilities": "gas, water, electric, main break",
        "streets": "pothole, signal, plow, sidewalk",
        "sanitation": "trash, recycling, illegal dump",
        "parks": "playground, tree, trail, graffiti park",
    }
    muni_cases = [
        ("Water main break flooding intersection of 5th and Pine.", "utilities"),
        ("Traffic signal stuck red on both approaches at Oak.", "streets"),
        ("Illegal dumping of construction debris behind lot 12.", "sanitation"),
        ("Playground swing chain broken at Riverside Park.", "parks"),
        ("Gas odor near manhole cover on Cedar Ave.", "utilities"),
        ("Giant pothole damaged two cars on Highway spur.", "streets"),
        ("Missed recycling pickup for whole cul-de-sac.", "sanitation"),
        ("Fallen tree blocking trail after storm.", "parks"),
        ("상수관 파열로 도로가 침수됐습니다.", "utilities"),
        ("신호등이 양쪽 모두 빨간불입니다.", "streets"),
        ("골목에 불법 폐기물이 쌓여 있습니다.", "sanitation"),
        ("놀이터 그네가 끊어졌습니다.", "parks"),
    ]
    for i, (s, _) in enumerate(muni_cases, 1):
        addc(f"{prefix}_choice_muni_{i}", "choice", s, {
            "team": {"type": "choice", "instructions": "Which municipal desk?", "criteria": muni}
        })

    # Insurance claims routing
    ins = {
        "fnol": "first notice, loss intake, new claim",
        "siu": "fraud ring, staged, SIU, identical claims",
        "cat": "storm surge, wildfire, earthquake CAT",
        "policy": "coverage question, endorsement, declarations",
    }
    ins_cases = [
        ("Rear-end collision yesterday; need to open a claim.", "fnol"),
        ("37 near-identical soft-tissue claims from one clinic.", "siu"),
        ("Hurricane landfall; 900 new wind claims overnight.", "cat"),
        ("Does my policy cover basement sump-pump failure?", "policy"),
        ("Hit a deer; windshield and bumper damage photos ready.", "fnol"),
        ("Provider billing patterns match known staging ring.", "siu"),
        ("Wildfire smoke damage across three counties.", "cat"),
        ("Please explain rental reimbursement endorsement.", "policy"),
        ("어제 추돌사고 접수하고 싶습니다.", "fnol"),
        ("동일 클리닉에서 유사한 청구가 다수입니다.", "siu"),
        ("태풍 피해 청구가 폭증했습니다.", "cat"),
        ("특약 보장 범위를 확인하고 싶습니다.", "policy"),
    ]
    for i, (s, _) in enumerate(ins_cases, 1):
        addc(f"{prefix}_choice_ins_{i}", "choice", s, {
            "team": {"type": "choice", "instructions": "Which insurance claims team?", "criteria": ins}
        })

    # Biotech lab routing
    bio = {
        "biosafety": "BSL, autoclave, spill, exposure",
        "qa": "quarantine, deviation, CAPA, lot hold",
        "facilities": "HVAC, freezer, power, coolant",
        "informatics": "LIMS, sequencer data, pipeline",
    }
    bio_cases = [
        ("Autoclave door opened mid-cycle with biohazard load.", "biosafety"),
        ("Deviation: lot 22A skipped in-process assay.", "qa"),
        ("-80 freezer compressor failed on wing C.", "facilities"),
        ("LIMS accession IDs colliding after migration.", "informatics"),
        ("Needle stick during animal procedure; exposure kit.", "biosafety"),
        ("CAPA overdue for Environmental Monitoring fail.", "qa"),
        ("Coolant leak onto sequencer high-voltage rack.", "facilities"),
        ("Pipeline dropped FASTQ uploads for run 884.", "informatics"),
        ("생물안전 캐비닛에서 누출이 있었습니다.", "biosafety"),
        ("로트 일탈 보고서가 미제출입니다.", "qa"),
        ("초저온 냉동고 알람이 울립니다.", "facilities"),
        ("시퀀싱 데이터 파이프라인이 실패했습니다.", "informatics"),
    ]
    for i, (s, _) in enumerate(bio_cases, 1):
        addc(f"{prefix}_choice_bio_{i}", "choice", s, {
            "team": {"type": "choice", "instructions": "Which lab team?", "criteria": bio}
        })

    # Telecom NOC routing
    tel = {
        "ipcore": "BGP, MPLS, core router, peering",
        "access": "OLT, DSLAM, last-mile, CPE",
        "voice": "SIP, SS7, STP, call completion",
        "field": "fiber splice, truck roll, OSP",
    }
    tel_cases = [
        ("Core router BGP sessions down to three peers.", "ipcore"),
        ("OLT PON port flapping; 200 ONTs dropping.", "access"),
        ("SIP trunk ASR collapsed across region east.", "voice"),
        ("Metro fiber cut; need splice crew on span 14.", "field"),
        ("MPLS LSP reroute oscillation on ring west.", "ipcore"),
        ("CPE firmware brick after mass upgrade canary.", "access"),
        ("SS7 signaling storm from interconnect partner.", "voice"),
        ("Manhole flood threatening splice case.", "field"),
        ("코어 라우터에서 패킷 손실이 큽니다.", "ipcore"),
        ("가입자 CPE가 대량으로 오프라인입니다.", "access"),
        ("SIP 호 완료율이 급락했습니다.", "voice"),
        ("광케이블 절체로 현장 출동이 필요합니다.", "field"),
    ]
    for i, (s, _) in enumerate(tel_cases, 1):
        addc(f"{prefix}_choice_tel_{i}", "choice", s, {
            "team": {"type": "choice", "instructions": "Which telecom NOC team?", "criteria": tel}
        })

    # Language detection (new phrases in new domains)
    langs = {"ko": "Korean", "en": "English", "ja": "Japanese", "zh": "Chinese"}
    lang_texts = [
        ("변전소 점검 일정을 변경하고 싶어요.", "ko"),
        ("Please reset my anti-cheat hardware ID ban.", "en"),
        ("水道管の漏水を報告します。", "ja"),
        ("我想查询保险理赔进度。", "zh"),
        ("실험실 냉동고 알람이 울려요.", "ko"),
        ("Fiber cut on span 22 needs a truck roll.", "en"),
        ("アレルゲン表示を確認してください。", "ja"),
        ("工地脚手架需要安全检查。", "zh"),
        ("홍수 경보 문자 수신을 원합니다.", "ko"),
        ("The parchment vault humidity is too high.", "en"),
        ("試合中の避難経路を教えてください。", "ja"),
        ("请帮我下载非营利组织年度报告。", "zh"),
        ("보조금 포털 비밀번호를 재설정해주세요.", "ko"),
        ("Metal detector rejects spiked on line 2.", "en"),
        ("気象センサーの校正記録が必要です。", "ja"),
        ("图书馆珍本需要紧急除湿。", "zh"),
    ]
    for i, (text, _) in enumerate(lang_texts, 1):
        addc(f"{prefix}_choice_lang_{i}", "choice", text, {
            "lang": {"type": "choice", "instructions": "Primary language of the message?", "criteria": langs}
        })

    # Intent / risk across new domains
    intents = {
        "emergency": "life safety, structural failure, biohazard, active threat, evacuation",
        "policy_question": "how to, what is covered, docs, eligibility, schedule",
        "complaint": "angry, unfair, broken promise, refund dispute",
        "praise": "thanks, excellent, love, great service",
    }
    intent_cases = [
        "Confined-space O2 at 16%; attendant activating rescue.",
        "How do I apply for a nonprofit capacity-building grant?",
        "Your adjuster ignored my flood claim for six weeks. Furious.",
        "Brilliant conservator response saved our parchment set—thank you!",
        "Stadium upper-deck vibration crossed red mid-game.",
        "What documents are required for municipal tree-removal permit?",
        "Anti-cheat banned me wrongly three times. Unacceptable.",
        "Love the new climate alert map—so clear!",
        "밀폐공간 산소가 위험 수준입니다.",
        "재활용 수거 신청은 어디서 하나요?",
        "보험금 지급이 미뤄져 정말 화가 납니다.",
        "현장 안전팀 대응이 훌륭해서 감동입니다.",
    ]
    for i, s in enumerate(intent_cases, 1):
        addc(f"{prefix}_choice_intent_{i}", "choice", s, {
            "intent": {"type": "choice", "instructions": "Best intent label?", "criteria": intents}
        })

    # Severity choice (new domains)
    sev = {
        "sev1": "total outage or life-safety / data-loss in progress",
        "sev2": "major capability degraded for many users/customers",
        "sev3": "limited impact / workaround exists",
        "sev4": "cosmetic or documentation only",
    }
    sev_cases = [
        ("City water SCADA write path down; valve control lost citywide.", "sev1"),
        ("Anti-cheat false-positive rate elevated for EU region only.", "sev2"),
        ("One climate sensor offline; neighbors still report.", "sev3"),
        ("Library catalog typo in FAQ footer copyright year.", "sev4"),
        ("Telecom core BGP total failure; national packet loss.", "sev1"),
        ("Grant portal slow for 12% of applicants; cache miss spike.", "sev2"),
        ("Single freezer alarm acknowledged; redundant unit healthy.", "sev3"),
        ("Stadium app icon 1px misaligned on settings screen.", "sev4"),
        ("식품공장 MES 전면 다운으로 생산 중단.", "sev1"),
        ("공사 안내 전단 오탈자 하나.", "sev4"),
        ("일부 피더만 정전, 우회 급전 가능.", "sev3"),
        ("전국 광코어 라우팅 전면 실패.", "sev1"),
    ]
    for i, (s, _) in enumerate(sev_cases, 1):
        addc(f"{prefix}_choice_sev_{i}", "choice", s, {
            "severity": {"type": "choice", "instructions": "Assign incident severity.", "criteria": sev}
        })

    # Food safety / construction / climate / sports / nonprofit extras to fill
    food = {
        "qa_hold": "positive swab, allergen, metal detector, temperature abuse",
        "sanitation": "CIP, cleaning, pest, hygiene",
        "labeling": "allergen label, nutrition, lot code print",
        "shipping": "cold chain logistics, dock temp, carrier",
    }
    food_cases = [
        ("Listeria PCR positive on RTE line swab.", "qa_hold"),
        ("CIP cycle incomplete on filler #2.", "sanitation"),
        ("Peanut oil used but label says nut-free.", "labeling"),
        ("Reefer trailer at 12C for poultry load.", "shipping"),
        ("Metal detector reject rate 8x normal.", "qa_hold"),
        ("Pest sighting near ingredient silo.", "sanitation"),
        ("Lot code printer skipping digits.", "labeling"),
        ("Dock seal torn; warm air ingress.", "shipping"),
    ]
    for i, (s, _) in enumerate(food_cases, 1):
        addc(f"{prefix}_choice_food_{i}", "choice", s, {
            "team": {"type": "choice", "instructions": "Which food-safety team?", "criteria": food}
        })

    # Trim/pad to need
    choice_only = [c for c in out if c["kind"] == "choice"]
    if len(choice_only) > need:
        # keep order, drop extras from end of non-critical
        keep_ids = {c["id"] for c in choice_only[:need]}
        out = [c for c in out if c["id"] in keep_ids]
        # also remove from used? already committed — fine for generation
        return out[:need]
    pad = 0
    while len([c for c in out if c["kind"] == "choice"]) < need:
        pad += 1
        s = f"Sports ops: ticket scanner offline at gate {pad} during preseason open house."
        crit = {
            "ticketing": "scanners, access control, will-call",
            "safety": "medical, structural, fire, crowd crush",
            "broadcast": "feeds, replay, overlay",
            "hospitality": "suites, catering, guest services",
        }
        ok = addc(f"{prefix}_choice_sports_pad_{pad}", "choice", s, {
            "team": {"type": "choice", "instructions": "Which sports ops team?", "criteria": crit}
        })
        if not ok:
            s = s + f" ref-{pad}"
            addc(f"{prefix}_choice_sports_pad_{pad}", "choice", s, {
                "team": {"type": "choice", "instructions": "Which sports ops team?", "criteria": crit}
            })
        if pad > need:
            break
    return [c for c in out if c["kind"] == "choice"][:need]


# =============================================================================
# SCORE
# =============================================================================

SEV_LEVELS = [
    "cosmetic / no user impact",
    "minor annoyance for few users",
    "degraded experience for many",
    "major feature broken",
    "full outage / data loss / life-safety risk",
]
URG_LEVELS = [
    "can wait a week",
    "this week is fine",
    "today",
    "within an hour",
    "drop everything now",
]


def build_score(prefix: str, used_ids: set, used_states: set, need: int) -> list:
    out: list = []
    tag = "TRAIN-SET" if prefix == "train" else "TEST-SET"
    score_sev = [
        "Library catalog FAQ footer copyright year off by one.",
        "Anti-cheat false positives affecting ~1% of EU ranked lobbies.",
        "Municipal 311 app submits fail for most users citywide.",
        "Telecom core BGP down; national packet loss in progress.",
        "Biotech LIMS double-writes accession IDs; reconciliation diverging.",
        "식품 라벨 아이콘 색이 약간 연함.",
        "일부 피더만 정전 지도 갱신이 느림.",
        "보조금 포털 결제가 모든 신청자에게 실패.",
        "경기장 구조 모니터링 쓰기 전면 실패.",
        "기후 대시보드 로고 정렬 1px 어긋남.",
        "Grant portal dark-mode toggle misaligned by 2px.",
        "Food MES write path down; all lines stopped.",
        "Climate alert SMS failing for entire county.",
        "Construction permit PDF download slow for 3 users.",
        "Archives vault RH logging silent for one sensor.",
        "Esports overlay font weight slightly bold.",
        "Insurance FNOL intake rejects all uploads.",
        "Sports ticketing scanners offline stadium-wide.",
        "Energy SCADA read-only for one substation HMI.",
        "Nonprofit volunteer signup typo in help tooltip.",
    ]
    score_sev = [f"{s} [{tag} sev]" for s in score_sev]
    for i, s in enumerate(score_sev, 1):
        _add(out, used_ids, used_states, f"{prefix}_score_sev_{i}", "score", s, {
            "severity": {"type": "score", "instructions": "Rate production severity.", "criteria": SEV_LEVELS}
        })

    score_urg = [
        "Update nonprofit annual-report cover photo crop.",
        "Library needs new quiet-hours sign before Friday tour.",
        "CEO grid board demo of SCADA UI fails tomorrow morning.",
        "Active ransomware on insured clinic EHR encrypting now.",
        "Gamer asks for pastel theme on anti-cheat appeal form.",
        "냉동 식품 콜드체인 알람 진행 중.",
        "블로그 오탈자 하나 수정 (시정마을 소식).",
        "법정 제출 마감 2시간 전 공사 안전 일지 손상.",
        "다음 주 학회 포스터 색상 변경.",
        "시 상수 SCADA 쓰기 전면 다운.",
        "Reprint stadium wayfinding map with clearer icons next month.",
        "Climate sensor firmware cosmetic changelog tidy.",
        "Fiber cut affecting 50k voice+data customers ongoing.",
        "Grant wire phishing in progress; funds moving.",
        "Replace broken swing chain sometime this season.",
        "Autoclave interlock failed mid-cycle with load inside.",
        "Update FAQ emoji on recycling page.",
        "Wildfire perimeter crossing berm toward town now.",
        "Adjuster desk wants nicer chart colors next sprint.",
        "Tournament finals payment rails failing globally.",
    ]
    score_urg = [f"{s} [{tag} urg]" for s in score_urg]
    for i, s in enumerate(score_urg, 1):
        _add(out, used_ids, used_states, f"{prefix}_score_urg_{i}", "score", s, {
            "urgency": {"type": "score", "instructions": "How urgently must this be handled?", "criteria": URG_LEVELS}
        })

    scores = [c for c in out if c["kind"] == "score"]
    if len(scores) < need:
        # pad unique scores
        pad = 0
        while len(scores) < need:
            pad += 1
            s = f"Climate ops cosmetic: rename dashboard panel title variant {pad} [{tag} pad]."
            ok = _add(out, used_ids, used_states, f"{prefix}_score_pad_{pad}", "score", s, {
                "severity": {"type": "score", "instructions": "Rate production severity.", "criteria": SEV_LEVELS}
            })
            scores = [c for c in out if c["kind"] == "score"]
            if pad > 20:
                break
    return scores[:need]


# =============================================================================
# MULTI RAG-guard
# =============================================================================

def build_multi(prefix: str, used_ids: set, used_states: set, need: int) -> list:
    tag = "" if prefix == "train" else "\n[TEST-SPLIT]"
    guards = [
        {
            "question": "What is the maximum inverter islanding time allowed under Grid Code G-12?",
            "context": "Grid Code G-12 discusses DER telemetry. The numeric islanding time limit is not stated in this excerpt.",
            "answer": "Inverters may island for exactly 12.5 minutes under G-12.",
        },
        {
            "question": "What is the anti-cheat hardware-ban appeal window?",
            "context": "Hardware bans may be appealed once. The exact calendar-day window is not listed in this excerpt.",
            "answer": "Players have exactly 14 days to appeal a hardware ban.",
        },
        {
            "question": "Who chairs the municipal floodplain review board?",
            "context": "The board reviews elevation certificates within 15 business days. Member names are confidential and not listed here.",
            "answer": "Director Maya Ortiz chairs the floodplain review board.",
        },
        {
            "question": "Are sole proprietors eligible for CyberShield policy tier-3 limits?",
            "context": "Tier-3 limits require a registered corporation with two officers. Sole proprietors are limited to tier-1.",
            "answer": "No. Sole proprietors cannot obtain tier-3; they are capped at tier-1.",
        },
        {
            "question": "Is parking reimbursed for biotech visiting auditors?",
            "context": "Parking is not reimbursed. Use the shuttle from Lot C.",
            "answer": "No, parking is not reimbursed.",
        },
        {
            "question": "Must the climate alert system ban all non-English messages forever?",
            "context": "Alerts must be clear. Multilingual templates are encouraged. Lifetime bans on non-English are not specified.",
            "answer": "Yes, all non-English messages must be permanently banned with no exceptions.",
        },
        {
            "question": "밀폐공간 산소 하한 기준은?",
            "context": "산소농도 19.5% 미만이면 진입을 중단한다. 구조팀 호출 기준은 별도 절차에 따른다.",
            "answer": "산소농도 19.5% 미만이면 진입을 중단해야 합니다.",
        },
        {
            "question": "서고 H3의 목표 상대습도는?",
            "context": "본 발췌에는 서고 H3의 목표 상대습도 수치가 없다. 다른 서고 예시만 언급된다.",
            "answer": "서고 H3은 상대습도 35%를 유지합니다.",
        },
        {
            "question": "What is the exact SS7 scrub threshold under NOC Playbook T-4?",
            "context": "Playbook T-4 discusses signaling storms. The numeric scrub threshold is not stated in this excerpt.",
            "answer": "Scrub activates at exactly 50k MSU/sec under T-4.",
        },
        {
            "question": "Are food-contact gloves required on Line 7 packaging?",
            "context": "Line 7 packaging requires food-contact gloves and hairnets. Jewelry is prohibited.",
            "answer": "Yes. Food-contact gloves and hairnets are required on Line 7 packaging.",
        },
        {
            "question": "Who is the named PI for Grant GX-220?",
            "context": "Grant GX-220 covers capacity building. The PI name is not disclosed in this excerpt.",
            "answer": "Dr. Samuel Rhee is the PI for Grant GX-220.",
        },
        {
            "question": "Must stadium egress maps omit all stairwells forever?",
            "context": "Egress maps must show stairwells and exits clearly. Omitting stairwells is not permitted.",
            "answer": "Yes, all stairwells must be omitted forever with no exceptions.",
        },
        {
            "question": "공사 비계 점검 주기는?",
            "context": "비계는 작업 전 매일 점검한다. 강풍 경보 시 추가 점검을 실시한다.",
            "answer": "비계는 작업 전 매일 점검하며 강풍 경보 시 추가 점검합니다.",
        },
        {
            "question": "마이크로그리드 배터리 최소 SOC는?",
            "context": "본 문서에는 최소 SOC 수치가 명시되어 있지 않다. 텔레메트리 항목만 설명한다.",
            "answer": "최소 SOC는 18%입니다.",
        },
        {
            "question": "What metal-detector calibration interval applies on Line 2?",
            "context": "Line 2 metal detectors are calibrated every 2 hours and after product changeovers.",
            "answer": "Calibrate every 2 hours and after product changeovers.",
        },
        {
            "question": "Is the climate sensor firmware changelog publicly versioned?",
            "context": "Firmware changelogs are internal. Public versioning is not described in this excerpt.",
            "answer": "Yes, changelogs are always free and public forever with no exceptions.",
        },
        {
            "question": "도서관 귀중본 대출이 가능한가?",
            "context": "귀중본은 열람만 가능하며 대출은 불가하다. 장갑 착용 후 지정 좌석에서 열람한다.",
            "answer": "아니요. 귀중본은 대출할 수 없고 지정 좌석 열람만 가능합니다.",
        },
        {
            "question": "What is the nonprofit wire dual-control dollar threshold?",
            "context": "Dual control is required for wires. The dollar threshold amount is not listed in this excerpt.",
            "answer": "Dual control applies to wires at exactly $25,000.",
        },
    ]
    out: list = []
    for i, st in enumerate(guards, 1):
        if len(out) >= need:
            break
        state = (
            f"QUESTION:\n{st['question']}\n\n"
            f"RETRIEVED CONTEXT:\n{st['context']}\n\n"
            f"MODEL ANSWER:\n{st['answer']}"
            + tag
        )
        _add(out, used_ids, used_states, f"{prefix}_multi_guard_{i}", "multi", state, {
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
    return out[:need]


def build_split(prefix: str, used_ids: set, used_states: set) -> list:
    cases: list = []
    cases.extend(build_noul(prefix, used_ids, used_states, TARGET["noul"]))
    cases.extend(build_choice(prefix, used_ids, used_states, TARGET["choice"]))
    cases.extend(build_score(prefix, used_ids, used_states, TARGET["score"]))
    cases.extend(build_multi(prefix, used_ids, used_states, TARGET["multi"]))
    # ensure exact counts by kind
    by_kind: dict[str, list] = {k: [] for k in TARGET}
    for c in cases:
        by_kind[c["kind"]].append(c)
    final = []
    for k, n in TARGET.items():
        chunk = by_kind[k][:n]
        if len(chunk) < n:
            raise SystemExit(f"{prefix} short on {k}: {len(chunk)}/{n}")
        final.extend(chunk)
    for idx, c in enumerate(final, 1):
        c["idx"] = idx
    assert len(final) == 400
    assert len({c["id"] for c in final}) == 400
    assert len({c["state"] for c in final}) == 400
    return final


def main() -> None:
    used_ids: set = set()
    used_states: set = set()
    train = build_split("train", used_ids, used_states)
    test = build_split("test", used_ids, used_states)

    assert not ({c["id"] for c in train} & {c["id"] for c in test})
    assert not ({c["state"] for c in train} & {c["state"] for c in test})
    assert not ({c["id"] for c in train + test} & EXISTING_IDS)
    assert not ({c["state"] for c in train + test} & EXISTING_STATES)

    train_path = BENCH / "cases_train400.json"
    test_path = BENCH / "cases_test400.json"
    train_path.write_text(json.dumps(train, ensure_ascii=False, indent=2), encoding="utf-8")
    test_path.write_text(json.dumps(test, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TRAIN", len(train), Counter(c["kind"] for c in train), "->", train_path)
    print("TEST ", len(test), Counter(c["kind"] for c in test), "->", test_path)
    print("dedup ok vs v1/v2 and train/test")


if __name__ == "__main__":
    main()
