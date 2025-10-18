#!/usr/bin/env python3
"""
Simple Python vs Rust Performance Benchmark
"""

import time
import statistics

def benchmark_peak_operations():
    """Simple benchmark for peak operations"""
    print("OpenMSUtils Python vs Rust Performance Benchmark")
    print("=" * 50)

    # Test data
    num_peaks = 10000
    peaks = [(100.0 + i * 0.001, 1000.0 + i * 10) for i in range(num_peaks)]

    print(f"Testing with {num_peaks:,} peaks")
    print()

    # 1. Peak Addition
    print("1. Peak Addition Performance:")
    print("-" * 30)

    # Test Python MSObject (if available)
    try:
        from OpenMSUtils.SpectraUtils.MSObject import MSObject as PythonMSObject

        python_times = []
        for i in range(3):
            ms_obj = PythonMSObject(level=2)
            start = time.perf_counter()
            for mz, intensity in peaks:
                ms_obj.add_peak(mz, intensity)
            elapsed = time.perf_counter() - start
            python_times.append(elapsed)
            print(f"  Python run {i+1}: {elapsed:.4f}s")

        avg_python = statistics.mean(python_times)
        python_speed = num_peaks / avg_python
        print(f"  Python average: {avg_python:.4f}s ({python_speed:.0f} peaks/s)")

    except Exception as e:
        print(f"  Python version not available: {e}")
        avg_python = None
        python_speed = 0

    # Test Rust TestMSObject
    try:
        from _openms_utils_rust import TestMSObject

        rust_times = []
        for i in range(3):
            test_obj = TestMSObject(0)
            start = time.perf_counter()
            for mz, intensity in peaks:
                test_obj.add_peak(mz, intensity)
            elapsed = time.perf_counter() - start
            rust_times.append(elapsed)
            print(f"  Rust run {i+1}: {elapsed:.4f}s")

        avg_rust = statistics.mean(rust_times)
        rust_speed = num_peaks / avg_rust
        print(f"  Rust average: {avg_rust:.4f}s ({rust_speed:.0f} peaks/s)")

        if avg_python:
            speedup = avg_python / avg_rust
            print(f"  Speedup: {speedup:.1f}x faster")

    except Exception as e:
        print(f"  Rust version failed: {e}")

    print()

    # 2. Peak Sorting
    print("2. Peak Sorting Performance:")
    print("-" * 30)

    # Create unsorted data
    unsorted_peaks = [(1000.0 - i * 0.1, 1000.0 + i * 10) for i in range(num_peaks)]

    # Test Python sorting
    try:
        python_sort_times = []
        for i in range(3):
            ms_obj = PythonMSObject(level=2)
            for mz, intensity in unsorted_peaks:
                ms_obj.add_peak(mz, intensity)

            start = time.perf_counter()
            ms_obj.sort_peaks()
            elapsed = time.perf_counter() - start
            python_sort_times.append(elapsed)
            print(f"  Python sort {i+1}: {elapsed:.4f}s")

        avg_python_sort = statistics.mean(python_sort_times)
        print(f"  Python average: {avg_python_sort:.4f}s")

    except Exception as e:
        print(f"  Python sorting failed: {e}")
        avg_python_sort = None

    # Test Rust sorting
    try:
        from _openms_utils_rust import Spectrum

        rust_sort_times = []
        for i in range(3):
            spectrum = Spectrum(0)
            for mz, intensity in unsorted_peaks:
                spectrum.add_peak(mz, intensity)

            start = time.perf_counter()
            spectrum.sort_peaks()
            elapsed = time.perf_counter() - start
            rust_sort_times.append(elapsed)
            print(f"  Rust sort {i+1}: {elapsed:.4f}s")

        avg_rust_sort = statistics.mean(rust_sort_times)
        print(f"  Rust average: {avg_rust_sort:.4f}s")

        if avg_python_sort and avg_python_sort > 0:
            sort_speedup = avg_python_sort / avg_rust_sort
            print(f"  Speedup: {sort_speedup:.1f}x faster")

    except Exception as e:
        print(f"  Rust sorting failed: {e}")

    print()

    # 3. Peak Filtering (Rust only)
    print("3. Peak Filtering Performance (Rust):")
    print("-" * 35)

    try:
        from _openms_utils_rust import Spectrum

        filter_times = []
        for i in range(3):
            spectrum = Spectrum(0)
            for mz, intensity in peaks:
                spectrum.add_peak(mz, intensity)

            start = time.perf_counter()
            removed = spectrum.filter_by_intensity(5000.0)
            elapsed = time.perf_counter() - start
            filter_times.append(elapsed)
            print(f"  Rust filter {i+1}: {elapsed:.4f}s (removed {removed} peaks)")

        avg_filter = statistics.mean(filter_times)
        print(f"  Rust average: {avg_filter:.4f}s")
        print(f"  Filtering speed: {num_peaks/avg_filter:.0f} peaks/s")

    except Exception as e:
        print(f"  Rust filtering failed: {e}")

    print()

    # 4. MZML File Processing
    print("4. MZML File Processing:")
    print("-" * 25)

    test_file = r"C:\Users\Administrator\Desktop\20250103-ZMT-NSP-IMS-VTP1-3.mzML"

    if os.path.exists(test_file):
        try:
            from OpenMSUtils.SpectraUtils import MZMLReader, SpectraConverter

            # Test Rust backend
            print("  Testing Rust MZML processing...")
            start = time.perf_counter()
            reader_rust = MZMLReader(test_file, use_rust=True)
            spectra_rust = reader_rust.read_first_spectra(20)
            rust_time = time.perf_counter() - start

            total_peaks = 0
            for spectrum in spectra_rust:
                ms_obj = SpectraConverter.to_msobject(spectrum)
                total_peaks += ms_obj.peak_count

            print(f"  Rust: {rust_time:.4f}s, {len(spectra_rust)} spectra, {total_peaks} peaks")
            if total_peaks > 0 and rust_time > 0:
                print(f"  Speed: {total_peaks/rust_time:.0f} peaks/s")

        except Exception as e:
            print(f"  MZML processing failed: {e}")
    else:
        print("  Test MZML file not found")

    print()

    # Summary
    print("BENCHMARK SUMMARY")
    print("=" * 50)

    if 'python_speed' in locals() and 'rust_speed' in locals():
        addition_speedup = rust_speed / python_speed
        print(f"Peak Addition:    {addition_speedup:.1f}x speedup")
        print(f"  Python: {python_speed:,.0f} peaks/s")
        print(f"  Rust:   {rust_speed:,.0f} peaks/s")

    if 'avg_python_sort' in locals() and 'avg_rust_sort' in locals():
        if avg_python_sort > 0 and avg_rust_sort > 0:
            sort_speedup = avg_python_sort / avg_rust_sort
            print(f"Peak Sorting:     {sort_speedup:.1f}x speedup")

    print()
    print("CONCLUSION:")
    if 'rust_speed' in locals() and rust_speed > 1000000:
        print("RUST EXCELLENT: >1M peaks/second processing speed")
    elif 'rust_speed' in locals() and rust_speed > 100000:
        print("RUST GOOD: >100k peaks/second processing speed")
    else:
        print("Processing speeds measured successfully")

if __name__ == "__main__":
    import os
    benchmark_peak_operations()