//! MSObject Python兼容层
//! 
//! 这个模块提供了与原Python MSObject完全兼容的接口，
//! 确保用户代码无需修改即可使用Rust实现。

use crate::core::spectrum::{Spectrum, PrecursorInfo, ScanInfo};
use crate::core::types::*;
use std::collections::HashMap;

#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use pyo3::types::{PyList, PyTuple, PyDict, PyAny};

/// Python兼容的MSObject类
#[cfg(feature = "python")]
#[pyclass]
#[derive(Debug, Clone)]
pub struct MSObject {
    pub spectrum: Spectrum,
}

/// Python兼容的前体离子类
#[cfg(feature = "python")]
#[pyclass]
#[derive(Debug, Clone)]
pub struct Precursor {
    pub precursor: PrecursorInfo,
}

/// Python兼容的扫描信息类
#[cfg(feature = "python")]
#[pyclass]
#[derive(Debug, Clone)]
pub struct Scan {
    pub scan: ScanInfo,
}

/// Python兼容的键值对类
#[cfg(feature = "python")]
#[pyclass]
#[derive(Debug, Clone)]
pub struct KeyValue {
    #[pyo3(get)]
    pub key: String,
    #[pyo3(get)]
    pub value: String,
}

#[cfg(feature = "python")]
impl From<KeyValue> for crate::core::types::KeyValue {
    fn from(kv: KeyValue) -> Self {
        Self {
            key: kv.key,
            value: kv.value,
        }
    }
}

#[cfg(feature = "python")]
impl From<crate::core::types::KeyValue> for KeyValue {
    fn from(kv: crate::core::types::KeyValue) -> Self {
        Self {
            key: kv.key,
            value: kv.value,
        }
    }
}

