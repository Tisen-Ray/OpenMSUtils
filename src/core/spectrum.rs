//! 核心质谱数据结构
//! 
//! 这个模块定义了质谱数据处理的核心数据结构，包括：
//! - Spectrum: 核心质谱数据结构
//! - SpectrumBin: 用于索引的谱图bin
//! - BinnedSpectraIndex: 二进制索引结构

use crate::core::types::*;
use serde::{Deserialize, Serialize};
use std::ops::Range;

#[cfg(test)]
mod test_spectrum;

/// 前体离子信息
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PrecursorInfo {
    /// 参考扫描编号
    pub ref_scan_number: ScanNumber,
    /// 前体离子m/z
    pub mz: f64,
    /// 前体离子强度
    pub intensity: f64,
    /// 电荷状态
    pub charge: Charge,
    /// 激活方法
    pub activation_method: String,
    /// 激活能量
    pub activation_energy: f64,
    /// 分离窗口
    pub isolation_window: (f64, f64),
}

impl Default for PrecursorInfo {
    fn default() -> Self {
        Self {
            ref_scan_number: constants::DEFAULT_SCAN_NUMBER,
            mz: 0.0,
            intensity: 0.0,
            charge: constants::DEFAULT_CHARGE,
            activation_method: "unknown".to_string(),
            activation_energy: 0.0,
            isolation_window: (0.0, 0.0),
        }
    }
}

/// 扫描信息
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ScanInfo {
    /// 扫描编号
    pub scan_number: ScanNumber,
    /// 保留时间 (秒)
    pub retention_time: RetentionTime,
    /// 漂移时间 (秒)
    pub drift_time: DriftTime,
    /// 扫描窗口
    pub scan_window: (f64, f64),
    /// 额外信息
    pub additional_info: SmallKeyValueList,
}

impl Default for ScanInfo {
    fn default() -> Self {
        Self {
            scan_number: constants::DEFAULT_SCAN_NUMBER,
            retention_time: constants::DEFAULT_RETENTION_TIME,
            drift_time: constants::DEFAULT_DRIFT_TIME,
            scan_window: (0.0, 0.0),
            additional_info: SmallKeyValueList::new(),
        }
    }
}

/// 核心质谱数据结构
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Spectrum {
    /// 质谱峰数据 (m/z, intensity)
    pub peaks: PeakList,
    /// MS级别 (1, 2, 3...)
    pub level: MSLevel,
    /// 扫描信息
    pub scan: ScanInfo,
    /// 前体离子信息 (仅MS2+)
    pub precursor: Option<Box<PrecursorInfo>>,
    /// 额外信息
    pub additional_info: SmallKeyValueList,
}

impl Spectrum {
    /// 创建新的质谱对象
    pub fn new(level: MSLevel) -> CoreResult<Self> {
        if level < constants::MIN_MS_LEVEL || level > constants::MAX_MS_LEVEL {
            return Err(CoreError::InvalidMSLevel {
                level,
                min: constants::MIN_MS_LEVEL,
                max: constants::MAX_MS_LEVEL,
            });
        }

        Ok(Self {
            peaks: Vec::new(),
            level,
            scan: ScanInfo::default(),
            precursor: None,
            additional_info: SmallKeyValueList::new(),
        })
    }

    /// 创建MS1质谱
    pub fn ms1() -> CoreResult<Self> {
        Self::new(1)
    }

    /// 创建MS2质谱
    pub fn ms2() -> CoreResult<Self> {
        Self::new(2)
    }

    /// 添加质谱峰
    pub fn add_peak(&mut self, mz: f64, intensity: f64) -> CoreResult<()> {
        if mz < 0.0 || intensity < 0.0 {
            return Err(CoreError::InvalidPeakData { mz, intensity });
        }
        self.peaks.push((mz, intensity));
        Ok(())
    }

    /// 批量添加质谱峰
    pub fn add_peaks(&mut self, peaks: impl IntoIterator<Item = Peak>) -> CoreResult<()> {
        for (mz, intensity) in peaks {
            self.add_peak(mz, intensity)?;
        }
        Ok(())
    }

    /// 清除所有质谱峰
    pub fn clear_peaks(&mut self) {
        self.peaks.clear();
    }

