# ✨ Feature Manifest — earth Kernel

Authoritative feature list with **source-code evidence** and an explicit status for
every entry. Verified against LineageOS `android_kernel_xiaomi_earth` @
`lineage-24.0` (Linux **4.19.325**) and the configuration actually built by CI.

> 📌 **Companion documents:** [KERNEL_CONFIG.md](KERNEL_CONFIG.md) has the
> before/after config comparison · [DISABLED](changelog/DISABLED.md) has decline
> reasons · [CHANGELOG.md](CHANGELOG.md) has the change history.

---

## 🏷️ Status vocabulary

| Status | Meaning |
|---|---|
| **Enabled** | Config `=y` in the final `.config` **and** the implementing source is present in the tree |
| **Implemented** | Code is present and linked; requires userspace or runtime configuration to have an effect |
| **Available-but-disabled** | Source exists, config is `n`. Could be enabled; see the reason |
| **Experimental** | Present only in an isolated experimental build, never in stable |
| **Planned** | Approved for investigation, **not yet in any build** |
| **Unsupported** | Cannot work on this kernel/device — with evidence |

⚠️ **Enabled ≠ measured.** No performance, battery or frame-rate figure in this
repository is a measurement. Boot behaviour is unverified until tested on device.

---

## 📦 Which build has what

| Feature group | Stable `earth-stable-22` | SUSFS `earth-susfs-5` |
|---|:---:|:---:|
| Everything below except SUSFS | ✅ | ✅ |
| SUSFS v1.5.5 | ❌ | ✅ |

---

## 🧠 CPU & scheduling

| Feature | Status | Config | Source evidence |
|---|---|---|---|
| **EAS (Energy Aware Scheduling)** | **Enabled** | `ENERGY_MODEL=y` | `kernel/sched/fair.c:7553` `find_energy_efficient_cpu()`; gated at `:7702` by `sched_energy_present` |
| **Energy model registration** | **Enabled** | — | `drivers/misc/mediatek/base/power/cpufreq_v1/src/v2/mtk_cpufreq_main.c:1302` calls `em_register_perf_domain()` unconditionally |
| Asymmetric CPU capacities | **Enabled** | — | `arch/arm64/boot/dts/mediatek/mt6768.dts`: A75 `capacity-dmips-mhz=1024, dynamic-power-coefficient=275`; A55 `495 / 85` |
| **schedutil** governor (default) | **Enabled** | `CPU_FREQ_GOV_SCHEDUTIL=y`, `CPU_FREQ_DEFAULT_GOV_SCHEDUTIL=y` *(already stock)* | `kernel/sched/cpufreq_schedutil.c` |
| performance / conservative governors | **Enabled** | `CPU_FREQ_GOV_PERFORMANCE=y`, `…_CONSERVATIVE=y` | `drivers/cpufreq/` |
| **UCLAMP** (task + group) | **Enabled** | `UCLAMP_TASK=y`, `UCLAMP_TASK_GROUP=y` *(stock)* | `init/Kconfig:724` |
| UCLAMP bucket granularity | **Available-but-disabled** | `UCLAMP_BUCKETS_COUNT=5` (range **5–20**, `init/Kconfig:726`) | Raising to 20 is **Planned** (Phase C1) |
| **Full preemption** | **Enabled** | `PREEMPT=y`, `HZ=250` | `kernel/Kconfig.preempt` |
| Scheduler multinode | **Enabled** | `SCHED_MC=y` | `kernel/sched/` |
| **SCHEDSTATS** | **Enabled** | `CONFIG_SCHEDSTATS=y` — ⚠️ **already stock** (`earth_defconfig:378`); the Group 4 request was redundant | `kernel/sched/stats.c` |
| CPU hotplug | **Enabled** | `HOTPLUG_CPU=y` | — |
| `CPU_FREQ_TIMES` (time-in-state) | **Enabled** | `=y` | `drivers/cpufreq/cpufreq_times.c` |
| `CPU_FREQ_STAT` | **Enabled** | `=y` *(stock)* | `drivers/cpufreq/cpufreq_stats.c` |
| **SCHED_AUTOGROUP** | Available-but-disabled | `n` | Declined: TTY-oriented grouping can hurt Android responsiveness |
| **CPU_IDLE_GOV_TEO** | **Unsupported** | symbol absent | TEO is a 5.x governor; `MENU=y` is used |
| **WALT** | **Unsupported** | — | Qualcomm-only scheduler; this is MediaTek |

