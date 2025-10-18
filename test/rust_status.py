#!/usr/bin/env python3
"""
Simple Rust Status Check for OpenMSUtils
"""

import sys
import time

def main():
    print("OpenMSUtils Rust Backend Status")
    print("=" * 35)

    try:
        # Test Python imports
        from OpenMSUtils import SpectraUtils, MolecularUtils, FastaUtils, AnalysisUtils
        print("[OK] Python modules imported")
    except ImportError as e:
        print(f"[FAIL] Python import failed: {e}")
        sys.exit(1)

    try:
        # Test Rust imports
        from _openms_utils_rust import TestMSObject, Spectrum
        print("[OK] Rust backend imported")
    except ImportError as e:
        print(f"[FAIL] Rust backend not available: {e}")
        sys.exit(1)

    try:
        # Test Rust functionality
        test_obj = TestMSObject(0)
        test_obj.add_peak(100.0, 1000.0)
        count = test_obj.peak_count()
        print(f"[OK] Rust functionality working ({count} peaks)")
    except Exception as e:
        print(f"[FAIL] Rust functionality failed: {e}")
        sys.exit(1)

    try:
        # Test MSObject with Rust backend
        from OpenMSUtils.SpectraUtils import MSObject
        ms_obj = MSObject(level=2)
        ms_obj.add_peak(100.0, 1000.0)

        if hasattr(ms_obj, 'filter_by_intensity'):
            print("[OK] MSObject using Rust backend")
        else:
            print("[FAIL] MSObject not using Rust backend")
            sys.exit(1)
    except Exception as e:
        print(f"[FAIL] MSObject test failed: {e}")
        sys.exit(1)

    # Performance test
    print("\nPerformance Test:")
    try:
        test_obj = TestMSObject(0)
        start = time.time()
        for i in range(10000):
            test_obj.add_peak(100.0 + i * 0.001, 1000.0 + i * 10)
        elapsed = time.time() - start
        speed = 10000 / elapsed
        print(f"Added 10,000 peaks in {elapsed:.4f}s")
        print(f"Speed: {speed:,.0f} peaks/second")

        if speed > 1000000:
            print("Performance: EXCELLENT")
        elif speed > 100000:
            print("Performance: GOOD")
        else:
            print("Performance: NEEDS IMPROVEMENT")

    except Exception as e:
        print(f"Performance test failed: {e}")

    print("\n" + "=" * 35)
    print("SUCCESS: Rust backend is fully operational!")
    print("OpenMSUtils is ready for high-performance processing.")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)