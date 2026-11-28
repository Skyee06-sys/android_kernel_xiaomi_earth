# 🛡️ Security — earth Kernel

Verified hardening state with source evidence. Nothing here is claimed to make
the device "secure" — it documents which mitigations are actually compiled in.

> Kernel: Linux **4.19.325** arm64 · Device `earth`/`aether` · MT6768
> See [FEATURES.md](FEATURES.md) for the status vocabulary.

---

## ✅ Enabled hardening (verified in the built `.config`)

### Memory-safety and exploitation mitigations

| Mitigation | Config | Purpose | Evidence |
|---|---|---|---|
| **Hardened usercopy** | `HARDENED_USERCOPY=y` | Bounds-checks `copy_to/from_user` against slab object size | `security/Kconfig`, `mm/usercopy.c` |
| **Strong stack protector** | `STACKPROTECTOR=y`, `STACKPROTECTOR_STRONG=y` | Canary on functions with risky locals | `arch/Kconfig` |
| **Virtually mapped stacks** | `VMAP_STACK=y` | Guard pages catch stack overflow | `arch/arm64/Kconfig` |
| **KASLR** | `RANDOMIZE_BASE=y`, `RANDOMIZE_MODULE_REGION_FULL=y` | Randomises kernel/module placement | `arch/arm64/Kconfig` |
| **Zero-on-alloc** | `INIT_ON_ALLOC_DEFAULT_ON=y` | Removes uninitialised-memory leaks | `mm/page_alloc.c`, `mm/slub.c` |
| **Full refcount checks** | `REFCOUNT_FULL=y` | Detects refcount overflow (use-after-free precursor) | `lib/refcount.c` |
| **Panic on data corruption** | `BUG_ON_DATA_CORRUPTION=y` | Stops instead of continuing corrupted | `lib/Kconfig.debug` |
| **List integrity** | `DEBUG_LIST=y` | Detects corrupted linked lists | `lib/list_debug.c` |

### ARM64 architectural protections

| Mitigation | Config | Purpose |
|---|---|---|
| **PAN** | `ARM64_PAN=y` | Kernel cannot accidentally access user memory |
| **UAO** | `ARM64_UAO=y` | Unprivileged access-override for correct uaccess semantics |
| **Software TTBR0 PAN** | `ARM64_SW_TTBR0_PAN=y` | PAN emulation on cores without hardware PAN |
| **KPTI** | `UNMAP_KERNEL_AT_EL0=y` | Meltdown-class isolation |
| **Branch predictor hardening** | `HARDEN_BRANCH_PREDICTOR=y` | Spectre-v2 mitigation |
| **Spectre-BHB mitigation** | `MITIGATE_SPECTRE_BRANCH_HISTORY=y` | Spectre-BHB |

### Access control

| Item | Config | Note |
|---|---|---|
| **SELinux** | `SECURITY_SELINUX=y` | Android's mandatory access control |
| SELinux develop mode | `SECURITY_SELINUX_DEVELOP=y` | Required for Android's `setenforce` handling — **kept**, not a weakening we introduced |
| SELinux AVC stats | `SECURITY_SELINUX_AVC_STATS=y` | Auditing |
| **`/dev/mem` absent** | `DEVMEM=n` | Stronger than `STRICT_DEVMEM`: the interface does not exist at all |
| `/proc/kcore` absent | `PROC_KCORE=n` | No kernel memory dump interface |
| `kexec` absent | `KEXEC=n` | No arbitrary kernel replacement |
| **debugfs off** | `DEBUG_FS=n` | Deliberate policy — reduces exposed kernel internals |

### BPF

| Item | Config | Note |
|---|---|---|
| BPF syscall + JIT | `BPF_SYSCALL=y`, `BPF_JIT=y` | Required by Android |
| **JIT always on** | `BPF_JIT_ALWAYS_ON=y` | Removes the interpreter (a known attack surface) |
| **Unprivileged BPF default-off** | `BPF_UNPRIV_DEFAULT_OFF=y` | ✅ **Enabled in Phase C1** |

---

## ⚠️ Known gaps and what we plan to do

| Gap | Current | Plan | Trade-off |
|---|---|---|---|
| **Usercopy fallback** | ✅ **Fixed in C1:** `HARDENED_USERCOPY_FALLBACK=n` — violations now fail instead of `WARN()` (`security/Kconfig:174-180`) | Done | May surface a latent vendor-driver bug as a crash rather than a warning. Boot testing required. |
| Slab freelist randomisation | ✅ **Enabled in C1** (`SLAB_FREELIST_RANDOM=y`) | Done | Negligible |
| Slab freelist hardening | ✅ **Enabled in C1** (`SLAB_FREELIST_HARDENED=y`) | Done | ~1% slab overhead |
| Compile-time bounds checks | ✅ **Enabled in C1** (`FORTIFY_SOURCE=y`) | Done | Small size increase |

| No ptrace restriction | `SECURITY_YAMA=n` | **Held** — your decision | May break KernelSU-Next, debuggers and root tools. Must be verified first. |
| CFI / LTO / shadow stack | `n` in stable/SUSFS; **`y` in `experimental.yml`** with `CFI_PERMISSIVE=y` | Isolated experiment, manual-only pre-release | High risk of breaking MTK vendor drivers; excluded from stable until boot + runtime testing pass |
| Modules unsigned | `MODULE_SIG=n` | **Declined** | Enabling auto-generates a random key per build (`MODULE_SIG_ALL=y`), breaking reproducibility, and is pointless without `SIG_FORCE` |
| Zero-on-free | `INIT_ON_FREE_DEFAULT_ON=n` | **Declined** | Clears memory on every free — measurable cost, unclear gain given zero-on-alloc is already on |

---

## 🔓 Root attack surface — stated plainly

- **KernelSU-Next** grants root by design. Root is an intentional, large increase
  in privilege; no kernel hardening option removes that.
- **SUSFS** (experimental build only) *hides* root from apps. Hiding is **not**
  a security boundary — it changes what apps can observe, not what root can do.
- `SUS_SU` is **Unsupported** here (needs kprobes on a non-GKI kernel).
- No hiding configuration defeats **Play Integrity hardware attestation**.
- `SECURITY_SELINUX_DEVELOP=y` is stock and required by Android; it is not a
  weakening introduced by this project.

---

## 🧪 Verifying on device

```bash
# Confirm the running kernel and root state
uname -r
su -c "dmesg | grep -iE 'BUG:|Oops|kernel panic|WARNING:'" | tail

# Hardening side effects would show as usercopy/slab warnings — check after boot
su -c "dmesg | grep -i 'usercopy'"
```

`tools/verify_device.sh` includes a fault scan. It is strictly read-only.

---

## 📏 Reporting a security issue

See [CONTRIBUTING.md](CONTRIBUTING.md). Do not open a public issue with a working
exploit; describe impact and affected build instead.

---

## 🔗 Related

[FEATURES.md](FEATURES.md) · [KERNEL_CONFIG.md](KERNEL_CONFIG.md) · [KNOWN_ISSUES.md](KNOWN_ISSUES.md) · [SUSFS_USAGE_GUIDE.md](SUSFS_USAGE_GUIDE.md)
