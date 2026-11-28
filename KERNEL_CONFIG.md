# ⚙️ Kernel Configuration — before / after

Every option this project requests, with its **stock value**, its **built value**,
and the requested value. Generated from the real `lineage-24.0` tree with
kconfiglib, not hand-written.

| | |
|---|---|
| Base | `arch/arm64/configs/earth_defconfig` @ `lineage-24.0` |
| Kernel | Linux **4.19.325**, arm64 |
| Requested options (stable) | **163** |
| Changed vs stock | **158** |
| Already stock (request was a no-op) | **5** |
| Requested options (SUSFS build) | **179** (163 + 16 SUSFS) |

---

## 📖 How to read this

- **Stock defconfig** `—` means the symbol is *not mentioned* in `earth_defconfig`;
  Kconfig's own default decides. It does **not** mean disabled.
- **Built** is the value after `make earth_defconfig` resolves all dependencies.
- `absent` for `KSU*` is expected **in local validation only**: KernelSU-Next is
  cloned during CI, so those symbols do not exist in a bare source tree. CI
  asserts them `=y` and the assertion passes.

### ⚠️ The 5 requests that changed nothing (already stock)

| Option | Stock |
|---|---|
| `SECURITYFS` | `y` (`earth_defconfig:366`) |
| `ZRAM` | `y` (`:68`) |
| `ZSMALLOC` | `y` (`:52`) |
| `CPU_FREQ_DEFAULT_GOV_SCHEDUTIL` | `y` (`:41`) |
| `SCHEDSTATS` | `y` (`:378`) |

These are kept in the request list as explicit assertions — they guarantee the
option stays on even if upstream changes the defconfig. They are **not** new
features, and the changelog does not count them as additions.

---

## 🚫 Options deliberately left off

| Option | Reason | Evidence |
|---|---|---|
| `DEBUG_FS` | Policy: do not expose kernel internals | Several debug options `select` it |
| `ZSMALLOC_STAT` | **`select DEBUG_FS`** → forces debugfs + 14 more debug symbols | `mm/Kconfig:617` |
| `ZRAM_MEMORY_TRACKING` | `depends on DEBUG_FS` | `drivers/block/zram/Kconfig` |
| `NFS_FS`, `NFS_V3`, `NFS_V4`, `NFSD` | Build break in this tree | `fs/nfs/client.c:625` uses `rpc_clnt.cl_softerr`, absent from `include/linux/sunrpc/clnt.h` |
| `KSU_SUSFS_SUS_SU` | Needs kprobes; non-GKI 4.19 | SUSFS `SUS_SU` implementation |
| `KSU_SUSFS_SUS_OVERLAYFS` | Not available on 4.19 | — |
| `KSU_SUSFS_HAS_MAGIC_MOUNT` | KSU-Next legacy does not use magic mount | — |
| `KSU_KPROBES_HOOK` | Manual hooks used instead | — |
| `MODULE_SIG` | Auto-generates a signing key each build → not reproducible | `MODULE_SIG_ALL=y`, `MODULE_SIG_KEY="certs/signing_key.pem"` |
| `SCHED_AUTOGROUP` | TTY-oriented; can hurt Android responsiveness | — |
| `9P_FS` | virtio/Plan9 transport, no use on this device | — |
| `SECURITY_YAMA` | Held off pending root-tool / KSU-Next compatibility verification | `security/yama/yama_lsm.c` |

---

## 🧪 Available but not yet enabled (approved for later phases)

