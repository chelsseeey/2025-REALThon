import os
import base64
import json
import re
from openai import OpenAI

client = OpenAI(api_key="")  # <- 키 넣기


def encode_image(image_path: str) -> str:
    """이미지를 base64 data URL 형태로 인코딩"""
    import mimetypes
    mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"


def call_openai_for_problems(image_path: str) -> dict:
    """
    모델에게는 '문제 텍스트 + 배점'만 뽑게 한다.
    question_count는 계산하지 않음.
    """
    image_data_url = encode_image(image_path)

    system_prompt = """
당신은 한국어 수학 시험지를 구조화하는 도우미입니다.
이미지에서 각 문제의 번호, 문제 전체 텍스트, 문제의 배점만 추출해야 합니다.
"""

    user_prompt = """
이미지에는 1, 2, 3 처럼 번호가 매겨진 '큰 문제'들이 있고,
각 문제의 본문 끝에는 "[40점]", "[30점]"과 같이 배점이 적혀 있습니다.

각 문제에 대해 다음 정보를 추출해 주세요.

반환 형식(중요!):

{
  "problems": [
    {
      "problem_index": 1,
      "raw_text": "문제 1 전체 텍스트 (지문 + 소문항 포함, 배점 표시는 빼도 됨)",
      "score": 40
    },
    {
      "problem_index": 2,
      "raw_text": "문제 2 전체 텍스트",
      "score": 30
    }
  ]
}

규칙:
- problems:
  - 페이지에 보이는 큰 문제들을 위에서부터 순서대로 problem_index 1, 2, 3... 으로 번호를 매깁니다.
- raw_text:
  - 해당 문제에 포함된 모든 문장을 하나의 문자열로 넣되, 다른 문제와 섞이지 않게 해주세요.
  - 소문항 (1), (2)..., ①, ②... 도 그대로 포함합니다.
- score:
  - 각 문제 끝의 "[40점]" 같은 표기에서 숫자만 뽑아 정수로 넣습니다.
- JSON 이외의 다른 텍스트는 절대 출력하지 마세요.
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",  # vision 지원 모델
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ],
            },
        ],
        max_tokens=1400,
    )

    content = resp.choices[0].message.content
    return json.loads(content)


def count_subquestions(text: str) -> int:
    """
    문제 텍스트에서 소문항 개수 세기.
    - (1), (2), (3) 형식
    - ①, ②, ③ 형식
    하나도 없으면 1로 간주.
    """
    # (1), ( 2 ) 등
    paren_nums = re.findall(r"\(\s*\d+\s*\)", text)
    # ①~⑨
    circled_nums = re.findall(r"[①②③④⑤⑥⑦⑧⑨]", text)

    cnt = len(paren_nums) + len(circled_nums)
    return cnt if cnt > 0 else 1


def parse_exam(image_path: str, output_json_path: str | None = None) -> dict:
    # 1단계: 문제/텍스트/배점만 모델에게서 받기
    raw = call_openai_for_problems(image_path)

    problems_out = []
    total_score = 0

    for p in raw.get("problems", []):
        idx = p.get("problem_index")
        text = p.get("raw_text", "")
        score = int(p.get("score", 0))

        q_count = count_subquestions(text)
        total_score += score

        # 🔽 여기에서 raw_text도 같이 저장
        problems_out.append(
            {
                "problem_index": idx,
                "question_count": q_count,
                "score": score,
                "raw_text": text,  # <- 문제 내용 저장
            }
        )

    result = {
        "problems": problems_out,
        "total_score": total_score,
    }

    if output_json_path:
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    return result


if __name__ == "__main__":
    img = "문제지.png"          # 네 이미지 파일
    out = "문제지_parsed.json"

    parsed = parse_exam(img, out)
    print(json.dumps(parsed, ensure_ascii=False, indent=2))
    print(f"\n저장 완료: {out}")
