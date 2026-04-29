# iTerm2 Agent Guide

> Essential guide for AI agents working on iTerm2.

## Critical Rules

**Read `CLAUDE.md` first** - it contains mandatory coding practices. Key rules:

1. **Never** write >1 line of JavaScript/HTML/CSS inline - use external files with `iTermBrowserTemplateLoader.swift`
2. Use `it_fatalError` and `it_assert` (not standard `fatalError`/`assert`) for proper crash logs
3. **Never** create dependency cycles - use delegates/closures instead
4. `git add` new files immediately after creation

## Architecture

**iTerm2** uses hybrid Objective-C/Swift: core system in Objective-C, modern features in Swift.

**Application Flow:** App → Window/Tab → Session → Terminal Emulation → Rendering

### Key Components

- **Application:** `iTermController` - Main coordinator
- **Window/Tab:** `PseudoTerminal`, `PTYTab` - Window and tab management
- **Session:** `PTYSession` - Session lifecycle, I/O, state
- **Terminal Emulation:** `VT100Parser`, `VT100Terminal`, `VT100ScreenMutableState`, `VT100Screen`, `VT100Grid`
- **Rendering:** `PTYTextView` - Metal-accelerated rendering

## Directory Structure

```
iTerm2/
├── sources/               # Main application code
├── ModernTests/           # Unit tests (~1924)
├── proto/api.proto        # Protocol Buffer API
├── tools/                 # Build scripts
├── submodules/            # Git submodules
├── WebExtensionsFramework/  # Swift SPM framework (see WebExtensionsFramework/CLAUDE.md)
├── iTerm2.sdef            # AppleScript API
├── CLAUDE.md              # Code best practices
└── iTerm2.xcodeproj/      # Xcode project
```

## Common Development Tasks

### Modifying Terminal Emulation
- Escape sequences flow: `VT100Parser`/`VT100Terminal` → `VT100ScreenMutableState`/`VT100Screen` → `VT100Grid`
- Look at `ModernTests/VT100ScreenTests.swift` for examples
- Test changes thoroughly

### Extending APIs
- **WebSocket API:** Edit `proto/api.proto`, run `tools/build_proto.sh`
- **AppleScript:** Edit `iTerm2.sdef`, implement in `*+Scripting.{h,m}` files

## Code Patterns

### Avoiding Dependency Cycles
```swift
// ❌ Bad: Strong reference cycle
class Parent { var child: Child? }
class Child { var parent: Parent? }

// ✅ Good: Use weak reference
class Child { weak var parent: Parent? }
```

### Using External Templates
```objc
// ✅ Good
NSString *html = [iTermBrowserTemplateLoader loadTemplateNamed:@"chat"];

// ❌ Bad: Inline HTML
NSString *html = @"<html><body>...</body></html>";
```

### Error Handling
```swift
// ✅ Good
it_fatalError("Unexpected state")
it_assert(value != nil, "Value required")

// ❌ Bad: Won't create crash logs
fatalError("Unexpected state")
assert(value != nil)
```

## Linting, Testing, and Coverage

### Linting

**Swift:**

| Tool | Command | Notes |
|---|---|---|
| **Compiler** | `make run` or `tools/build.sh` | Treat warnings as errors. Fix any new warnings before committing. |
| **SwiftLint** | `make swiftlint` | Static analysis. Config in `.swiftlint.yml`. Currently ~3736 warnings, ~16 errors in existing code. New code should not introduce errors. |

**Objective-C:**

| Tool | Command | Notes |
|---|---|---|
| **Compiler** | `make run` or `tools/build.sh` | Treat warnings as errors. Fix any new warnings before committing. |

**Python API** (`api/library/python/iterm2/`):

| Tool | Command | Notes |
|---|---|---|
| **mypy** | `make mypy` | Type checking. Uses `--ignore-missing-imports` to skip untyped dependencies. |
| **pylint** | `make pylint` | Style and correctness. Uses `--load-plugins=pylint_protobuf` for generated code. |

Pylint will report issues on `iterm2/api_pb2.py` (auto-generated protobuf). These are expected and not actionable — do not attempt to fix them.

### Running Tests

**Main application tests (Swift/ObjC):**

| Command | Description |
|---|---|
| `make test` | Runs all ~1924 tests in the ModernTests suite |
| `tools/run_tests.expect ModernTests/TestClass/testMethod` | Runs a specific test. Path format: `<scheme>/<class>/<method>`. Multiple paths accepted. |

**False positive:** `xcodebuild` may report `** TEST FAILED **` even when all tests pass. This is caused by WebKit entitlement warnings. Always verify with the summary line: `Executed N tests, with 0 failures (0 unexpected)`.

**Python API tests** (`api/library/python/iterm2/tests/`):

| Command | Description |
|---|---|
| `cd api/library/python/iterm2 && make test` | Runs all Python API tests (~1885 tests) with verbose output |
| `cd api/library/python/iterm2 && python3 -m pytest tests/test_session.py -v` | Runs tests for a specific module |
| `cd api/library/python/iterm2 && python3 -m pytest tests/test_session.py::test_property_access -v` | Runs a specific test function |

### Assessing Code Coverage

**Python API:**

```bash
cd api/library/python/iterm2 && make test-cov
```

This runs `pytest` with `--cov=iterm2 --cov-report=term-missing` and outputs per-module coverage with uncovered line numbers. Key metrics:

- **Target:** 80%+ overall coverage
- **High coverage (≥95%):** `rpc.py`, `tab.py`, `app.py`, `session.py`, `triggers.py`, `notifications.py`, `prompt.py`, `util.py`, `capabilities.py`
- **Expected low coverage (≤60%):** `auth.py` (OAuth flow), `tool.py` (registration helpers), `api_pb2.py` (generated protobuf), `tmux.py` (integration), `customcontrol.py` (protocol), `profile.py` (generated code with many untested accessors)

**Main application:** Coverage is measured by test execution count. The ModernTests suite covers terminal emulation, session logic, rendering, and scripting. There is no numeric coverage report — verify by checking that test count increases and no failures are introduced.

### Workflow Checklist

After making changes:

1. **Lint:** Run `make mypy` and `make pylint` (Python), `make swiftlint` (Swift), or `make run` (Swift/ObjC)
2. **Test:** Run `make test` (Swift/ObjC) and/or `cd api/library/python/iterm2 && make test` (Python)
3. **Coverage:** Run `cd api/library/python/iterm2 && make test-cov` (Python) to verify coverage hasn't regressed
4. **Commit:** Ensure no warnings, no test failures, and coverage is stable or improved

## Finding Your Way

**Language choice:**
- Use Objective-C when modifying existing Objective-C code
- Use Swift for new features
- Use `@objc` attributes for Swift/Objective-C interop
- The Swift bridging header is `sources/iTerm2SharedARC-Bridging-Header.h` - check here for available Objective-C types and constants in Swift

**Where code lives:**
- Session logic → `PTYSession.{h,m}`
- Terminal emulation → `VT100Parser`, `VT100Terminal`, `VT100ScreenMutableState`
- UI rendering → `PTYTextView.{h,m}`
- Unit tests → `ModernTests/` (main suite, ~1924 tests)
- Performance tests → `PerformanceTests/`
- Python API → `api/library/python/iterm2/iterm2/`
- Python API tests → `api/library/python/iterm2/tests/`
