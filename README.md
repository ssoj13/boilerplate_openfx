# OpenFX Plugin Series Template

[![CI](https://github.com/ssoj13/boilerplate_openfx/actions/workflows/ci.yml/badge.svg)](https://github.com/ssoj13/boilerplate_openfx/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Conan](https://img.shields.io/badge/Conan-2.x-blue.svg)](https://conan.io/)
[![OpenFX](https://img.shields.io/badge/OpenFX-1.5-green.svg)](https://openeffects.org/)

Monorepo template for a series of OpenFX plugins. One command scaffolds a new plugin,
one command builds, checks and packages all of them. OpenFX SDK comes from Conan.

![DaVinci Resolve Plugin](docs/davinci20.png)

**What you get:**
- `bootstrap.py` — build/install/check/package + `new <Name>` plugin scaffolding (stdlib Python)
- `add_ofx_plugin_bundle()` — one CMake call per plugin, correct `.ofx.bundle` layout per OFX spec
- `ofxc` shared header — pixel-format dispatch (8/16/32-bit × RGBA/RGB/Alpha), image fetch/validation,
  multi-threaded `OFX::ImageProcessor` runner, series-wide descriptor defaults, plugin registration
- Examples: **ColorFill** (generator) and the **template** (Gain filter with `isIdentity`)
- C++17, static MSVC runtime (the `.ofx` depends only on `KERNEL32.dll`)
- CI builds + verifies every push; tags publish a zipped release

## Project structure

```
├── plugins/
│   └── colorFill/
│       ├── CMakeLists.txt      # add_ofx_plugin_bundle(colorFill ID ... SOURCES ...)
│       └── colorFill.cpp       # plugin implementation
├── common/include/ofxc/ofxc.h  # shared helpers for all plugins
├── templates/plugin/           # scaffold used by `bootstrap.py new` (compiled on every build)
├── cmake/
│   ├── OfxPlugin.cmake         # add_ofx_plugin_bundle()
│   └── Info.plist.in           # bundle plist template
├── CMakeLists.txt              # series metadata (group, bundle-id prefix), plugin discovery
├── conanfile.py                # OpenFX SDK dependency, runtime/C++ policy
├── version.txt                 # series version (single source of truth)
├── bootstrap.py                # build driver
└── build.cmd                   # Windows one-click: build + install
```

## Build

**Prerequisites:** Python 3.8+, CMake 3.23+, Conan 2.x (or [uv](https://docs.astral.sh/uv/) — `uvx conan` is used automatically), Visual Studio 2022+

```cmd
python bootstrap.py b            &rem build all plugins (runs conan install when needed)
python bootstrap.py b colorFill  &rem build one plugin
python bootstrap.py c            &rem verify bundles: plist, layout, OFX exports
python bootstrap.py p            &rem dist/<bundles> + dist/<repo>-<version>-win64.zip
python bootstrap.py h            &rem all commands
```

Or just run `build.cmd` (build + install into the system OFX folder).

Under the hood: `conan install . -s compiler.cppstd=17 -s compiler.runtime=static`, then
`cmake --preset conan-default` and `cmake --build --preset conan-release`.
The Visual Studio version comes from your Conan profile. `build/`, `dist/` and
`CMakeUserPresets.json` are generated and not tracked.

## New plugin

```cmd
python bootstrap.py new MyGlow --id com.yourcompany.MyGlow --label "My Glow"
python bootstrap.py b myGlow
```

This creates `plugins/myGlow/` from `templates/plugin/` (a working Gain filter). CMake finds it automatically.
Then:
1. Replace the processor's `multiThreadProcessImages()` with your algorithm.
2. Add parameters in `describeInContext()` and fetch them in the constructor.
3. Adjust contexts/components in `describe()` / `describeInContext()`.

The plugin **ID** is what hosts store in saved projects: pick it once and never change it.
Per-plugin `VERSION` and `BUNDLE_ID` can be passed to `add_ofx_plugin_bundle()`; defaults come from
`version.txt` and `OFX_BUNDLE_ID_PREFIX`. Series-wide settings live at the top of `CMakeLists.txt`.

**Render pattern** (see `plugins/colorFill/colorFill.cpp`):
```cpp
void render(const OFX::RenderArguments &args) override {
    auto dst = ofxc::fetchImage(_dstClip, args);                  // validated, throws on failure
    auto src = ofxc::fetchImage(_srcClip, args, /*optional=*/true);
    ofxc::dispatchPixelFormat(*dst, [&](auto fmt) {               // 8/16/32-bit x RGBA/RGB/Alpha
        MyProcessor<decltype(fmt)> processor(*this, src.get());
        ofxc::runProcessor(processor, *dst, args);                // multi-threaded over renderWindow
    });
}
```
Inside the processor, access pixels only via `getPixelAddress(x, y)` and convert with
`ofxc::toPixel` / `ofxc::fromPixel`.

## Installation

- `python bootstrap.py i` — all bundles into `C:\Program Files\Common Files\OFX\Plugins\Joss_examples\` (needs admin rights)
- `python bootstrap.py i colorFill --prefix <dir>` — one bundle into a custom folder

Manual: copy `<name>.ofx.bundle` folders into your host's OFX plugin folder:
- **Nuke:** `C:\Program Files\Nuke##\plugins\`
- **Resolve:** `C:\Program Files\Blackmagic Design\DaVinci Resolve\OFX\Plugins\`
- **Common:** `C:\Program Files\Common Files\OFX\Plugins\`

## Usage

Restart your host app. Plugins show up under the `Joss_examples` group.

**Nuke Python:**
```python
colorFill = nuke.createNode("ColorFill")
colorFill['color'].setValue([1.0, 0.0, 0.0, 1.0])
```

## Troubleshooting

- **Plugin missing:** wrong folder or bundle layout (`python bootstrap.py c` verifies it), or the host needs a restart. Nuke blacklists plugins that failed to load once; touch the `.ofx` to retry.
- **Build fails after changing toolchain/profile:** `python bootstrap.py cl` then `b`.
- **`MSVC runtime must be static`:** you ran `conan install` by hand; add `-s compiler.runtime=static` or use `bootstrap.py`.

## GitHub Actions and releases

CI builds and checks every push/PR to `main` and uploads the bundles as an artifact.
Push a tag equal to `v` + `version.txt` to publish a GitHub Release with the zipped bundles:
```bash
git tag v1.0.0 && git push origin v1.0.0
```

## License

[MIT](LICENSE) © Alex Khal

## Acknowledgements

Special thanks to [Claude Code](https://www.anthropic.com/claude-code) and [Qwen Code](https://github.com/QwenLM/qwen-code) for simplifying boring tasks and tremendous help with development.
