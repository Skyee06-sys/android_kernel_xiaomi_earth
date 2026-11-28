# ❌ Disabled & declined — with reasons 🐧

A feature list is only honest if it says what is **not** there and why. Nothing
below was skipped by accident.

> 🎯 **Rule:** stability over feature count. A feature that cannot work, cannot be
> verified, or trades stability for a benchmark number does not go in.

---

## 🚫 Broken in this kernel tree

| Feature | Reason | Could it be fixed? |
|---|---|---|
| **NFS_FS / NFS_V3 / NFS_V4 / NFSD** | `fs/nfs/client.c:625` sets `rpc_clnt.cl_softerr`, but this tree's `include/linux/sunrpc/clnt.h` has **no such member**. `fs/nfs/client.o` fails to compile. | Yes, but it needs a **SUNRPC backport** — invasive and out of scope for a stability-first release. |

This was discovered by build **#13 failing**, not by reading a feature list.

---

## 🚫 Not present in Linux 4.19 / this tree

| Feature | Status | Why not backported |
|---|---|---|
| **MGLRU** (multi-gen LRU) | Absent (`lru_gen` count 0) | Large, invasive MM rewrite. Belongs in a separate experimental branch, never the stable build. |
| **DAMON** | `mm/damon` absent | Data-access monitoring framework; substantial backport, no clear win here. |
| **BBR2 / BBRplus** | Only BBR v1 in tree | Copying newer TCP code blindly is explicitly out of scope. BBR v1 + FQ is enabled and now the default. |
| **NTFS3** | `fs/ntfs3` absent | In-tree **NTFS read/write** + exFAT already cover the use case. |
| **sdfat** | `fs/sdfat` absent | Same — exFAT is already working. |
| **alucard / darkness / impulse** governors | Not in tree | Would need porting; not added to lengthen a feature list. `schedutil` + performance + conservative are present. |
| **NET_SCH_ETS**, **HID_UHID** | Absent | Verified unavailable during evaluation. |
| **SUS_OVERLAYFS** | Not on 4.19 | SUSFS feature requires newer kernel infrastructure. |

---

## 🚫 Wrong hardware or wrong kernel model

| Feature | Reason |
|---|---|
| **WALT** scheduler | **Qualcomm-only.** This is a MediaTek MT6768 device. Porting it would be meaningless at best. |
| **KSU_SUSFS_SUS_SU** | Needs **kprobe** hooking. This is a **non-GKI 4.19** kernel where that is not supported. Module knobs `sus_su` / `sus_su_active` must stay off. |
| **KSU_SUSFS_HAS_MAGIC_MOUNT** | KernelSU-Next `legacy` does not use magic mount. |
| **KSU_KPROBES_HOOK** | Manual hooks used instead — kprobes not viable here. |
| **KCAL**, sound control, vibration control, charging control | **No verified hardware support** on this panel/PMIC path. Claiming they work would be dishonest. |
| **GPU overclock** | Not required, and Mali DVFS stability matters more than a peak number. |
| **avc_log_spoofing**, **emulate_vold_app_data** (module knobs) | **Absent from SUSFS v1.5.5 kernel-4.19 source.** The module exposes the toggles but there is no kernel code to answer them. Found by reading the source. |

---

## 🚫 Conflicts with Android

| Feature | Reason |
|---|---|
| **simple_lmk** | Conflicts with Android's own **`lmkd`**. Two low-memory killers fighting produces worse behaviour, not better. |
| **SCHED_AUTOGROUP** | Desktop/TTY-oriented: it groups tasks by session. On Android it can lump apps together and **hurt** responsiveness. Available, evaluated, declined. |

---

## 🚫 Debug-only, or needs a debug interface we keep off

| Feature | Reason |
|---|---|
| **ZRAM_MEMORY_TRACKING** | Depends on **`DEBUG_FS`**, which stays off to avoid exposing kernel internals. It's a debugging aid, not a user feature. |
| **F2FS_CHECK_FS** | Runtime consistency checks — real overhead, no user benefit for daily use. |
| **DEBUG_FS** | Kept off deliberately. Note: `SCHEDSTATS` needs `DEBUG_KERNEL` + `PROC_FS`, **not** debugfs, so monitoring was added without it. |
| **LTO_CLANG**, **CFI_CLANG**, **SHADOW_CALL_STACK** | Present in the stock defconfig but dropped by Kconfig in this toolchain configuration. Not re-enabled; they were a source of verifier false-failures. |

---

## ⏸️ Available but deferred to a separate experimental build

These **are** in the tree and validated as available. They are held back because
they change behaviour and must not ride along in a stable kernel.

| Feature | Why deferred |
|---|---|
| **BLK_WBT / BLK_WBT_MQ** | Writeback throttling changes I/O behaviour. Could reduce latency spikes — but needs independent testing before it touches the stable build. |
| **F2FS_FS_COMPRESSION** | Present in this tree. Needs userspace/mount support; enabling the config alone does not compress existing data. Experimental. |
| **Game controllers** — `JOYSTICK_XPAD`(+FF/LEDS), `INPUT_JOYDEV`, `HID_SONY`, `HID_MICROSOFT`, `HID_NINTENDO`, `HID_LOGITECH`(+HIDPP), `HID_STEAM`, `HID_BETOP_FF` | All verified **available** and low-risk. Evaluated and offered; **not requested**, so not added. |
| **USB serial** — `CH341`, `CP210X`, `FTDI_SIO`, `PL2303` | Available; useful for OTG hardware work. Not requested. |
| **SECURITY_YAMA** | ptrace restrictions could break root/debug tooling. Needs an explicit decision. |

---

## ✅ Already enabled in stock — deliberately untouched

Re-adding these would be noise. They were verified present and left alone:

`PSI`, `UCLAMP_TASK`, `UCLAMP_TASK_GROUP`, `CGROUPS`, `CGROUP_SCHED`,
`CPU_FREQ_DEFAULT_GOV_SCHEDUTIL`, `CPU_FREQ_STAT`, `SND_USB_AUDIO`,
`TCP_CONG_BIC`, `NET_SCH_FQ`, `NET_SCH_HTB`, `IOSCHED_CFQ`, `IOSCHED_NOOP`,
`FUSE_FS`, `OVERLAY_FS`, exFAT, NTFS-RW, EROFS, F2FS (+encryption),
`SWAP`, `ZRAM` + `ZRAM_WRITEBACK`, `PM_DEVFREQ`, `SECURITYFS`, `IP_SET`,
`NETWORK_FILESYSTEMS`, `VFAT_FS`, `NLS_CODEPAGE_437`, `NO_HZ_IDLE`, `HZ_250`,
`WIREGUARD` (in-tree v1.0.0).

---

## 🧪 Experimental isolation

The SUSFS build is a **separate workflow**, **separate ZIP**, **separate tag**,
marked **pre-release**, and **manual-trigger only**. It can never leak into the
stable kernel. Invasive work (MGLRU, LTO_CLANG, MM backports) would follow the
same rule: test independently, revert on failure, never merge until proven.

⬅️ [Back to changelog](../CHANGELOG.md)
