// 简单的测试模块，用于验证Rust-Python集成

use pyo3::prelude::*;
use pyo3::types::PyList;
use crate::core::Spectrum;
use crate::parsers::{MZMLParser, MZMLUtils};

#[pyclass]
#[derive(Debug, Clone)]
pub struct TestMSObject {
    #[pyo3(get)]
    pub level: u8,
    #[pyo3(get)]
    pub scan_number: u32,
    #[pyo3(get)]
    pub retention_time: f64,
    peaks: Vec<(f64, f64)>,
}

#[pymethods]
impl TestMSObject {
    #[new]
    fn new(level: u8) -> Self {
        Self {
            level,
            scan_number: 0,
            retention_time: 0.0,
            peaks: Vec::new(),
        }
    }

    #[getter]
    fn peaks(&self, py: Python) -> PyResult<Py<PyList>> {
        let list = PyList::empty_bound(py);
        for (mz, intensity) in &self.peaks {
            list.append((mz, intensity))?;
        }
        Ok(list.into())
    }

    fn add_peak(&mut self, mz: f64, intensity: f64) {
        self.peaks.push((mz, intensity));
    }

    fn sort_peaks(&mut self) {
        self.peaks.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
    }

    fn peak_count(&self) -> usize {
        self.peaks.len()
    }

    fn total_ion_current(&self) -> f64 {
        self.peaks.iter().map(|(_, intensity)| *intensity).sum()
    }

    fn __repr__(&self) -> String {
        format!("TestMSObject(level={}, peaks={})", self.level, self.peaks.len())
    }
}