#[cfg(feature = "python")]
#[pymethods]
impl MSObject {
    /// 创建新的MSObject实例
    #[new]
    #[pyo3(signature = (level=1, peaks=None, precursor=None, scan=None, additional_info=None))]
    fn new(
        py: Python,
        level: u8,
        peaks: Option<&PyList>,
        precursor: Option<&PyAny>,
        scan: Option<&PyAny>,
        additional_info: Option<&PyDict>,
    ) -> PyResult<Self> {
        // 创建基础Spectrum对象
        let mut spectrum = Spectrum::new(level).map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
        })?;

        // 解析peaks参数
        if let Some(peaks_list) = peaks {
            for item in peaks_list.iter() {
                let tuple = item.downcast::<PyTuple>()?;
                let mz = tuple.get_item(0)?.extract::<f64>()?;
                let intensity = tuple.get_item(1)?.extract::<f64>()?;
                spectrum.add_peak(mz, intensity).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
                })?;
            }
        }

        // 解析precursor参数
        if let Some(prec_obj) = precursor {
            let precursor_info = parse_precursor_from_python(prec_obj)?;
            spectrum.set_precursor(precursor_info);
        }

        // 解析scan参数
        if let Some(scan_obj) = scan {
            let scan_info = parse_scan_from_python(scan_obj)?;
            spectrum.set_scan_info(scan_info);
        }

        // 解析additional_info参数
        if let Some(info_dict) = additional_info {
            for (key, value) in info_dict.iter() {
                let key_str = key.extract::<String>()?;
                let value_str = value.extract::<String>()?;
                spectrum.add_additional_info(key_str, value_str).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
                })?;
            }
        }

        Ok(Self { spectrum })
    }

    /// 获取MS级别
    #[getter]
    fn level(&self) -> u8 {
        self.spectrum.level
    }

    /// 设置MS级别
    #[setter]
    fn set_level(&mut self, level: u8) -> PyResult<()> {
        if level < constants::MIN_MS_LEVEL || level > constants::MAX_MS_LEVEL {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                format!("Invalid MS level: {}. Must be between {} and {}", 
                       level, constants::MIN_MS_LEVEL, constants::MAX_MS_LEVEL)
            ));
        }
        self.spectrum.level = level;
        Ok(())
    }

    /// 获取质谱峰数据
    #[getter]
    fn peaks(&self, py: Python) -> PyResult<Py<PyList>> {
        let list = PyList::empty_bound(py);
        for (mz, intensity) in &self.spectrum.peaks {
            list.append((mz, intensity))?;
        }
        Ok(list.into())
    }

    /// 设置质谱峰数据
    #[setter]
    fn set_peaks(&mut self, peaks: &PyList) -> PyResult<()> {
        self.spectrum.clear_peaks();
        for item in peaks.iter() {
            let tuple = item.downcast::<PyTuple>()?;
            let mz = tuple.get_item(0)?.extract::<f64>()?;
            let intensity = tuple.get_item(1)?.extract::<f64>()?;
            self.spectrum.add_peak(mz, intensity).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
            })?;
        }
        Ok(())
    }

    /// 获取前体离子信息
    #[getter]
    fn precursor(&self, py: Python) -> PyResult<Py<PyAny>> {
        if let Some(precursor) = &self.spectrum.precursor {
            let py_precursor = Py::new(py, Precursor { precursor: **precursor.clone() })?;
            Ok(py_precursor.into())
        } else {
            let empty_precursor = PrecursorInfo::default();
            let py_precursor = Py::new(py, Precursor { precursor: empty_precursor })?;
            Ok(py_precursor.into())
        }
    }

    /// 获取扫描信息
    #[getter]
    fn scan(&self, py: Python) -> PyResult<Py<PyAny>> {
        let py_scan = Py::new(py, Scan { scan: self.spectrum.scan.clone() })?;
        Ok(py_scan.into())
    }

    /// 获取扫描编号
    #[getter]
    fn scan_number(&self) -> u32 {
        self.spectrum.scan.scan_number
    }

    /// 设置扫描编号
    #[setter]
    fn set_scan_number(&mut self, scan_number: u32) {
        self.spectrum.set_scan_number(scan_number);
    }

    /// 获取保留时间
    #[getter]
    fn retention_time(&self) -> f64 {
        self.spectrum.scan.retention_time
    }

    /// 设置保留时间
    #[setter]
    fn set_retention_time(&mut self, retention_time: f64) -> PyResult<()> {
        self.spectrum.set_retention_time(retention_time).map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
        })
    }

    /// 获取额外信息
    #[getter]
    fn additional_info(&self, py: Python) -> PyResult<Py<PyDict>> {
        let dict = PyDict::new_bound(py);
        for kv in &self.spectrum.additional_info {
            dict.set_item(&kv.key, &kv.value)?;
        }
        Ok(dict.into())
    }

    /// 设置额外信息
    #[setter]
    fn set_additional_info(&mut self, info: &PyDict) -> PyResult<()> {
        self.spectrum.clear_additional_info();
        for (key, value) in info.iter() {
            let key_str = key.extract::<String>()?;
            let value_str = value.extract::<String>()?;
            self.spectrum.add_additional_info(key_str, value_str).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
            })?;
        }
        Ok(())
    }

    /// 添加质谱峰
    fn add_peak(&mut self, mz: f64, intensity: f64) -> PyResult<()> {
        self.spectrum.add_peak(mz, intensity).map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
        })
    }

    /// 清除所有质谱峰
    fn clear_peaks(&mut self) {
        self.spectrum.clear_peaks();
    }

    /// 按m/z排序质谱峰
    fn sort_peaks(&mut self) {
        self.spectrum.sort_peaks();
    }

    /// 设置前体离子信息
    #[pyo3(signature = (ref_scan_number=None, mz=None, charge=None, activation_method=None, activation_energy=None, isolation_window=None))]
    fn set_precursor(&mut self, ref_scan_number: Option<u32>, mz: Option<f64>, 
                    charge: Option<i8>, activation_method: Option<String>,
                    activation_energy: Option<f64>, isolation_window: Option<(f64, f64)>) -> PyResult<()> {
        let mut precursor = if let Some(existing) = &self.spectrum.precursor {
            **existing.clone()
        } else {
            PrecursorInfo::default()
        };

        if let Some(val) = ref_scan_number { precursor.ref_scan_number = val; }
        if let Some(val) = mz { precursor.mz = val; }
        if let Some(val) = charge { precursor.charge = val; }
        if let Some(val) = activation_method { precursor.activation_method = val; }
        if let Some(val) = activation_energy { precursor.activation_energy = val; }
        if let Some(val) = isolation_window { precursor.isolation_window = val; }

        self.spectrum.set_precursor(precursor);
        Ok(())
    }

    /// 设置扫描信息
    #[pyo3(signature = (scan_number=None, retention_time=None, drift_time=None, scan_window=None))]
    fn set_scan(&mut self, scan_number: Option<u32>, retention_time: Option<f64>,
               drift_time: Option<f64>, scan_window: Option<(f64, f64)>) -> PyResult<()> {
        if let Some(val) = scan_number { self.spectrum.set_scan_number(val); }
        if let Some(val) = retention_time { 
            self.spectrum.set_retention_time(val).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
            })?;
        }
        if let Some(val) = drift_time { 
            self.spectrum.set_drift_time(val).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
            })?;
        }
        if let Some(val) = scan_window { self.spectrum.scan.scan_window = val; }
        Ok(())
    }

    /// 添加额外信息项
    fn add_additional_info_item(&mut self, key: String, value: String) -> PyResult<()> {
        self.spectrum.add_additional_info(key, value).map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
        })
    }

    /// 清除额外信息
    fn clear_additional_info(&mut self) {
        self.spectrum.clear_additional_info();
    }

    /// 获取质谱峰数量
    fn peak_count(&self) -> usize {
        self.spectrum.peak_count()
    }

    /// 获取总离子流
    fn total_ion_current(&self) -> f64 {
        self.spectrum.total_ion_current()
    }

    /// 获取基峰
    fn base_peak(&self, py: Python) -> PyResult<Py<PyAny>> {
        if let Some((mz, intensity)) = self.spectrum.base_peak() {
            Ok((mz, intensity).into_py(py))
        } else {
            Ok(py.None())
        }
    }

    /// 获取m/z范围
    fn mz_range(&self, py: Python) -> PyResult<Py<PyAny>> {
        if let Some(range) = self.spectrum.mz_range() {
            Ok((range.start, range.end).into_py(py))
        } else {
            Ok(py.None())
        }
    }

    /// 验证质谱数据
    fn validate(&self) -> PyResult<()> {
        self.spectrum.validate().map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string())
        })
    }

    /// 检查是否为MS1谱图
    fn is_ms1(&self) -> bool {
        self.spectrum.is_ms1()
    }

    /// 检查是否为MS2谱图
    fn is_ms2(&self) -> bool {
        self.spectrum.is_ms2()
    }

    /// 检查是否有前体离子信息
    fn has_precursor(&self) -> bool {
        self.spectrum.has_precursor()
    }

    /// 字符串表示
    fn __repr__(&self) -> String {
        format!("MSObject(level={}, peaks={}, scan_number={})", 
                self.spectrum.level, 
                self.spectrum.peak_count(),
                self.spectrum.scan.scan_number)
    }

    /// 字符串表示
    fn __str__(&self) -> String {
        self.__repr__()
    }
}

