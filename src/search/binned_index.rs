//! 二进制索引实现
//!
//! 提供与原Python接口1:1兼容的二进制索引功能

use crate::core::{Spectrum, BinnedSpectraIndex, CoreResult};
use crate::core::types::*;
use std::collections::HashMap;

#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use pyo3::types::{PyList, PyAny};

/// Python兼容的二进制谱图索引
#[cfg(feature = "python")]
#[pyclass]
pub struct BinnedSpectra {
    pub spectra: Vec<Peak>,
    pub bin_size: f64,
    pub bin_indices: HashMap<i32, (usize, usize)>,
}

#[cfg(feature = "python")]
#[pymethods]
impl BinnedSpectra {
    #[new]
    fn new(spectra_list: Vec<&PyAny>, bin_size: f64) -> PyResult<Self> {
        let mut peaks = Vec::new();

        for py_spectrum in spectra_list {
            // 尝试从MSObject提取峰数据
            if let Ok(ms_object) = py_spectrum.extract::<crate::core::ms_object::MSObject>() {
                peaks.extend_from_slice(&ms_object.spectrum.peaks);
            }
            // 尝试从元组列表提取峰数据
            else if let Ok(peak_list) = py_spectrum.extract::<Vec<(f64, f64)>>() {
                peaks.extend(peak_list);
            } else {
                return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
                    "unsupported spectra type, expected MSObject or list of (mz, intensity) tuples"
                ));
            }
        }

        // 排序峰数据
        peaks.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());

        let mut instance = Self {
            spectra: peaks,
            bin_size,
            bin_indices: HashMap::new(),
        };

        // 生成bin索引
        instance.bin_indices = instance._generate_bin_indices();

        Ok(instance)
    }

    /// 搜索指定mz范围内的峰值
    fn search_peaks(&self, py: Python, mz_range: (f64, f64)) -> PyResult<Py<PyList>> {
        let (mz_low, mz_high) = mz_range;
        let bin_low = (mz_low / self.bin_size) as i32;
        let bin_high = (mz_high / self.bin_size) as i32;

        let mut low_index = -1isize;
        let mut high_index = -1isize;

        for bin_index in bin_low..=bin_high {
            if let Some((start, end)) = self.bin_indices.get(&bin_index) {
                if low_index == -1 {
                    low_index = *start as isize;
                }
                high_index = *end as isize;
            }
        }

        let results = if low_index == -1 || high_index == -1 {
            Vec::new()
        } else {
            let start_idx = low_index as usize;
            let end_idx = high_index as usize;
            let mut filtered = Vec::new();

            for i in start_idx..=end_idx.min(self.spectra.len() - 1) {
                let (mz, intensity) = self.spectra[i];
                if mz >= mz_low && mz <= mz_high {
                    filtered.push((mz, intensity));
                }
            }
            filtered
        };

        let py_results = PyList::empty(py);
        for (mz, intensity) in results {
            py_results.append((mz, intensity))?;
        }

        Ok(py_results.into())
    }

    /// 生成bin索引（内部方法，但保留以供Python调用）
    fn _generate_bin_indices(&self) -> HashMap<i32, (usize, usize)> {
        let mut mz_to_index = HashMap::new();

        if self.spectra.is_empty() {
            return mz_to_index;
        }

        for (index, &(mz, _)) in self.spectra.iter().enumerate() {
            let bin_index = (mz / self.bin_size) as i32;

            if let Some((start, end)) = mz_to_index.get_mut(&bin_index) {
                *end = index;
            } else {
                mz_to_index.insert(bin_index, (index, index));
            }
        }

        mz_to_index
    }
}

impl BinnedSpectra {
    /// 创建新的二进制谱图索引（Rust接口）
    pub fn from_spectra(spectra: Vec<Spectrum>, bin_size: f64) -> CoreResult<Self> {
        let mut peaks = Vec::new();
        for spectrum in spectra {
            peaks.extend_from_slice(&spectrum.peaks);
        }

        // 排序峰数据
        peaks.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());

        let mut instance = Self {
            spectra: peaks,
            bin_size,
            bin_indices: HashMap::new(),
        };

        // 生成bin索引
        instance.bin_indices = instance._generate_bin_indices();

        Ok(instance)
    }

    /// 搜索m/z范围内的峰（Rust接口）
    pub fn search_range(&self, mz_range: (f64, f64)) -> CoreResult<Vec<Peak>> {
        let (mz_low, mz_high) = mz_range;
        let bin_low = (mz_low / self.bin_size) as i32;
        let bin_high = (mz_high / self.bin_size) as i32;

        let mut low_index = -1isize;
        let mut high_index = -1isize;

        for bin_index in bin_low..=bin_high {
            if let Some((start, end)) = self.bin_indices.get(&bin_index) {
                if low_index == -1 {
                    low_index = *start as isize;
                }
                high_index = *end as isize;
            }
        }

        if low_index == -1 || high_index == -1 {
            return Ok(Vec::new());
        }

        let start_idx = low_index as usize;
        let end_idx = high_index as usize;
        let mut filtered = Vec::new();

        for i in start_idx..=end_idx.min(self.spectra.len() - 1) {
            let (mz, intensity) = self.spectra[i];
            if mz >= mz_low && mz <= mz_high {
                filtered.push((mz, intensity));
            }
        }

        Ok(filtered)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_binned_spectra_creation() {
        let peaks = vec![(100.0, 1000.0), (200.0, 2000.0)];
        let binned = BinnedSpectra::from_spectra(Vec::new(), 10.0).unwrap();
        // 基本创建测试
    }

    #[test]
    fn test_search_range() {
        let mut peaks = vec![(100.0, 1000.0), (200.0, 2000.0), (300.0, 1500.0)];
        peaks.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());

        let mut binned = BinnedSpectra {
            spectra: peaks,
            bin_size: 10.0,
            bin_indices: HashMap::new(),
        };
        binned.bin_indices = binned._generate_bin_indices();

        let results = binned.search_range((90.0, 110.0)).unwrap();
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].0, 100.0);
    }
}
