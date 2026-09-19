#!/usr/bin/env python3
"""
bootstrap.py - Unified local build/install/check script for the OpenFX plugin series.

Cross-platform, Python 3.8+, stdlib only.

Dependencies (OpenFX SDK) come from Conan; CMake is driven through the presets
that `conan install` generates (no hardcoded generator / toolchain path).
If `conan` is not on PATH, it is run via `uvx conan`.
Plugins live in plugins/<name>/ and are discovered by CMake automatically.

Commands:
    d(eps)          conan install (detects a default profile if missing)
    b(uild) [name]  Configure + build all plugins, or one (runs `d` when needed)
    i(nstall) [name] cmake --install all bundles, or one (default: system OFX dir; --prefix)
    p(ackage)       Install all bundles into dist/ and zip them
    c(heck)         Stage-install and verify every bundle (plist, layout, OFX exports)
    new <Name>      Create plugins/<name>/ from templates/plugin
    cl(ean)         Remove build/, dist/, CMakeUserPresets.json
    h(elp)          Print help

Examples:
    python bootstrap.py b
    python bootstrap.py b colorFill
    python bootstrap.py new MyGlow --id com.joss.MyGlow --label "My Glow"
    python bootstrap.py i --prefix C:/OFX/Plugins
    python bootstrap.py p
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import plistlib
import re
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path


ROOT_DIR = Path(__file__).parent.resolve()
IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"

# Build layout produced by `cmake_layout` in conanfile.py. Multi-config
# generators (Visual Studio) share one build dir; single-config ones
# (Makefiles/Ninja on Linux/macOS) get build/<BuildType>/.
BUILD_DIR = ROOT_DIR / "build"
DIST_DIR = ROOT_DIR / "dist"
PLUGINS_DIR = ROOT_DIR / "plugins"
TEMPLATE_DIR = ROOT_DIR / "templates" / "plugin"
USER_PRESETS = ROOT_DIR / "CMakeUserPresets.json"
CPPSTD = "17"  # openfx >= 1.5 requires C++17
OFX_EXPORTS = ("OfxGetPlugin", "OfxGetNumberOfPlugins")


class C:
    RST = "\033[0m"
    RED = "\033[91m"
    GRN = "\033[92m"
    YLW = "\033[93m"
    CYN = "\033[96m"
    WHT = "\033[97m"

    @classmethod
    def init(cls) -> None:
        if IS_WINDOWS:
            os.system("")


def fmt_time(ms: float) -> str:
    if ms < 1000:
        return f"{ms:.0f}ms"
    if ms < 60000:
        return f"{ms / 1000:.1f}s"
    mins = int(ms // 60000)
    secs = (ms % 60000) / 1000
    return f"{mins}m{secs:.0f}s"


def header(text: str) -> None:
    line = "=" * 60
    print(f"\n{C.CYN}{line}\n{text}\n{line}{C.RST}")


def step(text: str) -> None:
    print(f"  {C.WHT}{text}{C.RST}")


def ok(text: str) -> None:
    print(f"  {C.GRN}[OK] {text}{C.RST}")


def warn(text: str) -> None:
    print(f"  {C.YLW}[WARN] {text}{C.RST}")


def err(text: str) -> None:
    print(f"  {C.RED}[ERR] {text}{C.RST}")


def run(args: list[str], cwd: Path | None = None, capture: bool = False) -> tuple[int, str, float]:
    start = time.perf_counter()
    try:
        result = subprocess.run(args, cwd=cwd or ROOT_DIR, capture_output=capture, text=True)
    except FileNotFoundError:
        err(f"`{args[0]}` not found")
        return 127, "", 0.0
    elapsed_ms = (time.perf_counter() - start) * 1000
    output = (result.stdout or "") + (result.stderr or "") if capture else ""
    return result.returncode, output, elapsed_ms


def which(cmd: str) -> Path | None:
    found = shutil.which(cmd)
    return Path(found) if found else None


# ---- Toolchain -------------------------------------------------------------

def build_type(args: argparse.Namespace) -> str:
    return "Debug" if args.debug else "Release"


def conan_cmd() -> list[str] | None:
    if which("conan"):
        return ["conan"]
    if which("uvx"):
        return ["uvx", "conan"]
    return None


def check_tools() -> bool:
    passed = True
    if not which("cmake"):
        err("`cmake` not found on PATH (3.23+ required)")
        passed = False
    if conan_cmd() is None:
        err("Neither `conan` nor `uvx` found on PATH")
        step("Install Conan 2: pip install conan  (or install uv: https://docs.astral.sh/uv/)")
        passed = False
    return passed


def cmake_binary_dir(bt: str) -> Path:
    return BUILD_DIR if IS_WINDOWS else BUILD_DIR / bt


def configure_preset(bt: str) -> str:
    return "conan-default" if IS_WINDOWS else f"conan-{bt.lower()}"


def build_preset(bt: str) -> str:
    return f"conan-{bt.lower()}"


def plugin_bin_dir(bt: str) -> Path:
    # LIBRARY_OUTPUT_DIRECTORY = <binary dir>/bin; multi-config generators append /<Type>
    bin_dir = cmake_binary_dir(bt) / "bin"
    return bin_dir / bt if IS_WINDOWS else bin_dir


def read_version() -> str:
    return (ROOT_DIR / "version.txt").read_text(encoding="utf-8").strip()


# ---- Deps (conan install) --------------------------------------------------

def conan_settings(conan: list[str]) -> list[str]:
    settings = ["-s", f"compiler.cppstd={CPPSTD}"]
    code, out, _ = run([*conan, "profile", "show"], capture=True)
    if code == 0 and re.search(r"^compiler=msvc$", out, re.M):
        settings += ["-s", "compiler.runtime=static"]  # enforced by conanfile.validate()
    return settings


def deps_stamp_path(bt: str) -> Path:
    return cmake_binary_dir(bt) / "generators" / f".deps-{bt.lower()}.json"


def recipe_hash() -> str:
    recipe = (ROOT_DIR / "conanfile.py").read_bytes() + (ROOT_DIR / "version.txt").read_bytes()
    return hashlib.sha256(recipe).hexdigest()


def deps_ready(bt: str) -> bool:
    stamp = deps_stamp_path(bt)
    if not (stamp.is_file() and USER_PRESETS.is_file()):
        return False
    try:
        saved = json.loads(stamp.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return saved.get("recipe_sha256") == recipe_hash()


def run_deps(args: argparse.Namespace) -> int:
    header("DEPS (conan install)")
    if not check_tools():
        return 1
    conan = conan_cmd()
    assert conan is not None
    if conan[0] == "uvx":
        warn("`conan` not on PATH, using `uvx conan`")

    code, _, _ = run([*conan, "profile", "path", "default"], capture=True)
    if code != 0:
        step("No default Conan profile, detecting one")
        code, _, _ = run([*conan, "profile", "detect"])
        if code != 0:
            err("conan profile detect failed")
            return code

    bt = build_type(args)
    install_args = ["install", ".", "--build=missing", "-s", f"build_type={bt}", *conan_settings(conan)]
    step(f"conan {' '.join(install_args)}")
    print()
    code, _, elapsed = run([*conan, *install_args])
    if code == 0:
        stamp = {"args": install_args, "recipe_sha256": recipe_hash()}
        deps_stamp_path(bt).write_text(json.dumps(stamp), encoding="utf-8")
        ok(f"Dependencies ready ({fmt_time(elapsed)})")
    else:
        err("conan install failed")
    print()
    return code


# ---- Build / install / package ---------------------------------------------

def run_build(args: argparse.Namespace) -> int:
    bt = build_type(args)
    if args.fresh or not deps_ready(bt):
        code = run_deps(args)
        if code != 0:
            return code

    header("BUILD")
    step(f"Mode: {bt.lower()}, target: {args.target or 'all'}")
    code, _, elapsed = run(["cmake", "--preset", configure_preset(bt)])
    if code != 0:
        err("CMake configure failed")
        step("Try: python bootstrap.py cl && python bootstrap.py b")
        return code
    ok(f"Configured ({fmt_time(elapsed)})")

    print()
    cmd = ["cmake", "--build", "--preset", build_preset(bt)]
    if args.target:
        cmd += ["--target", args.target]
    code, _, elapsed = run(cmd)
    if code == 0:
        ok(f"Build successful ({fmt_time(elapsed)})")
        step(f"Plugins: {plugin_bin_dir(bt)}")
    else:
        err("Build failed")
    print()
    return code


def install_bundles(args: argparse.Namespace, prefix: Path | None, quiet: bool = False) -> int:
    """Single install path used by `i`, `p` and `c`. Always brings the build up to date first."""
    bt = build_type(args)
    code = run_build(args)
    if code != 0:
        return code

    cmd = ["cmake", "--install", str(cmake_binary_dir(bt)), "--config", bt]
    if prefix:
        cmd += ["--prefix", str(prefix)]
    if args.target:
        cmd += ["--component", args.target]
    code, out, elapsed = run(cmd, capture=quiet)
    if code != 0:
        if quiet:
            print(out)
        err("Install failed")
        if not prefix:
            step("No write access? Use --prefix <dir> or run from an elevated shell")
    elif not quiet:
        ok(f"Installed ({fmt_time(elapsed)})")
    return code


def run_install(args: argparse.Namespace) -> int:
    header("INSTALL")
    prefix = Path(args.prefix).resolve() if args.prefix else None
    step(f"Prefix: {prefix or 'system OFX plugin dir (may need admin rights)'}")
    code = install_bundles(args, prefix)
    print()
    return code


def run_package(args: argparse.Namespace) -> int:
    header("PACKAGE")
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    code = install_bundles(args, DIST_DIR)
    if code != 0:
        return code

    bundles = find_bundles(DIST_DIR)
    if not bundles:
        err("No bundles installed")
        return 1
    for doc in ("LICENSE", "README.md"):
        shutil.copy2(ROOT_DIR / doc, DIST_DIR / doc)
    archdir = bundle_binary(bundles[0])[0].parent.name
    archive_base = ROOT_DIR / f"{ROOT_DIR.name}-{read_version()}-{archdir.lower()}"
    archive = Path(shutil.make_archive(str(archive_base), "zip", root_dir=DIST_DIR))
    archive = Path(shutil.move(str(archive), str(DIST_DIR / archive.name)))
    for bundle in bundles:
        ok(f"Bundle: {bundle.relative_to(ROOT_DIR)}")
    ok(f"Archive: {archive.relative_to(ROOT_DIR)}")
    print()
    return 0


# ---- Check -----------------------------------------------------------------

def find_bundles(prefix: Path) -> list[Path]:
    return sorted(p for p in prefix.glob("*.ofx.bundle") if p.is_dir())


def bundle_binary(bundle: Path) -> tuple[Path, dict]:
    """Returns (Contents/<arch>/<exe>, Info.plist dict). Raises ValueError on a malformed bundle."""
    plist_path = bundle / "Contents" / "Info.plist"
    if not plist_path.is_file():
        raise ValueError("Contents/Info.plist missing")
    info = plistlib.loads(plist_path.read_bytes())
    exe = info.get("CFBundleExecutable")
    if exe != bundle.name[: -len(".bundle")]:
        raise ValueError(f"CFBundleExecutable {exe!r} does not match bundle name")
    binaries = [p for p in (bundle / "Contents").glob(f"*/{exe}") if p.is_file()]
    if len(binaries) != 1:
        raise ValueError(f"expected exactly one Contents/<arch>/{exe}, found {len(binaries)}")
    return binaries[0], info


def pe_exports(data: bytes) -> set[str]:
    """Exported symbol names of a PE (DLL) image, stdlib only."""
    u16 = lambda off: struct.unpack_from("<H", data, off)[0]  # noqa: E731
    u32 = lambda off: struct.unpack_from("<I", data, off)[0]  # noqa: E731
    pe = u32(0x3C)
    if data[pe:pe + 4] != b"PE\0\0":
        raise ValueError("not a PE image")
    coff = pe + 4
    n_sections, opt_size = u16(coff + 2), u16(coff + 16)
    opt = coff + 20
    data_dirs = opt + (112 if u16(opt) == 0x20B else 96)  # PE32+ : PE32
    export_rva = u32(data_dirs)
    if export_rva == 0:
        return set()
    sections = [
        (u32(s + 12), max(u32(s + 8), u32(s + 16)), u32(s + 20))  # VA, size, raw offset
        for s in range(opt + opt_size, opt + opt_size + 40 * n_sections, 40)
    ]

    def offset(rva: int) -> int:
        for va, size, raw in sections:
            if va <= rva < va + size:
                return rva - va + raw
        raise ValueError(f"RVA {rva:#x} outside sections")

    exp = offset(export_rva)
    n_names, names_rva = u32(exp + 24), u32(exp + 32)
    names = set()
    for i in range(n_names):
        start = offset(u32(offset(names_rva) + 4 * i))
        names.add(data[start:data.index(b"\0", start)].decode("ascii"))
    return names


def list_exports(binary: Path) -> set[str]:
    if IS_WINDOWS:
        return pe_exports(binary.read_bytes())
    code, out, _ = run(["nm", "-gU" if IS_MACOS else "-D", str(binary)], capture=True)
    if code != 0:
        raise ValueError("nm failed")
    return {line.split()[-1].lstrip("_") for line in out.splitlines() if line.strip()}


def run_check(args: argparse.Namespace) -> int:
    header("CHECK")
    stage = BUILD_DIR / "_check_stage"
    if stage.exists():
        shutil.rmtree(stage)
    code = install_bundles(args, stage, quiet=True)
    if code != 0:
        return code

    bundles = find_bundles(stage)
    passed = bool(bundles)
    if not bundles:
        err("No bundles installed")
    for bundle in bundles:
        try:
            binary, info = bundle_binary(bundle)
            missing = [sym for sym in OFX_EXPORTS if sym not in list_exports(binary)]
            if missing:
                raise ValueError(f"missing exports: {', '.join(missing)}")
            ok(f"{bundle.name}  {binary.parent.name}/  v{info.get('CFBundleVersion')}  {info.get('CFBundleIdentifier')}")
        except (ValueError, OSError, plistlib.InvalidFileException, struct.error) as e:
            err(f"{bundle.name}: {e}")
            passed = False

    shutil.rmtree(stage, ignore_errors=True)
    print()
    if passed:
        ok("All checks passed")
    else:
        err("Some checks failed")
    print()
    return 0 if passed else 1


# ---- Scaffolding -----------------------------------------------------------

def run_new(args: argparse.Namespace) -> int:
    header("NEW PLUGIN")
    if not args.target or not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", args.target):
        err("Usage: python bootstrap.py new <Name>   (letters/digits, e.g. MyGlow)")
        return 1
    plugin_class = args.target[0].upper() + args.target[1:]
    plugin_name = args.target[0].lower() + args.target[1:]
    dest = PLUGINS_DIR / plugin_name
    if dest.exists():
        err(f"{dest.relative_to(ROOT_DIR)} already exists")
        return 1
    existing = {p.name.lower() for p in PLUGINS_DIR.iterdir() if p.is_dir()} if PLUGINS_DIR.is_dir() else set()
    if plugin_name.lower() in existing:
        err(f"A plugin named {plugin_name!r} (case-insensitive) already exists")
        return 1

    # Same tokens as the OFX_BUILD_TEMPLATE_CHECK instantiation in CMakeLists.txt
    tokens = {
        "@PLUGIN_NAME@": plugin_name,
        "@PLUGIN_CLASS@": plugin_class,
        "@PLUGIN_ID@": args.id or f"com.example.{plugin_class}",
        "@PLUGIN_LABEL@": args.label or plugin_class,
    }

    def substitute(text: str) -> str:
        for token, value in tokens.items():
            text = text.replace(token, value)
        return text

    dest.mkdir(parents=True)
    for src in sorted(TEMPLATE_DIR.iterdir()):
        target = dest / substitute(src.name)
        target.write_text(substitute(src.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
        step(f"created {target.relative_to(ROOT_DIR)}")
    ok(f"Plugin {plugin_name} created (ID {tokens['@PLUGIN_ID@']})")
    if not args.id:
        warn("Default ID com.example.* used — pass --id <reverse.dns> before shipping")
    step(f"Build it: python bootstrap.py b {plugin_name}")
    print()
    return 0


def run_clean(_args: argparse.Namespace) -> int:
    header("CLEAN")
    for path in (BUILD_DIR, DIST_DIR):
        if path.exists():
            step(f"Removing {path}")
            shutil.rmtree(path, ignore_errors=True)
    if USER_PRESETS.is_file():
        step(f"Removing {USER_PRESETS.name}")
        USER_PRESETS.unlink()
    ok("Clean")
    print()
    return 0


HELP_TEXT = """
OPENFX PLUGIN SERIES BUILD SYSTEM