| Option | Phase | Verified side effects |
|---|---|---|
| `UCLAMP_BUCKETS_COUNT=20` | C1 | **none** (range 5–20, `init/Kconfig:726`) |
| `SLAB_FREELIST_RANDOM`, `SLAB_FREELIST_HARDENED` | C1 | **none** |
| `FORTIFY_SOURCE` | C1 | `PROFILE_ALL_BRANCHES` choice entry disappears (benign) |
| `BPF_UNPRIV_DEFAULT_OFF` | C1 | **none** |
| `HARDENED_USERCOPY_FALLBACK=n` | C1 | **none** (makes existing hardening strict) |
| `IDLE_PAGE_TRACKING` | C1 | **none** |
| `BLK_CGROUP_IOLATENCY` | C1 | **none** |
| `PACKET_DIAG`, `INET_UDP_DIAG`, `INET_RAW_DIAG` | C1 | **none** |
| `CGROUP_NET_PRIO` | C1 | **none** |
| `TLS` | C2 | selects `STREAM_PARSER=y` |
| `BPF_STREAM_PARSER` | C2 | selects `STREAM_PARSER=y` |
| `BLK_DEV_THROTTLING` | C2 | adds `BLK_DEV_THROTTLING_LOW=n` |
| `NF_CONNTRACK_TIMEOUT` | C2 | adds `NF_CT_NETLINK_TIMEOUT=n` |
| `BLK_WBT` | C3 experimental | auto-selects `BLK_WBT_MQ=y` |
| `F2FS_FS_COMPRESSION` | C3 experimental | auto-selects LZ4 + LZO + ZSTD |
| `LTO_CLANG`, `CFI_CLANG`, `SHADOW_CALL_STACK` | C3 experimental | require clang + lld |
| `FUNCTION_TRACER` | C3 experimental | pulls `FUNCTION_GRAPH_TRACER`, `FTRACE_MCOUNT_RECORD` |
| `TRANSPARENT_HUGEPAGE` | C3 experimental | defaults to `THP_ALWAYS=y` — must force `MADVISE` |
| `CPU_THERMAL`, `PM_AUTOSLEEP` | C3 experimental | config-clean but runtime conflict risk |

**Method:** each candidate was resolved *individually* against the baseline and
the full config diffed, so the side effects above are observed, not guessed.

---

## 🔬 How validation is performed

```bash
# Resolve the configuration without compiling anything
CC=gcc ARCH=arm64 SRCARCH=arm64 KERNELVERSION=4.19.325 srctree=. \
  python3 -c "import kconfiglib; k=kconfiglib.Kconfig('Kconfig'); \
              k.load_config('.config'); k.write_config('resolved.config')"
```

`CC` **must** be set, otherwise `scripts/Kconfig.include` fails its assembler
probe. Note that `CC_IS_CLANG`-dependent symbols (`LTO_CLANG`, `CFI_CLANG`,
`SHADOW_CALL_STACK`) resolve to `n` under gcc and only become available with
clang — which is what CI uses.

CI then asserts, in the **final** `out/.config`:
1. every requested `=y` symbol is `=y`
2. every requested **string/numeric** value matches (added after the BBR bug)
3. required symbols exist in `System.map`

---

## 📋 Full before / after manifest (stable build)

