import os
import base64
import json
import glob
from pathlib import Path
from openai import OpenAI

# 실제 사용할 때는 환경변수로 관리하는 걸 추천
client = OpenAI(api_key="")

def encode_image(image_path: str) -> str:
    """이미지를 base64 data URL 형태로 인코딩"""
    import mimetypes
    mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"

def parse_sheet(image_path: str, output_json_path: str | None = None) -> dict:
    image_data_url = encode_image(image_path)

    prompt = """
이미지에는 한 학생의 답안이 있으며,
상단에 "학번 : XXXX" 형식의 텍스트와
그 아래에 '문항'과 '점수' 헤더를 가진 표가 있습니다.

당신의 임무는 이미지에서 학번과 각 문항의 점수를 읽어,
아래 예시와 같은 형식의 JSON 한 개만 출력하는 것입니다.

예시:
{
  "student_id": "2271022",
  "scores": {
    "1": 15,
    "2": 15,
    "3": 15,
    "4": 20
  }
}

규칙:
- 최종 출력은 반드시 위 예시와 동일한 구조의 JSON 객체 하나여야 합니다.
- student_id:
  - "학번" 또는 "학 번"이라는 단어 뒤에 나오는 숫자 전체를 문자열로 넣으세요.
  - 숫자 사이에 공백이나 하이픈이 있어도 모두 붙인 하나의 문자열로 만드세요.
- scores:
  - 표에서 '문항' 열에 있는 값을 key 로 사용합니다.
    - 문항 번호는 그대로 문자열로 넣으세요. (예: 1 → "1")
  - 같은 행의 '점수' 열 값을 value 로 사용합니다.
    - 점수는 정수형 숫자로 넣으세요. (예: "15" → 15)
  - 문항 번호가 숫자가 아니거나, 점수가 인식되지 않은 행은 무시하세요.
  - 표에 존재하는 모든 문항을 누락 없이 포함하세요.
- 표에 다른 열이 더 있더라도, '문항'과 '점수' 두 열만 사용하세요.
- JSON 이외의 설명, 주석, 불필요한 텍스트는 절대 출력하지 마세요.
"""



    response = client.chat.completions.create(
        model="gpt-4o-mini",  # 또는 gpt-4o / gpt-4.1 등 비전 지원 모델
        response_format={"type": "json_object"},  # JSON 모드
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_url},
                    },
                ],
            }
        ],
        max_tokens=300,
    )

    # 모델이 반환한 JSON 문자열 파싱
    content = response.choices[0].message.content
    result = json.loads(content)

    # 결과를 파일로 저장
    if output_json_path is not None:
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    return result


if __name__ == "__main__":
    # 점수 폴더의 모든 png 파일을 찾기
    score_folder = "점수"
    image_files = sorted(glob.glob(os.path.join(score_folder, "*.png")))
    
    if not image_files:
        print(f"'{score_folder}' 폴더에 PNG 파일이 없습니다.")
        exit(1)
    
    print(f"{len(image_files)}개의 이미지 파일을 찾았습니다.")
    
    all_results = []
    
    for idx, image_path in enumerate(image_files, 1):
        filename = Path(image_path).name
        print(f"\n[{idx}/{len(image_files)}] 처리 중: {filename}")
        
        try:
            result = parse_sheet(image_path, output_json_path=None)
            all_results.append(result)
            print(f" 완료: 학번 {result.get('student_id', 'N/A')}")
        except Exception as e:
            print(f" 오류: {e}")
            # 에러가 나도 계속 진행
            all_results.append({
                "error": str(e)
            })
    
    # 하나의 JSON 파일로 저장
    output_path = "점수.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*50}")
    print(f"모든 결과를 '{output_path}' 파일에 저장했습니다.")
    print(f"총 {len(all_results)}개의 시험지 처리 완료")
    print(f"{'='*50}")
