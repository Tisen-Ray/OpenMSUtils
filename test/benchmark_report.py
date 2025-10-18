#!/usr/bin/env python3
"""
Comprehensive Benchmark Report: Python vs Rust Performance
"""

import time
import statistics
import sys
import os

class BenchmarkReport:
    """Generate comprehensive benchmark report"""

    def __init__(self):
        self.results = {}
        self.test_specs = {
            'small_peaks': 1000,
            'medium_peaks': 10000,
            'large_peaks': 50000
        }

    def run_all_benchmarks(self):
        """Run complete benchmark suite"""
        print("OpenMSUtils Comprehensive Performance Benchmark")
        print("=" * 55)
        print(f"Python Version: {sys.version.split()[0]}")
        print(f"Platform: {sys.platform}")
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Run different scale tests
        for test_name, num_peaks in self.test_specs.items():
            print(f"Running {test_name.replace('_', ' ').title()} ({num_peaks:,} peaks):")
            self.run_peak_benchmark(num_peaks, test_name)
            print()

        # MZML processing test
        self.run_mzml_benchmark()
        print()

        # Generate summary
        self.generate_summary()

    def run_peak_benchmark(self, num_peaks: int, test_name: str):
        """Run peak operations benchmark"""
        # Generate test data
        peaks = [(100.0 + i * 0.001, 1000.0 + i * 10) for i in range(num_peaks)]
        unsorted_peaks = [(1000.0 - i * 0.1, 1000.0 + i * 10) for i in range(num_peaks)]

        results = {'num_peaks': num_peaks}

        # Peak Addition Test
        try:
            # Test Python
            from OpenMSUtils.SpectraUtils.MSObject import MSObject as PythonMSObject
            python_times = []
            for _ in range(3):
                ms_obj = PythonMSObject(level=2)
                start = time.perf_counter()
                for mz, intensity in peaks:
                    ms_obj.add_peak(mz, intensity)
                python_times.append(time.perf_counter() - start)

            results['python_addition'] = {
                'mean': statistics.mean(python_times),
                'speed': num_peaks / statistics.mean(python_times)
            }
            print(f"  Peak Addition - Python: {results['python_addition']['speed']:.0f} peaks/s")

        except Exception as e:
            print(f"  Peak Addition - Python: Failed ({e})")
            results['python_addition'] = None

        # Test Rust
        try:
            from _openms_utils_rust import TestMSObject
            rust_times = []
            for _ in range(3):
                test_obj = TestMSObject(0)
                start = time.perf_counter()
                for mz, intensity in peaks:
                    test_obj.add_peak(mz, intensity)
                rust_times.append(time.perf_counter() - start)

            results['rust_addition'] = {
                'mean': statistics.mean(rust_times),
                'speed': num_peaks / statistics.mean(rust_times)
            }
            print(f"  Peak Addition - Rust:   {results['rust_addition']['speed']:.0f} peaks/s")

            if results['python_addition']:
                speedup = results['rust_addition']['speed'] / results['python_addition']['speed']
                results['addition_speedup'] = speedup
                print(f"  Speedup: {speedup:.1f}x")

        except Exception as e:
            print(f"  Peak Addition - Rust: Failed ({e})")
            results['rust_addition'] = None

        # Peak Sorting Test
        try:
            # Test Python
            python_sort_times = []
            for _ in range(3):
                ms_obj = PythonMSObject(level=2)
                for mz, intensity in unsorted_peaks:
                    ms_obj.add_peak(mz, intensity)
                start = time.perf_counter()
                ms_obj.sort_peaks()
                python_sort_times.append(time.perf_counter() - start)

            results['python_sort'] = {
                'mean': statistics.mean(python_sort_times),
                'speed': num_peaks / statistics.mean(python_sort_times)
            }
            print(f"  Peak Sorting - Python:  {results['python_sort']['mean']:.4f}s")

        except Exception as e:
            print(f"  Peak Sorting - Python: Failed ({e})")
            results['python_sort'] = None

        try:
            # Test Rust
            from _openms_utils_rust import Spectrum
            rust_sort_times = []
            for _ in range(3):
                spectrum = Spectrum(0)
                for mz, intensity in unsorted_peaks:
                    spectrum.add_peak(mz, intensity)
                start = time.perf_counter()
                spectrum.sort_peaks()
                rust_sort_times.append(time.perf_counter() - start)

            results['rust_sort'] = {
                'mean': statistics.mean(rust_sort_times),
                'speed': num_peaks / statistics.mean(rust_sort_times)
            }
            print(f"  Peak Sorting - Rust:    {results['rust_sort']['mean']:.4f}s")

            if results['python_sort'] and results['rust_sort']['mean'] > 0:
                speedup = results['python_sort']['mean'] / results['rust_sort']['mean']
                results['sort_speedup'] = speedup
                print(f"  Speedup: {speedup:.1f}x")

        except Exception as e:
            print(f"  Peak Sorting - Rust: Failed ({e})")
            results['rust_sort'] = None

        # Peak Filtering Test (Rust only)
        try:
            from _openms_utils_rust import Spectrum
            filter_times = []
            for _ in range(3):
                spectrum = Spectrum(0)
                for mz, intensity in peaks:
                    spectrum.add_peak(mz, intensity)
                start = time.perf_counter()
                spectrum.filter_by_intensity(5000.0)
                filter_times.append(time.perf_counter() - start)

            results['rust_filter'] = {
                'mean': statistics.mean(filter_times),
                'speed': num_peaks / statistics.mean(filter_times)
            }
            print(f"  Peak Filtering - Rust:  {results['rust_filter']['speed']:.0f} peaks/s")

        except Exception as e:
            print(f"  Peak Filtering - Rust: Failed ({e})")
            results['rust_filter'] = None

        self.results[test_name] = results

    def run_mzml_benchmark(self):
        """Run MZML processing benchmark"""
        print("MZML File Processing Benchmark:")
        print("-" * 35)

        test_file = r"C:\Users\Administrator\Desktop\20250103-ZMT-NSP-IMS-VTP1-3.mzML"

        if not os.path.exists(test_file):
            print("  Test file not found")
            return

        try:
            from OpenMSUtils.SpectraUtils import MZMLReader, SpectraConverter

            # Test Rust backend
            start = time.perf_counter()
            reader = MZMLReader(test_file, use_rust=True)
            spectra = reader.read_first_spectra(50)
            rust_time = time.perf_counter() - start

            total_peaks = 0
            for spectrum in spectra:
                ms_obj = SpectraConverter.to_msobject(spectrum)
                total_peaks += ms_obj.peak_count

            self.results['mzml'] = {
                'rust_time': rust_time,
                'spectra': len(spectra),
                'total_peaks': total_peaks,
                'peaks_per_second': total_peaks / rust_time if rust_time > 0 else 0
            }

            print(f"  File: {os.path.basename(test_file)}")
            print(f"  Spectra processed: {len(spectra)}")
            print(f"  Total peaks: {total_peaks:,}")
            print(f"  Processing time: {rust_time:.4f}s")
            print(f"  Speed: {self.results['mzml']['peaks_per_second']:.0f} peaks/s")

        except Exception as e:
            print(f"  MZML processing failed: {e}")

    def generate_summary(self):
        """Generate comprehensive summary"""
        print("COMPREHENSIVE BENCHMARK SUMMARY")
        print("=" * 55)

        # Collect all speedups
        addition_speedups = []
        sort_speedups = []

        for test_name, results in self.results.items():
            if test_name == 'mzml':
                continue

            if results.get('addition_speedup'):
                addition_speedups.append(results['addition_speedup'])
            if results.get('sort_speedup'):
                sort_speedups.append(results['sort_speedup'])

        # Peak addition summary
        if addition_speedups:
            avg_addition = statistics.mean(addition_speedups)
            min_addition = min(addition_speedups)
            max_addition = max(addition_speedups)
            print(f"Peak Addition Performance:")
            print(f"  Average speedup: {avg_addition:.1f}x")
            print(f"  Range: {min_addition:.1f}x - {max_addition:.1f}x")

        # Peak sorting summary
        if sort_speedups:
            avg_sort = statistics.mean(sort_speedups)
            min_sort = min(sort_speedups)
            max_sort = max(sort_speedups)
            print(f"Peak Sorting Performance:")
            print(f"  Average speedup: {avg_sort:.1f}x")
            print(f"  Range: {min_sort:.1f}x - {max_sort:.1f}x")

        # Overall performance assessment
        all_speedups = addition_speedups + sort_speedups
        if all_speedups:
            overall_avg = statistics.mean(all_speedups)
            print(f"\nOverall Performance:")
            print(f"  Average speedup across all operations: {overall_avg:.1f}x")

            # Performance classification
            if overall_avg > 20:
                classification = "OUTSTANDING"
                description = "Exceptional performance improvements"
            elif overall_avg > 10:
                classification = "EXCELLENT"
                description = "Significant performance improvements"
            elif overall_avg > 5:
                classification = "VERY GOOD"
                description = "Substantial performance improvements"
            elif overall_avg > 2:
                classification = "GOOD"
                description = "Noticeable performance improvements"
            else:
                classification = "MODERATE"
                description = "Some performance improvements"

            print(f"  Classification: {classification}")
            print(f"  Assessment: {description}")

        # Best performance highlights
        print(f"\nPerformance Highlights:")
        if addition_speedups:
            best_addition = max(addition_speedups)
            print(f"  Best peak addition speedup: {best_addition:.1f}x")
        if sort_speedups:
            best_sort = max(sort_speedups)
            print(f"  Best peak sorting speedup: {best_sort:.1f}x")

        if 'mzml' in self.results:
            mzml_speed = self.results['mzml']['peaks_per_second']
            print(f"  MZML processing speed: {mzml_speed:.0f} peaks/s")

        print(f"\nTest Configuration:")
        for test_name, num_peaks in self.test_specs.items():
            print(f"  {test_name}: {num_peaks:,} peaks")

        print(f"\nCONCLUSION:")
        if all_speedups:
            avg = statistics.mean(all_speedups)
            if avg > 10:
                print("The Rust backend provides EXCEPTIONAL performance improvements")
                print("Highly recommended for production use and large datasets")
            elif avg > 5:
                print("The Rust backend provides EXCELLENT performance improvements")
                print("Recommended for performance-critical applications")
            elif avg > 2:
                print("The Rust backend provides GOOD performance improvements")
                print("Beneficial for most use cases")
            else:
                print("The Rust backend provides MODERATE performance improvements")
                print("Consider based on specific requirements")
        else:
            print("Performance comparison completed")

def main():
    """Main function"""
    report = BenchmarkReport()
    report.run_all_benchmarks()

if __name__ == "__main__":
    main()