| Option | Stock defconfig | Built | Requested |
|---|---|---|---|
| `KSU` | — | **y** | y |
| `KSU_MANUAL_HOOK` | — | **y** | y |
| `KSU_KPROBES_HOOK` | — | **absent** | n |
| `SECURITYFS` | y | **y** | y |
| `TCP_CONG_ADVANCED` | — | **y** | y |
| `TCP_CONG_BBR` | — | **y** | y |
| `TCP_CONG_WESTWOOD` | n | **y** | y |
| `DEFAULT_TCP_CONG` | — | **"bbr"** | "bbr" |
| `NET_SCH_FQ` | — | **y** | y |
| `ZRAM` | y | **y** | y |
| `ZSMALLOC` | y | **y** | y |
| `CRYPTO_LZ4` | — | **y** | y |
| `CRYPTO_ZSTD` | — | **y** | y |
| `CLEANCACHE` | — | **y** | y |
| `FRONTSWAP` | — | **y** | y |
| `CPU_FREQ_DEFAULT_GOV_SCHEDUTIL` | y | **y** | y |
| `NO_HZ_IDLE` | — | **y** | y |
| `HZ_250` | — | **y** | y |
| `CC_OPTIMIZE_FOR_PERFORMANCE` | — | **y** | y |
| `WIREGUARD` | — | **y** | y |
| `IP_NF_TARGET_TTL` | — | **y** | y |
| `IP6_NF_TARGET_HL` | — | **y** | y |
| `IP_SET` | — | **y** | y |
| `IP_SET_BITMAP_IP` | — | **y** | y |
| `IP_SET_BITMAP_IPMAC` | — | **y** | y |
| `IP_SET_BITMAP_PORT` | — | **y** | y |
| `IP_SET_HASH_IP` | — | **y** | y |
| `IP_SET_HASH_IPMAC` | — | **y** | y |
| `IP_SET_HASH_IPMARK` | — | **y** | y |
| `IP_SET_HASH_IPPORT` | — | **y** | y |
| `IP_SET_HASH_IPPORTIP` | — | **y** | y |
| `IP_SET_HASH_IPPORTNET` | — | **y** | y |
| `IP_SET_HASH_MAC` | — | **y** | y |
| `IP_SET_HASH_NET` | — | **y** | y |
| `IP_SET_HASH_NETNET` | — | **y** | y |
| `IP_SET_HASH_NETPORT` | — | **y** | y |
| `IP_SET_HASH_NETPORTNET` | — | **y** | y |
| `IP_SET_HASH_NETIFACE` | — | **y** | y |
| `IP_SET_LIST_SET` | — | **y** | y |
| `NETFILTER_XT_SET` | — | **y** | y |
| `TCP_CONG_CUBIC` | — | **y** | y |
| `TCP_CONG_VEGAS` | — | **y** | y |
| `TCP_CONG_VENO` | — | **y** | y |
| `TCP_CONG_YEAH` | — | **y** | y |
| `TCP_CONG_ILLINOIS` | — | **y** | y |
| `TCP_CONG_LP` | — | **y** | y |
| `TCP_CONG_SCALABLE` | — | **y** | y |
| `TCP_CONG_HTCP` | n | **y** | y |
| `CPU_FREQ_GOV_PERFORMANCE` | — | **y** | y |
| `CPU_FREQ_GOV_CONSERVATIVE` | — | **y** | y |
| `IOSCHED_BFQ` | — | **y** | y |
| `BFQ_GROUP_IOSCHED` | — | **y** | y |
| `MQ_IOSCHED_KYBER` | — | **y** | y |
| `MQ_IOSCHED_DEADLINE` | — | **y** | y |
| `SWAP` | — | **y** | y |
| `KSM` | — | **y** | y |
| `ZSWAP` | — | **y** | y |
| `Z3FOLD` | — | **y** | y |
| `ZBUD` | — | **y** | y |
| `CRYPTO_LZO` | — | **y** | y |
| `NETWORK_FILESYSTEMS` | n | **y** | y |
| `CIFS` | — | **y** | y |
| `DEVFREQ_GOV_SIMPLE_ONDEMAND` | — | **y** | y |
| `DEVFREQ_GOV_PERFORMANCE` | — | **y** | y |
| `DEVFREQ_GOV_POWERSAVE` | — | **y** | y |
| `DEVFREQ_GOV_USERSPACE` | — | **y** | y |
| `DEVFREQ_GOV_PASSIVE` | — | **y** | y |
| `THERMAL_GOV_STEP_WISE` | — | **y** | y |
| `THERMAL_GOV_FAIR_SHARE` | — | **y** | y |
| `THERMAL_GOV_BANG_BANG` | — | **y** | y |
| `THERMAL_GOV_USER_SPACE` | — | **y** | y |
| `THERMAL_GOV_POWER_ALLOCATOR` | — | **y** | y |
| `THERMAL_WRITABLE_TRIPS` | — | **y** | y |
| `DEVFREQ_THERMAL` | — | **y** | y |
| `THERMAL_STATISTICS` | — | **y** | y |
| `NET_SCH_CAKE` | — | **y** | y |
| `NET_SCH_FQ_CODEL` | — | **y** | y |
| `NET_SCH_PIE` | — | **y** | y |
| `NET_SCH_CODEL` | — | **y** | y |
| `NET_SCH_NETEM` | — | **y** | y |
| `NET_SCH_HFSC` | — | **y** | y |
| `NET_SCH_PRIO` | — | **y** | y |
| `NET_SCH_SFQ` | — | **y** | y |
| `NET_SCH_TBF` | — | **y** | y |
| `NET_SCH_INGRESS` | — | **y** | y |
| `NET_SCH_MQPRIO` | — | **y** | y |
| `TCP_CONG_DCTCP` | — | **y** | y |
| `TCP_CONG_HSTCP` | — | **y** | y |
| `TCP_CONG_HYBLA` | — | **y** | y |
| `TCP_CONG_NV` | — | **y** | y |
| `TCP_CONG_CDG` | — | **y** | y |
| `NF_TABLES` | — | **y** | y |
| `NF_TABLES_INET` | — | **y** | y |
| `NFT_COMPAT` | — | **y** | y |
| `NFT_NAT` | — | **y** | y |
| `NFT_MASQ` | — | **y** | y |
| `NFT_REDIR` | — | **y** | y |
| `NFT_CT` | — | **y** | y |
| `NFT_COUNTER` | — | **y** | y |
| `NFT_LOG` | — | **y** | y |
| `NFT_LIMIT` | — | **y** | y |
| `NFT_REJECT` | — | **y** | y |
| `IP6_NF_NAT` | — | **y** | y |
| `IP6_NF_TARGET_MASQUERADE` | — | **y** | y |
| `NF_NAT_IPV6` | — | **y** | y |
| `NETFILTER_XT_TARGET_TEE` | — | **y** | y |
| `SQUASHFS` | — | **y** | y |
| `SQUASHFS_XZ` | — | **y** | y |
| `SQUASHFS_LZ4` | — | **y** | y |
| `SQUASHFS_ZSTD` | — | **y** | y |
| `XFS_FS` | — | **y** | y |
| `BTRFS_FS` | — | **y** | y |
| `HFSPLUS_FS` | — | **y** | y |
| `UDF_FS` | — | **y** | y |
| `JFS_FS` | — | **y** | y |
| `KERNEL_LZ4` | — | **y** | y |
| `NET_CLS` | — | **y** | y |
| `NET_CLS_ACT` | — | **y** | y |
| `NET_CLS_U32` | — | **y** | y |
| `NET_CLS_FLOWER` | — | **y** | y |
| `NET_CLS_CGROUP` | — | **y** | y |
| `NET_ACT_POLICE` | — | **y** | y |
| `NET_ACT_MIRRED` | — | **y** | y |
| `NFT_TPROXY` | — | **y** | y |
| `NFT_FIB_IPV4` | — | **y** | y |
| `NFT_FIB_IPV6` | — | **y** | y |
| `NFT_FIB_INET` | — | **y** | y |
| `NFT_FIB` | — | **y** | y |
| `NFT_SOCKET` | — | **y** | y |
| `NFT_OSF` | — | **y** | y |
| `NETFILTER_INGRESS` | — | **y** | y |
| `NF_FLOW_TABLE` | — | **y** | y |
| `NF_FLOW_TABLE_INET` | — | **y** | y |
| `NFT_FLOW_OFFLOAD` | — | **y** | y |
| `NETFILTER_XT_TARGET_TPROXY` | — | **y** | y |
| `NETFILTER_XT_TARGET_NOTRACK` | — | **y** | y |
| `NETFILTER_XT_MATCH_OWNER` | — | **y** | y |
| `NETFILTER_XT_MATCH_QUOTA` | — | **y** | y |
| `NETFILTER_XT_MATCH_TIME` | — | **y** | y |
| `NETFILTER_XT_MATCH_SOCKET` | — | **y** | y |
| `CPU_FREQ_TIMES` | — | **y** | y |
| `TASKSTATS` | — | **y** | y |
| `TASK_DELAY_ACCT` | — | **y** | y |
| `TASK_XACCT` | — | **y** | y |
| `TASK_IO_ACCOUNTING` | — | **y** | y |
| `SCHEDSTATS` | y | **y** | y |
| `DEFAULT_BBR` | — | **y** | y |
| `UCLAMP_BUCKETS_COUNT` | — | **20** | 20 |
| `SLAB_FREELIST_RANDOM` | — | **y** | y |
| `SLAB_FREELIST_HARDENED` | — | **y** | y |
| `FORTIFY_SOURCE` | — | **y** | y |
| `BPF_UNPRIV_DEFAULT_OFF` | — | **y** | y |
| `HARDENED_USERCOPY_FALLBACK` | — | **n** | n |
| `IDLE_PAGE_TRACKING` | — | **y** | y |
| `BLK_CGROUP_IOLATENCY` | — | **y** | y |
| `PACKET_DIAG` | — | **y** | y |
| `INET_UDP_DIAG` | — | **y** | y |
| `INET_RAW_DIAG` | — | **y** | y |
| `CGROUP_NET_PRIO` | — | **y** | y |
| `TLS` | — | **y** | y |
| `BPF_STREAM_PARSER` | — | **y** | y |
| `BLK_DEV_THROTTLING` | — | **y** | y |
| `NF_CONNTRACK_TIMEOUT` | — | **y** | y |

