//! XIC结果数据结构
//! 
//! 定义XIC提取结果的数据结构

use serde::{Deserialize, Serialize};

/// XIC提取结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct XICResult {
    /// 保留时间数组
    pub rt_array: Vec<f64>,
    /// 强度数组
    pub intensity_array: Vec<f64>,
    /// 目标质荷比
    pub mz: f64,
    /// PPM误差
    pub ppm_error: f64,
    /// 离子类型
    pub ion_type: String,
    /// 电荷状态
    pub charge: i8,
}

/// 碎片离子信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FragmentIon {
    pub ion_type: String,
    pub charge: i8,
    pub mz: f64,
}

/// 聚合物信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PolymerInfo {
    pub sequence: String,
    pub modified_sequence: String,
    pub charge: i8,
    pub mz: f64,
    pub rt: f64,
    pub rt_start: f64,
    pub rt_stop: f64,
    pub fragment_ions: Vec<FragmentIon>,
}
