#!/usr/bin/env python3
"""
Port SUSFS (kernel-4.19 branch, v1.5.5) onto LineageOS earth 4.19.325 with
KernelSU-Next 'legacy'.

Why this script exists
----------------------
susfs4ksu ships two patches:
  * 50_add_susfs_in_kernel-4.19.patch  -> kernel side (fs/, include/, kernel/)
  * 10_enable_susfs_for_ksu.patch      -> KernelSU side

Neither applies cleanly here:
  1. The kernel patch fails 4 hunks on earth because earth carries the
     fs_context backport (vfs_create_mount(fc) instead of vfs_kern_mount(name))
     and its struct vfsmount / task_struct KABI layout differs.
  2. The KernelSU patch targets *original* KernelSU's flat layout
     (kernel/ksu.c, kernel/core_hook.c, ...). KernelSU-Next legacy is modular
     (kernel/core/, kernel/selinux/, kernel/feature/, ...) and contains no SUSFS
     support at all, so that patch is not usable.

This script applies the kernel patch, then repairs the rejected hunks with
exact, single-match anchors, and provides the small KernelSU-side glue that
SUSFS needs. Every edit is idempotent and asserts its anchor, so a drift in
upstream fails loudly instead of silently producing a half-patched tree.

Usage (from the kernel root, after KernelSU-Next is cloned into ./KernelSU-Next):
    python3 scripts/port_susfs.py --susfs /path/to/susfs4ksu

Exit code is non-zero if anything could not be applied.
"""

import argparse
import pathlib
import re
import shutil
import subprocess
import sys

KSU = pathlib.Path("KernelSU-Next/kernel")

# ---------------------------------------------------------------- helpers


def read(p):
    return pathlib.Path(p).read_text()


def write(p, s):
    pathlib.Path(p).write_text(s)


def replace_once(path, old, new, label):
    """Replace exactly one occurrence. Idempotent: no-op if already applied."""
    s = read(path)
    if new in s:
        print(f"  = {label} (already applied)")
        return
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"ANCHOR ERROR [{label}] in {path}: expected 1 match, found {n}")
    write(path, s.replace(old, new, 1))
    print(f"  + {label}")


def append_if_missing(path, marker, block, label):
    s = read(path)
    if marker in s:
        print(f"  = {label} (already applied)")
        return
    write(path, s.rstrip("\n") + "\n\n" + block)
    print(f"  + {label}")


# ---------------------------------------------------------------- kernel side

MOUNT_H_OLD = """	ANDROID_KABI_RESERVE(4);
} __randomize_layout;"""

MOUNT_H_NEW = """#ifdef CONFIG_KSU_SUSFS
	ANDROID_KABI_USE(4, u64 susfs_mnt_id_backup);
#else
	ANDROID_KABI_RESERVE(4);
#endif
} __randomize_layout;"""

SCHED_H_OLD = "	ANDROID_KABI_RESERVE(8);"
SCHED_H_NEW = """#ifdef CONFIG_KSU_SUSFS
	ANDROID_KABI_USE(8, u64 susfs_last_fake_mnt_id);
#else
	ANDROID_KABI_RESERVE(8);
#endif"""

# namespace.c hunk #1: includes, externs, IDAs, clone flags, auto-add switches.
NS_HEADER = """
#if defined(CONFIG_KSU_SUSFS_SUS_MOUNT) || defined(CONFIG_KSU_SUSFS_TRY_UMOUNT)
#include <linux/susfs_def.h>
#endif

#ifdef CONFIG_KSU_SUSFS_SUS_MOUNT
extern bool susfs_is_current_ksu_domain(void);
extern bool susfs_is_current_zygote_domain(void);

static DEFINE_IDA(susfs_mnt_id_ida);
static DEFINE_IDA(susfs_mnt_group_ida);

#define CL_ZYGOTE_COPY_MNT_NS BIT(24) /* used by copy_mnt_ns() */
#define CL_COPY_MNT_NS BIT(25) /* used by copy_mnt_ns() */
#endif

#ifdef CONFIG_KSU_SUSFS_AUTO_ADD_SUS_KSU_DEFAULT_MOUNT
extern void susfs_auto_add_sus_ksu_default_mount(const char __user *to_pathname);
bool susfs_is_auto_add_sus_ksu_default_mount_enabled = true;
#endif
#ifdef CONFIG_KSU_SUSFS_AUTO_ADD_SUS_BIND_MOUNT
extern int susfs_auto_add_sus_bind_mount(const char *pathname, struct path *path_target);
bool susfs_is_auto_add_sus_bind_mount_enabled = true;
#endif
#ifdef CONFIG_KSU_SUSFS_AUTO_ADD_TRY_UMOUNT_FOR_BIND_MOUNT
extern void susfs_auto_add_try_umount_for_bind_mount(struct path *path);
bool susfs_is_auto_add_try_umount_for_bind_mount_enabled = true;
#endif
"""

