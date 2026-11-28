# 🐞 Known Issues — earth Kernel

Real, currently-open limitations. Fixed problems live in
[changelog/BUILD-LEDGER.md](changelog/BUILD-LEDGER.md) with their post-mortems.

**Status vocabulary:** `Open` · `By design` · `Unsupported` · `Fixed in <build>`

---

## 🔴 Open — affecting users

### KI-001 · No on-device boot verification

| | |
|---|---|
| **Status** | **Open** |
| **Affects** | Every build, every ROM |
| **Detail** | CI proves compilation, ARM64 image, requested configs in the final `.config`, and required symbols in `System.map`. It cannot prove the kernel boots, nor any performance, battery or thermal behaviour. |
| **Mitigation** | Back up **Boot + DTBO** before flashing. Flash **stable** first. Run `tools/verify_device.sh` and check WiFi, camera, charging, fingerprint, calls. |
| **Why not closed** | Requires physical device testing, which has not been done. |

### KI-002 · NFS / NFSD cannot be enabled

| | |
|---|---|
| **Status** | **Unsupported** (tree defect) |
| **Evidence** | `fs/nfs/client.c:625` assigns `rpc_clnt.cl_softerr`; `include/linux/sunrpc/clnt.h` in this tree has no such member → `fs/nfs/client.o` fails to compile |
| **Discovered** | Build **#13** failed |
| **Workaround** | Use **CIFS/SMB** (enabled) for network shares |
| **Real fix** | A SUNRPC backport — invasive, deliberately out of scope for a stability-first release |

### KI-003 · SUSFS hides nothing without the userspace module

| | |
|---|---|
| **Status** | **By design** |
| **Detail** | The kernel provides the mechanism; the hide-list comes from userspace. Without `sidex15/susfs4ksu-module`, SUSFS initialises with an empty list. |
| **Fix** | Install the module via the manager, then **reboot** (mandatory) |
| **Verify** | `su -c "dmesg \| grep -i susfs"` |

### KI-004 · Three SUSFS module knobs do nothing here

| Knob | Status | Evidence |
|---|---|---|
| `sus_su` / `sus_su_active` | **Unsupported** | `CONFIG_KSU_SUSFS_SUS_SU=n`; needs kprobes on a non-GKI kernel |
| `avc_log_spoofing` | **Unsupported** | Absent from SUSFS v1.5.5 kernel-4.19 source |
| `emulate_vold_app_data` | **Unsupported** | Absent from SUSFS v1.5.5 kernel-4.19 source |

The module exposes these toggles regardless of kernel support. **Leave them off.**

### KI-005 · Play Integrity hardware attestation is not defeated

| | |
|---|---|
| **Status** | **By design / out of scope** |
| **Detail** | SUSFS hides root artefacts from apps. Hardware-backed attestation is a separate mechanism that no hiding configuration addresses. |

### KI-006 · Stock MIUI and cross-device ports are unsupported

| | |
|---|---|
| **Status** | **Unsupported** |
| **Detail** | This is LineageOS's kernel. MIUI HALs expect Xiaomi-specific kernel interfaces this tree does not provide. Likely symptoms: camera, charging or thermal misbehaviour. |
| **See** | [COMPATIBILITY.md](COMPATIBILITY.md) |

---

## 🟢 Addressed in Phase B — build/tooling

> These are implemented in the workflows; confirm in the next build's job summary
> and `REVISIONS.txt` before treating them as closed.

### KI-007 · Toolchain versions are not pinned

| | |
|---|---|
| **Status** | **Addressed in Phase B** — verify in build output |
| **Evidence** | `apt-get install clang` (unversioned); GCC binutils cloned with `-b master` from `android.googlesource.com` |
| **Impact** | Builds are not reproducible over time; an upstream clang bump can break the build without any repo change |
| **Plan** | Pin clang and the toolchain commit in Phase B |

### KI-008 · No build cache

| | |
|---|---|
| **Status** | **Addressed in Phase B** — ccache + actions/cache |
| **Impact** | Every build is a full ~17-minute compile |
| **Plan** | ccache + `actions/cache` |

