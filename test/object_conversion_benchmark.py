#!/usr/bin/env python3
"""
Object Conversion Performance Benchmark

This script tests the performance of converting between different object types:
- MSObject (Python)
- MSObjectRust (Rust)
- IMSObject (Ion Mobility)
- Various spectrum formats

Usage:
    python object_conversion_benchmark.py [options]
"""

import time
import statistics
import sys
import argparse
from typing import Dict, List, Any, Tuple

class ObjectConversionBenchmark:
    """Benchmark object conversion performance"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {}

    def log(self, message: str):
        """Log message if verbose mode is enabled"""
        if self.verbose:
            print(f"  [LOG] {message}")

    def time_operation(self, func, *args, **kwargs) -> Tuple[float, Any]:
        """Time a function execution and return time and result"""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start_time
        return elapsed, result

    def create_test_data(self, num_peaks: int = 10000) -> List[Tuple[float, float]]:
        """Create test peak data"""
        return [(100.0 + i * 0.001, 1000.0 + i * 10) for i in range(num_peaks)]

    def benchmark_msobject_creation(self, num_peaks: int = 10000, iterations: int = 5) -> Dict[str, Any]:
        """Benchmark MSObject creation and data loading"""
        print(f"\n{'='*60}")
        print(f"MSObject Creation Benchmark ({num_peaks:,} peaks)")
        print(f"{'='*60}")

        test_peaks = self.create_test_data(num_peaks)
        results = {'python': {}, 'rust': {}}

        # Test Python MSObject creation
        try:
            from OpenMSUtils.SpectraUtils.MSObject import MSObject as PythonMSObject

            print("Testing Python MSObject creation...")
            creation_times = []
            loading_times = []

            for i in range(iterations):
                self.log(f"Python iteration {i+1}/{iterations}")

                # Creation time
                elapsed, ms_obj = self.time_operation(PythonMSObject, level=2)
                creation_times.append(elapsed)

                # Data loading time
                elapsed, _ = self.time_operation(
                    lambda obj, peaks: [obj.add_peak(mz, intensity) for mz, intensity in peaks],
                    ms_obj, test_peaks
                )
                loading_times.append(elapsed)

                print(f"  Iteration {i+1}: Creation {creation_times[-1]:.4f}s, Loading {loading_times[-1]:.4f}s")

            results['python'] = {
                'creation_times': creation_times,
                'loading_times': loading_times,
                'avg_creation': statistics.mean(creation_times),
                'avg_loading': statistics.mean(loading_times),
                'total_time': statistics.mean([c + l for c, l in zip(creation_times, loading_times)])
            }

            print(f"Python Average - Creation: {results['python']['avg_creation']:.4f}s")
            print(f"Python Average - Loading: {results['python']['avg_loading']:.4f}s")
            print(f"Python Average - Total: {results['python']['total_time']:.4f}s")

        except Exception as e:
            print(f"Python MSObject test failed: {e}")

        # Test Rust MSObject creation
        try:
            from OpenMSUtils.SpectraUtils.MSObject_Rust import MSObjectRust

            print("\nTesting Rust MSObject creation...")
            rust_creation_times = []
            rust_loading_times = []

            for i in range(iterations):
                self.log(f"Rust iteration {i+1}/{iterations}")

                # Creation time
                elapsed, rust_obj = self.time_operation(MSObjectRust, level=2)
                rust_creation_times.append(elapsed)

                # Data loading time
                elapsed, _ = self.time_operation(
                    lambda obj, peaks: [obj.add_peak(mz, intensity) for mz, intensity in peaks],
                    rust_obj, test_peaks
                )
                rust_loading_times.append(elapsed)

                print(f"  Iteration {i+1}: Creation {rust_creation_times[-1]:.4f}s, Loading {rust_loading_times[-1]:.4f}s")

            results['rust'] = {
                'creation_times': rust_creation_times,
                'loading_times': rust_loading_times,
                'avg_creation': statistics.mean(rust_creation_times),
                'avg_loading': statistics.mean(rust_loading_times),
                'total_time': statistics.mean([c + l for c, l in zip(rust_creation_times, rust_loading_times)])
            }

            print(f"Rust Average - Creation: {results['rust']['avg_creation']:.4f}s")
            print(f"Rust Average - Loading: {results['rust']['avg_loading']:.4f}s")
            print(f"Rust Average - Total: {results['rust']['total_time']:.4f}s")

        except Exception as e:
            print(f"Rust MSObject test failed: {e}")

        # Calculate speedup
        if 'total_time' in results['python'] and 'total_time' in results['rust']:
            speedup = results['python']['total_time'] / results['rust']['total_time']
            print(f"\nCreation Speedup: {speedup:.1f}x (Rust is {speedup:.1f}x faster)")
            results['speedup'] = speedup

        return results

    def benchmark_spectra_conversion(self, num_peaks: int = 10000, iterations: int = 5) -> Dict[str, Any]:
        """Benchmark spectra conversion between different formats"""
        print(f"\n{'='*60}")
        print(f"Spectra Conversion Benchmark ({num_peaks:,} peaks)")
        print(f"{'='*60}")

        test_peaks = self.create_test_data(num_peaks)
        results = {}

        try:
            from OpenMSUtils.SpectraUtils.SpectraConverter import SpectraConverter
            from OpenMSUtils.SpectraUtils.MSObject import MSObject as PythonMSObject
            from OpenMSUtils.SpectraUtils.MSObject_Rust import MSObjectRust
            from _openms_utils_rust import Spectrum

            # Create source objects for conversion
            python_ms_obj = PythonMSObject(level=2)
            rust_ms_obj = MSObjectRust(level=2)
            rust_spectrum = Spectrum(0)

            for mz, intensity in test_peaks:
                python_ms_obj.add_peak(mz, intensity)
                rust_ms_obj.add_peak(mz, intensity)
                rust_spectrum.add_peak(mz, intensity)

            print("Testing conversion operations...")

            # Test 1: Python MSObject to various formats
            print("\n1. Python MSObject Conversions:")

            # Convert to MZMLSpectrum
            try:
                conversion_times = []
                for i in range(iterations):
                    elapsed, _ = self.time_operation(
                        SpectraConverter.to_mzml_spectrum, python_ms_obj
                    )
                    conversion_times.append(elapsed)

                results['python_to_mzml'] = {
                    'avg_time': statistics.mean(conversion_times),
                    'times': conversion_times
                }
                print(f"  To MZMLSpectrum: {results['python_to_mzml']['avg_time']:.4f}s")
            except Exception as e:
                print(f"  To MZMLSpectrum: Failed ({e})")

            # Convert to MGFSpectrum
            try:
                conversion_times = []
                for i in range(iterations):
                    elapsed, _ = self.time_operation(
                        SpectraConverter.to_mgf, python_ms_obj
                    )
                    conversion_times.append(elapsed)

                results['python_to_mgf'] = {
                    'avg_time': statistics.mean(conversion_times),
                    'times': conversion_times
                }
                print(f"  To MGFSpectrum: {results['python_to_mgf']['avg_time']:.4f}s")
            except Exception as e:
                print(f"  To MGFSpectrum: Failed ({e})")

            # Test 2: Rust MSObject conversions
            print("\n2. Rust MSObject Conversions:")

            # Convert to MZMLSpectrum
            try:
                conversion_times = []
                for i in range(iterations):
                    elapsed, _ = self.time_operation(
                        SpectraConverter.to_mzml_spectrum, rust_ms_obj
                    )
                    conversion_times.append(elapsed)

                results['rust_to_mzml'] = {
                    'avg_time': statistics.mean(conversion_times),
                    'times': conversion_times
                }
                print(f"  To MZMLSpectrum: {results['rust_to_mzml']['avg_time']:.4f}s")

                if 'python_to_mzml' in results:
                    speedup = results['python_to_mzml']['avg_time'] / results['rust_to_mzml']['avg_time']
                    print(f"    Speedup vs Python: {speedup:.1f}x")

            except Exception as e:
                print(f"  To MZMLSpectrum: Failed ({e})")

            # Convert to MGFSpectrum
            try:
                conversion_times = []
                for i in range(iterations):
                    elapsed, _ = self.time_operation(
                        SpectraConverter.to_mgf, rust_ms_obj
                    )
                    conversion_times.append(elapsed)

                results['rust_to_mgf'] = {
                    'avg_time': statistics.mean(conversion_times),
                    'times': conversion_times
                }
                print(f"  To MGFSpectrum: {results['rust_to_mgf']['avg_time']:.4f}s")

                if 'python_to_mgf' in results:
                    speedup = results['python_to_mgf']['avg_time'] / results['rust_to_mgf']['avg_time']
                    print(f"    Speedup vs Python: {speedup:.1f}x")

            except Exception as e:
                print(f"  To MGFSpectrum: Failed ({e})")

            # Test 3: Round-trip conversions
            print("\n3. Round-trip Conversions:")

            # Python -> MZML -> Python
            try:
                roundtrip_times = []
                for i in range(iterations):
                    mzml_spec = SpectraConverter.to_mzml_spectrum(python_ms_obj)
                    elapsed, recovered_obj = self.time_operation(
                        SpectraConverter.to_msobject, mzml_spec
                    )
                    roundtrip_times.append(elapsed)

                results['python_roundtrip'] = {
                    'avg_time': statistics.mean(roundtrip_times),
                    'times': roundtrip_times
                }
                print(f"  Python round-trip: {results['python_roundtrip']['avg_time']:.4f}s")
            except Exception as e:
                print(f"  Python round-trip: Failed ({e})")

            # Rust -> MZML -> Rust
            try:
                roundtrip_times = []
                for i in range(iterations):
                    mzml_spec = SpectraConverter.to_mzml_spectrum(rust_ms_obj)
                    elapsed, recovered_obj = self.time_operation(
                        SpectraConverter.to_msobject, mzml_spec
                    )
                    roundtrip_times.append(elapsed)

                results['rust_roundtrip'] = {
                    'avg_time': statistics.mean(roundtrip_times),
                    'times': roundtrip_times
                }
                print(f"  Rust round-trip: {results['rust_roundtrip']['avg_time']:.4f}s")

                if 'python_roundtrip' in results:
                    speedup = results['python_roundtrip']['avg_time'] / results['rust_roundtrip']['avg_time']
                    print(f"    Speedup vs Python: {speedup:.1f}x")

            except Exception as e:
                print(f"  Rust round-trip: Failed ({e})")

        except Exception as e:
            print(f"Spectra conversion benchmark failed: {e}")

        return results

    def benchmark_ims_object_conversion(self, num_peaks: int = 10000, iterations: int = 5) -> Dict[str, Any]:
        """Benchmark IMSObject (Ion Mobility) conversions"""
        print(f"\n{'='*60}")
        print(f"IMSObject Conversion Benchmark ({num_peaks:,} peaks)")
        print(f"{'='*60}")

        test_peaks = self.create_test_data(num_peaks)
        results = {}

        try:
            from OpenMSUtils.SpectraUtils.IonMobilityUtils import IMSObject
            from OpenMSUtils.SpectraUtils.SpectraConverter import SpectraConverter
            from OpenMSUtils.SpectraUtils.MSObject import MSObject as PythonMSObject
            from OpenMSUtils.SpectraUtils.MSObject_Rust import MSObjectRust

            print("Testing IMSObject conversions...")

            # Create test objects
            python_ms_obj = PythonMSObject(level=2)
            rust_ms_obj = MSObjectRust(level=2)

            for mz, intensity in test_peaks:
                python_ms_obj.add_peak(mz, intensity)
                rust_ms_obj.add_peak(mz, intensity)

            # Test 1: MSObject to IMSObject conversions
            print("\n1. MSObject to IMSObject:")

            # Python MSObject to IMSObject
            try:
                conversion_times = []
                for i in range(iterations):
                    elapsed, ims_obj = self.time_operation(
                        SpectraConverter.to_ims, python_ms_obj
                    )
                    conversion_times.append(elapsed)

                results['python_to_ims'] = {
                    'avg_time': statistics.mean(conversion_times),
                    'times': conversion_times
                }
                print(f"  Python MSObject -> IMSObject: {results['python_to_ims']['avg_time']:.4f}s")
            except Exception as e:
                print(f"  Python MSObject -> IMSObject: Failed ({e})")

            # Rust MSObject to IMSObject
            try:
                conversion_times = []
                for i in range(iterations):
                    elapsed, ims_obj = self.time_operation(
                        SpectraConverter.to_ims, rust_ms_obj
                    )
                    conversion_times.append(elapsed)

                results['rust_to_ims'] = {
                    'avg_time': statistics.mean(conversion_times),
                    'times': conversion_times
                }
                print(f"  Rust MSObject -> IMSObject: {results['rust_to_ims']['avg_time']:.4f}s")

                if 'python_to_ims' in results:
                    speedup = results['python_to_ims']['avg_time'] / results['rust_to_ims']['avg_time']
                    print(f"    Speedup vs Python: {speedup:.1f}x")

            except Exception as e:
                print(f"  Rust MSObject -> IMSObject: Failed ({e})")

            # Test 2: IMSObject to MSObject conversions
            print("\n2. IMSObject to MSObject:")

            try:
                # First create an IMSObject
                ims_obj = SpectraConverter.to_ims(python_ms_obj)

                # Convert back to Python MSObject
                conversion_times = []
                for i in range(iterations):
                    elapsed, recovered_obj = self.time_operation(
                        SpectraConverter.to_msobject, ims_obj
                    )
                    conversion_times.append(elapsed)

                results['ims_to_python'] = {
                    'avg_time': statistics.mean(conversion_times),
                    'times': conversion_times
                }
                print(f"  IMSObject -> Python MSObject: {results['ims_to_python']['avg_time']:.4f}s")

            except Exception as e:
                print(f"  IMSObject -> Python MSObject: Failed ({e})")

            # Test 3: Create IMSObject with ion mobility data
            print("\n3. IMSObject with ion mobility data:")

            try:
                creation_times = []
                for i in range(iterations):
                    elapsed, ims_obj = self.time_operation(IMSObject, level=2)
                    creation_times.append(elapsed)

                    # Add peaks with ion mobility information
                    for j, (mz, intensity) in enumerate(test_peaks[:1000]):  # Use fewer peaks for IMS test
                        im_value = 0.5 + j * 0.001  # Simulate ion mobility values
                        ims_obj.add_peak(mz, intensity, im_value)

                results['ims_creation'] = {
                    'avg_time': statistics.mean(creation_times),
                    'times': creation_times
                }
                print(f"  IMSObject creation (with IM data): {results['ims_creation']['avg_time']:.4f}s")

            except Exception as e:
                print(f"  IMSObject creation: Failed ({e})")

        except ImportError:
            print("IMSObject not available - skipping IMS conversions")
            results['error'] = "IMSObject not available"
        except Exception as e:
            print(f"IMSObject benchmark failed: {e}")

        return results

    def benchmark_batch_conversions(self, num_objects: int = 100, peaks_per_object: int = 1000) -> Dict[str, Any]:
        """Benchmark batch conversion operations"""
        print(f"\n{'='*60}")
        print(f"Batch Conversion Benchmark ({num_objects} objects, {peaks_per_object} peaks each)")
        print(f"{'='*60}")

        results = {}

        try:
            from OpenMSUtils.SpectraUtils.SpectraConverter import SpectraConverter
            from OpenMSUtils.SpectraUtils.MSObject import MSObject as PythonMSObject
            from OpenMSUtils.SpectraUtils.MSObject_Rust import MSObjectRust

            # Create batch of objects
            python_objects = []
            rust_objects = []

            print(f"Creating {num_objects} objects...")
            for i in range(num_objects):
                # Python objects
                py_obj = PythonMSObject(level=2)
                for j in range(peaks_per_object):
                    py_obj.add_peak(100.0 + j * 0.001 + i * 10, 1000.0 + j * 10 + i * 100)
                python_objects.append(py_obj)

                # Rust objects
                rust_obj = MSObjectRust(level=2)
                for j in range(peaks_per_object):
                    rust_obj.add_peak(100.0 + j * 0.001 + i * 10, 1000.0 + j * 10 + i * 100)
                rust_objects.append(rust_obj)

            # Test 1: Batch conversion Python -> MZML
            print("\n1. Python batch conversion to MZML:")
            start_time = time.perf_counter()
            mzml_objects = []
            for py_obj in python_objects:
                mzml_obj = SpectraConverter.to_mzml_spectrum(py_obj)
                mzml_objects.append(mzml_obj)
            python_batch_time = time.perf_counter() - start_time

            results['python_batch_mzml'] = {
                'total_time': python_batch_time,
                'avg_time_per_object': python_batch_time / num_objects
            }
            print(f"  Total time: {python_batch_time:.4f}s")
            print(f"  Average per object: {results['python_batch_mzml']['avg_time_per_object']:.4f}s")

            # Test 2: Batch conversion Rust -> MZML
            print("\n2. Rust batch conversion to MZML:")
            start_time = time.perf_counter()
            rust_mzml_objects = []
            for rust_obj in rust_objects:
                mzml_obj = SpectraConverter.to_mzml_spectrum(rust_obj)
                rust_mzml_objects.append(mzml_obj)
            rust_batch_time = time.perf_counter() - start_time

            results['rust_batch_mzml'] = {
                'total_time': rust_batch_time,
                'avg_time_per_object': rust_batch_time / num_objects
            }
            print(f"  Total time: {rust_batch_time:.4f}s")
            print(f"  Average per object: {results['rust_batch_mzml']['avg_time_per_object']:.4f}s")

            # Calculate batch speedup
            batch_speedup = python_batch_time / rust_batch_time
            print(f"\nBatch conversion speedup: {batch_speedup:.1f}x")
            results['batch_speedup'] = batch_speedup

            # Test 3: Batch round-trip conversions
            print("\n3. Batch round-trip conversions:")

            # Python round-trip
            start_time = time.perf_counter()
            for mzml_obj in mzml_objects[:20]:  # Test subset for round-trip
                recovered = SpectraConverter.to_msobject(mzml_obj)
            python_roundtrip_time = time.perf_counter() - start_time

            results['python_batch_roundtrip'] = {
                'total_time': python_roundtrip_time,
                'avg_time_per_object': python_roundtrip_time / 20
            }
            print(f"  Python round-trip (20 objects): {python_roundtrip_time:.4f}s")

            # Rust round-trip
            start_time = time.perf_counter()
            for mzml_obj in rust_mzml_objects[:20]:  # Test subset for round-trip
                recovered = SpectraConverter.to_msobject(mzml_obj)
            rust_roundtrip_time = time.perf_counter() - start_time

            results['rust_batch_roundtrip'] = {
                'total_time': rust_roundtrip_time,
                'avg_time_per_object': rust_roundtrip_time / 20
            }
            print(f"  Rust round-trip (20 objects): {rust_roundtrip_time:.4f}s")

            if rust_roundtrip_time > 0:
                roundtrip_speedup = python_roundtrip_time / rust_roundtrip_time
                print(f"  Round-trip speedup: {roundtrip_speedup:.1f}x")

        except Exception as e:
            print(f"Batch conversion benchmark failed: {e}")

        return results

    def run_comprehensive_benchmark(self, num_peaks: int = 10000, iterations: int = 5) -> Dict[str, Any]:
        """Run comprehensive object conversion benchmark"""
        print("OpenMSUtils Object Conversion Performance Benchmark")
        print("=" * 60)

        self.results = {
            'metadata': {
                'num_peaks': num_peaks,
                'iterations': iterations,
                'timestamp': time.time(),
                'python_version': sys.version,
                'platform': sys.platform
            }
        }

        # Run individual benchmarks
        self.results['msobject_creation'] = self.benchmark_msobject_creation(num_peaks, iterations)
        self.results['spectra_conversion'] = self.benchmark_spectra_conversion(num_peaks // 2, iterations)
        self.results['ims_conversion'] = self.benchmark_ims_object_conversion(num_peaks // 4, iterations)
        self.results['batch_conversion'] = self.benchmark_batch_conversions(50, num_peaks // 10)

        return self.results

    def generate_summary(self) -> str:
        """Generate benchmark summary"""
        if not self.results:
            return "No benchmark results available"

        summary = ["\n" + "="*60]
        summary.append("OBJECT CONVERSION BENCHMARK SUMMARY")
        summary.append("="*60)

        # MSObject Creation Summary
        if 'msobject_creation' in self.results:
            mc = self.results['msobject_creation']
            if mc.get('speedup'):
                summary.append(f"\nMSObject Creation Speedup: {mc['speedup']:.1f}x")
                if 'total_time' in mc.get('python', {}) and 'total_time' in mc.get('rust', {}):
                    summary.append(f"  Python: {mc['python']['total_time']:.4f}s")
                    summary.append(f"  Rust:   {mc['rust']['total_time']:.4f}s")

        # Spectra Conversion Summary
        if 'spectra_conversion' in self.results:
            sc = self.results['spectra_conversion']
            conversions_with_speedup = []
            for conv_name, conv_data in sc.items():
                if isinstance(conv_data, dict) and 'avg_time' in conv_data:
                    if 'python_to_mzml' in conv_name:
                        if 'rust_to_mzml' in sc:
                            speedup = sc['python_to_mzml']['avg_time'] / sc['rust_to_mzml']['avg_time']
                            conversions_with_speedup.append(f"MZML: {speedup:.1f}x")
                    elif 'python_to_mgf' in conv_name:
                        if 'rust_to_mgf' in sc:
                            speedup = sc['python_to_mgf']['avg_time'] / sc['rust_to_mgf']['avg_time']
                            conversions_with_speedup.append(f"MGF: {speedup:.1f}x")

            if conversions_with_speedup:
                summary.append(f"\nSpectra Conversion Speedups:")
                for speedup_info in conversions_with_speedup:
                    summary.append(f"  {speedup_info}")

        # Batch Conversion Summary
        if 'batch_conversion' in self.results:
            bc = self.results['batch_conversion']
            if bc.get('batch_speedup'):
                summary.append(f"\nBatch Conversion Speedup: {bc['batch_speedup']:.1f}x")

        # Overall Assessment
        speedups = []
        if 'msobject_creation' in self.results and self.results['msobject_creation'].get('speedup'):
            speedups.append(self.results['msobject_creation']['speedup'])
        if 'batch_conversion' in self.results and self.results['batch_conversion'].get('batch_speedup'):
            speedups.append(self.results['batch_conversion']['batch_speedup'])

        if speedups:
            avg_speedup = statistics.mean(speedups)
            summary.append(f"\nOverall Average Speedup: {avg_speedup:.1f}x")

            if avg_speedup > 5:
                summary.append("Conversion Performance: EXCELLENT")
            elif avg_speedup > 2:
                summary.append("Conversion Performance: VERY GOOD")
            elif avg_speedup > 1.5:
                summary.append("Conversion Performance: GOOD")
            else:
                summary.append("Conversion Performance: MODERATE")

        # Practical Recommendations
        summary.append(f"\nPractical Recommendations:")
        summary.append(f"• Use Rust MSObject for better performance in data loading")
        summary.append(f"• Batch conversions show significant improvements with Rust")
        summary.append(f"• Consider Rust backend for high-throughput applications")

        return "\n".join(summary)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Object Conversion Performance Benchmark')
    parser.add_argument('--peaks', type=int, default=10000, help='Number of peaks for single object tests')
    parser.add_argument('--iterations', type=int, default=5, help='Number of iterations for each test')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Create benchmark suite
    suite = ObjectConversionBenchmark(verbose=args.verbose)

    try:
        # Run comprehensive benchmark
        results = suite.run_comprehensive_benchmark(
            num_peaks=args.peaks,
            iterations=args.iterations
        )

        # Generate summary
        summary = suite.generate_summary()
        print(summary)

        return True

    except Exception as e:
        print(f"Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)