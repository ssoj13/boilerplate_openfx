# plan1 — Bug hunt report & fix plan

Status: **implemented** (approved 2026-09-18). Scope widened by the user: the repo is now a
**monorepo template for a series of OpenFX plugins** (see section 4).
Scope: whole repo (`src/`, `CMakeLists.txt`, `conanfile.py`, `bootstrap.py`, `build.cmd`, CI, README).
Verified against: OpenFX SDK 1.5.1 (Conan package headers in `~/.conan2/p/b/openf*/p/include`,
sources in `../openfx` at `OFX_Release_1.5.1-13`), OFX spec docs
(`../openfx/Documentation/sources/Reference/ofxImageEffectContexts.rst`), official generator
example `../openfx/Support/Plugins/Generator/noise.cpp`.

## 0. Already done (previous steps of this session)

- [x] Build revived: Conan 2 + openfx pinned `1.5.1`, C++17, CMake presets, no configure-time writes to Program Files.
- [x] `bootstrap.py` (d/b/i/p/c/cl) adapted from gitnexus-rs; `build.cmd` and CI delegate to it.
- [x] `version.txt` is SSOT (CMake `project(VERSION)`, Conan `set_version`, Info.plist, plugin factory version).
- [x] Plugin metadata block in `CMakeLists.txt` → `PLUGIN_ID` / `PLUGIN_GROUPING` / version passed to C++ as defines.
- [x] `Info.plist.in` → `cmake/Info.plist.in`; stale `.gitmodules` and generated `CMakeUserPresets.json` untracked.
- [x] Release job checks tag == `v$(version.txt)`.

## 1. Findings

Severity: **CRIT** = memory corruption / host rejects plugin; **HIGH** = wrong output / spec violation;
**MED** = robustness, SSOT, dead code; **LOW** = cleanup.

### C++ plugin (`src/`)

| # | Sev | Where | Problem | Evidence |
|---|-----|-------|---------|----------|
| B1 | CRIT | `src/colorFill.cpp:57-58` vs `:26,35-43` | Declares `UByte`/`UShort` support but `render()` always writes `float` RGBA. On 8/16-bit output it writes 4×/2× past each row → heap corruption / host crash. | `render()` casts to `float*` unconditionally. Reference `noise.cpp:169-222` dispatches on `getPixelDepth()`. |
| B2 | CRIT | `src/colorFill.cpp:34-36` | Row address = `getPixelData() + y*rowBytes` ignores image `bounds` (`getPixelData()` points at `(bounds.x1,bounds.y1)`), and `x` is never offset by `bounds.x1`. With tiles/multi-res enabled (`:62-63,73`) and any non-zero-origin image, writes outside the buffer. | `ofxsImageEffect.h:541` `getBounds()`, `:586` `getPixelAddress(x,y)`; `noise.cpp:62` uses `getPixelAddress(procWindow.x1, y)`. |
| B3 | HIGH | `src/colorFill.cpp:55,70-73` | Supports `eContextFilter` but defines no `Source` clip. Spec: filter context "has to have one and only one input clip, called *Source*". Hosts may refuse to load/instantiate. | `ofxExample4_Saturation.rst:23-25`; `noise.cpp:253-258` defines an optional Source even for generators. |
| B4 | HIGH | `src/colorFill.cpp:53-56` | Plugin is a generator but does not advertise `eContextGenerator` → not offered as a generator in hosts that list generators separately (Resolve "Generators", Nuke). | `noise.cpp:236-237`. |
| B5 | MED | `src/colorFill.h:3-4`, `src/colorFill.cpp:3` + `:52-65` | `ofxsMultiThread.h` included, `setRenderThreadSafety(eRenderFullySafe)` + `setHostFrameThreading(false)` declared, but render is single-threaded and ignores `abort()`. Unfinished piece: SDK `OFX::ImageProcessor` (`ofxsProcessing.h:28-160`) is the intended path (MT slicing, bounds check, GPU hooks). | `ofxsProcessing.h:88-107` (`multiThreadFunction`), `:144-160` (`process()` bounds guard). |
| B6 | MED | `src/colorFill.cpp:21-23` | `throw std::runtime_error` without `<stdexcept>`; SDK idiom is `OFX::throwSuiteStatusException(kOfxStatFailed)` (SDK `mainEntry` does catch `std::exception` → `kOfxStatFailed`, `ofxsImageEffect.cpp:2877`, so behaviour is the same, but the header is missing and the idiom differs). | `ofxsCore.h:214`. |
| B7 | MED | `src/colorFill.cpp` (no `getClipPreferences`) | Output premultiplication state undeclared; the fill writes straight (unpremultiplied) RGBA. Declare `setOutputPremultiplication(eImageUnPreMultiplied)` so hosts treat alpha correctly. Behaviour of pixel values unchanged. | `ofxsImageEffect.h:1144`. |
| B8 | LOW | `src/colorFill.cpp:26` | `pixelData` computed and never used. | — |
| B9 | LOW | `src/colorFill.cpp:4-9`, `src/colorFill.h:6` | Unused includes: `ofxCore.h`, `ofxPixels.h`, `<cstring>`, `<algorithm>`, `<memory>` (header). | grep. |
| B10 | LOW | `src/colorFill.h:11` | `virtual ... override final` — `virtual` redundant. | — |
| B11 | LOW | `src/colorFill.cpp:74-77` | RGBA param has no hint/script name; no `PageParamDescriptor` (some hosts show nothing without a page). | `noise.cpp:263-276`. |

