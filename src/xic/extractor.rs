//! XIC提取器
//!
//! 提供高性能的XIC（提取离子色谱图）提取功能

use crate::core::{Spectrum, BinnedSpectraIndex, CoreResult};
use crate::core::types::*;
use crate::utils::helpers::*;
use crate::xic::result::{XICResult, PolymerInfo, FragmentIon};

#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use pyo3::types::PyAny;

/// XIC提取器
#[cfg(feature = "python")]
#[pyclass]
pub struct XICSExtractor {
    /// MS1谱图数据
    ms1_spectra: Vec<Spectrum>,
    /// MS2谱图数据
    ms2_spectra: Vec<Spectrum>,
    /// MS1谱图索引用于快速搜索
    ms1_index: BinnedSpectraIndex,
    /// MS2谱图索引用于快速搜索
    ms2_index: BinnedSpectraIndex,
    /// PPM容差
    ppm_tolerance: f64,
    /// 是否已加载数据
    loaded: bool,
}

impl XICSExtractor {
    /// 创建新的XIC提取器
    pub fn new(ppm_tolerance: f64) -> Self {
        Self {
            ms1_spectra: Vec::new(),
            ms2_spectra: Vec::new(),
            ms1_index: BinnedSpectraIndex::empty(),
            ms2_index: BinnedSpectraIndex::empty(),
            ppm_tolerance,
            loaded: false,
        }
    }

    /// 从谱图列表创建XIC提取器
    pub fn from_spectra(spectra: Vec<Spectrum>, ppm_tolerance: f64, bin_size: f64) -> CoreResult<Self> {
        let mut ms1_spectra = Vec::new();
        let mut ms2_spectra = Vec::new();

        // 分类谱图
        for spectrum in spectra {
            match spectrum.level {
                1 => ms1_spectra.push(spectrum),
                2 => ms2_spectra.push(spectrum),
                _ => {} // 忽略其他级别
            }
        }

        // 创建索引
        let ms1_index = BinnedSpectraIndex::new(ms1_spectra.clone(), bin_size)?;
        let ms2_index = BinnedSpectraIndex::new(ms2_spectra.clone(), bin_size)?;

        Ok(Self {
            ms1_spectra,
            ms2_spectra,
            ms1_index,
            ms2_index,
            ppm_tolerance,
            loaded: true,
        })
    }

    /// 加载谱图数据
    pub fn load_spectra(&mut self, spectra: Vec<Spectrum>, bin_size: f64) -> CoreResult<()> {
        let mut ms1_spectra = Vec::new();
        let mut ms2_spectra = Vec::new();

        // 分类谱图
        for spectrum in spectra {
            match spectrum.level {
                1 => ms1_spectra.push(spectrum),
                2 => ms2_spectra.push(spectrum),
                _ => {}
            }
        }

        // 创建索引
        self.ms1_index = BinnedSpectraIndex::new(ms1_spectra.clone(), bin_size)?;
        self.ms2_index = BinnedSpectraIndex::new(ms2_spectra.clone(), bin_size)?;

        self.ms1_spectra = ms1_spectra;
        self.ms2_spectra = ms2_spectra;
        self.loaded = true;

        Ok(())
    }

    /// 提取前体离子XIC
    pub fn extract_precursor_xics(&self, precursor: &PolymerInfo, num_isotopes: usize) -> CoreResult<Vec<XICResult>> {
        if !self.loaded {
            return Err(CoreError::EmptyPeakList); // 使用现有错误类型
        }

        let mut results = Vec::new();

        // 提取前体离子XIC
        let precursor_result = self.extract_single_xic(
            precursor.mz,
            precursor.charge,
            &precursor.sequence,
            precursor.rt_start,
            precursor.rt_stop,
        )?;
        results.push(precursor_result);

        // 提取同位素峰XIC
        for isotope in 1..num_isotopes {
            let isotope_mz = precursor.mz + (isotope as f64) / precursor.charge as f64;
            let isotope_result = self.extract_single_xic(
                isotope_mz,
                precursor.charge,
                &format!("{}[{}+{}]", precursor.sequence, isotope, precursor.charge),
                precursor.rt_start,
                precursor.rt_stop,
            )?;
            results.push(isotope_result);
        }

        Ok(results)
    }