### KI-009 · No job timeout or concurrency guard

| | |
|---|---|
| **Status** | **Addressed in Phase B** — timeout 60 min + concurrency |
| **Impact** | A hung job can consume the 6-hour default; superseded pushes waste runners |
| **Plan** | `timeout-minutes` + `concurrency` with cancel-in-progress |

### KI-010 · Compiler warnings are not surfaced

| | |
|---|---|
| **Status** | **Addressed in Phase B** — warnings counted and reported |
| **Evidence** | `KCFLAGS="-Wno-error"` |
| **Why it exists** | The MTK vendor tree emits many warnings; `-Werror` would make the build impossible |
| **Problem** | Warning counts are never reported, so a genuine new warning is invisible |
| **Plan** | Keep `-Wno-error` but **count and report** warnings in the job summary |

### KI-011 · No artifact checksums

| | |
|---|---|
| **Status** | **Addressed in Phase B** — SHA256SUMS.txt published |
| **Impact** | Download integrity cannot be verified |
| **Plan** | Publish SHA256 alongside each release asset |

---

## 🟢 By design — not bugs

| Item | Reason |
|---|---|
| **`DEBUG_FS=n`** | Deliberate policy. Consequently `ZRAM_MEMORY_TRACKING` and `ZSMALLOC_STAT` are unavailable — the latter **`select DEBUG_FS`** (`mm/Kconfig:617`) and would force it on plus 14 further debug symbols. |
| **No default-qdisc config** | `NET_SCH_DEFAULT` does not exist in 4.19. Set `net.core.default_qdisc` at runtime instead. |
| **No ZRAM compression config** | `ZRAM_DEF_COMP_*` does not exist in 4.19. Choose via `/sys/block/zram0/comp_algorithm`. |
| **`SECURITY_YAMA=n`** | Held off deliberately until KernelSU-Next, debugger and root-tool compatibility is verified. |
| **`MODULE_SIG=n`** | Enabling it auto-generates a signing key per build, breaking reproducibility, and does nothing without `SIG_FORCE`. |
| **SUSFS build is manual-only** | `workflow_dispatch` exclusively, so experimental code can never enter a stable release automatically. |
| **Uclamp granularity is 5** | Stock default. Raising to 20 is approved for Phase C1, not yet applied. |

---

## ✅ Recently fixed

| Issue | Fixed in | Root cause |
|---|---|---|
| **BBR was not the default** | `earth-stable-22` / `earth-susfs-5` | `CONFIG_DEFAULT_TCP_CONG` is a promptless string derived from a Kconfig choice; assigning it was silently discarded, so `DEFAULT_CUBIC` won. Fixed with `DEFAULT_BBR=y`; verifier now checks string values. |
| `tc` shaping only half-usable | `earth-stable-22` | Qdiscs existed but no classifiers/actions to feed them |
| SUSFS link failure | SUSFS build #2 | Patch called `susfs_try_umount_all`; v1.5.5 defines `susfs_try_umount` |
| Kernel would not link | early builds | `path_umount()` is a 5.9 API absent from 4.19 — backported |
| Duplicate WireGuard symbols | early builds | earth ships WireGuard in-tree; the compat copy compiled it twice |
| Verifier false failures | build #15 | It checked the whole defconfig including symbols Kconfig legitimately drops |

---

## 📣 Reporting a new issue

Please include:
1. Build tag (`earth-stable-NN` / `earth-susfs-N`)
2. `uname -r` and `getprop ro.vendor.build.fingerprint`
3. Output of `sh tools/verify_device.sh`
4. `su -c "dmesg | grep -iE 'BUG:|Oops|WARNING:|panic'"`
5. What you expected vs what happened

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 🔗 Related

[changelog/BUILD-LEDGER.md](changelog/BUILD-LEDGER.md) · [COMPATIBILITY.md](COMPATIBILITY.md) · [SECURITY.md](SECURITY.md) · [CHANGELOG.md](CHANGELOG.md)