#[cfg(feature = "python")]
#[pymethods]
impl Precursor {
    #[new]
    #[pyo3(signature = (mz=0.0, charge=0, ref_scan_number=0, isolation_window=None, activation_method="unknown", activation_energy=0.0))]
    fn new(
        mz: f64,
        charge: i8,
        ref_scan_number: u32,
        isolation_window: Option<(f64, f64)>,
        activation_method: String,
        activation_energy: f64,
    ) -> Self {
        Self {
            precursor: PrecursorInfo {
                ref_scan_number,
                mz,
                charge,
                activation_method,
                activation_energy,
                isolation_window: isolation_window.unwrap_or((0.0, 0.0)),
            },
        }
    }

    #[getter]
    fn mz(&self) -> f64 {
        self.precursor.mz
    }

    #[setter]
    fn set_mz(&mut self, mz: f64) {
        self.precursor.mz = mz;
    }

    #[getter]
    fn charge(&self) -> i8 {
        self.precursor.charge
    }

    #[setter]
    fn set_charge(&mut self, charge: i8) {
        self.precursor.charge = charge;
    }

    #[getter]
    fn ref_scan_number(&self) -> u32 {
        self.precursor.ref_scan_number
    }

    #[setter]
    fn set_ref_scan_number(&mut self, ref_scan_number: u32) {
        self.precursor.ref_scan_number = ref_scan_number;
    }

