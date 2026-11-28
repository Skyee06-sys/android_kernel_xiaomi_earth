# 🏗️ Build ledger 🐧

Every CI run, **including the failures** — because the root causes are the most
useful part of this project's history.

![Stable](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/actions/workflows/blank.yml/badge.svg)

> Failures are never hidden. Each one below records the symptom, the real root
> cause, and the fix — not just "retry until green".

---

## ✅ Currently published

| Build | Tag | Run ID | Result | ZIP |
|---|---|---|---|---|
| Stable | `earth-stable-22` | [46137709296](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/actions/runs/46137709296) | ✅ success · 0 annotations | 17,295,388 B |
| SUSFS | `earth-susfs-5` | [46137717612](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/actions/runs/46137717612) | ✅ success · 0 annotations | 17,305,967 B |

---

##  Stable workflow (`blank.yml`)

Runs GitHub still retains:

| Run | ID | Result | Source | What it was |
|:---:|---|:---:|---|---|
| **#24** | 46176922148 | ❌ | `9c1428b` | Cache fixed — reached the compiler (~20 min). **Real in-tree defect:** `net/core/skmsg.c` calls `sk_psock_from_strp()` before defining it. Exposed by C2's `BPF_STREAM_PARSER=y`. |
| #23 | 46176374866 | ❌ | `6e5501a` | Phase B/C1/C2 — **failed at `Restore ccache`**: cache key contained commas. Never reached the compiler. |
| #22 | 46137709296 | ✅ | `2fc7655` | Traffic control + proxy/firewall + monitoring; **BBR default fixed** |
| #20 | 46128068561 | ✅ | `4d6c7ee` | Post-cleanup rebuild; `tools/` added, doc/tool trigger filter |
| #19 | 46126184460 | ✅ | `db5b925` | SUSFS usage guide + version recording |
| #18 | 46122056735 | ✅ | `a854381` | First build publishing to **Releases** |
| #17 | 46121603337 | ✅ | `90d089e` | After SUSFS port merged to main |
| #16 | 46118010781 | ✅ | `cdd1b1c` | Tier A + real verification |
| #15 | 46116681955 | ✅ | `794a4b7` | First fully clean Tier A build |
| #12 | 46111066184 | ✅ | `13e8442` | `upload-artifact` v7 on main |
| #11 | 46109516160 | ✅ | `46b0daa` | `upload-artifact` v4 → v7 |

### Earlier runs (no longer retained by GitHub Actions)

Recorded from the project log so the history stays complete:

| Run | Result | Root cause / note |
|:---:|:---:|---|
| #21 | ️ **cancelled** | Triggered by a workflow edit that had not been authorised; cancelled on request. No release published. |
| #14 | ❌ failure | Compiled fine, **verifier false-failed** — it checked the whole defconfig including stock entries Kconfig legitimately drops. Fixed by scoping to `/tmp/requested-config.txt`. |
| #13 | ❌ failure | `fs/nfs/client.c:625` sets `rpc_clnt.cl_softerr`, which does not exist in this tree's `sunrpc/clnt.h`. **NFS/NFSD disabled**, not patched around. |
| #10 | ✅ success | WireGuard fix on main |
| #9 | ✅ success | First build after removing the duplicate WireGuard copy |
| #3 | ✅ success | First build with the `path_umount` backport |
| #4–#8 | ❌ failures | The WireGuard debugging chain — see below |

---

## 🧪 SUSFS workflow (`susfs.yml`)

Manual-only. Never runs on push.

| Run | ID | Result | Source | What it was |
|:---:|---|:---:|---|---|
| **#7** | 46176930512 | ❌ | `9c1428b` | Same `skmsg.c` compile error as stable #24. |
| #6 | 46176386174 | ❌ | `6e5501a` | Phase B/C1/C2 — same comma-in-cache-key failure at `Restore ccache`. |
| #5 | 46137717612 | ✅ | `2fc7655` | Same features as stable-22 + SUSFS v1.5.5 |
| #4 | 46123981627 | ✅ | `050caac` | `REVISIONS.txt` now records `susfs_version` |
| #3 | 46122026185 | ✅ | `f4a33c3` | First SUSFS build published to Releases |
| #2 | 46120198847 | ✅ | `540356a` | **First working SUSFS build** — 16m35s, 0 annotations |
| #1 | 46118020502 | ❌ | `f2b6c46` | Link failure: undefined `susfs_try_umount_all` |

