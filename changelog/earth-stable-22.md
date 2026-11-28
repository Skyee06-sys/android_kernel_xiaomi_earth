# 🚀 earth-stable-22

[![Stable](https://img.shields.io/badge/release-stable-success)](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/tag/earth-stable-22)
![Kernel](https://img.shields.io/badge/kernel-4.19.325-blue)
![No SUSFS](https://img.shields.io/badge/SUSFS-not%20included-lightgrey)

**The recommended daily-driver build.** No SUSFS — root only, maximum stability.

| | |
|---|---|
| 📦 **Release** | <https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/tag/earth-stable-22> |
| 🏗️ **CI run** | [#22 · 46137709296](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/actions/runs/46137709296) — ✅ success, **0 annotations** |
| 📏 **ZIP size** | 17,295,388 B |
| 🔖 **Source** | `2fc7655` |
| 📅 **Built** | 2026-11-28 |

---

##  Target device & ROM

| | |
|---|---|
| Device | **Redmi 12C / POCO C55** (`earth` / `aether`) |
| SoC | MediaTek **MT6768** / Helio G85, arm64 |
| Kernel | Linux **4.19.325** |
| Source | LineageOS `android_kernel_xiaomi_earth` @ `lineage-24.0` |
| ROM | **LineageOS 24.0 / Android 17**, or AOSP ROMs on that same base |
| Root | KernelSU-Next `legacy`, manual hooks |

🔴 **Not for stock MIUI or cross-device port ROMs.** See the
[ROM compatibility matrix](../SUSFS_USAGE_GUIDE.md).

---

## ✨ What's new vs stable-20

### 🐛 BBR is now genuinely the default
`CONFIG_DEFAULT_TCP_CONG` is a promptless string derived from a Kconfig *choice*,
so setting it in defconfig was silently discarded — **every earlier build ran
cubic**. Fixed by selecting `CONFIG_DEFAULT_BBR=y`.

**Expected benefit:** lower queueing latency and better throughput on lossy mobile
links than loss-based cubic.

```bash
cat /proc/sys/net/ipv4/tcp_congestion_control    # → bbr
```

### ✨ `tc` shaping now actually works
Added `NET_CLS_U32`, `NET_CLS_FLOWER`, `NET_CLS_CGROUP`, `NET_ACT_POLICE`,
`NET_ACT_MIRRED`. The qdiscs were already present but had no way to be *fed*.

**Expected benefit:** CAKE/FQ_CODEL can isolate game traffic from background
downloads — the mechanism that reduces latency spikes under load.

```bash
su -c "tc qdisc add dev wlan0 root cake bandwidth 20mbit"
su -c "tc -s qdisc show dev wlan0"
```

### ✨ Per-app firewall + transparent proxy
`XT_MATCH_OWNER` (uid rules), `TPROXY` + `MATCH_SOCKET`, `QUOTA`, `TIME`,
`NOTRACK`, `NFT_FIB_*`, `NFT_SOCKET`, `NFT_OSF`, `NF_FLOW_TABLE*`,
`NFT_FLOW_OFFLOAD`.

**Expected benefit:** per-app network blocking (battery + latency); TPROXY avoids
VPN-layer overhead. `NFT_COMPAT` untouched → Android `netd` rules keep working.

### ✨ Monitoring
`CPU_FREQ_TIMES`, `TASKSTATS`, `TASK_DELAY_ACCT`, `TASK_XACCT`,
`TASK_IO_ACCOUNTING`, `SCHEDSTATS`. `DEBUG_FS` stays **off**.

**Expected benefit:** you can now *measure* frequency residency and per-task I/O
delay instead of guessing.

```bash
su -c "cat /sys/devices/system/cpu/cpufreq/policy0/stats/time_in_state"
```

---

## 📊 What was verified

| Check | Result |
|---|---|
| Kernel image | non-empty `Image.gz-dtb` |
| Architecture | `vmlinux` = AArch64 |
| Requested `=y` symbols | **145/145** present in final `.config` |
| Requested string options | **`DEFAULT_TCP_CONG="bbr"`** confirmed |
| Linked symbols | `path_umount`, `ksu_handle_execveat`, `ksu_handle_faccessat`, `ksu_handle_vfs_read`, `ksu_handle_sys_reboot`, `wg_socket_init` |
| Package contents | ZIP contains `Image.gz-dtb`; device locked to `earth`/`aether` |
| CI annotations | **0** |

📄 Every release ships `REVISIONS.txt` (exact source SHAs) and `build-config.txt`
(the complete `.config` actually built, 151,427 B).

---

## ❌ Not included / not enabled

- **SUSFS** — deliberately absent. Use [`earth-susfs-5`](earth-susfs-5.md) if you want it.
- **NFS / NFSD** — broken in this tree (`rpc_clnt.cl_softerr` missing).
- **ZRAM_MEMORY_TRACKING** — needs `DEBUG_FS`, kept off.
- **SCHED_AUTOGROUP**, **F2FS_CHECK_FS**, **BLK_WBT**, **F2FS_FS_COMPRESSION** —
  see [DISABLED.md](DISABLED.md).

---

## 📲 Install

1. **Back up Boot + DTBO in TWRP/OrangeFox** ← your undo button
2. Recovery → Install → `Earth-Lineage24-KSUNext.zip` → swipe
3. Reboot to System. **No cache wipe needed. Never wipe Data.**
4. Install the [KernelSU-Next manager v3.4.2](https://github.com/KernelSU-Next/KernelSU-Next/releases/download/v3.4.2/KernelSU_Next_v3.4.2_33355-release.apk) → must say **Working**
5. Run the read-only check: `sh tools/verify_device.sh`

**Rollback:** recovery → Restore → your Boot backup → reboot.

---

## ⚠️ Honest limits

Compilation, configuration and linked symbols are proven. **Boot, performance and
battery are not** — no device testing has been performed. Use it for a few days
before trying the experimental build.

⬅️ [Back to changelog](../CHANGELOG.md)