    /// 按m/z排序质谱峰
    pub fn sort_peaks(&mut self) {
        self.peaks.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
    }

    /// 获取m/z范围
    pub fn mz_range(&self) -> Option<Range<f64>> {
        if self.peaks.is_empty() {
            return None;
        }

        let mut min_mz = f64::INFINITY;
        let mut max_mz = f64::NEG_INFINITY;

        for (mz, _) in &self.peaks {
            min_mz = min_mz.min(*mz);
            max_mz = max_mz.max(*mz);
        }

        Some(min_mz..max_mz)
    }

    /// 获取总离子流
    pub fn total_ion_current(&self) -> f64 {
        self.peaks.iter().map(|(_, intensity)| *intensity).sum()
    }

    /// 获取基峰
    pub fn base_peak(&self) -> Option<Peak> {
        self.peaks.iter()
            .max_by(|a, b| a.1.partial_cmp(&b.1).unwrap())
            .copied()
    }

    /// 设置前体离子信息
    pub fn set_precursor(&mut self, precursor: PrecursorInfo) {
        self.precursor = Some(Box::new(precursor));
    }

    /// 清除前体离子信息
    pub fn clear_precursor(&mut self) {
        self.precursor = None;
    }

    /// 设置扫描信息
    pub fn set_scan_info(&mut self, scan: ScanInfo) {
        self.scan = scan;
    }

    /// 设置扫描编号
    pub fn set_scan_number(&mut self, scan_number: ScanNumber) {
        self.scan.scan_number = scan_number;
    }

    /// 设置保留时间
    pub fn set_retention_time(&mut self, retention_time: RetentionTime) -> CoreResult<()> {
        if retention_time < 0.0 {
            return Err(CoreError::InvalidRetentionTime { rt: retention_time });
        }
        self.scan.retention_time = retention_time;
        Ok(())
    }

    /// 设置漂移时间
    pub fn set_drift_time(&mut self, drift_time: DriftTime) -> CoreResult<()> {
        if drift_time < 0.0 {
            return Err(CoreError::InvalidDriftTime { dt: drift_time });
        }
        self.scan.drift_time = drift_time;
        Ok(())
    }

    /// 添加额外信息
    pub fn add_additional_info(&mut self, key: impl Into<String>, value: impl Into<String>) -> CoreResult<()> {
        let key_str = key.into();
        
        // 检查是否已存在相同的key
        if self.additional_info.iter().any(|kv| kv.key == key_str) {
            return Err(CoreError::DuplicateKey { key: key_str });
        }

        self.additional_info.push(KeyValue::new(key_str, value));
        Ok(())
    }

    /// 获取额外信息
    pub fn get_additional_info(&self, key: &str) -> Option<&str> {
        self.additional_info.iter()
            .find(|kv| kv.key == key)
            .map(|kv| kv.value.as_str())
    }

    /// 清除额外信息
    pub fn clear_additional_info(&mut self) {
        self.additional_info.clear();
    }

    /// 验证质谱数据
    pub fn validate(&self) -> CoreResult<()> {
        if self.peaks.is_empty() {
            return Err(CoreError::EmptyPeakList);
        }

        for (mz, intensity) in &self.peaks {
            if *mz < 0.0 || *intensity < 0.0 {
                return Err(CoreError::InvalidPeakData { mz: *mz, intensity: *intensity });
            }
        }

        if self.level < constants::MIN_MS_LEVEL || self.level > constants::MAX_MS_LEVEL {
            return Err(CoreError::InvalidMSLevel {
                level: self.level,
                min: constants::MIN_MS_LEVEL,
                max: constants::MAX_MS_LEVEL,
            });
        }

        Ok(())
    }

    /// 获取质谱峰数量
    pub fn peak_count(&self) -> usize {
        self.peaks.len()
    }

    /// 检查是否为MS1谱图
    pub fn is_ms1(&self) -> bool {
        self.level == 1
    }

    /// 检查是否为MS2谱图
    pub fn is_ms2(&self) -> bool {
        self.level == 2
    }

    /// 检查是否有前体离子信息
    pub fn has_precursor(&self) -> bool {
        self.precursor.is_some()
    }
}