    #[getter]
    fn activation_method(&self) -> &str {
        &self.precursor.activation_method
    }

    #[setter]
    fn set_activation_method(&mut self, activation_method: String) {
        self.precursor.activation_method = activation_method;
    }

    #[getter]
    fn activation_energy(&self) -> f64 {
        self.precursor.activation_energy
    }

    #[setter]
    fn set_activation_energy(&mut self, activation_energy: f64) {
        self.precursor.activation_energy = activation_energy;
    }

    #[getter]
    fn isolation_window(&self) -> (f64, f64) {
        self.precursor.isolation_window
    }

    #[setter]
    fn set_isolation_window(&mut self, isolation_window: (f64, f64)) {
        self.precursor.isolation_window = isolation_window;
    }

    fn __repr__(&self) -> String {
        format!("Precursor(mz={}, charge={})", self.precursor.mz, self.precursor.charge)
    }
}

#[cfg(feature = "python")]
#[pymethods]
impl Scan {
    #[new]
    #[pyo3(signature = (scan_number=0, retention_time=0.0, drift_time=0.0, scan_window=None, additional_info=None))]
    fn new(
        py: Python,
        scan_number: u32,
        retention_time: f64,
        drift_time: f64,
        scan_window: Option<(f64, f64)>,
        additional_info: Option<&PyDict>,
    ) -> PyResult<Self> {
        let mut additional_info_vec = SmallKeyValueList::new();
        if let Some(info_dict) = additional_info {
            for (key, value) in info_dict.iter() {
                let key_str = key.extract::<String>()?;
                let value_str = value.extract::<String>()?;
                additional_info_vec.push(KeyValue::new(key_str, value_str));
            }
        }

        Ok(Self {
            scan: ScanInfo {
                scan_number,
                retention_time,
                drift_time,
                scan_window: scan_window.unwrap_or((0.0, 0.0)),
                additional_info: additional_info_vec,
            },
        })
    }

    #[getter]
    fn scan_number(&self) -> u32 {
        self.scan.scan_number
    }

    #[setter]
    fn set_scan_number(&mut self, scan_number: u32) {
        self.scan.scan_number = scan_number;
    }

    #[getter]
    fn retention_time(&self) -> f64 {
        self.scan.retention_time
    }

    #[setter]
    fn set_retention_time(&mut self, retention_time: f64) -> PyResult<()> {
        if retention_time < 0.0 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Retention time must be non-negative"
            ));
        }
        self.scan.retention_time = retention_time;
        Ok(())
    }

    #[getter]
    fn drift_time(&self) -> f64 {
        self.scan.drift_time
    }

    #[setter]
    fn set_drift_time(&mut self, drift_time: f64) -> PyResult<()> {
        if drift_time < 0.0 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Drift time must be non-negative"
            ));
        }
        self.scan.drift_time = drift_time;
        Ok(())
    }

    #[getter]
    fn scan_window(&self) -> (f64, f64) {
        self.scan.scan_window
    }

    #[setter]
    fn set_scan_window(&mut self, scan_window: (f64, f64)) {
        self.scan.scan_window = scan_window;
    }

    #[getter]
    fn additional_info(&self, py: Python) -> PyResult<Py<PyDict>> {
        let dict = PyDict::new(py);
        for kv in &self.scan.additional_info {
            dict.set_item(&kv.key, &kv.value)?;
        }
        Ok(dict.into())
    }

    fn __repr__(&self) -> String {
        format!("Scan(scan_number={}, retention_time={})", 
                self.scan.scan_number, self.scan.retention_time)
    }
}

#[cfg(feature = "python")]
#[pymethods]
impl KeyValue {
    #[new]
    fn new(key: String, value: String) -> Self {
        Self { key, value }
    }

