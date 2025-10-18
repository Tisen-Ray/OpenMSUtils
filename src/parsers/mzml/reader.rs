//! MZML Python读取器
//!
//! 这个模块提供了与原Python MZMLReader完全兼容的接口

#[cfg(feature = "python")]
use crate::core::ms_object::MSObject;
use crate::core::spectrum::Spectrum;
use crate::parsers::mzml::parser::MZMLParser;
use crate::parsers::common::ParseResult;

#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use pyo3::types::{PyList, PyAny};
use std::sync::Arc;

/// Python兼容的MZML读取器
#[cfg(feature = "python")]
#[pyclass]
pub struct MZMLReader {
    parser: MZMLParser,
}

/// Python兼容的MZML对象
#[cfg(feature = "python")]
#[pyclass]
pub struct MZMLObject {
    pub spectra: Vec<MSObject>,
    pub file_info: MZMLFileInfo,
}

/// MZML文件信息
#[cfg(feature = "python")]
#[pyclass]
#[derive(Debug, Clone)]
pub struct MZMLFileInfo {
    #[pyo3(get)]
    pub file_path: String,
    #[pyo3(get)]
    pub spectrum_count: usize,
    #[pyo3(get)]
    pub ms1_count: usize,
    #[pyo3(get)]
    pub ms2_count: usize,
    #[pyo3(get)]
    pub file_format: String,
    #[pyo3(get)]
    pub version: Option<String>,
}

#[cfg(feature = "python")]
impl MZMLFileInfo {
    pub fn new(file_path: String) -> Self {
        Self {
            file_path,
            spectrum_count: 0,
            ms1_count: 0,
            ms2_count: 0,
            file_format: "mzML".to_string(),
            version: None,
        }
    }
}

#[cfg(feature = "python")]
#[pymethods]
impl MZMLReader {
    /// 创建新的MZML读取器
    #[new]
    fn new() -> Self {
        Self {
            parser: MZMLParser::new(),
        }
    }

    /// 读取MZML文件并返回MZMLObject
    #[pyo3(signature = (filename, parse_spectra=true, parallel=false, num_processes=None))]
    fn read(
        &self,
        py: Python,
        filename: &str,
        parse_spectra: bool,
        parallel: bool,
        num_processes: Option<usize>,
    ) -> PyResult<Py<PyAny>> {
        // 创建解析器
        let parser = if parallel {
            let num_threads = num_processes.unwrap_or_else(|| num_cpus::get());
            MZMLParser::new_parallel(num_threads)
        } else {
            MZMLParser::new()
        };

        // 解析文件
        let spectra = if parse_spectra {
            parser.parse_sequential(filename)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?
        } else {
            Vec::new()
        };

        // 创建文件信息
        let mut file_info = MZMLFileInfo::new(filename.to_string());
        file_info.spectrum_count = spectra.len();
        
        for spectrum in &spectra {
            match spectrum.level {
                1 => file_info.ms1_count += 1,
                2 => file_info.ms2_count += 1,
                _ => {}
            }
        }

        // 创建MSObject列表
        let ms_objects: Result<Vec<MSObject>, PyErr> = spectra
            .into_iter()
            .map(|spectrum| {
                let ms_object = MSObject { spectrum };
                Ok(ms_object)
            })
            .collect();

        let mzml_object = MZMLObject {
            spectra: ms_objects?,
            file_info,
        };

        Ok(Py::new(py, mzml_object)?.into())
    }

    /// 读取MZML文件并返回MSObject列表
    #[pyo3(signature = (filename, parallel=false, num_processes=None))]
    fn read_to_msobjects(
        &self,
        py: Python,
        filename: &str,
        parallel: bool,
        num_processes: Option<usize>,
    ) -> PyResult<Py<PyList>> {
        // 创建解析器
        let parser = if parallel {
            let num_threads = num_processes.unwrap_or_else(|| num_cpus::get());
            MZMLParser::new_parallel(num_threads)
        } else {
            MZMLParser::new()
        };

        // 解析文件
        let spectra = parser.parse_sequential(filename)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;

        // 转换为MSObject列表
        let ms_objects = PyList::empty(py);
        for spectrum in spectra {
            let ms_object = MSObject { spectrum };
            ms_objects.append(Py::new(py, ms_object)?)?;
        }

        Ok(ms_objects.into())
    }

