const API_BASE = "";

let currentStream = null;
let isVerifying = false;

// DOM Elements
const video = document.getElementById("webcam");
const canvas = document.getElementById("snapshot-canvas");
const cameraSelect = document.getElementById("camera-select");
const employeeInput = document.getElementById("employee-id");
const btnVerify = document.getElementById("btn-verify");
const btnForgot = document.getElementById("btn-forgot");

const resultBox = document.getElementById("result-box");
const resultIcon = document.getElementById("result-icon");
const resultStatus = document.getElementById("result-status");
const resultMsg = document.getElementById("result-msg");

const personDetails = document.getElementById("person-details");
const detName = document.getElementById("det-name");
const detId = document.getElementById("det-id");
const detDept = document.getElementById("det-dept");

const faceBar = document.getElementById("face-bar");
const faceScore = document.getElementById("face-score");
const bodyBar = document.getElementById("body-bar");
const bodyScore = document.getElementById("body-score");

const tailgateBanner = document.getElementById("tailgate-banner");
const tailgateMsg = document.getElementById("tailgate-msg");
const clockEl = document.getElementById("clock");
const apiStatusEl = document.getElementById("api-status");

// 1. Clock
setInterval(() => {
  const now = new Date();
  clockEl.textContent = now.toTimeString().split(" ")[0];
}, 1000);

// 2. Health Check
async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (res.ok) {
      const data = await res.json();
      apiStatusEl.textContent = `Online (${data.database.mode})`;
      apiStatusEl.style.color = "#10b981";
    } else {
      throw new Error();
    }
  } catch {
    apiStatusEl.textContent = "Offline / Reconnecting";
    apiStatusEl.style.color = "#ef4444";
  }
}
setInterval(checkHealth, 5000);
checkHealth();

// 3. Webcam Initialization
async function initWebcam(deviceId = null) {
  if (currentStream) {
    currentStream.getTracks().forEach(t => t.stop());
  }

  const constraints = {
    video: deviceId ? { deviceId: { exact: deviceId } } : { facingMode: "user" },
    audio: false
  };

  try {
    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    currentStream = stream;
    video.srcObject = stream;
    await populateCameraList();
  } catch (err) {
    console.error("Camera access error:", err);
    resultMsg.textContent = "Please allow webcam access in your browser to verify.";
  }
}

async function populateCameraList() {
  if (!navigator.mediaDevices?.enumerateDevices) return;
  const devices = await navigator.mediaDevices.enumerateDevices();
  const videoDevices = devices.filter(d => d.kind === "videoinput");

  cameraSelect.innerHTML = "";
  videoDevices.forEach((dev, index) => {
    const opt = document.createElement("option");
    opt.value = dev.deviceId;
    opt.textContent = dev.label || `Camera ${index + 1}`;
    cameraSelect.appendChild(opt);
  });
}

cameraSelect.addEventListener("change", (e) => {
  initWebcam(e.target.value);
});

// 4. Capture Frame as Base64
function captureFrameBase64() {
  if (!video.videoWidth || !video.videoHeight) return null;
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  
  // Note: Unmirror frame for backend CV models
  ctx.save();
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  ctx.restore();

  return canvas.toDataURL("image/jpeg", 0.85);
}

// 5. Access Verification
async function verifyAccess(employeeId = null) {
  if (isVerifying) return;
  isVerifying = true;

  const empId = employeeId !== null ? employeeId : employeeInput.value.trim();
  const frameBase64 = captureFrameBase64();

  // Reset visuals
  setLoadingState("Verifying Identity...");

  try {
    const payload = {
      employee_id: empId || null,
      camera_id: "CAM-01",
      frame_base64: frameBase64
    };

    const res = await fetch(`${API_BASE}/api/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    handleVerificationResponse(data);
  } catch (err) {
    console.error("Verification error:", err);
    showDecisionResult("DENIED", "Network error: Unable to contact verification server", 0, 0);
  } finally {
    isVerifying = false;
  }
}

function verifyWithoutCard() {
  employeeInput.value = "";
  verifyAccess("");
}

// 6. Handle Verification Response
function handleVerificationResponse(data) {
  const decision = data.decision || "DENIED";
  const message = data.message || "";
  const faceConf = Math.round((data.face_confidence || 0) * 100);
  const bodyConf = Math.round((data.body_confidence || 0) * 100);

  // Check Tailgating
  if (data.tailgate_detected) {
    tailgateBanner.classList.remove("hidden");
    tailgateMsg.textContent = message;
  } else {
    tailgateBanner.classList.add("hidden");
  }

  // Populate person details
  if (data.employee_id) {
    personDetails.classList.remove("hidden");
    detName.textContent = data.employee_name || "Employee";
    detId.textContent = data.employee_id;
    detDept.textContent = data.department || "General";
  } else {
    personDetails.classList.add("hidden");
  }

  showDecisionResult(decision, message, faceConf, bodyConf);

  // Auto-reset back to scanning state after 4 seconds
  setTimeout(() => {
    resetToDefaultState();
  }, 4000);
}

function setLoadingState(msg) {
  resultBox.className = "decision-display default";
  resultStatus.textContent = "VERIFYING BIOMETRICS...";
  resultMsg.textContent = msg;
}

function showDecisionResult(decision, message, faceConf, bodyConf) {
  resultBox.className = `decision-display ${decision.toLowerCase()}`;
  
  if (decision === "GRANTED") {
    resultStatus.textContent = "ACCESS GRANTED [VERIFIED]";
  } else if (decision === "WARNING") {
    resultStatus.textContent = "ACCESS WARNING [DEVIATION]";
  } else {
    resultStatus.textContent = "ACCESS DENIED [FAILED]";
  }

  resultMsg.textContent = message;

  // Meters
  faceBar.style.width = `${faceConf}%`;
  faceScore.textContent = `${faceConf}%`;
  bodyBar.style.width = `${bodyConf}%`;
  bodyScore.textContent = `${bodyConf}%`;
}

function resetToDefaultState() {
  resultBox.className = "decision-display default";
  resultStatus.textContent = "AWAITING CREDENTIAL";
  resultMsg.textContent = "Ready for badge swipe or biometric detection.";
  personDetails.classList.add("hidden");
  tailgateBanner.classList.add("hidden");
  faceBar.style.width = "0%";
  faceScore.textContent = "--%";
  bodyBar.style.width = "0%";
  bodyScore.textContent = "--%";
  employeeInput.value = "";
  employeeInput.focus();
}

// Initial Run
window.addEventListener("DOMContentLoaded", () => {
  initWebcam();
  employeeInput.focus();
});
