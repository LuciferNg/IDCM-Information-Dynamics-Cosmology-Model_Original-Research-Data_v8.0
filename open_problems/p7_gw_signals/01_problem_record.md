# Problem 7: 重力波信號 — W-field 相變產生嘅隨機重力波背景

## 1. 問題

W-field 喺早期宇宙經歷了 spontaneous symmetry breaking（自發對稱破缺），呢個相變理論上會產生隨機重力波背景（Stochastic Gravitational Wave Background, SGWB）。

**但呢個問題嘅本質係宇宙學/ontology 問題，唔係技術問題。**
- 冇數值偏差要 fix（唔似 p1-p5 有 7%、11%、34% 偏差）
- 冇公式錯誤
- 冇參數 fitting
- 問題係：W-field 嘅本質會唔會產生可探測嘅 GW？

## 2. 物理機制

### 2.1 W-field 相變

W-field 嘅 Mexican hat 勢能：
$$V(W) = -\varepsilon |W|^2 + \kappa |W|^4$$

喺 T > T_c，W-field 喺 W = 0（對稱相位）
喺 T < T_c，W-field 滾動到 VEV：
$$|W_0| = \sqrt{\frac{\varepsilon}{2\kappa}} = \sqrt{\frac{\varphi^{-1}/4}{2/16}} = \sqrt{2\varphi^{-1}} \approx 1.11$$

臨界溫度 T_c 由勢能參數決定：
$$T_c \sim \sqrt{\varepsilon} \cdot M_{Pl} \sim 0.39 \cdot M_{Pl} \sim 4.7 \times 10^{18} \text{ GeV}$$

呢個係非常高嘅溫度——接近 Planck 標度。相變發生喺暴脹之前或期間。

### 2.2 GW 產生機制

相變產生 GW 嘅三種機制：

| 機制 | 信號特徵 | 峰值頻率 | IDCM 相關性 |
|:----|:---------|:--------:|:-----------|
| 氣泡碰撞 | 尖峰譜，Ω ∝ f³ | f_* ∼ β | 🟡 如果係 first-order |
| 聲波 | 雙峰譜 | f_* ∼ 2β | 🟡 如果係 second-order |
| 湍流 | 冪律譜 | f_* ∼ β/2 | 🟡 如果係 first-order |

### 2.3 相變參數

| 參數 | 定義 | IDCM 值 | 預期範圍 |
|:----|:----|:-------:|:--------:|
| α | ρ_vac/ρ_rad | ε/κ | ~2.47 |
| β/H | 相變速率 | O(100)-O(1000) | 取決於溫度和勢能形狀 |
| T_* | 相變溫度 | T_c/√2 ~ 10¹⁸ GeV | 接近 Planck 標度 |
| v_w | 氣泡壁速度 | ~1 | 取決於摩擦力 |

## 3. 推導框架

### 3.1 GW 能譜公式

氣泡碰撞主導嘅 SGWB：
$$\Omega_{GW}(f)h^2 = 1.67 \times 10^{-5} \left(\frac{H_*}{\beta}\right)^2 \left(\frac{\kappa \alpha}{1+\alpha}\right)^2 \left(\frac{100}{g_*}\right)^{1/3} S(f)$$

譜形函數：$S(f) = \frac{3.8(f/f_{peak})^{2.8}}{1 + 2.8(f/f_{peak})^{3.8}}$

峰值頻率：
$$f_{peak} = 1.65 \times 10^{-5} \text{ Hz} \left(\frac{f_*}{\beta}\right) \left(\frac{\beta}{H_*}\right) \left(\frac{T_*}{100 \text{ GeV}}\right) \left(\frac{g_*}{100}\right)^{1/6}$$

### 3.2 IDCM 特有嘅參數

IDCM 相變參數由 W-field 結構唯一確定：
$$\alpha = \frac{\varepsilon}{\kappa} = \frac{\varphi^{-1}/4}{1/16} = 4\varphi^{-1} = 2.472$$

$$\kappa \approx \frac{1}{8} \frac{\lambda_W^2}{16\pi^2} \approx O(10^{-2})$$

所以 idcm 預測：
- α ~ 2.47（相對大嘅相變強度）
- β/H* ~ 100-1000（中等相變速率）
- T_* ~ O(10¹⁸) GeV（高溫相變）

### 3.3 峰值頻率估算

$$f_{peak} \sim 1.65 \times 10^{-5} \text{ Hz} \times 1 \times 100 \times \frac{10^{18}}{100} \times \left(\frac{100}{100}\right)^{1/6}$$

$$f_{peak} \sim 1.65 \times 10^{-5} \times 10^{16} \text{ Hz} \sim 1.65 \times 10^{11} \text{ Hz}$$

呢個頻率遠高於 LISA（mHz）同 DECIGO（0.1 Hz）嘅靈敏度範圍。

**結論：** W-field 相變喺 Planck 標度，產生嘅 GW 頻率太高，現有/近未來探測器探測唔到。

## 4. 替代場景：低能相變

IDCM 可能仲有其他低能相變：

### 4.1 同步轉變（Sync Transition at z_c ≈ 0.6）

- 溫度：T_c ~ 2.2 × 10⁻³ eV（宇宙學時間 77 億年）
- 係 slow phase transition（唔係 first-order bubble nucleation）
- 唔會產生可探測嘅 GW 信號