🔎 **Runtime proof of EAS:** `dmesg | grep "energy model register"` — the MTK driver
logs `energy model register result %d` at the line cited above.

---

##  Memory management

| Feature | Status | Config | Source evidence |
|---|---|---|---|
| **ZRAM** | **Enabled** | `ZRAM=y` *(stock)* | `drivers/block/zram/zram_drv.c` |
| **ZRAM writeback** | **Enabled** | `ZRAM_WRITEBACK=y` *(stock)* | `zram_drv.c:443` `backing_dev_store`, `:626` `writeback_store` |
| LZ4 / ZSTD compression | **Enabled** | `CRYPTO_LZ4=y`, `CRYPTO_ZSTD=y` | Algorithm chosen at runtime via `comp_algorithm` |
| **ZSWAP** | **Enabled** | `ZSWAP=y`, `FRONTSWAP=y` | `mm/zswap.c` |
| **Z3FOLD / ZBUD** allocators | **Enabled** | `=y` | `mm/z3fold.c`, `mm/zbud.c` |
| **KSM** page merging | **Enabled** | `KSM=y` | `mm/ksm.c` |
| **CLEANCACHE** | **Enabled** | `CLEANCACHE=y` | `mm/cleancache.c` |
| **PSI** pressure metrics | **Enabled** | `PSI=y`, `PSI_DEFAULT_DISABLED=n` *(stock)* | `kernel/sched/psi.c` |
| **Compaction / CMA** | **Enabled** | `COMPACTION=y`, `CMA=y` *(stock)* | `mm/compaction.c`, `mm/cma.c` |
| Memory cgroups + swap | **Enabled** | `MEMCG=y`, `MEMCG_SWAP=y` | `mm/memcontrol.c` |
| `PROC_PAGE_MONITOR` | **Enabled** | `=y` *(stock)* | `fs/proc/task_mmu.c` |
| **`IDLE_PAGE_TRACKING`** | Available-but-disabled → **Planned** | `n` | `mm/page_idle.c` present; zero side effects verified |
| **`ZRAM_MEMORY_TRACKING`** | **Unsupported by policy** | `n` | `drivers/block/zram/Kconfig`: `depends on DEBUG_FS`, which stays off |
| **`ZSMALLOC_STAT`** | **Declined** | `n` | `mm/Kconfig:617` **`select DEBUG_FS`** → would force debugfs on plus 14 further debug symbols |
| **`ZRAM_DEF_COMP_*`** | **Unsupported** | symbol absent | Not in 4.19; runtime `comp_algorithm` instead |
| **MGLRU** | **Unsupported** | absent | No `mm/lru_gen`; invasive MM backport |
| **DAMON** | **Unsupported** | absent | No `mm/damon` |
| **simple_lmk** | **Declined** | absent | Conflicts with Android `lmkd` |
| **TRANSPARENT_HUGEPAGE** | Available-but-disabled | `n` | Enabling defaults to `THP_ALWAYS=y` — unsafe for Android latency. **Experimental** only, with explicit `MADVISE` |

---

## 🎮 GPU & gaming

| Feature | Status | Config | Source evidence |
|---|---|---|---|
| **Mali Valhall r32p1** | **Enabled** | `MTK_GPU_VERSION="mali valhall r32p1"` | `drivers/gpu/mediatek/gpu_mali/mali_valhall/mali-r32p1/` |
| MTK GPU DVFS | **Enabled** | `MTK_GPU_SUPPORT=y`, `MTK_GPU_COMMON_DVFS_SUPPORT=y` | `drivers/gpu/mediatek/` |
| **devfreq governors** (5) | **Enabled** | `DEVFREQ_GOV_{SIMPLE_ONDEMAND,PERFORMANCE,POWERSAVE,USERSPACE,PASSIVE}=y` | `drivers/devfreq/governor_simpleondemand.c` et al. |
| devfreq thermal cooling | **Enabled** | `DEVFREQ_THERMAL=y` | `drivers/thermal/devfreq_cooling.c` |
| **GPU overclock** | **Declined** | — | Not required; Mali DVFS stability outweighs peak numbers |
| Frame-pacing / rendering tweaks | **Planned** | — | No verified mechanism identified yet; no claim made |

