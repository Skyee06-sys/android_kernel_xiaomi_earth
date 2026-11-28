#!/usr/bin/env python3
"""
Restore upstream declaration order in net/core/skmsg.c.

The defect
----------
LineageOS android_kernel_xiaomi_earth (lineage-24.0, Linux 4.19.325) carries a
mis-ordered backport of the sockmap / stream-parser code:

    net/core/skmsg.c:789  static void sk_psock_strp_read(...)
    net/core/skmsg.c:791      struct sk_psock *psock = sk_psock_from_strp(strp);
    ...
    net/core/skmsg.c:812  static struct sk_psock *sk_psock_from_strp(...)   <-- too late

`sk_psock_from_strp()` is called 21 lines before it is defined, with no forward
declaration. GCC accepts this as an implicit declaration plus an int->pointer
conversion warning. Clang treats it as a hard error:

    net/core/skmsg.c:791:27: error: implicit declaration of function
        'sk_psock_from_strp' [-Werror,-Wimplicit-function-declaration]
    net/core/skmsg.c:791:19: error: incompatible integer to pointer conversion
        initializing 'struct sk_psock *' with an expression of type 'int'
    net/core/skmsg.c:812:25: error: static declaration of 'sk_psock_from_strp'
        follows non-static declaration

Why nobody noticed
------------------
The whole block sits inside `#if IS_ENABLED(CONFIG_BPF_STREAM_PARSER)`, and the
stock earth defconfig does not enable it. The code is simply never compiled.
Enabling CONFIG_BPF_STREAM_PARSER (Phase C2) exposes the latent defect.
This is a bug in the vendor tree, not in the configuration.

The fix
-------
Move the definition above its first caller, which is exactly where upstream
puts it. Verified against torvalds/linux v5.4 net/core/skmsg.c:

    L681  static struct sk_psock *sk_psock_from_strp(struct strparser *strp)
    L741  static void sk_psock_strp_read(...)
    L743      struct sk_psock *psock = sk_psock_from_strp(strp);

The function body in this tree is byte-identical to upstream v5.4. This is pure
code motion: not one token is added, removed or altered.

Regression safety
-----------------
* The moved block stays inside the SAME `#if IS_ENABLED(CONFIG_BPF_STREAM_PARSER)`
  region, so a kernel with the option disabled preprocesses to identical output.
* The script asserts that the multiset of file lines is unchanged, that brace
  balance is unchanged, and that the definition now precedes every call.
* Idempotent: an already-correct file is left untouched.
* Every anchor must match exactly once, so upstream drift fails loudly instead
  of producing a half-patched tree.

Usage (from the kernel root):
    python3 scripts/fix_skmsg_order.py [--kernel-dir kernel] [--check]

--check reports whether the fix is needed without writing anything.
Exit code is non-zero if the tree does not match expectations.
"""

import argparse
import difflib
import pathlib
import sys

# Exact text, including tabs. Anchored on the guard so the block cannot be
# moved outside the #ifdef that owns it.
GUARD = "#if IS_ENABLED(CONFIG_BPF_STREAM_PARSER)\n"

FUNC = (
    "static struct sk_psock *sk_psock_from_strp(struct strparser *strp)\n"
    "{\n"
    "\tstruct sk_psock_parser *parser;\n"
    "\n"
    "\tparser = container_of(strp, struct sk_psock_parser, strp);\n"
    "\treturn container_of(parser, struct sk_psock, parser);\n"
    "}\n"
)

CALLER = "static void sk_psock_strp_read(struct strparser *strp, struct sk_buff *skb)\n"


def die(msg):
    print(f"::error title=skmsg order::{msg}" if _CI else f"ERROR: {msg}")
    sys.exit(1)


_CI = False


def analyse(text):
    """Return (definition_line, first_call_line) as 1-based line numbers."""
    lines = text.splitlines()
    defline = None
    calls = []
    for i, line in enumerate(lines, 1):
        if line.startswith("static struct sk_psock *sk_psock_from_strp("):
            if defline is not None:
                die("sk_psock_from_strp defined more than once")
            defline = i
        elif "sk_psock_from_strp(" in line:
            calls.append(i)
    return defline, calls


