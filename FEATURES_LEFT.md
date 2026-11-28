# What's Left to Add — earth (Redmi 12C / MT6768, Linux 4.19.325)

Every entry below was checked against the real LineageOS `lineage-24.0` earth source and evaluated with **kconfiglib** against `earth_defconfig`, so "available" and "currently off" are verified facts, not guesses.

---

## First: things you might think are missing, but are ALREADY on

I checked these because they're common "must-have" requests. No work needed:

| Feature | Effective value | Note |
|---|---|---|
| **PSI** (pressure stall info) | `y` | Already enabled; `PSI_DEFAULT_DISABLED=n`, so `/proc/pressure/*` is live |
| **UCLAMP_TASK** + **UCLAMP_TASK_GROUP** | `y` | Utilization clamping already active (schedutil is default) |
| `CGROUPS`, `CGROUP_SCHED` | `y` | |
| **All 6 CPU governors** | `y` | performance, powersave, userspace, ondemand, conservative, schedutil — **nothing left here** |
| `TCP_CONG_BIC` | `y` | already on |
| `NET_SCH_HTB` | `y` | already on |
| `IOSCHED_CFQ`, `IOSCHED_NOOP` | `y` | already on |
| `FUSE_FS`, `OVERLAY_FS` | `y` | already on |
| exFAT, NTFS-RW, EROFS, F2FS (+encryption) | `y` | stock |
| ZRAM + ZRAM_WRITEBACK | `y` | stock + our LZ4/ZSTD |

---

## TIER A — Available in-tree, just a config flip (low risk)

These exist in the source and are currently `n`. No patching required.

### A1. DDR / devfreq governors — **highest value in Tier A** ⭐
Your SoC is `MACH_MT6768=y`, which builds `drivers/devfreq/helio-dvfsrc-v2/` — the MediaTek **DDR frequency** devfreq driver. But **no devfreq governors are enabled**, so that hardware has no governor choice.

| Config | Currently | Gives you |
|---|---|---|
| `DEVFREQ_GOV_SIMPLE_ONDEMAND` | `n` | load-based DDR scaling (the normal default) |
| `DEVFREQ_GOV_PERFORMANCE` | `n` | pin DDR at max — gaming latency |
| `DEVFREQ_GOV_POWERSAVE` | `n` | pin DDR at min — battery |
| `DEVFREQ_GOV_USERSPACE` | `n` | manual DDR freq via sysfs |
| `DEVFREQ_GOV_PASSIVE` | `n` | follow parent device |

### A2. Thermal governors
Only `THERMAL_DEFAULT_GOV_BACKWARD_COMPATIBLE` is set. All the real governors are off.

| Config | Currently | Gives you |
|---|---|---|
| `THERMAL_GOV_STEP_WISE` | `n` | standard stepwise throttling |
| `THERMAL_GOV_FAIR_SHARE` | `n` | weighted fair cooling |
| `THERMAL_GOV_BANG_BANG` | `n` | simple on/off fan-style |
| `THERMAL_GOV_USER_SPACE` | `n` | userspace thermal control |
| `THERMAL_GOV_POWER_ALLOCATOR` | `n` | PID power-budget allocator (best sustained perf) |
| `THERMAL_WRITABLE_TRIPS` | not set | lets you edit trip points from sysfs |
| `DEVFREQ_THERMAL` | `n` | DDR cooling device |

### A3. Queue disciplines (bufferbloat / latency)
Only `FQ` and `HTB` are on.

| Config | Currently | Why |
|---|---|---|
| `NET_SCH_CAKE` | `n` | best-in-class all-in-one AQM/shaper ⭐ |
| `NET_SCH_FQ_CODEL` | `n` | the standard bufferbloat fix ⭐ |
| `NET_SCH_PIE` | `n` | PIE AQM |
| `NET_SCH_CODEL` | `n` | base CoDel |
| `NET_SCH_NETEM` | `n` | emulate delay/loss (testing) |
| also available | `n` | HFSC, PRIO, SFQ, TBF, MULTIQ, RED, SFB, GRED, DRR, MQPRIO, QFQ, CHOKE, HHF, CBS, ETF, INGRESS |

### A4. Remaining TCP congestion controls
5 left (we already added 8 + BBR).