---

## ✅ Phase C1 + C2 — now applied (before → after)

| Option | Before | After | Side effect observed |
|---|---|---|---|
| `UCLAMP_BUCKETS_COUNT` | `5` | **`20`** | none |
| `SLAB_FREELIST_RANDOM` | `n` | **`y`** | none |
| `SLAB_FREELIST_HARDENED` | `n` | **`y`** | none |
| `FORTIFY_SOURCE` | `n` | **`y`** | `PROFILE_ALL_BRANCHES` choice entry disappears |
| `BPF_UNPRIV_DEFAULT_OFF` | `n` | **`y`** | none |
| `HARDENED_USERCOPY_FALLBACK` | **`y`** | **`n`** | none — makes existing hardening strict |
| `IDLE_PAGE_TRACKING` | `n` | **`y`** | none |
| `BLK_CGROUP_IOLATENCY` | `n` | **`y`** | none |
| `PACKET_DIAG` | `n` | **`y`** | none |
| `INET_UDP_DIAG` | `n` | **`y`** | none |
| `INET_RAW_DIAG` | `n` | **`y`** | none |
| `CGROUP_NET_PRIO` | `n` | **`y`** | none |
| `TLS` | `n` | **`y`** | selects `STREAM_PARSER=y`; `TLS_DEVICE=n` |
| `BPF_STREAM_PARSER` | `n` | **`y`** | selects `STREAM_PARSER=y` |
| `BLK_DEV_THROTTLING` | `n` | **`y`** | `BLK_DEV_THROTTLING_LOW=n` |
| `NF_CONNTRACK_TIMEOUT` | `n` | **`y`** | `NF_CT_NETLINK_TIMEOUT=n` |

