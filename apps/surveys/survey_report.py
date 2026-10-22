"""Customer Report metrics for the eight-question questionnaire.

Read-only. Only surveys whose ``template_key`` is the current questionnaire
version are aggregated, so legacy/custom surveys are never mixed in. Questions
are identified by ``config["key"]`` and options by their position inside the
question, never by database IDs, so several surveys of the same version can be
combined. Every ratio guards against a zero denominator and returns ``None``
("no data") instead of 0, NaN or a fabricated value.
"""
from collections import Counter, defaultdict
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

from django.utils import timezone

from .constants import RESPONSE_SUBMITTED, SurveyStatus
from .models import Survey, SurveyAnswer, SurveyOption, SurveyQuestion, SurveyResponse
from .questionnaire import NOT_USED, TEMPLATE_KEY, short_label

COMMENT_LIMIT = 10
COMMENT_PREVIEW = 120
TREND_MONTHS = 6
CSAT_RANGE = (1, 5)
NPS_RANGE = (1, 10)
MATRIX_RANGE = (1, 5)


# tv4: làm tròn nửa lên (xa số 0) cho % và điểm báo cáo
def round_half_up(value, places=0):
    """Round half away from zero (Python's round() uses banker's rounding)."""
    if value is None:
        return None
    if isinstance(value, Fraction):
        number = Decimal(value.numerator) / Decimal(value.denominator)
    else:
        number = Decimal(str(value))
    rounded = number.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    return int(rounded) if places == 0 else float(rounded)


# tv4: tính % có chặn mẫu số 0 (trả None = chưa có dữ liệu)
def percent(part, whole, places=1):
    return None if not whole else round_half_up(Fraction(part * 100, whole), places)


# tv4: trung bình có chặn danh sách rỗng
def average(values, places=1):
    return round_half_up(Fraction(sum(values), len(values)), places) if values else None


# tv4: nhãn mức NPS: >=50 Xuất sắc, 0–49 Tốt, <0 Cần cải thiện
def nps_level(score):
    """Owner rule: >=50 excellent, 0–49 good, <0 needs improvement."""
    if score is None:
        return None
    return "excellent" if score >= 50 else "good" if score >= 0 else "poor"


# tv4: tính NPS câu 7 (Promoter 9–10, Passive 7–8, Detractor 1–6)
def compute_nps(scores):
    """Promoter 9–10, Passive 7–8, Detractor 1–6 on the 1–10 scale."""
    low, high = NPS_RANGE
    valid = [s for s in scores if low <= s <= high]
    promoters = sum(1 for s in valid if s >= 9)
    passives = sum(1 for s in valid if 7 <= s <= 8)
    detractors = sum(1 for s in valid if s <= 6)
    total = len(valid)
    score = round_half_up(Fraction((promoters - detractors) * 100, total)) if total else None
    counts = Counter(valid)
    return {
        "score": score, "level": nps_level(score), "respondents": total,
        "promoters": promoters, "passives": passives, "detractors": detractors,
        "promoter_pct": percent(promoters, total), "passive_pct": percent(passives, total),
        "detractor_pct": percent(detractors, total),
        "distribution": [{"score": s, "n": counts.get(s, 0), "pct": percent(counts.get(s, 0), total)}
                         for s in range(low, high + 1)],
    }