| Config | Currently |
|---|---|
| `TCP_CONG_DCTCP` | `n` (datacenter-style, low queue) |
| `TCP_CONG_HSTCP` | `n` (HighSpeed — the real name; `TCP_CONG_HIGHSPEED` doesn't exist) |
| `TCP_CONG_HYBLA` | `n` |
| `TCP_CONG_NV` | `n` |
| `TCP_CONG_CDG` | `n` |

### A5. Modern firewall / NAT
| Config | Currently | Gives you |
|---|---|---|
| `NF_TABLES` (+ `NFT_*`) | `n` | nftables backend — **zero** nft support right now |
| `IP6_NF_NAT` | `n` | IPv6 NAT / tethering |
| `NETFILTER_XT_TARGET_TEE` | `n` | packet cloning |

### A6. Filesystems
| Config | Currently | Use |
|---|---|---|
| `NFS_FS` / `NFSD` | `n` | NFS client / server |
| `SQUASHFS` | `n` | read-only compressed images (modules, ROMs) |
| `XFS_FS` | `n` | XFS on OTG drives |
| `BTRFS_FS` | `n` | Btrfs (heavier) |
| `HFSPLUS_FS` | `n` | Mac-formatted drives |
| `UDF_FS` | `n` | DVD/UDF media |
| `JFS_FS`, `9P_FS` | `n` | niche |

### A7. Misc
| Config | Currently | Effect |
|---|---|---|
| `KERNEL_LZ4` | `n` (GZIP default) | much faster boot decompression, slightly bigger image |
| `ZRAM_MEMORY_TRACKING` | `n` | per-page zram stats for tuning |
| `LTO_CLANG` | `n` | link-time optimisation — possible perf gain, **risky** on 4.19 MTK; test separately |

---

## TIER B — Not in the tree; needs a real port or driver patch

These are **absent from the source**, so they're genuine projects, not config flips.

| Feature | Status in tree | Effort / notes |
|---|---|---|
| **SUSFS (root hiding)** ⭐⭐ | patch exists but targets *original* KernelSU layout | **The biggest gap.** Needs porting the SUSFS Kconfig + `susfs.o` build gate + `susfs_is_current_ksu_domain()` / `_zygote_domain()` into KernelSU-Next `legacy`. Currently inactive. |
| **MGLRU** (Multi-Gen LRU) | absent — no `lru_gen` in `mm/vmscan.c` | Big reclaim/latency win; 4.19 ports exist but are invasive |
| **DAMON** | absent — no `mm/damon/` | memory access monitoring; large backport |
| **simple_lmk** | absent | alternative low-memory killer |
| **BBR2 / BBRplus** | absent (BBR v1 only) | needs importing newer BBR |
| **NTFS3** | absent (legacy `ntfs` only) | modern NTFS driver, 5.15+ |
| **sdfat** | absent | faster exFAT; you already have `exfat` |
| **Custom CPU governors** (alucard, darkness, impulse, blu_active, lionheart…) | absent — only the 6 standard ones exist | would need importing each governor |
| **KCAL / display colour control** | needs MTK display driver patch | device-specific |
| **Sound control / headphone gain** | needs MTK audio driver patch | device-specific |
| **Vibration intensity control** | needs vibrator driver patch | device-specific |
| **Charging control / bypass charging (ACC)** | needs MTK charger driver patch | device-specific, battery-risk if wrong |
| **GPU OC / UC** | Mali Valhall r32p1 DVFS tables | risky — stability/heat |
| **WALT scheduler** | Qualcomm-only | **not applicable** to your MediaTek SoC |
| **SUS_SU** | unsupported on non-GKI | deliberately `n` |

---

## My recommendation, in order

1. **SUSFS port** (Tier B) — the only *headline* feature that's advertised but not working. Highest user-visible value.
2. **Tier A bundle: DDR devfreq governors + thermal governors + CAKE/FQ_CODEL + nftables + IPv6 NAT.** All verified-available config flips, one CI run to prove them, real benefits to gaming latency, thermals and networking.
3. **Optional extras:** remaining TCP algos, NFS/SquashFS/HFS+/UDF, `KERNEL_LZ4`, `ZRAM_MEMORY_TRACKING`.
4. **Only if you want to experiment:** MGLRU backport, then `LTO_CLANG` — each in its own build so a failure is easy to attribute.
5. **Skip:** WALT (wrong vendor), SUS_SU (non-GKI), GPU OC and charger patches unless you accept bricking/heat risk.
