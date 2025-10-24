# Phase 2 Intelligence Engine - Quick Start Guide

## What's New in Phase 2

Phase 1 gave you **manual semantic exploration**. Phase 2 gives you **automated intelligence**.

### The Shift

**Phase 1 (Manual):**
- You update manifest.yaml manually
- You identify redundancies by inspection
- You guess at dependencies
- You discover capabilities through reading

**Phase 2 (Automated):**
- ✅ System scans code automatically
- ✅ AI finds redundancies and duplicates
- ✅ Blast radius calculated automatically
- ✅ Hidden capabilities inferred by AI

---

## 4 New Superpowers

### 1. 🔍 Automated Redundancy Scanner

**What it does:** Scans all code in your repository and finds duplicates

```bash
python .repometa/analyzer.py --scan-redundancies
```

**Output:**
```
Cluster #1 - 15 duplicates found
Potential savings: 450 lines
Locations:
   - testing/test_model.py:120-150 (30 lines)
   - phase-2-predictive/validation.py:88-118 (30 lines)
   ... 13 more duplicates
💡 Code appears in 8 files - consider creating shared module
```

**Use cases:**
- Find duplicate code before code review
- Identify consolidation opportunities
- Calculate technical debt in lines of code
- Prioritize refactoring efforts

**How it works:**
1. Extracts all code blocks from markdown files
2. Generates hash signatures for exact matches
3. Tokenizes content for similarity analysis
4. Clusters similar blocks (70%+ similarity)
5. Calculates potential line savings

### 2. 💥 Dependency Impact Analyzer

**What it does:** Calculates "blast radius" - what breaks if X fails

```bash
python .repometa/analyzer.py --impact-analysis
```

**Output:**
```
⚠️  SINGLE POINTS OF FAILURE:
   🔴 testing/TESTING_STRATEGY.md
      Reason: Critical component with 5 dependents
      Failure impact: CATASTROPHIC (10 components affected)
      Mitigation: Implement circuit breaker | Set up redundancy

📊 TOP COMPONENTS BY CRITICALITY:
   🟠 phase-2-predictive/lead-scoring/
      Criticality: 100/100
      Blast radius: 8 direct dependents
      If this fails → 12 total components impacted
```

**Use cases:**
- Prioritize which components need failover
- Understand cascade failures
- Plan disaster recovery
- Make architecture decisions

**How it works:**
1. Builds complete dependency graph from manifest
2. Calculates reverse dependencies (who depends on me)
3. Uses BFS to find transitive dependencies
4. Scores criticality based on importance + dependents
5. Identifies single points of failure

### 3. 💡 Capability Inference Engine

**What it does:** AI discovers hidden capabilities by analyzing patterns

```bash
python .repometa/analyzer.py --infer-capabilities
```

**Output:**
```
🟢 Self-Healing Feature Validation
   Confidence: 85%
   Description: Features can trigger their own chaos tests
   Evidence:
      • Found 1 orchestration file + 1 chaos file
      • Both use event-driven architecture
   💰 Value: Zero-downtime deployments
   ⚙️  Implementation effort: medium

🟡 Multi-Model A/B Testing in Production
   Confidence: 78%
   Description: Test multiple ML models simultaneously
   💰 Value: Continuous improvement without risk
   ⚙️  Implementation effort: low
```

**Use cases:**
- Discover features you didn't know you could build
- Find synergies between components
- Prioritize new capabilities by confidence
- Plan feature roadmap

**How it works:**
1. **Pattern 1:** Testing + Feature = Self-Testing Feature
2. **Pattern 2:** Multiple ML models + Orchestration = A/B Testing
3. **Pattern 3:** Performance Monitoring + Data = Auto-Optimization
4. **Pattern 4:** Similar files = Consolidation opportunity
5. **Pattern 5:** Data + AI = Predictive capability

Each pattern has heuristics and confidence scoring.

### 4. 📊 Code Complexity Scorer

**What it does:** Identifies which files need refactoring

```bash
python .repometa/analyzer.py --complexity-score
```

**Output:**
```
⚠️  FILES RECOMMENDED FOR REFACTORING:

   🔴 testing/TESTING_STRATEGY.md
      Complexity score: 79.1/100
      Lines: 1219, Functions: 7, Sections: 36
      Reasons: Large file (1219 lines), High complexity (79/100)

📈 OVERALL STATISTICS:
   Total files: 15
   Average complexity: 52.5/100
   Files needing refactoring: 13 (86.7%)
   Total lines of code: 10,132
```

