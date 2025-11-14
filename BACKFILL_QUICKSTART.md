# Backfill Quick Reference

## 🚀 Start Backfilling Now

### Test First (5 minutes)
```bash
python src/scripts/batch_backfill.py --month 2024-09
```

### Full 3-Year Backfill (18-72 hours)

**Option 1: Sequential Processing**
```bash
# Run in background, one year at a time
nohup python src/scripts/batch_backfill.py --year 2024 > backfill_2024.log 2>&1 &
# When done, run 2023, then 2022
```

**Option 2: Parallel Processing (Faster)**
```bash
# Terminal 1
nohup python src/scripts/batch_backfill.py --year 2024 > backfill_2024.log 2>&1 &

# Terminal 2
nohup python src/scripts/batch_backfill.py --year 2023 > backfill_2023.log 2>&1 &

# Terminal 3
nohup python src/scripts/batch_backfill.py --year 2022 > backfill_2022.log 2>&1 &
```

## 📊 Monitor Progress

```bash
# Check what's running
ps aux | grep batch_backfill

# View live progress
tail -f backfill_2024.log

# Check checkpoint
cat data/batch_checkpoint.txt

# Count completed dates
ls data/sitstart_recommendations_*.csv | wc -l
```

## 🔄 Resume After Interruption

```bash
# Just run the same command again - it auto-resumes
python src/scripts/batch_backfill.py --year 2023

# Or use auto mode
python src/scripts/batch_backfill.py --auto
```

## 📝 All Commands

| Command | Description |
|---------|-------------|
| `--date 2023-04-15` | Single date |
| `--month 2023-04` | Entire month |
| `--year 2023` | Entire year |
| `--start 2023-01-01 --end 2023-03-31` | Custom range |
| `--auto` | Process next pending date |

## 📁 Output Locations

- **Data**: `data/sitstart_recommendations_YYYYMMDD_*.csv`
- **Logs**: `data/backfill_logs/backfill_YYYYMMDD.log`
- **Checkpoint**: `data/batch_checkpoint.txt`

## ⏱️ Time Estimates

- 1 day: ~1 minute
- 1 month: ~30-60 minutes
- 1 year: ~6-24 hours
- 3 years: ~18-72 hours

## 🆘 Troubleshooting

**Process stopped?** Just run the same command - it will resume.

**Want to restart?** Delete checkpoint:
```bash
rm data/batch_checkpoint.txt
```

**Check for errors:**
```bash
grep -i error data/backfill_logs/*.log
```

---

📖 Full documentation: See **BACKFILL_GUIDE.md**