# namespace.c hunk #7 adapted: earth uses vfs_create_mount(fs_context *fc).
NS_ALLOC_OLD = '	mnt = alloc_vfsmnt(fc->source ?: "none");'
NS_ALLOC_NEW = """#ifdef CONFIG_KSU_SUSFS_SUS_MOUNT
	// For newly created mounts, the only caller process we care about is KSU
	if (unlikely(susfs_is_current_ksu_domain())) {
		mnt = alloc_vfsmnt(fc->source ?: "none", true, 0);
		goto bypass_orig_flow;
	}
	mnt = alloc_vfsmnt(fc->source ?: "none", false, 0);
bypass_orig_flow:
#else
	mnt = alloc_vfsmnt(fc->source ?: "none");
#endif"""

# namespace.c hunk #9: clone_mnt() domain-aware allocation.
NS_CLONE_OLD = "	mnt = alloc_vfsmnt(old->mnt_devname);"
NS_CLONE_NEW = """#ifdef CONFIG_KSU_SUSFS_SUS_MOUNT
	bool is_current_ksu_domain = susfs_is_current_ksu_domain();
	bool is_current_zygote_domain = susfs_is_current_zygote_domain();

	// KSU process: single clone gets a new sus mnt_id; unshare spoofs the old id
	if (unlikely(is_current_ksu_domain)) {
		if (!(flag & CL_COPY_MNT_NS)) {
			mnt = alloc_vfsmnt(old->mnt_devname, true, 0);
			goto bypass_orig_flow;
		}
		mnt = alloc_vfsmnt(old->mnt_devname, true, old->mnt_id);
		if (mnt) {
			mnt->mnt.susfs_mnt_id_backup = DEFAULT_SUS_MNT_ID_FOR_KSU_PROC_UNSHARE;
		}
		goto bypass_orig_flow;
	}
	// zygote process cloning an already-sus mount
	if (likely(is_current_zygote_domain) && (old->mnt_id >= DEFAULT_SUS_MNT_ID)) {
		mnt = alloc_vfsmnt(old->mnt_devname, true, 0);
		goto bypass_orig_flow;
	}
	// any other process doing unshare, only for old sus mounts
	if ((flag & CL_COPY_MNT_NS) && (old->mnt_id >= DEFAULT_SUS_MNT_ID)) {
		mnt = alloc_vfsmnt(old->mnt_devname, true, 0);
		goto bypass_orig_flow;
	}
	mnt = alloc_vfsmnt(old->mnt_devname, false, 0);
bypass_orig_flow:
#else
	mnt = alloc_vfsmnt(old->mnt_devname);
#endif"""

# hunk #10 applied with fuzz upstream and lost the CL_ZYGOTE_COPY_MNT_NS guard.
# Restore the faithful version so zygote unshare does not double-renumber.
NS_REORDER_OLD = """#ifdef CONFIG_KSU_SUSFS_SUS_MOUNT
	// If caller process is zygote, then it is a normal mount, so we just reorder the mnt_id
	if (susfs_is_current_zygote_domain()) {
		mnt->mnt.susfs_mnt_id_backup = mnt->mnt_id;
		mnt->mnt_id = current->susfs_last_fake_mnt_id++;
	}
#endif"""

NS_REORDER_NEW = """#ifdef CONFIG_KSU_SUSFS_SUS_MOUNT
	// If caller process is zygote and not doing unshare, just reorder the mnt_id
	if (likely(is_current_zygote_domain) && !(flag & CL_ZYGOTE_COPY_MNT_NS)) {
		mnt->mnt.susfs_mnt_id_backup = mnt->mnt_id;
		mnt->mnt_id = current->susfs_last_fake_mnt_id++;
	}
#endif"""

