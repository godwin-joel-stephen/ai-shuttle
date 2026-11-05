#!/bin/zsh
# Build and run the schedule-import eval (or sample generator) on this Mac.
# Compiles the app's own ScheduleImport sources for macOS, so the eval
# measures exactly the prompt, schema, rules and validation the app ships.
set -e
here=${0:A:h}
src=$here/../ScheduleImport
bin=$here/.build/schedule-eval
mkdir -p $here/.build

# Xcode 26.4.1 can hang on its clang version probe; kill it if it appears.
( while true; do sleep 3; pkill -f "clang -v -E -dM" 2>/dev/null || true; done ) &
watchdog=$!
trap "kill $watchdog 2>/dev/null" EXIT

xcrun swiftc -O -o $bin \
  -sdk $(xcrun --sdk macosx --show-sdk-path) -target arm64-apple-macos26.0 \
  -swift-version 5 -default-isolation MainActor \
  -enable-upcoming-feature MemberImportVisibility \
  -enable-upcoming-feature InferSendableFromCaptures \
  -enable-upcoming-feature NonisolatedNonsendingByDefault \
  -enable-upcoming-feature InferIsolatedConformances \
  -enable-upcoming-feature GlobalActorIsolatedTypesUsability \
  $src/ScheduleModels.swift $src/DocumentSafety.swift $src/ScheduleTextReader.swift \
  $src/RuleBasedScheduleParser.swift $src/ScheduleExtractor.swift \
  $here/ScheduleRenderer.swift $here/main.swift

kill $watchdog 2>/dev/null
$bin "$@"
