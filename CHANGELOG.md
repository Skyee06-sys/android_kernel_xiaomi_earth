# 📋 Changelog — earth Kernel 🐧

Every change to the **stable** and **SUSFS experimental** kernels, with **why** it
was made and **what it should improve**. Newest first.

[![Stable build](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/actions/workflows/blank.yml/badge.svg)](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/actions/workflows/blank.yml)
![Kernel](https://img.shields.io/badge/kernel-4.19.325-blue)
![Device](https://img.shields.io/badge/device-earth%20%7C%20aether-orange)
![SUSFS](https://img.shields.io/badge/SUSFS-v1.5.5-purple)

> ⚠️ **Honesty rule.** "Expected benefit" is a *reasoned expectation*, not a
> measurement. CI proves compilation, configuration and linked symbols. It does
> **not** prove boot, performance or battery life. Nothing here is flashed
> automatically.

---

## 🏷️ Legend
| Icon | Meaning |
|:---:|---|
| ✨ | **Added** — new capability |
| 🐛 | **Fixed** — a real defect, with root cause |
| 🔧 | **Changed** — build/verification/tooling improvement |
| 📚 | **Docs** — documentation only, no kernel change |
| ❌ | **Disabled / declined** — with the reason |
| 📊 | **Verified** — what was actually proven |

**Two builds, always separate:**

| | Stable | SUSFS experimental |
|---|---|---|
| Workflow | `blank.yml` | `susfs.yml` |
| ZIP | `Earth-Lineage24-KSUNext.zip` | `Earth-Lineage24-KSUNext-SUSFS-EXPERIMENTAL.zip` |
| Tag | `earth-stable-<n>` | `earth-susfs-<n>` |
| SUSFS | ❌ none | ✅ v1.5.5 |
| Release type | normal | **pre-release** |
| Trigger | auto on `main` | **manual only** |

---

## 🚀 Current builds

| Build | Tag | Run | ZIP size | Status |
|---|---|---|---|---|
| **Stable** | [`earth-stable-22`](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/tag/earth-stable-22) | [#22](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/actions/runs/46137709296) | 17,295,388 B | ✅ success, 0 annotations |
| **SUSFS** | [`earth-susfs-5`](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/tag/earth-susfs-5) | [#5](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/actions/runs/46137717612) | 17,305,967 B | ✅ success, 0 annotations |

📖 Deep dives: [stable-22](changelog/earth-stable-22.md) · [susfs-5](changelog/earth-susfs-5.md)

---

## [stable-22] + [susfs-5] — 2026-11-28

**Both builds.** Source: `2fc7655` · PR [#12](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/pull/12)
30 new symbols, all validated `=y` before building.

### 🐛 Fixed — BBR was never actually the default

| | |
|---|---|
| **What** | Added `CONFIG_DEFAULT_BBR=y` |
| **Root cause** | `CONFIG_DEFAULT_TCP_CONG` is a **promptless string** derived from the "Default TCP congestion control" Kconfig *choice*. Assigning it in defconfig is silently discarded, so the choice default `DEFAULT_CUBIC` won. |
| **Impact** | Every release before this one ran **cubic** while the docs claimed bbr. |
| **Expected benefit** | BBR's bottleneck-bandwidth/RTT model generally gives lower queueing latency and better throughput on lossy mobile links than loss-based cubic. |
| **Risk** | Low — BBR v1 was already compiled in; only the default selection changes. |
| 📊 **Verified** | kconfiglib: `DEFAULT_BBR=y`, `DEFAULT_CUBIC=n`, `DEFAULT_TCP_CONG="bbr"`. Confirmed again by CI in the final `.config` for **both** builds. |

Check on device: `cat /proc/sys/net/ipv4/tcp_congestion_control` → should say `bbr`.
On `earth-stable-20` or older it will say `cubic` — that is this bug, not your setup.

### ✨ Added — traffic-control classifiers and actions

`NET_CLS`, `NET_CLS_ACT`, `NET_CLS_U32`, `NET_CLS_FLOWER`, `NET_CLS_CGROUP`,
`NET_ACT_POLICE`, `NET_ACT_MIRRED`

- **Why:** Tier A had added qdiscs (CAKE, FQ_CODEL, PIE, CoDel…) but **no
  classifiers or actions**. A qdisc could be attached but not *fed* — `tc` could
  not sort traffic into classes or police it. The feature was half-usable.
- **Expected benefit:** real, usable shaping. CAKE/FQ_CODEL can now actually
  isolate a game's traffic from a background download, which is the mechanism
  that reduces latency spikes under load.
- **Risk:** low. Additive; nothing changes until you add a `tc` rule.

### ✨ Added — transparent proxy and per-app firewall

| Config | Enables |
|---|---|
| `NFT_TPROXY`, `NETFILTER_XT_TARGET_TPROXY`, `NETFILTER_XT_MATCH_SOCKET` | Transparent proxying (Clash, v2ray, SagerNet) without per-app VPN mode |
| `NETFILTER_XT_MATCH_OWNER` | **uid-based per-app firewall** rules (AFWall+ style) |
| `NETFILTER_XT_MATCH_QUOTA`, `NETFILTER_XT_MATCH_TIME` | Data caps and time-based rules |
| `NETFILTER_XT_TARGET_NOTRACK` | Conntrack bypass for throughput |
| `NFT_FIB_IPV4/IPV6/INET`, `NFT_FIB`, `NFT_SOCKET`, `NFT_OSF` | Policy routing lookups, socket matching, OS fingerprinting in nftables |
| `NETFILTER_INGRESS`, `NF_FLOW_TABLE`, `NF_FLOW_TABLE_INET`, `NFT_FLOW_OFFLOAD` | Flow offload fast path |

- **Why:** these are the pieces Android firewall/proxy apps expect. Without
  `MATCH_OWNER` a per-app firewall cannot match by uid at all.
- **Expected benefit:** per-app blocking can stop background apps from using the
  network (battery + latency); TPROXY avoids the extra VPN-layer overhead.
- **Risk:** low. `NFT_COMPAT` is untouched, so Android `netd`'s existing iptables
  rules keep working — this was checked specifically.

> 🔎 **Two dependency traps found during validation.** `NFT_FIB` is *promptless*
> and is selected by `NFT_FIB_IPV4`/`IPV6`; `NFT_FLOW_OFFLOAD` requires
> `NF_FLOW_TABLE`, which itself requires `NETFILTER_INGRESS`. Requesting only the
> leaf symbols left all three at `n`. Caught before building, not after.

### ✨ Added — monitoring, so tuning can be evidence-based

`CPU_FREQ_TIMES`, `TASKSTATS`, `TASK_DELAY_ACCT`, `TASK_XACCT`,
`TASK_IO_ACCOUNTING`, `SCHEDSTATS`

- **Why:** until now, performance and battery claims could not be checked on the
  device. These expose the counters needed to measure instead of guess.
- **Expected benefit:** `time_in_state` shows how long each CPU frequency was
  actually used, so you can see whether the CPU sits high when idle. Per-task
  delay accounting shows which app is actually stalling on I/O.
- **Risk:** very low, small accounting overhead. `SCHEDSTATS` needs
  `DEBUG_KERNEL` + `PROC_FS`, **not** `DEBUG_FS` — so `DEBUG_FS` stays off.

```bash
su -c "cat /sys/devices/system/cpu/cpufreq/policy0/stats/time_in_state"
su -c "head -3 /proc/schedstat"
```

### 🔧 Changed — the verifier can no longer miss string options

- **What:** it matched only `^CONFIG_…=y$` and ignored string/numeric values
  entirely. That is *why* the BBR bug was invisible for so many builds.
- **Now:** requested string/numeric options are compared against the final
  `.config` and a mismatch fails the build.
- 📊 **Negative-tested:** restoring `"cubic"` produces
  `::error title=Config value not applied::CONFIG_DEFAULT_TCP_CONG wanted "bbr" got "cubic"`
  and exit 1.

### ❌ Declined in this round

| Option | Reason |
|---|---|
| `SCHED_AUTOGROUP` | Desktop/TTY-oriented; can lump all Android apps into one group and **hurt** responsiveness |
| `F2FS_CHECK_FS` | Debug consistency checks — runtime overhead, not a user feature |
| `BLK_WBT`, `F2FS_FS_COMPRESSION` | Available, but behaviour-changing → belong in a separate experimental build, never the stable one |
| Game-controller drivers | Verified available (`JOYSTICK_XPAD`, `HID_SONY`…) but not requested |

### 📊 Verified

- 30/30 new symbols `=y`; **0 regressions** across the existing 116
- `susfs.yml`: 144/144 non-KSU options match
- Verifier dry-run exit 0; both YAML files parse
- `DEBUG_FS`, `ZRAM_MEMORY_TRACKING`, `NFS_FS`, `NFSD`, `SCHED_AUTOGROUP`,
  `F2FS_CHECK_FS` confirmed still **off**
- CI: stable **#22** and SUSFS **#5** both success, **0 annotations**

---

## [stable-20] — 2026-11-28 · superseded

### 🔧 Changed — documentation edits no longer rebuild the kernel

- **What:** `paths-ignore: ['**.md', 'tools/**']` on the push trigger.
- **Why:** every doc merge was firing a ~17-minute kernel build **and** publishing
  a redundant release. That is what created the release pile-up.
- **Benefit:** faster iteration, no wasted CI minutes, no confusing duplicate
  downloads.
- 📊 **Verified:** a later doc-only merge produced **no** new run.

### ✨ Added — `tools/verify_device.sh`

- **What:** a strictly **read-only** runtime report for Termux.
- **Why:** CI proves compilation; nothing proved what actually runs on the phone.
- **Covers:** ROM identity, kernel version, KernelSU-Next, **both SUSFS halves**,
  cpufreq/devfreq governors, thermal zones and temps, zram/PSI, TCP CC,
  filesystems, and a `dmesg` BUG/Oops/panic scan.
- **Risk:** none — no sysfs/procfs writes, no setting changes, no flashing.
- 📊 **Verified:** `sh -n`, `dash -n`, `busybox sh -n`, plus an end-to-end smoke
  test (missing nodes degrade to `n/a`, exit 0).

---

## [susfs-4] — 2026-11-28 · superseded

### ✨ Added — SUSFS version recorded in `REVISIONS.txt`

- **What:** `susfs_version=`, `susfs_remote=`, `susfs_sha=`, `sus_su=disabled`.
- **Why:** the userspace module requires SUSFS **≥1.5.2**, but the version was
  only visible in CI logs — and log/asset downloads are not always reachable.
  Users had no reliable way to check compatibility before installing.
- **Benefit:** compatibility is checkable from a 480-byte text file on the release
  page. Confirms **v1.5.5** vs module requirement 1.5.2+.
- 📊 **Verified:** `REVISIONS.txt` grew 341 B → 480 B on `earth-susfs-4`.

### 📚 Docs — SUSFS usage guide rewritten

- ROM compatibility matrix (the kernel targets **LineageOS 24.0**; stock MIUI and
  cross-device ports are not supported).
- **WebUI** configuration discovered in module R28 (`webroot/index.html`) — no
  more hand-editing `config.sh`.
- Full 21-knob audit read from the **release tag**, because the module's `main`
  branch is stale at v1.4.2-R12.
- **Two more unsupported knobs found** by reading the SUSFS v1.5.5 kernel-4.19
  source: `avc_log_spoofing` and `emulate_vold_app_data` are **absent** there.
  Documented as leave-off, alongside the already-known `sus_su`.

---

## [stable-18] + [susfs-3] — 2026-11-28 · superseded

### ✨ Added — flashable ZIPs published to GitHub Releases

- **Why:** Actions artifacts require a GitHub **sign-in** and expire after 90
  days — unusable as a shareable download link on a phone.
- **What:** `gh release create` from CI, with `permissions: contents: write`.
  SUSFS publishes as `--prerelease`.
- **Benefit:** direct, permanent, no-sign-in downloads; each release also carries
  `REVISIONS.txt` (exact source SHAs) and `build-config.txt` (the real `.config`).

---

## [susfs-2] — 2026-11-28 · first working SUSFS build

### 🐛 Fixed — SUSFS API name mismatch broke linking

| | |
|---|---|
| **Symptom** | SUSFS build **#1** failed at link: undefined `susfs_try_umount_all` referenced from `fs/namespace.c` |
| **Root cause** | The 4.19 patch calls `susfs_try_umount_all(uid)`, but SUSFS v1.5.5 defines `susfs_try_umount(target_uid)` |
| **Fix** | `reconcile_api()` rewrites the extern and the call site |
| **Prevention** | `check_symbols()` now resolves every SUSFS/KSU symbol locally before CI — **27/27 resolved** |
| 📊 **Verified** | SUSFS **#2** success in 16m35s, 0 annotations |

> Alternatives were evaluated and rejected: `W-Nana` mirror (329 B, invalid) and
> `TheNoxS1d` v1.5.12 (no `_all`, no `vfs_create_mount`). Neither was better.

---

## [stable-15] — 2026-11-28

### 🐛 Fixed — NFS was breaking the build

| | |
|---|---|
| **Symptom** | Build **#13** failed: `fs/nfs/client.c:625` sets `rpc_clnt.cl_softerr` |
| **Root cause** | `include/linux/sunrpc/clnt.h` in this tree has **no such member** — a latent bug, never exposed because NFS is off in the stock defconfig |
| **Decision** | ❌ `NFS_FS` / `NFS_V3` / `NFS_V4` / `NFSD` stay **off** in both builds |
| **Why not fix it** | A correct fix needs a SUNRPC backport — invasive, and out of scope for a stability-first release |

### 🐛 Fixed — verifier was failing on options we never requested

- **Symptom:** build **#14** compiled fine but verification failed.
- **Root cause:** it checked the *whole* defconfig, including stock entries
  Kconfig legitimately drops (`EXFAT_DISCARD`, `CUSTOM_KERNEL_SAR`,
  `MTK_AB_OTA_UPDATER`, `SHADOW_CALL_STACK`, `CFI_CLANG`, `LTO_CLANG`).
- **Fix:** verification is scoped to `/tmp/requested-config.txt` — only what we
  actually ask for.
- 📊 **Verified:** **#15** success, 0 annotations.

---

## [stable-11 / -12] — 2026-11-28

### 🔧 Changed — `upload-artifact` v4 → v7

- **Why:** v4 runs on Node.js 20, which GitHub deprecated; the run emitted a
  warning on every build.
- **Benefit:** clean runs, **0 annotations**, no deprecation noise hiding real
  problems.

---

## Earlier foundations — 2026-11-27 / 28

### 🐛 Fixed — `path_umount` undefined (kernel would not link)

- **Root cause:** KernelSU-Next's `feature/kernel_umount.c` calls `path_umount()`
  when `KSU_HAS_PATH_UMOUNT` is set, but that function is a **5.9** API and does
  not exist in 4.19.
- **Fix:** backported the upstream 5.9 implementation into `fs/namespace.c`.
- **Why it matters:** without it there is **no kernel image at all**.

### 🐛 Fixed — WireGuard built twice (duplicate symbols)

- **Symptom:** five consecutive failed builds.
- **Root cause:** earth already ships **WireGuard v1.0.0 in-tree** at
  `drivers/net/wireguard`. Adding `wireguard-linux-compat` produced duplicate
  `wg_*` symbols.
- **Fix:** removed the compat step; just enable `CONFIG_WIREGUARD=y`.
- **Lesson recorded:** never re-add the compat module to this tree.

### 🐛 Fixed — KernelSU hook mode typo and AnyKernel3 device names

- KSU hook configuration corrected to **manual hooks**
  (`KSU_MANUAL_HOOK=y`, `KSU_KPROBES_HOOK=n`) — kprobes are not viable here.
- AnyKernel3 locked to `device.name1=earth`, `name2=aether` so the ZIP **refuses
  to flash** on the wrong device.

### ✨ Added — Tier A feature set

DDR devfreq governors · thermal governors + writable trips (hardware protection
preserved) · CAKE/FQ_CODEL/PIE/CoDel/NETEM + shaping qdiscs · DCTCP/HSTCP/HYBLA/
NV/CDG · nftables + IPv6 NAT + TEE · SquashFS/XFS/Btrfs/HFS+/UDF/JFS · KERNEL_LZ4.
Each validated `=y` with kconfiglib **before** building.

### ✨ Added — SUSFS port, isolated in its own workflow

- `scripts/port_susfs.py`: idempotent, anchor-asserting port with self-verification.
- Repairs needed because earth carries backports: `fs_context`
  (`vfs_create_mount(fc)`), `vfsmount` KABI reserve(4), `task_struct` KABI
  reserve(8), `task_mmu.c` anchor.
- Restores the `CL_ZYGOTE_COPY_MNT_NS` guard that upstream hunk #8 dropped via fuzz.
- **13 SUSFS options `=y`, 3 `=n`** — `SUS_SU` (no kprobes on non-GKI),
  `SUS_OVERLAYFS` (not on 4.19), `HAS_MAGIC_MOUNT` (KSU-Next legacy).

---

## 📚 More detail

| Document | Contents |
|---|---|
| [changelog/BUILD-LEDGER.md](changelog/BUILD-LEDGER.md) | Every CI run, including failures and root causes |
| [changelog/FEATURES.md](changelog/FEATURES.md) | Feature → why → expected benefit |
| [changelog/DISABLED.md](changelog/DISABLED.md) | Everything declined, with reasons |
| [changelog/TEMPLATE.md](changelog/TEMPLATE.md) | How to write the next entry |
| [FINAL_KERNEL_REPORT.md](FINAL_KERNEL_REPORT.md) | Full 9-step audit and rationale |
| [SUSFS_USAGE_GUIDE.md](SUSFS_USAGE_GUIDE.md) | Installing and configuring SUSFS |

---

<div align="center">

🐧 **Stability over feature count.** Every entry above explains *why*, and every
"expected benefit" is labelled as an expectation — not a benchmark. 🐧

</div>
