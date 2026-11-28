# 📲 Installation — earth Kernel

Phone-only procedure. No PC required. **Read [COMPATIBILITY.md](COMPATIBILITY.md)
first** — flashing on an unsupported ROM base is the most common failure.

---

## 📥 What to download

| # | File | Where |
|---|---|---|
| 1 | **Stable kernel** `Earth-Lineage24-KSUNext.zip` | [earth-stable-22](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/tag/earth-stable-22) |
| 2 | **KernelSU-Next manager** v3.4.2 | [APK](https://github.com/KernelSU-Next/KernelSU-Next/releases/download/v3.4.2/KernelSU_Next_v3.4.2_33355-release.apk) |
| 3 | *(SUSFS only)* experimental ZIP | [earth-susfs-5](https://github.com/Skyee06-sys/android_kernel_xiaomi_earth/releases/tag/earth-susfs-5) |
| 4 | *(SUSFS only)* userspace module | [ksu_module_susfs_1.5.2+.zip](https://github.com/sidex15/susfs4ksu-module/releases/download/v1.5.2%2B_R28/ksu_module_susfs_1.5.2%2B.zip) |

**Start with stable.** Only move to the SUSFS build after stable has proven itself.

---

## ✅ Pre-flight (2 minutes, do not skip)

In Termux:
```bash
uname -r                              # must be 4.19.x — if 5.x, STOP
getprop ro.product.device             # must be earth or aether
getprop ro.vendor.build.fingerprint   # confirm Lineage-24.0-based vendor
```

| Check | Required |
|---|---|
| Device | `earth` or `aether` — the ZIP refuses anything else |
| Kernel family | **4.19.x** |
| ROM base | LineageOS 24.0 / AOSP on that base |
| Recovery | TWRP or OrangeFox installed and working |
| Storage | ZIP downloaded and reachable from recovery |

---

## 🛡️ Step 1 — Back up (your undo button)

TWRP/OrangeFox → **Backup** → select **Boot** and **DTBO** → swipe.

Copy the backup off the phone if you can. **Without this you have no rollback.**

---

## 🔧 Step 2 — Flash the kernel

1. Reboot to recovery
2. **Install** → select `Earth-Lineage24-KSUNext.zip`
3. Swipe to flash
4. **Reboot → System**

| Question | Answer |
|---|---|
| Wipe cache / Dalvik? | **Not needed** |
| Wipe Data? | 🔴 **Never** |
| Which partitions are written? | `boot`, and `dtbo` only if present |
| Are `system`/`vendor`/`vbmeta` touched? | ❌ No |

First boot may take longer than usual. Be patient before assuming a bootloop.

---

## 🔓 Step 3 — Install the manager

1. Install the KernelSU-Next manager APK
2. Open it — it must say **Working**

| Manager says | Meaning | Action |
|---|---|---|
| **Working** | Kernel side is active | Continue |
| **Not installed** | The flashed kernel is not running | Restore your Boot backup |

The manager is authenticated by its **APK signing certificate**, so the
`-spoofed` variant works too. Do not install both.

---

## 🧪 Step 4 *(SUSFS build only)* — install the module

1. Manager → **Modules** → **Install from storage**
2. Select `ksu_module_susfs_1.5.2+.zip`
3. Leave the module **enabled**
4. **Reboot** ← mandatory; rules are applied during boot
5. Verify:

```bash
su -c "dmesg | grep -i susfs"
su -c "ls /data/adb/ksu/bin/ | grep -i susfs"
```

**No `dmesg` output = SUSFS is not running.** Usually the stable ZIP was flashed
by mistake, or the module is disabled.

Configure it through the module's **WebUI** in the manager rather than editing
`config.sh`. Full detail: [SUSFS_USAGE_GUIDE.md](SUSFS_USAGE_GUIDE.md).

⚠️ Leave `sus_su`, `avc_log_spoofing` and `emulate_vold_app_data` **off** — they are
unsupported on this kernel ([KNOWN_ISSUES.md](KNOWN_ISSUES.md) KI-004).

---

## 🔍 Step 5 — Verify

```bash
sh tools/verify_device.sh
```

Strictly read-only. Or check individually:

```bash
uname -r                                                  # 4.19.325…
cat /proc/sys/net/ipv4/tcp_congestion_control              # bbr
cat /proc/pressure/memory                                  # PSI present
cat /proc/swaps                                            # zram active
su -c "dmesg | grep 'energy model register'"               # EAS initialised
su -c "dmesg | grep -iE 'BUG:|Oops|panic|WARNING:'"        # faults
```

**Then use the phone normally for a few days.** Confirm WiFi, Bluetooth, camera,
charging, fingerprint, calls, and thermals under load.

---

## ⏪ Rollback

### Kernel problems / bootloop
1. Hold **Power + Volume Up** to enter recovery
2. **Restore** → your **Boot** (+ DTBO) backup
3. Reboot

### SUSFS module causes a bootloop
1. Recovery → file manager (or the recovery's module manager)
2. Delete `/data/adb/modules/susfs4ksu`
3. Reboot

### Apps crash or storage behaves oddly (SUSFS)
Set the aggressive knob back to `0` (`auto_try_umount`, `hide_*`) and reboot.
Change one setting at a time.

---

## ❓ Common questions

| Question | Answer |
|---|---|
| Do I need to reflash the ROM? | No — only `boot` is replaced |
| Will my data be wiped? | No |
| Can I go back to stock kernel? | Yes — restore the Boot backup |
| Do I need Magisk too? | No — KernelSU-Next provides root |
| Can I use both ZIPs at once? | No — one kernel at a time; they are alternatives |
| Does stable include SUSFS? | ❌ No, by design |
| Is a cache wipe needed? | No |

---

## ⚠️ Honest reminder

CI proves the kernel compiles and contains what it claims. **It does not prove it
boots on your device.** Treat the first flash as a test and keep that Boot backup.

---

## 🔗 Related

[COMPATIBILITY.md](COMPATIBILITY.md) · [SUSFS_USAGE_GUIDE.md](SUSFS_USAGE_GUIDE.md) · [KNOWN_ISSUES.md](KNOWN_ISSUES.md) · [PERFORMANCE.md](PERFORMANCE.md)
