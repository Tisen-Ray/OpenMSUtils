//! Core mass spectrometry data structures and operations
//!
//! This module provides the fundamental data structures for handling
//! mass spectrometry data with high performance memory management
//! and optimized algorithms for common operations.

use pyo3::prelude::*;
use pyo3::types::{PyList, PyTuple};
use std::cmp::Ordering;

/// High-performance peak data structure
///
/// Uses struct of arrays for better cache locality when processing
/// large numbers of peaks
#[derive(Debug, Clone)]
pub struct Peak {
    pub mz: f64,
    pub intensity: f64,
}

impl Peak {
    #[inline]
    pub fn new(mz: f64, intensity: f64) -> Self {
        Self { mz, intensity }
    }

    #[inline]
    pub fn mz(&self) -> f64 {
        self.mz
    }

    #[inline]
    pub fn intensity(&self) -> f64 {
        self.intensity
    }
}

/// Core spectrum data structure with optimized memory layout
///
/// This structure provides efficient storage and manipulation of
/// mass spectrometry spectrum data with Python bindings
#[pyclass]
#[derive(Debug, Clone)]
pub struct Spectrum {
    #[pyo3(get)]
    pub level: u8,
    #[pyo3(get)]
    pub scan_number: u32,
    #[pyo3(get)]
    pub retention_time: f64,
    peaks: Vec<Peak>,
    sorted: bool,
}

#[pymethods]
impl Spectrum {
    /// Create a new spectrum with the specified MS level
    #[new]
    pub fn new(level: u8) -> Self {
        Self {
            level,
            scan_number: 0,
            retention_time: 0.0,
            peaks: Vec::new(),
            sorted: true,
        }
    }

    /// Create a spectrum with peak data
    #[staticmethod]
    fn with_peaks(level: u8, mz_array: Vec<f64>, intensity_array: Vec<f64>) -> PyResult<Self> {
        if mz_array.len() != intensity_array.len() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "MZ and intensity arrays must have the same length"
            ));
        }

        let mut peaks: Vec<Peak> = mz_array
            .into_iter()
            .zip(intensity_array.into_iter())
            .map(|(mz, intensity)| Peak::new(mz, intensity))
            .collect();

        // Check if already sorted
        let sorted = peaks.windows(2).all(|w| w[0].mz <= w[1].mz);

        Ok(Self {
            level,
            scan_number: 0,
            retention_time: 0.0,
            peaks,
            sorted,
        })
    }

    /// Get peak data as Python list of tuples
    #[getter]
    fn peaks(&self, py: Python) -> PyResult<Py<PyList>> {
        let list = PyList::empty_bound(py);
        for peak in &self.peaks {
            list.append((peak.mz, peak.intensity))?;
        }
        Ok(list.into())
    }

    /// Get number of peaks
    #[getter]
    fn peak_count(&self) -> usize {
        self.peaks.len()
    }

    /// Get total ion current (sum of intensities)
    #[getter]
    fn total_ion_current(&self) -> f64 {
        self.peaks.iter().map(|peak| peak.intensity).sum()
    }

    /// Get base peak intensity (maximum intensity)
    #[getter]
    fn base_peak_intensity(&self) -> f64 {
        self.peaks
            .iter()
            .map(|peak| peak.intensity)
            .fold(0.0, f64::max)
    }

    /// Get base peak m/z (m/z of maximum intensity peak)
    #[getter]
    fn base_peak_mz(&self) -> f64 {
        self.peaks
            .iter()
            .max_by(|a, b| a.intensity.partial_cmp(&b.intensity).unwrap())
            .map(|peak| peak.mz)
            .unwrap_or(0.0)
    }

    /// Add a single peak to the spectrum
    fn add_peak(&mut self, mz: f64, intensity: f64) {
        self.peaks.push(Peak::new(mz, intensity));
        self.sorted = false;
    }

    /// Add multiple peaks efficiently
    pub fn add_peaks(&mut self, mz_array: Vec<f64>, intensity_array: Vec<f64>) -> PyResult<()> {
        if mz_array.len() != intensity_array.len() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "MZ and intensity arrays must have the same length"
            ));
        }

        let new_peaks: Vec<Peak> = mz_array
            .into_iter()
            .zip(intensity_array.into_iter())
            .map(|(mz, intensity)| Peak::new(mz, intensity))
            .collect();

        self.peaks.extend(new_peaks);
        self.sorted = false;
        Ok(())
    }

    /// Sort peaks by m/z (if not already sorted)
    pub fn sort_peaks(&mut self) {
        if !self.sorted {
            self.peaks.sort_by(|a, b| a.mz.partial_cmp(&b.mz).unwrap());
            self.sorted = true;
        }
    }

    /// Clear all peaks
    fn clear_peaks(&mut self) {
        self.peaks.clear();
        self.sorted = true;
    }

    /// Filter peaks by intensity threshold
    fn filter_by_intensity(&mut self, threshold: f64) -> usize {
        let initial_count = self.peaks.len();
        self.peaks.retain(|peak| peak.intensity >= threshold);
        initial_count - self.peaks.len()
    }

    /// Filter peaks by m/z range
    fn filter_by_mz_range(&mut self, min_mz: f64, max_mz: f64) -> usize {
        let initial_count = self.peaks.len();
        self.peaks.retain(|peak| peak.mz >= min_mz && peak.mz <= max_mz);
        initial_count - self.peaks.len()
    }

    /// Get peaks in m/z range (returns new spectrum)
    fn get_mz_range(&self, min_mz: f64, max_mz: f64) -> Spectrum {
        let filtered_peaks: Vec<Peak> = self.peaks
            .iter()
            .filter(|peak| peak.mz >= min_mz && peak.mz <= max_mz)
            .cloned()
            .collect();

        Spectrum {
            level: self.level,
            scan_number: self.scan_number,
            retention_time: self.retention_time,
            peaks: filtered_peaks,
            sorted: self.sorted, // Preserves sorted status
        }
    }

    /// Find peaks within tolerance of target m/z
    fn find_peaks_in_tolerance(&self, target_mz: f64, tolerance: f64) -> Vec<(f64, f64)> {
        self.peaks
            .iter()
            .filter(|peak| (peak.mz - target_mz).abs() <= tolerance)
            .map(|peak| (peak.mz, peak.intensity))
            .collect()
    }

    /// Get m/z array
    #[getter]
    fn mz_array(&self, py: Python) -> PyResult<Py<PyList>> {
        let list = PyList::empty_bound(py);
        for peak in &self.peaks {
            list.append(peak.mz)?;
        }
        Ok(list.into())
    }

    /// Get intensity array
    #[getter]
    fn intensity_array(&self, py: Python) -> PyResult<Py<PyList>> {
        let list = PyList::empty_bound(py);
        for peak in &self.peaks {
            list.append(peak.intensity)?;
        }
        Ok(list.into())
    }

    /// Normalize spectrum to maximum intensity
    fn normalize(&mut self) -> f64 {
        let max_intensity = self.base_peak_intensity();
        if max_intensity > 0.0 {
            for peak in &mut self.peaks {
                peak.intensity /= max_intensity;
            }
        }
        max_intensity
    }

    /// String representation
    fn __repr__(&self) -> String {
        format!(
            "Spectrum(level={}, peaks={}, retention_time={:.3})",
            self.level,
            self.peaks.len(),
            self.retention_time
        )
    }

    /// String representation for print()
    fn __str__(&self) -> String {
        self.__repr__()
    }
}

