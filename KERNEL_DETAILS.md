# 📗 Kernel Details — earth (Redmi 12C / POCO C55)

Technical reference for the current builds. Rewritten from verified repository and
source facts; the previously recorded manager-certificate details are preserved
below because they remain useful.

> 📌 History: this document previously described commit `13e8442` and the
> pre-SUSFS artifact-only workflow. That information is superseded — releases are
> now published publicly and SUSFS builds successfully. See
> [CHANGELOG.md](CHANGELOG.md) for the progression.

---

## 1. Current builds

| Build | Tag | CI run | ZIP size | Result |
|---|---|---|---|---|
| **Stable** | [`earth-stable-22`](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/tag/earth-stable-22) | [#22 · 46137709296](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/actions/runs/46137709296) | 17,295,388 B | ✅ success, 0 annotations |
| **SUSFS experimental** | [`earth-susfs-5`](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/tag/earth-susfs-5) | [#5 · 46137717612](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/actions/runs/46137717612) | 17,305,967 B | ✅ success, 0 annotations |

Downloads are **public release assets — no GitHub sign-in**. Each release ships
`REVISIONS.txt` and `build-config.txt`.

> ℹ️ Actions artifacts are no longer the distribution channel: they require
> sign-in and expire after 90 days.

---

## 2. Base and toolchain

| Item | Value | Evidence |
|---|---|---|
| Kernel source | `LineageOS/android_kernel_xiaomi_earth` @ **`lineage-24.0`** | workflow clone step |
| Kernel version | **Linux 4.19.325** | `Makefile`: `VERSION=4 PATCHLEVEL=19 SUBLEVEL=325` |
| Architecture | **arm64** | CI asserts `vmlinux` is AArch64 |
| Device config | `earth_defconfig` | `arch/arm64/configs/earth_defconfig` |
| SoC | MT6768 / Helio G85 | `MACH_MT6768=y`, `MTK_PLATFORM="mt6768"` |
| CPU topology | 2× Cortex-A75 + 6× Cortex-A55 | `mt6768.dts`: A75 `capacity=1024 dpc=275`; A55 `495 / 85` |
| GPU | Mali **Valhall r32p1** | `MTK_GPU_VERSION="mali valhall r32p1"` |
| Compiler | **clang + ld.lld** | `CC=clang LD=ld.lld AR=llvm-ar NM=llvm-nm …` |
| Binutils | aarch64 / arm GCC **4.9** prebuilts | `toolchain/gcc64`, `toolchain/gcc32` |
| Kernel image | `Image.gz-dtb` (DTB appended) | `CONFIG_BUILD_ARM64_APPENDED_DTB_IMAGE=y`, names `mediatek/mt6768` |
| Packaging | AnyKernel3, locked to `earth` / `aether` | `anykernel.sh` device names |
| Preemption / timer | `PREEMPT=y`, `HZ=250` | resolved config |

⚠️ Toolchain versions are **not yet pinned** — tracked as
[KI-007](KNOWN_ISSUES.md), scheduled for Phase B.

---

## 3. Root: KernelSU-Next

| Item | Value |
|---|---|
| Branch | **`legacy`** (manual hooks) |
| Config | `KSU=y`, `KSU_MANUAL_HOOK=y`, `KSU_KPROBES_HOOK=n` |
| Integration | cloned to `KernelSU-Next`, symlinked as `drivers/kernelsu`, Kconfig/Makefile hooked in |
| Required backport | **`path_umount()`** — a Linux 5.9 API absent from 4.19; without it the kernel **does not link** |
| LKM mode | 🔴 **Unsupported** — LKM targets 5.10+, there is no 4.19 LKM |

### Manager APK (preserved verified details)

**KernelSU-Next v3.4.2**, versionCode **33355**.

| Variant | File | Size |
|---|---|---|
| **Standard (recommended)** | `KernelSU_Next_v3.4.2_33355-release.apk` | 16,682,167 B |
| Spoofed (disguised name) | `KernelSU_Next_v3.4.2-spoofed_33355-release.apk` | 16,684,355 B |

<https://github.com/KernelSU-Next/KernelSU-Next/releases/tag/v3.4.2>

**Authentication is by signing certificate, not package name:**

| Property | Value |
|---|---|
| Certificate size | `0x3e6` (998 bytes) |
| Certificate SHA-256 | `79e590113c4c4c0c222978e413a5faa801666957b1212a328e46c00c69821bf7` |

Both official variants are therefore accepted. A re-signed APK from a mirror will
**fail** the certificate check and root will not be granted. Do not install both
variants at once.

---

## 4. SUSFS (experimental build only)

| Item | Value |
|---|---|
| Version | **v1.5.5** (`include/linux/susfs.h`) |
| Upstream | `simonpunk/susfs4ksu` @ `kernel-4.19` (GitLab), fallback mirror `Zhanfg/susfs4ksu` |
| Port | `scripts/port_susfs.py` — idempotent, anchor-asserting, self-verifying |
| Options | **13 `=y`**, **3 `=n`** |
| Off | `SUS_SU` (needs kprobes), `SUS_OVERLAYFS` (not on 4.19), `HAS_MAGIC_MOUNT` (KSU-Next legacy) |
| Module | `sidex15/susfs4ksu-module` **v1.5.2+_R28** (requires ≥1.5.2 → compatible) |
| Local symbol check | `check_symbols()` — **27/27** resolved before CI |

### Why a custom port was necessary

KernelSU-Next `legacy` ships **no** SUSFS support, and the upstream
`10_enable_susfs_for_ksu.patch` targets the flat original-KernelSU layout. The
4.19 kernel patch also needed repairs because earth carries backports:

| Anchor | Repair |
|---|---|
| `fs_context` backport | `vfs_create_mount(fc)` signature |
| `vfsmount` KABI | `ANDROID_KABI_USE(4, u64 susfs_mnt_id_backup)` |
| `task_struct` KABI | `ANDROID_KABI_USE(8, u64 susfs_last_fake_mnt_id)` |
| `task_mmu.c` | anchor at `pkeys.h` |
| Upstream hunk #8 | applied with fuzz and dropped the `CL_ZYGOTE_COPY_MNT_NS` guard — script restores it |
| API drift | patch called `susfs_try_umount_all`; v1.5.5 defines `susfs_try_umount` → `reconcile_api()` |

**Runtime hiding is unverified.** The kernel is only half of SUSFS; the userspace
module supplies the hide-list. See [SUSFS_USAGE_GUIDE.md](SUSFS_USAGE_GUIDE.md).

---

## 5. Configuration summary

| | Stable | SUSFS |
|---|---|---|
| Requested options | **147** | **163** |
| Changed vs stock defconfig | 142 | 142 + SUSFS |
| Already stock (assertions only) | 5 | 5 |

Full before/after table: [KERNEL_CONFIG.md](KERNEL_CONFIG.md).
Feature-by-feature status with source evidence: [FEATURES.md](FEATURES.md).

---

## 6. Verification performed by CI

| Check | Enforced |
|---|---|
| Non-empty `Image.gz-dtb` | ✅ |
| `vmlinux` is AArch64 | ✅ |
| Every requested `=y` symbol present in final `.config` | ✅ |
| Every requested **string/numeric** value matches | ✅ |
| `path_umount`, `ksu_handle_execveat`, `ksu_handle_faccessat`, `ksu_handle_vfs_read`, `ksu_handle_sys_reboot`, `wg_socket_init` in `System.map` | ✅ |
| SUSFS: `susfs_init`, `susfs_is_current_ksu_domain`, `susfs_is_current_zygote_domain`, `ksu_try_umount`, `susfs_try_umount` | ✅ |
| ZIP contains `Image.gz-dtb`; device locked to `earth`/`aether` | ✅ |

**Not verified:** boot, performance, battery, thermals, runtime hiding.

---

## 7. Runtime checks

```bash
uname -r                                            # 4.19.325…
cat /proc/sys/net/ipv4/tcp_congestion_control        # bbr
su -c "dmesg | grep 'energy model register'"         # EAS initialised (MTK driver)
su -c "dmesg | grep -i susfs"                        # experimental build only
sh tools/verify_device.sh                            # full read-only report
```

---

## 8. Environment note (preserved)

Release binaries are served from `objects.githubusercontent.com`, which is outside
this project's automation allowlist; direct asset downloads return `302` with 0
bytes. Consequently **facts are recorded into `REVISIONS.txt` at build time**
(kernel/KSU SHAs, and for SUSFS the version, remote and `sus_su` state) so they can
be read without downloading binaries. Official maintainer links are always used
rather than re-hosted files.

---

## 🔗 Related

[FEATURES.md](FEATURES.md) · [KERNEL_CONFIG.md](KERNEL_CONFIG.md) · [BUILD_GUIDE.md](BUILD_GUIDE.md) · [INSTALLATION.md](INSTALLATION.md) · [COMPATIBILITY.md](COMPATIBILITY.md) · [CHANGELOG.md](CHANGELOG.md)