    #[setter]
    fn set_key(&mut self, key: String) {
        self.key = key;
    }

    #[setter]
    fn set_value(&mut self, value: String) {
        self.value = value;
    }

    fn __repr__(&self) -> String {
        format!("KeyValue(key={}, value={})", self.key, self.value)
    }
}

/// 从Python对象解析前体离子信息
fn parse_precursor_from_python(prec_obj: &PyAny) -> PyResult<PrecursorInfo> {
    let mut precursor = PrecursorInfo::default();

    // 尝试获取各个属性
    if let Ok(mz) = prec_obj.getattr("mz") {
        precursor.mz = mz.extract()?;
    }
    if let Ok(charge) = prec_obj.getattr("charge") {
        precursor.charge = charge.extract()?;
    }
    if let Ok(ref_scan_number) = prec_obj.getattr("ref_scan_number") {
        precursor.ref_scan_number = ref_scan_number.extract()?;
    }
    if let Ok(activation_method) = prec_obj.getattr("activation_method") {
        precursor.activation_method = activation_method.extract()?;
    }
    if let Ok(activation_energy) = prec_obj.getattr("activation_energy") {
        precursor.activation_energy = activation_energy.extract()?;
    }
    if let Ok(isolation_window) = prec_obj.getattr("isolation_window") {
        precursor.isolation_window = isolation_window.extract()?;
    }

    Ok(precursor)
}

/// 从Python对象解析扫描信息
fn parse_scan_from_python(scan_obj: &PyAny) -> PyResult<ScanInfo> {
    let mut scan = ScanInfo::default();

    // 尝试获取各个属性
    if let Ok(scan_number) = scan_obj.getattr("scan_number") {
        scan.scan_number = scan_number.extract()?;
    }
    if let Ok(retention_time) = scan_obj.getattr("retention_time") {
        scan.retention_time = retention_time.extract()?;
    }
    if let Ok(drift_time) = scan_obj.getattr("drift_time") {
        scan.drift_time = drift_time.extract()?;
    }
    if let Ok(scan_window) = scan_obj.getattr("scan_window") {
        scan.scan_window = scan_window.extract()?;
    }

    // 处理additional_info
    if let Ok(additional_info) = scan_obj.getattr("additional_info") {
        if let Ok(info_dict) = additional_info.downcast::<PyDict>() {
            for (key, value) in info_dict.iter() {
                let key_str = key.extract::<String>()?;
                let value_str = value.extract::<String>()?;
                scan.additional_info.push(KeyValue::new(key_str, value_str));
            }
        }
    }

    Ok(scan)
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::Python;

    #[test]
    fn test_msobject_creation() {
        Python::with_gil(|py| {
            let ms_obj = MSObject::new(py, 1, None, None, None, None).unwrap();
            assert_eq!(ms_obj.level(), 1);
            assert_eq!(ms_obj.peak_count(), 0);
        });
    }

    #[test]
    fn test_msobject_with_peaks() {
        Python::with_gil(|py| {
            let peaks = PyList::new(py, vec![(100.0, 1000.0), (200.0, 2000.0)]);
            let ms_obj = MSObject::new(py, 1, Some(peaks), None, None, None).unwrap();
            assert_eq!(ms_obj.peak_count(), 2);
            assert_eq!(ms_obj.total_ion_current(), 3000.0);
        });
    }

    #[test]
    fn test_precursor_creation() {
        let precursor = Precursor::new(500.0, 2, 1000, None, "CID".to_string(), 35.0);
        assert_eq!(precursor.mz(), 500.0);
        assert_eq!(precursor.charge(), 2);
        assert_eq!(precursor.ref_scan_number(), 1000);
    }

    #[test]
    fn test_scan_creation() {
        Python::with_gil(|py| {
            let scan = Scan::new(py, 100, 10.5, 0.1, None, None).unwrap();
            assert_eq!(scan.scan_number(), 100);
            assert_eq!(scan.retention_time(), 10.5);
            assert_eq!(scan.drift_time(), 0.1);
        });
    }
}