def main():
    global _CI
    ap = argparse.ArgumentParser()
    ap.add_argument("--kernel-dir", default="kernel", help="kernel source root")
    ap.add_argument("--check", action="store_true", help="report only, do not write")
    ap.add_argument("--ci", action="store_true", help="emit GitHub annotations")
    args = ap.parse_args()
    _CI = args.ci

    path = pathlib.Path(args.kernel_dir) / "net/core/skmsg.c"
    if not path.is_file():
        die(f"{path} not found")
    original = path.read_text()

    defline, calls = analyse(original)
    if defline is None:
        # Upstream removed this helper in later kernels. Nothing to do, but say so.
        print("sk_psock_from_strp() not present in this tree - no fix needed.")
        return
    if not calls:
        die("sk_psock_from_strp() defined but never called - unexpected tree")

    if defline < min(calls):
        print(f"skmsg.c already correct: definition L{defline} precedes calls {calls}")
        return

    print(f"skmsg.c defect confirmed: definition L{defline}, calls {calls}")
    if args.check:
        print("Fix required (no changes written).")
        return

    # ---- exact anchors -------------------------------------------------
    if original.count(GUARD) != 1:
        die(f"expected exactly one BPF_STREAM_PARSER guard, found {original.count(GUARD)}")
    if original.count(FUNC) != 1:
        die("sk_psock_from_strp definition does not match the expected upstream body")
    if original.count(CALLER) != 1:
        die("sk_psock_strp_read definition not found exactly once")

    guard_at = original.index(GUARD)
    func_at = original.index(FUNC)
    caller_at = original.index(CALLER)
    endif_at = original.find("#endif /* CONFIG_BPF_STREAM_PARSER */", guard_at)
    if endif_at == -1:
        die("could not locate the end of the BPF_STREAM_PARSER region")
    if not (guard_at < func_at < endif_at):
        die("definition is not inside the BPF_STREAM_PARSER region - refusing to move it")
    if not (guard_at < caller_at < func_at):
        die("unexpected ordering - refusing to patch")

    # ---- pure code motion ---------------------------------------------
    # Remove the definition (and the blank line that separated it from the
    # next function), then re-insert it directly after the guard.
    removed = FUNC + "\n"
    if original.count(removed) != 1:
        die("expected a blank line after the definition")
    without = original.replace(removed, "", 1)
    fixed = without.replace(GUARD, GUARD + FUNC + "\n", 1)

    # ---- regression assertions ----------------------------------------
    if sorted(fixed.splitlines()) != sorted(original.splitlines()):
        die("line multiset changed - this must be pure code motion")
    if fixed.count("{") != original.count("{") or fixed.count("}") != original.count("}"):
        die("brace balance changed")
    if len(fixed) != len(original):
        die("byte length changed - this must be pure code motion")

    newdef, newcalls = analyse(fixed)
    if newdef is None or not newcalls or newdef >= min(newcalls):
        die("post-patch verification failed: definition still not first")

    newguard = fixed.index(GUARD)
    newendif = fixed.index("#endif /* CONFIG_BPF_STREAM_PARSER */", newguard)
    if not (newguard < fixed.index(FUNC) < newendif):
        die("post-patch: definition escaped its #ifdef region")

    # Strongest guarantee: with CONFIG_BPF_STREAM_PARSER disabled the whole
    # region is preprocessed away, so everything OUTSIDE it must be untouched.
    # If that holds, a stock (option-off) kernel cannot change behaviour.
    if original[:guard_at] != fixed[:newguard]:
        die("text before the guarded region changed")
    if original[endif_at:] != fixed[newendif:]:
        die("text after the guarded region changed")
    if sorted(original[guard_at:endif_at].splitlines()) != sorted(
        fixed[newguard:newendif].splitlines()
    ):
        die("guarded region is not a pure permutation")

    if args.check:
        print("Fix required (no changes written).")
        return

    path.write_text(fixed)
    print(f"skmsg.c fixed: definition L{defline} -> L{newdef}, calls now {newcalls}")
    print("Verified: pure code motion, same #ifdef region, braces balanced.")
    sys.stdout.writelines(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile="a/net/core/skmsg.c",
            tofile="b/net/core/skmsg.c",
            n=3,
        )
    )


if __name__ == "__main__":
    main()