---

## 💾 Storage & I/O

| Feature | Status | Config | Source evidence |
|---|---|---|---|
| **BFQ** + group scheduling | **Enabled** | `IOSCHED_BFQ=y`, `BFQ_GROUP_IOSCHED=y` | `block/bfq-iosched.c` |
| **Kyber / MQ deadline** | **Enabled** | `MQ_IOSCHED_KYBER=y`, `MQ_IOSCHED_DEADLINE=y` | `block/kyber-iosched.c` |
| CFQ / NOOP | **Enabled** | *(stock)* | `block/` |
| Block cgroups | **Enabled** | `BLK_CGROUP=y` *(stock)* | `block/blk-cgroup.c` |
| Inline encryption | **Enabled** | `BLK_INLINE_ENCRYPTION=y` *(stock)* | `block/keyslot-manager.c` |
| **F2FS** + stat/xattr/security | **Enabled** | all `=y` — ⚠️ **already stock**, no change was needed | `fs/f2fs/` |
| EROFS / EXT4 / exFAT / NTFS-RW / FUSE / OVERLAY | **Enabled** | *(stock)* | `fs/` |
| **SquashFS** (XZ/LZ4/ZSTD) | **Enabled** | `SQUASHFS=y` + compressors | `fs/squashfs/inode.c` |
| **XFS / Btrfs / HFS+ / UDF / JFS** | **Enabled** | `=y` | `fs/xfs/libxfs/xfs_alloc.c`, `fs/btrfs/super.c`, … |
| **CIFS/SMB** | **Enabled** | `CIFS=y`, `NETWORK_FILESYSTEMS=y` | `fs/cifs/` |
| **`BLK_CGROUP_IOLATENCY`** | Available-but-disabled → **Planned** | `n` | `block/blk-iolatency.c` present; zero side effects |
| **`BLK_DEV_THROTTLING`** | Available-but-disabled → **Planned (C2)** | `n` | `block/blk-throttle.c`; adds `…_LOW=n` |
| **`BLK_WBT`** | Available-but-disabled → **Experimental** | `n` | `block/blk-wbt.c`; auto-selects `BLK_WBT_MQ=y`. Changes I/O behaviour |
| **`F2FS_FS_COMPRESSION`** | Available-but-disabled → **Experimental** | `n` | `fs/f2fs/compress.c` present; auto-selects LZ4/LZO/ZSTD. Needs userspace support; does **not** compress existing data |
| **NFS / NFSD** | **Unsupported** | `n` | `fs/nfs/client.c:625` sets `rpc_clnt.cl_softerr`, absent from this tree's `include/linux/sunrpc/clnt.h` |
| **NTFS3 / sdfat** | **Unsupported** | absent | Not in 4.19; in-tree NTFS-RW + exFAT cover the use case |

---

## 🌐 Networking

