# ✨ Features — what, why, and expected benefit 🐧

Every enabled feature with its **purpose** and the **mechanism** by which it should
help. Grouped by the goal it serves.

> ⚠️ **Expected ≠ measured.** These are reasoned expectations based on how the
> code works. No on-device benchmarking has been performed. Measure with
> `tools/verify_device.sh` and the monitoring counters below.

---

## 🎮 Gaming latency

| Feature | Why it's here | Expected benefit |
|---|---|---|
| **CAKE**, **FQ_CODEL**, **PIE**, **CoDel** | Bufferbloat: a big unmanaged queue adds hundreds of ms under load | Keeps queues short, so a download doesn't inflate a game's ping |
| **NET_CLS_U32 / FLOWER / CGROUP**, **NET_ACT_POLICE / MIRRED** | Qdiscs alone can't be *fed* — traffic must be classified into classes | Makes shaping actually usable; isolate game traffic from bulk transfers |
| **BBR default** (+ FQ) | Loss-based cubic fills buffers before reacting | Lower queueing latency, better throughput on lossy mobile links |
| **NETEM** | Network emulation | Lets you *test* latency/loss behaviour deliberately |
| **HFSC, PRIO, SFQ, TBF, INGRESS, MQPRIO** | Classful shaping and prioritisation | Priority for latency-sensitive traffic |
| **HZ_250**, **NO_HZ_IDLE** | Timer frequency / tickless idle | Already stock; balances responsiveness against idle wakeups |

**How to check:**
```bash
cat /proc/sys/net/ipv4/tcp_congestion_control          # bbr
su -c "tc -s qdisc show dev wlan0"                     # queue stats, drops, backlog
```

---

## 🧠 Memory & multitasking

| Feature | Why it's here | Expected benefit |
|---|---|---|
| **ZRAM** + **LZ4 / ZSTD** | Compressed swap in RAM instead of killing apps | More apps stay resident; fewer cold restarts |
| **ZRAM_WRITEBACK** | Idle compressed pages can go to storage | Frees RAM pressure without losing the page |
| **ZSWAP**, **Z3FOLD**, **ZBUD** | Compressed cache for swapped pages | Lower swap I/O |
| **KSM** | Merges identical memory pages | Reclaims RAM from duplicate content |
| **CLEANCACHE / FRONTSWAP** | Reclaims clean page-cache pages instead of discarding | Fewer re-reads from storage |
| **PSI** (stock) | Pressure Stall Information | Shows *actual* memory/CPU/IO stall time — the honest multitasking metric |
| **UCLAMP_TASK / _GROUP** (stock) | Per-task utilisation clamping | Lets the scheduler place background work on little cores |

**How to check:**
```bash
cat /proc/pressure/memory      # some/full avg = real stall time
cat /proc/swaps                # zram active
cat /sys/block/zram0/mm_stat   # compression ratio
```

---

##  DDR / bandwidth scaling

| Feature | Why it's here | Expected benefit |
|---|---|---|
| **DEVFREQ_GOV_SIMPLE_ONDEMAND** | Demand-driven DDR frequency | Bandwidth when needed, savings when idle |
| **DEVFREQ_GOV_PERFORMANCE / POWERSAVE / USERSPACE / PASSIVE** | Alternative policies | Choice for testing; passive follows another device |

Real on this SoC: `MACH_MT6768=y` builds `drivers/devfreq/helio-dvfsrc-v2`.
**No frequencies are forced** — the driver's own OPP table is respected.

```bash
cat /sys/class/devfreq/*/governor
cat /sys/class/devfreq/*/cur_freq
```

---

## 🌡️ Thermals

| Feature | Why it's here | Expected benefit |
|---|---|---|
| **STEP_WISE**, **FAIR_SHARE**, **BANG_BANG**, **USER_SPACE**, **POWER_ALLOCATOR** | Different throttling policies | Fair-share/power-allocator can spread limits instead of clamping one device hard |
| **THERMAL_WRITABLE_TRIPS** | Adjustable trip points | Tunable *without* removing protection |
| **DEVFREQ_THERMAL** | DDR/GPU as cooling devices | More ways to shed heat than CPU-only throttling |
| **THERMAL_STATISTICS** | Per-zone transition counts | Evidence of how often throttling actually happens |

> 🛡️ **Hardware protection is preserved.** No cooling device or trip point was
> removed, and no thermal safeguard was disabled. `MTK_LEGACY_THERMAL` and the
> stock governor stay on.