    /// 读取单个谱图
    fn read_spectrum(&self, py: Python, filename: &str, spectrum_index: usize) -> PyResult<Py<PyAny>> {
        let spectra = self.parser.parse_sequential(filename)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;

        if spectrum_index >= spectra.len() {
            return Err(PyErr::new::<pyo3::exceptions::PyIndexError, _>(
                format!("Spectrum index {} out of range (0..{})", spectrum_index, spectra.len())
            ));
        }

        let spectrum = spectra.into_iter().nth(spectrum_index).unwrap();
        let ms_object = MSObject { spectrum };
        Ok(Py::new(py, ms_object)?.into())
    }

    /// 获取文件信息
    fn get_file_info(&self, py: Python, filename: &str) -> PyResult<Py<PyAny>> {
        let spectra = self.parser.parse_sequential(filename)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;

        let mut file_info = MZMLFileInfo::new(filename.to_string());
        file_info.spectrum_count = spectra.len();
        
        for spectrum in &spectra {
            match spectrum.level {
                1 => file_info.ms1_count += 1,
                2 => file_info.ms2_count += 1,
                _ => {}
            }
        }

        Ok(Py::new(py, file_info)?.into())
    }

    /// 验证MZML文件
    fn validate_file(&self, filename: &str) -> PyResult<bool> {
        match self.parser.parse_sequential(filename) {
            Ok(_) => Ok(true),
            Err(_) => Ok(false),
        }
    }

    /// 获取谱图数量
    fn get_spectrum_count(&self, filename: &str) -> PyResult<usize> {
        let spectra = self.parser.parse_sequential(filename)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        Ok(spectra.len())
    }

    /// 获取MS1谱图数量
    fn get_ms1_count(&self, filename: &str) -> PyResult<usize> {
        let spectra = self.parser.parse_sequential(filename)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        
        let ms1_count = spectra.iter()
            .filter(|s| s.level == 1)
            .count();
        
        Ok(ms1_count)
    }

    /// 获取MS2谱图数量
    fn get_ms2_count(&self, filename: &str) -> PyResult<usize> {
        let spectra = self.parser.parse_sequential(filename)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        
        let ms2_count = spectra.iter()
            .filter(|s| s.level == 2)
            .count();
        
        Ok(ms2_count)
    }
}

#[cfg(feature = "python")]
#[pymethods]
impl MZMLObject {
    /// 获取谱图数量
    #[getter]
    fn spectrum_count(&self) -> usize {
        self.spectra.len()
    }

    /// 获取MS1谱图
    #[getter]
    fn ms1_spectra(&self, py: Python) -> PyResult<Py<PyList>> {
        let ms1_list = PyList::empty(py);
        for spectrum in &self.spectra {
            if spectrum.is_ms1() {
                ms1_list.append(Py::new(py, spectrum.clone())?)?;
            }
        }
        Ok(ms1_list.into())
    }

    /// 获取MS2谱图
    #[getter]
    fn ms2_spectra(&self, py: Python) -> PyResult<Py<PyList>> {
        let ms2_list = PyList::empty(py);
        for spectrum in &self.spectra {
            if spectrum.is_ms2() {
                ms2_list.append(Py::new(py, spectrum.clone())?)?;
            }
        }
        Ok(ms2_list.into())
    }

    /// 获取所有谱图
    #[getter]
    fn spectra(&self, py: Python) -> PyResult<Py<PyList>> {
        let spectra_list = PyList::empty(py);
        for spectrum in &self.spectra {
            spectra_list.append(Py::new(py, spectrum.clone())?)?;
        }
        Ok(spectra_list.into())
    }

    /// 按索引获取谱图
    fn get_spectrum(&self, py: Python, index: usize) -> PyResult<Py<PyAny>> {
        if index >= self.spectra.len() {
            return Err(PyErr::new::<pyo3::exceptions::PyIndexError, _>(
                format!("Index {} out of range", index)
            ));
        }
        Ok(Py::new(py, self.spectra[index].clone())?.into())
    }

