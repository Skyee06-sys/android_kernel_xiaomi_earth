# 🤝 Contributing — earth Kernel

Engineering rules for this repository. They exist because every one of them
corresponds to a mistake that actually happened here.

---

## 🥇 The ultimate rule

> **Every kernel change must ship its documentation updates in the same commit.**

A feature is not merged until its docs are accurate. If you cannot document it
truthfully, it is not ready.

### Files to synchronise

| File | Update when |
|---|---|
| [CHANGELOG.md](CHANGELOG.md) | **Always** — what, why, expected benefit, risk, verification |
| [FEATURES.md](FEATURES.md) | Any feature added / changed / removed / re-statused |
| [KERNEL_CONFIG.md](KERNEL_CONFIG.md) | Any config change — with **before/after** values |
| [README.md](README.md) | Downloads, highlights, build links change |
| [SECURITY.md](SECURITY.md) | Hardening or root behaviour changes |
| [PERFORMANCE.md](PERFORMANCE.md) | A mechanism or measurement method changes |
| [COMPATIBILITY.md](COMPATIBILITY.md) | Device/ROM/component compatibility changes |
| [INSTALLATION.md](INSTALLATION.md) | Flash procedure or partition targets change |
| [BUILD_GUIDE.md](BUILD_GUIDE.md) | Workflow, toolchain or verification changes |
| [KNOWN_ISSUES.md](KNOWN_ISSUES.md) | New limitation, or an issue fixed |
| [SUSFS_USAGE_GUIDE.md](SUSFS_USAGE_GUIDE.md) | SUSFS version, options or module behaviour changes |
| [changelog/BUILD-LEDGER.md](changelog/BUILD-LEDGER.md) | **Every** build — successes *and* failures |
| [changelog/DISABLED.md](changelog/DISABLED.md) | Anything evaluated and declined |
| `changelog/earth-*.md` | Each new release gets its own page |

Use [changelog/TEMPLATE.md](changelog/TEMPLATE.md) — it has the entry format and
the pre-merge / post-build checklists.

---

## 🏷️ Status vocabulary — use it exactly

| Status | Meaning |
|---|---|
| **Enabled** | `=y` in the final `.config` **and** implementing source present |
| **Implemented** | Code present and linked; needs userspace/runtime config to act |
| **Available-but-disabled** | Source exists, config `n`, reason recorded |
| **Experimental** | Isolated experimental build only |
| **Planned** | Approved for investigation, in **no** build yet |
| **Unsupported** | Cannot work here — with evidence |

Never write "supported" for something merely configured.

---

## 🔬 Evidence requirements

1. **Source-code evidence for every feature.** Cite a real path (and line where
   useful). Example: `mm/Kconfig:617` for `ZSMALLOC_STAT select DEBUG_FS`.
2. **Before/after for every config change.** Stock value → built value.
3. **Side-effect diff, per candidate.** Resolve the baseline, then baseline + one
   option, and diff the *whole* config. Hidden `select`s are the main trap.
4. **Regression review for every patch.** Confirm previously requested options
   still resolve, and that nothing working was removed.
5. **Accurate feature manifest per release.**
6. **Artifact validation on every successful build.**

### Validating without compiling
See [BUILD_GUIDE.md](BUILD_GUIDE.md#-validating-config-changes-without-compiling).
kconfiglib resolves in seconds. `CC` must be set. Remember clang-only symbols
(`LTO_CLANG`, `CFI_CLANG`, `SHADOW_CALL_STACK`) resolve `n` under gcc.

---

## 🚫 Hard prohibitions

| Never | Because |
|---|---|
| Invent a feature or claim an unverified improvement | Credibility is the product |
| Claim performance gains without measurement | No measurement has been done here |
| Assume compilation proves it works | Compile ≠ boot ≠ good |
| Hide a build error or retry blindly | Root cause first, always |
| Ignore warnings that indicate real problems | Report counts even when `-Wno-error` is required |
| Remove working functionality without justification | Preserve what works |
| Touch unrelated files | Keep changes reviewable and reversible |
| Let docs go stale | The ultimate rule |
| Let experimental code reach stable silently | SUSFS workflow is manual-only for this reason |
| Disable thermal safeguards | Never, for any performance reason |
| Pin max CPU/GPU frequency or overclock the GPU | Stability over benchmarks |
| Cherry-pick newer-kernel code blindly | Resolve API differences properly |

---

## 🌿 Branch and workflow discipline

- Work on the **current session branch**; commit and push only to it.
- Open a pull request into `main`; do not push directly to `main`.
- After a squash merge, `main` and the branch diverge. Reconcile by merging
  `origin/main` into the branch, **verifying no content is lost**, then re-merge.
- ⚠️ **Pushing a workflow change to `main` triggers a build.** Get approval before
  merging workflow edits. Doc-only (`**.md`) and `tools/**` changes do not build.
- Never force-push without first diffing against the remote — a stale local
  checkout can otherwise delete files.

### Commit messages
Explain **why**, not just what. For a fix, include the root cause and the check
added to prevent recurrence. Reference the build/run number when relevant.

---

## 🧪 Experimental work

- Isolated workflow, `workflow_dispatch` only, published as a **pre-release**.
- Test independently; **revert on failure**.
- Never merge into the stable build until it passes boot and runtime testing.
- Current experimental candidates: `LTO_CLANG` + `CFI_CLANG`,
  `SHADOW_CALL_STACK`, `BLK_WBT`, `F2FS_FS_COMPRESSION`, `FUNCTION_TRACER`,
  `TRANSPARENT_HUGEPAGE` (only with `MADVISE`), `CPU_THERMAL`, `PM_AUTOSLEEP`.

> ℹ️ This session tracks a single fixed branch, so experimental isolation is
> implemented as a **separate workflow and pre-release**, not a separate git
> branch. The isolation guarantee is identical: experimental code cannot enter a
> stable build.

---

## 🐞 Reporting bugs

Include: build tag, `uname -r`, `getprop ro.vendor.build.fingerprint`, output of
`sh tools/verify_device.sh`, relevant `dmesg`, and expected vs actual behaviour.
See [KNOWN_ISSUES.md](KNOWN_ISSUES.md) first — it may already be documented.

## 🛡️ Reporting security issues

Do **not** publish a working exploit. Describe impact, affected build tag, and
reproduction conditions. Note that root is granted by design and SUSFS hiding is
not a security boundary — see [SECURITY.md](SECURITY.md).

---

## 📋 Pull-request checklist

- [ ] Technical justification written for every change
- [ ] Source-code evidence cited
- [ ] kconfiglib: new options resolve as intended
- [ ] kconfiglib: **no regressions** in previously requested options
- [ ] Per-candidate side-effect diff reviewed
- [ ] String/numeric values verified, not just `=y`
- [ ] Both workflows updated if the change applies to both
- [ ] `DEBUG_FS`, thermal safeguards, `NFT_COMPAT` unchanged
- [ ] YAML parses
- [ ] **All affected docs updated in this same commit**
- [ ] Changelog entry with why + expected benefit + risk + verification
- [ ] Build ledger updated
- [ ] User approval obtained before any build is triggered

---

## 🔗 Related

[changelog/TEMPLATE.md](changelog/TEMPLATE.md) · [BUILD_GUIDE.md](BUILD_GUIDE.md) · [KERNEL_CONFIG.md](KERNEL_CONFIG.md) · [CHANGELOG.md](CHANGELOG.md)
