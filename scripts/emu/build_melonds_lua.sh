#!/usr/bin/env bash
# scripts/emu/build_melonds_lua.sh
# Builds the pinned melonDS-lua fork (NPO-197) with the GDB stub enabled,
# applying any patches in scripts/emu/patches/.
#
# macOS / Apple Silicon notes (learned the hard way, see README):
#   * The CMake option is ENABLE_GDBSTUB (not ENABLE_GDB_STUB). It defaults ON.
#   * Homebrew's `qt@6` is an alias for the `qt` formula; the whole formula is
#     needed because find_package(Qt6 ...) wants Core/Gui/Widgets/Network/
#     Multimedia/OpenGL/OpenGLWidgets/Svg from one prefix.
#   * `brew install lua` now installs Lua 5.5, which this fork does not build
#     against. Install lua@5.4 and point CMAKE_PREFIX_PATH at it. If plain
#     `lua` is linked it will win the FindLua search, so we unlink it.
#   * libarchive and lua@5.4 are keg-only, so both must be in CMAKE_PREFIX_PATH.
set -euo pipefail

REPO_URL="https://github.com/NPO-197/melonDS-lua"
PINNED_COMMIT="${PINNED_COMMIT:-c26edf0e0d75364823856c9272a103fe39e03999}"
SRC_DIR="${SRC_DIR:-$HOME/src/melonDS-lua}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- dependencies ---------------------------------------------------------
# dbus (a Qt dependency) wants to create this directory during install.
if [ -d /opt/homebrew/var/run ] && [ ! -w /opt/homebrew/var/run ]; then
  echo "WARNING: /opt/homebrew/var/run is not writable; the dbus formula may" >&2
  echo "         fail to create /opt/homebrew/var/run/dbus. This is harmless." >&2
fi

for pkg in cmake pkg-config lua@5.4 qt sdl2 libarchive enet zstd faad2; do
  brew list --formula "$pkg" >/dev/null 2>&1 || brew install "$pkg"
done

# Lua 5.5 (formula `lua`) breaks the build if it is the linked version.
if brew list --formula lua >/dev/null 2>&1; then
  if [ -e /opt/homebrew/include/lua.h ] && \
     ! grep -q '5\.4' /opt/homebrew/include/lua.h 2>/dev/null; then
    echo "Unlinking Lua 5.5 and linking lua@5.4"
    brew unlink lua
    brew link --overwrite lua@5.4
  fi
fi

# --- source --------------------------------------------------------------
if [ ! -d "$SRC_DIR" ]; then
  git clone --recursive "$REPO_URL" "$SRC_DIR"
fi
cd "$SRC_DIR"
git fetch --all
git checkout "$PINNED_COMMIT"
git reset --hard && git clean -fd
git submodule update --init --recursive

for p in "$SCRIPT_DIR"/patches/*.patch; do
  [ -e "$p" ] || continue
  echo "Applying $p"
  git apply "$p"
done

# --- build ---------------------------------------------------------------
PREFIX_PATH="$(brew --prefix qt);$(brew --prefix libarchive);$(brew --prefix lua@5.4)"

cmake -B build \
  -DCMAKE_BUILD_TYPE=Release \
  -DENABLE_GDBSTUB=ON \
  -DUSE_QT6=ON \
  -DCMAKE_PREFIX_PATH="$PREFIX_PATH"

cmake --build build -j"$(sysctl -n hw.logicalcpu)"

# --- record --------------------------------------------------------------
COMMIT=$(git rev-parse HEAD)
PATCHES=$(cd "$SCRIPT_DIR/patches" 2>/dev/null && shasum -a 256 *.patch 2>/dev/null || echo none)
cat > "$SCRIPT_DIR/build_info.json" <<EOF
{"fork_commit": "$COMMIT",
 "patches": "$(echo "$PATCHES" | tr '\n' ';')",
 "app_path": "$SRC_DIR/build/melonDS.app/Contents/MacOS/melonDS",
 "cmake_prefix_path": "$PREFIX_PATH",
 "built_at": "$(date -u +%FT%TZ)"}
EOF
echo "Built: $SRC_DIR/build/melonDS.app (commit $COMMIT)"