    /// 按扫描编号获取谱图
    fn get_spectrum_by_scan_number(&self, py: Python, scan_number: u32) -> PyResult<Py<PyAny>> {
        for spectrum in &self.spectra {
            if spectrum.scan_number() == scan_number {
                return Ok(Py::new(py, spectrum.clone())?.into());
            }
        }
        Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            format!("No spectrum found with scan number {}", scan_number)
        ))
    }

    /// 按保留时间范围获取谱图
    fn get_spectra_by_rt_range(&self, py: Python, rt_min: f64, rt_max: f64) -> PyResult<Py<PyList>> {
        let spectra_list = PyList::empty(py);
        for spectrum in &self.spectra {
            let rt = spectrum.retention_time();
            if rt >= rt_min && rt <= rt_max {
                spectra_list.append(Py::new(py, spectrum.clone())?)?;
            }
        }
        Ok(spectra_list.into())
    }

    /// 按m/z范围获取谱图
    fn get_spectra_by_mz_range(&self, py: Python, mz_min: f64, mz_max: f64) -> PyResult<Py<PyList>> {
        let spectra_list = PyList::empty(py);
        for spectrum in &self.spectra {
            let peaks = spectrum.peaks(py)?;
            for peak in peaks.iter()? {
                let tuple = peak?.downcast::<pyo3::types::PyTuple>()?;
                let mz = tuple.get_item(0)?.extract::<f64>()?;
                if mz >= mz_min && mz <= mz_max {
                    spectra_list.append(Py::new(py, spectrum.clone())?)?;
                    break;
                }
            }
        }
        Ok(spectra_list.into())
    }

    /// 获取文件信息
    #[getter]
    fn file_info(&self) -> MZMLFileInfo {
        self.file_info.clone()
    }

    /// 迭代谱图
    fn __iter__(&self, py: Python) -> PyResult<Py<PyAny>> {
        use pyo3::types::PyIterator;
        let spectra_list = self.spectra(py)?;
        PyIterator::from_object(spectra_list)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyTypeError, _>(e.to_string()))
    }

    /// 获取长度
    fn __len__(&self) -> usize {
        self.spectra.len()
    }

    /// 字符串表示
    fn __repr__(&self) -> String {
        format!("MZMLObject(spectra={}, ms1={}, ms2={})", 
                self.spectra.len(), 
                self.file_info.ms1_count,
                self.file_info.ms2_count)
    }

    /// 字符串表示
    fn __str__(&self) -> String {
        self.__repr__()
    }
}

#[cfg(feature = "python")]
#[pymethods]
impl MZMLFileInfo {
    /// 字符串表示
    fn __repr__(&self) -> String {
        format!("MZMLFileInfo(file='{}', spectra={}, ms1={}, ms2={})",
                self.file_path,
                self.spectrum_count,
                self.ms1_count,
                self.ms2_count)
    }

    /// 字符串表示
    fn __str__(&self) -> String {
        self.__repr__()
    }
}

#[cfg(all(test, feature = "python"))]
mod tests {
    use super::*;
    use pyo3::Python;

    #[test]
    fn test_mzml_reader_creation() {
        Python::with_gil(|py| {
            let reader = MZMLReader::new();
            // 基本创建测试
            assert!(true); // 如果能创建就通过
        });
    }

    #[test]
    fn test_mzml_file_info() {
        let file_info = MZMLFileInfo::new("test.mzML".to_string());
        assert_eq!(file_info.file_path, "test.mzML");
        assert_eq!(file_info.file_format, "mzML");
        assert_eq!(file_info.spectrum_count, 0);
    }

    #[test]
    fn test_mzml_object_creation() {
        Python::with_gil(|py| {
            let file_info = MZMLFileInfo::new("test.mzML".to_string());
            let mzml_object = MZMLObject {
                spectra: Vec::new(),
                file_info,
            };
            
            assert_eq!(mzml_object.spectrum_count(), 0);
            assert_eq!(mzml_object.__len__(), 0);
        });
    }
}
