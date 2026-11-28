# Final Kernel Report — Redmi 12C / POCO C55 (earth)

**Device:** Xiaomi Redmi 12C / POCO C55 · **SoC:** MediaTek MT6768 (Helio G85) · **Arch:** ARM64
**Kernel:** Linux 4.19.325 · **ROM:** LineageOS 24.0 · **Root:** KernelSU-Next `legacy`
**Build:** GitHub Actions only (no PC required) · **Repo:** `Skyee06-sys/android_kernel_xiaomi_earth` · **main:** `90d089e`

---

## 0. What you actually get — two separate builds

| | **STABLE** (recommended daily driver) | **SUSFS EXPERIMENTAL** |
|---|---|---|
| Workflow | `blank.yml` (auto on push to main + manual) | `susfs.yml` (**manual dispatch only**) |
| Artifact | `Earth-Lineage24-KSUNext` | `Earth-Lineage24-KSUNext-SUSFS-EXPERIMENTAL` |
| Verified run | **#20** on `main` — success | **#4** (`46123981627`) — success |
| ZIP size | 17,271,577 B | 17,281,274 B |
| SUSFS | not included, not claimed | ported, compiled, symbol-verified |
| Annotations | **zero** | **zero** |

Both contain the same Tier A improvements. The only difference is SUSFS.
**Start with STABLE.** Move to EXPERIMENTAL only after the stable one boots and behaves.

**Direct downloads (public, no sign-in):**
- STABLE: <https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/download/earth-stable-20/Earth-Lineage24-KSUNext.zip>
- SUSFS EXPERIMENTAL: <https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/download/earth-susfs-4/Earth-Lineage24-KSUNext-SUSFS-EXPERIMENTAL.zip>

Release pages: [earth-stable-20](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/tag/earth-stable-20) ·
[earth-susfs-4](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/tag/earth-susfs-4)

Each release also carries `REVISIONS.txt` (exact source SHAs, and for SUSFS the
`susfs_version`) and `build-config.txt` (the full `.config` actually built).
Superseded releases were removed; the tags remain for provenance.

---

## 1. Step 1 — Source audit (before changing anything)

Findings that changed the plan:

1. **SUSFS was never functional.** KernelSU-Next `legacy` contains **zero** SUSFS files and **no** `KSU_SUSFS` Kconfig symbols upstream (verified against the branch tree). The old workflow copied susfs4ksu sources and ran `patch … || true`, which silently left a half-applied tree. The artifact name advertised SUSFS anyway. Both problems are fixed.
2. **The upstream SUSFS KernelSU patch is unusable here.** `10_enable_susfs_for_ksu.patch` targets *original* KernelSU's flat layout (`kernel/ksu.c`, `kernel/core_hook.c`, …). Next-legacy is modular (`kernel/core/`, `kernel/selinux/`, `kernel/feature/`, `kernel/runtime/`, …).
3. **The upstream kernel patch rejects 4 hunks on earth**, because earth carries the `fs_context` backport (`vfs_create_mount(fc)` instead of `vfs_kern_mount(name)`) and has a different KABI layout.
4. **NFS is broken in this tree.** `fs/nfs/client.c:625` sets `rpc_clnt.cl_softerr`, but `include/linux/sunrpc/clnt.h` has no such member. Latent, because NFS has never been built here.
5. **Already enabled — left untouched:** `PSI` (+ `PSI_DEFAULT_DISABLED=n`), `UCLAMP_TASK`, `UCLAMP_TASK_GROUP`, `CGROUPS`, `CGROUP_SCHED`, all CPU governors, `TCP_CONG_BIC`, `NET_SCH_HTB`, `IOSCHED_CFQ`, `IOSCHED_NOOP`, `FUSE_FS`, `OVERLAY_FS`, exFAT, NTFS-RW, EROFS, F2FS (+encryption), ZRAM + ZRAM_WRITEBACK.
6. **Platform:** `MACH_MT6768=y` builds `drivers/devfreq/helio-dvfsrc-v2/` (DDR DVFS) — but **no devfreq governor was enabled**. GPU is Mali Valhall r32p1 via `MTK_GPU_COMMON_DVFS_SUPPORT`. Thermal used only the backward-compatible governor.

