<div align="center">

# 🐧 earth Kernel

### Optimised Linux 4.19.325 for Redmi 12C / POCO C55

[![Stable build](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/actions/workflows/blank.yml/badge.svg)](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/actions/workflows/blank.yml)
[![Latest release](https://img.shields.io/github/v/release/Skyee06-sys/android_kernel_xiaomi_earth?label=stable&color=success)](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/latest)
![Kernel](https://img.shields.io/badge/kernel-4.19.325-blue)
![Arch](https://img.shields.io/badge/arch-arm64-lightgrey)
![SoC](https://img.shields.io/badge/SoC-MT6768%20Helio%20G85-orange)
![Device](https://img.shields.io/badge/device-earth%20%7C%20aether-informational)
![LineageOS](https://img.shields.io/badge/LineageOS-24.0%20%2F%20Android%2017-167C80)
![KernelSU](https://img.shields.io/badge/KernelSU--Next-legacy-success)
![SUSFS](https://img.shields.io/badge/SUSFS-v1.5.5%20(experimental)-purple)

**Built entirely in GitHub Actions — no PC required.** 📱

[📥 Download](#-download) · [📋 Changelog](CHANGELOG.md) · [📖 SUSFS guide](SUSFS_USAGE_GUIDE.md) · [🔍 Full report](FINAL_KERNEL_REPORT.md)

</div>

---

## 📥 Download

| Build | What you get | Link |
|---|---|---|
| 🟢 **Stable** | Root + all performance features. **No SUSFS.** Recommended daily driver. | **[earth-stable-22](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/tag/earth-stable-22)** |
|  **SUSFS experimental** | Everything in stable **+ SUSFS v1.5.5** for root hiding. Pre-release. | **[earth-susfs-5](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/tag/earth-susfs-5)** |

Two **separate** ZIPs from two separate workflows. SUSFS can never leak into the
stable build. Each release also ships `REVISIONS.txt` (exact source SHAs) and
`build-config.txt` (the complete `.config` actually built).

**Also needed:** [KernelSU-Next manager v3.4.2](https://github.com/KernelSU-Next/KernelSU-Next/releases/download/v3.4.2/KernelSU_Next_v3.4.2_33355-release.apk)
· and for SUSFS only, the [userspace module](https://github.com/sidex15/susfs4ksu-module/releases/download/v1.5.2%2B_R28/ksu_module_susfs_1.5.2%2B.zip).

---

## ⚠️ Read before flashing

| | |
|---|---|
| ✅ **Supported** | LineageOS **24.0** / Android 17, and AOSP ROMs on that same base |
| 🟡 **Maybe** | Other AOSP ROMs sharing the `lineage-24.0` device tree + vendor |
| 🔴 **Not supported** | **Stock MIUI**, cross-device port ROMs, other devices |

```bash
uname -r                    # must be 4.19.x — if 5.x, STOP
getprop ro.product.device   # must be earth or aether
```

The ZIP is locked to `earth`/`aether` and **refuses to flash** elsewhere.

> 🛡️ **Back up Boot + DTBO in TWRP first.** That is your undo button.
> No cache wipe needed. **Never wipe Data.** Only `boot` (and `dtbo`) are written.

---

## ✨ Highlights

<table>
<tr><td>🎮</td><td><b>Gaming latency</b></td><td>CAKE / FQ_CODEL / PIE / CoDel with working traffic classifiers, BBR default, NETEM</td></tr>
<tr><td>🧠</td><td><b>Memory</b></td><td>ZRAM + LZ4/ZSTD + writeback, ZSWAP, Z3FOLD, KSM, PSI, uclamp</td></tr>
<tr><td>📶</td><td><b>DDR scaling</b></td><td>Real devfreq governors on MT6768 DVFSRC — no forced frequencies</td></tr>
<tr><td>🌡️</td><td><b>Thermals</b></td><td>5 governors + writable trips + devfreq cooling. <b>Hardware protection preserved.</b></td></tr>
<tr><td>🔥</td><td><b>Firewall</b></td><td>nftables, per-app uid rules, TPROXY, IPv6 NAT, flow offload — Android netd rules kept</td></tr>
<tr><td>💾</td><td><b>Filesystems</b></td><td>SquashFS, XFS, Btrfs, HFS+, UDF, JFS, CIFS + BFQ/Kyber I/O</td></tr>
<tr><td>📊</td><td><b>Monitoring</b></td><td>CPU time-in-state, per-task delay accounting, schedstat, thermal stats</td></tr>
<tr><td>🔓</td><td><b>Root</b></td><td>KernelSU-Next legacy, manual hooks, <code>path_umount</code> backport</td></tr>
<tr><td>🕵️</td><td><b>SUSFS</b></td><td>v1.5.5, 13 options enabled — <b>experimental build only</b></td></tr>
</table>

📖 Full rationale for every feature: [changelog/FEATURES.md](changelog/FEATURES.md)
❌ Everything declined and why: [changelog/DISABLED.md](changelog/DISABLED.md)

---

## 📚 Documentation

| Document | What's inside |
|---|---|
| 📋 **[CHANGELOG.md](CHANGELOG.md)** | Every change with **why** it was made and **what it should improve** |
| 🚀 [stable-22](changelog/earth-stable-22.md) · 🧪 [susfs-5](changelog/earth-susfs-5.md) | Per-release deep dives |
| 🏗️ **[BUILD-LEDGER.md](changelog/BUILD-LEDGER.md)** | Every CI run **including failures**, with root-cause post-mortems |
| ✨ [FEATURES.md](changelog/FEATURES.md) | Feature → why → expected benefit |
| ❌ [DISABLED.md](changelog/DISABLED.md) | Declined features with reasons |
| 📝 [TEMPLATE.md](changelog/TEMPLATE.md) | How the next entry gets written |
| 📖 **[SUSFS_USAGE_GUIDE.md](SUSFS_USAGE_GUIDE.md)** | ROM compatibility, install order, WebUI config, all 21 module knobs |
| 🔍 [FINAL_KERNEL_REPORT.md](FINAL_KERNEL_REPORT.md) | The full 9-step audit |
| 🧰 `tools/verify_device.sh` | **Read-only** runtime report for Termux |

---

## 🔬 How this is built

```
GitHub Actions
  ├─ clone LineageOS android_kernel_xiaomi_earth @ lineage-24.0
  ├─ clone KernelSU-Next @ legacy  → manual hooks
  ├─ [experimental only] port SUSFS via scripts/port_susfs.py
  ├─ append validated config → earth_defconfig
  ├─ compile Image.gz-dtb (clang + lld, arm64)
  ├─ VERIFY: image, AArch64, every requested config =y,
  │          string values match, required symbols in System.map
  ├─ package AnyKernel3 (locked to earth/aether)
  └─ publish ZIP + REVISIONS.txt + build-config.txt to Releases
```

Every config option is validated with **kconfiglib against the real tree before
building** — that is what caught the NFS build break, the `NFT_FIB` dependency
trap, and the BBR-default bug.

| Workflow | Trigger | Output |
|---|---|---|
| `blank.yml` | push to `main` (docs/tools excluded) | stable release |
| `susfs.yml` | **manual only** | pre-release |

---

## 🧪 Verify on your device

```bash
sh tools/verify_device.sh
```

Strictly **read-only** — no writes, no setting changes, no flashing. Reports ROM
identity, kernel version, KernelSU-Next, both SUSFS halves, governors, thermal
zones, zram/PSI, TCP CC, filesystems, and scans `dmesg` for faults.

Quick individual checks:
```bash
cat /proc/sys/net/ipv4/tcp_congestion_control    # bbr
su -c "dmesg | grep -i susfs"                    # experimental build only
su -c "cat /sys/devices/system/cpu/cpufreq/policy0/stats/time_in_state"
```

---

## ⚠️ Honest limits

- ✅ **Proven:** compilation, ARM64 image, every requested config in the final
  `.config`, required symbols linked in, package contents, device lock.
- ❌ **Not proven:** boot, gaming performance, battery life, runtime hiding.
  **No on-device testing has been performed.**
- "Expected benefit" in the changelog is a **reasoned expectation**, never a
  benchmark claim.
- Thermal safeguards are never disabled. No CPU/GPU frequency is pinned.
- Nothing is flashed automatically — every install step is yours.

---

<div align="center">

🐧 **Stability over feature count.** 🐧

Every change explains *why*. Every failure is documented. Every claim is labelled
with what was actually verified.

</div>