**Aggregate regression review:** 5 unrequested changes, all listed above and all
predicted. **Zero** previously-enabled options were lost. Guards confirmed unchanged:
`DEBUG_FS=n`, `NFS_FS=n`, `NFSD=n`, `NFT_COMPAT=y`, `THERMAL_WRITABLE_TRIPS=y`,
`ZRAM_MEMORY_TRACKING=n`, `SCHED_AUTOGROUP=n`, `TRANSPARENT_HUGEPAGE=n`,
`MODULE_SIG=n`, and **`LTO_CLANG=n` in stable/SUSFS** (experimental isolation holds).

### Verifier now asserts `=n` too

Requesting `=n` is only meaningful if checked: Kconfig can re-enable a symbol via
`default y` or a `select`. The verifier now validates explicitly-disabled options
in the final `.config` alongside `=y` and string/numeric values.

Dry run: **159 `=y` + 2 `=n` + 2 string/numeric**, exit 0.

---

## 🧪 Phase C3 — experimental workflow only

`.github/workflows/experimental.yml` adds, on top of everything above:

| Option | Value | Availability evidence |
|---|---|---|
| `LTO_CLANG` | `y` | `arch/arm64/Kconfig:61`; `Makefile:864-877` |
| `THINLTO` | `y` | `arch/arm64/Kconfig:62`; `arch/Kconfig:514` |
| `CFI_CLANG` | `y` | `arch/Kconfig:560`; `Makefile:894-904` |
| `CFI_PERMISSIVE` | `y` | violations WARN, not panic — diagnosable |
| `SHADOW_CALL_STACK` | `y` | `arch/arm64/Kconfig:63,988` (clang ≥7); `asm/scs.h` |

Prerequisites verified: `KALLSYMS=y`, `KASAN` unset, `HAVE_C_RECORDMCOUNT=y`,
`FTRACE_MCOUNT_RECORD` unset. These resolve `n` under gcc and require clang+lld,
which is why they are built with a pinned **clang-16** rather than the stable
build's clang-18.

---

## 🔗 Related

[FEATURES.md](FEATURES.md) · [SECURITY.md](SECURITY.md) · [BUILD_GUIDE.md](BUILD_GUIDE.md) · [CHANGELOG.md](CHANGELOG.md)