OpenFX SDK comes from Conan (conancenter, pinned in conanfile.py); MSVC runtime is static.
CMake runs through the presets written by `conan install`; the generator
(e.g. Visual Studio version) is taken from your Conan profile.
`conan` is used from PATH, otherwise via `uvx conan`.
Plugins: plugins/<name>/ (auto-discovered). Shared code: common/include/ofxc/ofxc.h.

COMMANDS
  d            conan install (re-run automatically when conanfile.py/version.txt change)
  b [name]     configure + build all plugins, or only <name>
  i [name]     install all bundles, or only <name> (default: system OFX dir)
  p            install all bundles into dist/ and zip them
  c            stage-install and verify every bundle (plist, layout, OFX exports)
  new <Name>   create plugins/<name>/ from templates/plugin
  cl           remove build/, dist/, CMakeUserPresets.json
  h            help

OPTIONS
  -d, --debug         Debug build type (default: Release)
  --prefix DIR        install prefix for `i`
  --fresh             re-run conan install before `b`
  --id ID             OFX plugin ID for `new` (default: com.example.<Name>)
  --label TEXT        UI label for `new` (default: <Name>)

EXAMPLES
  python bootstrap.py b
  python bootstrap.py b colorFill
  python bootstrap.py c
  python bootstrap.py new MyGlow --id com.joss.MyGlow --label "My Glow"
  python bootstrap.py i --prefix %APPDATA%/OFX/Plugins
  python bootstrap.py p
  python bootstrap.py cl
"""

COMMANDS = ["d", "b", "i", "p", "c", "new", "cl", "h"]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)

    C.init()

    parser = argparse.ArgumentParser(
        description="OpenFX plugin series build system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("command", nargs="?", choices=COMMANDS, default="h", help=", ".join(COMMANDS))
    parser.add_argument("target", nargs="?", help="plugin name (b, i) or new plugin Name (new)")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug build type")
    parser.add_argument("--prefix", help="Install prefix (i)")
    parser.add_argument("--fresh", action="store_true", help="Re-run conan install before build (b)")
    parser.add_argument("--id", help="OFX plugin ID (new)")
    parser.add_argument("--label", help="UI label (new)")

    args = parser.parse_args()

    if args.command == "h":
        print(HELP_TEXT)
        return 0
    if args.target and args.command not in ("b", "i", "new"):
        err(f"`{args.command}` takes no plugin name")
        return 1

    dispatch = {
        "d": run_deps,
        "b": run_build,
        "i": run_install,
        "p": run_package,
        "c": run_check,
        "new": run_new,
        "cl": run_clean,
    }
    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