    /// 提取碎片离子XIC
    pub fn extract_fragment_xics(&self, peptide_info: &PolymerInfo) -> CoreResult<Vec<XICResult>> {
        if !self.loaded {
            return Err(CoreError::EmptyPeakList);
        }

        let mut results = Vec::new();

        for fragment_ion in &peptide_info.fragment_ions {
            let result = self.extract_single_xic(
                fragment_ion.mz,
                fragment_ion.charge,
                &fragment_ion.ion_type,
                peptide_info.rt_start,
                peptide_info.rt_stop,
            )?;
            results.push(result);
        }

        Ok(results)
    }

    /// 提取单个XIC
    pub fn extract_single_xic(&self, mz: f64, charge: i8, ion_type: &str, rt_start: f64, rt_end: f64) -> CoreResult<XICResult> {
        if !self.loaded {
            return Err(CoreError::EmptyPeakList);
        }

        let tolerance = mz * self.ppm_tolerance * 1e-6;
        let mz_range = (mz - tolerance, mz + tolerance);

        // 提取MS1谱图数据
        let mut rt_array = Vec::new();
        let mut intensity_array = Vec::new();

        for spectrum in &self.ms1_spectra {
            let rt = spectrum.scan.retention_time;

            // 检查保留时间范围
            if rt < rt_start || rt > rt_end {
                continue;
            }

            // 搜索匹配的峰
            let matching_indices = find_peaks_in_tolerance(&spectrum.peaks, mz, tolerance);

            if !matching_indices.is_empty() {
                rt_array.push(rt);

                // 计算总强度
                let total_intensity: f64 = matching_indices
                    .iter()
                    .map(|&idx| spectrum.peaks[idx].1)
                    .sum();

                intensity_array.push(total_intensity);
            }
        }

        // 计算PPM误差
        let ppm_error = if !rt_array.is_empty() {
            // 简化计算，实际中可能需要更复杂的计算
            self.ppm_tolerance
        } else {
            0.0
        };

        Ok(XICResult {
            rt_array,
            intensity_array,
            mz,
            ppm_error,
            ion_type: ion_type.to_string(),
            charge,
        })
    }

    /// 批量提取XIC
    pub fn extract_batch_xics(&self, targets: &[(f64, i8, &str)], rt_start: f64, rt_end: f64) -> CoreResult<Vec<XICResult>> {
        let mut results = Vec::new();

        for &(mz, charge, ion_type) in targets {
            let result = self.extract_single_xic(mz, charge, ion_type, rt_start, rt_end)?;
            results.push(result);
        }

        Ok(results)
    }

    /// 按保留时间范围过滤谱图
    pub fn filter_spectra_by_rt(&self, spectra: &[Spectrum], rt_start: f64, rt_end: f64) -> Vec<&Spectrum> {
        spectra
            .iter()
            .filter(|spectrum| {
                let rt = spectrum.scan.retention_time;
                rt >= rt_start && rt <= rt_end
            })
            .collect()
    }

    /// 计算XIC质量评估指标
    pub fn evaluate_xic_quality(&self, xic: &XICResult) -> XICQualityMetrics {
        if xic.rt_array.is_empty() {
            return XICQualityMetrics::default();
        }

        let points = xic.rt_array.len();
        let max_intensity = xic.intensity_array.iter().fold(0.0, |a, &b| a.max(b));
        let total_signal = xic.intensity_array.iter().sum::<f64>();
        let mean_intensity = total_signal / points as f64;

        // 计算信噪比（简化版本）
        let noise_threshold = mean_intensity * 0.1; // 假设噪声为平均强度的10%
        let signal_points = xic.intensity_array.iter().filter(|&&intensity| intensity > noise_threshold).count();
        let signal_to_noise = if noise_threshold > 0.0 { max_intensity / noise_threshold } else { 0.0 };

        // 计算峰对称性（简化版本）
        let peak_idx = xic.intensity_array.iter()
            .position(|&intensity| intensity == max_intensity)
            .unwrap_or(0);

        let left_area = xic.intensity_array[..peak_idx].iter().sum::<f64>();
        let right_area = xic.intensity_array[peak_idx..].iter().sum::<f64>();
        let symmetry = if (left_area + right_area) > 0.0 {
            2.0 * left_area.min(right_area) / (left_area + right_area)
        } else {
            0.0
        };

        XICQualityMetrics {
            points,
            max_intensity,
            mean_intensity,
            signal_to_noise,
            symmetry,
            signal_points,
            noise_points: points - signal_points,
        }
    }

    /// 获取MS1谱图数量
    pub fn ms1_count(&self) -> usize {
        self.ms1_spectra.len()
    }

    /// 获取MS2谱图数量
    pub fn ms2_count(&self) -> usize {
        self.ms2_spectra.len()
    }

