# AGENTS.md — OpenFX plugin series template

Monorepo of OpenFX image-effect plugins. Conan 2 provides the OpenFX SDK (openfx/1.5.1),
CMake presets drive the build, `bootstrap.py` is the single build entry point.
Windows-first (static MSVC runtime), layout follows the OFX packaging spec for macOS/Linux too.

## Entry points

| What | Where |
|------|-------|
| Build driver (SSOT for build commands) | `bootstrap.py` — `d`, `b [name]`, `i [name]`, `p`, `c`, `new <Name>`, `cl` |
| Windows one-click | `build.cmd` → `bootstrap.py b` + `i` |
| CI / Release | `.github/workflows/ci.yml`, `release.yml` → `bootstrap.py b`, `c`, `p` |
| Series version (SSOT) | `version.txt` (CMake `project(VERSION)`, Conan `set_version`, plist, factory version) |
| Series metadata | top of `CMakeLists.txt`: `OFX_PLUGIN_GROUPING`, `OFX_BUNDLE_ID_PREFIX` |
| Per-plugin metadata | `plugins/<name>/CMakeLists.txt` → `add_ofx_plugin_bundle(<name> ID ... LABEL ... SOURCES ...)` |
| Bundle/target logic | `cmake/OfxPlugin.cmake` |
| Shared C++ helpers | `common/include/ofxc/ofxc.h` (header-only target `ofx_common`) |
| Plugin scaffold | `templates/plugin/` (tokens `@PLUGIN_NAME@ @PLUGIN_CLASS@ @PLUGIN_ID@ @PLUGIN_LABEL@`) |
| Open work / history | latest `planN.md` |

## Build pipeline

```
version.txt ──┬───────────────────────────────┐
              v                               v
conanfile.py ─ conan install ─────────> build/generators/    CMakeLists.txt
  openfx/1.5.1   -s compiler.cppstd=17    toolchain, presets   ├─ series metadata
  validate():    -s compiler.runtime=static (MSVC)             ├─ include(cmake/OfxPlugin.cmake)
  C++17, static  (bootstrap.py; stamp in                       ├─ add_subdirectory(common)       -> ofx_common
  MSVC runtime    build/generators/.deps-<type>.json)          ├─ glob plugins/*/CMakeLists.txt  -> add_subdirectory each
                                                               └─ OFX_BUILD_TEMPLATE_CHECK: configure templates/plugin
                                                                  -> build/templateCheck (built, never installed)
cmake --preset conan-default ; cmake --build --preset conan-release [--target <name>]
    -> build/bin/Release/<name>.ofx           (multi-config; Linux/macOS: build/Release/bin/)
    -> build/plugins/<name>/Info.plist
cmake --install build --config Release [--prefix P] [--component <name>]
    -> P/<name>.ofx.bundle/Contents/Info.plist
    -> P/<name>.ofx.bundle/Contents/<Win64|MacOS|Linux-x86-64|...>/<name>.ofx
    default P = C:/Program Files/Common Files/OFX/Plugins/<OFX_PLUGIN_GROUPING>
```

`bootstrap.py`: `b` → deps if stamp stale → configure → build. `i`/`p`/`c` all go through
`install_bundles()` (always incremental-builds first). `c` installs into `build/_check_stage`
and validates each bundle: plist `CFBundleExecutable` == bundle name, exactly one
`Contents/<arch>/<exe>`, exports `OfxGetPlugin` + `OfxGetNumberOfPlugins` (PE parser on Windows, `nm` elsewhere).

## Runtime codepath (host → plugin), same for every plugin

```
host loads <name>.ofx  (MODULE, static CRT, exports only from libOfxSupport)
  └─ OfxGetNumberOfPlugins / OfxGetPlugin           libOfxSupport (ofxsImageEffect.cpp)
       └─ OFX::Plugin::getPluginIDs()               OFXC_REGISTER_PLUGIN(Factory)
            -> static Factory(PLUGIN_ID, PLUGIN_VERSION_MAJOR/MINOR)   defines from add_ofx_plugin_bundle()
Describe            -> Factory::describe()          ofxc::describeCommon(label, grouping) + contexts
DescribeInContext   -> Factory::describeInContext() clips (Source optional unless Filter), page + params
CreateInstance      -> Factory::createInstance()    Plugin ctor: fetchClip / fetch*Param
GetClipPreferences  -> Plugin::getClipPreferences() (colorFill: output unpremultiplied)
IsIdentity          -> Plugin::isIdentity()         (template: gain == 1 -> Source)
Render (per tile)   -> Plugin::render(args)
     ├─ ofxc::fetchImage(clip, args[, optional])    null/renderScale/field validation
     ├─ ofxc::dispatchPixelFormat(*dst, lambda)     depth x components -> PixelFormat<PIX,n,max>
     └─ ofxc::runProcessor(proc, *dst, args)        OFX::ImageProcessor::process()
          └─ multiThreadFunction -> multiThreadProcessImages(window slice)
               for y: abort()? ; dst = getPixelAddress(x1, y) ; per pixel toPixel/fromPixel
```

## Rules for agents

- Build/verify only through `bootstrap.py` (`cl`, `b`, `c`, `p`); don't hand-roll cmake/conan lines elsewhere.
- New plugin: `python bootstrap.py new <Name> --id <reverse.dns>`; never copy a plugin dir by hand.
- Never hardcode plugin names, versions or arch dirs outside `add_ofx_plugin_bundle()` calls,
  `version.txt`, and `cmake/OfxPlugin.cmake`. `bootstrap.py` derives them from installed bundles.
- Pixel access only via `OFX::Image::getPixelAddress(x, y)`; honour image depth/components through
  `ofxc::dispatchPixelFormat`; never assume float RGBA.
- Filter context requires a `Source` clip (spec); generators should still define an optional `Source`.
- Keep plugin IDs stable once shipped (hosts store them in projects).
- Template changes must keep compiling: `OFX_BUILD_TEMPLATE_CHECK` builds it on every build.
- MSVC runtime is static by policy (`conanfile.validate()`); don't switch to `/MD`.
- Don't use `add_ofx_plugin()` from the Conan-provided `OpenFX.cmake` build module (auto-included; it
  writes into Program Files at configure time and hardcodes a template path).
- `CMakeUserPresets.json`, `build/`, `dist/` are generated — never commit.
