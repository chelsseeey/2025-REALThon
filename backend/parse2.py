import os
import base64
import json
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# OpenAI API 키를 환경변수에서 읽어오기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# 1) 클라이언트 생성
# 환경 변수에서 API 키를 읽거나, 직접 입력하세요
client = OpenAI(api_key=OPENAI_API_KEY)

def encode_image(image_path: str) -> str:
    """이미지 파일을 base64 문자열로 인코딩"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# === 여기만 너 상황에 맞게 바꾸면 됨 ===
student_code = "2271022"  # 학번 (이미지에서 추출하거나 직접 입력)
image_path = "답안지.png"  # 손글씨 답안 이미지 경로
# =======================================

base64_image = encode_image(image_path)

system_prompt = """
당신은 손글씨 시험 답안을 JSON 구조로 파싱하는 보조자입니다.

입력: 한 학생의 시험지 답안 이미지
출력: 아래 스키마를 따르는 JSON 하나.

스키마:

{
  "student_code": string,
  "answers": [
    {
      "question_number": integer,
      "answer_text": string,
      "score": integer
    }
  ]
}

규칙:

- student_code:
  - 이미지에서 "학번 : XXXX" 형식의 텍스트를 찾아서 학번을 문자열로 넣으세요.
  - 학번이 보이지 않으면 사용자가 제공한 값을 그대로 사용하세요.
- answers:
  - 시험지에 있는 모든 문항의 답안을 배열로 나열하세요.
  - question_number:
    - 시험지에 보이는 "1.", "문제 1", "문항 1" 등을 보고 정수로 추론하세요.
    - 순서대로 1, 2, 3... 으로 번호를 매깁니다.
  - answer_text:
    - 해당 문항에 대한 학생의 손글씨 답안을 가능한 한 그대로 텍스트로 옮기세요.
    - 수식이 있으면 LaTeX 형식으로 변환하거나, 가능한 한 읽기 쉬운 형태로 작성하세요.
    - 여러 줄에 걸쳐 있으면 공백으로 구분하여 하나의 문자열로 합치세요.
    - 답안이 비어있으면 빈 문자열("")로 넣으세요.
  - score:
    - 이미지에 점수가 표시되어 있으면 정수형 숫자로 넣으세요.
    - 점수가 보이지 않으면 0으로 넣으세요.

중요:
- 손글씨 답안을 최대한 그대로 옮기는 것이 목적입니다. 새로운 설명을 덧붙이거나 의미를 요약하지 마세요.
- JSON 이외의 어떤 텍스트도 출력하지 마세요.
- 반환 형식은 반드시 위 스키마와 정확히 일치해야 합니다.
- 예시 형식:
{
  "student_code": "2271100",
  "answers": [
    { "question_number": 1, "answer_text": "", "score": 14 },
    { "question_number": 2, "answer_text": "", "score": 26 },
    { "question_number": 3, "answer_text": "", "score": 16 }
  ]
}
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
                        f"이 이미지는 학번 '{student_code}' 학생의 답안지입니다. "
                        "위에서 정의된 JSON 스키마에 맞게 이 답안지를 파싱해 주세요. "
                        f"'student_code' 필드에는 반드시 \"{student_code}\" 를 그대로 넣으세요."
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