### Build system

| # | Sev | Where | Problem | Fix |
|---|-----|-------|---------|-----|
| S1 | MED | `CMakeLists.txt:65` | Links `openfx::openfx` = `Support` + `HostSupport` + `expat`. A plugin needs only `openfx::Support`. | `target_link_libraries(... openfx::Support)`. |
| S2 | MED | `CMakeLists.txt:48` | `SHARED` produces `.lib/.exp` import libs for a dlopen'ed module; official `add_ofx_plugin` uses `MODULE` on Apple. `MODULE` is the correct CMake kind for plugins on all platforms. | `add_library(... MODULE ...)`, install via `LIBRARY DESTINATION` only. |
| S3 | LOW | `CMakeLists.txt:54` | `C_VISIBILITY_PRESET` in a `LANGUAGES CXX` project. | Drop. |
| S4 | MED | `conanfile.py:41-42` | Injects `WINDOWS` and `NOMINMAX` globally. SDK uses only `_WIN32` (`ofxCore.h:25`) and never includes `windows.h` → both dead. | Remove; use `generators = "CMakeDeps", "CMakeToolchain"`. |
| S5 | MED | `conanfile.py:17,46-55` | `build()`/`package()` exist but no `exports_sources` → `conan create` cannot build. | Add `exports_sources = "CMakeLists.txt", "version.txt", "src/*", "cmake/*"`; verify `conan create`. |
| S6 | INFO | `OpenFX.cmake` (Conan build module, auto-included) | Package's `add_ofx_plugin()` is unusable (hardcodes `Examples/Info.plist.in`, writes plist into Program Files at configure) and it sets global `PLUGIN_INSTALLDIR`/`ARCHDIR`. We intentionally keep our own logic; document why in `CMakeLists.txt`. | Comment only. |
| S7 | DECISION | toolchain / profile | Dynamic CRT (`MSVCP140.dll`, `VCRUNTIME140*.dll`) — works in Resolve/Nuke (they ship the runtime), static CRT (`/MT`) is common for plugins to avoid DLL-version clashes. Needs openfx rebuilt with `compiler.runtime=static` (Conan does it with `--build=missing`). | **Ask user.** |

### `bootstrap.py` / CI

| # | Sev | Where | Problem | Fix |
|---|-----|-------|---------|-----|
| T1 | MED | `bootstrap.py:284-290,310` | `c` relies on `dumpbin`, absent outside VS dev shell (and on CI) → export check silently degrades to WARN. | Parse the PE export table in stdlib Python (Windows); keep `nm` on Linux/macOS. One `list_exports()` path. |
| T2 | MED | `bootstrap.py:58,60` | `PLUGIN_NAME`, `ARCHDIR` duplicate CMake (SSOT is `CMakeLists.txt`). | Derive from artifacts: binary = `build/<Type>/*.ofx`, bundle = `<prefix>/*.ofx.bundle`, archdir = the single dir under `Contents/` holding the `.ofx`. |
| T3 | LOW | `bootstrap.py:48` | `IS_LINUX` unused. | Drop. |
| T4 | LOW | `.github/workflows/ci.yml:26`, `release.yml:34` | `conan profile detect --force` duplicates `bootstrap.py d` profile detection. | Drop the step. |
| T5 | LOW | `.github/workflows/ci.yml` upload path | Hardcodes `dist/colorFill.ofx.bundle/`. | `dist/*.ofx.bundle`. |

### Docs

| # | Sev | Where | Problem |
|---|-----|-------|---------|
| D1 | MED | `README.md:82-84` | "Rename"/"Update plugin ID" steps are stale — metadata now lives in the `CMakeLists.txt` block. |
| D2 | LOW | `README.md:70` | "Find ColorFill under Color or Custom effects" — grouping is `PLUGIN_GROUPING` (`Joss_examples`). |
| D3 | LOW | `README.md` structure tree | Missing `bootstrap.py`, `cmake/`, `version.txt`. |
| D4 | DECISION | repo root | README + `conanfile.py` claim MIT, but there is no `LICENSE` file. **Ask user** (copyright holder / year). |

