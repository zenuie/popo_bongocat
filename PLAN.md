# Po 桌寵專案計劃書（Desktop Pet "Po"）

> 這份文件是給 **Claude Code** 接手用的規格書。前期的技術選型討論已經完成，
> 下列決策請當作**已定案**，不需要再重新評估或詢問使用者，直接照著實作即可。
> 使用者母語為繁體中文，溝通請用繁體中文，程式碼與識別字用英文。

---

## 0. 一句話描述

在 Windows 與 macOS 桌面上，常駐一隻叫「Po」的機器人桌寵：透明、永遠置頂、可拖曳，
會待機飄浮，滑鼠移過去 / 點擊時會切換姿勢與反應。先做出「活著」的 MVP，再逐步加互動。

---

## 1. 技術選型（已定案，理由附後，請勿更動）

| 項目 | 決定 | 理由 |
|---|---|---|
| 語言 | **Python 3.10+** | 迭代最快、桌寵範例最多、debug 最容易 |
| GUI 框架 | **PySide6（Qt6）** | 透明/置頂在 Win+macOS 行為一致，跨平台抹平度最高 |
| 目標平台 | **Windows 10/11 + macOS 12+** | |
| 打包 | PyInstaller | macOS 需另處理 .app bundle / 簽章（見 §8） |

不要改用 C++、Go、Electron/Tauri。原型階段 Python/PySide6 在「開發速度 × 跨平台 × 範例豐富」三者平衡最佳，已評估過。

---

## 2. 美術素材清單（已備妥，放在 `assets/`）

三張圖皆為 **112×112、RGBA、已正確去背（透明背景）**，是同一隻角色「Po」（戴耳機的機器人）的不同姿勢。

| 檔名 | 內容 | 對應狀態 |
|---|---|---|
| `assets/idle.png` | 正面、印有 "po / HELLO!" | `IDLE`（待機，預設） |
| `assets/hover.png` | 探頭、印有 "Hi / Po" | `HOVER`（滑鼠移過） |
| `assets/click.png` | 比讚、印有 "讚讚 / po" | `CLICK`（被點擊反應） |

### ⚠️ 兩個已知限制（實作時要注意，但 MVP 先不解決）

1. **文字燒進圖裡**：三張圖都把 "Hi" / "HELLO!" / "讚讚" 等字直接畫在圖上。
   桌寵的台詞理想上應該由程式動態產生對話泡泡，而非寫死在圖上。
   → **MVP 階段先接受**（直接用原圖）；Phase 2 再改成「乾淨角色 + 程式對話泡泡」。
2. **每個狀態只有一張靜圖，不是連續影格**：所以狀態切換會是「啪一下換姿勢」，
   不是流暢補間動畫。流暢動畫需要每個動作多格影格（未來補美術）。
   → MVP 用「程式做的飄浮 + 輕微縮放/彈跳」來營造生命感，彌補單張靜圖的僵硬。

---

## 3. 開發階段規劃

### Phase 1 — MVP（本次目標，請先完成這個並讓它能跑）
- 透明、無邊框、永遠置頂的視窗，桌面上顯示 `idle.png`
- 可用滑鼠拖曳移動
- 待機時程式化的上下飄浮 + 輕微縮放（呼吸感）
- 滑鼠移入 → 切到 `hover`；移出 → 回 `idle`
- 點擊 → 播 `click` 反應（短暫彈跳/放大），數秒後回 `idle`
- 透明區域點擊穿透（點到 Po 才有反應，點到空白處穿透到底下視窗）— 用 `setMask()`，見 §6
- 右鍵 / 系統匣選單：至少有「結束」

### Phase 2 — 互動與台詞
- 乾淨角色圖（去掉燒進去的文字）+ 程式動態對話泡泡（QLabel/自繪氣泡）
- 定時/隨機講話（報時、提醒、隨機台詞）
- 雙擊、餵食、跟隨滑鼠等小互動
- 開機自動啟動選項

### Phase 3 — 進階（視意願）
- 多格影格的流暢動畫（補美術後升級播放器）
- 或評估改用 Live2D（需重做美術為分圖層立繪，門檻高）
- 設定面板（飄浮幅度、大小、是否置頂等）