TASK_MMU_OLD = "#include <linux/pkeys.h>"
TASK_MMU_NEW = """#include <linux/pkeys.h>
#ifdef CONFIG_KSU_SUSFS_SUS_KSTAT
#include <linux/susfs_def.h>
#endif"""


def patch_kernel(susfs: pathlib.Path):
    print("[1/3] copying SUSFS sources")
    shutil.copy(susfs / "kernel_patches/fs/susfs.c", "fs/susfs.c")
    for h in ("susfs.h", "susfs_def.h"):
        shutil.copy(susfs / f"kernel_patches/include/linux/{h}", f"include/linux/{h}")
    # sus_su.c is deliberately not copied: SUS_SU is unsupported on non-GKI.
    print("  + fs/susfs.c, include/linux/susfs.h, include/linux/susfs_def.h")

    print("[2/3] applying upstream kernel patch (rejects repaired next)")
    patch = susfs / "kernel_patches/50_add_susfs_in_kernel-4.19.patch"
    r = subprocess.run(["patch", "-p1", "--forward", "-i", str(patch)],
                       capture_output=True, text=True)
    print(r.stdout[-2500:] if r.stdout else "")
    rejects = sorted(str(p) for p in pathlib.Path(".").rglob("*.rej"))
    print(f"  rejected hunks left in: {rejects}")

    print("[3/3] repairing rejected hunks with exact anchors")
    replace_once("include/linux/mount.h", MOUNT_H_OLD, MOUNT_H_NEW, "vfsmount.susfs_mnt_id_backup")
    replace_once("include/linux/sched.h", SCHED_H_OLD, SCHED_H_NEW, "task_struct.susfs_last_fake_mnt_id")
    replace_once("fs/proc/task_mmu.c", TASK_MMU_OLD, TASK_MMU_NEW, "task_mmu susfs_def include")

    ns = read("fs/namespace.c")
    if "susfs_mnt_id_ida" in ns and "static DEFINE_IDA(susfs_mnt_id_ida)" not in ns:
        replace_once("fs/namespace.c", '#include "internal.h"\n',
                     '#include "internal.h"\n' + NS_HEADER, "namespace.c SUSFS header block")
    else:
        print("  = namespace.c SUSFS header block (already applied)")
    replace_once("fs/namespace.c", NS_ALLOC_OLD, NS_ALLOC_NEW, "vfs_create_mount SUSFS alloc")
    replace_once("fs/namespace.c", NS_CLONE_OLD, NS_CLONE_NEW, "clone_mnt SUSFS alloc")
    if NS_REORDER_OLD in read("fs/namespace.c"):
        replace_once("fs/namespace.c", NS_REORDER_OLD, NS_REORDER_NEW, "clone_mnt zygote reorder guard")

    for p in pathlib.Path(".").rglob("*.rej"):
        p.unlink()
    for p in pathlib.Path(".").rglob("*.orig"):
        p.unlink()
    print("  cleaned .rej/.orig")


# ---------------------------------------------------------------- KernelSU side

