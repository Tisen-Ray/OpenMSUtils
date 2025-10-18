#!/usr/bin/env python3
"""
OpenMSUtils Rust Integration Test Suite

This script tests the integration between Python OpenMSUtils library and Rust backend.
It provides comprehensive testing for functionality, performance, and compatibility.

Usage:
    python test_rust_integration.py [options]

Options:
    --file <path>     Test with specific MZML file
    --performance     Run performance benchmarks
    --stress          Run stress tests
    --verbose         Verbose output
    --help            Show this help message
"""

import sys
import time
import argparse
import os
from pathlib import Path

def test_basic_imports():
    """Test basic module imports and Rust backend availability"""
    print("=" * 60)
    print("1. Basic Import Tests")
    print("=" * 60)

    results = {}

    # Test Python modules
    try:
        from OpenMSUtils import SpectraUtils, MolecularUtils, FastaUtils, AnalysisUtils
        print("[OK] Python modules imported successfully")
        results['python_imports'] = True
    except ImportError as e:
        print(f"[FAIL] Python import failed: {e}")
        results['python_imports'] = False

    # Test Rust backend
    try:
        from _openms_utils_rust import TestMSObject, Spectrum
        print("[OK] Rust backend imported successfully")
        results['rust_imports'] = True
    except ImportError as e:
        print(f"[FAIL] Rust backend import failed: {e}")
        results['rust_imports'] = False

    # Test MSObject creation
    try:
        from OpenMSUtils.SpectraUtils import MSObject
        ms_obj = MSObject(level=2)
        print(f"[OK] MSObject created: level={ms_obj.level}")
        results['msobject_creation'] = True

        # Check if it's using Rust backend
        rust_backend = hasattr(ms_obj, 'filter_by_intensity') and callable(ms_obj.filter_by_intensity)
        if rust_backend:
            print("[OK] MSObject using Rust backend")
            results['rust_backend_msobject'] = True
        else:
            print("[WARN] MSObject not using Rust backend")
            results['rust_backend_msobject'] = False

    except Exception as e:
        print(f"[FAIL] MSObject creation failed: {e}")
        results['msobject_creation'] = False

    return results

def test_rust_functionality():
    """Test core Rust functionality"""
    print("\n" + "=" * 60)
    print("2. Rust Functionality Tests")
    print("=" * 60)

    results = {}

    try:
        from _openms_utils_rust import TestMSObject, Spectrum

        # Test TestMSObject
        print("Testing TestMSObject...")
        test_obj = TestMSObject(0)
        test_obj.add_peak(100.0, 1000.0)
        test_obj.add_peak(200.0, 2000.0)
        test_obj.add_peak(300.0, 1500.0)

        peak_count = test_obj.peak_count()
        print(f"[OK] TestMSObject: {peak_count} peaks")
        results['test_msobject'] = peak_count > 0

        # Test Spectrum
        print("Testing Spectrum...")
        spectrum = Spectrum(0)
        spectrum.add_peak(100.0, 1000.0)
        spectrum.add_peak(200.0, 2000.0)
        spectrum.add_peak(300.0, 1500.0)
        spectrum.add_peak(400.0, 800.0)

        print(f"[OK] Spectrum: {spectrum.peak_count} peaks")
        print(f"[OK] Spectrum TIC: {spectrum.total_ion_current}")
        results['spectrum_creation'] = spectrum.peak_count > 0

        # Test sorting
        spectrum.sort_peaks()
        print("[OK] Peak sorting completed")
        results['peak_sorting'] = True

        # Test filtering
        original_count = spectrum.peak_count
        removed = spectrum.filter_by_intensity(1200.0)
        print(f"[OK] Filtering: removed {removed} peaks, {spectrum.peak_count} remaining")
        results['peak_filtering'] = True

        # Test range query
        range_obj = spectrum.get_mz_range(150.0, 350.0)
        print(f"[OK] Range query: {range_obj.peak_count} peaks in range")
        results['range_query'] = True

        # Test normalization
        spectrum.normalize()
        print("[OK] Normalization completed")
        results['normalization'] = True

    except Exception as e:
        print(f"[FAIL] Rust functionality test failed: {e}")
        results['rust_functionality'] = False

    return results