| Feature | Status | Config | Source evidence |
|---|---|---|---|
| **BBR default** | **Enabled** | `DEFAULT_BBR=y` → `DEFAULT_TCP_CONG="bbr"` | `net/ipv4/tcp_bbr.c`. Fixed in build #22 — see [CHANGELOG](CHANGELOG.md) |
| DCTCP / HSTCP / HYBLA / NV / CDG / BIC / CUBIC / Westwood / Vegas / Veno / Yeah / Illinois / LP / Scalable / HTCP | **Enabled** | `=y` | `net/ipv4/tcp_*.c` |
| **CAKE / FQ_CODEL / PIE / CoDel / NETEM** | **Enabled** | `=y` | `net/sched/sch_cake.c`, `sch_fq_codel.c`, … |
| HFSC / PRIO / SFQ / TBF / INGRESS / MQPRIO / FQ / HTB | **Enabled** | `=y` | `net/sched/` |
| **Classifiers + actions** | **Enabled** | `NET_CLS_U32/FLOWER/CGROUP`, `NET_ACT_POLICE/MIRRED` | `net/sched/cls_u32.c`, `act_police.c` |
| **nftables** + compat | **Enabled** | `NF_TABLES=y`, `NF_TABLES_INET=y`, `NFT_COMPAT=y` | `net/netfilter/nf_tables_api.c` |
| **TPROXY** | **Enabled** | `NFT_TPROXY=y`, `NETFILTER_XT_TARGET_TPROXY=y`, `…_MATCH_SOCKET=y` | `net/netfilter/nft_tproxy.c` |
| **Per-app firewall (uid)** | **Enabled** | `NETFILTER_XT_MATCH_OWNER=y` | `net/netfilter/xt_owner.c` |
| QUOTA / TIME / NOTRACK | **Enabled** | `=y` | `net/netfilter/xt_*.c` |
| FIB / SOCKET / OSF | **Enabled** | `NFT_FIB_IPV4/IPV6/INET`, `NFT_SOCKET`, `NFT_OSF` | `net/netfilter/nft_fib*.c` |
| **Flow offload** | **Enabled** | `NETFILTER_INGRESS`, `NF_FLOW_TABLE(_INET)`, `NFT_FLOW_OFFLOAD` | `net/netfilter/nf_flow_table_core.c` |
| IPv6 NAT / MASQUERADE / TEE | **Enabled** | `=y` | `net/ipv6/netfilter/` |
| ipset (17 variants) + TTL/HL | **Enabled** | `=y` | `net/netfilter/ipset/` |
| **WireGuard** | **Enabled** | `WIREGUARD=y` — in-tree **v1.0.0**, never duplicated | `drivers/net/wireguard/socket.c` |
| **BPF** core | **Enabled** | `BPF_SYSCALL`, `BPF_JIT`, `BPF_JIT_ALWAYS_ON`, `CGROUP_BPF`, `XDP_SOCKETS`, `NET_CLS_BPF`, `NET_ACT_BPF` *(stock)* | `kernel/bpf/syscall.c` |
| `BPF_UNPRIV_DEFAULT_OFF` | Available-but-disabled → **Planned** | `n` | Zero side effects; reduces unprivileged attack surface |
| **`TLS` (kTLS)** | Available-but-disabled → **Planned (C2)** | `n` | `net/tls/tls_main.c`; selects `STREAM_PARSER=y` |
| **`BPF_STREAM_PARSER`** | Available-but-disabled → **Planned (C2)** | `n` | sockmap; selects `STREAM_PARSER=y` |
| **`PACKET_DIAG` / `INET_UDP_DIAG` / `INET_RAW_DIAG`** | Available-but-disabled → **Planned** | `n` | `net/core/sock_diag.c`; enables proper `ss` output |
| **`CGROUP_NET_PRIO`** | Available-but-disabled → **Planned** | `n` | `net/core/netprio_cgroup.c` |
| **`NF_CONNTRACK_TIMEOUT`** | Available-but-disabled → **Planned (C2)** | `n` | Adds `NF_CT_NETLINK_TIMEOUT=n` |
| **`NET_SCH_DEFAULT`** | **Unsupported** | symbol absent | Not in 4.19; default qdisc is the runtime sysctl `net.core.default_qdisc` |
| **BBR2 / BBRplus** | **Unsupported** | absent | Only BBR v1 in tree |

---

## 🌡️ Thermal & power

| Feature | Status | Config | Source evidence |
|---|---|---|---|
| **5 thermal governors** | **Enabled** | `THERMAL_GOV_{STEP_WISE,FAIR_SHARE,BANG_BANG,USER_SPACE,POWER_ALLOCATOR}=y` | `drivers/thermal/` |
| **Writable trip points** | **Enabled** | `THERMAL_WRITABLE_TRIPS=y` | `drivers/thermal/thermal_core.c` |
| **Thermal statistics** | **Enabled** | `THERMAL_STATISTICS=y` | `drivers/thermal/thermal_sysfs.c` |
| **MTK thermal (hardware protection)** | **Enabled** | `MTK_THERMAL=y`, `MTK_LEGACY_THERMAL=y` *(stock, preserved)* | `drivers/thermal/mtk_thermal.c` |
| DDR/GPU cooling | **Enabled** | `DEVFREQ_THERMAL=y` | `drivers/thermal/devfreq_cooling.c` |
| Suspend / wakelocks | **Enabled** | `PM_SLEEP=y`, `SUSPEND=y`, `PM_WAKELOCKS=y` *(stock)* | `kernel/power/` |
| Power-efficient workqueues | **Enabled** | `WQ_POWER_EFFICIENT_DEFAULT=y` *(stock)* | `kernel/workqueue.c` |
| **`CPU_THERMAL`** (generic cooling) | Available-but-disabled → **Experimental** | `n` | `drivers/thermal/cpu_cooling.c` present, but may register a cooling device competing with `mtk_thermal.c` |
| **`PM_AUTOSLEEP`** | Available-but-disabled → **Experimental** | `n` | Android manages sleep via its own wakeup sources; conflict risk |
| Disabling thermal safeguards | **Never** | — | 🛡️ No trip point or cooling device removed, ever |
| Charging / voltage control | **Unsupported** | — | No verified hardware interface on this PMIC path |