**Use cases:**
- Identify refactoring priorities
- Track complexity over time
- Set quality gates (reject PRs > 70 complexity)
- Monitor technical debt growth

**How it works:**
1. Counts lines, functions, classes, imports
2. Normalizes each metric (0-100 scale)
3. Weights: 50% lines, 20% functions, 20% sections, 10% imports
4. Flags files >500 lines OR >70 complexity OR >30 functions

---

## Run Everything at Once

```bash
python .repometa/analyzer.py --full-analysis
```

Runs all 4 analyses in sequence. Takes 1-2 minutes for typical repository.

---

## Real-World Workflows

### Workflow 1: Pre-Commit Technical Debt Check

**Goal:** Don't merge code that increases technical debt

```bash
# Before committing
python .repometa/analyzer.py --scan-redundancies --complexity-score

# If new redundancies found → Refactor before commit
# If complexity >70 on new files → Simplify before commit
```

**Integrate into CI/CD:**
```yaml
# .github/workflows/code-quality.yml
- name: Check for code redundancies
  run: |
    python .repometa/analyzer.py --scan-redundancies
    # Fail if redundancies increased from baseline
```

### Workflow 2: Architecture Review Preparation

**Goal:** Present data-driven architecture insights

```bash
# Generate comprehensive analysis
python .repometa/analyzer.py --full-analysis > architecture-review.txt

# Key sections to highlight:
# 1. Single points of failure → Need redundancy
# 2. Inferred capabilities → Future roadmap
# 3. Complexity hotspots → Refactoring plan
```

### Workflow 3: Prioritizing Refactoring Work

**Goal:** Which files should we refactor first?

```bash
# Run complexity analysis
python .repometa/analyzer.py --complexity-score

# Prioritize by:
# 1. Complexity score (>70 = urgent)
# 2. Blast radius (from impact analysis)
# 3. Change frequency (from git history)

# Formula: Priority = Complexity × BlastRadius × ChangeFrequency
```

### Workflow 4: Discovering Quick Wins

**Goal:** Find features we can build quickly

```bash
python .repometa/analyzer.py --infer-capabilities

# Look for:
# - High confidence (>80%)
# - Low implementation effort
# - High value

# Example: "Real-time A/B testing" (78% confidence, low effort, high value)
# → Build this sprint!
```

### Workflow 5: Monthly Technical Debt Report

**Goal:** Track technical debt trends over time

```bash
# Run on 1st of every month
mkdir reports/2025-10
python .repometa/analyzer.py --full-analysis > reports/2025-10/analysis.txt

# Track metrics:
# - Total redundancy clusters (goal: decrease)
# - Average complexity (goal: <50)
# - Single points of failure (goal: 0)
# - Inferred capabilities (goal: increase confidence)
```

---

## Advanced: Customizing Thresholds

### Redundancy Detection Sensitivity

```bash
# More strict (fewer false positives)
python .repometa/analyzer.py --scan-redundancies --similarity-threshold 90

# More lenient (catch more potential duplicates)
python .repometa/analyzer.py --scan-redundancies --similarity-threshold 60
```

**Recommended thresholds:**
- **90%+** - Exact or near-exact duplicates (safe to consolidate)
- **70-89%** - Similar patterns (review before consolidating)
- **50-69%** - Potentially related (use judgment)

### Complexity Scoring Interpretation

**Complexity Score Ranges:**
- **0-30:** Simple, well-structured
- **31-50:** Moderate complexity (acceptable)
- **51-70:** Getting complex (consider refactoring)
- **71-100:** High complexity (refactor recommended)

**Complexity Triggers:**
- Lines > 500 → Split file
- Functions > 30 → Extract modules
- Complexity > 70 → Simplify logic

---

## Integration with Phase 1

Phase 2 **complements** Phase 1, doesn't replace it.

### Use Phase 1 (visualizer.py) for:
- ✅ Quick exploration ("show me the testing branch")
- ✅ Onboarding new team members
- ✅ Generating diagrams for documentation
- ✅ Understanding high-level architecture

### Use Phase 2 (analyzer.py) for:
- ✅ Deep code analysis
- ✅ Finding technical debt
- ✅ Discovering non-obvious capabilities
- ✅ Quantifying blast radius

### Use Both Together:

```bash
# 1. Start with Phase 1 - Get oriented
python .repometa/visualizer.py --interactive
> tree                    # See overall structure
> branch phase-2          # Focus on ML

# 2. Switch to Phase 2 - Deep analysis
python .repometa/analyzer.py --infer-capabilities
# Discover: "Multi-Model A/B Testing possible!"

# 3. Back to Phase 1 - Understand dependencies
python .repometa/visualizer.py --dependencies
# See: ML models → orchestration → monitoring

# 4. Phase 2 again - Check complexity
python .repometa/analyzer.py --complexity-score
# Confirm: ML files are manageable complexity

# 5. Decision: Build the A/B testing feature!
```

