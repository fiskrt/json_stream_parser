# Require CMake 3.15+ (matching scikit-build-core) Use new versions of all
# policies up to CMake 3.27
cmake_minimum_required(VERSION 3.15...3.27)

message(STATUS "🎯 Running CMake ...")
# Scikit-build-core sets these values
project(
  ${SKBUILD_PROJECT_NAME}
  VERSION ${SKBUILD_PROJECT_VERSION}
  LANGUAGES CXX)

# Find the module development requirements (requires FindPython from 3.17 or
# scikit-build-core's built-in backport)
find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)

# Define source files for the streaming JSON parser
set(PARSER_SOURCES
  cpp_src/jsonparser.cpp
)

# Define header files (for IDE integration)
set(PARSER_HEADERS
  cpp_src/jsonparser.h
)

# Add a library using FindPython's tooling
python_add_library(_core MODULE 
  cpp_src/bindings.cpp
  ${PARSER_SOURCES}
  WITH_SOABI
)

# Make sure the include directory is in the include path
target_include_directories(_core PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/cpp_src)

# Link against pybind11
target_link_libraries(_core PRIVATE pybind11::headers)

# This is passing in the version as a define just as an example
target_compile_definitions(_core PRIVATE VERSION_INFO=${PROJECT_VERSION})

# The install directory is the output (wheel) directory
install(TARGETS _core DESTINATION streamyjson)
message(STATUS "🎯 Finished Running CMake!")
