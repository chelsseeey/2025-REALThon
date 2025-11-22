document.addEventListener("DOMContentLoaded", () => {
  setupDragAndDrop("blank-drop-zone", "blankFile", handleBlankFileSelect);
  setupDragAndDrop(
    "student-drop-zone",
    "studentFiles",
    handleStudentFileSelect
  );

  document
    .getElementById("blankFile")
    .addEventListener("change", (e) => handleBlankFileSelect(e.target.files));
  document
    .getElementById("studentFiles")
    .addEventListener("change", (e) => handleStudentFileSelect(e.target.files));
  document
    .getElementById("analyze-btn")
    .addEventListener("click", startFinalAnalysis);

  // 모달 닫기 버튼 이벤트
  document
    .getElementById("close-modal-btn")
    .addEventListener("click", closeModal);
  // 모달 배경 클릭 시 닫기
  document.getElementById("report-modal").addEventListener("click", (e) => {
    if (e.target.id === "report-modal") closeModal();
  });
});

// 1. 드래그 앤 드롭 (기존 동일)
function setupDragAndDrop(zoneId, inputId, callback) {
  const zone = document.getElementById(zoneId);
  const input = document.getElementById(inputId);
  zone.addEventListener("dragover", (e) => {
    e.preventDefault();
    zone.classList.add("drag-over");
  });
  zone.addEventListener("dragleave", (e) => {
    e.preventDefault();
    zone.classList.remove("drag-over");
  });
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("drag-over");
    if (e.dataTransfer.files.length > 0) {
      input.files = e.dataTransfer.files;
      callback(e.dataTransfer.files);
    }
  });
}

function handleBlankFileSelect(files) {
  if (files.length > 0) {
    document.getElementById(
      "blank-label"
    ).innerHTML = `<span class="text-green-600 font-bold">${files[0].name}</span><br>준비 완료`;
    document.getElementById("blank-check").classList.remove("hidden");
    document.getElementById("blank-drop-zone").style.borderColor = "#22c55e";
    document.getElementById("blank-drop-zone").style.backgroundColor =
      "#f0fdf4";
  }
}

function handleStudentFileSelect(files) {
  if (files.length > 0) {
    document.getElementById("file-count-badge").innerText = files.length;
    document.getElementById("file-count-badge").classList.remove("hidden");
    document.getElementById(
      "student-label"
    ).innerHTML = `<span class="text-indigo-600 font-bold">${files.length}개</span> 파일 선택됨`;
  }
}

// 2. 분석 시작
async function startFinalAnalysis() {
  const blank = document.getElementById("blankFile").files.length;
  const students = document.getElementById("studentFiles").files.length;

  if (blank === 0 || students === 0) {
    alert("파일을 모두 업로드해주세요.");
    return;
  }

  document.getElementById("upload-section").classList.add("hidden");
  document.getElementById("loading-section").classList.remove("hidden");

  setTimeout(() => {
    const mockData = generateMockData();
    renderDashboard(mockData);
  }, 1500);
}

// 3. Mock Data
function generateMockData() {
  const studentCount = 30;
  return {
    totalStudents: studentCount,
    questions: [
      {
        qNum: 1,
        maxScore: 10,
        qText:
          "이차방정식 x² - 5x + 6 = 0 의 두 근을 구하고 과정을 서술하시오.",
        correctRate: 85,
        scoreLabels: ["0점", "1-3점", "4-6점", "7-9점", "10점"],
        scoreData: [2, 1, 3, 4, 20],
        avgScore: 8.5,
        detailAnalysis: {
          mistakes: [
            "인수분해 부호 실수 ((x+2)(x+3)으로 계산)",
            "근의 공식 대입 시 분모 계산 오류",
          ],
          missing: ["최종 답안에 'x=' 표기 누락", "풀이 과정 없이 답만 기재"],
          keywords: ["인수분해", "근의 공식", "판별식"],
        },
      },
      {
        qNum: 2,
        maxScore: 15,
        qText: "행렬 A = [[1, 2], [3, 4]] 의 역행렬을 구하시오.",
        correctRate: 50,
        scoreLabels: ["0점", "1-5점", "6-10점", "11-14점", "15점"],
        scoreData: [5, 8, 4, 3, 10],
        avgScore: 7.2,
        detailAnalysis: {
          mistakes: [
            "ad-bc 행렬식(Determinant) 계산 오류 (4-6 = -2를 2로 계산)",
            "역행렬 공식 부호 위치 혼동",
          ],
          missing: [
            "행렬식이 0이 아님을 확인하는 과정 누락",
            "최종 행렬의 각 원소 약분 미수행",
          ],
          keywords: [
            "Determinant(행렬식)",
            "Adjugate Matrix(수반행렬)",
            "역행렬 존재 조건",
          ],
        },
      },
      {
        qNum: 3,
        maxScore: 20,
        qText: "함수 f(x) = sin(x)cos(x) 를 0에서 π까지 적분하시오.",
        correctRate: 30,
        scoreLabels: ["0점", "1-7점", "8-14점", "15-19점", "20점"],
        scoreData: [10, 8, 5, 4, 3],
        avgScore: 5.5,
        detailAnalysis: {
          mistakes: [
            "치환적분 범위 재설정 누락 (0~π를 그대로 사용)",
            "배각 공식 sin(2x) 변환 실수",
          ],
          missing: [
            "적분상수 C 표기 (부정적분 혼동)",
            "치환 변수 t에 대한 정의",
          ],
          keywords: ["치환적분법", "부분적분법", "삼각함수 항등식"],
        },
      },
    ],
  };
}