impl Spectrum {
    /// Check if peaks are sorted
    pub fn is_sorted(&self) -> bool {
        self.sorted
    }

    /// Get internal peaks reference for efficient processing
    pub fn peaks_ref(&self) -> &[Peak] {
        &self.peaks
    }

    /// Get mutable internal peaks reference for efficient processing
    pub fn peaks_mut(&mut self) -> &mut Vec<Peak> {
        &mut self.peaks
    }

    /// Binary search for peak range (requires sorted peaks)
    pub fn find_peak_range(&self, min_mz: f64, max_mz: f64) -> Option<(usize, usize)> {
        if !self.sorted || self.peaks.is_empty() {
            return None;
        }

        let start = self.peaks.binary_search_by(|peak| {
            if peak.mz < min_mz {
                Ordering::Less
            } else if peak.mz >= min_mz {
                Ordering::Greater
            } else {
                Ordering::Equal
            }
        }).unwrap_or_else(|idx| idx);

        let end = self.peaks.binary_search_by(|peak| {
            if peak.mz <= max_mz {
                Ordering::Less
            } else {
                Ordering::Greater
            }
        }).unwrap_or_else(|idx| idx);

        if start < end {
            Some((start, end))
        } else {
            None
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_spectrum_creation() {
        let spectrum = Spectrum::new(2);
        assert_eq!(spectrum.level, 2);
        assert_eq!(spectrum.peak_count(), 0);
        assert!(spectrum.is_sorted());
    }

    #[test]
    fn test_peak_operations() {
        let mut spectrum = Spectrum::new(2);

        // Add peaks
        spectrum.add_peak(100.0, 1000.0);
        spectrum.add_peak(200.0, 2000.0);
        spectrum.add_peak(150.0, 1500.0);

        assert_eq!(spectrum.peak_count(), 3);
        assert!(!spectrum.is_sorted());

        // Sort peaks
        spectrum.sort_peaks();
        assert!(spectrum.is_sorted());

        // Check TIC
        assert_eq!(spectrum.total_ion_current(), 4500.0);

        // Check base peak
        assert_eq!(spectrum.base_peak_intensity(), 2000.0);
        assert_eq!(spectrum.base_peak_mz(), 200.0);
    }

    #[test]
    fn test_spectrum_with_arrays() {
        let mz = vec![100.0, 200.0, 300.0];
        let intensity = vec![1000.0, 2000.0, 1500.0];

        let spectrum = Spectrum::with_peaks(2, mz, intensity).unwrap();

        assert_eq!(spectrum.peak_count(), 3);
        assert!(spectrum.is_sorted());
        assert_eq!(spectrum.total_ion_current(), 4500.0);
    }
}