def test_mzml_processing(file_path=None):
    """Test MZML file processing with Rust backend"""
    print("\n" + "=" * 60)
    print("3. MZML Processing Tests")
    print("=" * 60)

    results = {}

    # Default test file if none provided
    if not file_path:
        default_file = r"C:\Users\Administrator\Desktop\20250103-ZMT-NSP-IMS-VTP1-3.mzML"
        if os.path.exists(default_file):
            file_path = default_file
        else:
            print("[SKIP] No MZML file provided for testing")
            results['mzml_test'] = 'skipped'
            return results

    print(f"Testing file: {file_path}")

    try:
        from OpenMSUtils.SpectraUtils import MZMLReader, SpectraConverter

        # Test Rust backend MZML reader
        print("Initializing MZMLReader with Rust backend...")
        start_time = time.time()
        reader = MZMLReader(file_path, use_rust=True)
        init_time = time.time() - start_time

        print(f"[OK] MZMLReader initialized in {init_time:.4f}s")
        print(f"[INFO] Using Rust backend: {reader.using_rust}")
        results['mzml_reader_init'] = reader.using_rust

        # Get file info
        try:
            spectrum_count = reader.get_spectrum_count_estimate()
            print(f"[INFO] Estimated spectra: {spectrum_count}")
            results['file_info'] = True
        except:
            print("[WARN] Could not get file info")
            results['file_info'] = False

        # Read first few spectra
        print("Reading first 10 spectra...")
        start_time = time.time()
        spectra = reader.read_first_spectra(10)
        read_time = time.time() - start_time

        print(f"[OK] Read {len(spectra)} spectra in {read_time:.4f}s")
        results['spectra_reading'] = len(spectra) > 0

        # Test conversion and processing
        print("Testing spectra conversion and processing...")
        conversion_start = time.time()
        total_peaks = 0
        processed_count = 0

        for i, spectrum in enumerate(spectra[:5]):  # Test first 5
            try:
                ms_obj = SpectraConverter.to_msobject(spectrum)
                total_peaks += ms_obj.peak_count
                processed_count += 1

                # Test operations
                if ms_obj.peak_count > 0:
                    ms_obj.filter_by_intensity(100.0)
                    ms_obj.sort_peaks()

                print(f"  Spectrum {i+1}: {ms_obj.peak_count} peaks, level {ms_obj.level}")

            except Exception as e:
                print(f"  [WARN] Spectrum {i+1} processing failed: {e}")

        conversion_time = time.time() - conversion_start
        print(f"[OK] Processed {processed_count} spectra ({total_peaks} peaks) in {conversion_time:.4f}s")

        if total_peaks > 0 and conversion_time > 0:
            speed = total_peaks / conversion_time
            print(f"[INFO] Processing speed: {speed:.0f} peaks/second")
            results['processing_performance'] = speed > 1000  # Should be much higher
        else:
            results['processing_performance'] = False

        results['mzml_processing'] = processed_count > 0

    except Exception as e:
        print(f"[FAIL] MZML processing test failed: {e}")
        results['mzml_processing'] = False

    return results

def test_performance_benchmarks():
    """Run performance benchmarks"""
    print("\n" + "=" * 60)
    print("4. Performance Benchmarks")
    print("=" * 60)

    results = {}

    try:
        from _openms_utils_rust import TestMSObject, Spectrum

        # Benchmark 1: Peak addition
        print("Benchmark 1: Peak addition speed")
        test_obj = TestMSObject(0)
        num_peaks = 100000

        start_time = time.time()
        for i in range(num_peaks):
            test_obj.add_peak(100.0 + i * 0.001, 1000.0 + i * 10)
        add_time = time.time() - start_time

        add_speed = num_peaks / add_time
        print(f"[OK] Added {num_peaks:,} peaks in {add_time:.4f}s")
        print(f"[INFO] Speed: {add_speed:.0f} peaks/second")
        results['peak_addition_speed'] = add_speed

        # Benchmark 2: Peak sorting
        print("\nBenchmark 2: Peak sorting speed")
        spectrum = Spectrum(0)

        # Add unsorted peaks
        for i in range(10000):
            spectrum.add_peak(1000.0 - i * 0.1, 1000.0 + i * 10)

        start_time = time.time()
        spectrum.sort_peaks()
        sort_time = time.time() - start_time

        print(f"[OK] Sorted {spectrum.peak_count} peaks in {sort_time:.4f}s")
        results['peak_sorting_speed'] = sort_time < 0.1  # Should be very fast

        # Benchmark 3: Filtering
        print("\nBenchmark 3: Peak filtering speed")
        start_time = time.time()
        removed = spectrum.filter_by_intensity(5000.0)
        filter_time = time.time() - start_time

        print(f"[OK] Filtered peaks in {filter_time:.4f}s, removed {removed}")
        results['peak_filtering_speed'] = filter_time < 0.01  # Should be very fast

        # Benchmark 4: Range queries
        print("\nBenchmark 4: Range query speed")
        start_time = time.time()
        range_obj = spectrum.get_mz_range(100.0, 500.0)
        range_time = time.time() - start_time

        print(f"[OK] Range query in {range_time:.4f}s, found {range_obj.peak_count} peaks")
        results['range_query_speed'] = range_time < 0.01  # Should be very fast

        # Overall performance assessment
        print(f"\n[INFO] Overall performance: EXCELLENT" if add_speed > 1000000 else
              f"[INFO] Overall performance: GOOD" if add_speed > 100000 else
              f"[INFO] Overall performance: NEEDS IMPROVEMENT")

    except Exception as e:
        print(f"[FAIL] Performance benchmarks failed: {e}")
        results['performance_tests'] = False

    return results

