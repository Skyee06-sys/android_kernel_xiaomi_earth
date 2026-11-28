# 🏗️ Build Guide — earth Kernel

All compilation happens in **GitHub Actions**. No PC is required; a phone with
Termux and a browser is enough.

---

## 🧭 The two workflows

| | Stable | SUSFS experimental |
|---|---|---|
| File | `.github/workflows/blank.yml` | `.github/workflows/susfs.yml` |
| Trigger | push to `main` + manual | **manual only** (`workflow_dispatch`) |
| Ignored paths | `**.md`, `tools/**` | — |
| Output ZIP | `Earth-Lineage24-KSUNext.zip` | `Earth-Lineage24-KSUNext-SUSFS-EXPERIMENTAL.zip` |
| Release tag | `earth-stable-<run_number>` | `earth-susfs-<run_number>` |
| Release type | normal | **pre-release** |
| SUSFS | ❌ none | ✅ v1.5.5 |

🔒 **Isolation guarantee:** the SUSFS workflow is never triggered by a push, so
experimental code cannot silently enter a stable release.

---

## ▶️ Running a build from your phone

### Stable
Any push to `main` that touches the workflow or `scripts/` starts a build.
Doc-only and `tools/`-only changes do **not**.

To run manually: **Actions → Build earth Kernel … → Run workflow**.

### SUSFS experimental
**Actions → SUSFS experimental build → Run workflow.** It never runs on its own.

### With `gh` in Termux
```bash
gh workflow run blank.yml --ref main
gh workflow run susfs.yml --ref main
gh run list --limit 5
gh run watch <run-id>
```

> ⚠️ A brand-new workflow file returns **404** from `gh workflow run` until it
> exists on the default branch.

---

## 🔬 Pipeline stages

```
1. Install Dependencies      bc bison flex libssl-dev libelf-dev dwarves
                             zip python3 cpio wget git clang lld llvm
2. Clone & Patch Kernel      LineageOS earth @ lineage-24.0
                             KernelSU-Next @ legacy → drivers/kernelsu
                             path_umount backport into fs/namespace.c
                             [SUSFS only] scripts/port_susfs.py
                             append validated config to earth_defconfig
3. Setup GCC Binutils        aarch64 + arm GCC 4.9 prebuilts (binutils only)
4. Compile Kernel            make Image.gz-dtb, clang + lld, arm64
5. Verify                    image, AArch64, configs, string values, symbols
6. Package AnyKernel3        locked to earth / aether
7. Upload Artifact           actions/upload-artifact@v7
8. Validate artifacts        unzip -t, image, device lock, SHA256SUMS
9. Publish Release           gh release create (+ --prerelease for SUSFS/experimental)
```

### Compiler invocation
```
CC=clang  LD=ld.lld  AR=llvm-ar  NM=llvm-nm
OBJCOPY=llvm-objcopy  OBJDUMP=llvm-objdump  STRIP=llvm-strip
CLANG_TRIPLE=aarch64-linux-gnu-
CROSS_COMPILE=aarch64-linux-android-
CROSS_COMPILE_ARM32=arm-linux-androideabi-
KCFLAGS="-Wno-error"
```

`-Wno-error` is required: the MTK vendor tree emits many warnings and `-Werror`
would make the build impossible. ⚠️ Warning **counts are not yet reported** —
tracked as [KI-010](KNOWN_ISSUES.md) and scheduled for Phase B.

---

## ✅ What verification actually asserts

| Check | Fails the build? |
|---|---|
| `Image.gz-dtb` exists and is non-empty | ✅ |
| `out/vmlinux` is **AArch64** | ✅ |
| Every requested `=y` symbol is `=y` in `out/.config` | ✅ |
| Every requested **string/numeric** value matches | ✅ |
| `path_umount`, `ksu_handle_execveat`, `ksu_handle_faccessat`, `ksu_handle_vfs_read`, `ksu_handle_sys_reboot`, `wg_socket_init` in `System.map` | ✅ |
| SUSFS builds additionally: `susfs_init`, `susfs_is_current_ksu_domain`, `susfs_is_current_zygote_domain`, `ksu_try_umount`, `susfs_try_umount` | ✅ |
| ZIP contains `Image.gz-dtb` | ✅ |
| Device names are `earth` / `aether` | ✅ |

