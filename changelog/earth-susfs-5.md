# 🧪 earth-susfs-5

[![Pre-release](https://img.shields.io/badge/release-pre--release-orange)](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/tag/earth-susfs-5)
![Kernel](https://img.shields.io/badge/kernel-4.19.325-blue)
![SUSFS](https://img.shields.io/badge/SUSFS-v1.5.5-purple)

**Experimental.** Everything in [`earth-stable-22`](earth-stable-22.md) **plus**
SUSFS v1.5.5. Flash the stable build first and live with it before trying this.

| | |
|---|---|
| 📦 **Release** | <https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/tag/earth-susfs-5> |
| 🏗️ **CI run** | [#5 · 46137717612](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/actions/runs/46137717612) — ✅ success, **0 annotations** |
| 📏 **ZIP size** | 17,305,967 B |
| 🔖 **Source** | `2fc7655` |
| 📅 **Built** | 2026-11-28 |
| 🔁 **Trigger** | **manual only** (`workflow_dispatch`) — never auto-built |

---

## 🧩 SUSFS needs TWO halves

| Half | What it does | Where |
|---|---|---|
| **Kernel** | The SUSFS code | ✅ inside this ZIP |
| **Userspace module** | Tells SUSFS *what* to hide | ❌ **install separately** |

**Without the module, SUSFS hides nothing** — it has an empty hide-list.

| Component | Version | Compatible? |
|---|---|---|
| Kernel SUSFS | **v1.5.5** | — |
| Module requirement | **≥1.5.2** | ✅ yes |
| Recommended module | [`v1.5.2+_R28`](https://github.com/sidex15/susfs4ksu-module/releases/download/v1.5.2%2B_R28/ksu_module_susfs_1.5.2%2B.zip) | ✅ pin this version |

 Confirm from the release's `REVISIONS.txt` (480 B) — it records
`susfs_version=`, `susfs_remote=`, `susfs_sha=` and `sus_su=disabled`.

---

## ✅ Enabled SUSFS options (13)

```
KSU_SUSFS                          SUS_PATH
SUS_MOUNT                          SUS_KSTAT
TRY_UMOUNT                         SPOOF_UNAME
ENABLE_LOG                         OPEN_REDIRECT
SPOOF_CMDLINE_OR_BOOTCONFIG        HIDE_KSU_SUSFS_SYMBOLS
AUTO_ADD_SUS_KSU_DEFAULT_MOUNT     AUTO_ADD_SUS_BIND_MOUNT
AUTO_ADD_TRY_UMOUNT_FOR_BIND_MOUNT
```

## ❌ Disabled SUSFS options (3) — with reasons

| Option | Why off |
|---|---|
| `SUS_SU` | Needs **kprobe** hooking — unsupported on this non-GKI 4.19 kernel |
| `SUS_OVERLAYFS` | Not available on 4.19 |
| `HAS_MAGIC_MOUNT` | KernelSU-Next `legacy` does not use magic mount |

### Module knobs that do nothing here — leave them off

| Knob | Reason |
|---|---|
| `sus_su` / `sus_su_active` | `CONFIG_KSU_SUSFS_SUS_SU=n` |
| `avc_log_spoofing` | **Absent** from SUSFS v1.5.5 kernel-4.19 source |
| `emulate_vold_app_data` | **Absent** from SUSFS v1.5.5 kernel-4.19 source |

The last two were found by reading the kernel source, not assumed — the module
exposes the toggles but there is no kernel code to answer them.

---

## 🆕 Also new in this build

Identical to [stable-22](earth-stable-22.md):
🐛 BBR now genuinely default · ✨ `tc` classifiers/actions · ✨ per-app firewall +
TPROXY · ✨ monitoring (`CPU_FREQ_TIMES`, TASKSTATS, SCHEDSTATS).

---

## 📊 What was verified

| Check | Result |
|---|---|
| Requested `=y` symbols | **161/161** (145 base + 16 SUSFS-related) |
| String options | `DEFAULT_TCP_CONG="bbr"` confirmed |
| SUSFS symbols | `susfs_init`, `susfs_is_current_ksu_domain`, `susfs_is_current_zygote_domain`, `ksu_try_umount`, `susfs_try_umount` |
| Local symbol resolution | **27/27** via `check_symbols()` before CI |
| CI annotations | **0** |

`build-config.txt` = 152,043 B (the full `.config` actually built).

---

## 📲 Install order

1. Prove **stable-22** works first
2. **Back up Boot + DTBO** in TWRP
3. Flash `Earth-Lineage24-KSUNext-SUSFS-EXPERIMENTAL.zip` → reboot
4. Manager must say **Working**
5. Manager → Modules → Install from storage → `ksu_module_susfs_1.5.2+.zip`
6. **Reboot** ← mandatory, rules apply at boot
7. Verify:

```bash
su -c "dmesg | grep -i susfs"
su -c "ls /data/adb/ksu/bin/ | grep -i susfs"
```

**No `dmesg` output = SUSFS is not running.** Usually means the stable ZIP was
flashed by mistake, or the module is disabled.

⚙️ Configure via the module's **WebUI** in the manager (R28 ships
`webroot/index.html`) rather than editing `config.sh` by hand.

📖 Full walkthrough: [SUSFS_USAGE_GUIDE.md](../SUSFS_USAGE_GUIDE.md)

---

## ⚠️ Honest limits

- CI proves SUSFS is **compiled and linked in**. It does **not** prove runtime
  hiding — step 7 is how *you* verify that on the device.
- Marked **pre-release** deliberately.
- No hiding setup defeats Play Integrity **hardware attestation**; that is a
  separate problem SUSFS does not solve.
- Nothing is flashed automatically.

⬅️ [Back to changelog](../CHANGELOG.md)