## 2. Plan (execute after approval)

- [x] P1 Rewrite render path on `OFX::ImageProcessor` (B1, B2, B5, B6, B8): one templated `FillProcessor<PIX, nComp, max>`; one `render()` dispatch over depth × components (RGBA, Alpha); `getPixelAddress`, `abort()` checks, `throwSuiteStatusException`.
- [x] P2 Contexts & clips (B3, B4): contexts Generator + Filter + General; `Source` clip defined (optional outside Filter), Output RGBA + Alpha; `getClipPreferences` → unpremultiplied (B7).
- [x] P3 Param polish (B11): page, hint, script name.
- [x] P4 Include/`virtual` cleanup (B9, B10).
- [x] P5 CMake: `MODULE`, `openfx::Support`, drop C preset, comment about `OpenFX.cmake` (S1-S3, S6).
- [x] P6 Conan: generators attribute, drop dead defines, `exports_sources`; verify `conan create` (S4, S5).
- [x] P7 bootstrap: PE export parser, artifact-derived names, drop `IS_LINUX` (T1-T3); CI cleanup (T4, T5).
- [x] P8 README / AGENTS.md / DIAGRAMS.md refresh (D1-D3).
- [x] P9 Verify: `bootstrap.py cl && b && c && p` (Release + Debug), `conan create`, exports check, bundle layout.
- [x] P10 Decisions from user: S7 (static CRT?), D4 (LICENSE holder).

## 3. Not changed on purpose

- Plugin ID `com.example.ColorFill` kept: changing it orphans the effect in saved host projects.
- Own ARCHDIR/install logic kept instead of `add_ofx_plugin()` (S6).
- Non-Windows export visibility: `OfxExport` is plain `extern` on non-Windows (`ofxCore.h:25-29`); exports come from `libOfxSupport` compiled with default visibility, our `CXX_VISIBILITY_PRESET hidden` affects only our TU. Not verified on Linux/macOS (no toolchain here).

## 4. Outcome (what was actually done)

Decisions: S7 → **static MSVC runtime** (researched: Microsoft advises /MD for DLLs because of CRT
objects crossing DLL boundaries and the FLS slot limit; the OFX C API passes no CRT objects, the FLS
limit was raised to 4000 in Windows 10 1903, and /MT avoids clashes with an older `msvcp140.dll`
already loaded by the host). Enforced in `conanfile.py` `validate()`, passed by `bootstrap.py`.
D4 → `LICENSE` MIT, © 2026 Alex Khal <joss13@gmail.com>.

Restructure (user request "template for a series of plugins", monorepo chosen):
- `plugins/<name>/` auto-discovered; `cmake/OfxPlugin.cmake` `add_ofx_plugin_bundle()` (MODULE,
  `openfx::Support` via `ofx_common`, per-plugin install COMPONENT, arch dir per OFX packaging spec).
- `common/include/ofxc/ofxc.h`: `PixelFormat`/`dispatchPixelFormat`, `toPixel`/`fromPixel`,
  `fetchImage(clip, args, optional)`, `runProcessor`, `describeCommon`, `OFXC_REGISTER_PLUGIN`.
- `plugins/colorFill/colorFill.cpp`: B1–B11 fixed on top of `ofxc` (ImageProcessor, all depths,
  RGBA+Alpha, getPixelAddress, abort, Generator+Filter+General, Source clip, unpremultiplied output, page/hint).
- `templates/plugin/`: Gain filter scaffold (Source handling outside src bounds, format mismatch
  check, isIdentity). Instantiated and compiled on every build (`OFX_BUILD_TEMPLATE_CHECK`), never installed.
- `bootstrap.py`: `new <Name> [--id --label]`, `b/i [name]`, `c` = stage install + plist/layout/exports
  (stdlib PE parser), names/arch derived from installed bundles, deps stamp (recipe hash) → auto `conan install`.
- CI: no duplicate profile step; artifacts `dist/*.ofx.bundle`; release zip includes LICENSE + README.

Verification (Windows, VS 2026 / MSVC 19.50, Conan 2.32 via uvx):
- `cl → b → c → p` from scratch: OK, no compiler warnings; `colorFill.ofx` depends only on `KERNEL32.dll`.
- `b -d` (Debug, static debug runtime): OK.
- `new MyGlow --id com.joss.MyGlow` → auto-discovered, built, `c` validated both bundles; test plugin removed.
- `new` rejects existing / invalid names; `i colorFill --prefix` installs one component.
- `conan create` with static runtime: OK (package removed from cache afterwards); with dynamic runtime:
  rejected by `validate()`.
- `pe_exports` cross-checked on `kernel32.dll` (1697 exports) and `colorFill.ofx`.
- Not verified: loading in a real host (Resolve/Nuke), GitHub Actions run, Linux/macOS builds.