**String verification was added after the BBR bug**: the verifier previously
matched only `=y` lines, so `CONFIG_DEFAULT_TCP_CONG="bbr"` being silently
overridden by `DEFAULT_CUBIC` went unnoticed for several releases.

Verification is scoped to `/tmp/requested-config.txt` — only options we ask for.
Checking the whole defconfig produced false failures on stock symbols Kconfig
legitimately drops.

---

## 🧪 Validating config changes without compiling

This is how every option in this project was checked **before** building. It runs
in seconds and needs no toolchain.

```bash
pip install kconfiglib
# fetch the source tree (tarball is faster than a clone)
curl -L "https://codeload.github.com/LineageOS/android_kernel_xiaomi_earth/tar.gz/refs/heads/lineage-24.0" -o k.tgz
mkdir k && tar xzf k.tgz -C k --strip-components=1
cd k
cat arch/arm64/configs/earth_defconfig /path/to/your-options.txt > .config
CC=gcc ARCH=arm64 SRCARCH=arm64 KERNELVERSION=4.19.325 srctree=. \
  python3 -c "import kconfiglib; k=kconfiglib.Kconfig('Kconfig'); \
              k.load_config('.config'); k.write_config('resolved.config')"
grep -E '^CONFIG_(YOUR_OPTION)=' resolved.config
```

| Gotcha | Detail |
|---|---|
| **`CC` must be set** | Otherwise `scripts/Kconfig.include` fails its assembler probe |
| **clang-only symbols** | `LTO_CLANG`, `CFI_CLANG`, `SHADOW_CALL_STACK` resolve `n` under gcc; they need `CC_IS_CLANG && LD_IS_LLD` |
| **KSU symbols absent** | KernelSU-Next is cloned only in CI, so `KSU*` do not exist in a bare tree |
| **Promptless symbols** | e.g. `DEFAULT_TCP_CONG`, `NFT_FIB` — cannot be set directly; select their parent |
| **Hidden `select`s** | e.g. `ZSMALLOC_STAT` **selects `DEBUG_FS`**. Always diff the *whole* resolved config, not just your option |

**Recommended method:** resolve the baseline, then resolve baseline + one
candidate, and diff. That reveals side effects per feature. See
[KERNEL_CONFIG.md](KERNEL_CONFIG.md) for the observed results.

---

## 📦 Artifacts produced

| File | Contents |
|---|---|
| `Earth-Lineage24-KSUNext[-SUSFS-EXPERIMENTAL].zip` | AnyKernel3 flashable package |
| `REVISIONS.txt` | kernel/KSU SHAs, build UTC; SUSFS also records `susfs_version`, `susfs_remote`, `susfs_sha`, `sus_su` |
| `build-config.txt` | the complete `.config` actually built |
| `SHA256SUMS.txt` | SHA256 of the ZIP, REVISIONS and build-config |

Release assets are public — **no GitHub sign-in**. Actions artifacts require
sign-in and expire after 90 days, which is why releases are used for distribution.

---

## 🔧 Phase B hardening (implemented, awaiting first green run)