impl Default for Spectrum {
    fn default() -> Self {
        Self::new(1).unwrap()
    }
}

/// 用于索引的谱图bin
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpectrumBin {
    /// m/z范围
    pub mz_range: Range<f64>,
    /// 峰索引列表 (避免数据复制)
    pub peak_indices: Vec<usize>,
}

impl SpectrumBin {
    /// 创建新的bin
    pub fn new(mz_range: Range<f64>) -> Self {
        Self {
            mz_range,
            peak_indices: Vec::new(),
        }
    }

    /// 添加峰索引
    pub fn add_peak_index(&mut self, index: usize) {
        self.peak_indices.push(index);
    }

    /// 检查m/z值是否在bin范围内
    pub fn contains_mz(&self, mz: f64) -> bool {
        mz >= self.mz_range.start && mz < self.mz_range.end
    }

    /// 获取bin的中心m/z值
    pub fn center_mz(&self) -> f64 {
        (self.mz_range.start + self.mz_range.end) / 2.0
    }
}

/// 二进制谱图索引
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BinnedSpectraIndex {
    /// bin大小
    pub bin_size: f64,
    /// m/z范围
    pub mz_range: (f64, f64),
    /// bin数据
    pub bins: Vec<SpectrumBin>,
    /// 原始谱图数据引用
    pub spectra: Vec<Spectrum>,
}

impl BinnedSpectraIndex {
    /// 创建空的索引
    pub fn empty() -> Self {
        Self {
            bin_size: constants::DEFAULT_BIN_SIZE,
            mz_range: (0.0, 0.0),
            bins: Vec::new(),
            spectra: Vec::new(),
        }
    }

    /// 从谱图列表创建索引
    pub fn new(spectra: Vec<Spectrum>, bin_size: f64) -> CoreResult<Self> {
        if spectra.is_empty() {
            return Ok(Self::empty());
        }

        // 计算全局m/z范围
        let mut min_mz = f64::INFINITY;
        let mut max_mz = f64::NEG_INFINITY;

        for spectrum in &spectra {
            if let Some(range) = spectrum.mz_range() {
                min_mz = min_mz.min(range.start);
                max_mz = max_mz.max(range.end);
            }
        }

        if min_mz.is_infinite() || max_mz.is_infinite() {
            return Ok(Self::empty());
        }

        let mz_range = (min_mz, max_mz);
        let num_bins = ((max_mz - min_mz) / bin_size).ceil() as usize;

        // 创建bins
        let mut bins = Vec::with_capacity(num_bins);
        for i in 0..num_bins {
            let start = min_mz + (i as f64) * bin_size;
            let end = start + bin_size;
            bins.push(SpectrumBin::new(start..end));
        }

        // 填充bins
        for (spectrum_idx, spectrum) in spectra.iter().enumerate() {
            for (peak_idx, (mz, _)) in spectrum.peaks.iter().enumerate() {
                let bin_idx = ((*mz - min_mz) / bin_size) as usize;
                if bin_idx < bins.len() {
                    // 使用复合索引来唯一标识峰
                    let global_peak_index = spectrum_idx * spectrum.peaks.len() + peak_idx;
                    bins[bin_idx].add_peak_index(global_peak_index);
                }
            }
        }

        Ok(Self {
            bin_size,
            mz_range,
            bins,
            spectra,
        })
    }

    /// 搜索m/z范围内的峰
    pub fn search_range(&self, mz_range: (f64, f64)) -> CoreResult<Vec<Peak>> {
        let mut results = Vec::new();

        let start_bin = ((mz_range.0 - self.mz_range.0) / self.bin_size).floor() as isize;
        let end_bin = ((mz_range.1 - self.mz_range.0) / self.bin_size).ceil() as isize;

        let start_bin = start_bin.max(0) as usize;
        let end_bin = end_bin.min((self.bins.len() - 1) as isize) as usize;

        for bin_idx in start_bin..=end_bin {
            let bin = &self.bins[bin_idx];
            for &global_peak_index in &bin.peak_indices {
                // 从全局索引计算谱图索引和峰索引
                let (spectrum_idx, peak_idx) = self.decode_global_index(global_peak_index);
                
                if let Some(spectrum) = self.spectra.get(spectrum_idx) {
                    if let Some((mz, intensity)) = spectrum.peaks.get(peak_idx) {
                        if *mz >= mz_range.0 && *mz <= mz_range.1 {
                            results.push((*mz, *intensity));
                        }
                    }
                }
            }
        }

        Ok(results)
    }