```bash
for z in /sys/class/thermal/thermal_zone*; do
  echo "$(cat $z/type) $(cat $z/temp) $(cat $z/policy)"
done
```

---

## 🔥 Firewall, proxy & networking

| Feature | Why it's here | Expected benefit |
|---|---|---|
| **NF_TABLES** + **INET** | Was completely absent | Modern ruleset support |
| **NFT_COMPAT** | Android `netd` uses iptables | **Preserves** existing Android networking |
| **XT_MATCH_OWNER** | Match by uid | **Per-app firewall** (AFWall+ style) → block background apps |
| **TPROXY** + **MATCH_SOCKET** | Transparent interception | Clash/v2ray/SagerNet without VPN-layer overhead |
| **XT_MATCH_QUOTA / TIME** | Caps and schedules | Data control |
| **XT_TARGET_NOTRACK** | Skip conntrack | Less per-packet overhead on trusted flows |
| **NFT_FIB_*, NFT_SOCKET, NFT_OSF** | Routing lookups, socket match, OS fingerprint | Policy routing and advanced rules |
| **NF_FLOW_TABLE*, NFT_FLOW_OFFLOAD** | Flow offload fast path | Lower CPU cost per packet on established flows |
| **IPv6 NAT**, **MASQUERADE**, **TEE** | IPv6 tethering, packet duplication | Working IPv6 hotspot; traffic mirroring |
| **TTL / HL targets**, **ipset** (17 variants) | Tethering handling, large sets | Efficient bulk rules |
| **WireGuard** (in-tree v1.0.0) | Modern VPN | Already in the tree — enabled, not duplicated |

---

## 💾 Storage & filesystems

| Feature | Why it's here | Expected benefit |
|---|---|---|
| **SquashFS** (XZ/LZ4/ZSTD) | Read-only compressed images | Mount compressed archives |
| **XFS**, **Btrfs**, **HFS+**, **UDF**, **JFS** | OTG drives and NAS media | Read disks from other systems |
| **CIFS/SMB** | Network shares | Mount NAS shares |
| **BFQ** + group scheduling | Fair I/O between processes | A background write shouldn't stall the foreground app |
| **MQ_KYBER**, **MQ_DEADLINE** | Low-latency multiqueue schedulers | Alternative I/O policies |
| **KERNEL_LZ4** | Kernel decompression | Faster boot decompression than GZIP |
| *stock:* F2FS, EROFS, exFAT, NTFS-RW, FUSE, OVERLAY | Already working | Untouched |

---

## 📊 Monitoring — measure, don't guess

| Feature | Exposes | Use |
|---|---|---|
| **CPU_FREQ_TIMES** | `stats/time_in_state` | How long each frequency was used → real battery analysis |
| **CPU_FREQ_STAT** (stock) | Frequency transition stats | Scaling behaviour |
| **TASKSTATS**, **TASK_DELAY_ACCT** | Per-task CPU/IO delay | Which app is actually stalling |
| **TASK_XACCT**, **TASK_IO_ACCOUNTING** | Per-task I/O bytes | Which app is hammering storage |
| **SCHEDSTATS** | `/proc/schedstat` | Scheduler placement decisions |
| **THERMAL_STATISTICS** | Zone transition counts | Throttling frequency |
| **PSI** (stock) | `/proc/pressure/*` | Real stall time |

`DEBUG_FS` stays **off** — `SCHEDSTATS` needs `DEBUG_KERNEL` + `PROC_FS`, not debugfs.

```bash
su -c "cat /sys/devices/system/cpu/cpufreq/policy0/stats/time_in_state"
su -c "head -3 /proc/schedstat"
```

---

## 🔓 Root & hiding

| Feature | Build | Notes |
|---|---|---|
| **KernelSU-Next** `legacy`, manual hooks | both | `KSU_MANUAL_HOOK=y`, `KSU_KPROBES_HOOK=n` — kprobes not viable here |
| **path_umount** backport | both | 5.9 API required by KSU; without it the kernel won't link |
| **SUSFS v1.5.5** | **experimental only** | 13 options `=y`; needs the userspace module to hide anything |

See [earth-susfs-5.md](earth-susfs-5.md) and [SUSFS_USAGE_GUIDE.md](../SUSFS_USAGE_GUIDE.md).

---

## ❌ Not enabled

Everything declined, with reasons: [DISABLED.md](DISABLED.md)

⬅️ [Back to changelog](../CHANGELOG.md)