---

## 🔓 Root & security

| Feature | Status | Config | Source evidence |
|---|---|---|---|
| **KernelSU-Next** (legacy) | **Enabled** | `KSU=y`, `KSU_MANUAL_HOOK=y`, `KSU_KPROBES_HOOK=n` | Cloned at build time; symlinked to `drivers/kernelsu` |
| **`path_umount` backport** | **Enabled** | — | Backported 5.9 API into `fs/namespace.c`; required or the kernel will not link |
| **SUSFS v1.5.5** | **Experimental** | 13 options `=y`, 3 `=n` | `scripts/port_susfs.py`; **`earth-susfs-5` only** |
| SELinux | **Enabled** | `SECURITY_SELINUX=y`, `…_DEVELOP=y`, `…_AVC_STATS=y` *(stock)* | `security/selinux/` |
| Hardening suite | **Enabled** | see [SECURITY.md](SECURITY.md) | `security/Kconfig`, `arch/arm64/Kconfig` |
| **`SECURITY_YAMA`** | Available-but-disabled | `n` | `security/yama/yama_lsm.c` present. **Kept off** pending KernelSU-Next / root-tool / debugging compatibility verification |
| **LTO_CLANG + CFI_CLANG** | Available-but-disabled → **Experimental** | `n` | `arch/arm64/Kconfig:61` `select ARCH_SUPPORTS_LTO_CLANG`; `arch/Kconfig:530,560`. Requires clang+lld |
| **SHADOW_CALL_STACK** | Available-but-disabled → **Experimental** | `n` | `arch/arm64/Kconfig:63`; `arch/arm64/include/asm/scs.h` present |
| **`MODULE_SIG`** | **Declined** | `n` | Auto-selects `MODULE_SIG_ALL=y` + a generated `certs/signing_key.pem` → breaks build reproducibility |
| **`SUS_SU`** | **Unsupported** | `=n` | Requires kprobes; not viable on this non-GKI 4.19 kernel |
| **`avc_log_spoofing`, `emulate_vold_app_data`** | **Unsupported** | — | Absent from SUSFS v1.5.5 kernel-4.19 source |

---

## 📊 Debugging & tracing

| Feature | Status | Config | Source evidence |
|---|---|---|---|
| `KPROBES`, `KPROBE_EVENTS`, `UPROBE_EVENTS` | **Enabled** | `=y` *(stock)* | `kernel/kprobes.c` |
| `FTRACE`, `TRACING`, `PERF_EVENTS`, `HW_PERF_EVENTS` | **Enabled** | `=y` *(stock)* | `kernel/trace/` |
| **`DEBUG_FS`** | **Available-but-disabled by policy** | `n` | Kept off deliberately; several debug options `select` it |
| **`FUNCTION_TRACER`** | Available-but-disabled → **Experimental** | `n` | Pulls `FUNCTION_GRAPH_TRACER` + `FTRACE_MCOUNT_RECORD` → `-pg` on every function (size + overhead) |
| `ZSMALLOC_STAT`, `ZRAM_MEMORY_TRACKING` | **Declined** | `n` | Both force `DEBUG_FS` on |

---

## 🔗 Related

[KERNEL_CONFIG.md](KERNEL_CONFIG.md) · [SECURITY.md](SECURITY.md) · [PERFORMANCE.md](PERFORMANCE.md) · [COMPATIBILITY.md](COMPATIBILITY.md) · [KNOWN_ISSUES.md](KNOWN_ISSUES.md) · [CHANGELOG.md](CHANGELOG.md)
