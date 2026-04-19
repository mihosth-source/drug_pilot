HIGH_RISK_KEYWORDS = [
    "息苦しい", "呼吸困難", "意識", "胸痛", "けいれん",
    "全身の発疹", "アナフィラキシー", "倒れた", "強い腹痛"
]

CAUTION_KEYWORDS = [
    "妊娠", "授乳", "子ども", "高齢", "腎臓", "肝臓",
    "2回分", "倍量", "他人の薬", "飲み合わせ"
]


def detect_risk(user_query: str) -> str:
    query = user_query or ""
    for word in HIGH_RISK_KEYWORDS:
        if word in query:
            return "high"
    for word in CAUTION_KEYWORDS:
        if word in query:
            return "medium"
    return "low"


def emergency_answer(user_query: str) -> str:
    return (
        "安全のため、自己判断で続ける・中止すると決めず、できるだけ早く医師または薬剤師に相談してください。\n"
        "息苦しさ、意識の変化、全身の強い発疹、強い胸痛などがある場合は、早めの受診が必要です。\n"
        "緊急性が高いと感じる場合は救急要請も検討してください。"
    )
