# 📍 GPS Spoof（Windows 版）— 用 Windows 電腦偽造 iPhone 的 GPS 位置

> 不需要越獄，不需要工程背景，照著步驟就可以把 iPhone 的 GPS 定位偽裝到世界上任何地方。

> **📌 使用方式：** 用 USB 線把 iPhone 接到 Windows 電腦，在電腦上執行這個工具，即可從電腦的瀏覽器控制 iPhone 的 GPS 位置。**Android 手機不適用。**

> 🍎 **用 Mac 的人請看 [README.md](README.md)。** 這份是專門給 Windows 使用者的版本。

---

## 在開始之前，先看這裡 👀

這個工具讓你可以：
- 打開地圖，點擊任意地點，iPhone 的 GPS 立刻移動過去
- 用虛擬搖桿控制移動方向，就像玩電動一樣
- 設定一連串路線點，自動沿路走
- 儲存常用地點到收藏夾，一鍵跳過去

**誰適合用：** Pokémon GO、旅遊類遊戲、測試 App 定位功能、任何需要假裝在其他地方的場合。

**完全不需要：** 越獄、購買任何東西、工程師背景。

> ⚠️ **Windows 和 Mac 最大的差別在哪裡？**
> Windows 本身不認得 iPhone，所以多了一個步驟：要先裝「Apple 裝置驅動」。另外，建立通道的指令在 Windows 要用「以系統管理員身分執行」的視窗來跑。其餘操作和 Mac 完全一樣。

---

## 目錄

