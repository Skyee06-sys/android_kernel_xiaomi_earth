# 🗺️ Roadmap — what is left to do

Rewritten from verified source facts. This document previously listed the
**Tier A** audit as pending work; that work is **complete and shipped**. The
original findings are preserved below as a historical record, with their current
status marked.

>  **Authoritative feature status:** [FEATURES.md](FEATURES.md)
> 📋 **Change history:** [CHANGELOG.md](CHANGELOG.md)
> ❌ **Decline reasons:** [changelog/DISABLED.md](changelog/DISABLED.md)

---

## ✅ Completed since the original audit

| Original Tier A item | Status now | Shipped in |
|---|---|---|
| DDR / devfreq governors (5) | **Enabled** | stable-15 onward |
| Thermal governors (5) + writable trips + statistics | **Enabled** | stable-15 onward |
| Qdiscs: CAKE, FQ_CODEL, PIE, CoDel, NETEM + shaping | **Enabled** | stable-15 onward |
| TCP: DCTCP, HSTCP, HYBLA, NV, CDG | **Enabled** | stable-15 onward |
| nftables + IPv6 NAT + TEE | **Enabled** | stable-15 onward |
| SquashFS, XFS, Btrfs, HFS+, UDF, JFS | **Enabled** | stable-15 onward |
| `KERNEL_LZ4` | **Enabled** | stable-15 onward |
| SUSFS port | **Enabled (experimental build)** | susfs-2 onward, v1.5.5 |
| Traffic-control classifiers + actions | **Enabled** | stable-22 / susfs-5 |
| TPROXY, per-app firewall, nft extras | **Enabled** | stable-22 / susfs-5 |
| Monitoring: `CPU_FREQ_TIMES`, TASKSTATS, … | **Enabled** | stable-22 / susfs-5 |
| BBR actually the default | **Fixed** | stable-22 / susfs-5 |

### Historical note preserved
The original audit correctly observed that **no devfreq governors were enabled**
despite `MACH_MT6768=y` building the MediaTek DDR driver, and that only
`THERMAL_DEFAULT_GOV_BACKWARD_COMPATIBLE` was set. Both were fixed. It also
correctly listed PSI, UCLAMP, all CPU governors, `TCP_CONG_BIC`, `NET_SCH_HTB`,
CFQ/NOOP, FUSE/OVERLAY, exFAT/NTFS-RW/EROFS/F2FS and ZRAM+WRITEBACK as **already
stock** — that finding still holds and those were never re-added as features.

---

## ✅ Phase C1 — implemented

All validated with kconfiglib. **Zero unrequested side effects** unless noted.

| Option | Current → Target | Purpose |
|---|---|---|
| `UCLAMP_BUCKETS_COUNT` | **5 → 20** | Clamp granularity 20% → 5%; range is 5–20 (`init/Kconfig:726`) |
| `SLAB_FREELIST_RANDOM` | n → y | Randomise slab allocation order |
| `SLAB_FREELIST_HARDENED` | n → y | Validate freelist pointers |
| `FORTIFY_SOURCE` | n → y | Compile/runtime bounds checks *(benign: `PROFILE_ALL_BRANCHES` choice entry disappears)* |
| `BPF_UNPRIV_DEFAULT_OFF` | n → y | Disable unprivileged BPF by default |
| `HARDENED_USERCOPY_FALLBACK` | **y → n** | Make existing usercopy hardening strict instead of `WARN()` (`security/Kconfig:174-180`) |
| `IDLE_PAGE_TRACKING` | n → y | Idle-page analysis (`mm/page_idle.c`) |
| `BLK_CGROUP_IOLATENCY` | n → y | Per-cgroup I/O latency targets |
| `PACKET_DIAG`, `INET_UDP_DIAG`, `INET_RAW_DIAG` | n → y | Proper `ss` socket introspection |
| `CGROUP_NET_PRIO` | n → y | Per-cgroup network priority |

**Status:** all 12 applied to stable and SUSFS. Validated 16/16 (with C2), zero
regressions, guards unchanged. Docs updated in the same commit. **Boot testing
still required.**

---

## ✅ Phase C2 — implemented (low-risk subset)

| Option | Verified side effect | Open question |
|---|---|---|
| `TLS` (kTLS) | selects `STREAM_PARSER=y` | Any app on this device that actually uses kTLS? |
| `BPF_STREAM_PARSER` | selects `STREAM_PARSER=y` | Worth it for sockmap-based proxies? |
| `BLK_DEV_THROTTLING` | adds `BLK_DEV_THROTTLING_LOW=n` | Needed alongside `BLK_CGROUP_IOLATENCY`? |
| `NF_CONNTRACK_TIMEOUT` | adds `NF_CT_NETLINK_TIMEOUT=n` | Useful for mobile-data flow churn? |
| `F2FS_FS_COMPRESSION` | auto-selects LZ4 + LZO + ZSTD | Needs userspace/mount support; does **not** compress existing data |

