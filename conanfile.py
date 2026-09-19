from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, cmake_layout
from conan.tools.files import load
import os


class OfxPluginsConan(ConanFile):
    name = "ofx-plugins"
    license = "MIT"
    author = "Alex Khal <joss13@gmail.com>"
    description = "OpenFX plugin series (template)"

    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain"
    exports = "version.txt"
    exports_sources = "CMakeLists.txt", "version.txt", "cmake/*", "common/*", "plugins/*", "templates/*"

    def set_version(self):
        self.version = load(self, os.path.join(self.recipe_folder, "version.txt")).strip()

    def requirements(self):
        # Pinned: openfx >= 1.5 requires C++17
        self.requires("openfx/1.5.1")

    def validate(self):
        check_min_cppstd(self, 17)
        # Plugins link the MSVC runtime statically: hosts may already have an older
        # msvcp140.dll loaded, and the OFX C API passes no CRT objects across the boundary.
        if self.settings.compiler == "msvc" and self.settings.compiler.runtime != "static":
            raise ConanInvalidConfiguration(
                "MSVC runtime must be static: pass -s compiler.runtime=static (bootstrap.py does)")

    def layout(self):
        cmake_layout(self)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