---

## 🧬 Experimental workflow (`experimental.yml`) — LTO + CFI + SCS

Manual-only, pre-release. **SUSFS deliberately excluded.** Isolated so an LTO
failure can never be mistaken for a SUSFS failure, and so experimental options
can never reach a stable release by accident.

| Run | ID | Result | Source | What it was |
|:---:|---|:---:|---|---|
| **#2** | 46176932686 | ❌ | `9c1428b` | Same `skmsg.c` compile error. **LTO still untested** — the build died in `net/core`, before the LTO link stage. |
| #1 | 46176388608 | ❌ | `6e5501a` | First dispatch — failed at `Restore ccache` (comma in key), **before** any LTO code was compiled. LTO itself is still untested. |

> ⚠️ **Neither run #1 nor #2 says anything about whether LTO works on this
> tree.** #1 died in the cache step; #2 died compiling `net/core/skmsg.c`, long
> before the LTO link stage. The LTO question remains open.

---

## 🔍 Failure post-mortems

### 1. `path_umount` undefined — no kernel image at all

| | |
|---|---|
| **Symptom** | `vmlinux` link failed: undefined `path_umount` |
| **Root cause** | KernelSU-Next calls it when `KSU_HAS_PATH_UMOUNT` is set, but `path_umount()` is a **Linux 5.9** API absent from 4.19 |
| **Fix** | Backported the upstream 5.9 implementation into `fs/namespace.c` |
| **Prevention** | `path_umount` is now a required symbol in the Verify step |

### 2. WireGuard built twice — five failed runs

| | |
|---|---|
| **Symptom** | Duplicate `wg_*` symbols at link |
| **Wrong turns** | compat-layer guards, keeping `selftest/`, Makefile layout changes — all treated symptoms |
| **Root cause** | earth **already ships WireGuard v1.0.0 in-tree** at `drivers/net/wireguard`; adding `wireguard-linux-compat` compiled it a second time |
| **Fix** | Deleted the compat step entirely; just `CONFIG_WIREGUARD=y` |
| **Rule** | 🚫 Never re-add `wireguard-linux-compat` to this tree |

### 3. NFS — latent tree bug

| | |
|---|---|
| **Symptom** | `fs/nfs/client.o` fails to compile |
| **Root cause** | `client.c` sets `rpc_clnt.cl_softerr`; this tree's `include/linux/sunrpc/clnt.h` has no such member. Never exposed before because NFS is off in the stock defconfig. |
| **Decision** | ❌ Keep `NFS_FS`/`V3`/`V4`/`NFSD` **off** in both builds |
| **Why not fix** | A correct fix needs a SUNRPC backport — invasive, out of scope for stability-first |

### 4. Verifier false failures

| | |
|---|---|
| **Symptom** | Build compiled, verification failed |
| **Root cause** | Checked the entire defconfig, including stock symbols Kconfig drops: `EXFAT_DISCARD`, `CUSTOM_KERNEL_SAR`, `MTK_AB_OTA_UPDATER`, `SHADOW_CALL_STACK`, `CFI_CLANG`, `LTO_CLANG` |
| **Fix** | Verify only what we request (`/tmp/requested-config.txt`) |

### 5. SUSFS API name mismatch

| | |
|---|---|
| **Symptom** | Undefined `susfs_try_umount_all` from `fs/namespace.c:3925` |
| **Root cause** | The 4.19 patch calls `susfs_try_umount_all(uid)`; SUSFS **v1.5.5** defines `susfs_try_umount(target_uid)` |
| **Fix** | `reconcile_api()` rewrites the extern and call site |
| **Prevention** | `check_symbols()` resolves all SUSFS/KSU symbols locally before CI — **27/27** |
| **Rejected alternatives** | `W-Nana` mirror (329 B, invalid); `TheNoxS1d` v1.5.12 (no `_all`, no `vfs_create_mount`) |

