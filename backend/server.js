const express = require("express");
const multer = require("multer");
const cors = require("cors");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

const app = express();
const port = 3000;

app.use(cors());

// JSON 및 URL 인코딩 파싱 미들웨어 추가
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// dashboard 폴더 경로 확인 (여러 위치 시도)
const dashboardPaths = [
  path.join(__dirname, "../dashboard"),
  path.join(__dirname, "../../hackathon/dashboard"),
  path.join(__dirname, "../../2025-REALThon-parsing/dashboard"),
];

let dashboardPath = null;
for (const dp of dashboardPaths) {
  if (fs.existsSync(dp)) {
    dashboardPath = dp;
    break;
  }
}

if (dashboardPath) {
  app.use(express.static(dashboardPath));
  // 루트 경로 접속 시 dashboard.html 제공
  app.get("/", (req, res) => {
    res.sendFile(path.join(dashboardPath, "dashboard.html"));
  });
} else {
  // dashboard 폴더가 없으면 기본 메시지 제공
  app.get("/", (req, res) => {
    res.send(`
      <html>
        <head><title>REALThon API Server</title></head>
        <body>
          <h1>REALThon API Server</h1>
          <p>서버가 정상적으로 실행 중입니다.</p>
          <p>API 엔드포인트:</p>
          <ul>
            <li>POST /question-papers/upload - 문제지/점수표 업로드</li>
            <li>POST /answer-sheets/upload - 답안지 업로드 및 분석</li>
          </ul>
        </body>
      </html>
    `);
  });
}

// 업로드 폴더 생성
const uploadDir = path.join(__dirname, "uploads");
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir);
}

const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, uploadDir);
  },
  filename: function (req, file, cb) {
    const uniqueSuffix = Date.now() + "-" + Math.round(Math.random() * 1e9);
    const ext = path.extname(file.originalname);
    cb(null, file.fieldname + "-" + uniqueSuffix + ext);
  },
});

const upload = multer({ storage: storage });

// 임시 파일 경로 저장소 및 업로드 상태
let tempFilePaths = {
  blankPath: null,
  rubricPath: null,
  scorePaths: [],
};

// 업로드 단계 상태
let uploadStatus = {
  step1_blank: false,      // 1단계: 문제지 업로드 완료
  step2_rubric: false,     // 2단계: 채점 기준표 업로드 완료
  step3_scores: false,     // 3단계: 점수표 업로드 완료
  step4_answers: false,    // 4단계: 답안지 업로드 완료
};

// ==========================================
// 1단계: 문제지 업로드
// ==========================================
const blankUpload = upload.single("file");

app.post("/question-papers/upload/blank", blankUpload, (req, res) => {
  console.log("📥 [1단계] 문제지 업로드 수신");

  try {
    if (!req.file) {
      return res.status(400).json({ error: "문제지 파일이 필요합니다." });
    }

    tempFilePaths.blankPath = req.file.path;
    uploadStatus.step1_blank = true;

    res.status(200).json({ 
      message: "문제지 업로드 완료",
      step: 1,
      nextStep: "채점 기준표를 업로드하세요."
    });
  } catch (e) {
    console.error("Step 1 Error:", e);
    res.status(500).json({ error: "파일 업로드 실패", details: e.message });
  }
});

// ==========================================
// 2단계: 채점 기준표 업로드
// ==========================================
const rubricUpload = upload.single("rubric");

app.post("/question-papers/upload/rubric", rubricUpload, (req, res) => {
  console.log("📥 [2단계] 채점 기준표 업로드 수신");

  try {
    if (!uploadStatus.step1_blank) {
      return res.status(400).json({ 
        error: "먼저 문제지를 업로드하세요.",
        requiredStep: 1
      });
    }

    if (!req.file) {
      return res.status(400).json({ error: "채점 기준표 파일이 필요합니다." });
    }

    tempFilePaths.rubricPath = req.file.path;
    uploadStatus.step2_rubric = true;

    res.status(200).json({ 
      message: "채점 기준표 업로드 완료",
      step: 2,
      nextStep: "점수표를 업로드하세요."
    });
  } catch (e) {
    console.error("Step 2 Error:", e);
    res.status(500).json({ error: "파일 업로드 실패", details: e.message });
  }
});

