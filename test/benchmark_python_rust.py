#!/usr/bin/env python3
"""
OpenMSUtils Python vs Rust Performance Benchmark

This script provides comprehensive performance comparison between
pure Python implementation and Rust-accelerated version.

Usage:
    python benchmark_python_rust.py [options]

Options:
    --peaks <num>     Number of peaks to test (default: 10000)
    --iterations <n>  Number of iterations (default: 5)
    --file <path>     MZML file for real-world test
    --output <file>   Save results to file
    --plot           Generate performance plots
    --verbose        Verbose output
    --help           Show this help message
"""

import sys
import time
import statistics
import argparse
import json
from typing import Dict, List, Tuple, Any
import os

class BenchmarkSuite:
    """Comprehensive benchmark suite for Python vs Rust performance"""

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

    def benchmark_peak_addition(self, num_peaks: int = 10000, iterations: int = 5) -> Dict[str, Any]:
        """Benchmark peak addition performance"""
        print(f"\n{'='*60}")
        print(f"Peak Addition Benchmark ({num_peaks:,} peaks, {iterations} iterations)")
        print(f"{'='*60}")

        results = {'python': [], 'rust': []}

        # Test Python implementation
        try:
            from OpenMSUtils.SpectraUtils.MSObject import MSObject as PythonMSObject

            print("Testing Python implementation...")
            python_times = []

            for i in range(iterations):
                self.log(f"Python iteration {i+1}/{iterations}")
                ms_obj = PythonMSObject(level=2)

                elapsed, _ = self.time_operation(
                    lambda: [ms_obj.add_peak(100.0 + j * 0.001, 1000.0 + j * 10)
                            for j in range(num_peaks)]
                )
                python_times.append(elapsed)
                print(f"  Iteration {i+1}: {elapsed:.4f}s ({num_peaks/elapsed:.0f} peaks/s)")

            avg_python = statistics.mean(python_times)
            results['python'] = {
                'times': python_times,
                'mean': avg_python,
                'std': statistics.stdev(python_times) if len(python_times) > 1 else 0,
                'speed': num_peaks / avg_python
            }
            print(f"Python Average: {avg_python:.4f}s ({results['python']['speed']:.0f} peaks/s)")

        except Exception as e:
            print(f"Python implementation test failed: {e}")
            results['python'] = None

        # Test Rust implementation
        try:
            from _openms_utils_rust import TestMSObject

            print("\nTesting Rust implementation...")
            rust_times = []

            for i in range(iterations):
                self.log(f"Rust iteration {i+1}/{iterations}")
                test_obj = TestMSObject(0)

                elapsed, _ = self.time_operation(
                    lambda: [test_obj.add_peak(100.0 + j * 0.001, 1000.0 + j * 10)
                            for j in range(num_peaks)]
                )
                rust_times.append(elapsed)
                print(f"  Iteration {i+1}: {elapsed:.4f}s ({num_peaks/elapsed:.0f} peaks/s)")

            avg_rust = statistics.mean(rust_times)
            results['rust'] = {
                'times': rust_times,
                'mean': avg_rust,
                'std': statistics.stdev(rust_times) if len(rust_times) > 1 else 0,
                'speed': num_peaks / avg_rust
            }
            print(f"Rust Average: {avg_rust:.4f}s ({results['rust']['speed']:.0f} peaks/s)")

        except Exception as e:
            print(f"Rust implementation test failed: {e}")
            results['rust'] = None

        # Calculate speedup
        if results['python'] and results['rust']:
            speedup = results['python']['mean'] / results['rust']['mean']
            print(f"\nSpeedup: {speedup:.1f}x (Rust is {speedup:.1f}x faster)")
            results['speedup'] = speedup

        return results

    def benchmark_peak_sorting(self, num_peaks: int = 10000, iterations: int = 5) -> Dict[str, Any]:
        """Benchmark peak sorting performance"""
        print(f"\n{'='*60}")
        print(f"Peak Sorting Benchmark ({num_peaks:,} peaks, {iterations} iterations)")
        print(f"{'='*60}")

        results = {'python': [], 'rust': []}

        # Generate unsorted peaks data
        unsorted_peaks = [(1000.0 - i * 0.1, 1000.0 + i * 10) for i in range(num_peaks)]

        # Test Python implementation
        try:
            from OpenMSUtils.SpectraUtils.MSObject import MSObject as PythonMSObject

            print("Testing Python implementation...")
            python_times = []

            for i in range(iterations):
                self.log(f"Python iteration {i+1}/{iterations}")
                ms_obj = PythonMSObject(level=2)

                # Add unsorted peaks
                for mz, intensity in unsorted_peaks:
                    ms_obj.add_peak(mz, intensity)

                elapsed, _ = self.time_operation(ms_obj.sort_peaks)
                python_times.append(elapsed)
                print(f"  Iteration {i+1}: {elapsed:.4f}s")

            avg_python = statistics.mean(python_times)
            results['python'] = {
                'times': python_times,
                'mean': avg_python,
                'std': statistics.stdev(python_times) if len(python_times) > 1 else 0,
                'speed': num_peaks / avg_python
            }
            print(f"Python Average: {avg_python:.4f}s")

        except Exception as e:
            print(f"Python implementation test failed: {e}")
            results['python'] = None

        # Test Rust implementation
        try:
            from _openms_utils_rust import Spectrum

            print("\nTesting Rust implementation...")
            rust_times = []

            for i in range(iterations):
                self.log(f"Rust iteration {i+1}/{iterations}")
                spectrum = Spectrum(0)

                # Add unsorted peaks
                for mz, intensity in unsorted_peaks:
                    spectrum.add_peak(mz, intensity)

                elapsed, _ = self.time_operation(spectrum.sort_peaks)
                rust_times.append(elapsed)
                print(f"  Iteration {i+1}: {elapsed:.4f}s")

            avg_rust = statistics.mean(rust_times)
            results['rust'] = {
                'times': rust_times,
                'mean': avg_rust,
                'std': statistics.stdev(rust_times) if len(rust_times) > 1 else 0,
                'speed': num_peaks / avg_rust
            }
            print(f"Rust Average: {avg_rust:.4f}s")

        except Exception as e:
            print(f"Rust implementation test failed: {e}")
            results['rust'] = None

        # Calculate speedup
        if results['python'] and results['rust']:
            speedup = results['python']['mean'] / results['rust']['mean']
            print(f"\nSpeedup: {speedup:.1f}x (Rust is {speedup:.1f}x faster)")
            results['speedup'] = speedup

        return results

    def benchmark_peak_filtering(self, num_peaks: int = 10000, iterations: int = 5) -> Dict[str, Any]:
        """Benchmark peak filtering performance"""
        print(f"\n{'='*60}")
        print(f"Peak Filtering Benchmark ({num_peaks:,} peaks, {iterations} iterations)")
        print(f"{'='*60}")

        results = {'python': [], 'rust': []}
        results['threshold'] = 5000.0

        # Test Python implementation
        try:
            from OpenMSUtils.SpectraUtils.MSObject import MSObject as PythonMSObject

            print("Testing Python implementation...")
            python_times = []

            for i in range(iterations):
                self.log(f"Python iteration {i+1}/{iterations}")
                ms_obj = PythonMSObject(level=2)

                # Add peaks with varying intensities
                for j in range(num_peaks):
                    intensity = 100.0 + j * (10000.0 / num_peaks)
                    ms_obj.add_peak(100.0 + j * 0.001, intensity)

                elapsed, _ = self.time_operation(ms_obj.filter_by_intensity, results['threshold'])
                python_times.append(elapsed)
                print(f"  Iteration {i+1}: {elapsed:.4f}s")

            avg_python = statistics.mean(python_times)
            results['python'] = {
                'times': python_times,
                'mean': avg_python,
                'std': statistics.stdev(python_times) if len(python_times) > 1 else 0,
                'speed': num_peaks / avg_python
            }
            print(f"Python Average: {avg_python:.4f}s")

        except Exception as e:
            print(f"Python implementation test failed: {e}")
            results['python'] = None

        # Test Rust implementation
        try:
            from _openms_utils_rust import Spectrum

            print("\nTesting Rust implementation...")
            rust_times = []

            for i in range(iterations):
                self.log(f"Rust iteration {i+1}/{iterations}")
                spectrum = Spectrum(0)

                # Add peaks with varying intensities
                for j in range(num_peaks):
                    intensity = 100.0 + j * (10000.0 / num_peaks)
                    spectrum.add_peak(100.0 + j * 0.001, intensity)

                elapsed, _ = self.time_operation(spectrum.filter_by_intensity, results['threshold'])
                rust_times.append(elapsed)
                print(f"  Iteration {i+1}: {elapsed:.4f}s")

            avg_rust = statistics.mean(rust_times)
            results['rust'] = {
                'times': rust_times,
                'mean': avg_rust,
                'std': statistics.stdev(rust_times) if len(rust_times) > 1 else 0,
                'speed': num_peaks / avg_rust
            }
            print(f"Rust Average: {avg_rust:.4f}s")

        except Exception as e:
            print(f"Rust implementation test failed: {e}")
            results['rust'] = None

        # Calculate speedup
        if results['python'] and results['rust']:
            speedup = results['python']['mean'] / results['rust']['mean']
            print(f"\nSpeedup: {speedup:.1f}x (Rust is {speedup:.1f}x faster)")
            results['speedup'] = speedup

        return results

    def benchmark_mzml_processing(self, file_path: str, num_spectra: int = 100) -> Dict[str, Any]:
        """Benchmark MZML file processing performance"""
        print(f"\n{'='*60}")
        print(f"MZML Processing Benchmark ({num_spectra} spectra)")
        print(f"{'='*60}")
        print(f"File: {os.path.basename(file_path)}")

        results = {'python': None, 'rust': None}

        # Test Python backend
        try:
            from OpenMSUtils.SpectraUtils import MZMLReader, SpectraConverter

            print("Testing Python MZML processing...")
            elapsed, reader = self.time_operation(MZMLReader, file_path, use_rust=False)
            print(f"  Reader initialization: {elapsed:.4f}s")

            # Read spectra
            start_time = time.perf_counter()
            spectra = reader.read_first_spectra(num_spectra)
            read_time = time.perf_counter() - start_time
            print(f"  Read {len(spectra)} spectra: {read_time:.4f}s")

            # Process spectra
            start_time = time.perf_counter()
            total_peaks = 0
            for spectrum in spectra:
                ms_obj = SpectraConverter.to_msobject(spectrum)
                total_peaks += ms_obj.peak_count
                # Basic operations
                if ms_obj.peak_count > 0:
                    ms_obj.filter_by_intensity(100.0)
                    ms_obj.sort_peaks()

            process_time = time.perf_counter() - start_time
            total_time = elapsed + read_time + process_time

            results['python'] = {
                'init_time': elapsed,
                'read_time': read_time,
                'process_time': process_time,
                'total_time': total_time,
                'spectra_processed': len(spectra),
                'total_peaks': total_peaks,
                'spectra_per_second': len(spectra) / total_time,
                'peaks_per_second': total_peaks / process_time if process_time > 0 else 0
            }

            print(f"  Process {total_peaks} peaks: {process_time:.4f}s")
            print(f"  Total time: {total_time:.4f}s")
            print(f"  Speed: {results['python']['peaks_per_second']:.0f} peaks/s")

        except Exception as e:
            print(f"Python MZML processing failed: {e}")

        # Test Rust backend
        try:
            from OpenMSUtils.SpectraUtils import MZMLReader, SpectraConverter

            print("\nTesting Rust MZML processing...")
            elapsed, reader = self.time_operation(MZMLReader, file_path, use_rust=True)
            print(f"  Reader initialization: {elapsed:.4f}s")

            # Read spectra
            start_time = time.perf_counter()
            spectra = reader.read_first_spectra(num_spectra)
            read_time = time.perf_counter() - start_time
            print(f"  Read {len(spectra)} spectra: {read_time:.4f}s")

            # Process spectra
            start_time = time.perf_counter()
            total_peaks = 0
            for spectrum in spectra:
                ms_obj = SpectraConverter.to_msobject(spectrum)
                total_peaks += ms_obj.peak_count
                # Basic operations
                if ms_obj.peak_count > 0:
                    ms_obj.filter_by_intensity(100.0)
                    ms_obj.sort_peaks()

            process_time = time.perf_counter() - start_time
            total_time = elapsed + read_time + process_time

            results['rust'] = {
                'init_time': elapsed,
                'read_time': read_time,
                'process_time': process_time,
                'total_time': total_time,
                'spectra_processed': len(spectra),
                'total_peaks': total_peaks,
                'spectra_per_second': len(spectra) / total_time,
                'peaks_per_second': total_peaks / process_time if process_time > 0 else 0
            }

            print(f"  Process {total_peaks} peaks: {process_time:.4f}s")
            print(f"  Total time: {total_time:.4f}s")
            print(f"  Speed: {results['rust']['peaks_per_second']:.0f} peaks/s")

        except Exception as e:
            print(f"Rust MZML processing failed: {e}")

        # Calculate speedup
        if results['python'] and results['rust']:
            speedup = results['python']['total_time'] / results['rust']['total_time']
            print(f"\nSpeedup: {speedup:.1f}x (Rust is {speedup:.1f}x faster)")
            results['speedup'] = speedup

        return results

    def benchmark_memory_usage(self, num_peaks: int = 50000) -> Dict[str, Any]:
        """Benchmark memory usage (simplified)"""
        print(f"\n{'='*60}")
        print(f"Memory Usage Benchmark ({num_peaks:,} peaks)")
        print(f"{'='*60}")

        results = {}

        try:
            import psutil
            import gc

            # Test Python implementation
            print("Testing Python memory usage...")
            gc.collect()
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB

            from OpenMSUtils.SpectraUtils.MSObject import MSObject as PythonMSObject
            ms_obj = PythonMSObject(level=2)

            for i in range(num_peaks):
                ms_obj.add_peak(100.0 + i * 0.001, 1000.0 + i * 10)

            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            python_memory = memory_after - memory_before

            print(f"Python memory usage: {python_memory:.1f} MB")
            print(f"Memory per peak: {python_memory * 1024 / num_peaks:.2f} KB")

            results['python'] = {
                'total_memory_mb': python_memory,
                'memory_per_peak_kb': python_memory * 1024 / num_peaks
            }

            # Clean up
            del ms_obj
            gc.collect()

            # Test Rust implementation
            print("\nTesting Rust memory usage...")
            memory_before = process.memory_info().rss / 1024 / 1024

            from _openms_utils_rust import TestMSObject
            test_obj = TestMSObject(0)

            for i in range(num_peaks):
                test_obj.add_peak(100.0 + i * 0.001, 1000.0 + i * 10)

            memory_after = process.memory_info().rss / 1024 / 1024
            rust_memory = memory_after - memory_before

            print(f"Rust memory usage: {rust_memory:.1f} MB")
            print(f"Memory per peak: {rust_memory * 1024 / num_peaks:.2f} KB")

            results['rust'] = {
                'total_memory_mb': rust_memory,
                'memory_per_peak_kb': rust_memory * 1024 / num_peaks
            }

            # Calculate memory efficiency
            if results['python'] and results['rust']:
                efficiency = results['python']['memory_per_peak_kb'] / results['rust']['memory_per_peak_kb']
                print(f"\nMemory efficiency: {efficiency:.1f}x (Rust uses {efficiency:.1f}x less memory per peak)")
                results['memory_efficiency'] = efficiency

        except ImportError:
            print("psutil not available, skipping memory benchmark")
            results['error'] = "psutil not available"
        except Exception as e:
            print(f"Memory benchmark failed: {e}")
            results['error'] = str(e)

        return results

    def run_comprehensive_benchmark(self, num_peaks: int = 10000, iterations: int = 5,
                                 file_path: str = None) -> Dict[str, Any]:
        """Run comprehensive benchmark suite"""
        print("OpenMSUtils Python vs Rust Performance Benchmark")
        print("=" * 60)

        self.results = {
            'metadata': {
                'num_peaks': num_peaks,
                'iterations': iterations,
                'file_path': file_path,
                'timestamp': time.time(),
                'python_version': sys.version,
                'platform': sys.platform
            }
        }

        # Run individual benchmarks
        self.results['peak_addition'] = self.benchmark_peak_addition(num_peaks, iterations)
        self.results['peak_sorting'] = self.benchmark_peak_sorting(num_peaks, iterations)
        self.results['peak_filtering'] = self.benchmark_peak_filtering(num_peaks, iterations)

        if file_path and os.path.exists(file_path):
            self.results['mzml_processing'] = self.benchmark_mzml_processing(file_path, 100)

        self.results['memory_usage'] = self.benchmark_memory_usage(num_peaks * 5)

        return self.results

    def generate_summary(self) -> str:
        """Generate benchmark summary"""
        if not self.results:
            return "No benchmark results available"

        summary = ["\n" + "="*60]
        summary.append("BENCHMARK SUMMARY")
        summary.append("="*60)

        # Peak addition summary
        if 'peak_addition' in self.results:
            pa = self.results['peak_addition']
            if pa.get('speedup'):
                summary.append(f"\nPeak Addition Speedup: {pa['speedup']:.1f}x")
                if pa['python'] and pa['rust']:
                    summary.append(f"  Python: {pa['python']['speed']:.0f} peaks/s")
                    summary.append(f"  Rust:   {pa['rust']['speed']:.0f} peaks/s")

        # Peak sorting summary
        if 'peak_sorting' in self.results:
            ps = self.results['peak_sorting']
            if ps.get('speedup'):
                summary.append(f"\nPeak Sorting Speedup: {ps['speedup']:.1f}x")

        # Peak filtering summary
        if 'peak_filtering' in self.results:
            pf = self.results['peak_filtering']
            if pf.get('speedup'):
                summary.append(f"\nPeak Filtering Speedup: {pf['speedup']:.1f}x")

        # MZML processing summary
        if 'mzml_processing' in self.results:
            mp = self.results['mzml_processing']
            if mp.get('speedup'):
                summary.append(f"\nMZML Processing Speedup: {mp['speedup']:.1f}x")
                if mp['python'] and mp['rust']:
                    summary.append(f"  Python: {mp['python']['peaks_per_second']:.0f} peaks/s")
                    summary.append(f"  Rust:   {mp['rust']['peaks_per_second']:.0f} peaks/s")

        # Memory usage summary
        if 'memory_usage' in self.results:
            mu = self.results['memory_usage']
            if mu.get('memory_efficiency'):
                summary.append(f"\nMemory Efficiency: {mu['memory_efficiency']:.1f}x")
                if mu['python'] and mu['rust']:
                    summary.append(f"  Python: {mu['python']['memory_per_peak_kb']:.2f} KB/peak")
                    summary.append(f"  Rust:   {mu['rust']['memory_per_peak_kb']:.2f} KB/peak")

        # Overall assessment
        speedups = [self.results[k].get('speedup', 0) for k in self.results
                   if isinstance(self.results[k], dict) and 'speedup' in self.results[k]]
        if speedups:
            avg_speedup = statistics.mean(speedups)
            summary.append(f"\nOverall Average Speedup: {avg_speedup:.1f}x")

            if avg_speedup > 10:
                summary.append("Performance Classification: EXCELLENT")
            elif avg_speedup > 5:
                summary.append("Performance Classification: VERY GOOD")
            elif avg_speedup > 2:
                summary.append("Performance Classification: GOOD")
            else:
                summary.append("Performance Classification: MODERATE")

        return "\n".join(summary)

    def save_results(self, filename: str):
        """Save benchmark results to JSON file"""
        if not self.results:
            print("No results to save")
            return

        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            print(f"\nResults saved to: {filename}")
        except Exception as e:
            print(f"Failed to save results: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='OpenMSUtils Python vs Rust Benchmark')
    parser.add_argument('--peaks', type=int, default=10000, help='Number of peaks to test')
    parser.add_argument('--iterations', type=int, default=5, help='Number of iterations')
    parser.add_argument('--file', type=str, help='MZML file for testing')
    parser.add_argument('--output', type=str, help='Save results to file')
    parser.add_argument('--plot', action='store_true', help='Generate performance plots')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Set default file if not provided
    if not args.file:
        default_file = r"C:\Users\Administrator\Desktop\20250103-ZMT-NSP-IMS-VTP1-3.mzML"
        if os.path.exists(default_file):
            args.file = default_file
            print(f"Using default MZML file: {os.path.basename(default_file)}")

    # Create benchmark suite
    suite = BenchmarkSuite(verbose=args.verbose)

    try:
        # Run comprehensive benchmark
        results = suite.run_comprehensive_benchmark(
            num_peaks=args.peaks,
            iterations=args.iterations,
            file_path=args.file
        )

        # Generate summary
        summary = suite.generate_summary()
        print(summary)

        # Save results if requested
        if args.output:
            suite.save_results(args.output)

        # Generate plots if requested
        if args.plot:
            try:
                generate_plots(results)
            except Exception as e:
                print(f"Failed to generate plots: {e}")

        return True

    except Exception as e:
        print(f"Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_plots(results: Dict[str, Any]):
    """Generate performance plots (requires matplotlib)"""
    try:
        import matplotlib.pyplot as plt
        import numpy as np

        # Create subplot layout
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('OpenMSUtils Python vs Rust Performance Benchmark', fontsize=16)

        # Speedup comparisons
        benchmarks = []
        speedups = []

        for benchmark_name, benchmark_data in results.items():
            if isinstance(benchmark_data, dict) and 'speedup' in benchmark_data:
                benchmarks.append(benchmark_name.replace('_', ' ').title())
                speedups.append(benchmark_data['speedup'])

        if benchmarks:
            # Bar chart of speedups
            axes[0, 0].bar(benchmarks, speedups, color=['skyblue', 'lightgreen', 'salmon', 'orange'])
            axes[0, 0].set_title('Performance Speedup (Rust vs Python)')
            axes[0, 0].set_ylabel('Speedup (x)')
            axes[0, 0].tick_params(axis='x', rotation=45)

            # Add value labels on bars
            for i, v in enumerate(speedups):
                axes[0, 0].text(i, v + 0.1, f'{v:.1f}x', ha='center')

        # Peak addition performance
        if 'peak_addition' in results and results['peak_addition']:
            pa = results['peak_addition']
            if pa['python'] and pa['rust']:
                implementations = ['Python', 'Rust']
                speeds = [pa['python']['speed'], pa['rust']['speed']]

                axes[0, 1].bar(implementations, speeds, color=['red', 'blue'])
                axes[0, 1].set_title('Peak Addition Performance')
                axes[0, 1].set_ylabel('Speed (peaks/second)')
                axes[0, 1].set_yscale('log')

        # Processing time comparison
        if 'mzml_processing' in results and results['mzml_processing']:
            mp = results['mzml_processing']
            if mp['python'] and mp['rust']:
                implementations = ['Python', 'Rust']
                times = [mp['python']['total_time'], mp['rust']['total_time']]

                axes[1, 0].bar(implementations, times, color=['red', 'blue'])
                axes[1, 0].set_title('MZML Processing Time')
                axes[1, 0].set_ylabel('Time (seconds)')

        # Memory usage comparison
        if 'memory_usage' in results and results['memory_usage']:
            mu = results['memory_usage']
            if mu['python'] and mu['rust']:
                implementations = ['Python', 'Rust']
                memory = [mu['python']['memory_per_peak_kb'], mu['rust']['memory_per_peak_kb']]

                axes[1, 1].bar(implementations, memory, color=['red', 'blue'])
                axes[1, 1].set_title('Memory Usage per Peak')
                axes[1, 1].set_ylabel('Memory (KB/peak)')

        plt.tight_layout()
        plt.savefig('benchmark_results.png', dpi=300, bbox_inches='tight')
        print("\nPerformance plots saved to: benchmark_results.png")

    except ImportError:
        print("matplotlib not available, skipping plot generation")
    except Exception as e:
        print(f"Failed to generate plots: {e}")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)