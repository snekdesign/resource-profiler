cmake_minimum_required(VERSION 3.30)

project(
    ${SKBUILD_PROJECT_NAME}
    VERSION ${SKBUILD_PROJECT_VERSION}
    LANGUAGES C
)

include(CheckIPOSupported)
check_ipo_supported()

set(CMAKE_C_STANDARD 17)

find_package(
    Python 3.9...<3.14
    COMPONENTS Development.SABIModule
    REQUIRED
)
find_package(Cython MODULE REQUIRED)
include(UseCython)

cython_transpile(
    src/resource_profiler/__init__.py
    LANGUAGE C
    OUTPUT_VARIABLE RESOURCE_PROFILER_INIT
)
Python_add_library(
    __init__
    MODULE USE_SABI 3.9
    ${RESOURCE_PROFILER_INIT}
)
target_link_directories(__init__ PRIVATE target/release)
target_link_libraries(
    __init__
    PRIVATE
    bcrypt comctl32 dwmapi shlwapi tauri
    $ENV{CONDA_PREFIX}/Library/x86_64-w64-mingw32/sysroot/usr/lib/libntoskrnl.a
)
install(
    TARGETS __init__
    DESTINATION ${SKBUILD_PROJECT_NAME}
)
