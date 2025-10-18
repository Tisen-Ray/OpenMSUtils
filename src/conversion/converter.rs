//! 主转换器
//!
//! 提供不同质谱数据格式之间的高性能转换功能

use crate::core::{Spectrum};
use crate::core::types::*;

#[cfg(feature = "python")]
use crate::core::MSObject;
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use pyo3::types::{PyAny, PyDict, PyList, PyTuple};

/// Python兼容的谱图转换器
#[cfg(feature = "python")]
#[pyclass]
pub struct SpectraConverter;

#[cfg(feature = "python")]
#[pymethods]
impl SpectraConverter {
    /// 将任意谱图格式转换为MSObject
    #[staticmethod]
    fn to_msobject(py: Python, spectrum: &PyAny) -> PyResult<Py<PyAny>> {
        // 尝试检测输入类型并转换
        if let Ok(ms_object) = spectrum.extract::<MSObject>() {
            // 已经是MSObject，直接返回
            return Ok(ms_object.into_py(py));
        }

        // 尝试从字典转换
        if let Ok(dict) = spectrum.downcast::<PyDict>() {
            let ms_object = Self::dict_to_msobject(dict)?;
            return Ok(ms_object.into_py(py));
        }

        // 尝试从元组列表转换
        if let Ok(list) = spectrum.downcast::<PyList>() {
            let ms_object = Self::list_to_msobject(list)?;
            return Ok(ms_object.into_py(py));
        }

        Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
            "Unsupported spectrum format"
        ))
    }

    /// 将MSObject转换为指定类型的谱图
    #[staticmethod]
    fn to_spectra(py: Python, ms_object: &PyAny, spectra_type: &str) -> PyResult<Py<PyAny>> {
        let ms_obj = ms_object.extract::<MSObject>()?;

        match spectra_type.to_lowercase().as_str() {
            "dict" | "dictionary" => {
                let dict = Self::msobject_to_dict(&ms_obj, py)?;
                Ok(dict.into())
            }
            "list" | "tuple" => {
                let list = Self::msobject_to_list(&ms_obj, py)?;
                Ok(list.into())
            }
            "numpy" => {
                // 转换为numpy数组格式
                let dict = Self::msobject_to_numpy_dict(&ms_obj, py)?;
                Ok(dict.into())
            }
            _ => Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!("Unsupported spectra type: {}", spectra_type)
            ))
        }
    }

    /// 批量转换多个谱图
    #[staticmethod]
    fn batch_convert(py: Python, spectra: Vec<&PyAny>, target_format: &str) -> PyResult<Py<PyList>> {
        let results = PyList::empty(py);

        for spectrum in spectra {
            let converted = if target_format == "msobject" {
                Self::to_msobject(py, spectrum)?
            } else {
                let ms_object = Self::to_msobject(py, spectrum)?;
                Self::to_spectra(py, ms_object.into_ref(py), target_format)?
            };
            results.append(converted)?;
        }

        Ok(results.into())
    }

    /// 验证谱图数据完整性
    #[staticmethod]
    fn validate_spectrum(py: Python, spectrum: &PyAny) -> PyResult<Py<PyDict>> {
        let result = PyDict::new(py);

        // 尝试转换为MSObject进行验证
        match spectrum.extract::<MSObject>() {
            Ok(ms_object) => {
                let spectrum = &ms_object.spectrum;

                // 基本验证
                result.set_item("valid", true)?;
                result.set_item("peak_count", spectrum.peaks.len())?;
                result.set_item("ms_level", spectrum.level)?;
                result.set_item("has_retention_time", spectrum.scan.retention_time > 0.0)?;
                result.set_item("has_drift_time", spectrum.scan.drift_time > 0.0)?;

                // 数据质量检查
                let total_intensity = spectrum.total_ion_current();
                let base_peak = spectrum.base_peak();
                result.set_item("total_ion_current", total_intensity)?;
                result.set_item("base_peak_mz", base_peak.map_or(0.0, |(mz, _)| mz))?;
                result.set_item("base_peak_intensity", base_peak.map_or(0.0, |(_, intensity)| intensity))?;

                // 检查m/z和强度的合理性
                let (valid_mz_count, valid_intensity_count) = Self::validate_peak_data(&spectrum.peaks);
                result.set_item("valid_mz_count", valid_mz_count)?;
                result.set_item("valid_intensity_count", valid_intensity_count)?;
            }
            Err(_) => {
                result.set_item("valid", false)?;
                result.set_item("error", "Failed to parse spectrum")?;
            }
        }

        Ok(result.into())
    }
}

