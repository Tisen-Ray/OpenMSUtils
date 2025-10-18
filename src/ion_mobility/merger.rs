//! 峰合并算法
//!
//! 提供基础的峰合并算法实现

use crate::core::types::*;
use std::collections::HashMap;

/// 峰合并器
pub struct PeakMerger {
    /// 合并策略
    merge_strategy: MergeStrategy,
}

/// 合并策略
#[derive(Debug, Clone, Copy)]
pub enum MergeStrategy {
    /// 取最大强度
    MaxIntensity,
    /// 取平均强度
    AverageIntensity,
    /// 累加强度
    SumIntensity,
    /// 加权平均（基于强度）
    WeightedAverage,
}

impl PeakMerger {
    /// 创建新的峰合并器
    pub fn new(strategy: MergeStrategy) -> Self {
        Self {
            merge_strategy: strategy,
        }
    }

    /// 使用默认策略创建峰合并器
    pub fn default() -> Self {
        Self::new(MergeStrategy::MaxIntensity)
    }

    /// 合并峰列表
    pub fn merge_peaks(&self, peaks: Vec<Peak>, tolerance: f64) -> Vec<Peak> {
        if peaks.is_empty() {
            return Vec::new();
        }

        if peaks.len() == 1 {
            return peaks;
        }

        // 按m/z排序
        let mut sorted_peaks = peaks;
        sorted_peaks.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());

        // 使用标量合并算法
        self.merge_peaks_scalar(sorted_peaks, tolerance)
    }

    /// 标量版本的峰合并
    fn merge_peaks_scalar(&self, peaks: Vec<Peak>, tolerance: f64) -> Vec<Peak> {
        let mut merged = Vec::new();
        let mut current_group = Vec::new();

        for &peak in &peaks {
            if current_group.is_empty() {
                current_group.push(peak);
            } else {
                let last_mz = current_group.last().unwrap().0;
                if (peak.0 - last_mz) <= tolerance {
                    current_group.push(peak);
                } else {
                    // 合并当前组
                    if !current_group.is_empty() {
                        merged.push(self.merge_group(&current_group));
                    }
                    current_group.clear();
                    current_group.push(peak);
                }
            }
        }

        // 合并最后一组
        if !current_group.is_empty() {
            merged.push(self.merge_group(&current_group));
        }

        merged
    }

    
    /// 合并一组峰
    fn merge_group(&self, group: &[Peak]) -> Peak {
        match self.merge_strategy {
            MergeStrategy::MaxIntensity => {
                group.iter()
                    .max_by(|a, b| a.1.partial_cmp(&b.1).unwrap())
                    .copied()
                    .unwrap_or((0.0, 0.0))
            }
            MergeStrategy::AverageIntensity => {
                let count = group.len() as f64;
                let sum_intensity: f64 = group.iter().map(|(_, intensity)| *intensity).sum();
                let avg_intensity = sum_intensity / count;

                // 使用加权平均计算m/z
                let weighted_mz: f64 = group.iter()
                    .map(|(mz, intensity)| mz * intensity)
                    .sum();
                let avg_mz = if sum_intensity > 0.0 { weighted_mz / sum_intensity } else { 0.0 };

                (avg_mz, avg_intensity)
            }
            MergeStrategy::SumIntensity => {
                let sum_intensity: f64 = group.iter().map(|(_, intensity)| *intensity).sum();

                // 使用加权平均计算m/z
                let weighted_mz: f64 = group.iter()
                    .map(|(mz, intensity)| mz * intensity)
                    .sum();
                let avg_mz = if sum_intensity > 0.0 { weighted_mz / sum_intensity } else { 0.0 };

                (avg_mz, sum_intensity)
            }
            MergeStrategy::WeightedAverage => {
                let total_intensity: f64 = group.iter().map(|(_, intensity)| *intensity).sum();
                let max_intensity: f64 = group.iter().map(|(_, intensity)| *intensity).fold(0.0_f64, |a, b| a.max(b));

                // 基于强度的加权平均
                let weighted_mz: f64 = group.iter()
                    .map(|(mz, intensity)| mz * (intensity / max_intensity))
                    .sum();
                let weight_sum: f64 = group.iter()
                    .map(|(_, intensity)| intensity / max_intensity)
                    .sum();
                let avg_mz = if weight_sum > 0.0 { weighted_mz / weight_sum } else { 0.0 };

                // 使用最大强度作为合并后的强度
                (avg_mz, max_intensity)
            }
        }
    }

    /// 批量合并多个峰列表
    pub fn merge_multiple_peak_lists(&self, peak_lists: &[Vec<Peak>], tolerance: f64) -> Vec<Peak> {
        let mut all_peaks = Vec::new();

        for peak_list in peak_lists {
            all_peaks.extend_from_slice(peak_list);
        }

        self.merge_peaks(all_peaks, tolerance)
    }

    /// 分级合并（先小容差合并，再大容差合并）
    pub fn hierarchical_merge(&self, peaks: Vec<Peak>, tolerances: &[f64]) -> Vec<Peak> {
        let mut current_peaks = peaks;

        for &tolerance in tolerances {
            current_peaks = self.merge_peaks(current_peaks, tolerance);
        }

        current_peaks
    }

    /// 基于密度的合并（在峰密度高的区域使用更小的容差）
    pub fn density_based_merge(&self, peaks: Vec<Peak>, base_tolerance: f64) -> Vec<Peak> {
        if peaks.len() < 3 {
            return self.merge_peaks(peaks, base_tolerance);
        }

        // 计算峰密度
        let mut densities = Vec::new();
        let window_size = 5; // 使用5个最近的峰计算密度

        for i in 0..peaks.len() {
            let start = if i >= window_size { i - window_size } else { 0 };
            let end = (i + window_size).min(peaks.len() - 1);

            let window_range = peaks[end].0 - peaks[start].0;
            let density = (end - start) as f64 / window_range;
            densities.push(density);
        }

        // 根据密度调整容差
        let max_density: f64 = densities.iter().fold(0.0_f64, |a, &b| a.max(b));
        let min_density = densities.iter().fold(f64::INFINITY, |a, &b| a.min(b));
        let density_range = max_density - min_density;

        let mut merged_peaks = Vec::new();
        let mut current_group = Vec::new();

        for (i, &peak) in peaks.iter().enumerate() {
            let density_factor = if density_range > 0.0 {
                (densities[i] - min_density) / density_range
            } else {
                0.5
            };

            // 密度高的区域使用更小的容差
            let adjusted_tolerance = base_tolerance * (1.5 - density_factor);

            if current_group.is_empty() {
                current_group.push(peak);
            } else {
                let last_mz = current_group.last().unwrap().0;
                if (peak.0 - last_mz) <= adjusted_tolerance {
                    current_group.push(peak);
                } else {
                    if !current_group.is_empty() {
                        merged_peaks.push(self.merge_group(&current_group));
                    }
                    current_group.clear();
                    current_group.push(peak);
                }
            }
        }

        if !current_group.is_empty() {
            merged_peaks.push(self.merge_group(&current_group));
        }

        merged_peaks
    }

    /// 获取合并统计信息
    pub fn get_merge_statistics(&self, original: &[Peak], merged: &[Peak]) -> MergeStatistics {
        let original_count = original.len();
        let merged_count = merged.len();
        let reduction_ratio = if original_count > 0 {
            1.0 - (merged_count as f64 / original_count as f64)
        } else {
            0.0
        };

        let total_intensity_original: f64 = original.iter().map(|(_, intensity)| *intensity).sum();
        let total_intensity_merged: f64 = merged.iter().map(|(_, intensity)| *intensity).sum();
        let intensity_retention = if total_intensity_original > 0.0 {
            total_intensity_merged / total_intensity_original
        } else {
            1.0
        };

        MergeStatistics {
            original_peak_count: original_count,
            merged_peak_count: merged_count,
            reduction_ratio,
            intensity_retention,
            merge_strategy: self.merge_strategy,
        }
    }
}

