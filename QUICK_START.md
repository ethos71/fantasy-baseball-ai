# ⚾ Fantasy Baseball AI - Quick Start Card

## 🚀 The Simplest Way to Get Sit/Start Recommendations

### Step 1: Initial Setup (First Time Only)
```bash
python src/fb_ai.py --refresh
```
Takes ~5-10 minutes. Do this once to download all data.

---

### Step 2: Morning of Game Day

**Check when your games start:**
```bash
./fb-ai --when
```

This shows you exactly when to run the analysis (30 mins before first game).

---

### Step 3: 30 Minutes Before First Game

**Get sit/start recommendations:**
```bash
./fb-ai
```

That's it! The system will:
- ✅ Update latest data
- ✅ Run all 13 factor analyses
- ✅ Tune weights (if before 10 AM) or skip for speed (if after 10 AM)
- ✅ Show you who to start and who to bench

**Too close to game time? Use quick mode:**
```bash
./fb-ai --quick
```

---

### Step 4: Review & Set Lineup

The analysis will show:

```
🌟 TOP 5 STARTS:
  +1.85  Aaron Judge              ✅ FAVORABLE - START
  +1.72  Shohei Ohtani            ✅ FAVORABLE - START
  +1.68  Mookie Betts             ✅ FAVORABLE - START
  ...

🚫 BOTTOM 5 SITS:
  -1.45  Player Name              ⚠️ UNFAVORABLE - CONSIDER BENCHING
  -1.62  Player Name              🚫 VERY UNFAVORABLE - BENCH
  ...
```

Apply recommendations to your Yahoo Fantasy lineup!

---

## 📊 Other Useful Commands

```bash
./fb-ai --last              # View yesterday's recommendations
./fb-ai --date 2025-09-29   # Run for specific date (postseason)
./fb-ai --help              # See all options
```

---

## ⏰ Typical Daily Workflow

| Time | Command | What It Does |
|------|---------|-------------|
| **Morning (8-9 AM)** | `./fb-ai --when` | Check game times |
| **30 mins before games** | `./fb-ai` | Get recommendations |
| **Set lineup** | (Manual) | Apply recommendations in Yahoo |

---

## 🎯 Score Guide

| Score | Recommendation | What To Do |
|-------|----------------|------------|
| +1.5 to +2.0 | 🌟 VERY FAVORABLE | **Definitely start** |
| +0.5 to +1.5 | ✅ FAVORABLE | **Start if available** |
| -0.5 to +0.5 | ⚖️ NEUTRAL | Use your judgment |
| -1.5 to -0.5 | ⚠️ UNFAVORABLE | **Consider benching** |
| -2.0 to -1.5 | 🚫 VERY UNFAVORABLE | **Definitely bench** |

---

## 💡 Pro Tips

- **Run early?** System uses full analysis with weight tuning (more accurate)
- **Run late?** System skips weight tuning for speed (still very good)
- **Force quick mode?** Use `./fb-ai --quick` (1-2 minutes)
- **Weekly task:** Run `python src/scripts/daily_sitstart.py --tune-only` to refresh weight calibration

---

## 🔧 Automation (Optional)

**Setup daily automatic run at 7:00 AM:**
```bash
crontab -e
```

Add this line:
```
0 7 * * * cd /home/dominick/workspace/fantasy-baseball-ai && ./fb-ai
```

Recommendations will be ready when you wake up!

---

## 📁 Output Files

All recommendations saved to:
```
data/sitstart_recommendations_YYYYMMDD_HHMMSS.csv
```

View anytime with:
```bash
./fb-ai --last
```

Or open in Excel/Google Sheets for detailed analysis.

---

## ❓ Need Help?

```bash
./fb-ai --help                          # Quick help
cat README.md                           # Full documentation
cat docs/DAILY_WORKFLOW.md              # Detailed workflow guide
```

---

**That's it! Just type `./fb-ai` 30 minutes before game time and you're done!** 🎉
