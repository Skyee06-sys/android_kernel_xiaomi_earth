# How to Use the SUSFS Experimental Kernel — earth (Redmi 12C / POCO C55)

> **Status:** experimental pre-release. The kernel side is compiled and
> symbol-verified in CI; **runtime hiding is not verified** — you verify that on
> the device in Step 6. Nothing here is flashed automatically.

---

## ⚠️ Read this first: will it work on your ROM?

This kernel is built from **LineageOS `lineage-24.0`** kernel source for `earth`
(Linux **4.19.325**, MT6768 / Helio G85). ROM compatibility is decided by the
**vendor/firmware base**, not the ROM's name.

| ROM type | Verdict | Why |
|---|---|---|
| **LineageOS 24.0** (Android 17) | ✅ **Intended target** | Built from its exact kernel source |
| **AOSP ROMs on a lineage-24.0 base** (crDroid, PixelOS, EvolutionX…) | 🟡 **Likely works** | Same device tree + vendor blobs |
| **AOSP ROMs on an older base** (Lineage 21 / 22.1 / 23.0) | 🟠 **Risky** | Vendor expects different kernel interfaces |
| **Stock MIUI** | 🔴 **Not recommended** | MIUI HALs expect Xiaomi kernel nodes this tree doesn't provide |
| **Port ROM** | 🔴 **Depends on the port** | Uses earth's own vendor → maybe; cross-device vendor → no |
| **Other device / mismatched vendor** | 🔴 **No** | DTB and vendor mismatch |

**Pre-flight check** — run in Termux *before* flashing:

```bash
uname -r                              # must be 4.19.x  (if 5.x → STOP, wrong kernel)
getprop ro.build.version.release      # Android version
getprop ro.product.device             # must be earth or aether
getprop ro.vendor.build.fingerprint   # which vendor base you're on
```

The ZIP is locked to `device.name1=earth` / `name2=aether` and will **refuse to
flash** on other devices. That is a safety net, not a bug.

Helpful detail: WiFi (`CONFIG_WLAN_DRV_BUILD_IN=y`) and Mali `r32p1` are **built
into** the kernel, not loadable modules — so they don't depend on vendor `.ko`
files matching. The ZIP ships **no modules**, so it can't clash with vendor ones.

---

## The key thing to understand

SUSFS is **two halves**. Flashing the kernel is only half of it:

| Half | What it is | Status |
|---|---|---|
| **Kernel side** | SUSFS code compiled into the kernel | ✅ Done — the experimental ZIP |
| **Userspace side** | `ksu_susfs` tool + boot scripts that tell SUSFS *what* to hide | ❌ **You must install this separately** |

Without the userspace module, SUSFS is loaded but **hides nothing** — it has an
empty hide-list. That's why the module is required.

Your kernel ships **SUSFS v1.5.5**; the module requires **1.5.2+** → compatible.

**Confirm it yourself:** each release ships `REVISIONS.txt` recording
`susfs_version=`, `susfs_remote=`, `susfs_sha=` and the `sus_su` state:
<https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/download/earth-susfs-4/REVISIONS.txt>
If it ever reports below 1.5.2, use an older module build instead.

---

## What you need

