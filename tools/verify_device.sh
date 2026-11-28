#!/system/bin/sh
# verify_device.sh — READ-ONLY runtime report for the earth custom kernel.
#
# Run in Termux after flashing:   sh verify_device.sh
# (root is used only to read dmesg / KSU paths; everything else works unrooted)
#
# This script only READS sysfs/procfs. It never writes, never changes settings,
# never flashes anything. Safe to run at any time.
#
# Purpose: CI proves the kernel compiles. This proves what is actually RUNNING.

L() { printf '\n===== %s =====\n' "$1"; }
rd() { # rd <label> <path>
  if [ -r "$2" ]; then printf '%-28s %s\n' "$1:" "$(cat "$2" 2>/dev/null | head -1)"
  else printf '%-28s %s\n' "$1:" "n/a"; fi
}
have() { command -v "$1" >/dev/null 2>&1; }
SU=""
if have su; then SU="su -c"; fi
rroot() { # rroot <cmd>  (best-effort root read)
  if [ -n "$SU" ]; then su -c "$1" 2>/dev/null; else sh -c "$1" 2>/dev/null; fi
}

printf '###############################################\n'
printf '# earth kernel — runtime verification report\n'
printf '# %s\n' "$(date 2>/dev/null)"
printf '###############################################\n'

L "1. DEVICE / ROM IDENTITY"
for p in ro.product.device ro.product.model ro.build.version.release \
         ro.build.version.sdk ro.vendor.build.fingerprint ro.lineage.version \
         ro.build.display.id; do
  printf '%-34s %s\n' "$p" "$(getprop $p 2>/dev/null)"
done
echo "--> Kernel target: earth/aether, LineageOS 24.0 base. Mismatch here explains most failures."

L "2. IS THE CUSTOM KERNEL RUNNING?"
printf 'uname -r      : %s\n' "$(uname -r)"
printf 'uname -a      : %s\n' "$(uname -a)"
rd "proc/version" /proc/version
case "$(uname -r)" in
  4.19.325*) echo "RESULT: kernel version matches the build (4.19.325) OK" ;;
  4.19*)     echo "RESULT: 4.19.x but not .325 — possibly the stock/older kernel" ;;
  *)         echo "RESULT: NOT a 4.19 kernel — wrong kernel for this device!" ;;
esac

L "3. KERNELSU-NEXT"
if [ -d /data/adb/ksu ]; then echo "/data/adb/ksu           : present"; else echo "/data/adb/ksu           : not readable (need root) or absent"; fi
rroot "ls /data/adb/ksu/bin 2>/dev/null | head -10"
echo "--> The manager app must say 'Working'. That is the authoritative check."
echo "KSU symbols in kernel:"
rroot "grep -cE ' ksu_handle_execveat| ksu_handle_faccessat' /proc/kallsyms" \
  | sed 's/^/  ksu_handle_* count: /'

L "4. SUSFS (experimental build only)"
echo "-- kernel side --"
rroot "dmesg | grep -i susfs | head -12"
echo "  (no lines above = SUSFS not active, or you flashed the STABLE build)"
rroot "grep -c susfs /proc/kallsyms" | sed 's/^/  susfs symbols in kallsyms: /'
echo "-- userspace side --"
for p in /data/adb/ksu/bin/ksu_susfs /data/adb/modules/susfs4ksu \
         /data/adb/modules/susfs4ksu/config.sh; do
  rroot "test -e $p && echo '  PRESENT  $p' || echo '  missing  $p'"
done
echo "-- module version / key knobs --"
rroot "grep -E '^(version|versionCode)=' /data/adb/modules/susfs4ksu/module.prop"
rroot "grep -E '^(susfs_log|spoof_uname|auto_try_umount|sus_su|hide_sus_mnts_for_all_or_non_su_procs)=' /data/adb/modules/susfs4ksu/config.sh"
echo "--> Both halves must be present. Kernel alone hides nothing."

L "5. CPU FREQ / GOVERNORS"
for pol in /sys/devices/system/cpu/cpufreq/policy*; do
  [ -d "$pol" ] || continue
  echo "[$(basename $pol)]"
  rd "  governor" "$pol/scaling_governor"
  rd "  available" "$pol/scaling_available_governors"
  rd "  cur freq" "$pol/scaling_cur_freq"
  rd "  min/max" "$pol/scaling_min_freq"
  printf '%-28s %s / %s\n' "  hw min/max:" \
    "$(cat $pol/cpuinfo_min_freq 2>/dev/null)" "$(cat $pol/cpuinfo_max_freq 2>/dev/null)"
done
echo "--> Governor should be schedutil. Max freq must equal hw max (no pinning)."