SUSFS_KCONFIG = """menu "KernelSU - SUSFS"

config KSU_SUSFS
	bool "KernelSU addon - SUSFS"
	depends on KSU
	default y
	help
	  Enable SUSFS support (ported to KernelSU-Next legacy for earth 4.19).

config KSU_SUSFS_HAS_MAGIC_MOUNT
	bool "KernelSU repo has magic mount implemented"
	depends on KSU_SUSFS
	default n
	help
	  KernelSU-Next legacy does not use 5ec1cff's magic mount workdir layout,
	  so this stays off.

config KSU_SUSFS_SUS_PATH
	bool "Hide suspicious paths"
	depends on KSU_SUSFS
	default y
	help
	  Hide user-defined paths from various syscalls. Costs some performance.

config KSU_SUSFS_SUS_MOUNT
	bool "Hide suspicious mounts"
	depends on KSU_SUSFS
	default y

config KSU_SUSFS_AUTO_ADD_SUS_KSU_DEFAULT_MOUNT
	bool "Auto-hide KSU default mounts"
	depends on KSU_SUSFS_SUS_MOUNT
	default y

config KSU_SUSFS_AUTO_ADD_SUS_BIND_MOUNT
	bool "Auto-hide bind mounts"
	depends on KSU_SUSFS_SUS_MOUNT
	default y

config KSU_SUSFS_SUS_KSTAT
	bool "Spoof suspicious kstat"
	depends on KSU_SUSFS
	default y

config KSU_SUSFS_SUS_OVERLAYFS
	bool "Spoof overlayfs"
	depends on KSU_SUSFS
	default n

config KSU_SUSFS_TRY_UMOUNT
	bool "Try umount suspicious mounts"
	depends on KSU_SUSFS
	default y

config KSU_SUSFS_AUTO_ADD_TRY_UMOUNT_FOR_BIND_MOUNT
	bool "Auto add try-umount for bind mounts"
	depends on KSU_SUSFS_TRY_UMOUNT
	default y

config KSU_SUSFS_SPOOF_UNAME
	bool "Spoof uname"
	depends on KSU_SUSFS
	default y

config KSU_SUSFS_ENABLE_LOG
	bool "Enable SUSFS logging"
	depends on KSU_SUSFS
	default y
	help
	  Kept on so SUSFS operation can be verified in dmesg.

config KSU_SUSFS_HIDE_KSU_SUSFS_SYMBOLS
	bool "Hide KSU/SUSFS kernel symbols"
	depends on KSU_SUSFS
	default y

config KSU_SUSFS_OPEN_REDIRECT
	bool "Redirect open() paths"
	depends on KSU_SUSFS
	default y

config KSU_SUSFS_SPOOF_CMDLINE_OR_BOOTCONFIG
	bool "Spoof /proc/cmdline and bootconfig"
	depends on KSU_SUSFS
	default y

config KSU_SUSFS_SUS_SU
	bool "SUS_SU (unsupported on non-GKI)"
	depends on KSU_SUSFS
	default n
	help
	  Requires kprobe-based hooking; not supported on this non-GKI kernel.

endmenu
"""

SELINUX_H_DECL = """
#ifdef CONFIG_KSU_SUSFS
/* SUSFS domain helpers, implemented on top of Next's cached SIDs. */
bool susfs_is_current_ksu_domain(void);
bool susfs_is_current_zygote_domain(void);
bool susfs_is_current_init_domain(void);
#endif
"""

SELINUX_C_IMPL = """
#ifdef CONFIG_KSU_SUSFS
/*
 * SUSFS asks "is the current task in the ksu / zygote / init SELinux domain?".
 * KernelSU-Next legacy already caches those SIDs in cache_sid(), so reuse the
 * existing predicates instead of duplicating SID lookup code.
 */
bool susfs_is_current_ksu_domain(void)
{
	return is_ksu_domain();
}

bool susfs_is_current_zygote_domain(void)
{
	return is_zygote(current_cred());
}

bool susfs_is_current_init_domain(void)
{
	return is_init(current_cred());
}
#endif
"""

TRY_UMOUNT_IMPL = """
#ifdef CONFIG_KSU_SUSFS
/*
 * SUSFS calls this 4-argument form. Next legacy's internal try_umount() takes
 * (mnt, flags); expose a compatible wrapper. 'check_mnt' reproduces the
 * root-mountpoint check, 'uid' is accepted for API compatibility.
 */
void ksu_try_umount(const char *mnt, bool check_mnt, int flags, uid_t uid)
{
	struct path path;
	int err;

	(void)uid;
	err = kern_path(mnt, 0, &path);
	if (err)
		return;

	if (check_mnt && path.dentry != path.mnt->mnt_root) {
		path_put(&path);
		return;
	}

	ksu_umount_mnt(mnt, &path, flags);
}
#endif
"""


