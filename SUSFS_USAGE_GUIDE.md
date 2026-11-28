# How to Use the SUSFS Experimental Kernel — earth (Redmi 12C / POCO C55)

## The key thing to understand

SUSFS is **two halves**. Flashing the kernel is only half of it:

| Half | What it is | Status |
|---|---|---|
| **Kernel side** | The SUSFS code compiled into your kernel | ✅ Done — that's the experimental ZIP |
| **Userspace side** | The `ksu_susfs` tool + boot scripts that actually tell SUSFS *what* to hide | ❌ You must install this separately |

Without the userspace module, SUSFS is loaded but **hides nothing** — it has no list of paths/mounts to hide. That's why the module is required.

Your kernel ships **SUSFS v1.5.5**; the module requires **1.5.2 or later** → compatible.

**Confirm it yourself:** each release includes `REVISIONS.txt`, which now records
`susfs_version=`, `susfs_remote=` (GitLab upstream or the GitHub mirror used),
`susfs_sha=` and the `sus_su` state. Open it before installing the module:
<https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/download/earth-susfs-4/REVISIONS.txt>
If it reports anything below 1.5.2, use an older module build instead.

---

## What you need

1. **Experimental kernel ZIP**
   <https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/tag/earth-susfs-4>
2. **KernelSU-Next manager v3.4.2**
   <https://github.com/KernelSU-Next/KernelSU-Next/releases/download/v3.4.2/KernelSU_Next_v3.4.2_33355-release.apk>
3. **SUSFS userspace module** — `ksu_module_susfs_1.5.2+.zip` (v1.5.2+ R28, ~890 KB)
   <https://github.com/sidex15/susfs4ksu-module/releases/latest>

---

## Install order (do it in this order)

### Step 0 — Prove the stable kernel works first
Flash `Earth-Lineage24-KSUNext.zip` (stable) and use it for a while. If the stable one misbehaves, the experimental one will too, and you'll waste time debugging the wrong thing.

### Step 1 — Back up
In TWRP/OrangeFox: **Backup → Boot (and DTBO) → swipe.** This is your undo button. Do not skip it.

### Step 2 — Flash the experimental kernel
Recovery → **Install** → `Earth-Lineage24-KSUNext-SUSFS-EXPERIMENTAL.zip` → swipe → **Reboot to System**.
No cache wipe needed. Never wipe Data.

### Step 3 — Install / open the manager
Install the KernelSU-Next manager APK. Open it — it must say **Working**.
If it says "Not installed", stop and restore your Boot backup.

### Step 4 — Install the SUSFS module
Manager → **Modules** → **Install from storage** → pick `ksu_module_susfs_1.5.2+.zip` → wait for it to finish.

### Step 5 — Reboot
The module applies its hiding rules during boot (`post-fs-data.sh` / `service.sh`). **A reboot is mandatory** — installing it is not enough.

### Step 6 — Verify it's actually alive
With a terminal (Termux) or `adb shell`:

```bash
su
dmesg | grep -i susfs
```

You should see SUSFS initialise and log its version. If there is **nothing**, SUSFS is not running — check the module is enabled and that you flashed the *experimental* kernel, not the stable one.

Also useful:
```bash
su -c "ls /data/adb/ksu/bin/ | grep susfs"   # the ksu_susfs helper should exist
uname -r                                    # 4.19.325…
```

---

## Configuring what gets hidden

The module's settings live in its `config.sh`, and it has an **Action button** in the manager's module list. Its real defaults are:

| Setting | Default | What it does | Supported by your kernel? |
|---|---|---|---|
| `susfs_log` | `1` | SUSFS logging | ✅ `ENABLE_LOG=y` |
| `hide_sus_mnts_for_all_or_non_su_procs` | `1` | Hide suspicious mounts | ✅ `SUS_MOUNT=y` |
| `auto_try_umount` | `0` | Auto-umount suspicious mounts for apps | ✅ `TRY_UMOUNT=y` |
| `spoof_uname` | `0` | Fake `uname -r` / `uname -v` | ✅ `SPOOF_UNAME=y` |
| `kernel_version` / `kernel_build` | `default` | The values to spoof uname to | ✅ |
| `spoof_cmdline` | `0` | Spoof `/proc/cmdline` | ✅ `SPOOF_CMDLINE_OR_BOOTCONFIG=y` |
| `hide_cusrom`, `hide_gapps`, `hide_revanced`, `hide_loops` | `0` | Hide specific paths | ✅ `SUS_PATH=y` |
| `sus_su`, `sus_su_active` | `2` (off) | SUS_SU alternative root | ❌ **Not supported — leave off** |

**`sus_su` must stay disabled.** Your kernel is built with `CONFIG_KSU_SUSFS_SUS_SU=n` because SUS_SU needs kprobe hooking, which this non-GKI 4.19 kernel doesn't support. Enabling it in the module will not work.

The module also reads lists you can edit: `sus_path.txt`, `sus_mount.txt`, `sus_kstat_statically.json`, `sus_maps.txt`, `sus_open_redirect.txt` — these map to the `SUS_PATH`, `SUS_MOUNT`, `SUS_KSTAT` and `OPEN_REDIRECT` features your kernel has enabled.

Start with the defaults. Change one thing at a time and reboot, so you know what caused any problem.

---

## Testing whether hiding works

1. Install a root-detection app (e.g. a banking app you use, or a root checker).
2. In the manager, make sure that app is **not** granted root.
3. Run it. With SUSFS + the module active it should not detect root.
4. Optional extras that pair well: **Shamiko v1.2.1+**, **HideMyApplist**. These are optional, not required.

Be realistic: no hiding solution defeats every detector. Play Integrity / hardware attestation is a separate problem that SUSFS does not solve.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `dmesg` shows no SUSFS lines | Stable kernel flashed instead of experimental, or module disabled | Reflash experimental ZIP; enable module; reboot |
| Manager says "Not installed" | Kernel didn't boot from the flashed image | Restore Boot backup |
| Bootloop after flashing | Kernel/device mismatch | Hold Power+Vol Up → recovery → restore Boot backup |
| Bootloop after installing module | A hiding rule broke something | Recovery → delete `/data/adb/modules/susfs4ksu` (or use recovery's module manager) → reboot |
| Apps crash / storage weirdness | `SUS_PATH` or `auto_try_umount` too aggressive | Turn that setting back to `0`, reboot |
| `sus_su` does nothing | Expected | Not supported on non-GKI; leave off |

### Rollback (full)
Recovery → **Restore** → your Boot backup → reboot. You're back to your previous kernel.
Then, if needed, remove the module from `/data/adb/modules/`.

---

## Honest limits

- The kernel side is **compiled and symbol-verified in CI**. That proves the code is in the image; it does **not** prove runtime hiding. Step 6 above is how *you* verify it on the device.
- This build is marked **pre-release** deliberately. Treat it as a test build.
- SUS_SU is unsupported on this kernel and stays off.
- Nothing here is flashed automatically — every step above is yours to run.