**Implemented:** `TLS`, `BPF_STREAM_PARSER`, `BLK_DEV_THROTTLING`,
`NF_CONNTRACK_TIMEOUT` — the four with small, fully-understood side effects.

**Held back:** `F2FS_FS_COMPRESSION` stays out of stable. It changes filesystem
behaviour and needs userspace/mount support, so it remains an experimental
candidate rather than riding along in a daily-driver build.

---

## 🧪 Phase C3 — LTO/CFI/SCS now in an isolated workflow

Never in a stable release until boot **and** runtime testing succeed.

| Option | Evidence it is available | Main risk |
|---|---|---|
| `LTO_CLANG` + `CFI_CLANG` | `arch/arm64/Kconfig:61` selects `ARCH_SUPPORTS_LTO_CLANG`; `arch/Kconfig:530,560`. Needs clang+lld (CI has both) | MTK vendor drivers frequently break under LTO. Start with `CFI_PERMISSIVE=y` |
| `SHADOW_CALL_STACK` | `arch/arm64/Kconfig:63`; `arch/arm64/include/asm/scs.h` present | Needs clang SCS support; per-thread memory cost |
| `BLK_WBT` | `block/blk-wbt.c`; auto-selects `BLK_WBT_MQ=y` | Changes I/O behaviour |
| `FUNCTION_TRACER` | pulls `FUNCTION_GRAPH_TRACER`, `FTRACE_MCOUNT_RECORD` | `-pg` on every function → size + overhead |
| `TRANSPARENT_HUGEPAGE` | defaults to `THP_ALWAYS=y` when enabled | Must force `MADVISE`; latency risk on Android |
| `CPU_THERMAL` | `drivers/thermal/cpu_cooling.c` present | May register a cooling device competing with `mtk_thermal.c` |
| `PM_AUTOSLEEP` | config-clean | Android manages sleep via its own wakeup sources |

> ℹ️ Isolation is implemented as a **separate manual-only workflow publishing a
> pre-release**, because this session tracks one fixed branch. The guarantee is
> the same: experimental code cannot enter a stable build.

---

## ✅ Phase B — CI improvements (implemented)

| Item | Tracking |
|---|---|
| Pin clang version | [KI-007](KNOWN_ISSUES.md) |
| Pin GCC toolchain commit (currently `-b master`) | KI-007 |
| ccache + `actions/cache` | KI-008 |
| `timeout-minutes` + `concurrency` | KI-009 |
| Report compiler-warning counts | KI-010 |
| SHA256 checksums for release assets | KI-011 |
| Build duration + `$GITHUB_STEP_SUMMARY` | new |

---

##  Held pending verification

| Option | Why held |
|---|---|
| `SECURITY_YAMA` | **Your decision:** keep disabled until KernelSU-Next, debugger and root-tool compatibility is verified. `security/yama/yama_lsm.c` is present and it resolves cleanly with no side effects. |

---

## ❌ Closed — will not be pursued

| Item | Reason |
|---|---|
| `ZSMALLOC_STAT` | **`select DEBUG_FS`** (`mm/Kconfig:617`) → forces debugfs plus 14 further debug symbols |
| `MODULE_SIG` | Auto-generates a signing key per build → breaks reproducibility |
| `STRICT_DEVMEM` / `IO_STRICT_DEVMEM` | `DEVMEM=n` already — the interface does not exist, which is stronger |
| `INIT_ON_FREE_DEFAULT_ON` | Cost on every free; zero-on-alloc already enabled |
| NFS / NFSD | Tree defect: `fs/nfs/client.c:625` uses absent `rpc_clnt.cl_softerr` |
| MGLRU, DAMON, BBR2/BBRplus, NTFS3, sdfat | Absent from this 4.19 tree; invasive backports |
| WALT | Qualcomm-only |
| simple_lmk | Conflicts with Android `lmkd` |
| `SCHED_AUTOGROUP` | TTY-oriented; can hurt Android responsiveness |
| `ZRAM_DEF_COMP_*`, `NET_SCH_DEFAULT`, `CPU_IDLE_GOV_TEO` | Symbols do not exist in 4.19 |
| KCAL / sound / vibration / charging control, GPU OC | No verified hardware interface, or not required |
| Game controllers, USB serial drivers | Verified available and low-risk, but **not requested** |

---

## 🔗 Related

[FEATURES.md](FEATURES.md) · [KERNEL_CONFIG.md](KERNEL_CONFIG.md) · [KNOWN_ISSUES.md](KNOWN_ISSUES.md) · [CONTRIBUTING.md](CONTRIBUTING.md) · [CHANGELOG.md](CHANGELOG.md)
