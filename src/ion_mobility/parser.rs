//! 离子迁移率解析
//!
//! 提供离子迁移率数据解析和处理功能

use crate::core::{Spectrum, CoreResult};
use crate::core::types::*;
use crate::ion_mobility::merger::merge_peaks_by_mz_internal;
use std::collections::HashMap;

#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use pyo3::types::{PyDict, PyList, PyTuple, PyAny};

/// Python兼容的离子迁移率工具
#[cfg(feature = "python")]
#[pyclass]
pub struct IonMobilityUtils;

#[cfg(feature = "python")]
#[pymethods]
impl IonMobilityUtils {
    /// 解析离子迁移率数据
    #[staticmethod]
    #[pyo3(signature = (ms_object_list, rt_range=None, mz_tolerance=10, rt_tolerance=None))]
    fn parse_ion_mobility(py: Python, ms_object_list: Vec<&PyAny>, rt_range: Option<(f64, f64)>,
                         mz_tolerance: f64, rt_tolerance: Option<f64>) -> PyResult<Py<PyDict>> {
        // 解析MSObject列表
        let mut spectra = Vec::new();
        for py_ms_object in ms_object_list {
            let ms_object = py_ms_object.extract::<crate::core::ms_object::MSObject>()?;
            spectra.push(ms_object.spectrum);
        }

        // 调用内部解析函数
        let ion_mobility_data = parse_ion_mobility_internal(spectra, rt_range, mz_tolerance, rt_tolerance)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

        // 转换为Python字典
        let result_dict = PyDict::new(py);
        for (drift_time_ms, peaks) in ion_mobility_data {
            let py_peaks = PyList::empty(py);
            for (mz, intensity) in peaks {
                py_peaks.append((mz, intensity))?;
            }
            let drift_time = drift_time_ms as f64 / 1000.0; // 转换回秒
            result_dict.set_item(drift_time, py_peaks)?;
        }

        Ok(result_dict.into())
    }

    /// 根据m/z容差合并峰
    #[staticmethod]
    fn merge_peaks_by_mz(py: Python, peaks: Vec<&PyAny>, mz_tolerance: f64) -> PyResult<Py<PyList>> {
        // 解析峰列表
        let mut peak_data = Vec::new();
        for py_peak in peaks {
            let tuple = py_peak.downcast::<PyTuple>()?;
            let mz = tuple.get_item(0)?.extract::<f64>()?;
            let intensity = tuple.get_item(1)?.extract::<f64>()?;
            peak_data.push((mz, intensity));
        }

        // 合并峰
        let merged_peaks = merge_peaks_by_mz_internal(peak_data, mz_tolerance);

        // 转换为Python列表
        let py_results = PyList::empty(py);
        for (mz, intensity) in merged_peaks {
            py_results.append((mz, intensity))?;
        }

        Ok(py_results.into())
    }

    /// 计算离子迁移率校准曲线
    #[staticmethod]
    fn calculate_calibration_curve(py: Python, calibration_points: &PyList) -> PyResult<Py<PyAny>> {
        let mut points = Vec::new();
        for point in calibration_points.iter() {
            let tuple = point.downcast::<PyTuple>()?;
            let known_mz = tuple.get_item(0)?.extract::<f64>()?;
            let drift_time = tuple.get_item(1)?.extract::<f64>()?;
            points.push((known_mz, drift_time));
        }

        if points.len() < 2 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "At least 2 calibration points are required"
            ));
        }

        // 简单线性校准 (实际中可能需要更复杂的模型)
        let calibration = calculate_linear_calibration(&points);

        // 返回校准参数
        Ok((calibration.slope, calibration.intercept).into_py(py))
    }

    /// 应用校准曲线
    #[staticmethod]
    fn apply_calibration(py: Python, drift_times: &PyList, slope: f64, intercept: f64) -> PyResult<Py<PyList>> {
        let mut calibrated_mz = Vec::new();
        for dt in drift_times.iter() {
            let drift_time = dt.extract::<f64>()?;
            let mz = slope * drift_time + intercept;
            calibrated_mz.push(mz);
        }

        let py_results = PyList::empty(py);
        for mz in calibrated_mz {
            py_results.append(mz)?;
        }

        Ok(py_results.into())
    }

    /// 分析离子迁移率分布
    #[staticmethod]
    fn analyze_mobility_distribution(py: Python, mobility_data: &PyDict) -> PyResult<Py<PyDict>> {
        let mut drift_times = Vec::new();
        let mut peak_counts = Vec::new();

        for (key, value) in mobility_data.iter() {
            let drift_time = key.extract::<f64>()?;
            let peaks = value.downcast::<PyList>()?;
            let peak_count = peaks.len();

            drift_times.push(drift_time);
            peak_counts.push(peak_count);
        }

        if drift_times.is_empty() {
            return Ok(PyDict::new(py).into());
        }

        // 计算统计指标
        let total_peaks: usize = peak_counts.iter().sum();
        let avg_peaks = total_peaks as f64 / peak_counts.len() as f64;
        let max_peaks = peak_counts.iter().max().unwrap_or(&0);
        let min_peaks = peak_counts.iter().min().unwrap_or(&0);

        // 找到峰最多的漂移时间
        let max_idx = peak_counts.iter()
            .position(|&count| count == *max_peaks)
            .unwrap_or(0);
        let optimal_drift_time = drift_times[max_idx];

        // 创建结果字典
        let result_dict = PyDict::new(py);
        result_dict.set_item("total_peaks", total_peaks)?;
        result_dict.set_item("avg_peaks_per_drift_time", avg_peaks)?;
        result_dict.set_item("max_peaks", *max_peaks)?;
        result_dict.set_item("min_peaks", *min_peaks)?;
        result_dict.set_item("optimal_drift_time", optimal_drift_time)?;
        result_dict.set_item("drift_time_range",
            (drift_times.iter().fold(f64::INFINITY, |a, &b| a.min(b)),
             drift_times.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b))))?;

        Ok(result_dict.into())
    }
}

