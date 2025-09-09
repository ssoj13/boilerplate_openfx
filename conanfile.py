from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy
import os

class ColorFillPlugin(ConanFile):
    name = "colorfill-plugin"
    version = "1.0.0"
    
    # Package metadata
    license = "Custom"
    description = "ColorFill OpenFX Plugin"
    
    # Binary configuration
    settings = "os", "arch", "compiler", "build_type"
    
    # Requirements
    def requirements(self):
        self.requires("openfx/[>=1.4.0]")
    
    # Layout
    def layout(self):
        cmake_layout(self)
    
    # Generate files
    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()
        
        tc = CMakeToolchain(self)
        if self.settings.os == "Windows":
            tc.preprocessor_definitions["WINDOWS"] = 1
            tc.preprocessor_definitions["NOMINMAX"] = 1
        tc.generate()
    
    # Build
    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
    
    # Package (optional, for when building as a package)
    def package(self):
        copy(self, "*.ofx", src=self.build_folder, dst=os.path.join(self.package_folder, "bin"), keep_path=False)
        copy(self, "Info.plist", src=self.source_folder, dst=os.path.join(self.package_folder, "bundle"))