    /// 检查是否已加载数据
    pub fn is_loaded(&self) -> bool {
        self.loaded
    }

    /// 获取PPM容差
    pub fn ppm_tolerance(&self) -> f64 {
        self.ppm_tolerance
    }

    /// 设置PPM容差
    pub fn set_ppm_tolerance(&mut self, ppm_tolerance: f64) {
        self.ppm_tolerance = ppm_tolerance;
    }
}

/// XIC质量评估指标
#[derive(Debug, Clone)]
pub struct XICQualityMetrics {
    /// 数据点数量
    pub points: usize,
    /// 最大强度
    pub max_intensity: f64,
    /// 平均强度
    pub mean_intensity: f64,
    /// 信噪比
    pub signal_to_noise: f64,
    /// 峰对称性 (0-1, 1表示完全对称)
    pub symmetry: f64,
    /// 信号点数量
    pub signal_points: usize,
    /// 噪声点数量
    pub noise_points: usize,
}

impl Default for XICQualityMetrics {
    fn default() -> Self {
        Self {
            points: 0,
            max_intensity: 0.0,
            mean_intensity: 0.0,
            signal_to_noise: 0.0,
            symmetry: 0.0,
            signal_points: 0,
            noise_points: 0,
        }
    }
}

impl PolymerInfo {
    /// 从Python对象创建PolymerInfo
    pub fn from_python(obj: &PyAny) -> PyResult<Self> {
        let sequence = obj.getattr("sequence")?.extract::<String>()?;
        let modified_sequence = obj.getattr("modified_sequence")?.extract::<String>()?;
        let charge = obj.getattr("charge")?.extract::<i8>()?;
        let mz = obj.getattr("mz")?.extract::<f64>()?;
        let rt = obj.getattr("rt")?.extract::<f64>()?;
        let rt_start = obj.getattr("rt_start")?.extract::<f64>()?;
        let rt_stop = obj.getattr("rt_stop")?.extract::<f64>()?;

        // 解析碎片离子
        let mut fragment_ions = Vec::new();
        if let Ok(fragment_list) = obj.getattr("fragment_ions") {
            if let Ok(fragment_iter) = fragment_list.iter() {
                for fragment in fragment_iter {
                    let ion_type = fragment.getattr("ion_type")?.extract::<String>()?;
                    let charge = fragment.getattr("charge")?.extract::<i8>()?;
                    let mz = fragment.getattr("mz")?.extract::<f64>()?;
                    fragment_ions.push(FragmentIon { ion_type, charge, mz });
                }
            }
        }

        Ok(PolymerInfo {
            sequence,
            modified_sequence,
            charge,
            mz,
            rt,
            rt_start,
            rt_stop,
            fragment_ions,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_xic_extractor_creation() {
        let extractor = XICSExtractor::new(10.0);
        assert_eq!(extractor.ppm_tolerance(), 10.0);
        assert!(!extractor.is_loaded());
    }

    #[test]
    fn test_xic_extraction() {
        let mut spectra = Vec::new();

        // 创建测试MS1谱图
        for i in 0..10 {
            let mut spectrum = Spectrum::ms1().unwrap();
            spectrum.set_scan_number(i as u32);
            spectrum.set_retention_time(i as f64 * 60.0).unwrap();

            // 添加测试峰
            spectrum.add_peak(500.0, 1000.0 * (i + 1) as f64).unwrap();
            spectrum.add_peak(501.0, 500.0 * (i + 1) as f64).unwrap();

            spectra.push(spectrum);
        }

        let extractor = XICSExtractor::from_spectra(spectra, 10.0, 1.0).unwrap();

        let result = extractor.extract_single_xic(500.0, 2, "test", 0.0, 600.0).unwrap();
        assert_eq!(result.rt_array.len(), 10);
        assert_eq!(result.mz, 500.0);
        assert_eq!(result.charge, 2);
    }

    #[test]
    fn test_xic_quality_metrics() {
        let xic = XICResult {
            rt_array: vec![1.0, 2.0, 3.0, 4.0, 5.0],
            intensity_array: vec![100.0, 200.0, 500.0, 200.0, 100.0],
            mz: 500.0,
            ppm_error: 5.0,
            ion_type: "test".to_string(),
            charge: 2,
        };

        let extractor = XICSExtractor::new(10.0);
        let metrics = extractor.evaluate_xic_quality(&xic);

        assert_eq!(metrics.points, 5);
        assert_eq!(metrics.max_intensity, 500.0);
        assert!(metrics.signal_to_noise > 0.0);
    }
}