/// 内部解析函数
pub fn parse_ion_mobility_internal(
    spectra: Vec<Spectrum>,
    rt_range: Option<(f64, f64)>,
    mz_tolerance: f64,
    rt_tolerance: Option<f64>,
) -> CoreResult<HashMap<i32, Vec<Peak>>> {
    let mut mobility_data = HashMap::new();

    for spectrum in spectra {
        // 检查是否有漂移时间信息
        if spectrum.scan.drift_time <= 0.0 {
            continue;
        }

        // 检查保留时间范围
        if let Some((rt_start, rt_end)) = rt_range {
            let rt = spectrum.scan.retention_time;
            if rt < rt_start || rt > rt_end {
                continue;
            }
        }

        let drift_time = spectrum.scan.drift_time;
        let drift_time_ms = (drift_time * 1000.0) as i32; // 转换为毫秒作为整数key

        // 检查保留时间容差（如果指定）
        if let Some(rt_tol) = rt_tolerance {
            let should_include = mobility_data
                .keys()
                .any(|&existing_dt| {
                    let existing_rt = get_rt_for_drift_time(&mobility_data, existing_dt);
                    (existing_rt - spectrum.scan.retention_time).abs() <= rt_tol
                });

            if !should_include && !mobility_data.is_empty() {
                continue;
            }
        }

        // 获取或创建该漂移时间的峰列表
        let peaks = mobility_data.entry(drift_time_ms).or_insert_with(Vec::new);

        // 添加当前谱图的峰
        for &(mz, intensity) in &spectrum.peaks {
            // 检查是否与现有峰过于接近（避免重复）
            let should_add = peaks.iter().all(|&(existing_mz, _)| {
                (existing_mz - mz).abs() > mz_tolerance
            });

            if should_add {
                peaks.push((mz, intensity));
            }
        }
    }

    // 对每个漂移时间的峰进行合并和排序
    for (_, peaks) in mobility_data.iter_mut() {
        // 使用SIMD加速合并相近的峰
        *peaks = merge_peaks_by_mz_internal(peaks.clone(), mz_tolerance);

        // 按m/z排序
        peaks.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
    }

    Ok(mobility_data)
}

/// 获取漂移时间对应的保留时间（简化实现）
fn get_rt_for_drift_time(mobility_data: &HashMap<i32, Vec<Peak>>, drift_time_ms: i32) -> f64 {
    // 这是一个简化的实现，实际中可能需要更复杂的映射
    drift_time_ms as f64 / 1000.0 // 简化：使用漂移时间作为保留时间的代理
}

/// 线性校准参数
#[derive(Debug, Clone)]
pub struct CalibrationCurve {
    pub slope: f64,
    pub intercept: f64,
    pub r_squared: f64,
}

/// 计算线性校准曲线
pub fn calculate_linear_calibration(points: &[(f64, f64)]) -> CalibrationCurve {
    if points.len() < 2 {
        return CalibrationCurve {
            slope: 0.0,
            intercept: 0.0,
            r_squared: 0.0,
        };
    }

    // 计算线性回归参数
    let n = points.len() as f64;
    let sum_x: f64 = points.iter().map(|(_, x)| *x).sum();
    let sum_y: f64 = points.iter().map(|(y, _)| *y).sum();
    let sum_xy: f64 = points.iter().map(|(y, x)| y * x).sum();
    let sum_x2: f64 = points.iter().map(|(_, x)| x * x).sum();

    let slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x);
    let intercept = (sum_y - slope * sum_x) / n;

    // 计算R²
    let mean_y = sum_y / n;
    let ss_tot: f64 = points.iter().map(|(y, _)| (y - mean_y).powi(2)).sum();
    let ss_res: f64 = points.iter()
        .map(|(y, x)| {
            let predicted = slope * x + intercept;
            (y - predicted).powi(2)
        })
        .sum();

    let r_squared = if ss_tot > 0.0 { 1.0 - (ss_res / ss_tot) } else { 0.0 };

    CalibrationCurve {
        slope,
        intercept,
        r_squared,
    }
}

/// 离子迁移率分析器
pub struct IonMobilityAnalyzer {
    mobility_data: HashMap<i32, Vec<Peak>>,
    calibration: Option<CalibrationCurve>,
}