- [你需要準備什麼](#-你需要準備什麼)
- [第一次設定（一次性）](#️-第一次設定一次性)
- [每次使用的步驟](#-每次使用的步驟)
- [Web UI 功能介紹](#️-web-ui-功能介紹)
- [常見問題與解決方法](#️-常見問題與解決方法)
- [English Reference](#-english-reference)

---

## 📋 你需要準備什麼

開始前，請確認你有以下東西。**缺一不可。**

### 硬體

**1. 一台 Windows 電腦**
- Windows 10 或 Windows 11 都可以

**2. 一支 iPhone**
- iOS 版本建議 16 或以上
- 確認方式：iPhone 設定 → 一般 → 關於本機 → 軟體版本

**3. 一條支援「資料傳輸」的 USB 線（非常重要！）**

> ⚠️ **市面上很多 USB 線只能充電，不能傳輸資料，這種線沒辦法用！**
>
> **怎麼判斷你的線是否支援資料傳輸？**
> 1. 把 iPhone 接上電腦
> 2. iPhone 螢幕出現「**要信任這台電腦嗎？**」→ ✅ 這條線可以用
> 3. iPhone 只出現充電閃電圖示，什麼也沒問 → ❌ 這條線不行，請換一條

---

### 軟體（免費，需要安裝一次）

這個工具在 Windows 上需要裝三樣東西：**Python**、**Apple 裝置驅動**、**pymobiledevice3 套件**。下面會一步一步帶你裝完。

---

<details>
<summary>📌 備註：什麼是「命令提示字元」？怎麼開？（點擊展開）</summary>

命令提示字元（英文叫 Command Prompt，簡稱 CMD）是 Windows 裡的一個程式，讓你用文字指令控制電腦。你不需要了解它怎麼運作，只需要知道怎麼開啟、怎麼貼上指令、怎麼按 `Enter`。

**打開命令提示字元的方法：**
1. 按下鍵盤左下角的 **開始鍵（⊞ Windows 鍵）**
2. 直接打字輸入「cmd」或「命令提示字元」
3. 按 `Enter` 開啟

**這個工具有些步驟需要「以系統管理員身分執行」，方法是：**
1. 開始鍵 → 輸入「cmd」
2. 在跳出來的「命令提示字元」上**按右鍵**
3. 選擇 **以系統管理員身分執行**
4. 跳出「是否允許這個 App 變更你的裝置」→ 點 **是**
5. 視窗標題列會出現「系統管理員」字樣，代表成功

**使用小技巧：**
- 貼上指令：在視窗內按右鍵，或按 `Ctrl + V`
- 執行指令：按 `Enter`
- 中斷正在執行的程序：按 `Ctrl + C`

</details>

---

## 🛠️ 第一次設定（一次性）

以下步驟只需要做一次，之後每次使用不需要重複。

### 步驟 A — 安裝 Python 3

Python 是一個讓電腦跑程式的工具，這個 GPS 工具需要它才能運作。

1. 用瀏覽器前往 [python.org/downloads](https://www.python.org/downloads/)
2. 點擊大大的黃色 **Download Python** 按鈕
3. 下載完成後，雙擊執行那個 `.exe` 安裝檔
4. ⚠️ **非常重要：** 安裝畫面最下方有一個勾選框 **「Add Python to PATH」**，**一定要打勾**，再點 **Install Now**
5. 安裝完成後，**開啟命令提示字元**，輸入 `python --version` 按 `Enter`
6. 看到 `Python 3.10.x` 或更高的數字 → ✅ 安裝成功

> **看到錯誤「不是內部或外部命令」？** 多半是安裝時忘了勾「Add Python to PATH」。請重新執行安裝檔，選 **Modify**，把那個勾選框打勾，或乾脆移除後重裝並記得打勾。

---

### 步驟 B — 安裝 Apple 裝置驅動（Windows 專屬，最關鍵）

Windows 本身不認得 iPhone，需要 Apple 的驅動程式才能透過 USB 跟 iPhone 溝通。最簡單的做法是安裝 **iTunes**，它會一併裝上需要的「Apple Mobile Device Support」。

1. 前往 [apple.com/itunes/download](https://www.apple.com/itunes/download/) 下載 **桌面版 iTunes**
   - 建議下載 Apple 官網的版本，安裝過程比較單純
2. 雙擊安裝，一路點「下一步」完成
3. 安裝完成後，用 USB 線把 iPhone 接上電腦
4. iPhone 跳出「**要信任這台電腦嗎？**」→ 點 **信任**，輸入解鎖密碼
5. 如果 iTunes 能看到你的 iPhone，代表驅動裝好了 ✅（看到後就可以把 iTunes 關掉，工具不需要它一直開著）

> **不想裝 iTunes？** 也可以裝 Microsoft Store 上的「Apple 裝置（Apple Devices）」App，同樣會帶上裝置驅動。但若遇到問題，桌面版 iTunes 相容性最穩。

---

### 步驟 C — 安裝必要的程式套件

1. 開啟命令提示字元
2. 把以下整行文字複製、貼上，按 `Enter`：
   ```
   pip install pymobiledevice3
   ```
3. 終端機會開始顯示一堆文字在跑，**這是正常的**，耐心等待
4. 等到你看到 `Successfully installed ...` 這樣的文字出現 → ✅ 安裝成功

> **遇到錯誤 `pip 不是內部或外部命令`？** 改用：
> ```
> python -m pip install pymobiledevice3
> ```

---

### 步驟 D — 在 iPhone 上開啟「開發者模式」

這個設定讓電腦的程式可以跟 iPhone 通訊。（iOS 16 以上才需要做這步，舊版本不需要）

1. 先用 USB 線把 iPhone 接上電腦
2. iPhone 螢幕如果出現「要信任這台電腦嗎？」，點擊 **信任**，然後輸入 iPhone 解鎖密碼
3. 在 iPhone 上打開 **設定**（灰色齒輪圖示）
4. 往下捲，找到並點擊 **隱私權與安全性**
5. 繼續往下捲到最底部
6. 找到 **開發者模式**，點進去
7. 把開關 **打開**（滑到綠色）
8. 出現警告說要重新啟動，點擊 **重新啟動**
9. iPhone 重啟後，再次確認開發者模式是 **開啟** 狀態

> **找不到「開發者模式」？** iOS 15 或更早版本不需要這個設定，可以跳過。

---

### 步驟 E — 下載本工具

1. 在這個 GitHub 頁面，點擊右上角的綠色 **Code** 按鈕
2. 點選 **Download ZIP**
3. 下載完成後，在檔案總管中找到下載的 ZIP 檔案，按右鍵 → **解壓縮全部**
4. 把解壓縮後的資料夾移到你容易找到的地方，例如「文件（Documents）」資料夾裡

---

## 🚀 每次使用的步驟

每次想要使用 GPS 模擬，都要照以下步驟操作。總共需要開啟 **兩個命令提示字元視窗** 和 **一個瀏覽器**。

---

### 步驟 1 — 連接 iPhone

1. 用 **資料傳輸 USB 線** 把 iPhone 接上電腦
2. 確認 iPhone 螢幕是 **亮著的且已解鎖**（不是黑色鎖定畫面）
3. 如果 iPhone 出現「**要信任這台電腦嗎？**」，點擊 **信任**，再輸入解鎖密碼

---

### 步驟 2 — 開啟「系統管理員」命令提示字元 1，建立通道

> 這個視窗 **整個使用期間都要保持開著**，不能關閉。

1. 開始鍵 → 輸入「cmd」→ 在「命令提示字元」上按右鍵 → **以系統管理員身分執行** → 點 **是**
   - ⚠️ **這一步一定要用系統管理員身分**，否則建立通道會失敗
2. 複製以下指令，貼到視窗，按 `Enter`（注意：Windows **不用** `sudo`）：
   ```
   python -m pymobiledevice3 remote start-tunnel
   ```
3. **第一次執行時**，如果它提示需要安裝 **WinTun** 驅動（一個虛擬網路卡），照畫面指示安裝即可，裝完再執行一次這個指令
4. 等待幾秒鐘，直到看到類似這樣的文字：
   ```
   RSD Address: fd1a:48e:cc16::1
   RSD Port:    58981
   ```
5. **把這兩行資訊抄下來（或截圖）**，下一步會用到
   - `RSD Address` 是一串數字和字母的組合
   - `RSD Port` 是一串純數字

> ⚠️ **注意：** 這兩個數字每次連接都會不一樣！每次使用都要重新看視窗的輸出，不能用上次的舊數字。

> **等了很久都沒看到 RSD Address？** 試試看：
> - 確認 iPhone 已解鎖（螢幕要亮著）
> - 確認這個視窗真的是「系統管理員」身分（標題列會寫）
> - 拔掉 USB 線再重新插上
> - 確認已點了「信任這台電腦」

---

### 步驟 3 — 開啟命令提示字元 2，啟動 GPS 伺服器

1. 開啟 **另一個新的命令提示字元視窗**（這個不用系統管理員身分，普通開啟即可，也不要關掉視窗 1）
2. 切換到工具所在的資料夾。輸入 `cd ` （cd 後面有一個空格），然後：
   - 打開 **檔案總管**，找到你下載並解壓縮的資料夾（`pikmin-spoof`）
   - 把那個資料夾 **直接拖進命令提示字元視窗**（拖到 `cd ` 後面）
   - 路徑會自動填入，按 `Enter`
3. 現在輸入以下指令（把 `<RSD_ADDRESS>` 換成步驟 2 抄下的 RSD Address，`<RSD_PORT>` 換成 RSD Port）：
   ```
   python gps_spoof.py --rsd <RSD_ADDRESS> <RSD_PORT>
   ```

   **舉例（你的數字會不一樣）：**
   ```
   python gps_spoof.py --rsd fd1a:48e:cc16::1 58981
   ```

4. 按 `Enter`，等待看到這行文字：
   ```
   Device connected. Ready to spoof.
   ```

   出現這行 → ✅ 成功！iPhone 已準備好接受 GPS 模擬

> **等了一分鐘還沒出現 `Device connected`？** 可能原因：
> - RSD Address 或 RSD Port 抄錯了（注意大小寫，數字不能有多餘空格，是冒號 `:` 不是句點 `.`）
> - 視窗 1 被意外關閉了，請重新以系統管理員身分開啟
> - iPhone 螢幕鎖定了，解鎖後再試

---

### 步驟 4 — 開啟控制介面

1. 打開 **Edge**、**Chrome** 或任何瀏覽器
2. 在網址列輸入：
   ```
   http://localhost:8765
   ```
3. 按 `Enter`
4. 你會看到一個地圖介面：左側是控制面板，右側是地圖
5. 確認左側面板最上方的小圓點變成 **綠色** ✅

🎉 **恭喜！設定完成。** 現在可以開始控制 iPhone 的 GPS 位置了！

> 如果小圓點是橘色，表示正在連接中，等 10 到 15 秒看看。
> 如果是紅色，表示連接失敗，請看下方「常見問題」。

---

## 🗺️ Web UI 功能介紹

Web UI 的所有功能，在 Windows 和 Mac 上 **完全相同**。完整的圖文說明請直接看 [README.md 的「Web UI 功能介紹」章節](README.md#️-web-ui-功能介紹)。以下是快速整理：

| 功能 | 怎麼操作 |
|------|---------|
| 狀態圓點 | 🟠 連接中 / 🟢 已連接可用 / 🔴 連接失敗 |
| 跳躍到座標 | 輸入緯度（Latitude）與經度（Longitude）→ 點 **Jump** |
| 走到某地 | 在地圖上點一下，GPS 平滑走過去 |
| 設定路線 | 連點多個地方，GPS 依序走完 |
| 點掉路線點 | 點地圖上帶數字的圖釘即可刪除 |
| 拖曳圖釘 | 按住目前位置的圖釘拖到新位置 |
| 搖桿 | 按住中心藍點往任意方向拖 |
| 速度 | 拖滑桿（5 走路、12 慢跑、25 騎車） |
| 收藏地點 | 選圖示、打名稱、點 **Save**；之後點 **Go** 一鍵傳送 |
| 停止模擬 | 點紅色 **⏹ Stop Spoofing**，再拔掉 USB |

> **找座標小技巧：** 打開 Google 地圖 → 在地點上按右鍵 → 最上方會顯示像 `25.0339, 121.5645` 的數字，前面是緯度、後面是經度。

> **Pokémon GO 玩家注意：** 速度太快可能被遊戲判定為飛人，建議保持在 10 km/h 以下。

---

## 🛠️ 常見問題與解決方法

<details>
<summary>❓ 問題一：建立通道時出現權限或網路錯誤</summary>

iOS 17 以上建立通道需要系統管理員權限。請確認：

1. 命令提示字元視窗 1 是用 **以系統管理員身分執行** 開啟的（標題列要有「系統管理員」字樣）
2. 如果提示缺少 **WinTun** 驅動，依畫面指示安裝後再試一次
3. 如果你的防毒或防火牆軟體擋下了，暫時允許 Python 的網路存取

</details>

<details>
<summary>❓ 問題二：iPhone 接上去電腦完全沒反應 / iTunes 看不到</summary>

這幾乎都是「Apple 裝置驅動」沒裝好。

1. 確認已照 **步驟 B** 裝好桌面版 iTunes
2. 換一條確定能傳輸資料的 USB 線（只能充電的線不行）
3. 換一個電腦上的 USB 埠，避免使用 USB Hub 或延長線
4. 打開 Windows 的 **裝置管理員**，看「可攜式裝置」或「通用序列匯流排控制器」底下有沒有出現 Apple 相關裝置；若有驚嘆號，按右鍵 → **更新驅動程式**

</details>

<details>
<summary>❓ 問題三：終端機顯示「'python' 不是內部或外部命令」</summary>

表示 Python 沒裝好，或安裝時沒勾「Add Python to PATH」。

1. 重新執行 Python 安裝檔，選 **Modify**，把 **Add Python to PATH** 打勾
2. 或移除後重裝，記得在第一個畫面勾選那個選項
3. 裝好後 **關掉再重開** 命令提示字元，再試一次

</details>

<details>
<summary>❓ 問題四：終端機顯示「No module named pymobiledevice3」</summary>

表示套件沒安裝成功，或裝在不同的 Python 環境。

```
pip install pymobiledevice3
```
若 `pip` 找不到，改用：
```
python -m pip install pymobiledevice3
```

</details>

<details>
<summary>❓ 問題五：出現「Address already in use」</summary>

表示上次的程式沒完全關閉，還在佔用位置。

**最新版本已自動處理這個問題！** 重新執行啟動指令時，程式會自動偵測並關閉上一個舊程序。

如果自動處理失敗，可手動關掉佔用 8765 埠的程式：
```
for /f "tokens=5" %a in ('netstat -ano ^| findstr :8765') do taskkill /PID %a /F
```
執行後等一秒，再重新啟動視窗 2 的指令。

</details>

<details>
<summary>❓ 問題六：狀態圓點是紅色，顯示連線失敗</summary>

請依序檢查：

1. **視窗 1 還在跑嗎？** 若已關閉或報錯，重新以系統管理員身分開啟並重新執行 `python -m pymobiledevice3 remote start-tunnel`，抄下新的 RSD Address 和 Port
2. **USB 線還接著嗎？iPhone 解鎖了嗎？** 確認線插緊、iPhone 螢幕亮著且已解鎖
3. **RSD 數字抄對了嗎？** 仔細對照視窗 1 的輸出，是冒號 `:` 不是句點 `.`

還是不行就完整重啟：關掉兩個視窗（`Ctrl + C`）→ 拔 USB 等 5 秒 → 重插 → 點「信任」→ 重新照步驟 2、3 來一次。

</details>

<details>
<summary>❓ 問題七：搖桿或地圖點了，但 iPhone 定位沒動</summary>

1. 先確認狀態圓點是 **綠色**（不是的話先解決連線，見問題六）
2. 某些 App（尤其 Pokémon GO）需要在 GPS 改變後 **重新打開 App** 才會讀到新位置
3. 速度滑桿往右拖快一點試試
4. 在瀏覽器按 `Ctrl + R` 重新整理 Web UI

</details>

<details>
<summary>❓ 問題八：停止後 iPhone GPS 仍停在假位置</summary>

這是正常的，不是故障。**把 USB 線拔掉**，等約 5 到 10 秒，iPhone GPS 會自動恢復真實位置。

若還不恢復：iPhone 設定 → 隱私權與安全性 → 定位服務 → 關掉等 3 秒再打開，或重新啟動 iPhone。

</details>

---

<details>
<summary>📁 專案結構（給好奇的人）</summary>

```
pikmin-spoof/           （下載解壓縮後的資料夾名稱，從這裡執行工具）
├── gps_spoof.py        主程式（Python 伺服器 + 地圖控制介面，跨平台）
├── favorites.json      你儲存的收藏地點（自動產生，請別手動刪除）
├── last_position.json  上次的 GPS 位置（自動產生）
├── README.md           Mac 版說明
├── README-Windows.md   本文件（Windows 版說明）
└── GPSSpoofMac/
    └── swift/          Swift 原始碼（Mac 原生介面，Windows 用不到，可忽略）
```

</details>

---

<details>
<summary>🌐 English Reference（英文快速參考，點擊展開）</summary>

> The full tutorial is in Traditional Chinese above. This section is a concise English guide for Windows users.

### What This Does

This tool lets you fake your iPhone's GPS location from a Windows PC — no jailbreak needed. Teleport anywhere, walk a custom route, use a joystick, and save favorite spots. **Android is not supported.**

### What You Need

**Hardware:**
- A Windows 10 or 11 PC
- An iPhone (iOS 16+ recommended)
- A **data-capable USB cable** — when plugged in, iPhone must ask "Trust This Computer?"

**Software (free, one-time install):**
1. **Python 3.10+** from [python.org/downloads](https://www.python.org/downloads/) — during install, **check "Add Python to PATH"**
2. **Apple device driver** — install desktop **iTunes** from [apple.com/itunes/download](https://www.apple.com/itunes/download/) (Windows can't talk to an iPhone without it)
3. **pymobiledevice3** — open Command Prompt and run: `pip install pymobiledevice3`

### One-Time Setup

Enable Developer Mode on iPhone (iOS 16+): Settings → Privacy & Security → scroll to bottom → Developer Mode → ON → restart.

### Every Time You Use It

You need **two Command Prompt windows**.

**Window 1 — Run as Administrator, keep it open the whole session:**
```
python -m pymobiledevice3 remote start-tunnel
```
- No `sudo` on Windows.
- On first run it may prompt to install the **WinTun** driver — install it and rerun.
- Wait for `RSD Address` and `RSD Port` — write them down.

**Window 2 (normal, not admin):**
```
python gps_spoof.py --rsd YOUR_RSD_ADDRESS YOUR_RSD_PORT
```
Wait for: `Device connected. Ready to spoof.`

**Browser:** Go to `http://localhost:8765` — wait for the green dot in the top left.

### Troubleshooting Quick Reference

| Problem | Fix |
|---------|-----|
| Tunnel fails / permission error | Make sure Window 1 is **Run as Administrator**; install **WinTun** if prompted |
| iPhone not detected / iTunes can't see it | Install desktop iTunes (Apple device driver); use a data cable; try another USB port |
| `'python' is not recognized` | Reinstall Python with **Add Python to PATH** checked; reopen the terminal |
| `No module named pymobiledevice3` | Run: `pip install pymobiledevice3` |
| "Address already in use" | Script auto-handles it. Else: `for /f "tokens=5" %a in ('netstat -ano ^| findstr :8765') do taskkill /PID %a /F` |
| Red status dot | Restart both windows; re-plug USB; re-copy RSD address/port |
| GPS not changing on iPhone | Restart the app on iPhone; ensure the green dot shows |
| GPS stuck on fake location after stopping | Unplug the USB cable — real GPS restores in ~10 seconds |

</details>

---

*如果你卡在任何步驟，或遇到本文沒有列出的問題，歡迎開一個 GitHub Issue 描述問題！*
