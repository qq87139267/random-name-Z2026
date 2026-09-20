<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>“ 💪 →下一位～～就係你～～～👉↗”</title>
<style>
/* ========== 全局 ========== */
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  background: #1a1a2e;
  color: white;
  font-family: "Microsoft YaHei", sans-serif;
  height: 100vh;
  overflow: hidden;
  user-select: none;
  transition: opacity 0.8s;
}

body.dim { opacity: 0.3; }

/* ========== 顶部班级 ========== */
.header {
  text-align: center;
  padding: 20px 0 10px;
  font-size: 42px;
  font-weight: bold;
  color: #00d4ff;
  letter-spacing: 4px;
}

/* ========== 名字区域 ========== */
.center {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 60vh;
}

.name {
  font-family:
    "Xingkai SC", "STXingkai", "Xingkai TC",
    "KaiTi", "KaiTi_GB2312", "FZXingKai-Medium",
    "LiSu", "Microsoft YaHei", serif;
  font-size: 140px;
  font-weight: bold;
  cursor: pointer;
  padding: 20px 40px;
  border-radius: 20px;
  transition: transform 0.08s;
  text-align: center;

  /* 默认金色 */
  background: linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FF8C00 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  filter:
    drop-shadow(0 2px 0 #B8860B)
    drop-shadow(0 4px 0 #8B6508)
    drop-shadow(0 6px 8px rgba(0,0,0,0.6));
}

.name:active { transform: scale(0.97); }

/* ========== 底部信息 ========== */
.footer {
  position: absolute;
  bottom: 30px;
  width: 100%;
  text-align: center;
  font-size: 26px;
  color: #ccc;
}

/* ========== 按钮栏 ========== */
.buttons {
  position: absolute;
  bottom: 80px;
  width: 100%;
  text-align: center;
}

.buttons button {
  font-size: 22px;
  padding: 12px 30px;
  margin: 0 10px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  color: white;
}

.btn-start { background: #2196f3; }
.btn-reset { background: #ff9800; }
.btn-switch { background: #4caf50; }
</style>
</head>

<body>
<div class="header" id="classLabel">426班</div>

<div class="center">
  <div class="name" id="nameLabel">点击开始</div>
</div>

<div class="buttons">
  <button class="btn-start" onclick="toggleRoll()">开始 / 停止</button>
  <button class="btn-reset" onclick="resetClass()">重置</button>
  <button class="btn-switch" onclick="switchClass()">换班（Esc）</button>
</div>

<div class="footer" id="remainLabel">剩余 0/0</div>

<script>
/* ========== 名单配置（直接改这里） ========== */
const CLASSES = {
  "426班": [
    "蔡家乐","吴莹莹","廖梓良","张三","李四","王五"
  ],
  "428班": [
    "赵六","孙七","周八","吴九","郑十"
  ]
};

/* ========== 状态 ========== */
let classKeys = Object.keys(CLASSES);
let currentIdx = 0;
let currentClass = classKeys[currentIdx];
let originalNames = [...CLASSES[currentClass]];
let remainingNames = [...originalNames];

let isRolling = false;
let timer = null;
let startTime = 0;
let idleTimer = null;
let idleSeconds = 0;
const IDLE_LIMIT = 20;

/* ========== DOM ========== */
const nameLabel = document.getElementById("nameLabel");
const classLabel = document.getElementById("classLabel");
const remainLabel = document.getElementById("remainLabel");

/* ========== 万花筒色 ========== */
const COLORS = [
  "#ff4081","#ffeb3b","#00e5ff","#76ff03",
  "#e040fb","#ff6e40","#18ffff","#ffff00",
  "#f50057","#00ffa0","#651fff","#ffd740"
];

/* ========== 初始化 ========== */
updateDisplay();
resetIdle();
document.addEventListener("mousemove", resetIdle);
document.addEventListener("keydown", resetIdle);
document.addEventListener("click", resetIdle);

/* ========== 核心函数 ========== */
function updateDisplay() {
  classLabel.textContent = currentClass;
  remainLabel.textContent = `剩余 ${remainingNames.length}/${originalNames.length}`;
  if (!isRolling && nameLabel.dataset.picked !== "1") {
    nameLabel.textContent = "点击开始";
    resetGoldStyle();
  }
}

function resetGoldStyle() {
  nameLabel.style.background = "linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FF8C00 100%)";
  nameLabel.style.webkitBackgroundClip = "text";
  nameLabel.style.webkitTextFillColor = "transparent";
  nameLabel.style.filter = `
    drop-shadow(0 2px 0 #B8860B)
    drop-shadow(0 4px 0 #8B6508)
    drop-shadow(0 6px 8px rgba(0,0,0,0.6))
  `;
}

function setKaleidoscopeColor() {
  const c = COLORS[Math.floor(Math.random() * COLORS.length)];
  nameLabel.style.background = "none";
  nameLabel.style.webkitTextFillColor = c;
  nameLabel.style.filter = "none";
  nameLabel.style.color = c;
}

function toggleRoll() {
  if (remainingNames.length === 0) return;

  if (isRolling) {
    stopRoll();
  } else {
    startRoll();
  }
}

function startRoll() {
  isRolling = true;
  startTime = Date.now();
  nameLabel.dataset.picked = "0";
  rollTick();
  setTimeout(stopRoll, 3000); // 3秒自动停
}

function rollTick() {
  if (!isRolling) return;

  const elapsed = Date.now() - startTime;
  const name = remainingNames[Math.floor(Math.random() * remainingNames.length)];
  nameLabel.textContent = name;
  setKaleidoscopeColor();

  let delay = 80;
  if (elapsed > 2000) {
    const ratio = Math.min((elapsed - 2000) / 1000, 1);
    delay = 80 + ratio * 220;
  }

  timer = setTimeout(rollTick, delay);
}

function stopRoll() {
  if (!isRolling) return;
  isRolling = false;
  clearTimeout(timer);

  const idx = Math.floor(Math.random() * remainingNames.length);
  const finalName = remainingNames.splice(idx, 1)[0];
  nameLabel.textContent = finalName;
  nameLabel.dataset.picked = "1";
  resetGoldStyle();
  updateDisplay();
}

function switchClass() {
  currentIdx = (currentIdx + 1) % classKeys.length;
  currentClass = classKeys[currentIdx];
  originalNames = [...CLASSES[currentClass]];
  remainingNames = [...originalNames];
  nameLabel.dataset.picked = "0";
  clearTimeout(timer);
  isRolling = false;
  nameLabel.textContent = "已换班";