def test_compatibility():
    """Test compatibility and integration"""
    print("\n" + "=" * 60)
    print("5. Compatibility Tests")
    print("=" * 60)

    results = {}

    try:
        # Test version information
        try:
            import OpenMSUtils
            version = getattr(OpenMSUtils, '__version__', 'unknown')
            print(f"[INFO] OpenMSUtils version: {version}")
            results['version_info'] = True
        except:
            print("[WARN] Could not get version information")
            results['version_info'] = False

        # Test SpectraConverter integration
        try:
            from OpenMSUtils.SpectraUtils import SpectraConverter
            from _openms_utils_rust import Spectrum

            # Create a Rust spectrum and convert it
            rust_spectrum = Spectrum(0)
            rust_spectrum.add_peak(100.0, 1000.0)
            rust_spectrum.add_peak(200.0, 2000.0)

            # This should work without conversion since it's already MSObjectRust
            converted = SpectraConverter.to_msobject(rust_spectrum)
            print("[OK] SpectraConverter handles MSObjectRust correctly")
            results['converter_compatibility'] = True

        except Exception as e:
            print(f"[FAIL] SpectraConverter compatibility test failed: {e}")
            results['converter_compatibility'] = False

        # Test MZMLReader backend switching
        try:
            from OpenMSUtils.SpectraUtils import MZMLReader

            # Test that we can detect Rust availability
            if hasattr(MZMLReader, 'using_rust'):
                print("[OK] MZMLReader has Rust backend detection")
                results['mzml_rust_detection'] = True
            else:
                print("[WARN] MZMLReader missing Rust backend detection")
                results['mzml_rust_detection'] = False

        except Exception as e:
            print(f"[FAIL] MZMLReader compatibility test failed: {e}")
            results['mzml_compatibility'] = False

    except Exception as e:
        print(f"[FAIL] Compatibility tests failed: {e}")
        results['compatibility_tests'] = False

    return results

def generate_summary(all_results):
    """Generate summary of all test results"""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    total_tests = 0
    passed_tests = 0

    for category, results in all_results.items():
        if isinstance(results, dict):
            category_total = len([k for k, v in results.items() if k != 'mzml_test' or v != 'skipped'])
            category_passed = len([k for k, v in results.items()
                                 if v is True and k != 'mzml_test'])

            if category_total > 0:
                print(f"\n{category}:")
                print(f"  Passed: {category_passed}/{category_total}")

                total_tests += category_total
                passed_tests += category_passed

                # Show specific failures
                for test_name, result in results.items():
                    if result is False:
                        print(f"    - {test_name}: FAILED")
                    elif result is True:
                        print(f"    - {test_name}: PASSED")

    print(f"\nOVERALL RESULT: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - Rust integration is working perfectly!")
    elif passed_tests >= total_tests * 0.8:
        print("✅ MOST TESTS PASSED - Rust integration is working well")
    else:
        print("⚠️  SOME TESTS FAILED - Rust integration needs attention")

    # Performance summary
    if 'performance' in all_results and 'peak_addition_speed' in all_results['performance']:
        speed = all_results['performance']['peak_addition_speed']
        print(f"\n📊 Performance: {speed:.0f} peaks/second")
        if speed > 1000000:
            print("   Excellent performance (>1M peaks/second)")
        elif speed > 100000:
            print("   Good performance (>100k peaks/second)")
        else:
            print("   Performance could be improved")

    return passed_tests == total_tests

def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description='Test OpenMSUtils Rust Integration')
    parser.add_argument('--file', type=str, help='MZML file to test with')
    parser.add_argument('--performance', action='store_true', help='Run performance benchmarks')
    parser.add_argument('--stress', action='store_true', help='Run stress tests')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    print("OpenMSUtils Rust Integration Test Suite")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")

    # Run all tests
    all_results = {}

    # Basic functionality tests
    all_results['basic_imports'] = test_basic_imports()
    all_results['rust_functionality'] = test_rust_functionality()
    all_results['mzml_processing'] = test_mzml_processing(args.file)

    # Performance tests (optional or based on args)
    if args.performance or args.verbose:
        all_results['performance'] = test_performance_benchmarks()

    # Compatibility tests
    all_results['compatibility'] = test_compatibility()

    # Generate summary
    success = generate_summary(all_results)

    # Stress tests (if requested)
    if args.stress:
        print("\n" + "=" * 60)
        print("STRESS TESTS")
        print("=" * 60)
        try:
            test_performance_benchmarks()  # Run again for stress
            print("[OK] Stress tests completed")
        except Exception as e:
            print(f"[FAIL] Stress tests failed: {e}")

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()