Every configuration claim below was checked with **kconfiglib** against the real `earth_defconfig`, then proven by CI.

---

## 2. Step 2 — SUSFS + KernelSU-Next (highest priority)

### Root integration (unchanged, working)
`CONFIG_KSU=y`, `CONFIG_KSU_MANUAL_HOOK=y`, `CONFIG_KSU_KPROBES_HOOK=n`, with five manual hooks:

| Kernel function | File | Hook |
|---|---|---|
| `do_execveat_common` | `fs/exec.c` | `ksu_handle_execveat` / `_sucompat` |
| `do_faccessat` | `fs/open.c` | `ksu_handle_faccessat` |
| `vfs_read` | `fs/read_write.c` | `ksu_handle_vfs_read` |
| `vfs_statx` | `fs/stat.c` | `ksu_handle_stat` |
| `SYSCALL_DEFINE4(reboot…)` | `kernel/reboot.c` | `ksu_handle_sys_reboot` |

Plus the `can_umount()` / `path_umount()` backport (5.9 API absent in 4.19).

### The SUSFS port — `scripts/port_susfs.py`
Idempotent, anchor-asserting, self-verifying. It:

**Kernel side**
- copies `fs/susfs.c`, `include/linux/susfs.h`, `susfs_def.h` (deliberately **not** `sus_su.c`)
- applies the upstream 4.19 patch, then repairs **every** rejected hunk with single-match anchors:
  - `vfsmount.susfs_mnt_id_backup` via `ANDROID_KABI_USE(4, …)`
  - `task_struct.susfs_last_fake_mnt_id` via `ANDROID_KABI_USE(8, …)`
  - `fs/proc/task_mmu.c` include
  - `fs/namespace.c` SUSFS header block (externs, IDAs, `CL_COPY_MNT_NS` / `CL_ZYGOTE_COPY_MNT_NS`, auto-add switches)
  - `vfs_create_mount()` SUSFS-aware `alloc_vfsmnt()` — **adapted to earth's `fs_context` form**
  - `clone_mnt()` domain-aware allocation
  - restores the `CL_ZYGOTE_COPY_MNT_NS` guard that a fuzzed upstream hunk had dropped
- reconciles the API name: the patch calls `susfs_try_umount_all()`, v1.5.5's `susfs.c` provides `susfs_try_umount()` with identical semantics → the call site is pointed at the API that exists (no invented alias)

**KernelSU side**
- adds the `KSU_SUSFS` Kconfig menu
- implements `susfs_is_current_ksu_domain()` / `_zygote_domain()` / `_init_domain()` **on top of Next's existing cached SIDs** (`cache_sid()`, `is_ksu_domain()`, `is_zygote()`, `is_init()`) instead of duplicating SID lookup
- adds a 4-argument `ksu_try_umount()` wrapper over Next's internal umount path
- calls `susfs_init()` from `kernelsu_init()`

**Local safety net:** `check_symbols()` scans every `susfs_`/`ksu_` call in the patched tree and fails if any lacks a definition. A full sweep confirms **all 27** referenced functions resolve — this is why the second CI attempt linked instead of revealing one missing symbol per run.

### Enabled SUSFS features
`KSU_SUSFS`, `SUS_PATH`, `SUS_MOUNT`, `AUTO_ADD_SUS_KSU_DEFAULT_MOUNT`, `AUTO_ADD_SUS_BIND_MOUNT`, `SUS_KSTAT`, `TRY_UMOUNT`, `AUTO_ADD_TRY_UMOUNT_FOR_BIND_MOUNT`, `SPOOF_UNAME`, `ENABLE_LOG`, `HIDE_KSU_SUSFS_SYMBOLS`, `OPEN_REDIRECT`, `SPOOF_CMDLINE_OR_BOOTCONFIG` — all verified `=y` in the final `.config`.

### Conflicts checked
- `SUS_SU=n` — requires kprobe hooking, unsupported on this non-GKI kernel. Its code is `#ifdef`-guarded, so no undefined symbols.
- `HAS_MAGIC_MOUNT=n` — Next-legacy does not use the magic-mount workdir layout.
- `SUS_OVERLAYFS=n` — upstream default; not needed here.
- KernelSU root paths are untouched; SUSFS hooks are additive and `#ifdef`-guarded.