// ==========================================
// 3단계: 점수표 업로드
// ==========================================
const scoreUpload = upload.array("scoreFiles", 50);

app.post("/question-papers/upload/scores", scoreUpload, (req, res) => {
  console.log("📥 [3단계] 점수표 업로드 수신");

  try {
    if (!uploadStatus.step1_blank || !uploadStatus.step2_rubric) {
      return res.status(400).json({ 
        error: "먼저 문제지와 채점 기준표를 업로드하세요.",
        requiredSteps: [1, 2]
      });
    }

    if (!req.files || req.files.length === 0) {
      return res.status(400).json({ error: "점수표 파일이 필요합니다." });
    }

    tempFilePaths.scorePaths = req.files.map((f) => f.path);
    uploadStatus.step3_scores = true;

    res.status(200).json({ 
      message: "점수표 업로드 완료",
      step: 3,
      fileCount: req.files.length,
      nextStep: "답안지를 업로드하세요."
    });
  } catch (e) {
    console.error("Step 3 Error:", e);
    res.status(500).json({ error: "파일 업로드 실패", details: e.message });
  }
});

// ==========================================
// 업로드 상태 확인 API
// ==========================================
app.get("/upload/status", (req, res) => {
  res.json({
    steps: {
      step1_blank: uploadStatus.step1_blank,
      step2_rubric: uploadStatus.step2_rubric,
      step3_scores: uploadStatus.step3_scores,
      step4_answers: uploadStatus.step4_answers,
    },
    nextStep: !uploadStatus.step1_blank ? 1 :
              !uploadStatus.step2_rubric ? 2 :
              !uploadStatus.step3_scores ? 3 : 4
  });
});

// ==========================================
// 4단계: 답안지 업로드 및 분석 실행
// ==========================================
const answerUpload = upload.array("files", 50);