> **Status:** written and statically validated, **not yet confirmed by a
> successful build**. The first attempt (stable #23 / SUSFS #6 / experimental #1)
> failed at `Restore ccache` because the cache key was built from
> `github.workflow` — the display *name*, which contains commas — and
> `actions/cache` rejects commas. Now keyed by a fixed `CACHE_SLUG`.
> See [post-mortem 7](changelog/BUILD-LEDGER.md).

| Improvement | Detail |
|---|---|
| **Pinned clang** | `CLANG_VERSION='18'` (stable/SUSFS), `'16'` (experimental). Uses `clang-N`, `ld.lld-N`, `llvm-*-N`; falls back with a `::warning` if absent. Actual version recorded in `REVISIONS.txt`. |
| **Pinned GCC binutils** | LineageOS GitHub mirrors at fixed SHAs `5e030ea` / `111258a`, checked out detached and validated with `test -x` |
| **ccache** | `actions/cache@v5` (Node 24), keyed `ccache-<CACHE_SLUG>-clang<N>-<sha>` with prefix restore-keys. `CC="ccache …"`, `CCACHE_COMPILERCHECK=content`, `CCACHE_MAXSIZE=2G`, stats printed. **Keys must be comma-free** — hence the slug, not the workflow title. |
| **Timeout** | `timeout-minutes: 60` |
| **Concurrency** | per workflow+ref, `cancel-in-progress: true` |
| **Warning accounting** | total count + top `[-W…]` categories; `-Wno-error` retained because the vendor tree requires it |
| **Build duration** | measured, reported in summary and `REVISIONS.txt` |
| **Artifact validation** | `unzip -t` integrity, image present, **device lock asserted**, REVISIONS/config present — all fail the build |
| **Checksums** | `SHA256SUMS.txt` published as a release asset |
| **Job summary** | `$GITHUB_STEP_SUMMARY` tables for metrics and validation |

### Local source patches

CI applies source patches through asserting, idempotent scripts — never with a
blind `patch` call:

| Script | Applied to | Purpose |
|---|---|---|
| `scripts/port_susfs.py` | SUSFS build only | Port SUSFS v1.5.5 onto earth + KernelSU-Next legacy |
| `scripts/fix_skmsg_order.py` | **all three builds** | Restore upstream declaration order in `net/core/skmsg.c`, required by `CONFIG_BPF_STREAM_PARSER=y` |

Run the skmsg fix by hand against a checkout:

```bash
python3 scripts/fix_skmsg_order.py --kernel-dir kernel --check   # report only
python3 scripts/fix_skmsg_order.py --kernel-dir kernel           # apply + print diff
```

It is idempotent, asserts pure code motion, and exits non-zero if the tree does
not match the expected upstream body.

### The third workflow

| | Experimental |
|---|---|
| File | `.github/workflows/experimental.yml` |
| Trigger | **`workflow_dispatch` only — no `push` trigger at all** |
| Adds | `LTO_CLANG`, `THINLTO`, `CFI_CLANG`, `CFI_PERMISSIVE`, `SHADOW_CALL_STACK` |
| SUSFS | ❌ excluded, so an LTO failure cannot be confused with a SUSFS failure |
| Compiler | pinned **clang-16** (better matched to the 4.19 LTO backport) |
| Tag | `earth-experimental-<n>`, **pre-release** |

---

### Static checks to run before dispatching a workflow change

A CI edit deserves the same review as a kernel edit. These are free; a failed
17-minute runner is not.

```bash
# YAML parses, and the triggers are what you expect
python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/blank.yml')); print(d[True])"

# every run: block is valid bash, every embedded verifier is valid python
python3 - <<'EOF'
import yaml, re, subprocess, textwrap
d = yaml.safe_load(open('.github/workflows/blank.yml'))
for st in d['jobs']['build']['steps']:
    if 'run' not in st: continue
    s = re.sub(r'\$\{\{[^}]*\}\}', 'GHEXPR', st['run'])
    subprocess.run(['bash','-n'], input=s, text=True, check=True)
    for m in re.finditer(r"<< 'PYEOF'\n(.*?)\n\s*PYEOF", s, re.S):
        compile(textwrap.dedent(m.group(1)), '<verifier>', 'exec')
print('OK')
EOF
```

Also remember: **cache keys may not contain commas**, and `github.workflow` is
the workflow's title, not its filename.

---

## 🩺 When a build fails

The workflow extracts real compiler diagnostics into GitHub annotations:
`error:`, `fatal error`, `undefined symbol`, `undefined reference`,
`duplicate symbol`, `No rule to make target`, plus the log tail.

**Procedure:** read the annotation → find the root cause → fix the cause → add a
check so it cannot recur → rebuild. Never retry blindly and never hide the error.

Historical post-mortems: [changelog/BUILD-LEDGER.md](changelog/BUILD-LEDGER.md).

---

## 🔗 Related

[KERNEL_CONFIG.md](KERNEL_CONFIG.md) · [CONTRIBUTING.md](CONTRIBUTING.md) · [changelog/BUILD-LEDGER.md](changelog/BUILD-LEDGER.md)