> **Honest limit:** SUSFS is now *compiled in and symbol-verified*. That is not the same as proven runtime hiding. Confirm on-device with `dmesg | grep -i susfs` (logging is enabled for exactly this reason) before trusting it.

---

## 3. Step 3 — Tier A (all validated `=y`, then proven by a green build)

**A. DDR devfreq** — `SIMPLE_ONDEMAND`, `PERFORMANCE`, `POWERSAVE`, `USERSPACE`, `PASSIVE`.
Real on this SoC: `MACH_MT6768=y` builds `helio-dvfsrc-v2`. **No frequencies are forced** — the driver's own OPP table is respected; governors only choose among existing OPPs.

**B. Thermal** — `STEP_WISE`, `FAIR_SHARE`, `BANG_BANG`, `USER_SPACE`, `POWER_ALLOCATOR`, `THERMAL_WRITABLE_TRIPS`, `DEVFREQ_THERMAL`, `THERMAL_STATISTICS`.
**Hardware protection preserved:** `MTK_LEGACY_THERMAL` and the stock default governor stay on; no cooling device, trip point or throttle was removed. We only add governor *choices*.

**C. Networking** — `CAKE`, `FQ_CODEL`, `PIE`, `CODEL`, `NETEM`, `HFSC`, `PRIO`, `SFQ`, `TBF`, `INGRESS`, `MQPRIO`; TCP `DCTCP`, `HSTCP`, `HYBLA`, `NV`, `CDG`. Existing `FQ`, `HTB`, `BIC` kept; **BBR remains the default**.

**D. Firewall** — `NF_TABLES` + `NF_TABLES_INET`, `NFT_COMPAT`, `NFT_NAT/MASQ/REDIR/CT/COUNTER/LOG/LIMIT/REJECT`, `IP6_NF_NAT`, `IP6_NF_TARGET_MASQUERADE`, `NF_NAT_IPV6`, `NETFILTER_XT_TARGET_TEE`.
`NFT_COMPAT` is deliberate: it keeps Android's existing iptables/netd rules working alongside nftables.

**E. Filesystems** — `SQUASHFS` (+XZ/LZ4/ZSTD), `XFS_FS`, `BTRFS_FS`, `HFSPLUS_FS`, `UDF_FS`, `JFS_FS`. Existing exFAT/NTFS-RW/EROFS/F2FS/CIFS untouched.

**F. Misc** — `KERNEL_LZ4` (faster boot decompression). PSI / UCLAMP / CPU governors were already on and were left alone.

---

## 4. Step 4 — Tier B: evaluated individually, each with a decision