# tv4: ngày đầu tháng lùi `back` tháng
def _month_start(day, back=0):
    index = day.year * 12 + day.month - 1 - back
    return date(index // 12, index % 12 + 1, 1)


# tv4: so sánh số lượt tháng này với tháng trước
def _month_change(this_month, last_month):
    if not last_month:
        return {"pct": None, "direction": None}
    pct = round_half_up(Fraction((this_month - last_month) * 100, last_month))
    return {"pct": abs(pct), "direction": "up" if pct > 0 else "down" if pct < 0 else "flat"}


# tv4: nạp câu hỏi/lựa chọn/phản hồi đã nộp của bộ 8 câu
def _load(surveys):
    """Return (responses, answers per response/key, option metadata) for submitted responses."""
    questions = {q["question_id"]: q for q in SurveyQuestion.objects.filter(survey__in=surveys)
                 .values("question_id", "config")}
    key_of = {qid: (q["config"] or {}).get("key", "") for qid, q in questions.items()}
    other_ids = {(q["config"] or {}).get("other_option_id") for q in questions.values()} - {None}
    options, position = {}, Counter()
    for row in SurveyOption.objects.filter(question_id__in=questions).order_by(
            "question_id", "sort_order", "option_id").values("option_id", "question_id", "option_text"):
        index = position[row["question_id"]]
        position[row["question_id"]] += 1
        options[row["option_id"]] = {"question_id": row["question_id"], "index": index,
                                     "text": row["option_text"], "is_other": row["option_id"] in other_ids}
    responses = list(SurveyResponse.objects.filter(recipient__survey__in=surveys, status=RESPONSE_SUBMITTED)
                     .values("response_id", "submitted_at", "recipient__customer__full_name")
                     .order_by("-submitted_at", "-response_id"))
    answers = defaultdict(lambda: defaultdict(list))
    for row in SurveyAnswer.objects.filter(response__recipient__survey__in=surveys,
                                           response__status=RESPONSE_SUBMITTED,
                                           question_id__in=questions).values(
            "response_id", "question_id", "option_id", "answer_text", "rating_value"):
        option = options.get(row["option_id"])
        if option is not None and option["question_id"] != row["question_id"]:
            continue  # an option that does not belong to the question is never counted
        row["option"] = option
        answers[row["response_id"]][key_of[row["question_id"]]].append(row)
    return responses, answers


# tv4: các lựa chọn khác nhau của 1 phản hồi cho câu chọn
def _choices(rows):
    """Distinct options a response picked for one choice question."""
    seen = {}
    for row in rows:
        if row["option"] is not None:
            seen.setdefault(row["option"]["index"], row)
    return seen


# tv4: điểm hợp lệ của 1 phản hồi cho câu thang điểm
def _rating(rows, bounds):
    low, high = bounds
    values = [r["rating_value"] for r in rows if r["option_id"] is None and r["rating_value"] is not None
              and low <= r["rating_value"] <= high]
    return values[0] if values else None


# tv4: nhãn ngắn cho từng vị trí lựa chọn
def _option_labels(key, responses, answers):
    """Label per option index; the newest survey's wording wins (responses are newest first)."""
    labels = {}
    for response in responses:
        for row in answers[response["response_id"]].get(key, []):
            option = row["option"]
            if option is not None:
                labels.setdefault(option["index"], short_label(key, option["index"], option["text"]))
    return labels


# tv4: đếm người chọn và % theo người trả lời hợp lệ (câu 1, câu 2)
def _choice_rows(key, responses, answers):
    respondents, counts = 0, Counter()
    for response in responses:
        picked = _choices(answers[response["response_id"]].get(key, []))
        if picked:
            respondents += 1
            counts.update(picked.keys())
    labels = _option_labels(key, responses, answers)
    rows = [{"index": i, "label": labels[i], "n": n, "pct": percent(n, respondents)} for i, n in counts.items()]
    rows.sort(key=lambda r: (-r["n"], r["index"]))
    return respondents, rows


# tv4: donut câu 6: % lượt chọn, % người trả lời, gộp lát Khác
def _brands(responses, answers):
    respondents, counts, other_index, other_texts = 0, Counter(), None, []
    for response in responses:
        picked = _choices(answers[response["response_id"]].get("future_brands", []))
        if not picked:
            continue
        respondents += 1
        counts.update(picked.keys())
        for index, row in picked.items():
            if row["option"]["is_other"]:
                other_index = index
                text = (row["answer_text"] or "").strip()
                if text:
                    other_texts.append({"text": text, "customer": _customer(response),
                                        "submitted_at": response["submitted_at"]})
    selections = sum(counts.values())
    labels = _option_labels("future_brands", responses, answers)
    rows = [{"index": i, "label": labels[i], "n": n, "is_other": i == other_index,
             "share_pct": percent(n, selections), "respondent_pct": percent(n, respondents)}
            for i, n in counts.items()]
    rows.sort(key=lambda r: (r["is_other"], -r["n"], r["index"]))  # one "Other" slice, kept last
    return {"respondents": respondents, "selections": selections, "rows": rows, "other_texts": other_texts}


# tv4: tên khách hoặc None (Khách ẩn danh)
def _customer(response):
    name = (response.get("recipient__customer__full_name") or "").strip()
    return name or None


# tv4: tag cảm xúc theo điểm câu 3
def _sentiment(csat):
    if csat is None:
        return None
    return "positive" if csat >= 4 else "neutral" if csat == 3 else "negative"


# tv4: câu 4: điểm TB từng tiêu chí, loại Không sử dụng
def _criteria(responses, answers):
    low, high = MATRIX_RANGE
    labels, scores, not_used = {}, defaultdict(list), Counter()
    for response in responses:
        for row in answers[response["response_id"]].get("service_criteria", []):
            option = row["option"]
            if option is None:
                continue
            labels.setdefault(option["index"], short_label("service_criteria", option["index"], option["text"]))
            if row["rating_value"] is None and row["answer_text"] == NOT_USED:
                not_used[option["index"]] += 1
            elif row["answer_text"] is None and row["rating_value"] is not None and low <= row["rating_value"] <= high:
                scores[option["index"]].append(row["rating_value"])
    total = len(responses)
    return [{"label": labels[i], "avg": average(scores[i]), "scored": len(scores[i]),
             "not_used": not_used[i], "unanswered": max(total - len(scores[i]) - not_used[i], 0)}
            for i in sorted(labels)]


# tv4: CSAT câu 3 kèm chuỗi sao
def _csat(values):
    avg, scale = average(values), CSAT_RANGE[1]
    filled = round_half_up(avg) if avg is not None else 0
    return {"avg": avg, "respondents": len(values), "scale_max": scale,
            "stars": "★" * filled + "☆" * (scale - filled) if avg is not None else ""}


# tv4: khảo sát bộ 8 câu đã phát hành (không tính Nháp) – phạm vi của phần kết quả khảo sát
def published_questionnaire_surveys():
    return Survey.objects.filter(template_key=TEMPLATE_KEY).exclude(status=SurveyStatus.DRAFT)


# tv4: 4.1.7 số liệu kết quả khảo sát bộ 8 câu trên Customer Report
def build_report(survey=None, now=None):
    """Metrics for one questionnaire survey, or for every published survey of the current version.

    Chỉ lượt trả lời SUBMITTED; câu hỏi nhận diện bằng config["key"] nên chỉ gộp các khảo sát
    cùng phiên bản (cùng câu hỏi, cùng thang đo).
    - total.count: số lượt trả lời hợp lệ; this_month/last_month theo giờ Asia/Ho_Chi_Minh.
    - CSAT = trung bình điểm câu 3 (overall_satisfaction, thang 1–5) của các lượt có điểm hợp lệ.
    - NPS (câu 7, recommendation, thang 1–10) = %Promoter (9–10) − %Detractor (1–6), làm tròn
      nửa lên; Passive 7–8; mẫu số = số lượt có điểm câu 7 hợp lệ.
    - % chọn câu 1/2 = người chọn / người trả lời hợp lệ của câu (câu 1 tổng có thể > 100%).
    - Câu 4: trung bình mỗi tiêu chí trên điểm 1–5, loại "Không sử dụng" và chưa trả lời.
    Không có dữ liệu → None, không 0 giả. Lượt trả lời của khách sau này bị khóa/xóa vẫn được tính
    (hợp lệ tại thời điểm nộp); tên khách đã xóa hiển thị là ẩn danh.
    """
    now = timezone.localtime(now or timezone.now())
    surveys = published_questionnaire_surveys()
    if survey is not None:
        surveys = surveys.filter(pk=survey.pk)
    responses, answers = _load(surveys)

    this_month, last_month = _month_start(now.date()), _month_start(now.date(), 1)
    month_counts = Counter()
    for response in responses:
        if response["submitted_at"]:
            local = timezone.localtime(response["submitted_at"]).date()
            month_counts[local.replace(day=1)] += 1

    csat_by_response, csat_by_month, nps_scores = {}, defaultdict(list), []
    for response in responses:
        rid = response["response_id"]
        csat = _rating(answers[rid].get("overall_satisfaction", []), CSAT_RANGE)
        if csat is not None:
            csat_by_response[rid] = csat
            if response["submitted_at"]:
                month = timezone.localtime(response["submitted_at"]).date().replace(day=1)
                csat_by_month[month].append(csat)
        score = _rating(answers[rid].get("recommendation", []), NPS_RANGE)
        if score is not None:
            nps_scores.append(score)

    segment_respondents, segment_rows = _choice_rows("playing_frequency", responses, answers)
    purchase_respondents, purchase_rows = _choice_rows("purchases", responses, answers)
    purchase_labels = _option_labels("purchases", responses, answers)

    comments = []
    for response in responses:  # newest first
        rid = response["response_id"]
        text = next((r["answer_text"].strip() for r in answers[rid].get("suggestions", [])
                     if r["answer_text"] and r["answer_text"].strip()), "")
        if not text:
            continue
        topics = [purchase_labels[i] for i in sorted(_choices(answers[rid].get("purchases", [])))]
        comments.append({"customer": _customer(response), "text": text,
                         "preview": text if len(text) <= COMMENT_PREVIEW else text[:COMMENT_PREVIEW - 1].rstrip() + "…",
                         "is_long": len(text) > COMMENT_PREVIEW, "submitted_at": response["submitted_at"],
                         "sentiment": _sentiment(csat_by_response.get(rid)), "topics": topics})
        if len(comments) == COMMENT_LIMIT:
            break

    trend = []
    for back in range(TREND_MONTHS - 1, -1, -1):
        month = _month_start(now.date(), back)
        values = csat_by_month.get(month, [])
        trend.append({"label": month.strftime("%m/%Y"), "avg": average(values), "n": len(values)})

    return {
        "survey_count": surveys.count(),
        "total": {"count": len(responses), "this_month": month_counts[this_month],
                  "last_month": month_counts[last_month],
                  **_month_change(month_counts[this_month], month_counts[last_month])},
        "csat": _csat(list(csat_by_response.values())),
        "nps": compute_nps(nps_scores),
        "segment": ({**segment_rows[0], "respondents": segment_respondents} if segment_rows else None),
        "segments": segment_rows,
        "purchases": {"respondents": purchase_respondents, "rows": purchase_rows},
        "brands": _brands(responses, answers),
        "csat_trend": trend,
        "comments": comments,
        "criteria": _criteria(responses, answers),
    }