| # | File | Link |
|---|---|---|
| 0 | **Stable kernel** (test this first) | [earth-stable-20](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/tag/earth-stable-20) |
| 1 | **Experimental kernel ZIP** | [earth-susfs-4](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/tag/earth-susfs-4) |
| 2 | **KernelSU-Next manager v3.4.2** | [APK](https://github.com/KernelSU-Next/KernelSU-Next/releases/download/v3.4.2/KernelSU_Next_v3.4.2_33355-release.apk) |
| 3 | **SUSFS module v1.5.2+ R28** (~890 KB) | [ksu_module_susfs_1.5.2+.zip](https://github.com/sidex15/susfs4ksu-module/releases/download/v1.5.2%2B_R28/ksu_module_susfs_1.5.2%2B.zip) |

**Pin the module version.** Use the R28 link above rather than `/releases/latest`
— a future module may require a newer SUSFS than this kernel's v1.5.5.

**Manager variants:** there is also a `-spoofed` APK (renamed package, harder to
detect by package name). Either works; the kernel authenticates the manager by its
**signing certificate**, not its package name. Don't install both.

---

## Install order (do it in this order)

### Step 0 — Prove the stable kernel works first
Flash **`Earth-Lineage24-KSUNext.zip`** from `earth-stable-20` and use it for a few
days. If the stable build misbehaves, the experimental one will too — and you'd
waste time debugging the wrong thing.

### Step 1 — Back up
TWRP/OrangeFox → **Backup → Boot (and DTBO) → swipe.** This is your undo button.
**Do not skip it.** Keep a copy off the phone if you can.

### Step 2 — Flash the experimental kernel
Recovery → **Install** → `Earth-Lineage24-KSUNext-SUSFS-EXPERIMENTAL.zip` → swipe →
**Reboot to System.** No cache wipe needed. **Never wipe Data.**
It writes only `boot` (and `dtbo` if present) — no other partitions.

### Step 3 — Install / open the manager
Install the manager APK, open it — it must say **Working**.
If it says "Not installed", **stop** and restore your Boot backup.

### Step 4 — Install the SUSFS module
Manager → **Modules** → **Install from storage** → `ksu_module_susfs_1.5.2+.zip` →
wait for it to finish. Leave the module **enabled**.

### Step 5 — Reboot ← mandatory
The module applies its rules during boot (`post-fs-data.sh`, `post-mount.sh`,
`service.sh`, `boot-completed.sh`). Installing it is **not** enough.

### Step 6 — Verify it's actually alive
In Termux (or `adb shell`):

```bash
su
dmesg | grep -i susfs          # should show SUSFS init + version
ls /data/adb/ksu/bin/ | grep -i susfs   # ksu_susfs helper should exist
uname -r                       # 4.19.325…
```

**No `dmesg` output = SUSFS is not running.** Usual causes: you flashed the
*stable* ZIP by mistake, or the module is disabled. Re-check and reboot.

---

## Configuring what gets hidden

### The easy way — WebUI ✅
The R28 module ships a **WebUI** (`webroot/index.html`, plus `status.html` and
`custom.html`). In the KernelSU-Next manager, open the module and tap its
**WebUI / settings** entry. You get toggles and a status page instead of editing
shell scripts. **Use this** — it's safer than hand-editing `config.sh`.

There's also an **Action** button in the module list that re-applies settings.

### The manual way — `config.sh`
Located at `/data/adb/modules/susfs4ksu/config.sh`. These are the **real R28
defaults**, mapped to what this kernel actually supports:

| Setting | Default | What it does | Kernel support |
|---|---|---|---|
| `susfs_log` | `1` | SUSFS logging | ✅ `ENABLE_LOG=y` |
| `hide_sus_mnts_for_all_or_non_su_procs` | `1` | Hide suspicious mounts | ✅ `SUS_MOUNT=y` |
| `auto_try_umount` | `0` | Auto-umount for apps | ✅ `TRY_UMOUNT=y` |
| `umount_for_zygote_iso_service` | `0` | Umount for isolated zygote services | ✅ `TRY_UMOUNT=y` |
| `skip_legit_mounts` | `0` | Keep mounts listed in `legit_mounts.txt` | ✅ `SUS_MOUNT=y` |
| `spoof_uname` | `0` | Fake `uname -r` / `-v` | ✅ `SPOOF_UNAME=y` |
| `kernel_version` / `kernel_build` | `'default'` | Values to spoof uname to | ✅ |
| `spoof_cmdline` | `0` | Spoof `/proc/cmdline` | ✅ `SPOOF_CMDLINE_OR_BOOTCONFIG=y` |
| `hide_cusrom` | `0` | Hide custom-ROM traces | ✅ `SUS_PATH=y` |
| `hide_vendor_sepolicy` | `0` | Hide vendor sepolicy traces | ✅ `SUS_PATH=y` |
| `hide_compat_matrix` | `0` | Hide compatibility-matrix traces | ✅ `SUS_PATH=y` |
| `hide_gapps` | `0` | Hide GApps traces | ✅ `SUS_PATH=y` |
| `hide_revanced` | `0` | Hide ReVanced traces | ✅ `SUS_PATH=y` |
| `hide_loops` | `0` | Hide loop devices | ✅ `SUS_PATH=y` |
| `force_hide_lsposed` | `0` | Hide LSPosed | ✅ `SUS_PATH=y` |
| `disable_webui_bin_update` | `1` | Stop WebUI auto-updating the binary | ➖ module-only |
| **`sus_su` / `sus_su_active`** | `2` (off) | SUS_SU alternative root | ❌ **Unsupported — leave off** |
| **`avc_log_spoofing`** | `0` | Spoof AVC denial logs | ❌ **Not in the 4.19 SUSFS code** |
| **`emulate_vold_app_data`** | `0` | vold app-data emulation | ❌ **Not in the 4.19 SUSFS code** |

**Three knobs do nothing on this kernel — leave them off:**

- **`sus_su`** — built with `CONFIG_KSU_SUSFS_SUS_SU=n`. SUS_SU needs kprobe
  hooking, which this non-GKI 4.19 kernel doesn't support.
- **`avc_log_spoofing`** and **`emulate_vold_app_data`** — verified **absent** from
  the SUSFS v1.5.5 kernel-4.19 source. They're newer-kernel features; the module
  exposes them but there's nothing here to answer them.

### Editable hide-lists
In `/data/adb/modules/susfs4ksu/`, mapped to features this kernel enables:

| File | Kernel feature |
|---|---|
| `sus_path.txt`, `sus_path_loop.txt` | `SUS_PATH` |
| `sus_mount.txt`, `legit_mounts.txt` | `SUS_MOUNT` |
| `try_umount.txt` | `TRY_UMOUNT` |
| `sus_kstat_statically.json` | `SUS_KSTAT` |
| `sus_maps.txt`, `sus_open_redirect.txt` | `OPEN_REDIRECT` |

**Start with defaults.** Change **one** setting at a time and reboot, so you know
what caused any problem.

### What this kernel enables
13 SUSFS options `=y`, 3 deliberately `=n`:

```
=y  KSU_SUSFS, SUS_PATH, SUS_MOUNT, SUS_KSTAT, TRY_UMOUNT,
    AUTO_ADD_SUS_KSU_DEFAULT_MOUNT, AUTO_ADD_SUS_BIND_MOUNT,
    AUTO_ADD_TRY_UMOUNT_FOR_BIND_MOUNT, SPOOF_UNAME, ENABLE_LOG,
    HIDE_KSU_SUSFS_SYMBOLS, OPEN_REDIRECT, SPOOF_CMDLINE_OR_BOOTCONFIG
=n  SUS_SU (no kprobes), SUS_OVERLAYFS (not on 4.19), HAS_MAGIC_MOUNT (KSU-Next legacy)
```

---

## Testing whether hiding works

1. Install a root-detection app (a root checker, or a banking app you use).
2. In the manager, make sure that app is **not** granted root.
3. Run it. With SUSFS + the module active it should not detect root.
4. Optional companions: **Shamiko v1.2.1+**, **HideMyApplist**. Not required.
   For systemless hosts, the module author recommends **bindhosts**.

Be realistic: no hiding solution defeats every detector. **Play Integrity /
hardware attestation is a separate problem that SUSFS does not solve.**

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `dmesg` shows no SUSFS lines | Stable kernel flashed, or module disabled | Reflash experimental ZIP; enable module; reboot |
| Manager says "Not installed" | Kernel didn't boot from the flashed image | Restore Boot backup |
| Bootloop after flashing | Kernel/ROM/vendor mismatch | Power+Vol Up → recovery → restore Boot backup |
| Bootloop after installing module | A hiding rule broke something | Recovery → delete `/data/adb/modules/susfs4ksu` → reboot |
| Apps crash / storage weirdness | `SUS_PATH` or `auto_try_umount` too aggressive | Set that knob back to `0`, reboot |
| WiFi / camera / charging broken | Wrong ROM base (e.g. stock MIUI) | Restore Boot backup; this kernel targets Lineage 24.0 |
| `sus_su`, `avc_log_spoofing`, `emulate_vold_app_data` do nothing | Expected | Unsupported on this kernel — leave off |
| ZIP refuses to flash | Device isn't `earth`/`aether` | Correct — do not force it |

### Rollback (full)
Recovery → **Restore** → your Boot (+DTBO) backup → reboot. You're back to your
previous kernel. Then remove `/data/adb/modules/susfs4ksu` if needed.

---

## Honest limits

- CI proves the SUSFS code is **compiled and linked in** (27/27 symbols resolved,
  13 configs asserted `=y` in the final `.config`). It does **not** prove runtime
  hiding — Step 6 is how *you* verify that.
- **No boot test has been performed on any device.** Compilation ≠ boot proof.
- Marked **pre-release** deliberately. Treat it as a test build.
- Three module knobs are unsupported here, listed above.
- Nothing is flashed automatically — every step is yours to run.

---

## Quick reference

- Releases: <https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases>
- Full kernel report: [`FINAL_KERNEL_REPORT.md`](FINAL_KERNEL_REPORT.md)
- Module settings wiki: <https://github.com/sidex15/susfs4ksu-module/wiki>
- Module source: <https://github.com/sidex15/susfs4ksu-module>
