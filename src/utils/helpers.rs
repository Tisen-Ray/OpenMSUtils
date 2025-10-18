//! 基础工具函数

use crate::core::types::*;

/// 查找在给定容差范围内匹配的峰
pub fn find_peaks_in_tolerance(peaks: &[Peak], target_mz: f64, tolerance: f64) -> Vec<usize> {
    let mut result = Vec::new();
    for (i, &(mz, _)) in peaks.iter().enumerate() {
        if (mz - target_mz).abs() <= tolerance {
            result.push(i);
        }
    }
    result
}

/// 计算总离子流
pub fn total_ion_current(peaks: &[Peak]) -> f64 {
    peaks.iter().map(|(_, intensity)| *intensity).sum()
}

/// 查找基峰
pub fn find_base_peak(peaks: &[Peak]) -> Option<Peak> {
    peaks.iter()
        .max_by(|a, b| a.1.partial_cmp(&b.1).unwrap())
        .copied()
}

/// 按m/z范围过滤峰
pub fn filter_by_mz_range(peaks: &[Peak], range: (f64, f64)) -> Vec<Peak> {
    peaks.iter()
        .filter(|&&(mz, _)| mz >= range.0 && mz <= range.1)
        .copied()
        .collect()
}