L "6. DDR / DEVFREQ"
found=0
for d in /sys/class/devfreq/*; do
  [ -d "$d" ] || continue
  found=1
  echo "[$(basename $d)]"
  rd "  governor" "$d/governor"
  rd "  available" "$d/available_governors"
  rd "  cur freq" "$d/cur_freq"
  rd "  avail freq" "$d/available_frequencies"
done
[ "$found" = 0 ] && echo "no devfreq nodes (MTK DVFSRC may expose elsewhere)"
echo "--> Confirms DDR scaling is live, not just compiled in."

L "7. THERMAL (safeguards must be intact)"
n=0
for z in /sys/class/thermal/thermal_zone*; do
  [ -d "$z" ] || continue
  t=$(cat $z/type 2>/dev/null); tmp=$(cat $z/temp 2>/dev/null)
  pol=$(cat $z/policy 2>/dev/null)
  printf '  %-22s temp=%-8s policy=%s\n' "$t" "$tmp" "$pol"
  n=$((n+1))
  [ "$n" -ge 18 ] && { echo "  …(truncated)"; break; }
done
echo "thermal zones: $n"
rd "available policies" /sys/class/thermal/thermal_zone0/available_policies
echo "cooling devices: $(ls -d /sys/class/thermal/cooling_device* 2>/dev/null | wc -l)"
echo "writable trip test (read-only check of mode):"
rd "  trip_point_0_type" /sys/class/thermal/thermal_zone0/trip_point_0_type
echo "--> Zones must exist and report sane temps. Never disable these."

L "8. MEMORY / ZRAM / PSI"
grep -E '^(MemTotal|MemAvailable|SwapTotal|SwapFree|Cached)' /proc/meminfo 2>/dev/null
echo "-- swaps --"; cat /proc/swaps 2>/dev/null
for f in disksize comp_algorithm mm_stat mem_limit; do rd "zram0/$f" /sys/block/zram0/$f; done
echo "-- PSI (pressure stall info) --"
for r in cpu memory io; do rd "pressure/$r" /proc/pressure/$r; done
echo "-- KSM --"; rd "ksm/run" /sys/kernel/mm/ksm/run
echo "-- uclamp --"
for p in /dev/cpuctl/cpu.uclamp.min /sys/fs/cgroup/cpu.uclamp.min; do
  [ -e "$p" ] && echo "  present: $p"
done
echo "--> zram should be active with lz4/zstd. PSI files should exist."

L "9. NETWORK (TCP / qdisc)"
rd "tcp_congestion_control" /proc/sys/net/ipv4/tcp_congestion_control
rd "available CC" /proc/sys/net/ipv4/tcp_available_congestion_control
rd "default_qdisc" /proc/sys/net/core/default_qdisc
have tc && tc qdisc show 2>/dev/null | head -8
echo "--> bbr expected as default. Built-in qdiscs have no sysfs list; the"
echo "    available CC list above is the reliable compiled-in indicator."

L "10. FILESYSTEMS REGISTERED"
cat /proc/filesystems 2>/dev/null | awk '{print $NF}' | tr '\n' ' '; echo
echo "--> Look for squashfs, xfs, btrfs, hfsplus, udf, jfs, f2fs, erofs, exfat."

L "11. STABILITY SIGNALS"
echo "-- recent kernel errors/warnings --"
rroot "dmesg | grep -iE 'BUG:|Oops|kernel panic|call trace|WARNING:|segfault|thermal shutdown' | tail -12"
echo "  (empty = no obvious faults)"
echo "-- uptime / load --"; cat /proc/uptime 2>/dev/null; cat /proc/loadavg 2>/dev/null
echo "-- battery / charging --"
for p in capacity status current_now temp health; do
  rd "battery/$p" /sys/class/power_supply/battery/$p
done

L "SUMMARY — what to check by eye"
cat <<'EOF'
  [ ] Section 2  : uname -r shows 4.19.325
  [ ] Section 3  : manager says "Working"
  [ ] Section 4  : dmesg has susfs lines  (ONLY on the experimental build)
  [ ] Section 5  : governor = schedutil, max freq = hardware max
  [ ] Section 6  : devfreq governor present and changing
  [ ] Section 7  : thermal zones present, temps sane (< ~45000 idle)
  [ ] Section 8  : zram active, PSI files present
  [ ] Section 9  : tcp CC = bbr
  [ ] Section 11 : no BUG/Oops/panic lines
  [ ] Real use   : WiFi, camera, charging, fingerprint, calls all work
EOF
printf '\nDone. Copy this whole output back if you want help interpreting it.\n'