def patch_kernelsu():
    print("[KSU] adding SUSFS Kconfig")
    append_if_missing(KSU / "Kconfig", "config KSU_SUSFS", SUSFS_KCONFIG, "KSU_SUSFS Kconfig menu")

    print("[KSU] adding SUSFS domain helpers")
    append_if_missing(KSU / "selinux/selinux.h", "susfs_is_current_ksu_domain",
                      SELINUX_H_DECL, "selinux.h declarations")
    # keep the declarations inside the include guard
    h = read(KSU / "selinux/selinux.h")
    if h.rstrip().endswith("#endif") and "susfs_is_current_ksu_domain" in h:
        body = h.rstrip()
        idx = body.rfind("#endif")
        if body.find("susfs_is_current_ksu_domain") > idx:
            fixed = body[:idx] + SELINUX_H_DECL + "\n#endif\n"
            write(KSU / "selinux/selinux.h", fixed)
            print("  + moved declarations inside include guard")
    append_if_missing(KSU / "selinux/selinux.c", "bool susfs_is_current_ksu_domain(void)",
                      SELINUX_C_IMPL, "selinux.c definitions")

    print("[KSU] adding ksu_try_umount wrapper")
    append_if_missing(KSU / "feature/kernel_umount.c", "void ksu_try_umount(",
                      TRY_UMOUNT_IMPL, "ksu_try_umount")

    print("[KSU] calling susfs_init() during init")
    init_c = KSU / "core/init.c"
    s = read(init_c)
    if "susfs_init()" not in s:
        m = re.search(r"int __init kernelsu_init\(void\)\s*\{", s)
        if not m:
            raise SystemExit("ANCHOR ERROR: kernelsu_init() not found in core/init.c")
        inject = (m.group(0)
                  + "\n#ifdef CONFIG_KSU_SUSFS\n\textern void susfs_init(void);\n\tsusfs_init();\n#endif\n")
        write(init_c, s[:m.start()] + inject + s[m.end():])
        print("  + susfs_init() call")
    else:
        print("  = susfs_init() (already applied)")


# ---------------------------------------------------------------- verification


def verify():
    print("[verify] checking the ported tree is self-consistent")
    checks = [
        ("fs/susfs.c", "void susfs_init(void)"),
        ("fs/Makefile", "obj-$(CONFIG_KSU_SUSFS) += susfs.o"),
        ("include/linux/mount.h", "susfs_mnt_id_backup"),
        ("include/linux/sched.h", "susfs_last_fake_mnt_id"),
        ("fs/namespace.c", "static DEFINE_IDA(susfs_mnt_id_ida)"),
        ("fs/namespace.c", "bypass_orig_flow"),
        ("fs/namespace.c", "CL_ZYGOTE_COPY_MNT_NS"),
        (str(KSU / "Kconfig"), "config KSU_SUSFS"),
        (str(KSU / "selinux/selinux.c"), "bool susfs_is_current_ksu_domain(void)"),
        (str(KSU / "feature/kernel_umount.c"), "void ksu_try_umount("),
        (str(KSU / "core/init.c"), "susfs_init()"),
    ]
    bad = []
    for path, needle in checks:
        ok = needle in read(path)
        print(f"  {'OK  ' if ok else 'FAIL'} {path}: {needle}")
        if not ok:
            bad.append((path, needle))
    # Every 1-arg alloc_vfsmnt call must live in the "#else" (SUSFS-disabled)
    # branch; a 1-arg call on the SUSFS-enabled path would be a compile error.
    ns = read("fs/namespace.c")
    stale = []
    for m in re.finditer(r"alloc_vfsmnt\([^,()]*\);", ns):
        preceding = ns[max(0, m.start() - 120):m.start()]
        if "#else" not in preceding:
            stale.append(m.group(0))
    three_arg = len(re.findall(r"alloc_vfsmnt\([^;]*,[^;]*,[^;]*\)", ns))
    if stale:
        print(f"  FAIL 1-arg alloc_vfsmnt on the SUSFS path: {stale}")
        bad.append(("fs/namespace.c", str(stale)))
    elif three_arg < 5:
        print(f"  FAIL expected SUSFS-aware alloc_vfsmnt calls, found {three_arg}")
        bad.append(("fs/namespace.c", "3-arg alloc_vfsmnt"))
    else:
        print(f"  OK   alloc_vfsmnt: {three_arg} SUSFS-aware calls, "
              "1-arg calls only in #else fallbacks")
    if bad:
        raise SystemExit(f"SUSFS port incomplete: {bad}")
    print("SUSFS port applied and self-consistent.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--susfs", required=True, help="path to susfs4ksu checkout")
    a = ap.parse_args()
    susfs = pathlib.Path(a.susfs)
    if not (susfs / "kernel_patches/fs/susfs.c").exists():
        raise SystemExit(f"{susfs} does not look like susfs4ksu")
    if not KSU.exists():
        raise SystemExit(f"{KSU} missing - clone KernelSU-Next legacy first")
    patch_kernel(susfs)
    patch_kernelsu()
    verify()


if __name__ == "__main__":
    main()
