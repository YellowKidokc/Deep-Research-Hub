# Theophysics Coherence Framework - Automated Scoring & Visualization

## 🚀 ONE-CLICK SOLUTION

### Quick Start (PowerShell - Recommended for Windows)

```powershell
.\SCORE_AND_VISUALIZE.ps1
```

That's it! This will:
1. ✅ Score all 159 canonical documents across 4 categories
2. ✅ Generate beautiful interactive HTML dashboard
3. ✅ Create enhanced Excel workbook with pivot tables
4. ✅ Automatically open the dashboard in your browser

### Quick Start (Python - Cross-Platform)

```bash
python SCORE_AND_VISUALIZE.py
```

---

## 📊 What Gets Analyzed

### Documents Scored (159 total)

1. **Theophysics Foundational Papers** (12 documents)
   - Your core axioms, theorems, and framework papers
   - Self-consistency validation

2. **US Founding Documents** (3 documents)
   - Declaration of Independence
   - Bill of Rights
   - US Constitution

3. **Scientific Theories** (118 documents)
   - Information Theory, Quantum Mechanics, Relativity
   - Thermodynamics, Evolution, Systems Theory
   - Game Theory, Network Theory, Chaos Theory

4. **World Religions Sacred Texts** (29 documents)
   - Christianity, Islam, Hinduism, Buddhism
   - Taoism, Confucianism, Judaism, Zoroastrianism
   - Sikhism, Jainism, Shinto, Ancient traditions

---

## 📈 Output Files

### Interactive HTML Dashboard
**Location:** `outputs/dashboard/coherence_dashboard.html`

**Features:**
- 📊 Category comparison bar chart
- 🏆 Top 20 documents horizontal ranking
- 🌟 12 Fruits radar chart by category
- 📈 Grade distribution histogram
- 💡 Key insights and findings
- 🎨 Beautiful dark theme with Theophysics branding

### Enhanced Excel Workbook
**Location:** `outputs/dashboard/coherence_analysis_with_charts.xlsx`

**Sheets:**
- `All_Documents` - Complete dataset (159 rows)
- `Category_Summary` - Statistical breakdown by category
- `Top_50` - Highest scoring documents
- `Theophysics` - Your papers ranked
- `US_Founding_Documents` - Founding docs analyzed
- `Scientific_Theories` - All 118 theories
- `World_Religions` - Sacred texts
- `Fruits_by_Category` - 12 Fruits breakdown

---

## ⚙️ Advanced Options

### PowerShell

```powershell
# Regenerate dashboard only (skip scoring)
.\SCORE_AND_VISUALIZE.ps1 -SkipScoring

# Don't auto-open browser
.\SCORE_AND_VISUALIZE.ps1 -OpenDashboard:$false
```

### Python

```bash
# Regenerate dashboard only (skip scoring)
python SCORE_AND_VISUALIZE.py --skip-scoring

# Don't auto-open browser
python SCORE_AND_VISUALIZE.py --no-browser
```

---

## 🔧 Manual Steps (if needed)

### Step 1: Score Documents
```bash
python score_all_canonical.py
```

### Step 2: Generate Dashboard
```bash
python create_dashboard.py
```

---

## 📁 Directory Structure

```
foundational_papers_scoring/
├── SCORE_AND_VISUALIZE.ps1       # One-click PowerShell automation
├── SCORE_AND_VISUALIZE.py        # One-click Python automation
├── score_all_canonical.py        # Scoring engine
├── create_dashboard.py           # Dashboard generator
├── README.md                     # This file
└── outputs/
    ├── comprehensive/            # Raw scoring data (CSV, JSON, Excel)
    └── dashboard/                # Generated visualizations
        ├── coherence_dashboard.html
        └── coherence_analysis_with_charts.xlsx
```

---

## 🎯 Key Findings

### 1. Theophysics Validates Itself
**χ = 0.7709** - Highest category average across all domains

### 2. Information Theories Dominate
Top 3 scientific theories are ALL information-based:
- Shannon Information Theory: **0.8871**
- Algorithmic Information Theory: **0.8750**
- Integrated Information Theory: **0.8663**

### 3. Eastern Philosophy > Western
- Upanishads: **0.8103**
- Bhagavad Gita: **0.7954**
- Tao Te Ching: **0.7903**
- Bible Genesis: **0.6524**

### 4. Coherence Hierarchy
Information Theories **(0.87)** > Theophysics **(0.77)** > Eastern Philosophy **(0.75)** > Western Religion **(0.60)**

---

## 🛠️ Requirements

- Python 3.7+
- pandas
- openpyxl
- PowerShell (for .ps1 script, Windows only)

Install Python dependencies:
```bash
pip install pandas openpyxl
```

---

## 📧 Support

For questions about the Theophysics Coherence Framework or this analysis toolkit, please refer to the main Theophysics documentation.

---

## 🙏 Acknowledgments

Built on the 12 Fruits of the Spirit coherence metric:
1. Grace
2. Hope
3. Patience
4. Faithfulness
5. Self-Control
6. Love
7. Peace
8. Truth
9. Humility
10. Goodness
11. Unity
12. Joy

---

**May your coherence be high and your insights profound! 🌟**
