# 📝 Changelog entry template 🐧

Copy this when adding a new build. **Every change needs a *why* and an *expected
benefit*** — a bare list of config symbols is not a changelog.

---

## The rules

1. **Newest first.** New entries go directly under "Current builds" in
   [CHANGELOG.md](../CHANGELOG.md).
2. **Both builds, or say which.** If a change lands in only one, say so explicitly.
3. **Root cause, not symptom.** For a 🐛 fix, record what was actually wrong.
4. **Expected ≠ measured.** Never write "improves battery by X%" without a
   measurement. Write the *mechanism* and label it as an expectation.
5. **Record declines too.** If something was evaluated and rejected, add it to
   [DISABLED.md](DISABLED.md) with the reason.
6. **Validate before building.** Run kconfiglib against the real tree; confirm
   every new symbol lands `=y` and no existing option regressed.
7. **Never hide a failure.** Add it to [BUILD-LEDGER.md](BUILD-LEDGER.md) with its
   post-mortem.
8. **No boot claims.** Compilation, config and symbols are provable in CI. Boot,
   performance and battery are not.

---

## Copy from here

```markdown
## [stable-NN] + [susfs-N] — YYYY-MM-DD

**Both builds.** Source: `<sha>` · PR #N
<n> new symbols, all validated `=y` before building.

### ✨ Added — <short name>

`CONFIG_X`, `CONFIG_Y`

- **Why:** <the problem this solves — what was missing or broken>
- **Expected benefit:** <the mechanism, phrased as an expectation>
- **Risk:** <low / medium / high, and what it could affect>
- 📊 **Verified:** <kconfiglib result, CI run, symbol check>

### 🐛 Fixed — <short name>

| | |
|---|---|
| **Symptom** | <what was observed> |
| **Root cause** | <what was actually wrong> |
| **Fix** | <what changed> |
| **Prevention** | <the check added so it cannot recur> |
| 📊 **Verified** | <proof> |

### 🔧 Changed — <build/verification/tooling>

- **What:** …
- **Why:** …
- **Benefit:** …

### ❌ Declined in this round

| Option | Reason |
|---|---|
| `CONFIG_…` | … |

### 📊 Verified

- <n>/<n> new symbols `=y`; <n> regressions across the existing <n>
- CI: stable **#NN** and SUSFS **#N** — success, **0 annotations**
```

---

## Checklist before merging

- [ ] kconfiglib: every new symbol `=y`, dependencies satisfied
- [ ] kconfiglib: **no regressions** in previously requested options
- [ ] String/numeric options verified too (not just `=y`) — this is how the BBR bug hid
- [ ] Both workflows updated if the change applies to both
- [ ] `DEBUG_FS`, thermal safeguards, `NFT_COMPAT` unchanged
- [ ] YAML parses
- [ ] `CHANGELOG.md` entry written with why + expected benefit
- [ ] `changelog/earth-stable-NN.md` / `earth-susfs-N.md` release page created
- [ ] `BUILD-LEDGER.md` updated (successes **and** failures)
- [ ] `DISABLED.md` updated if anything was declined
- [ ] Release links in `SUSFS_USAGE_GUIDE.md` and `FINAL_KERNEL_REPORT.md` updated
- [ ] User approved the build (workflow edits on `main` trigger CI automatically)

---

## After the build

- [ ] Both runs green, **0 annotations** — check annotations, not just the conclusion
- [ ] Release assets present: ZIP + `REVISIONS.txt` + `build-config.txt`
- [ ] ZIP sizes recorded in the changelog and release page
- [ ] Superseded releases removed (keep the tags for provenance)
- [ ] Docs point at the new tags
- [ ] Reminder kept: **compile success is not boot proof**

⬅️ [Back to changelog](../CHANGELOG.md)
