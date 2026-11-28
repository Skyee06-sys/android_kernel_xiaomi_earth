# 📊 Performance — earth Kernel

**This document contains no performance claims.** It explains the mechanisms that
were enabled, how to measure them yourself, and what has *not* been measured.

> 🚫 **Rule:** no benchmark, FPS, battery-life or latency number appears in this
> repository unless it was actually measured on this device. Nothing has been
> measured yet. Every "expected benefit" elsewhere is a reasoned expectation.

---

## 📏 What is and is not established

| Established by CI | **Not** established |
|---|---|
| Kernel compiles and links | That it boots |
| Image is AArch64 | Frame rate or frame pacing |
| Requested configs are in the final `.config` | Battery life or idle drain |
| Required symbols are present | Thermal behaviour under load |
| Package contains the image, device-locked | App launch time, multitasking |

---

## 🎮 Gaming latency — mechanism, not promise

| Enabled | Mechanism | How to measure |
|---|---|---|
| **CAKE / FQ_CODEL / PIE / CoDel** | Keep queues short so a bulk transfer does not inflate interactive latency | `tc -s qdisc show dev wlan0` → `backlog`, `drops`, `overlimits` |
| **Classifiers + actions** (`cls_u32`, `cls_flower`, `act_police`) | Let you actually direct traffic into those qdiscs | Compare ping during a download, with and without shaping |
| **BBR default** | Models bottleneck bandwidth/RTT instead of reacting to loss | `cat /proc/sys/net/ipv4/tcp_congestion_control` |
| **`PREEMPT=y`, HZ=250** | Full preemption; stock timer rate | Frame-time consistency in your own game |

Example shaping rule (**your choice, not applied by the kernel**):
```bash
su -c "tc qdisc add dev wlan0 root cake bandwidth 20mbit"
su -c "tc -s qdisc show dev wlan0"
su -c "tc qdisc del dev wlan0 root"      # undo
```

⚠️ No qdisc is applied automatically. The kernel provides capability; the default
qdisc remains the system default until you or a userspace tool changes it.

---

## 🧠 Memory & multitasking

| Enabled | Mechanism | Measurement |
|---|---|---|
| **ZRAM + LZ4/ZSTD** | Compressed swap in RAM keeps more apps resident | `cat /sys/block/zram0/mm_stat` → compression ratio |
| **ZRAM writeback** | Idle/incompressible pages can move to storage | `cat /proc/swaps` |
| **ZSWAP / Z3FOLD / ZBUD** | Compressed cache ahead of swap I/O | `/sys/kernel/debug/zswap` unavailable (debugfs off) — use PSI instead |
| **KSM** | Merges identical pages | `/sys/kernel/mm/ksm/pages_shared` |
| **PSI** | Reports *actual* stall time — the honest metric | `cat /proc/pressure/memory` |

**PSI is the metric to trust.** `some avg10` rising means tasks are genuinely
stalled on memory. Compare before/after a change rather than guessing.

```bash
cat /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io
cat /proc/meminfo | head -5
cat /sys/block/zram0/mm_stat
```

---

## ⚡ CPU placement & EAS

**EAS is genuinely active** — not merely compiled:
- `kernel/sched/fair.c:7553` `find_energy_efficient_cpu()`, gated at `:7702`
- MTK registers the energy model at
  `drivers/misc/mediatek/base/power/cpufreq_v1/src/v2/mtk_cpufreq_main.c:1302`
- Asymmetric capacities: A75 `1024`, A55 `495` (`mt6768.dts`)

```bash
su -c "dmesg | grep 'energy model register'"     # proves EM initialised
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor    # schedutil
```

### Frequency residency — the useful battery measurement
```bash
su -c "cat /sys/devices/system/cpu/cpufreq/policy0/stats/time_in_state"
su -c "cat /sys/devices/system/cpu/cpufreq/policy6/stats/time_in_state"
```
Each line is `frequency (kHz)  time (10ms units)`. Take two readings around an
idle period and subtract: that shows whether the CPU sits at high frequencies
while doing nothing. **This is evidence; a battery percentage is not.**

### Uclamp granularity — raised in Phase C1
`UCLAMP_BUCKETS_COUNT` was **5** (20% buckets), the bottom of its permitted
**5–20** range (`init/Kconfig:726`). It is now **20** (5% buckets) for finer clamp
aggregation. Expected to make boost and task placement more precise on the
A75/A55 split — **still unmeasured**. Compare `time_in_state` and PSI before/after
if you want evidence.

---

## 🌡️ Thermals

Hardware protection is **never** disabled. What was added is governor *choice*
and visibility.

```bash
for z in /sys/class/thermal/thermal_zone*; do
  printf '%-24s %8s  %s\n' "$(cat $z/type)" "$(cat $z/temp)" "$(cat $z/policy)"
done
cat /sys/class/thermal/thermal_zone0/available_policies
```

`THERMAL_STATISTICS=y` exposes per-zone transition counts — use them to see how
often throttling actually occurs rather than assuming.

🛡️ No trip point or cooling device was removed. No CPU/GPU frequency is pinned.
GPU overclocking is not implemented.

---

## 💾 Storage & I/O

| Enabled | Mechanism | Measurement |
|---|---|---|
| **BFQ + group scheduling** | Fair I/O between cgroups | `/sys/block/*/queue/scheduler` |
| **Kyber / MQ deadline** | Alternative latency-oriented policies | Compare under your own workload |
| **F2FS** (stock) | Flash-friendly layout | — |

**Enabled in Phase C1/C2:** `BLK_CGROUP_IOLATENCY` (per-cgroup latency targets) and
`BLK_DEV_THROTTLING` (per-cgroup bandwidth caps). Neither acts until configured.

**Still not enabled in stable:** `BLK_WBT` (writeback throttling) and
`F2FS_FS_COMPRESSION`. Both exist in the tree but change behaviour, so they remain
experimental candidates and must be measured independently.

---

## 🧪 A fair measurement method

1. **Baseline first.** Record metrics on your current kernel before flashing.
2. **One change at a time.** Otherwise you cannot attribute a difference.
3. **Control conditions:** same brightness, same network, same apps, similar
   battery level and ambient temperature.
4. **Repeat.** A single run is noise. Use at least three.
5. **Prefer counters over impressions:** PSI stall time, `time_in_state`,
   `tc` backlog/drops, thermal transition counts.
6. **Record the build tag** with every result.

`tools/verify_device.sh` collects most of these in one read-only pass.

---

## ❌ What we deliberately do not do

| Avoided | Why |
|---|---|
| Pinning max CPU/GPU frequency | Burns battery and heat for a benchmark number |
| GPU overclocking | Not required; risks Mali DVFS stability |
| Aggressive voltage changes | No verified safe interface on this hardware |
| Disabling thermal safeguards | Never, under any circumstance |
| `SCHED_AUTOGROUP` | TTY-oriented; can hurt Android responsiveness |
| `TRANSPARENT_HUGEPAGE` with `THP_ALWAYS` | Default when enabled; latency risk on Android |
| Placebo "tweaks" | No mechanism, no benefit |

---

## 📣 Reporting a measured result

If you measure something, please include: build tag, ROM/vendor fingerprint,
the exact command output, conditions, and how many runs. Measured data is welcome
and will be recorded as measured — distinct from expectations.

---

## 🔗 Related

[FEATURES.md](FEATURES.md) · [KERNEL_CONFIG.md](KERNEL_CONFIG.md) · [KNOWN_ISSUES.md](KNOWN_ISSUES.md) · [CHANGELOG.md](CHANGELOG.md)
