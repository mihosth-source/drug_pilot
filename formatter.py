import re

REPLACEMENTS = {
    "禁忌": "使ってはいけない場合",
    "相互作用": "ほかの薬や食品との注意",
    "頓服": "症状が出たときだけ使う薬",
    "傾眠": "強い眠気",
    "消化器症状": "胃の不快感、吐き気、腹痛、下痢など",
    "用法・用量": "使い方と量",
    "服用": "飲むこと",
    "投与": "使うこと",
    "患者": "使う人",
}


def simplify_terms(text: str) -> str:
    if not text:
        return text
    out = text
    for src, dst in REPLACEMENTS.items():
        out = out.replace(src, dst)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def markdown_to_plain_bullets(text: str) -> str:
    if not text:
        return text
    out = text
    out = out.replace("### ", "").replace("## ", "").replace("# ", "")
    return out.strip()
