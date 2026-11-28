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
| **#22** | 46137709296 | ✅ | `2fc7655` | Traffic control + proxy/firewall + monitoring; **BBR default fixed** |
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
| **#5** | 46137717612 | ✅ | `2fc7655` | Same features as stable-22 + SUSFS v1.5.5 |
| #4 | 46123981627 | ✅ | `050caac` | `REVISIONS.txt` now records `susfs_version` |
| #3 | 46122026185 | ✅ | `f4a33c3` | First SUSFS build published to Releases |
| #2 | 46120198847 | ✅ | `540356a` | **First working SUSFS build** — 16m35s, 0 annotations |
| #1 | 46118020502 | ❌ | `f2b6c46` | Link failure: undefined `susfs_try_umount_all` |

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
