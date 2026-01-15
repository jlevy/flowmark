#!/usr/bin/env python3
"""
Benchmark script for Flowmark performance testing.

Usage:
    # Benchmark current dev version
    uv run devtools/benchmark.py

    # Benchmark a specific released version
    uv run devtools/benchmark.py --version 0.6.0

    # Benchmark with profiling enabled
    uv run devtools/benchmark.py --profile

    # Compare current dev against a release
    uv run devtools/benchmark.py --compare 0.6.0

    # Custom test file and iterations
    uv run devtools/benchmark.py --file tests/testdocs/testdoc.orig.md --iterations 10
"""

from __future__ import annotations

import argparse
import cProfile
import io
import pstats
import statistics
import subprocess
import sys
import time
from pathlib import Path
from textwrap import dedent

DEFAULT_TEST_FILE = Path("tests/testdocs/testdoc.orig.md")
DEFAULT_ITERATIONS = 10


def benchmark_current(test_file: Path, iterations: int, semantic: bool = True) -> list[float]:
    """Benchmark the current dev version by importing directly."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from flowmark import reformat_text

    content = test_file.read_text()
    print("Benchmarking current dev version")
    print(f"File: {test_file} ({len(content)} chars, {len(content.splitlines())} lines)")
    print(f"Running {iterations} iterations...\n")

    times: list[float] = []
    for i in range(iterations):
        start = time.perf_counter()
        reformat_text(content, semantic=semantic)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Run {i + 1}: {elapsed * 1000:.1f}ms")

    return times


def benchmark_version(
    version: str, test_file: Path, iterations: int, semantic: bool = True
) -> list[float]:
    """Benchmark a specific released version using uvx."""
    content = test_file.read_text()
    print(f"Benchmarking v{version}")
    print(f"File: {test_file} ({len(content)} chars, {len(content.splitlines())} lines)")
    print(f"Running {iterations} iterations...\n")

    benchmark_script = dedent(f'''
        import time
        import statistics
        from pathlib import Path
        from flowmark import reformat_text

        content = Path("{test_file}").read_text()
        times = []
        for i in range({iterations}):
            start = time.perf_counter()
            reformat_text(content, semantic={semantic})
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            print(f"  Run {{i + 1}}: {{elapsed * 1000:.1f}}ms")

        # Output times as comma-separated for parsing
        print("TIMES:" + ",".join(str(t) for t in times))
    ''').strip()

    result = subprocess.run(
        ["uvx", f"--with=flowmark=={version}", "python", "-c", benchmark_script],
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode != 0:
        print(f"Error running v{version}: {result.stderr}", file=sys.stderr)
        return []

    # Print the run output (excluding the TIMES line)
    for line in result.stdout.splitlines():
        if not line.startswith("TIMES:"):
            print(line)

    # Parse times from output
    for line in result.stdout.splitlines():
        if line.startswith("TIMES:"):
            return [float(t) for t in line[6:].split(",")]

    return []


def print_stats(name: str, times: list[float]) -> None:
    """Print statistics for timing results."""
    if not times:
        print(f"{name}: No valid results")
        return
    print(f"\n{name}:")
    print(f"  Mean:   {statistics.mean(times) * 1000:.1f}ms")
    print(f"  Median: {statistics.median(times) * 1000:.1f}ms")
    print(f"  Min:    {min(times) * 1000:.1f}ms")
    print(f"  Max:    {max(times) * 1000:.1f}ms")
    if len(times) > 1:
        print(f"  StdDev: {statistics.stdev(times) * 1000:.1f}ms")


def profile_current(test_file: Path, semantic: bool = True) -> None:
    """Profile the current dev version and show top functions."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from flowmark import reformat_text

    content = test_file.read_text()
    print("Profiling current dev version")
    print(f"File: {test_file} ({len(content)} chars, {len(content.splitlines())} lines)\n")

    profiler = cProfile.Profile()
    profiler.enable()
    reformat_text(content, semantic=semantic)
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("cumulative")
    stats.print_stats(40)
    print(stream.getvalue())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark Flowmark performance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--version",
        "-v",
        help="Benchmark a specific released version (e.g., 0.6.0)",
    )
    parser.add_argument(
        "--compare",
        "-c",
        help="Compare current dev against a specific version (e.g., 0.6.0)",
    )
    parser.add_argument(
        "--profile",
        "-p",
        action="store_true",
        help="Run profiling on current dev version",
    )
    parser.add_argument(
        "--file",
        "-f",
        type=Path,
        default=DEFAULT_TEST_FILE,
        help=f"Test file to use (default: {DEFAULT_TEST_FILE})",
    )
    parser.add_argument(
        "--iterations",
        "-n",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"Number of iterations (default: {DEFAULT_ITERATIONS})",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Use plain line wrapping instead of semantic",
    )

    args = parser.parse_args()
    semantic = not args.plain

    if not args.file.exists():
        print(f"Error: Test file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    if args.profile:
        profile_current(args.file, semantic=semantic)
    elif args.compare:
        current_times = benchmark_current(args.file, args.iterations, semantic=semantic)
        print()
        old_times = benchmark_version(args.compare, args.file, args.iterations, semantic=semantic)

        print_stats("Current dev version", current_times)
        print_stats(f"v{args.compare}", old_times)

        if current_times and old_times:
            current_mean = statistics.mean(current_times)
            old_mean = statistics.mean(old_times)
            ratio = current_mean / old_mean
            diff_pct = (ratio - 1) * 100
            print("\nComparison:")
            if ratio > 1:
                print(f"  Current is {diff_pct:.1f}% slower than v{args.compare}")
            else:
                print(f"  Current is {abs(diff_pct):.1f}% faster than v{args.compare}")
            print(f"  Ratio: {ratio:.2f}x")
    elif args.version:
        times = benchmark_version(args.version, args.file, args.iterations, semantic=semantic)
        print_stats(f"v{args.version}", times)
    else:
        times = benchmark_current(args.file, args.iterations, semantic=semantic)
        print_stats("Current dev version", times)


if __name__ == "__main__":
    main()