impl IonMobilityAnalyzer {
    /// 创建新的离子迁移率分析器
    pub fn new(spectra: Vec<Spectrum>) -> CoreResult<Self> {
        let mobility_data = parse_ion_mobility_internal(spectra, None, 10.0, None)?;
        Ok(Self {
            mobility_data,
            calibration: None,
        })
    }

    /// 设置校准曲线
    pub fn set_calibration(&mut self, calibration: CalibrationCurve) {
        self.calibration = Some(calibration);
    }

    /// 获取漂移时间范围
    pub fn get_drift_time_range(&self) -> Option<(f64, f64)> {
        if self.mobility_data.is_empty() {
            return None;
        }

        let min_dt_ms = self.mobility_data.keys().min().unwrap_or(&0);
        let max_dt_ms = self.mobility_data.keys().max().unwrap_or(&0);
        Some(((*min_dt_ms as f64) / 1000.0, (*max_dt_ms as f64) / 1000.0))
    }

    /// 获取指定漂移时间的谱图
    pub fn get_spectrum_at_drift_time(&self, drift_time: f64, tolerance: f64) -> Option<Vec<Peak>> {
        let target_dt_ms = (drift_time * 1000.0) as i32;
        let tolerance_ms = (tolerance * 1000.0) as i32;

        for (&dt_ms, peaks) in &self.mobility_data {
            if (dt_ms - target_dt_ms).abs() <= tolerance_ms {
                return Some(peaks.clone());
            }
        }
        None
    }

    /// 计算离子迁移率谱图的总离子流
    pub fn calculate_total_ion_current(&self) -> std::collections::HashMap<i32, f64> {
        let mut tic_map = std::collections::HashMap::new();
        for (&drift_time_ms, peaks) in &self.mobility_data {
            let tic = peaks.iter().map(|(_, intensity)| *intensity).sum();
            tic_map.insert(drift_time_ms, tic);
        }
        tic_map
    }

    /// 寻找最佳漂移时间（基于总离子流）
    pub fn find_optimal_drift_time(&self) -> Option<(f64, f64)> {
        let tic_map = self.calculate_total_ion_current();
        if tic_map.is_empty() {
            return None;
        }

        let (optimal_ms, max_tic) = tic_map.iter()
            .max_by(|a, b| a.1.partial_cmp(b.1).unwrap())
            .map(|(&ms, &tic)| (ms as f64 / 1000.0, tic))?; // 转换回秒

        Some((optimal_ms, max_tic))
    }

    /// 提取离子迁移率色谱图
    pub fn extract_mobility_chromatogram(&self, target_mz: f64, tolerance: f64) -> Vec<(f64, f64)> {
        let mut chromatogram = Vec::new();

        for (&drift_time_ms, peaks) in &self.mobility_data {
            // 搜索匹配的峰
            let matching_indices = crate::utils::helpers::find_peaks_in_tolerance(peaks, target_mz, tolerance);

            if !matching_indices.is_empty() {
                // 计算总强度
                let total_intensity: f64 = matching_indices
                    .iter()
                    .map(|&idx| peaks[idx].1)
                    .sum();

                chromatogram.push((drift_time_ms as f64 / 1000.0, total_intensity));
            }
        }

        // 按漂移时间排序
        chromatogram.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
        chromatogram
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::spectrum::Spectrum;

    #[test]
    fn test_ion_mobility_parsing() {
        let mut spectrum = Spectrum::ms1().unwrap();
        spectrum.set_retention_time(10.0).unwrap();
        spectrum.set_drift_time(5.0).unwrap();
        spectrum.add_peak(100.0, 1000.0).unwrap();
        spectrum.add_peak(200.0, 2000.0).unwrap();

        let result = parse_ion_mobility_internal(vec![spectrum], None, 10.0, None).unwrap();
        assert_eq!(result.len(), 1);
        assert!(result.contains_key(&5.0));
        assert_eq!(result[&5.0].len(), 2);
    }

    #[test]
    fn test_calibration_curve() {
        let points = vec![(100.0, 5.0), (200.0, 10.0), (300.0, 15.0)];
        let calibration = calculate_linear_calibration(&points);

        assert!(calibration.slope > 0.0);
        assert!(calibration.r_squared > 0.9); // 应该是很好的线性关系
    }

    #[test]
    fn test_ion_mobility_analyzer() {
        let mut spectrum1 = Spectrum::ms1().unwrap();
        spectrum1.set_drift_time(5.0).unwrap();
        spectrum1.add_peak(100.0, 1000.0).unwrap();

        let mut spectrum2 = Spectrum::ms1().unwrap();
        spectrum2.set_drift_time(10.0).unwrap();
        spectrum2.add_peak(100.0, 2000.0).unwrap();

        let analyzer = IonMobilityAnalyzer::new(vec![spectrum1, spectrum2]).unwrap();
        let optimal = analyzer.find_optimal_drift_time();

        assert!(optimal.is_some());
        assert_eq!(optimal.unwrap().0, 10.0); // 应该选择强度更高的漂移时间
    }
}
