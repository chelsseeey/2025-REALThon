// 전역 상태 관리
let questionList = [];
let nextQuestionId = 1;

document.addEventListener("DOMContentLoaded", () => {
  // 초기 문항 5개 세팅
  initializeQuestions(5);

  // [추가됨] 드래그 앤 드롭 설정
  setupDragAndDrop();

  // 기존 파일 선택 이벤트
  const fileInput = document.getElementById("studentFiles");
  fileInput.addEventListener("change", (e) =>
    updateFileCountUI(e.target.files.length)
  );

  document
    .getElementById("go-setup-btn")
    .addEventListener("click", showSetupSection);
});

// ==========================================
// 1. 드래그 앤 드롭 기능 구현
// ==========================================
function setupDragAndDrop() {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("studentFiles");

  // 1) 드래그 진입
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault(); // 필수: 브라우저가 파일 여는 것 방지
    e.stopPropagation();
    dropZone.classList.add("drag-over");
  });

  // 2) 드래그 나감
  dropZone.addEventListener("dragleave", (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove("drag-over");
  });

  // 3) 드롭
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove("drag-over");

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      // input 태그에 파일 할당 (중요)
      fileInput.files = files;
      // UI 업데이트 트리거
      updateFileCountUI(files.length);
    }
  });
}

// 파일 개수 UI 업데이트 헬퍼 함수
function updateFileCountUI(count) {
  if (count > 0) {
    const badge = document.getElementById("file-count-badge");
    const label = document.getElementById("student-label");
    badge.innerText = count;
    badge.classList.remove("hidden");
    label.innerHTML = `<span class="text-indigo-600 font-bold">${count}개</span>의 파일이 선택되었습니다.`;
  }
}

// ==========================================
// 2. 문항 관리 로직 (기존과 동일)
// ==========================================
function initializeQuestions(count) {
  questionList = [];
  nextQuestionId = 1;
  const container = document.getElementById("questions-container");
  container.innerHTML = "";
  for (let i = 0; i < count; i++) {
    addQuestion(false);
  }
  updateTotalCount();
}

function addQuestion(shouldScroll = true) {
  const qId = nextQuestionId++;
  const qNum = questionList.length + 1;
  questionList.push({ id: qId, score: 10 });

  const container = document.getElementById("questions-container");
  const row = document.createElement("div");
  row.className = "question-row fade-in";
  row.id = `q-row-${qId}`;
  row.innerHTML = `
        <div class="flex items-center gap-3">
            <span class="bg-indigo-100 text-indigo-700 text-sm font-bold px-3 py-1 rounded-full q-label">Q${qNum}</span>
            <span class="text-slate-600 font-medium text-sm">문항</span>
        </div>
        <div class="flex items-center gap-4">
            <div class="flex items-center gap-2">
                <span class="text-xs text-slate-400">만점</span>
                <input type="number" value="10" min="1" class="score-input" onchange="updateScore(${qId}, this.value)">
                <span class="text-sm text-slate-600">점</span>
            </div>
            <button onclick="removeQuestion(${qId})" class="btn-remove" title="문항 삭제">
                <i class="fas fa-minus"></i>
            </button>
        </div>
    `;
  container.appendChild(row);
  updateTotalCount();
  refreshLabels();
  if (shouldScroll) row.scrollIntoView({ behavior: "smooth", block: "center" });
}

function removeQuestion(id) {
  if (questionList.length <= 1) {
    alert("최소 1개의 문항은 있어야 합니다.");
    return;
  }
  questionList = questionList.filter((q) => q.id !== id);
  const row = document.getElementById(`q-row-${id}`);
  if (row) row.remove();
  updateTotalCount();
  refreshLabels();
}

function updateScore(id, value) {
  const question = questionList.find((q) => q.id === id);
  if (question) question.score = parseInt(value) || 0;
}

function refreshLabels() {
  const rows = document.querySelectorAll(".question-row");
  rows.forEach((row, index) => {
    const label = row.querySelector(".q-label");
    label.innerText = `Q${index + 1}`;
  });
}

function updateTotalCount() {
  document.getElementById("total-q-count").innerText = questionList.length;
}

// ==========================================
// 3. 페이지 전환 및 분석 로직
// ==========================================

