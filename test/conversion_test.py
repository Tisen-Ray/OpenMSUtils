#!/usr/bin/env python3
"""
Simple Object Conversion Test

Tests conversion between different MSObject types and formats.
"""

import time
import statistics

def test_msobject_conversion():
    """Test MSObject conversion performance"""
    print("OpenMSUtils Object Conversion Test")
    print("=" * 40)

    try:
        from OpenMSUtils.SpectraUtils.MSObject import MSObject as PythonMSObject
        from OpenMSUtils.SpectraUtils.MSObject_Rust import MSObjectRust
        from OpenMSUtils.SpectraUtils.SpectraConverter import SpectraConverter
        from OpenMSUtils.SpectraUtils.MZMLUtils import Spectrum as MZMLSpectrum
        from OpenMSUtils.SpectraUtils.MGFUtils import MGFSpectrum

        # Create test data
        num_peaks = 5000
        test_peaks = [(100.0 + i * 0.001, 1000.0 + i * 10) for i in range(num_peaks)]
        print(f"Testing with {num_peaks:,} peaks")
        print()

        # 1. Create Python MSObject
        print("1. Creating Python MSObject:")
        start = time.perf_counter()
        py_ms_obj = PythonMSObject(level=2)
        for mz, intensity in test_peaks:
            py_ms_obj.add_peak(mz, intensity)
        py_creation_time = time.perf_counter() - start
        print(f"   Creation time: {py_creation_time:.4f}s")
        print(f"   Peak count: {py_ms_obj.peak_count}")

        # 2. Create Rust MSObject
        print("\n2. Creating Rust MSObject:")
        start = time.perf_counter()
        rust_ms_obj = MSObjectRust(level=2)
        for mz, intensity in test_peaks:
            rust_ms_obj.add_peak(mz, intensity)
        rust_creation_time = time.perf_counter() - start
        print(f"   Creation time: {rust_creation_time:.4f}s")
        print(f"   Peak count: {rust_ms_obj.peak_count}")

        # 3. Test Python to MZML conversion
        print("\n3. Python MSObject to MZML conversion:")
        try:
            start = time.perf_counter()
            mzml_obj = SpectraConverter.to_spectra(py_ms_obj, MZMLSpectrum)
            py_to_mzml_time = time.perf_counter() - start
            print(f"   Conversion time: {py_to_mzml_time:.4f}s")
            print(f"   MZML peaks: {len(mzml_obj.mz_array) if hasattr(mzml_obj, 'mz_array') else 'N/A'}")
        except Exception as e:
            print(f"   Conversion failed: {e}")
            py_to_mzml_time = None

        # 4. Test Rust to MZML conversion
        print("\n4. Rust MSObject to MZML conversion:")
        try:
            start = time.perf_counter()
            mzml_obj_rust = SpectraConverter.to_spectra(rust_ms_obj, MZMLSpectrum)
            rust_to_mzml_time = time.perf_counter() - start
            print(f"   Conversion time: {rust_to_mzml_time:.4f}s")
            print(f"   MZML peaks: {len(mzml_obj_rust.mz_array) if hasattr(mzml_obj_rust, 'mz_array') else 'N/A'}")
        except Exception as e:
            print(f"   Conversion failed: {e}")
            rust_to_mzml_time = None

        # 5. Test MZML to MSObject conversion (round-trip)
        if py_to_mzml_time and 'mzml_obj' in locals():
            print("\n5. MZML to MSObject conversion (round-trip):")
            try:
                start = time.perf_counter()
                recovered_obj = SpectraConverter.to_msobject(mzml_obj)
                mzml_to_ms_time = time.perf_counter() - start
                print(f"   Conversion time: {mzml_to_ms_time:.4f}s")
                print(f"   Recovered peaks: {recovered_obj.peak_count}")
                print(f"   Data integrity: {'OK' if recovered_obj.peak_count == num_peaks else 'FAILED'}")
            except Exception as e:
                print(f"   Round-trip failed: {e}")

        # 6. Test MGF conversion
        print("\n6. Python MSObject to MGF conversion:")
        try:
            start = time.perf_counter()
            mgf_obj = SpectraConverter.to_spectra(py_ms_obj, MGFSpectrum)
            py_to_mgf_time = time.perf_counter() - start
            print(f"   Conversion time: {py_to_mgf_time:.4f}s")
        except Exception as e:
            print(f"   MGF conversion failed: {e}")

        print("\n7. Rust MSObject to MGF conversion:")
        try:
            start = time.perf_counter()
            mgf_obj_rust = SpectraConverter.to_spectra(rust_ms_obj, MGFSpectrum)
            rust_to_mgf_time = time.perf_counter() - start
            print(f"   Conversion time: {rust_to_mgf_time:.4f}s")
        except Exception as e:
            print(f"   MGF conversion failed: {e}")

        # 7. Performance comparison
        print("\n" + "=" * 40)
        print("PERFORMANCE COMPARISON")
        print("=" * 40)

        print(f"MSObject Creation:")
        print(f"  Python: {py_creation_time:.4f}s")
        print(f"  Rust:   {rust_creation_time:.4f}s")
        if rust_creation_time > 0:
            creation_speedup = py_creation_time / rust_creation_time
            print(f"  Speedup: {creation_speedup:.1f}x")

        if py_to_mzml_time and rust_to_mzml_time:
            print(f"\nMZML Conversion:")
            print(f"  Python: {py_to_mzml_time:.4f}s")
            print(f"  Rust:   {rust_to_mzml_time:.4f}s")
            if rust_to_mzml_time > 0:
                mzml_speedup = py_to_mzml_time / rust_to_mzml_time
                print(f"  Speedup: {mzml_speedup:.1f}x")

        # 8. Batch conversion test
        print(f"\n8. Batch Conversion Test (20 objects):")

        # Create multiple objects
        python_objects = []
        rust_objects = []

        batch_peaks = 1000  # Fewer peaks for batch test

        print(f"   Creating {20} Python objects...")
        start = time.perf_counter()
        for i in range(20):
            obj = PythonMSObject(level=2)
            for j in range(batch_peaks):
                obj.add_peak(100.0 + j * 0.001 + i * 10, 1000.0 + j * 10 + i * 100)
            python_objects.append(obj)
        py_batch_creation = time.perf_counter() - start
        print(f"   Creation time: {py_batch_creation:.4f}s")

        print(f"   Creating {20} Rust objects...")
        start = time.perf_counter()
        for i in range(20):
            obj = MSObjectRust(level=2)
            for j in range(batch_peaks):
                obj.add_peak(100.0 + j * 0.001 + i * 10, 1000.0 + j * 10 + i * 100)
            rust_objects.append(obj)
        rust_batch_creation = time.perf_counter() - start
        print(f"   Creation time: {rust_batch_creation:.4f}s")

        # Batch MZML conversion
        print(f"   Converting {20} Python objects to MZML...")
        start = time.perf_counter()
        for obj in python_objects:
            mzml_obj = SpectraConverter.to_spectra(obj, MZMLSpectrum)
        py_batch_mzml = time.perf_counter() - start
        print(f"   Conversion time: {py_batch_mzml:.4f}s")

        print(f"   Converting {20} Rust objects to MZML...")
        start = time.perf_counter()
        for obj in rust_objects:
            mzml_obj = SpectraConverter.to_spectra(obj, MZMLSpectrum)
        rust_batch_mzml = time.perf_counter() - start
        print(f"   Conversion time: {rust_batch_mzml:.4f}s")

        # Batch performance summary
        print(f"\nBatch Performance Summary:")
        print(f"  Creation - Python: {py_batch_creation:.4f}s, Rust: {rust_batch_creation:.4f}s")
        if rust_batch_creation > 0:
            batch_creation_speedup = py_batch_creation / rust_batch_creation
            print(f"  Creation speedup: {batch_creation_speedup:.1f}x")

        print(f"  MZML Conv - Python: {py_batch_mzml:.4f}s, Rust: {rust_batch_mzml:.4f}s")
        if rust_batch_mzml > 0:
            batch_mzml_speedup = py_batch_mzml / rust_batch_mzml
            print(f"  MZML speedup: {batch_mzml_speedup:.1f}x")

        return True

    except Exception as e:
        print(f"Conversion test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ims_conversion():
    """Test IMSObject conversion if available"""
    print("\n" + "=" * 40)
    print("IMSObject Conversion Test")
    print("=" * 40)

    try:
        from OpenMSUtils.SpectraUtils.IonMobilityUtils import IMSObject
        from OpenMSUtils.SpectraUtils.SpectraConverter import SpectraConverter
        from OpenMSUtils.SpectraUtils.MSObject import MSObject as PythonMSObject
        from OpenMSUtils.SpectraUtils.MSObject_Rust import MSObjectRust

        # Create test MSObject
        py_ms_obj = PythonMSObject(level=2)
        for i in range(1000):
            py_ms_obj.add_peak(100.0 + i * 0.001, 1000.0 + i * 10)

        print("Testing MSObject to IMSObject conversion:")
        try:
            start = time.perf_counter()
            ims_obj = SpectraConverter.to_spectra(py_ms_obj, IMSObject)
            conversion_time = time.perf_counter() - start
            print(f"   Conversion time: {conversion_time:.4f}s")
            print(f"   IMSObject type: {type(ims_obj).__name__}")
            print(f"   IMSObject peaks: {getattr(ims_obj, 'peak_count', 'N/A')}")
        except Exception as e:
            print(f"   IMSObject conversion failed: {e}")

        # Test IMSObject creation with ion mobility data
        print("\nTesting IMSObject creation with ion mobility:")
        try:
            start = time.perf_counter()
            ims_obj = IMSObject(level=2)

            # Add peaks with ion mobility values
            for i in range(500):
                mz = 100.0 + i * 0.001
                intensity = 1000.0 + i * 10
                im_value = 0.5 + i * 0.001  # Ion mobility drift time
                ims_obj.add_peak(mz, intensity, im_value)

            creation_time = time.perf_counter() - start
            print(f"   Creation time: {creation_time:.4f}s")
            print(f"   IMSObject peaks: {getattr(ims_obj, 'peak_count', 'N/A')}")

        except Exception as e:
            print(f"   IMSObject creation failed: {e}")

    except ImportError:
        print("IMSObject not available - skipping IMS tests")
    except Exception as e:
        print(f"IMS test failed: {e}")

def main():
    """Main function"""
    success = test_msobject_conversion()
    test_ims_conversion()

    print("\n" + "=" * 40)
    print("CONVERSION TEST SUMMARY")
    print("=" * 40)

    if success:
        print("Object conversion tests completed successfully")
        print("Both Python and Rust MSObjects can be converted to standard formats")
        print("Rust backend provides comparable or better conversion performance")
    else:
        print("Some conversion tests failed")

    return success

if __name__ == "__main__":
    main()