| Feature | Present in tree? | Decision | Reason |
|---|---|---|---|
| **MGLRU** | ✗ no `lru_gen` in `mm/vmscan.c` | **Not added** | Invasive MM rewrite; needs a large backport. Cannot validate runtime behaviour without a device. Stability first. |
| **DAMON** | ✗ no `mm/damon/` | **Not added** | Large subsystem backport; monitoring value only, no user-facing gain. |
| **simple_lmk** | ✗ absent | **Not added** | Would compete with Android's own `lmkd`. Conflicting memory killers cause app kills/instability. |
| **BBR2 / BBRplus** | ✗ only BBR v1 | **Not added** | Not in this tree; copying newer TCP code blindly is explicitly out of scope. BBR v1 + FQ already enabled. |
| **NTFS3** | ✗ absent (`fs/ntfs` only) | **Not added** | 5.15+ driver. In-tree NTFS with read/write already covers the use case. |
| **sdfat** | ✗ absent (`fs/exfat` present) | **Not added** | exFAT already works; a second FAT driver adds risk, not capability. |
| **Alucard / Darkness / Impulse** | ✗ only the standard governors | **Not added** | Would each need importing. schedutil (EAS-aware) + uclamp is the correct modern choice for MT6768; extra governors would be feature-count padding. |
| **KCAL** | needs MTK display patch | **Not added** | No upstream support in this display driver; a wrong patch breaks the panel. |
| **Sound control** | needs MTK audio patch | **Not added** | Device-specific; risk of audio path breakage. |
| **Vibration control** | needs vibrator patch | **Not added** | Device-specific, no safe generic implementation. |
| **Charging control** | needs MTK charger patch | **Not added** | Highest hardware risk of the list (battery/charging safety). Not attempted without hardware documentation. |
| **GPU OC** | Mali Valhall r32p1 DVFS | **Not added** (not requested) | Stability and thermals prioritised. DDR governors already help frame pacing. |
| **WALT** | Qualcomm-only | **Not applicable** | Wrong vendor for MT6768. Explicitly not attempted. |
| **NFS / NFSD** | present but **broken** | **Disabled** | `rpc_clnt.cl_softerr` missing → `fs/nfs/client.o` fails to compile (caught by CI run 46114067461). Adding just the field would make `SOFTERR` silently ineffective; a real fix needs a SUNRPC backport. |
| **ZRAM_MEMORY_TRACKING** | present | **Disabled** | Depends on `DEBUG_FS`, kept off to avoid exposing kernel internals. Debug aid, not a user feature. |
| **9P_FS** | present | **Disabled** | virtio/Plan9 transport — no use on a phone. |
| **LTO_CLANG / CFI_CLANG / SHADOW_CALL_STACK** | not supported in this tree/config | **Left off** | Stock defconfig requests some of these but Kconfig drops them. Not forced. |
| **SUS_SU** | guarded | **Disabled** | Needs kprobes; unsupported on non-GKI. |

---

## 5. Step 5 — Performance & battery rationale

The goal was real behaviour, not benchmark scores:

- **Frame-time stability:** DDR devfreq governors let memory bandwidth scale with load instead of sitting at a fixed point; BFQ + uclamp reduce I/O and scheduling jitter.
- **Gaming:** `performance` DDR/CPU governors are *available* when you want them, but **nothing is pinned to maximum by default**. schedutil stays the default CPU governor.
- **Thermals:** `power_allocator` gives a PID power-budget approach for sustained load rather than harsh step throttling. All hardware protections remain.
- **Multitasking / memory:** ZRAM (LZ4/ZSTD) + zswap/z3fold + KSM were already present and are kept; PSI and uclamp were already active.
- **Network latency:** BBR + FQ default, with CAKE/FQ_CODEL available to fight bufferbloat.
- **Battery:** `NO_HZ_IDLE`, `HZ_250`, schedutil, DDR `powersave`/`passive` options; no forced maximum frequencies anywhere.

---

## 6. Step 6 — Experimental isolation

- SUSFS lives **only** in `susfs.yml`, `workflow_dispatch` only. It cannot run on push and cannot affect the stable release.
- Its artifact is explicitly named `…-SUSFS-EXPERIMENTAL`.
- The stable `blank.yml` contains **no** SUSFS sources, configs or claims.
- MGLRU, LTO and other invasive backports were **not** attempted, per your stability requirement.
- Every change is a separate commit and the port script is idempotent, so any piece is reversible.

---

## 7. Step 7 — Build system

- Fully automated on GitHub Actions; no PC needed.
- ARM64: `clang` + `ld.lld` + LLVM tools, AOSP GCC 4.9 `aarch64-linux-android-` / `arm-linux-androideabi-` binutils, `ARCH=arm64`, `earth_defconfig`, target `Image.gz-dtb`.
- **Errors are never hidden:** `set -o pipefail`, full log via `tee`, and `::error` annotations extracting the real compiler/linker lines. No `|| true` on the build.
- **Reproducibility:** `REVISIONS.txt` records kernel SHA, KernelSU-Next SHA, SUSFS SHA, workflow SHA, kernel version and UTC build time. The exact `build-config.txt` ships with the artifact.
- Config requests are recorded to a file so verification checks *our* options, not unrelated stock entries Kconfig legitimately drops.

---

## 8. Step 8 — Verification (what was actually proven)

The verification step asserts, and fails the job if any check fails:

1. `Image.gz-dtb` exists and is non-empty.
2. `llvm-readelf -h out/vmlinux` reports **AArch64**.
3. **Every requested CONFIG** is `=y` in the final `out/.config` (SUSFS enforced in the experimental build).
4. **Required symbols present in `System.map`:** `path_umount`, `ksu_handle_execveat`, `ksu_handle_faccessat`, `ksu_handle_vfs_read`, `ksu_handle_sys_reboot`, `wg_socket_init` — plus, for SUSFS: `susfs_init`, `susfs_is_current_ksu_domain`, `susfs_is_current_zygote_domain`, `ksu_try_umount`, `susfs_try_umount`.
5. Package contents checked: the zip must contain `Image.gz-dtb`; device names printed.

**Results:** stable **#15**, **#16**, **#18**, **#19**, **#20** all success with zero annotations. SUSFS **#2** and **#4** success with zero annotations.

> **A successful compilation does not prove the kernel boots.** No runtime claim is made for either build. Nothing was flashed, and nothing will be flashed without your approval.

---

## 9. Step 9 — Flashable package & installation

**Package:** AnyKernel3 zip containing `Image.gz-dtb` (+ `dtbo.img` when produced). AnyKernel3 patches your **existing boot image** — it does not overwrite unrelated partitions.
**Device lock:** `device.name1=earth`, `device.name2=aether` (POCO C55); other name slots cleared, so it refuses to flash on the wrong phone.

### Before you start
- Bootloader unlocked, custom recovery (TWRP/OrangeFox) installed.
- **Take a full backup of `boot` (and `dtbo` if present) in recovery first.** This is your rollback.
- Keep a copy of your stock/current `boot.img` somewhere safe.

### TWRP installation
1. Copy the zip to the phone.
2. Reboot to recovery.
3. **Backup → select Boot (and DTBO) → swipe to back up.**
4. **Install →** select `Earth-Lineage24-KSUNext.zip` → swipe to flash.
5. Watch the log: it must report the device as `earth`/`aether` and succeed.
6. Reboot → System. First boot may take a little longer.
7. Install the KernelSU-Next manager and confirm it reports **Working**.

### Cache wiping
**Not required.** This is a kernel-only flash. Do **not** wipe Data. Wiping Dalvik/ART cache is optional and harmless but unnecessary; if you do it, expect slower first app launches while ART recompiles.

### Rollback
- **Recovery:** Restore → your Boot backup → reboot. That fully reverts the kernel.
- **Fastboot (if you have the image):** `fastboot flash boot boot.img` (and `fastboot flash dtbo dtbo.img` if you backed it up).
- **Bootloop:** hold Power+Vol Up to enter recovery, then restore the Boot backup.

### After flashing — sanity checks
```bash
adb shell uname -r                    # expect 4.19.325…
adb shell getprop ro.product.device   # expect earth (or aether for POCO C55)
adb shell su -c id                    # after granting root: uid=0(root)
# EXPERIMENTAL build only:
adb shell su -c "dmesg | grep -i susfs"
```

### KernelSU-Next manager
Latest stable **v3.4.2** (versionCode 33355):
- Standard: <https://github.com/KernelSU-Next/KernelSU-Next/releases/download/v3.4.2/KernelSU_Next_v3.4.2_33355-release.apk>
- Spoofed (disguised name): <https://github.com/KernelSU-Next/KernelSU-Next/releases/download/v3.4.2/KernelSU_Next_v3.4.2-spoofed_33355-release.apk>

The kernel authenticates the manager by signing certificate (size `0x3e6`, SHA-256 `79e5901…21bf7`), so use an official asset — a re-signed mirror APK will be rejected.

---

## 10. Recommended path

1. Flash **STABLE** (`Earth-Lineage24-KSUNext.zip` from release `earth-stable-20`). Use it for a few days.
2. If it is stable and you want root hiding, flash **EXPERIMENTAL** (`earth-susfs-4`), install the
   `sidex15/susfs4ksu-module` userspace module, reboot, then check `dmesg | grep -i susfs`.
   See `SUSFS_USAGE_GUIDE.md` — the kernel alone hides nothing without that module.
3. Report any misbehaviour; each change is isolated and reversible.

**Nothing is flashed automatically. Installation waits for your approval.**