function showSetupSection() {
  const files = document.getElementById("studentFiles").files;
  if (files.length === 0) {
    alert("먼저 학생 답안지를 업로드해주세요.");
    return;
  }
  document.getElementById("upload-section").classList.add("hidden");
  document.getElementById("setup-section").classList.remove("hidden");
}

function startFinalAnalysis() {
  document.getElementById("setup-section").classList.add("hidden");
  document.getElementById("loading-section").classList.remove("hidden");

  // [시뮬레이션]
  setTimeout(() => {
    const mockData = generateMockDataBasedOnConfig(questionList);
    renderDashboard(mockData);
  }, 2000);
}

function generateMockDataBasedOnConfig(config) {
  const studentCount = 30;
  let totalMaxScore = 0;
  let totalEarnedScore = 0;

  const questionsData = config.map((q, index) => {
    totalMaxScore += q.score;
    const correctRate = Math.floor(Math.random() * 50) + 40;
    const avgEarned = (q.score * correctRate) / 100;
    totalEarnedScore += avgEarned;

    return {
      qNum: index + 1,
      maxScore: q.score,
      correctRate: correctRate,
      errorDistribution: {
        "단순 계산 실수": Math.floor(Math.random() * 20) + 5,
        "풀이 과정 누락": Math.floor(Math.random() * 20) + 5,
        "개념 이해 부족": Math.floor(Math.random() * 20) + 5,
        기타: Math.floor(Math.random() * 5) + 1,
      },
    };
  });

  const hardest = questionsData.reduce((prev, curr) =>
    prev.correctRate < curr.correctRate ? prev : curr
  );

  return {
    summary: {
      totalStudents: studentCount,
      avgScore: Math.round((totalEarnedScore / totalMaxScore) * 100),
      hardestQuestion: `Q${hardest.qNum}`,
    },
    questions: questionsData,
  };
}

function renderDashboard(data) {
  document.getElementById("loading-section").classList.add("hidden");
  document.getElementById("result-section").classList.remove("hidden");

  document.getElementById(
    "res-total-students"
  ).innerText = `${data.summary.totalStudents}명`;
  document.getElementById(
    "res-avg-score"
  ).innerText = `${data.summary.avgScore}점`;
  document.getElementById("res-hardest-q").innerText =
    data.summary.hardestQuestion;

  const container = document.getElementById("charts-grid");
  container.innerHTML = "";

  data.questions.forEach((q, index) => {
    const card = document.createElement("div");
    card.className = "chart-card";
    card.innerHTML = `
            <div class="flex justify-between items-start mb-4">
                <div>
                    <span class="bg-indigo-100 text-indigo-700 text-xs font-bold px-2 py-1 rounded">Q${
                      q.qNum
                    }</span>
                    <span class="text-xs text-slate-400 ml-1">(${
                      q.maxScore
                    }점)</span>
                    <h4 class="font-bold text-slate-800 mt-1">문항 ${
                      q.qNum
                    } 분석</h4>
                </div>
                <div class="text-right">
                    <span class="text-xs text-slate-400 block">정답률</span>
                    <span class="text-lg font-bold ${getScoreColor(
                      q.correctRate
                    )}">${q.correctRate}%</span>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="chart-${index}"></canvas>
            </div>
            <div class="mt-4 pt-3 border-t border-slate-100 text-center">
                <p class="text-xs text-slate-500">
                    가장 많은 오답 원인: <span class="font-bold text-slate-700">${getTopReason(
                      q.errorDistribution
                    )}</span>
                </p>
            </div>
        `;
    container.appendChild(card);
    drawPieChart(`chart-${index}`, q.errorDistribution);
  });
}

function drawPieChart(canvasId, distribution) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: Object.keys(distribution),
      datasets: [
        {
          data: Object.values(distribution),
          backgroundColor: [
            "#36a2eb",
            "#ff6384",
            "#ffce56",
            "#4bc0c0",
            "#9966ff",
          ],
          borderWidth: 0,
          hoverOffset: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "right",
          labels: { boxWidth: 10, font: { size: 10 } },
        },
        title: { display: false },
      },
      layout: { padding: 0 },
    },
  });
}

function getScoreColor(score) {
  if (score >= 80) return "text-green-600";
  if (score >= 50) return "text-yellow-600";
  return "text-red-600";
}

function getTopReason(dist) {
  return Object.keys(dist).reduce((a, b) => (dist[a] > dist[b] ? a : b));
}
