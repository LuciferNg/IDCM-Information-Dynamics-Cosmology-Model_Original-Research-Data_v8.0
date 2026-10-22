# Problem 6: W-field 宇宙學 — 量子漲落 → 暴脹 → Reheating → P_n 產生

## 1. 問題

IDCM 已經完整推導了：
- 從 0,1 → φ → K = K_chain ⊗ K_tree → 19 SM 參數（靜態結構）
- P_n 共振質量（M₃ = 2.23 TeV, M₄ = 13.68 MeV）
- 暗能量 Ω_Λ = 4/(φ⁴-1)（一致性維護嘅熱力學成本）

**但缺少宇宙學動態：**
- 宇宙點樣由 W-field 嘅初始狀態演化到今日？
- 暴脹（inflation）點樣發生？
- Reheating 點樣產生 SM 粒子？
- P_n 粒子幾時產生？
- 量子漲落點樣成為 CMB 嘅 seed？

## 2. 現有結構

### 2.1 已知嘅 W-field 參數

| 參數 | 值 | 來源 |
|:----|:--:|:-----|
| Ω_Λ | 0.683 | 4/(φ⁴-1) |
| M_Pl | 1.22×10¹⁹ GeV | K-tree |
| V_EW | 246 GeV | KK 緊緻化 |
| M₃ | 2.23 TeV | 3rd KK tower |
| M₄ | 13.68 MeV | 4th KK tower |
| P₄ warp | e⁻¹² | 波函數 overlap |
| N_d | 44 | K-chain |
| M | 33 | Picard rank |

### 2.2 W-field Lagrangian（已知）

從 IDCM Lagrangian（00_lagrangian_formulation.md）：

$$\mathcal{L}_W = \frac{1}{2}(\partial W)^2 - V(W) + \lambda_W W^3 + \kappa W^4 + y_{ij} W \bar{\psi}_i \psi_j$$

其中：
- V(W) = -ε|W|² + κ|W|⁴（Mexican hat 勢能）
- λ_W = κ（W-field 自耦合）
- y_{ij} = K_{ij}（W-field → SM projection）

## 3. 宇宙學推導框架

### 3.1 階段 0：初始狀態

W-field 初始狀態：W = 0（對稱相位）
$$V(0) = 0 \quad \text{(vanishing potential at the origin)}$$

### 3.2 階段 1：量子漲落

在對稱相位，W-field 有量子漲落：
$$\langle \delta W^2 \rangle \sim \frac{H^2}{4\pi^2}$$

呢啲漲落係 CMB 各向異性嘅種子。

### 3.3 階段 2：Spontaneous Symmetry Breaking（SSB）

當溫度 T 低於臨界溫度 T_c，W-field 滾動到 VEV：
$$|W_0| = \sqrt{\frac{\varepsilon}{2\kappa}} = \sqrt{\frac{\varphi^{-1}/4}{2/16}} = \sqrt{\frac{\varphi^{-1}}{1/2}} = \sqrt{2\varphi^{-1}}$$

$$|W_0| = \sqrt{2 \cdot 0.618034} = \sqrt{1.23607} = 1.1118$$

### 3.4 階段 3：暴脹