// 4. 메인 대시보드 렌더링
function renderDashboard(data) {
  document.getElementById("loading-section").classList.add("hidden");
  document.getElementById("result-section").classList.remove("hidden");
  document.getElementById(
    "total-student-count"
  ).innerText = `${data.totalStudents}명`;

  const grid = document.getElementById("questions-grid");
  grid.innerHTML = "";

  data.questions.forEach((q) => {
    const card = document.createElement("div");
    card.className = "question-card group";
    card.onclick = () => openModal(q); // 클릭 시 모달 오픈

    card.innerHTML = `
        <div class="flex justify-between items-start mb-4">
            <span class="bg-indigo-100 text-indigo-700 font-bold px-2 py-1 rounded text-sm">Q${q.qNum}</span>
            <span class="text-slate-400 text-sm font-medium"></span>
        </div>
        <p class="text-slate-800 font-bold text-lg mb-2 line-clamp-3 break-keep">
            ${q.qText}
        </p>
    `;
    grid.appendChild(card);
  });
}

// 5. 모달 상세 보고서 로직
let detailChartInstance = null;

function openModal(qData) {
  const modal = document.getElementById("report-modal");

  document.getElementById("modal-q-num").innerText = `Q${qData.qNum}`;
  document.getElementById(
    "modal-title"
  ).innerText = `문항 ${qData.qNum} 상세 분석`;
  document.getElementById("modal-q-text").innerText = qData.qText;

  document.getElementById(
    "modal-avg-score"
  ).innerText = `평균: ${qData.avgScore}점`;
  document.getElementById(
    "modal-max-score"
  ).innerText = `배점: ${qData.maxScore}점`;

  const fillList = (id, items) => {
    const list = document.getElementById(id);
    list.innerHTML = "";
    items.forEach((item) => {
      const li = document.createElement(
        id === "analysis-keywords" ? "span" : "li"
      );
      if (id === "analysis-keywords") {
        li.className =
          "bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-xs font-bold border border-blue-100";
      }
      li.innerText = item;
      list.appendChild(li);
    });
  };

  fillList("analysis-mistakes", qData.detailAnalysis.mistakes);
  fillList("analysis-missing", qData.detailAnalysis.missing);
  fillList("analysis-keywords", qData.detailAnalysis.keywords);

  const ctx = document.getElementById("detail-chart").getContext("2d");
  if (detailChartInstance) detailChartInstance.destroy();

  detailChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: qData.scoreLabels,
      datasets: [
        {
          label: "학생 수",
          data: qData.scoreData,
          backgroundColor: "#6366f1",
          borderRadius: 4,
          barPercentage: 0.6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => `점수 구간: ${items[0].label}`,
            label: (item) =>
              `${item.raw}명 (${Math.round((item.raw / 30) * 100)}%)`,
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { display: true, drawBorder: false },
          ticks: { stepSize: 1 },
        },
        x: {
          grid: { display: false },
        },
      },
    },
  });

  modal.classList.remove("hidden");
  setTimeout(() => modal.classList.add("open"), 10);
  document.body.style.overflow = "hidden";
}

function closeModal() {
  const modal = document.getElementById("report-modal");
  modal.classList.remove("open");
  setTimeout(() => {
    modal.classList.add("hidden");
    document.body.style.overflow = "auto";
  }, 300);
}

// 6. 과목 변경 기능 (추가됨)
function changeSubject(subjectName) {
  const currentSubjectSpan = document.getElementById("current-subject");
  currentSubjectSpan.innerText = subjectName;

  const checkIcons = document.querySelectorAll(".check-icon");
  checkIcons.forEach((icon) => {
    if (icon.dataset.subject === subjectName) {
      icon.classList.remove("opacity-0");
      icon.classList.add("opacity-100");
    } else {
      icon.classList.remove("opacity-100");
      icon.classList.add("opacity-0");
    }
  });
}
