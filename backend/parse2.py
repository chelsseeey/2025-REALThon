import os
import base64
import json
from openai import OpenAI

# 1) 클라이언트 생성
# 환경 변수에서 API 키를 읽거나, 직접 입력하세요
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

def encode_image(image_path: str) -> str:
    """이미지 파일을 base64 문자열로 인코딩"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# === 여기만 너 상황에 맞게 바꾸면 됨 ===
exam_id = "student_2024_math_midterm"   # 이 시트의 ID (학번+시험종류 등 네가 정하기)
image_path = "문제지.pdf"  # 손글씨 답안 이미지 경로
# =======================================

base64_image = encode_image(image_path)

system_prompt = """
당신은 손글씨 시험 답안을 JSON 구조로 파싱하는 보조자입니다.

입력: 한 학생의 시험지(또는 한 문제에 대한 손글씨 답안) 이미지
출력: 아래 스키마를 따르는 JSON 하나.

스키마:

{
  "exam_id": string,
  "problems": [
    {
      "problem_number": integer,
      "subparts": [
        {
          "label": string,           // "a", "b", "c" 등. 소문자. 서브파트가 없으면 "a"로 둠.
          "is_blank": boolean,       // 이 서브파트가 완전히 비어 있으면 true, 아니면 false
          "contents": [
            {
              "index": integer,      // 0부터 시작하여 같은 subpart 내에서 1씩 증가
              "type": "text" | "equation",
              "value": string,       // type == "text" 일 때만: 손글씨 문장을 가능한 한 그대로 적기
              "raw": string,         // type == "equation" 일 때만: 손글씨 수식을 가능한 한 그대로 적기
              "latex": string,       // type == "equation" 일 때만: 가능하면 LaTeX로 정리, 못하면 raw와 비슷하게 작성
              "confidence": number   // 0.0 ~ 1.0 사이의 신뢰도 추정값
            }
          ]
        }
      ]
    }
  ]
}

규칙:

- exam_id 는 사용자로부터 전달된 값을 그대로 사용하세요 (임의로 변경하지 마세요).
- problem_number 는 시험지에 보이는 "1.", "문제 1" 등을 보고 정수로 추론하세요.
  - 이미지에 문제 1만 있다면 problem_number=1 하나만 넣으면 됩니다.
- (a), (b) 등의 표기가 보이면 label 에 "a", "b" 로 넣으세요.
  - (a)/(b) 구분이 없고 그냥 하나의 풀이면 label 을 "a" 로 두고 subparts 에 1개만 넣으세요.
- is_blank:
  - 해당 subpart 안에 손글씨 내용이 거의 없거나 아예 없는 경우 true
  - 조금이라도 내용이 있으면 false
- contents:
  - 손글씨를 위에서부터 읽으며, 문장과 수식을 순서대로 나열하세요.
  - 자연어 문장/설명은 type="text", value 에 내용을 적고, raw/latex 는 사용하지 않습니다.
  - 수식/공식은 type="equation", raw 에 손글씨 그대로의 표현, latex 에 LaTeX 표현을 적습니다.
- confidence:
  - 각 항목마다 0.0~1.0 범위에서 모델이 인식에 얼마나 자신 있는지 추정해서 적으세요.
  - 대략적인 값이면 됩니다. (예: 확신 높음=0.95, 애매함=0.6 등)

중요:
- 손글씨 자체를 최대한 그대로 옮기는 것이 목적입니다. 새로운 설명을 덧붙이거나 의미를 요약하지 마세요.
- JSON 이외의 어떤 텍스트도 출력하지 마세요.
"""

response = client.chat.completions.create(
    model="gpt-4o",  # 이미지 입력이 가능한 모델
    messages=[
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"이 이미지는 시험 '{exam_id}' 의 일부입니다. "
                        "위에서 정의된 JSON 스키마에 맞게 이 시험지를 파싱해 주세요. "
                        f"'exam_id' 필드에는 반드시 \"{exam_id}\" 를 그대로 넣으세요."
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    },
                },
            ],
        },
    ],
    response_format={"type": "json_object"},  # JSON 강제
)

json_text = response.choices[0].message.content
data = json.loads(json_text)

print(json.dumps(data, ensure_ascii=False, indent=2))

# 필요하면 파일로 저장
with open("parsed_exam3.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
