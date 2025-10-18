//! 基础类型定义
//! 
//! 这个模块定义了在整个项目中使用的基础类型和常量

use serde::{Deserialize, Serialize};

/// 键值对类型，用于存储元数据
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct KeyValue {
    pub key: String,
    pub value: String,
}

impl KeyValue {
    pub fn new(key: impl Into<String>, value: impl Into<String>) -> Self {
        Self {
            key: key.into(),
            value: value.into(),
        }
    }
}

/// 质谱峰数据类型
pub type Peak = (f64, f64);

/// 质谱峰列表类型
pub type PeakList = Vec<Peak>;

/// 小规模键值对列表类型（优化内存使用）
pub type SmallKeyValueList = Vec<KeyValue>;

impl SmallKeyValueList {
    pub fn new() -> Self {
        Vec::new()
    }
}

/// 质量容差类型
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum Tolerance {
    /// PPM容差
    PPM(f64),
    /// 绝对质量容差（Da）
    Absolute(f64),
}

impl Tolerance {
    /// 计算给定m/z的质量容差
    pub fn tolerance_at_mz(&self, mz: f64) -> f64 {
        match self {
            Tolerance::PPM(ppm) => mz * ppm * 1e-6,
            Tolerance::Absolute(da) => *da,
        }
    }
    
    /// 检查两个m/z值是否在容差范围内
    pub fn is_within_tolerance(&self, mz1: f64, mz2: f64) -> bool {
        let tolerance = self.tolerance_at_mz(mz1);
        (mz1 - mz2).abs() <= tolerance
    }
}

/// 常量定义
pub mod constants {
    use super::*;
    
    /// 默认PPM容差
    pub const DEFAULT_PPM_TOLERANCE: f64 = 10.0;
    
    /// 默认bin大小
    pub const DEFAULT_BIN_SIZE: f64 = 1.0;
    
    /// 最小MS级别
    pub const MIN_MS_LEVEL: u8 = 1;
    
    /// 最大MS级别
    pub const MAX_MS_LEVEL: u8 = 10;
    
    /// 默认电荷状态
    pub const DEFAULT_CHARGE: i8 = 0;
    
    /// 默认扫描编号
    pub const DEFAULT_SCAN_NUMBER: u32 = 0;
    
    /// 默认保留时间
    pub const DEFAULT_RETENTION_TIME: f64 = 0.0;
    
    /// 默认漂移时间
    pub const DEFAULT_DRIFT_TIME: f64 = 0.0;
}

/// MS级别类型
pub type MSLevel = u8;

/// 扫描编号类型
pub type ScanNumber = u32;

/// 电荷状态类型
pub type Charge = i8;

/// 保留时间类型（秒）
pub type RetentionTime = f64;

/// 漂移时间类型（秒）
pub type DriftTime = f64;

/// 错误类型定义
#[derive(Debug, thiserror::Error)]
pub enum CoreError {
    #[error("Invalid MS level: {level}. Must be between {min} and {max}")]
    InvalidMSLevel { level: MSLevel, min: MSLevel, max: MSLevel },
    
    #[error("Invalid charge: {charge}. Must be between {min} and {max}")]
    InvalidCharge { charge: Charge, min: Charge, max: Charge },
    
    #[error("Invalid retention time: {rt}. Must be non-negative")]
    InvalidRetentionTime { rt: RetentionTime },
    
    #[error("Invalid drift time: {dt}. Must be non-negative")]
    InvalidDriftTime { dt: DriftTime },
    
    #[error("Empty peak list")]
    EmptyPeakList,
    
    #[error("Invalid peak data: mz={mz}, intensity={intensity}. Both must be non-negative")]
    InvalidPeakData { mz: f64, intensity: f64 },
    
    #[error("Duplicate key: {key}")]
    DuplicateKey { key: String },
    
    #[error("Key not found: {key}")]
    KeyNotFound { key: String },

    #[error("Invalid format: {0}")]
    InvalidFormat(String),
}

/// 结果类型
pub type CoreResult<T> = Result<T, CoreError>;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tolerance_ppm() {
        let tolerance = Tolerance::PPM(10.0);
        let mz = 1000.0;
        let expected_tolerance = 0.01; // 1000 * 10 * 1e-6
        assert!((tolerance.tolerance_at_mz(mz) - expected_tolerance).abs() < 1e-10);
    }

    #[test]
    fn test_tolerance_absolute() {
        let tolerance = Tolerance::Absolute(0.1);
        let mz = 1000.0;
        assert_eq!(tolerance.tolerance_at_mz(mz), 0.1);
    }

    #[test]
    fn test_is_within_tolerance() {
        let tolerance = Tolerance::PPM(10.0);
        assert!(tolerance.is_within_tolerance(1000.0, 1000.005));
        assert!(!tolerance.is_within_tolerance(1000.0, 1000.02));
    }

    #[test]
    fn test_key_value() {
        let kv = KeyValue::new("test", "value");
        assert_eq!(kv.key, "test");
        assert_eq!(kv.value, "value");
    }
}