/// 合并统计信息
#[derive(Debug, Clone)]
pub struct MergeStatistics {
    pub original_peak_count: usize,
    pub merged_peak_count: usize,
    pub reduction_ratio: f64,
    pub intensity_retention: f64,
    pub merge_strategy: MergeStrategy,
}

/// 内部峰合并函数（供其他模块使用）
pub fn merge_peaks_by_mz_internal(peaks: Vec<Peak>, mz_tolerance: f64) -> Vec<Peak> {
    let merger = PeakMerger::new(MergeStrategy::MaxIntensity);
    merger.merge_peaks(peaks, mz_tolerance)
}

/// 高级峰合并功能
pub struct AdvancedPeakMerger {
    base_merger: PeakMerger,
}

impl AdvancedPeakMerger {
    /// 创建新的高级峰合并器
    pub fn new(strategy: MergeStrategy) -> Self {
        Self {
            base_merger: PeakMerger::new(strategy),
        }
    }

    /// 智能合并（自动选择最佳策略）
    pub fn intelligent_merge(&self, peaks: Vec<Peak>) -> Vec<Peak> {
        if peaks.len() < 2 {
            return peaks;
        }

        // 分析峰分布特征
        let features = self.analyze_peak_features(&peaks);

        // 根据特征选择最佳策略
        let strategy = self.select_optimal_strategy(&features);
        let tolerance = self.calculate_optimal_tolerance(&features);

        let merger = PeakMerger::new(strategy);
        merger.merge_peaks(peaks, tolerance)
    }