    /// 根据全局索引解码谱图索引和峰索引
    fn decode_global_index(&self, global_index: usize) -> (usize, usize) {
        // 这是一个简化的实现，实际中可能需要更复杂的索引管理
        let mut cumulative_peaks = 0;
        for (spectrum_idx, spectrum) in self.spectra.iter().enumerate() {
            if cumulative_peaks + spectrum.peaks.len() > global_index {
                return (spectrum_idx, global_index - cumulative_peaks);
            }
            cumulative_peaks += spectrum.peaks.len();
        }
        (0, 0) // 默认值，不应该到达这里
    }

    /// 获取bin数量
    pub fn bin_count(&self) -> usize {
        self.bins.len()
    }

    /// 获取谱图数量
    pub fn spectrum_count(&self) -> usize {
        self.spectra.len()
    }

    /// 获取总峰数量
    pub fn total_peak_count(&self) -> usize {
        self.spectra.iter().map(|s| s.peaks.len()).sum()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_spectrum_creation() {
        let spectrum = Spectrum::ms1().unwrap();
        assert_eq!(spectrum.level, 1);
        assert!(spectrum.peaks.is_empty());
        assert!(!spectrum.has_precursor());
    }

    #[test]
    fn test_add_peaks() {
        let mut spectrum = Spectrum::ms1().unwrap();
        spectrum.add_peak(100.0, 1000.0).unwrap();
        spectrum.add_peak(200.0, 2000.0).unwrap();
        
        assert_eq!(spectrum.peak_count(), 2);
        assert_eq!(spectrum.total_ion_current(), 3000.0);
    }

    #[test]
    fn test_sort_peaks() {
        let mut spectrum = Spectrum::ms1().unwrap();
        spectrum.add_peak(200.0, 2000.0).unwrap();
        spectrum.add_peak(100.0, 1000.0).unwrap();
        
        spectrum.sort_peaks();
        assert_eq!(spectrum.peaks[0].0, 100.0);
        assert_eq!(spectrum.peaks[1].0, 200.0);
    }

    #[test]
    fn test_mz_range() {
        let mut spectrum = Spectrum::ms1().unwrap();
        assert!(spectrum.mz_range().is_none());
        
        spectrum.add_peak(100.0, 1000.0).unwrap();
        spectrum.add_peak(200.0, 2000.0).unwrap();
        
        let range = spectrum.mz_range().unwrap();
        assert_eq!(range.start, 100.0);
        assert_eq!(range.end, 200.0);
    }

    #[test]
    fn test_binned_index() {
        let mut spectrum1 = Spectrum::ms1().unwrap();
        spectrum1.add_peak(100.5, 1000.0).unwrap();
        spectrum1.add_peak(200.5, 2000.0).unwrap();
        
        let mut spectrum2 = Spectrum::ms2().unwrap();
        spectrum2.add_peak(150.5, 1500.0).unwrap();
        
        let spectra = vec![spectrum1, spectrum2];
        let index = BinnedSpectraIndex::new(spectra, 50.0).unwrap();
        
        assert_eq!(index.spectrum_count(), 2);
        assert_eq!(index.total_peak_count(), 3);
        
        let results = index.search_range((90.0, 110.0)).unwrap();
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].0, 100.5);
    }

    #[test]
    fn test_validation() {
        let mut spectrum = Spectrum::ms1().unwrap();
        
        // 空谱图应该失败
        assert!(spectrum.validate().is_err());
        
        spectrum.add_peak(100.0, 1000.0).unwrap();
        
        // 有效谱图应该通过
        assert!(spectrum.validate().is_ok());
        
        // 无效峰应该失败
        spectrum.add_peak(-1.0, 1000.0).unwrap();
        assert!(spectrum.validate().is_err());
    }
}
