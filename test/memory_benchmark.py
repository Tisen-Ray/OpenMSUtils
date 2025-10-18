#!/usr/bin/env python3
"""
Memory Usage Benchmark: Python vs Rust
"""

import time
import gc
import sys

def get_memory_usage():
    """Get current memory usage in MB"""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        print("psutil not available, cannot measure memory usage")
        return None

def benchmark_memory_usage():
    """Benchmark memory usage comparison"""
    print("Memory Usage Benchmark: Python vs Rust")
    print("=" * 45)

    if get_memory_usage() is None:
        print("Cannot run memory benchmark without psutil")
        print("Install with: pip install psutil")
        return

    num_peaks = 50000
    print(f"Testing memory usage with {num_peaks:,} peaks")
    print()

    # Test Python implementation
    print("1. Python MSObject Memory Usage:")
    print("-" * 35)

    try:
        from OpenMSUtils.SpectraUtils.MSObject import MSObject as PythonMSObject

        # Baseline memory
        gc.collect()
        baseline = get_memory_usage()
        print(f"  Baseline memory: {baseline:.1f} MB")

        # Create Python MSObject and add peaks
        ms_obj = PythonMSObject(level=2)
        for i in range(num_peaks):
            ms_obj.add_peak(100.0 + i * 0.001, 1000.0 + i * 10)

        python_memory = get_memory_usage() - baseline
        print(f"  After adding peaks: {get_memory_usage():.1f} MB")
        print(f"  Python memory usage: {python_memory:.1f} MB")
        print(f"  Memory per peak: {python_memory * 1024 / num_peaks:.2f} KB/peak")

        # Clean up
        del ms_obj
        gc.collect()

    except Exception as e:
        print(f"  Python implementation failed: {e}")
        python_memory = None

    print()

    # Test Rust implementation
    print("2. Rust TestMSObject Memory Usage:")
    print("-" * 35)

    try:
        from _openms_utils_rust import TestMSObject

        # Baseline memory
        gc.collect()
        baseline = get_memory_usage()
        print(f"  Baseline memory: {baseline:.1f} MB")

        # Create Rust TestMSObject and add peaks
        test_obj = TestMSObject(0)
        for i in range(num_peaks):
            test_obj.add_peak(100.0 + i * 0.001, 1000.0 + i * 10)

        rust_memory = get_memory_usage() - baseline
        print(f"  After adding peaks: {get_memory_usage():.1f} MB")
        print(f"  Rust memory usage: {rust_memory:.1f} MB")
        print(f"  Memory per peak: {rust_memory * 1024 / num_peaks:.2f} KB/peak")

        # Clean up
        del test_obj
        gc.collect()

    except Exception as e:
        print(f"  Rust implementation failed: {e}")
        rust_memory = None

    print()

    # Memory efficiency comparison
    if python_memory and rust_memory:
        print("3. Memory Efficiency Comparison:")
        print("-" * 35)

        efficiency = python_memory / rust_memory
        print(f"  Python memory: {python_memory:.1f} MB")
        print(f"  Rust memory:   {rust_memory:.1f} MB")
        print(f"  Memory efficiency: {efficiency:.1f}x (Rust uses {efficiency:.1f}x less memory)")

        if efficiency > 2:
            print("  -> Significant memory savings with Rust!")
        elif efficiency > 1.2:
            print("  -> Moderate memory savings with Rust")
        else:
            print("  -> Similar memory usage")

    print()

    # Large dataset test
    print("4. Large Dataset Memory Test:")
    print("-" * 30)

    large_num_peaks = 200000
    print(f"Testing with {large_num_peaks:,} peaks")

    try:
        from _openms_utils_rust import TestMSObject

        gc.collect()
        baseline = get_memory_usage()

        large_obj = TestMSObject(0)
        for i in range(large_num_peaks):
            large_obj.add_peak(100.0 + i * 0.001, 1000.0 + i * 10)

        large_memory = get_memory_usage() - baseline
        print(f"  Large dataset memory: {large_memory:.1f} MB")
        print(f"  Memory per peak: {large_memory * 1024 / large_num_peaks:.2f} KB/peak")
        print(f"  Total peaks stored: {large_obj.peak_count()}")

        del large_obj
        gc.collect()

    except Exception as e:
        print(f"  Large dataset test failed: {e}")

    print()
    print("MEMORY BENCHMARK SUMMARY")
    print("=" * 45)

    if python_memory and rust_memory:
        print(f"Python memory per peak:  {python_memory * 1024 / num_peaks:.2f} KB")
        print(f"Rust memory per peak:    {rust_memory * 1024 / num_peaks:.2f} KB")
        print(f"Memory efficiency:       {efficiency:.1f}x")

    print("\nCONCLUSION:")
    if 'efficiency' in locals() and efficiency > 1.5:
        print("RUST provides significant memory efficiency improvements")
    elif 'efficiency' in locals() and efficiency > 1.0:
        print("RUST provides moderate memory efficiency improvements")
    else:
        print("Memory usage is comparable between implementations")

if __name__ == "__main__":
    benchmark_memory_usage()