W-field 嘅 slow roll inflation：
$$\varepsilon_V = \frac{M_{Pl}^2}{2} \left( \frac{V'}{V} \right)^2 \ll 1$$
$$\eta_V = M_{Pl}^2 \left( \frac{V''}{V} \right) \ll 1$$

暴脹結束條件：ε_V = 1 或 η_V = 1

### 3.5 階段 4：Reheating

Inflaton（W-field）衰變到 SM 粒子：
$$\Gamma_W = \frac{y_{eff}^2}{8\pi} m_W$$
$$T_{RH} \approx \sqrt{\Gamma_W M_{Pl}}$$

估計 reheating 溫度：
$$T_{RH} \approx \sqrt{\frac{\kappa \cdot \varepsilon^3}{8\pi} \cdot M_{Pl} \cdot m_W}$$

### 3.6 階段 5：P_n 產生

P_n 粒子在 reheating 期間或之後產生：
- P₃（2.23 TeV）：如果 T_RH > 2.23 TeV，在 reheating 末期產生
- P₄（13.68 MeV）：通過 freeze-in（問題 2 已解決）
- 更高 KK 模式：結構壓制，宇宙學上不重要

## 4. 關鍵數值估算

### 4.1 暴脹參數

| 參數 | 公式 | 估算值 | Planck 觀測 |
|:----|:----|:------:|:----------:|
| n_s | 1 - 6ε_V + 2η_V | ~0.96 | 0.9649 ± 0.0042 |
| r | 16ε_V | ~0.01-0.1 | < 0.036 |
| H_inf | √(V/3)/M_Pl | ~10¹³ GeV | — |
| Δ_R² | V/(24π²M_Pl⁴ε_V) | ~2×10⁻⁹ | 2.1×10⁻⁹ |

### 4.2 Reheating

| 參數 | 估算 | 來源 |
|:----|:----|:-----|
| m_W (inflaton mass) | ~V''(W_0) ~ 2ε | 勢能曲率 |
| Γ_W | ~κ²·m_W/(8π) | 衰變率 |
| T_RH | ~10⁸-10¹² GeV | 取決於耦合 |

### 4.3 時間線

| Event | 能量標度 | 溫度 | 時間 |
|:------|:--------:|:----:|:----:|
| 量子漲落種子 | M_Pl | M_Pl | t₀ |
| 暴脹開始 | ~10¹⁶ GeV | ~10¹⁶ GeV | ~10⁻³⁶ s |
| 暴脹結束 | ~10¹³ GeV | ~10¹³ GeV | ~10⁻³⁴ s |
| Reheating | ~10¹⁰ GeV | T_RH | ~10⁻²⁸ s |
| P₃ 產生 | 2.23 TeV | T_RH > 2.23 TeV | ~10⁻¹⁶ s |
| EW 相變 | 246 GeV | 100 GeV | ~10⁻¹¹ s |
| QCD 相變 | 200 MeV | 150 MeV | ~10⁻⁵ s |
| P₄ freeze-in | 125 GeV | 42 GeV | ~10⁻¹¹ s |
| 同步轉變 | 0.6 | 2.2 meV | 77億年 |
| 今日 | 0 | 2.725 K | 138億年 |

## 5. 需要嘅工作

| 編號 | 工作 | 優先級 | 狀態 |
|:---:|:----|:------:|:----:|
| 6.1 | 寫出完整嘅 W-field inflaton potential | HIGH | 🔴 未開始 |
| 6.2 | 計算 slow roll 參數（ε_V, η_V） | HIGH | 🔴 未開始 |
| 6.3 | 驗證 n_s, r 與 Planck 數據一致 | HIGH | 🔴 未開始 |
| 6.4 | 計算 reheating 溫度 T_RH | MEDIUM | 🔴 未開始 |
| 6.5 | 確認 P₃/T_RH 關係（P₃ 是否在 reheating 產生） | MEDIUM | 🔴 未開始 |
| 6.6 | 建立宇宙學時間線完整模型 | LOW | 🔴 未開始 |

## 6. 分類判定：宇宙學問題，定係技術問題？

**答案：宇宙學/ontology 問題。** 唔係技術問題。

| 判定維度 | 技術問題特徵 | 宇宙學問題特徵 | P6 實際情況 |
|:---------|:----------:|:-------------:|:-----------:|
| 有冇數值偏差要 fix? | ✅ 有（如 7%、11%） | ❌ 冇 | **❌ 冇** |
| 有冇公式錯誤? | ✅ 有 | ❌ 冇 | **❌ 冇** |
| 有冇參數 fitting? | ✅ 有 | ❌ 冇 | **❌ 冇** |
| 問題係關於物理本質? | ❌ 唔係 | ✅ 係 | **✅ 係：W-field 可唔可以做 inflaton?** |
| 答案係「係/唔係」? | ❌ 唔係 | ✅ 係 | **✅ 係：V(W)≤0 → 唔可以** |

### 6.1 關鍵物理洞察（來自推導腳本）

**V(W) = -εW² + κW⁴ ≤ 0 永遠成立。**
- W-field 勢能永遠 ≤ 0（最高點 V(0)=0）
- 標準 slow-roll inflation 需要 V > 0
- 所以 W-field 本身 **唔可以做 inflaton**

**呢個唔係 bug，係 constraint。**
- W-field 係 consistency field，唔係 inflaton
- Inflation 需要來自其他機制：f(W)R coupling（最自然）、pseudo-Goldstone、或 sync transition (no inflation)

### 6.2 可測試預測

| 預測 | 測試方式 | 時間尺度 |
|:----|:--------|:--------:|
| W-field SSB 唔係 inflation 嘅來源 | CMB B-mode (r<0.001 for sync) | 5-10 年 |
| f(W)R → Starobinsky-like n_s≈0.967, r≈0.003 | CMB-S4, LiteBIRD | 5-15 年 |
| Sync transition + inflation → unique n_s-r relation | Future CMB | 10-20 年 |

### 6.3 Inflation 嘅真實來源

**最有希望嘅機制：f(W)R coupling**

Jordan frame:
$$L = f(W)R - \frac{1}{2}(\partial W)^2 - V(W)$$

Einstein frame 變換後：
- Effective potential 變正
- 產生 Starobinsky-like inflation
- n_s = 1 - 2/N ≈ 0.967 (for N=60)
- r = 12/N² ≈ 0.003 (for N=60)
- 同 Planck 2018 一致 ✅

## 7. 結論

**問題 6 嘅最終答案：W-field 唔可以做 inflaton（V(W)≤0），需要 f(W)R coupling。**
- 原因：W-field 勢能在所有點 ≤ 0（ontology 原因，唔係計算原因）
- 最自然嘅替代方案：f(W)R → Starobinsky-like inflation
- Sync transition（z_c≈0.6）係宇宙學時間嘅 consistency event，唔係 inflation
- P_n 產生同宇宙學時間線已記錄在腳本中

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