# OpenMSUtils Installation Guide

## Overview

OpenMSUtils is a high-performance mass spectrometry data processing library that combines Python ease-of-use with Rust performance. This guide covers installation and basic usage.

## Requirements

- Python 3.8 or higher
- Rust toolchain (for building from source)
- Operating system: Windows, macOS, or Linux

## Installation Methods

### Method 1: Install from PyPI (Recommended)

```bash
pip install OpenMSUtils
```

This will install the pre-compiled package with Rust backend for optimal performance.
The precompiled wheel includes optimized Rust binaries for your platform.

### Method 2: Install from GitHub Releases

For specific versions or platforms:

```bash
# Windows x64 (Python 3.13)
pip install https://github.com/OpenMSUtils/OpenMSUtils/releases/download/v2.0.0/OpenMSUtils-2.0.0-cp313-cp313-win_amd64.whl

# Or download from releases page and install locally
pip install OpenMSUtils-2.0.0-cp313-cp313-win_amd64.whl
```

### Method 3: Install from Source

If you need to build from source (e.g., for development or custom builds):

```bash
# Clone the repository
git clone https://github.com/OpenMSUtils/OpenMSUtils.git
cd OpenMSUtils

# Install Rust toolchain (required)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env  # Windows: restart terminal

# Install the package with Rust compilation
pip install .
```

### Method 4: Development Installation

For developers who want to modify the code:

```bash
git clone https://github.com/OpenMSUtils/OpenMSUtils.git
cd OpenMSUtils

# Install in development mode (requires Rust)
pip install -e .
```

## Verification

After installation, verify the installation:

```python
# Test the installation
python -c "
import OpenMSUtils
from OpenMSUtils.SpectraUtils import MSObject, MZMLReader

print('OpenMSUtils version:', OpenMSUtils.__version__)

# Test basic functionality
ms_obj = MSObject(level=2)
ms_obj.add_peak(100.0, 1000.0)
print('MSObject created:', ms_obj)
print('Peak count:', ms_obj.peak_count)
print('TIC:', ms_obj.total_ion_current)

# Test Rust backend
try:
    from _openms_utils_rust import TestMSObject, Spectrum
    print('✅ Rust backend loaded successfully')

    test_obj = TestMSObject(0)
    test_obj.add_peak(100.0, 1000.0)
    print(f'✅ Rust TestMSObject working: {test_obj.peak_count()} peaks')

except ImportError as e:
    print(f'❌ Rust backend not available: {e}')
"
```

Or run the included test script:

```bash
python test_install.py
```

## Expected Output

When successfully installed with the precompiled version, you should see:
- "Using high-performance Rust-backed MSObject"
- "✅ Rust backend loaded successfully"
- "✅ Rust TestMSObject working: X peaks"
- Peak processing speeds of millions of peaks per second
- All imports working correctly

## Performance Benchmarks

The precompiled Rust backend provides significant performance improvements:

```python
import time
from _openms_utils_rust import TestMSObject

# Performance test
test_obj = TestMSObject(0)
start_time = time.time()

for i in range(100000):
    test_obj.add_peak(100.0 + i * 0.001, 1000.0 + i * 10)

add_time = time.time() - start_time
print(f"Added 100,000 peaks in {add_time:.4f}s")
print(f"Speed: {100000/add_time:.0f} peaks/second")

# Expected: > 1,000,000 peaks/second
```

## Performance Verification

The library should provide significantly better performance than pure Python:

```python
import time
from OpenMSUtils.SpectraUtils import MSObject

# Create a test with many peaks
ms_obj = MSObject(level=2)
start_time = time.time()

for i in range(10000):
    ms_obj.add_peak(100.0 + i * 0.001, 1000.0 + i * 10)

add_time = time.time() - start_time
print(f"Added 10000 peaks in {add_time:.4f}s ({10000/add_time:.0f} peaks/s)")

# You should see speeds of millions of peaks per second
```

## Troubleshooting

### Common Issues

1. **ImportError: No module named '_openms_utils_rust'**
   - This usually means the Rust extension wasn't built correctly
   - Try installing from source instead of PyPI

2. **Rust toolchain not found**
   - Install Rust from https://rustup.rs/
   - Follow the installation instructions

3. **Compilation errors on Windows**
   - Make sure you have Microsoft Visual Studio Build Tools installed
   - Use the Windows Subsystem for Linux (WSL) if needed

### Getting Help

- Check the GitHub Issues: https://github.com/OpenMSUtils/OpenMSUtils/issues
- Review the documentation: https://OpenMSUtils.readthedocs.io
- Contact the maintainers: ycliao@zju.edu.cn

## Basic Usage

### Creating MS Objects

```python
from OpenMSUtils.SpectraUtils import MSObject

# Create a new MS object
ms_obj = MSObject(level=2)  # MS2 level
ms_obj.add_peak(100.0, 1000.0)  # m/z, intensity
ms_obj.add_peak(200.0, 2000.0)

print(f"Peaks: {ms_obj.peak_count}")
print(f"TIC: {ms_obj.total_ion_current}")
```

### Reading MZML Files

```python
from OpenMSUtils.SpectraUtils import MZMLReader

# Read an MZML file
reader = MZMLReader("your_file.mzml")
for spectrum in reader:
    print(f"Spectrum {spectrum.scan_number}: {spectrum.peak_count} peaks")
```

### High-Performance Operations

```python
# Batch add peaks (much faster than individual adds)
peaks = [(100.0 + i * 0.1, 1000.0 + i * 10) for i in range(1000)]
ms_obj.add_peaks(peaks)

# Filter by intensity
removed = ms_obj.filter_by_intensity(5000.0)
print(f"Removed {removed} low-intensity peaks")

# Get m/z range
fragments = ms_obj.get_mz_range(200.0, 300.0)
print(f"Found {fragments.peak_count} fragments in range")
```

## Performance Tips

1. **Use batch operations**: `add_peaks()` is much faster than individual `add_peak()` calls
2. **Process in chunks**: For very large files, process data in manageable chunks
3. **Use filters early**: Filter data as early as possible to reduce processing load
4. **Avoid unnecessary copies**: The library uses efficient caching to minimize data copying

## Integration with Existing Code

The library is designed to be a drop-in replacement for existing Python mass spectrometry code:

```python
# Old code (still works)
from some_library import MSObject as OldMSObject

# New high-performance code
from OpenMSUtils.SpectraUtils import MSObject

# Same API, much better performance
```

## Next Steps

- Read the full documentation
- Check out the examples
- Explore the advanced features
- Contribute to the project

---

*For more information, visit: https://github.com/OpenMSUtils/OpenMSUtils*