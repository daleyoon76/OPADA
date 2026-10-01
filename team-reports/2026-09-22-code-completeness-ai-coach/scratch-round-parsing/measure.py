import sys, json, pathlib
sys.path.insert(0, "/Users/user/Documents/Dev/Hometest_op/src")
import server as S

SURVEY = pathlib.Path("/Users/user/Documents/Dev/.opada-survey")
samples = json.load(open(SURVEY / "samples.json"))
by_idx = {s["idx"]: s for s in samples}

def api_value(*a, **k):
    return ""

results = []
for idx in sorted(by_idx):
    s = by_idx[idx]
    html_path = SURVEY / "html" / f"pbanc_{idx:02d}.html"
    if not html_path.exists():
        results.append({"idx": idx, "error": "no html file"})
        continue
    text = html_path.read_text(errors="replace")
    inputs = S.hidden_inputs(text)

    # replicate server.py:2130-2146 logic exactly (api_entries assumed empty - no API key on this box)
    if inputs.get("pbctBgngDt") and inputs.get("pbctLastDdlnDt"):
        bid_period = f"{inputs['pbctBgngDt']} ~ {inputs['pbctLastDdlnDt']}"
        bid_period_source = "hidden_input"
    else:
        bid_period = S.values_after_label(text, "입찰기간")
        bid_period_source = "values_after_label" if bid_period else "none"
    api_start = ""
    api_end = ""
    if not bid_period and (api_start or api_end):
        bid_period = f"{api_start} ~ {api_end}".strip(" ~")
        bid_period_source = "api_fallback"
    bid_deadline = inputs.get("pbctLastDdlnDt") or api_end

    lowst_raw = (
        inputs.get("lowstBidPrc")
        or S.values_after_label(text, "공매예정가격(원)")
    )
    minimum_bid = S.minimum_bid_value(inputs, lowst_raw)
    round_value = S.values_after_label(text, "회차")

    # detect round-table structure: <th>...회차...</th> style table under "입찰일정 및 장소"
    sections = S.split_sections(text)
    schedule_section = sections.get("입찰일정 및 장소", "")
    has_round_table = bool(schedule_section) and ("<th" in schedule_section.lower())
    has_round_word = "회차" in schedule_section

    results.append({
        "idx": idx,
        "assetType": s.get("prptDvsnNm"),
        "disposition": s.get("dpslMtdNm"),
        "hasScheduleSection": bool(schedule_section),
        "hasRoundTable": has_round_table,
        "hasRoundWord": has_round_word,
        "bidPeriod": bid_period,
        "bidPeriodSource": bid_period_source,
        "bidPeriodEmpty": bid_period == "",
        "minimumBid": minimum_bid,
        "minimumBidEmpty": minimum_bid in ("", None),
        "roundField": round_value,
        "roundFieldEmpty": round_value == "",
        "hidden_pbctBgngDt": inputs.get("pbctBgngDt", ""),
        "hidden_pbctLastDdlnDt": inputs.get("pbctLastDdlnDt", ""),
        "hidden_lowstBidPrc": inputs.get("lowstBidPrc", ""),
    })

for r in results:
    print(json.dumps(r, ensure_ascii=False))

empty_period = sum(1 for r in results if r.get("bidPeriodEmpty"))
empty_price = sum(1 for r in results if r.get("minimumBidEmpty"))
round_table = sum(1 for r in results if r.get("hasRoundTable"))
print("---SUMMARY---")
print(f"total={len(results)} bidPeriodEmpty={empty_period} minimumBidEmpty={empty_price} hasRoundTable={round_table}")