---

## 4. 專案結構（建議）

```
po-desktop-pet/
├─ PLAN.md                 ← 本文件
├─ requirements.txt
├─ README.md
├─ src/
│  ├─ main.py              ← 進入點：建立 App、視窗、系統匣
│  ├─ pet_window.py        ← 核心：透明置頂視窗 + 拖曳 + 遮罩
│  ├─ state_machine.py     ← IDLE / HOVER / CLICK 狀態切換
│  ├─ animator.py          ← 飄浮、縮放、彈跳等程式化動畫
│  ├─ platform/
│  │  ├─ __init__.py       ← 偵測平台、提供統一介面
│  │  ├─ win.py            ← Windows 專屬（如需 ghost 全穿透）
│  │  └─ mac.py            ← macOS 專屬（如需 ghost 全穿透）
│  └─ tray.py              ← 系統匣選單
└─ assets/
   ├─ idle.png
   ├─ hover.png
   └─ click.png
```

`requirements.txt` 至少：
```
PySide6>=6.6
# Windows ghost 模式才需要（MVP 可不裝）：
# pywin32 ; platform_system == "Windows"
# macOS ghost 模式才需要：
# pyobjc-framework-Cocoa ; platform_system == "Darwin"
```

---

## 5. 核心功能規格

### 5.1 視窗設定
建立 `QWidget`，套用以下 flags 與屬性：
- `Qt.FramelessWindowHint`（無邊框）
- `Qt.WindowStaysOnTopHint`（永遠置頂）
- `Qt.Tool`（不在工作列出現，macOS 上也不搶焦點）
- `setAttribute(Qt.WA_TranslucentBackground)`（透明背景）
- 視窗大小貼合圖片（含飄浮需要的上下緩衝空間）

用 `QLabel` 或自繪 `paintEvent` 顯示目前狀態的 `QPixmap`。

### 5.2 拖曳
攔截 `mousePressEvent` / `mouseMoveEvent` / `mouseReleaseEvent`：
按下記錄 offset，移動時 `self.move(globalPos - offset)`。
要區分「點一下」（觸發 CLICK 反應）與「拖曳」（移動位置）：
以滑鼠移動距離是否超過門檻（例如 5px）來判斷。

### 5.3 狀態機（state_machine.py）
狀態：`IDLE`、`HOVER`、`CLICK`。
- 預設 `IDLE`
- `enterEvent` → `HOVER`；`leaveEvent` → `IDLE`
- 點擊（非拖曳）→ `CLICK`，啟動計時器 N 秒後回 `IDLE`/`HOVER`
切換狀態時更新顯示的 pixmap，並**重算遮罩**（見 5.5，因為不同姿勢輪廓不同）。

### 5.4 程式化動畫（animator.py）
用 `QTimer`（~60fps 或省電一點 ~30fps）驅動：
- **飄浮**：y 位移 = `A * sin(t)`，A 約 4–8px
- **點擊彈跳**：短暫 scale 1.0→1.15→1.0 的 ease 動畫（可用 `QPropertyAnimation`）
這是 MVP 生命感的主要來源，務必做好手感（幅度別太大、速度別太快）。

### 5.5 點擊穿透（重要，注意這裡的技術選擇）
桌寵要的是：**點到 Po 本體有反應，點到周圍透明區域要穿透到底下的視窗**。

> 注意：PySide6 的半透明視窗，預設**整個矩形範圍**都會吃滑鼠事件，
> 透明像素區也會擋住底下視窗。所以「透明 = 自動穿透」是錯的，要額外處理。

**MVP 採用的做法：`setMask()`（跨平台、不需平台專屬程式碼）**
依目前 pixmap 的 alpha channel 產生 `QBitmap`/`QRegion`，`self.setMask(region)`。
這樣視窗實際只存在於不透明像素處，透明區的點擊自然穿透。
- 每次切換狀態（pixmap 改變）就要**重算一次遮罩**。
- 實作：取 pixmap 的 alpha，用門檻轉成 1-bit mask（`pixmap.mask()` 或 `QPixmap.createHeuristicMask()` / 自行用 alpha 產生最準）。