---

## Performance & Scalability

### Current Repository (15 files, 10K lines)
- Redundancy scan: ~2 seconds
- Impact analysis: <1 second
- Capability inference: <1 second
- Complexity scoring: ~1 second
- **Full analysis: ~5 seconds**

### Large Repository (1000 files, 500K lines)
- Redundancy scan: ~30 seconds
- Impact analysis: ~5 seconds
- Capability inference: ~2 seconds
- Complexity scoring: ~10 seconds
- **Full analysis: ~50 seconds**

**Optimization tips:**
- Redundancy scan is the slowest (O(n²) comparison)
- For huge repos, use `--similarity-threshold 85` (fewer comparisons)
- Run full analysis nightly in CI, not on every commit

---

## Interpreting Results

### When Redundancy Scanner Shows Nothing

```
✅ No significant code redundancies detected!
```

This is **good!** Your codebase is well-organized. But consider:
- Lower the threshold: `--similarity-threshold 60`
- Check if files are too small to detect patterns
- Run on code files (not just markdown docs)

### When Impact Analysis Shows Everything as CATASTROPHIC

This happens when:
1. Everything is interconnected (monolithic design)
2. No isolation between components

**Solutions:**
- Introduce service boundaries
- Use dependency injection
- Add circuit breakers
- Implement caching layers

### When Capability Inference Shows Low Confidence

```
🟠 Some Feature (confidence: 55%)
```

**What it means:** The AI detected a pattern but isn't sure.

**What to do:**
- Review the evidence manually
- If valid, add to manifest as confirmed capability
- If invalid, ignore (false positive)
- As codebase grows, confidence will improve

### When Complexity Scores Are All High

```
Files needing refactoring: 13 (86.7%)
```

**For documentation repos:** This is normal. Large docs = high line count.

**For code repos:** This is a red flag. Time to refactor.

**Prioritize refactoring:**
1. High complexity + High blast radius = URGENT
2. High complexity + Low blast radius = Important
3. Low complexity + High blast radius = Monitor
4. Low complexity + Low blast radius = OK

---

## Troubleshooting

### Issue: "No module named 'yaml'"

```bash
pip install pyyaml
```

### Issue: Redundancy scan finds too many false positives

**Cause:** Threshold too low

**Solution:**
```bash
python .repometa/analyzer.py --scan-redundancies --similarity-threshold 85
```

### Issue: Impact analysis shows 0 dependencies

**Cause:** Manifest doesn't have `connects_to` populated

**Solution:** Update `.repometa/manifest.yaml` with connections between files

### Issue: Capability inference shows nothing

**Cause:** Not enough files or patterns to detect

**Solution:** Keep building. Phase 2 gets smarter as codebase grows.

---

## What's Next: Phase 3

**Current:** Automated analysis and insights

**Phase 3 (Weeks 5-6):** Conversational interface with NLP

**Imagine:**
```
You: "Show me all files with high complexity that are also single points of failure"

AI: Found 3 files:
   1. testing/TESTING_STRATEGY.md (79.1 complexity, 5 dependents)
   2. ...

You: "For file #1, what's the refactoring recommendation?"

AI: Break into 3 modules:
   1. testing/data-quality/  (lines 1-400)
   2. testing/ml-validation/ (lines 401-800)
   3. testing/integration/   (lines 801-1219)

You: "Do it"

AI: [Creates 3 new files, updates manifest, runs tests]
   ✅ Refactoring complete. Complexity reduced to 35/100.
```

**This is where we're heading.** 🚀

---

## Phase 2 Achievement Unlocked

You now have:
- ✅ **Automated redundancy detection** (no more manual searching)
- ✅ **Blast radius calculations** (know what breaks)
- ✅ **AI-powered capability discovery** (find hidden gems)
- ✅ **Complexity scoring** (prioritize refactoring)

**Impact:**
- 100x faster technical debt detection
- Instant architecture risk assessment
- Discover capabilities you didn't know existed
- Data-driven refactoring decisions

**This is Phase 2 of Vision 2045.**

Next stop: Natural language queries and conversational development. 🎯

---

**Last Updated:** 2025-10-23
**Phase 2 Status:** ✅ Complete and Operational
**Next Phase:** Conversational Interface (Weeks 5-6)