### 6. BBR silently not the default — the quietest bug

| | |
|---|---|
| **Symptom** | None. Every build was green. |
| **Root cause** | `CONFIG_DEFAULT_TCP_CONG` is a **promptless string** derived from a Kconfig choice; assigning it in defconfig is discarded, so `DEFAULT_CUBIC` won |
| **Why it hid** | The verifier matched only `^CONFIG_…=y$` and ignored string values entirely |
| **Fix** | Select `CONFIG_DEFAULT_BBR=y` |
| **Prevention** | Verifier now checks string/numeric options; negative-tested to fail on `"cubic"` |
| **Lesson** | A green build is not proof a setting took effect. Verify **values**, not just presence. |

---

### 7. Commas in a cache key — all three workflows died before compiling

**Symptom.** Stable #23, SUSFS #6 and experimental #1 all failed within seconds,
at the same step: `Restore ccache`. No compiler output at all.

**Real root cause.** The Phase B cache key was built from `github.workflow`,
which is the workflow's **display name**, not its filename. All three display
names contain commas:

```
Build earth Kernel (LineageOS 24.0 + KernelSU-Next, stable)
SUSFS experimental build (isolated, manual only)
EXPERIMENTAL earth Kernel (LTO + CFI + SCS, isolated, manual only)
```

`actions/cache` rejects commas outright:

```
Key Validation Error: ccache-Build earth Kernel (LineageOS 24.0 + KernelSU-Next,
stable)-18-6e5501a... cannot contain commas.
```

**Fix.** A fixed, comma-free `CACHE_SLUG` env var per workflow (`stable`,
`susfs`, `experimental`) now keys the cache. This is also *better* than the
display name: renaming a workflow no longer invalidates its cache.

**Caught in the same pass, before rebuilding:**

| Issue | Why it mattered | Fix |
|---|---|---|
| `actions/cache@v4` targets Node 20 | Runner emitted a deprecation warning and force-ran it on Node 24 | Bumped to `@v5` (native `node24`) |
| `WARN_COUNT=$(grep -c … \|\| echo 0)` | `grep -c` prints `0` **and** exits 1, so the fallback appended a second `0`, producing `0\n0` and an "integer expression expected" error on a warning-free build | `\|\| true` plus a `${VAR:-0}` default |
| Symbol probe still listed `nfs_init_sbi` | NFS is deliberately disabled (KI-002), so the probe printed a misleading note | Replaced with source-verified C1/C2 symbols: `fortify_panic`, `sk_psock_init`, `blk_throtl_init`, `blk_iolatency_init`, `nf_conntrack_timeout_init` |
| Release notes omitted the new features | A release must carry an accurate feature manifest | Notes now list C1/C2, state what is **excluded**, and point at `SHA256SUMS.txt` |

**Lesson.** A CI change needs the same review as a kernel change. Before
re-dispatching, every `run:` block in all three workflows was checked with
`bash -n` and every embedded Python verifier with `compile()` — 24 shell blocks,
0 failures. Static checks are free; a failed 17-minute runner is not.

---

### 8. `sk_psock_from_strp()` used before it is declared — a real vendor bug

**Symptom.** Stable #24, SUSFS #7 and experimental #2 all compiled for ~20
minutes and then failed on the same translation unit:

```
../net/core/skmsg.c:791:27: error: implicit declaration of function
    'sk_psock_from_strp' [-Werror,-Wimplicit-function-declaration]
../net/core/skmsg.c:791:19: error: incompatible integer to pointer conversion
    initializing 'struct sk_psock *' with an expression of type 'int'
../net/core/skmsg.c:812:25: error: static declaration of 'sk_psock_from_strp'
    follows non-static declaration
make[3]: *** [../scripts/Makefile.build:333: net/core/skmsg.o] Error 1
```

**Real root cause.** The LineageOS 4.19.325 tree carries a mis-ordered backport:

| | Line |
|---|---|
| `sk_psock_strp_read()` — the caller | 789 |
| `sk_psock_from_strp(strp)` — the call | **791** |
| `sk_psock_from_strp()` — the definition | **812** |

