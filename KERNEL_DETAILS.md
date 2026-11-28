# Redmi 12C (earth) — KernelSU-Next Manager + Full Kernel Details

Everything below reflects what is actually merged on `main` (commit `13e8442`) and verified by green CI builds.

---

## 1. The Manager APK (install this after flashing the kernel)

**Latest stable: KernelSU-Next v3.4.2** — released 2026-10-13, versionCode **33355**.

| Variant | File | Size | Link |
|---|---|---|---|
| **Standard (recommended)** | `KernelSU_Next_v3.4.2_33355-release.apk` | 16,682,167 B (~15.9 MB) | [Download](https://github.com/KernelSU-Next/KernelSU-Next/releases/download/v3.4.2/KernelSU_Next_v3.4.2_33355-release.apk) |
| Spoofed (disguised app name) | `KernelSU_Next_v3.4.2-spoofed_33355-release.apk` | 16,684,355 B (~15.9 MB) | [Download](https://github.com/KernelSU-Next/KernelSU-Next/releases/download/v3.4.2/KernelSU_Next_v3.4.2-spoofed_33355-release.apk) |

Release page (all assets + changelog): <https://github.com/KernelSU-Next/KernelSU-Next/releases/tag/v3.4.2>

> **Why links instead of an attached file:** my sandbox can reach `github.com` and `api.github.com`, but GitHub serves release binaries from `objects.githubusercontent.com`, which is outside my network allowlist. Both download attempts returned `302` with 0 bytes. The links above are the official maintainer assets.

### Which variant should you use?
Your kernel authenticates the manager by its **signing certificate**, not by app name:

- Expected certificate size: `0x3e6` (998 bytes)
- Expected SHA-256: `79e590113c4c4c0c222978e413a5faa801666957b1212a328e46c00c69821bf7`

Detection is signature-based (there is no hardcoded package name), so both official assets are accepted. Use the **standard** APK unless you specifically want the manager to appear under a disguised name — then use the spoofed one. Do **not** use a random re-signed APK from a mirror; it will fail the certificate check and root will not be granted.

---

## 2. The kernel zip

Built by GitHub Actions and attached as an artifact named **`Earth-Lineage24-KSUNext-SUSFS`** (~15.2 MB, contains the AnyKernel3 flashable zip).

| Run | Branch | Result | Artifact size |
|---|---|---|---|
| [#11 — 46109516160](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/actions/runs/46109516160) | feature branch | ✅ success, **0 warnings** | 15,973,662 B |
| [#12 — 46111066184](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/actions/runs/46111066184) | `main` | latest post-merge build | ~15.97 MB |

Open the run page → scroll to **Artifacts** → download. GitHub requires you to be signed in to download artifacts.

---

## 3. Install order

1. **Back up your boot partition** (TWRP/OrangeFox → Backup → Boot). This is your undo button.
2. Flash `Earth-Lineage24-KSUNext-SUSFS.zip` in custom recovery. AnyKernel3 patches your existing boot image and has a device check for **earth** (Redmi 12C) so it refuses to flash on the wrong phone.
3. Reboot to system.
4. Install the manager APK from section 1.
5. Open the manager — it should report **Working** and show the kernel-side KernelSU version.
6. Grant root per-app in the manager's **Superuser** tab.

If the manager says "Not installed", the kernel did not boot from the flashed image — restore your boot backup and re-check.

---

## 4. What was added to the kernel — full details

### 4.1 Base
- Source: LineageOS `android_kernel_xiaomi_earth`, branch **lineage-24.0**
- Kernel version: **Linux 4.19.325**, arm64
- Toolchain: clang + `ld.lld` + LLVM, with AOSP GCC 4.9 aarch64/arm binutils
- Packaging: AnyKernel3 (device-locked to earth)

### 4.2 Root — KernelSU-Next (`legacy` branch)
The `legacy` branch is the non-GKI line, which is what a 4.19 device kernel needs.

Integration:
- Cloned and symlinked to `drivers/kernelsu`
- Wired in via `source "drivers/kernelsu/Kconfig"` and `obj-$(CONFIG_KSU) += kernelsu/`

Config:
```
CONFIG_KSU=y
CONFIG_KSU_MANUAL_HOOK=y
CONFIG_KSU_KPROBES_HOOK=n
```

**Manual hooks (5 syscall entry points)** — chosen over kprobes because kprobes are unreliable/unavailable on many 4.19 device kernels, and manual hooks are deterministic with no probe overhead:

| Kernel function | File | KSU hook installed |
|---|---|---|
| `do_execveat_common` | `fs/exec.c` | `ksu_handle_execveat` / `ksu_handle_execveat_sucompat` |
| `do_faccessat` | `fs/open.c` | `ksu_handle_faccessat` |
| `vfs_read` | `fs/read_write.c` | `ksu_handle_vfs_read` |
| `vfs_statx` | `fs/stat.c` | `ksu_handle_stat` |
| `SYSCALL_DEFINE4(reboot, …)` | `kernel/reboot.c` | `ksu_handle_sys_reboot` |

All hooks are wrapped in `#ifdef CONFIG_KSU`, so they compile out cleanly if root is disabled. The reboot hook is also what KernelSU's Kbuild greps for to validate that manual hooking succeeded.

**Reported version:** `30000 + commit_count + 289`, deliberately offset so the kernel-side version lines up with the manager's versionCode. The Kbuild detects the shallow clone and runs `git fetch --unshallow` automatically, so the number is real, not `1`.

**`path_umount` backport:** KernelSU-Next calls `path_umount()` (a Linux 5.9 API) for its umount feature. 4.19 does not have it, which caused the original `ld.lld: undefined symbol: path_umount`. I backported `can_umount()` + `path_umount()` into `fs/namespace.c` (idempotent, guarded so it never double-applies).

### 4.3 Network & connectivity
| Config | What it gives you |
|---|---|
| `CONFIG_WIREGUARD=y` | WireGuard VPN — uses earth's **in-tree v1.0.0** driver at `drivers/net/wireguard` |
| `CONFIG_IP_NF_TARGET_TTL=y` | IPv4 TTL target — set packet TTL (commonly used so tethered traffic is treated like on-device traffic) |
| `CONFIG_IP6_NF_TARGET_HL=y` | IPv6 hop-limit target — same idea for IPv6 |
| `CONFIG_IP_SET=y` + 16 set types | ipset: bitmap ip/ipmac/port, hash ip/ipmac/ipmark/ipport/ipportip/ipportnet/mac/net/netnet/netport/netportnet/netiface, list:set |
| `CONFIG_NETFILTER_XT_SET=y` | iptables `-m set` match, so ipset rules actually work |
| `CONFIG_TCP_CONG_ADVANCED=y` | Unlocks selectable congestion controls |
| `CONFIG_TCP_CONG_BBR=y` + `CONFIG_DEFAULT_TCP_CONG="bbr"` | BBR as the default — better throughput/latency on lossy mobile links |
| `CONFIG_NET_SCH_FQ=y` | FQ qdisc, the pacing qdisc BBR wants |
| Extra congestion algos | CUBIC, VEGAS, VENO, YEAH, ILLINOIS, LP, SCALABLE, HTCP, WESTWOOD |

### 4.4 CPU, scheduling & I/O
| Config | Effect |
|---|---|
| `CONFIG_CPU_FREQ_DEFAULT_GOV_SCHEDUTIL=y` | schedutil default — EAS-aware, best battery/perf balance |
| `CONFIG_CPU_FREQ_GOV_PERFORMANCE=y` | performance governor available |
| `CONFIG_CPU_FREQ_GOV_CONSERVATIVE=y` | conservative governor available |
| `CONFIG_IOSCHED_BFQ=y` + `CONFIG_BFQ_GROUP_IOSCHED=y` | BFQ I/O scheduler with cgroup support — smoother under heavy I/O |
| `CONFIG_MQ_IOSCHED_KYBER=y`, `CONFIG_MQ_IOSCHED_DEADLINE=y` | blk-mq schedulers for UFS/eMMC |
| `CONFIG_NO_HZ_IDLE=y` | tickless idle — fewer wakeups, better idle battery |
| `CONFIG_HZ_250=y` | 250 Hz tick — lower overhead than 1000 Hz |
| `CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE=y` | `-O2` rather than size optimisation |

### 4.5 Memory & ZRAM
| Config | Effect |
|---|---|
| `CONFIG_ZRAM=y`, `CONFIG_ZSMALLOC=y` | compressed RAM swap |
| `CONFIG_CRYPTO_LZ4=y`, `CONFIG_CRYPTO_ZSTD=y`, `CONFIG_CRYPTO_LZO=y` | fast (LZ4) / high-ratio (ZSTD) ZRAM compressors |
| `CONFIG_SWAP=y` | swap support |
| `CONFIG_KSM=y` | kernel samepage merging — dedupes identical pages |
| `CONFIG_ZSWAP=y` + `CONFIG_Z3FOLD=y` + `CONFIG_ZBUD=y` | compressed swap cache with both allocators |
| `CONFIG_FRONTSWAP=y`, `CONFIG_CLEANCACHE=y` | required backend for zswap/z3fold + clean page cache offload |

### 4.6 Filesystems
| Config | Effect |
|---|---|
| `CONFIG_NETWORK_FILESYSTEMS=y` | unlocks network fs menu |
| `CONFIG_CIFS=y` | mount SMB/Windows/NAS shares |
| already stock | exFAT, NTFS (read/write), EROFS |

### 4.7 SUSFS — honest status: **present but inactive**
The workflow copies SUSFS sources and sets `CONFIG_KSU_SUSFS*`, but SUSFS also requires the KernelSU-side patch (`10_enable_susfs_for_ksu.patch`). That patch targets **original KernelSU's** file layout, not KernelSU-Next, so it is not applied. Consequently:

- Kconfig drops the `KSU_SUSFS` options (the symbols don't exist on KernelSU-Next `legacy`)
- **SUSFS hiding features do not work** on this build
- **KernelSU root itself works normally**

This is documented in the workflow rather than half-ported, because a partial port produces undefined-symbol link failures. If you want real SUSFS, it needs a deliberate port of the SUSFS Kconfig + `susfs.o` build gate + `susfs_is_current_ksu_domain()` / `susfs_is_current_zygote_domain()` definitions into KernelSU-Next.

Also note `CONFIG_KSU_SUSFS_SUS_SU=n` — SUS_SU is unsupported on non-GKI kernels.

---

## 5. Bugs found and fixed along the way

| Bug | Cause | Fix |
|---|---|---|
| `ld.lld: undefined symbol: path_umount` | KSU-Next calls a 5.9 API absent in 4.19 | Backported `can_umount()` + `path_umount()` into `fs/namespace.c` |
| `ld.lld: duplicate symbol: wg_*` (every WireGuard symbol) | earth already ships WireGuard in-tree; a second copy was added at `net/wireguard`, building the driver twice | Removed the redundant `wireguard-linux-compat` copy; `CONFIG_WIREGUARD=y` enables the in-tree driver |
| Wrong KSU hook symbol | `KSU_KPROBES_HOOK` typo / wrong mode selected | Corrected to manual hook mode |
| AnyKernel3 device check | template still listed maguro/toro/toroplus/tuna | `device.nameN` set for earth |
| Node.js 20 deprecation warning | `actions/upload-artifact@v4` targets node20 | Bumped to `@v7` (native node24) — annotations now empty |
| Silent "exit code 2" failures | build errors were swallowed | `set -o pipefail` + `tee` + `::error` annotations surfacing real compiler/linker messages |

---

## 6. Build provenance

| Run | Branch | Purpose | Result |
|---|---|---|---|
| #3 · 46072259352 | main | `path_umount` fix | ✅ success |
| #9 · 46084306419 | feature branch | feature pack, WireGuard fix | ✅ success (14m25s) |
| #10 · 46085612591 | main | post-merge verification | ✅ success |
| #11 · 46109516160 | feature branch | upload-artifact v7 | ✅ success, 0 warnings |
| #12 · 46111066184 | main | current post-merge build | latest |

Merged pull requests: **#1** (`path_umount`), **#2** (feature packs + WireGuard fix), **#3** (upload-artifact bump).

Every feature config listed above was validated with `kconfiglib` against the real earth defconfig — all resolve to `y` (dependencies like `FRONTSWAP` for zswap and `NETWORK_FILESYSTEMS` for CIFS were added explicitly so nothing silently dropped out).

---

## 7. Quick sanity checks after flashing

```bash
adb shell uname -r          # expect 4.19.325…
adb shell getprop ro.product.device   # expect earth
```
Then open the KernelSU-Next manager: it should show **Working**. Grant an app root and confirm with:
```bash
adb shell su -c id          # expect uid=0(root)
```