app.post("/answer-sheets/upload", answerUpload, (req, res) => {
  console.log("📥 [4단계] 답안지 수신 및 분석 시작...");

  // 이전 단계 확인 (1-3단계 모두 완료되어야 함)
  if (!uploadStatus.step1_blank || !uploadStatus.step2_rubric || !uploadStatus.step3_scores) {
    const missingSteps = [];
    if (!uploadStatus.step1_blank) missingSteps.push(1);
    if (!uploadStatus.step2_rubric) missingSteps.push(2);
    if (!uploadStatus.step3_scores) missingSteps.push(3);
    
    return res.status(400).json({
      error: `먼저 다음 단계를 완료하세요: ${missingSteps.join(", ")}단계`,
      requiredSteps: missingSteps,
      currentStatus: {
        step1_blank: uploadStatus.step1_blank,
        step2_rubric: uploadStatus.step2_rubric,
        step3_scores: uploadStatus.step3_scores
      }
    });
  }

  // 파일 확인
  if (!req.files || req.files.length === 0) {
    return res.status(400).json({
      error: "답안지 파일이 필요합니다.",
    });
  }

  try {
    const studentPaths = req.files.map((f) => f.path);
    
    // 모든 점수표 경로 전달 (여러 학생 인식을 위해)
    const scorePaths = tempFilePaths.scorePaths;
    
    if (scorePaths.length === 0) {
      return res.status(400).json({
        error: "점수표가 없습니다. 3단계에서 점수표를 업로드하세요.",
      });
    }
    
    uploadStatus.step4_answers = true;

    // analysis_wrapper.py의 절대 경로
    const wrapperPath = path.join(__dirname, "analysis_wrapper.py");
    
    // 가상환경 Python 경로 하드코딩 (venv\Scripts\python.exe 형식)
    const pythonCmd = path.join(__dirname, "venv", "Scripts", "python.exe");
    console.log("✅ 가상환경 Python 사용:", pythonCmd);
    console.log(`📊 점수표 ${scorePaths.length}개, 답안지 ${studentPaths.length}개 처리 예정`);
    
    // 여러 점수표를 한 번에 전달 (nargs='+' 형식)
    const args = [
      wrapperPath,
      "--blank",
      tempFilePaths.blankPath,
      "--rubric",
      tempFilePaths.rubricPath,
      "--score",
      ...scorePaths,  // 모든 점수표 경로를 한 번에 전달
      "--students",
      ...studentPaths,
    ];

    console.log("🐍 Python 스크립트 실행 중...");
    console.log(`명령어 형식: venv\\Scripts\\python.exe analysis_wrapper.py --blank ... --score ... --students ...`);
    console.log(`점수표: ${scorePaths.length}개, 답안지: ${studentPaths.length}개`);
    
    const pythonProcess = spawn(pythonCmd, args, {
      cwd: __dirname, // 작업 디렉토리를 현재 디렉토리로 설정
      shell: process.platform === "win32", // Windows에서는 shell 옵션 사용
    });

    let dataString = "";
    let errorString = "";

    pythonProcess.stdout.on("data", (data) => {
      dataString += data.toString();
    });

    pythonProcess.stderr.on("data", (data) => {
      errorString += data.toString();
      console.log("PyLog:", data.toString());
    });

    pythonProcess.on("close", (code) => {
      if (code !== 0) {
        console.error("Python 프로세스 종료 코드:", code);
        console.error("에러 출력:", errorString);
        console.error("표준 출력:", dataString);
        return res
          .status(500)
          .json({ 
            error: "분석 실패", 
            details: errorString || "알 수 없는 오류",
            exitCode: code,
            stdout: dataString.substring(0, 500) // 처음 500자만 전송
          });
      }
      
      // stdout에서 JSON 추출 (stderr 메시지 제거)
      const jsonMatch = dataString.match(/\{[\s\S]*\}/);
      const jsonString = jsonMatch ? jsonMatch[0] : dataString.trim();
      
      try {
        const resultJson = JSON.parse(jsonString);
        console.log("✅ 분석 완료:", Object.keys(resultJson));
        res.json(resultJson);
      } catch (e) {
        console.error("JSON Parse Error:", e);
        console.error("원본 데이터:", dataString.substring(0, 1000));
        res
          .status(500)
          .json({ 
            error: "결과 데이터 파싱 오류", 
            details: e.message,
            raw: dataString.substring(0, 1000) // 처음 1000자만 전송
          });
      }
    });
    
    pythonProcess.on("error", (err) => {
      console.error("Python 프로세스 실행 오류:", err);
      res.status(500).json({ 
        error: "Python 스크립트 실행 실패", 
        details: err.message 
      });
    });
  } catch (e) {
    console.error("Server Error:", e);
    res.status(500).json({ error: "서버 내부 오류" });
  }
});

app.listen(port, () => {
  console.log(`=============================================`);
  console.log(`🚀 서버 실행 중! 아래 주소로 접속하세요:`);
  console.log(`👉 http://localhost:${port}`);
  if (dashboardPath) {
    console.log(`📁 Dashboard: ${dashboardPath}`);
  } else {
    console.log(`⚠️  Dashboard 폴더를 찾을 수 없습니다.`);
  }
  console.log(`=============================================`);
}).on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`❌ 포트 ${port}가 이미 사용 중입니다.`);
    console.error(`다른 포트를 사용하거나 기존 프로세스를 종료하세요.`);
  } else {
    console.error(`❌ 서버 시작 실패:`, err);
  }
  process.exit(1);
});
