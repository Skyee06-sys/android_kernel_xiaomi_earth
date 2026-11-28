# 🔌 Compatibility — earth Kernel

What this kernel works with, what it does not, and **the evidence** for each
verdict. Compatibility is decided by the **vendor/firmware base**, not a ROM's name.

---

## 📱 Device

| | | Evidence |
|---|---|---|
| **Supported** | Redmi 12C / POCO C55 — `earth`, `aether` | AnyKernel3 locked to `device.name1=earth`, `device.name2=aether` |
| SoC | MediaTek **MT6768** / Helio G85 | `MACH_MT6768=y`, `MTK_PLATFORM="mt6768"` |
| Architecture | **arm64** | CI asserts `vmlinux` is AArch64 |
| Kernel version | **4.19.325** | `Makefile`: `VERSION=4 PATCHLEVEL=19 SUBLEVEL=325` |
| CPU topology | 2× Cortex-A75 + 6× Cortex-A55 | `arch/arm64/boot/dts/mediatek/mt6768.dts`: A75 `capacity=1024`, A55 `capacity=495` |
| GPU | Mali **Valhall r32p1** | `CONFIG_MTK_GPU_VERSION="mali valhall r32p1"`; `drivers/gpu/mediatek/gpu_mali/mali_valhall/mali-r32p1/` |
| **Other devices** | 🔴 **Refused** | The ZIP will not flash — the device-name check fails |

---

## 🧩 ROM compatibility

| ROM type | Verdict | Reason |
|---|---|---|
| **LineageOS 24.0 / Android 17** | ✅ **Intended target** | Kernel is built from `LineageOS/android_kernel_xiaomi_earth` @ `lineage-24.0` |
| **AOSP ROMs on a `lineage-24.0` base** (crDroid, PixelOS, EvolutionX…) | 🟡 **Likely works** | Same device tree and vendor blobs |
| **AOSP ROMs on an older base** (Lineage 21 / 22.1 / 23.0) | 🟠 **Risky** | Vendor expects different kernel interfaces |
| **Stock MIUI** | 🔴 **Not supported** | MIUI HALs talk to Xiaomi kernel nodes this tree does not provide |
| **Port ROM** | 🔴 **Depends on the port** | Uses earth's own vendor → maybe; cross-device vendor → no |
| **GSI** | 🟠 **Inherits the host vendor** | A GSI over Lineage-24.0 vendor behaves like Lineage; over MIUI vendor it inherits MIUI's constraints |
| **Different device / mismatched vendor** | 🔴 **No** | DTB and vendor mismatch |

### Why the source branch matters

The workflow clones:
```
git clone -b lineage-24.0 https://github.com/LineageOS/android_kernel_xiaomi_earth.git
```
This is **LineageOS's** kernel, not Xiaomi's stock kernel. Lineage carries changes
for AOSP userspace.

---

##  Pre-flight checks (run before flashing)

```bash
uname -r                              # must be 4.19.x — if 5.x, STOP
getprop ro.product.device             # must be earth or aether
getprop ro.build.version.release      # Android version
getprop ro.vendor.build.fingerprint   # which vendor base you are on
```

| Result | Meaning |
|---|---|
| `uname -r` = `4.19.325…` | This kernel is running |
| `uname -r` = `4.19.x` but not `.325` | Stock or older kernel |
| `uname -r` = `5.x` | 🔴 **Wrong kernel family — do not flash** |
| device ≠ `earth`/`aether` | 🔴 ZIP will refuse |

---

## 🧱 What the ZIP touches

| Partition | Written? |
|---|---|
| `boot` | ✅ yes — `Image.gz-dtb` |
| `dtbo` | ✅ only if a `dtbo.img` was produced |
| `system`, `vendor`, `data`, `recovery`, `vbmeta` | ❌ **never** |

- **No cache wipe needed.**
- **Never wipe Data.**
- Back up **Boot + DTBO** in TWRP/OrangeFox first — that is the rollback path.

---

## 🔗 Component compatibility

| Component | Version | Status | Evidence |
|---|---|---|---|
| **KernelSU-Next** | `legacy` branch | ✅ | Manual hooks (`KSU_MANUAL_HOOK=y`); kprobes not viable |
| KernelSU-Next **manager** | v3.4.2 (33355) | ✅ | Manager authenticated by APK **signing certificate**, not package name — the `-spoofed` variant also works |
| KernelSU-Next **LKM** | — | 🔴 **Unsupported** | LKM mode targets 5.10+; there is no 4.19 LKM |
| **SUSFS** kernel side | **v1.5.5** | ✅ experimental build | `include/linux/susfs.h` `#define SUSFS_VERSION "v1.5.5"` |
| **SUSFS module** | `v1.5.2+_R28` | ✅ compatible | Requires ≥1.5.2 |
| SUSFS module newer than R28 | — | ⚠️ **Pin R28** | A future module may require newer SUSFS than v1.5.5 |
| **Shamiko** | v1.2.1+ | 🟡 optional | Not required |
| **WireGuard** | in-tree **v1.0.0** | ✅ | `drivers/net/wireguard/` — never add `wireguard-linux-compat`, it duplicates symbols |

### Vendor module ABI

`CONFIG_MODULES=y`, `CONFIG_MODVERSIONS=y`. The ZIP ships **no `.ko` modules**, so
it cannot clash with vendor modules. Helpfully, WiFi (`CONFIG_WLAN_DRV_BUILD_IN=y`)
and the Mali GPU are **built into** the kernel, so they do not depend on vendor
module ABI matching.

---

## ❌ Feature-level incompatibility

| Feature | Why it cannot work here |
|---|---|
| **WALT** scheduler | Qualcomm-only; this is MediaTek |
| **SUS_SU** | Requires kprobes on a non-GKI kernel |
| **NFS / NFSD** | `fs/nfs/client.c:625` uses `rpc_clnt.cl_softerr`, absent from this tree's `sunrpc/clnt.h` |
| **NTFS3 / sdfat / MGLRU / DAMON / BBR2** | Not present in this 4.19 tree |
| **KCAL / sound / vibration / charging control** | No verified hardware interface |
| **`CPU_IDLE_GOV_TEO`, `NET_SCH_DEFAULT`, `ZRAM_DEF_COMP_*`** | Symbols do not exist in 4.19 |

Full list with evidence: [FEATURES.md](FEATURES.md) · [changelog/DISABLED.md](changelog/DISABLED.md)

---

## ⚠️ Unverified

**No on-device boot test has been performed for any ROM.** CI proves compilation,
configuration and linked symbols only. The verdicts above are based on source and
vendor-base reasoning, not testing. Treat first boot on any ROM as a test, with a
Boot backup ready.

---

## 🔗 Related

[INSTALLATION.md](INSTALLATION.md) · [KNOWN_ISSUES.md](KNOWN_ISSUES.md) · [SUSFS_USAGE_GUIDE.md](SUSFS_USAGE_GUIDE.md) · [FEATURES.md](FEATURES.md)