There is no forward declaration. GCC accepted this as an implicit declaration
plus an int→pointer warning; clang treats it as a hard error, and plain
`-Wno-error` does not undo clang's *default-error* diagnostics.

**Why it never showed up before.** The entire block lives inside
`#if IS_ENABLED(CONFIG_BPF_STREAM_PARSER)`. The stock `earth_defconfig` leaves
that off, so the code is **never compiled**. Phase C2 turning it on is what
exposed a bug that was already there. The configuration did not create the bug.

**Evidence that this is the vendor's bug, not ours.** Upstream
`torvalds/linux` **v5.4** `net/core/skmsg.c`:

| | Line |
|---|---|
| `sk_psock_from_strp()` definition | **681** |
| `sk_psock_strp_read()` | 741 |
| calls | 743, 766 |

Upstream defines it **first**. The function body in the earth tree is
**byte-identical** to upstream v5.4. Tellingly, the backport author *did* add a
forward declaration for `sk_psock_done_strp` (L574) — they just missed this one.

**Fix.** `scripts/fix_skmsg_order.py` moves the definition above its first
caller, restoring upstream ordering. Applied as its own visible CI step in all
three workflows.

**Regression review — asserted, not assumed:**

| Check | Result |
|---|---|
| Line multiset unchanged (pure code motion) | ✅ |
| Byte length unchanged | ✅ |
| Brace balance unchanged | ✅ |
| Definition stays in the same `#if` region | ✅ |
| Text outside the region unchanged | ✅ |
| `BPF_STREAM_PARSER=n` preprocessed output identical | ✅ independently verified |
| Definition precedes every call afterwards | ✅ L789 < L799, L822 |
| Idempotent | ✅ second run is a no-op |
| Tampered body → loud failure | ✅ exit 1 |

**Before rebuilding, the whole class was swept.** A use-before-declaration scan
(with comment/string/preprocessor stripping and a paren matcher to tell calls
from prototypes) across every translation unit C1/C2 newly enables —
`skmsg.c`, `tls_main.c`, `tls_sw.c`, `blk-throttle.c`, `blk-iolatency.c`,
`nf_conntrack_timeout.c`, `page_idle.c`, `udp_diag.c`, `raw_diag.c`,
`packet/diag.c`, `netprio_cgroup.c`, `slub.c`, `string.c`, `usercopy.c`,
`slab_common.c` — found **exactly one** real instance: this one.

False positives were checked by hand rather than dismissed:
`sk_psock_done_strp` has a real prototype at L574; `sysfs_slab_add` and
`__fanout_unlink` have prototypes next to preprocessor lines;
`packet_sock_flag` is a `static inline` in `net/packet/internal.h`, which
`diag.c` includes; `raw_get_hashinfo` is local to `raw_diag.c`;
`tls_device.c` is not built at all because `TLS_DEVICE=n`.

**Lesson.** "It compiled before" is not evidence of correctness — it can just
mean the code was preprocessed away. Enabling a subsystem is a *test* of that
subsystem, and a latent vendor bug is a legitimate, expected outcome.

---

## 🧰 Environment lessons

| Problem | Reality |
|---|---|
| Actions artifacts as download links | Require GitHub **sign-in**, expire in 90 days → publish to **Releases** instead |
| Sandbox binary downloads | Artifact ZIPs, CI job logs and release assets return **302 / 0 B** → record facts into `REVISIONS.txt` at build time |
| New workflow dispatch | `gh workflow run <new>.yml` returns **404** until the file exists on the default branch |
| Local compilation | Not possible in the sandbox (no clang/lld/cross-gcc) → all builds run in GitHub Actions |
| Config validation | kconfiglib needs `CC=gcc` set, otherwise `scripts/Kconfig.include` fails the assembler probe |

---

## 📈 Pattern worth keeping

Every failure above was fixed by finding the **actual root cause**, then adding a
check so the same class of bug cannot recur:

- `path_umount` → required-symbol check
- SUSFS API drift → `check_symbols()` before CI
- verifier noise → scope to requested options
- BBR string → value-aware verification

⬅️ [Back to changelog](../CHANGELOG.md)