#[cfg(feature = "python")]
impl SpectraConverter {
    /// 从字典创建MSObject
    fn dict_to_msobject(dict: &PyDict) -> PyResult<MSObject> {
        let mut spectrum = Spectrum::ms1().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
        })?;

        // 设置基本属性
        if let Ok(ms_level) = dict.get_item("ms_level") {
            if let Ok(level) = ms_level.extract::<u8>() {
                spectrum.level = level;
            }
        }

        if let Ok(rt) = dict.get_item("retention_time") {
            if let Ok(retention_time) = rt.extract::<f64>() {
                spectrum.set_retention_time(retention_time).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
                })?;
            }
        }

        if let Ok(dt) = dict.get_item("drift_time") {
            if let Ok(drift_time) = dt.extract::<f64>() {
                spectrum.set_drift_time(drift_time).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
                })?;
            }
        }

        // 添加峰数据
        if let Ok(peaks) = dict.get_item("peaks") {
            if let Ok(peak_list) = peaks.downcast::<PyList>() {
                for peak in peak_list.iter() {
                    if let Ok(peak_tuple) = peak.downcast::<PyTuple>() {
                        if peak_tuple.len() >= 2 {
                            let mz = peak_tuple.get_item(0)?.extract::<f64>()?;
                            let intensity = peak_tuple.get_item(1)?.extract::<f64>()?;
                            spectrum.add_peak(mz, intensity).map_err(|e| {
                                PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
                            })?;
                        }
                    }
                }
            }
        }

        Ok(MSObject { spectrum })
    }

    /// 从列表创建MSObject
    fn list_to_msobject(list: &PyList) -> PyResult<MSObject> {
        let mut spectrum = Spectrum::ms1().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
        })?;

        for item in list.iter() {
            if let Ok(peak_tuple) = item.downcast::<PyTuple>() {
                if peak_tuple.len() >= 2 {
                    let mz = peak_tuple.get_item(0)?.extract::<f64>()?;
                    let intensity = peak_tuple.get_item(1)?.extract::<f64>()?;
                    spectrum.add_peak(mz, intensity).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
                    })?;
                }
            }
        }

        Ok(MSObject { spectrum })
    }

    /// 将MSObject转换为字典
    fn msobject_to_dict(ms_object: &MSObject, py: Python) -> PyResult<Py<PyDict>> {
        let dict = PyDict::new(py);
        let spectrum = &ms_object.spectrum;

        dict.set_item("ms_level", spectrum.level)?;
        dict.set_item("retention_time", spectrum.scan.retention_time)?;
        dict.set_item("drift_time", spectrum.scan.drift_time)?;
        dict.set_item("scan_number", spectrum.scan.scan_number)?;

        // 转换峰数据
        let peaks_list = PyList::empty(py);
        for &(mz, intensity) in &spectrum.peaks {
            peaks_list.append((mz, intensity))?;
        }
        dict.set_item("peaks", peaks_list)?;

        // 添加计算属性
        dict.set_item("total_ion_current", spectrum.total_ion_current())?;
        if let Some((base_mz, base_intensity)) = spectrum.base_peak() {
            dict.set_item("base_peak_mz", base_mz)?;
            dict.set_item("base_peak_intensity", base_intensity)?;
        }

        Ok(dict)
    }

    /// 将MSObject转换为列表
    fn msobject_to_list(ms_object: &MSObject, py: Python) -> PyResult<Py<PyList>> {
        let list = PyList::empty(py);
        for &(mz, intensity) in &ms_object.spectrum.peaks {
            list.append((mz, intensity))?;
        }
        Ok(list)
    }

    /// 将MSObject转换为numpy兼容格式
    fn msobject_to_numpy_dict(ms_object: &MSObject, py: Python) -> PyResult<Py<PyDict>> {
        let dict = PyDict::new(py);
        let spectrum = &ms_object.spectrum;

        // 创建m/z和强度数组
        let mz_array = PyList::empty(py);
        let intensity_array = PyList::empty(py);

        for &(mz, intensity) in &spectrum.peaks {
            mz_array.append(mz)?;
            intensity_array.append(intensity)?;
        }

        dict.set_item("mz_array", mz_array)?;
        dict.set_item("intensity_array", intensity_array)?;
        dict.set_item("ms_level", spectrum.level)?;
        dict.set_item("retention_time", spectrum.scan.retention_time)?;

        Ok(dict)
    }

    /// 验证峰数据质量
    fn validate_peak_data(peaks: &[(f64, f64)]) -> (usize, usize) {
        let mut valid_mz = 0;
        let mut valid_intensity = 0;

        for &(mz, intensity) in peaks {
            // 检查m/z是否合理
            if mz > 0.0 && mz.is_finite() && !mz.is_nan() {
                valid_mz += 1;
            }

            // 检查强度是否合理
            if intensity >= 0.0 && intensity.is_finite() && !intensity.is_nan() {
                valid_intensity += 1;
            }
        }

        (valid_mz, valid_intensity)
    }
}


#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::spectrum::Spectrum;

    #[test]
    fn test_basic_conversion() {
        let mut spectrum = Spectrum::ms1().unwrap();
        spectrum.add_peak(100.0, 1000.0).unwrap();
        spectrum.add_peak(200.0, 2000.0).unwrap();

        let ms_object = MSObject { spectrum };

        // 测试转换（这里需要Python环境，所以只能测试基础逻辑）
        assert_eq!(ms_object.spectrum.peaks.len(), 2);
    }

    #[test]
    fn test_advanced_converter() {
        let converter = AdvancedConverter::new();
        assert!(converter.simd_processor.supports_avx2() || converter.simd_processor.supports_sse41());
    }

    #[test]
    fn test_conversion_report() {
        let converter = AdvancedConverter::new();
        let spectrum1 = Spectrum::ms1().unwrap();
        let spectrum2 = Spectrum::ms1().unwrap();

        let report = converter.generate_conversion_report(&[spectrum1, spectrum2], &[]);
        assert_eq!(report.original_count, 2);
        assert_eq!(report.converted_count, 0);
        assert_eq!(report.conversion_rate, 0.0);
    }
}