    /// 分析峰特征
    fn analyze_peak_features(&self, peaks: &[Peak]) -> PeakFeatures {
        let count = peaks.len();

        let intensities: Vec<f64> = peaks.iter().map(|(_, intensity)| *intensity).collect();
        let max_intensity: f64 = intensities.iter().fold(0.0_f64, |a, &b| a.max(b));
        let min_intensity = intensities.iter().fold(f64::INFINITY, |a, &b| a.min(b));
        let avg_intensity = intensities.iter().sum::<f64>() / count as f64;

        // 计算m/z范围
        let mz_values: Vec<f64> = peaks.iter().map(|(mz, _)| *mz).collect();
        let mz_range = mz_values.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b)) -
                      mz_values.iter().fold(f64::INFINITY, |a, &b| a.min(b));

        // 计算峰密度
        let density = count as f64 / mz_range;

        // 计算强度分布的变异系数
        let intensity_variance = intensities.iter()
            .map(|intensity| (intensity - avg_intensity).powi(2))
            .sum::<f64>() / (count - 1) as f64;
        let cv = if avg_intensity > 0.0 {
            intensity_variance.sqrt() / avg_intensity
        } else {
            0.0
        };

        PeakFeatures {
            count,
            max_intensity,
            min_intensity,
            avg_intensity,
            mz_range,
            density,
            intensity_cv: cv,
        }
    }

    /// 选择最佳合并策略
    fn select_optimal_strategy(&self, features: &PeakFeatures) -> MergeStrategy {
        // 根据峰特征选择策略
        if features.intensity_cv > 1.0 {
            // 强度变化大时，使用最大强度策略
            MergeStrategy::MaxIntensity
        } else if features.density > 10.0 {
            // 密度高时，使用加权平均
            MergeStrategy::WeightedAverage
        } else {
            // 默认使用平均强度
            MergeStrategy::AverageIntensity
        }
    }

    /// 计算最佳容差
    fn calculate_optimal_tolerance(&self, features: &PeakFeatures) -> f64 {
        // 基于峰密度和强度分布计算容差
        let base_tolerance = 0.01; // 10 ppm

        if features.density > 20.0 {
            base_tolerance * 0.5  // 密度高时减小容差
        } else if features.density < 1.0 {
            base_tolerance * 2.0  // 密度低时增大容差
        } else {
            base_tolerance
        }
    }
}

/// 峰特征
#[derive(Debug, Clone)]
struct PeakFeatures {
    count: usize,
    max_intensity: f64,
    min_intensity: f64,
    avg_intensity: f64,
    mz_range: f64,
    density: f64,
    intensity_cv: f64,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_peak_merger_basic() {
        let peaks = vec![
            (100.0, 1000.0),
            (100.005, 800.0),  // 在容差范围内
            (101.0, 1200.0),
            (200.0, 500.0),
        ];

        let merger = PeakMerger::new(MergeStrategy::MaxIntensity);
        let merged = merger.merge_peaks(peaks, 0.01);

        assert_eq!(merged.len(), 3); // 100.0和100.005应该合并
        assert!(merged.iter().any(|(mz, _)| (mz - 100.0).abs() < 0.001));
    }

    #[test]
    fn test_merge_strategies() {
        let peaks = vec![
            (100.0, 1000.0),
            (100.005, 800.0),
        ];

        let max_merger = PeakMerger::new(MergeStrategy::MaxIntensity);
        let max_result = max_merger.merge_peaks(peaks.clone(), 0.01);
        assert_eq!(max_result[0].1, 1000.0); // 应该取最大强度

        let avg_merger = PeakMerger::new(MergeStrategy::AverageIntensity);
        let avg_result = avg_merger.merge_peaks(peaks, 0.01);
        assert_eq!(avg_result[0].1, 900.0); // 应该取平均强度
    }

    #[test]
    fn test_density_based_merge() {
        let peaks = vec![
            (100.0, 1000.0),
            (100.001, 900.0),
            (100.002, 800.0),
            (100.003, 700.0),
            (200.0, 500.0),
        ];

        let merger = PeakMerger::new(MergeStrategy::MaxIntensity);
        let merged = merger.density_based_merge(peaks, 0.01);

        assert_eq!(merged.len(), 2); // 前4个峰密度高应该合并，第5个单独
    }

    #[test]
    fn test_merge_statistics() {
        let original = vec![(100.0, 1000.0), (200.0, 800.0)];
        let merged = vec![(100.0, 1800.0)]; // 两个峰合并

        let merger = PeakMerger::new(MergeStrategy::SumIntensity);
        let stats = merger.get_merge_statistics(&original, &merged);

        assert_eq!(stats.original_peak_count, 2);
        assert_eq!(stats.merged_peak_count, 1);
        assert_eq!(stats.reduction_ratio, 0.5);
        assert_eq!(stats.intensity_retention, 1.0);
    }
}