**（可選，Phase 2+）Ghost 全穿透模式**：若想要某種「連 Po 本體都不擋滑鼠」的純裝飾模式，
那才需要平台專屬程式碼，放在 `src/platform/`：
- Windows：用 `ctypes`/`pywin32` 對視窗加上 extended style `WS_EX_LAYERED | WS_EX_TRANSPARENT`
- macOS：透過 PyObjC 對 NSWindow 呼叫 `setIgnoresMouseEvents_(True)`
MVP **不需要**這段，setMask 已足夠。請勿在 MVP 過早引入平台原生程式碼。

### 5.6 系統匣（tray.py）
`QSystemTrayIcon` + `QMenu`，MVP 至少提供「結束」。
之後可加：置頂開關、重置位置、開機啟動。

---

## 6. 平台差異一覽

| 功能 | Windows | macOS | MVP 是否需分平台 |
|---|---|---|---|
| 透明/置頂/無邊框 | Qt 統一處理 | Qt 統一處理 | ❌ 共用 |
| 透明區穿透 | `setMask()` | `setMask()` | ❌ 共用 |
| Ghost 全穿透（可選） | `WS_EX_TRANSPARENT` | `setIgnoresMouseEvents` | （Phase 2+ 才需要） |
| 不出現在工作列/Dock | `Qt.Tool` 通常足夠 | `Qt.Tool`；必要時設 `LSUIElement` | 先用 Qt.Tool 觀察 |
| 打包簽章 | 較單純 | 需 codesign + notarize | 見 §8 |

**結論：MVP 幾乎可全部共用程式碼**，平台分歧到 Phase 2 引入 ghost 模式或打包時才會真正出現。

---

## 7. 打包與發布

- **Windows**：`pyinstaller --noconsole --onefile`，把 `assets/` 一併打包（`--add-data`）。相對單純。
- **macOS**：需產生 `.app` bundle。注意：
  - 沒有簽章 → 使用者下載後會被 Gatekeeper 擋；要正式散布需 Apple Developer 帳號做 **codesign + notarization**。
  - 個人測試可先用未簽章版本（手動右鍵開啟繞過）。
- 資源路徑：用 `sys._MEIPASS`（PyInstaller）或相對 `__file__` 解析 `assets/`，避免打包後找不到圖。

---

## 8. 給 Claude Code 的起手指示

1. 先讀完本文件，把 §1 的技術選型當定案，不要重新討論語言。
2. 依 §4 建立專案骨架與 `requirements.txt`，建立 venv 並安裝 PySide6。
3. **第一個里程碑**：讓 `idle.png` 以透明、置頂、可拖曳的視窗出現在桌面，並用 `setMask()` 完成透明區穿透。先確認這個能跑、能拖、空白處能穿透。
4. 接著加狀態機（hover/click 切換）與飄浮動畫（§5.3 / §5.4）。
5. 加系統匣「結束」。
6. 跑起來給使用者看，再依回饋微調**手感**（飄浮幅度、彈跳強度、切換時機）——這部分要快速迭代，預期會來回多次。
7. MVP 完成前，**不要**引入平台原生 click-through、不要動 Live2D、不要處理燒字問題（那些是 Phase 2）。

### 驗收標準（MVP Done 的定義）
- [ ] Po 出現在桌面、永遠置頂、無邊框、背景透明
- [ ] 可用滑鼠拖曳移動
- [ ] 點空白透明區會穿透到底下視窗
- [ ] 待機時有自然的飄浮（呼吸感）
- [ ] 滑鼠移入切 hover、移出回 idle
- [ ] 點擊（非拖曳）觸發 click 反應後自動回復
- [ ] 系統匣可結束程式
- [ ] 同一份程式碼在 Windows 與 macOS 都能跑起來

---

## 9. 未來待決事項（記錄，非 MVP 範圍）
- 燒進圖的文字如何移除：請繪師出乾淨版 / 或程式裁切？
- 是否要連續影格動畫（需補美術）或轉 Live2D（需重做分圖層）。
- 對話泡泡內容來源：固定台詞庫？報時/提醒？是否接 API？
- 開機自動啟動、設定面板。