### 4.2 P_n 退耦（類似 QCD phase transition）

當溫度低於 P_n 質量時，P_n 粒子從熱浴退耦：
- P₃：T~2.23 TeV（宇宙學時間好早）
- P₄：T~13.68 MeV（freeze-in，唔係相變）
- GW 信號太弱，探測唔到

### 4.3 W-field 嘅 second minimum

如果有 second minimum（W_U(1) breaking），可能有低能相變。但 IDCM Lagrangian 冇 evidence 支持 second minimum。

## 5. 可探測性分析

| 探測器 | 頻率範圍 | 靈敏度 Ωh² | IDCM 預測 | 可探測？ |
|:------|:--------:|:----------:|:---------:|:--------:|
| LISA | 0.1-100 mHz | ~10⁻¹² | << 10⁻¹² | ❌ |
| DECIGO | 0.1-10 Hz | ~10⁻¹⁴ | << 10⁻¹⁴ | ❌ |
| LIGO A+ | 10-10³ Hz | ~10⁻⁹ | << 10⁻⁹ | ❌ |
| ET | 1-10⁴ Hz | ~10⁻¹¹ | << 10⁻¹¹ | ❌ |
| PTA (SKA) | 10⁻⁹-10⁻⁷ Hz | ~10⁻¹⁰ | << 10⁻¹⁰ | ❌ |
| BBN bound | 10⁻¹⁰-10⁻⁶ Hz | ~10⁻⁶ | < 10⁻⁶ | ❌ |

## 6. 分類判定：宇宙學問題，定係技術問題？

**答案：宇宙學/ontology 問題。** 唔係技術問題。

| 判定維度 | 技術問題特徵 | 宇宙學問題特徵 | P7 實際情況 |
|:---------|:----------:|:-------------:|:-----------:|
| 有冇數值偏差要 fix? | ✅ 有（如 7%、11%） | ❌ 冇 | **❌ 冇** |
| 有冇公式錯誤? | ✅ 有 | ❌ 冇 | **❌ 冇** |
| 有冇參數 fitting? | ✅ 有 | ❌ 冇 | **❌ 冇** |
| 問題係關於物理本質? | ❌ 唔係 | ✅ 係 | **✅ 係：W-field 會唔會 thermalize?** |
| 答案係「係/唔係」? | ❌ 唔係 | ✅ 係 | **✅ 係：W-field 唔 thermalize，所以冇 GW** |

### 6.1 關鍵物理洞察

**「冇信號」本身就係預測，唔係計算錯誤。**

W-field 唔 thermalize（耦合 y ∼ 10⁻⁶）嘅原因：
- W-field 係 consistency field，唔係 SM gauge sector 嘅粒子
- K matrix 耦合係 φ-power 級數（y ∼ φ⁻ᵏ），唔係 gauge coupling（g ∼ 0.1-1）
- 所以 W-field 永遠唔會同 thermal bath 達到平衡
- → 冇 thermal phase transition
- → 冇 bubble nucleation
- → 冇 GW from SSB

### 6.2 可測試預測

| 預測 | 測試方式 | 時間尺度 |
|:----|:--------|:--------:|
| LISA 唔會探測到 W-field 相變嘅 GW | LISA 數據（2030s） | 5-10 年 |
| DECIGO 唔會探測到 W-field 相變嘅 GW | DECIGO 數據（2040s） | 15-20 年 |
| 任何 stochastic background 如果出現，唔係 W-field SSB 產生嘅 | 交叉對比頻譜形狀 | 持續 |

### 6.3 如果將來探測到 GW，係乜嘢？

如果 LISA/DECIGO 探測到 stochastic GW background，IDCM 可以講：
**「呢個唔係 W-field SSB 產生嘅。可能係 cosmic strings、first-order EW phase transition、或其他新物理。」**

呢個 refutability 本身就係科學嘅標誌。

## 7. 結論

**問題 7 嘅最終答案：W-field SSB 唔會產生可探測嘅 GW 信號。**
- 原因：W-field 唔 thermalize（ontology 原因，唔係技術原因）
- 「冇信號」就係 IDCM 嘅預測
- 呢個預測係可 refute 嘅：如果將來 LISA/DECIGO 探測到 stochastic GW，嗰個信號唔係來自 W-field

---

## 附件：與其他問題嘅對比

| # | 問題 | 類型 | 解決方式 |
|:-:|:----|:----|:--------|
| 1 | P₃ gg 寬度 | **技術** | 跡反常公式確認，BR(t̄t)=95.6% |
| 2 | P₄ freeze-in | **技術** | 因子 1.85 在 O(10) 不確定性內 |
| 3 | ρ 偏差 7% | **技術** | ε/2 修正已在文檔，0.11% match |
| 4 | J 偏差 34% | **技術** | J=A²λ⁶η 不依賴 ρ，0.5% match |
| 5 | m_u/m_t 偏差 11% | **技術** | CY₃ 近似 artifact，結構公式 4.08% |
| 6 | W-field 宇宙學 | **宇宙學/ontology** | V(W)≤0 → f(W)R 替代方案 |
| 7 | 重力波信號 | **宇宙學/ontology** | W-field 唔 thermalize → 冇 GW |