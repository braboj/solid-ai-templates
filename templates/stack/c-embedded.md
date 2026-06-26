# Stack -- Embedded C
[DEPENDS ON: templates/base/core/git.md, templates/base/core/docs.md, templates/base/core/quality.md, templates/base/core/testing.md]

Conventions for bare-metal embedded C projects. Covers toolchain, project
structure, static analysis, unit testing with Unity, and distribution as
both a flashable binary and a static library.

---

## Stack
[ID: c-embedded-stack]

- Language: C17 (ISO/IEC 9899:2018)
- Toolchain: GCC (arm-none-eabi-gcc or native gcc for host tests)
- Build system: CMake 3.20+
- Static analyser: cppcheck + clang-tidy
- Test runner: Unity (unit tests compiled for host, not target)
- Distribution: flashable binary (.hex / .bin) + static library (.a)

---

## Project structure
[ID: c-embedded-structure]

```
CMakeLists.txt              # top-level build
src/
  [module]/
    [module].c              # implementation
    [module].h              # public API
  main.c                    # entry point (binary target only)
include/                    # public headers (library target)
tests/
  unity/                    # Unity test framework source
  test_[module].c           # one test file per module
  CMakeLists.txt
cmake/
  toolchain-arm.cmake       # cross-compilation toolchain file
  toolchain-host.cmake      # host toolchain for running tests
scripts/
  flash.sh                  # flash binary to target
  run_tests.sh              # build and run host tests
.env.example                # environment variables (tool paths, device)
README.md
CLAUDE.md
```

---

## C conventions
[ID: c-embedded-code]

- Use C17 -- do not use compiler extensions unless unavoidable; mark them
  with a comment if used
- One header per module; guard all headers with `#pragma once`
- No dynamic memory allocation on bare metal -- use static buffers and
  memory pools only
- No recursion -- stack depth must be statically determinable
- No global mutable state outside of hardware abstraction layer (HAL)
- Prefix all public symbols with the module name: `uart_init()`, `uart_read()`
- Use `stdint.h` types for fixed-width integers: `uint8_t`, `uint32_t`, etc.
- Use `stdbool.h` for boolean values -- not `int` flags
- Initialise all variables at declaration
- Keep functions under 40 lines; extract helpers for longer logic
- Use `const` for read-only parameters and pointers to read-only data
- Use `volatile` only for hardware registers and ISR-shared variables --
  document why on the same line

---

## Hardware abstraction
[ID: c-embedded-hal]

- Isolate all hardware register access in a HAL layer (`src/hal/`)
- HAL functions are the only place allowed to read/write memory-mapped
  registers
- Application code calls HAL functions only -- never accesses registers directly
- Mock the HAL in unit tests to run on the host without hardware

---

## Interrupt service routines
[ID: c-embedded-isr]

- Keep ISRs as short as possible -- set a flag or write to a queue, return
- Never call blocking functions or allocate memory inside an ISR
- Mark ISR-shared variables `volatile`
- Disable interrupts around read-modify-write on shared variables if not
  using an RTOS primitive

---

## Build targets
[ID: c-embedded-build]

- Define two CMake targets: `firmware` (cross-compiled) and `tests`
  (host-compiled)
- The `tests` target links against the Unity runner and the HAL mock
- Keep toolchain files in `cmake/` -- do not hardcode tool paths in
  `CMakeLists.txt`
- Set `-Wall -Wextra -Werror` for both targets -- treat all warnings as errors
- Set `-fstack-usage` on the firmware target to verify stack consumption

---

## Testing
[ID: c-embedded-testing]
[EXTEND: base-testing]
[OVERRIDE: base-testing-general]

- All tests run on the host (PC), not on the target hardware — real
  hardware dependencies are replaced with HAL mocks or hardware-in-the-loop
  simulators
- Mock the HAL layer to isolate modules under test
- One test file per module: `tests/test_[module].c`
- Use Unity macros: `TEST_ASSERT_EQUAL`, `TEST_ASSERT_NULL`, etc.
- Test naming: `test_<module>_<state>_<expected>`
  e.g. `test_uart_buffer_full_returns_error`
- Run before every commit: `cmake --build build/tests && ctest --test-dir build/tests`

---

## Static analysis
[ID: c-embedded-analysis]

- Run `cppcheck --enable=all --error-exitcode=1 src/` -- fix all findings
- Run `clang-tidy` with the project `.clang-tidy` config -- no suppressions
  without a comment explaining why
- Enable `-fsanitize=address,undefined` on the host test build

---

## Git conventions
[ID: c-embedded-git]
[EXTEND: base-git]

- Do not commit compiled output (`*.o`, `*.a`, `*.elf`, `*.hex`, `*.bin`,
  `build/`)
- Do not commit IDE project files (`.vscode/`, `.cproject`)
- Do commit the toolchain files in `cmake/` and the Unity source in
  `tests/unity/`

---

## Commands

```bash
# Configure (cross-compile for target)
cmake -B build/firmware -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain-arm.cmake

# Configure (host build for tests)
cmake -B build/tests -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain-host.cmake

# Build firmware
cmake --build build/firmware

# Build and run tests
cmake --build build/tests && ctest --test-dir build/tests -V

# Static analysis
cppcheck --enable=all --error-exitcode=1 src/

# Flash to target
./scripts/flash.sh build/firmware/firmware.hex
```