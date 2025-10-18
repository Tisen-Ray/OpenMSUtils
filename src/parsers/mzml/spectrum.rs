//! MZML谱图数据结构
//! 
//! 这个模块定义了mzML格式特有的谱图数据结构

use crate::core::types::*;
use crate::parsers::common::{CVParam, UserParam, BinaryDataArray, ParseResult, ParseError};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// MZML谱图数据结构
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MZMLSpectrum {
    /// 谱图ID
    pub id: String,
    /// 默认累积长度
    pub default_array_length: usize,
    /// 索引
    pub index: Option<usize>,
    /// 源文件引用
    pub source_file_ref: Option<String>,
    /// CV参数列表
    pub cv_params: Vec<CVParam>,
    /// 用户参数列表
    pub user_params: Vec<UserParam>,
    /// 扫描列表
    pub scan_list: MZMLScanList,
    /// 前体离子列表
    pub precursors: Vec<MZMLPrecursor>,
    /// 二进制数据数组列表
    pub binary_data_arrays: Vec<MZMLBinaryDataArray>,
}

impl MZMLSpectrum {
    /// 创建新的MZML谱图
    pub fn new(id: String, default_array_length: usize) -> Self {
        Self {
            id,
            default_array_length,
            index: None,
            source_file_ref: None,
            cv_params: Vec::new(),
            user_params: Vec::new(),
            scan_list: MZMLScanList::new(),
            precursors: Vec::new(),
            binary_data_arrays: Vec::new(),
        }
    }

    /// 添加CV参数
    pub fn add_cv_param(&mut self, param: CVParam) {
        self.cv_params.push(param);
    }

    /// 添加用户参数
    pub fn add_user_param(&mut self, param: UserParam) {
        self.user_params.push(param);
    }

    /// 添加二进制数据数组
    pub fn add_binary_data_array(&mut self, array: MZMLBinaryDataArray) {
        self.binary_data_arrays.push(array);
    }

    /// 添加前体离子
    pub fn add_precursor(&mut self, precursor: MZMLPrecursor) {
        self.precursors.push(precursor);
    }

    /// 获取MS级别
    pub fn get_ms_level(&self) -> ParseResult<u8> {
        for param in &self.cv_params {
            if param.is_accession("MS:1000511") {
                return param.as_i64().map(|v| v as u8);
            }
        }
        Err(ParseError::MissingField {
            field: "MS level".to_string(),
        })
    }

    /// 获取谱图类型
    pub fn get_spectrum_type(&self) -> Option<String> {
        for param in &self.cv_params {
            if param.is_accession("MS:1000510") {
                return Some(param.value.clone());
            }
        }
        None
    }

    /// 获取总离子流
    pub fn get_total_ion_current(&self) -> Option<f64> {
        for param in &self.cv_params {
            if param.is_accession("MS:1000285") {
                return param.as_f64().ok();
            }
        }
        None
    }

    /// 获取基峰强度
    pub fn get_base_peak_intensity(&self) -> Option<f64> {
        for param in &self.cv_params {
            if param.is_accession("MS:1000284") {
                return param.as_f64().ok();
            }
        }
        None
    }

    /// 获取基峰m/z
    pub fn get_base_peak_mz(&self) -> Option<f64> {
        for param in &self.cv_params {
            if param.is_accession("MS:1000283") {
                return param.as_f64().ok();
            }
        }
        None
    }

    /// 获取扫描开始时间
    pub fn get_scan_start_time(&self) -> Option<f64> {
        for scan in &self.scan_list.scans {
            if let Some(time) = scan.get_scan_start_time() {
                return Some(time);
            }
        }
        None
    }

    /// 获取m/z数组
    pub fn get_mz_array(&self) -> ParseResult<Option<Vec<f64>>> {
        for array in &self.binary_data_arrays {
            if array.is_mz_array() {
                return Ok(Some(array.decode_f64()?));
            }
        }
        Ok(None)
    }

    /// 获取强度数组
    pub fn get_intensity_array(&self) -> ParseResult<Option<Vec<f64>>> {
        for array in &self.binary_data_arrays {
            if array.is_intensity_array() {
                return Ok(Some(array.decode_f64()?));
            }
        }
        Ok(None)
    }

    /// 获取质谱峰数据
    pub fn get_peaks(&self) -> ParseResult<Vec<(f64, f64)>> {
        let mz_array = self.get_mz_array()?;
        let intensity_array = self.get_intensity_array()?;

        match (mz_array, intensity_array) {
            (Some(mz), Some(intensity)) => {
                if mz.len() != intensity.len() {
                    return Err(ParseError::CorruptedData(format!(
                        "m/z array length ({}) != intensity array length ({})",
                        mz.len(), intensity.len()
                    )));
                }
                Ok(mz.into_iter().zip(intensity.into_iter()).collect())
            }
            _ => Err(ParseError::MissingField {
                field: "m/z or intensity array".to_string(),
            }),
        }
    }

    /// 验证谱图数据
    pub fn validate(&self) -> ParseResult<()> {
        // 检查必需的CV参数
        if self.get_ms_level().is_err() {
            return Err(ParseError::MissingField {
                field: "MS level".to_string(),
            });
        }

        // 检查数组长度一致性
        if let Some(mz_array) = self.get_mz_array()? {
            if let Some(intensity_array) = self.get_intensity_array()? {
                if mz_array.len() != intensity_array.len() {
                    return Err(ParseError::CorruptedData(
                        "m/z and intensity arrays have different lengths".to_string()
                    ));
                }
            }
        }

        Ok(())
    }
}

/// MZML扫描列表
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MZMLScanList {
    /// 扫描列表
    pub scans: Vec<MZMLScan>,
}

impl MZMLScanList {
    /// 创建新的扫描列表
    pub fn new() -> Self {
        Self {
            scans: Vec::new(),
        }
    }

    /// 添加扫描
    pub fn add_scan(&mut self, scan: MZMLScan) {
        self.scans.push(scan);
    }

    /// 获取第一个扫描
    pub fn first_scan(&self) -> Option<&MZMLScan> {
        self.scans.first()
    }
}

/// MZML扫描
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MZMLScan {
    /// 扫描ID
    pub id: Option<String>,
    /// 扫描编号
    pub scan_number: Option<u32>,
    /// CV参数列表
    pub cv_params: Vec<CVParam>,
    /// 用户参数列表
    pub user_params: Vec<UserParam>,
}

impl MZMLScan {
    /// 创建新的扫描
    pub fn new() -> Self {
        Self {
            id: None,
            scan_number: None,
            cv_params: Vec::new(),
            user_params: Vec::new(),
        }
    }

    /// 添加CV参数
    pub fn add_cv_param(&mut self, param: CVParam) {
        self.cv_params.push(param);
    }

    /// 添加用户参数
    pub fn add_user_param(&mut self, param: UserParam) {
        self.user_params.push(param);
    }

    /// 获取扫描开始时间
    pub fn get_scan_start_time(&self) -> Option<f64> {
        for param in &self.cv_params {
            if param.is_accession("MS:1000016") {
                return param.as_f64().ok();
            }
        }
        None
    }

    /// 获取扫描窗口下限
    pub fn get_scan_window_lower_limit(&self) -> Option<f64> {
        for param in &self.cv_params {
            if param.is_accession("MS:1000501") {
                return param.as_f64().ok();
            }
        }
        None
    }

    /// 获取扫描窗口上限
    pub fn get_scan_window_upper_limit(&self) -> Option<f64> {
        for param in &self.cv_params {
            if param.is_accession("MS:1000500") {
                return param.as_f64().ok();
            }
        }
        None
    }

    /// 获取扫描窗口
    pub fn get_scan_window(&self) -> Option<(f64, f64)> {
        match (self.get_scan_window_lower_limit(), self.get_scan_window_upper_limit()) {
            (Some(lower), Some(upper)) => Some((lower, upper)),
            _ => None,
        }
    }
}

/// MZML前体离子
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MZMLPrecursor {
    /// 前体谱图引用
    pub spectrum_ref: Option<String>,
    /// CV参数列表
    pub cv_params: Vec<CVParam>,
    /// 用户参数列表
    pub user_params: Vec<UserParam>,
    /// 分离窗口列表
    pub isolation_windows: Vec<MZMLIsolationWindow>,
    /// 激活信息
    pub activation: Option<MZMLActivation>,
}

impl MZMLPrecursor {
    /// 创建新的前体离子
    pub fn new() -> Self {
        Self {
            spectrum_ref: None,
            cv_params: Vec::new(),
            user_params: Vec::new(),
            isolation_windows: Vec::new(),
            activation: None,
        }
    }

    /// 添加CV参数
    pub fn add_cv_param(&mut self, param: CVParam) {
        self.cv_params.push(param);
    }

    /// 添加用户参数
    pub fn add_user_param(&mut self, param: UserParam) {
        self.user_params.push(param);
    }

    /// 添加分离窗口
    pub fn add_isolation_window(&mut self, window: MZMLIsolationWindow) {
        self.isolation_windows.push(window);
    }

    /// 设置激活信息
    pub fn set_activation(&mut self, activation: MZMLActivation) {
        self.activation = Some(activation);
    }

    /// 获取前体离子m/z
    pub fn get_precursor_mz(&self) -> Option<f64> {
        for param in &self.cv_params {
            if param.is_accession("MS:1000744") {
                return param.as_f64().ok();
            }
        }
        None
    }

    /// 获取前体离子强度
    pub fn get_precursor_intensity(&self) -> Option<f64> {
        for param in &self.cv_params {
            if param.is_accession("MS:1000042") {
                return param.as_f64().ok();
            }
        }
        None
    }

    /// 获取前体离子电荷
    pub fn get_precursor_charge(&self) -> Option<i8> {
        for param in &self.cv_params {
            if param.is_accession("MS:1000041") {
                return param.as_i64().ok().map(|v| v as i8);
            }
        }
        None
    }
}

/// MZML分离窗口
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MZMLIsolationWindow {
    /// CV参数列表
    pub cv_params: Vec<CVParam>,
    /// 用户参数列表
    pub user_params: Vec<UserParam>,
}

impl MZMLIsolationWindow {
    /// 创建新的分离窗口
    pub fn new() -> Self {
        Self {
            cv_params: Vec::new(),
            user_params: Vec::new(),
        }
    }

    /// 添加CV参数
    pub fn add_cv_param(&mut self, param: CVParam) {
        self.cv_params.push(param);
    }

    /// 添加用户参数
    pub fn add_user_param(&mut self, param: UserParam) {
        self.user_params.push(param);
    }

    /// 获取分离窗口m/z偏移
    pub fn get_isolation_window_target_mz(&self) -> Option<f64> {
        for param in &self.cv_params {
            if param.is_accession("MS:1000827") {
                return param.as_f64().ok();
            }
        }
        None
    }

    /// 获取分离窗口下限
    pub fn get_isolation_window_lower_offset(&self) -> Option<f64> {
        for param in &self.cv_params {
            if param.is_accession("MS:1000828") {
                return param.as_f64().ok();
            }
        }
        None
    }

    /// 获取分离窗口上限
    pub fn get_isolation_window_upper_offset(&self) -> Option<f64> {
        for param in &self.cv_params {
            if param.is_accession("MS:1000829") {
                return param.as_f64().ok();
            }
        }
        None
    }
}

/// MZML激活信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MZMLActivation {
    /// CV参数列表
    pub cv_params: Vec<CVParam>,
    /// 用户参数列表
    pub user_params: Vec<UserParam>,
}

impl MZMLActivation {
    /// 创建新的激活信息
    pub fn new() -> Self {
        Self {
            cv_params: Vec::new(),
            user_params: Vec::new(),
        }
    }

    /// 添加CV参数
    pub fn add_cv_param(&mut self, param: CVParam) {
        self.cv_params.push(param);
    }

    /// 添加用户参数
    pub fn add_user_param(&mut self, param: UserParam) {
        self.user_params.push(param);
    }

    /// 获取激活方法
    pub fn get_activation_method(&self) -> Option<String> {
        for param in &self.cv_params {
            if param.is_accession("MS:1000133") || // CID
               param.is_accession("MS:1000134") || // HCD
               param.is_accession("MS:1000135") || // ETD
               param.is_accession("MS:1000136") || // ECD
               param.is_accession("MS:1000137") { // PQD
                return Some(param.value.clone());
            }
        }
        None
    }

    /// 获取碰撞能量
    pub fn get_collision_energy(&self) -> Option<f64> {
        for param in &self.cv_params {
            if param.is_accession("MS:1000045") {
                return param.as_f64().ok();
            }
        }
        None
    }
}

/// MZML二进制数据数组
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MZMLBinaryDataArray {
    /// 数组长度
    pub length: Option<usize>,
    /// CV参数列表
    pub cv_params: Vec<CVParam>,
    /// 用户参数列表
    pub user_params: Vec<UserParam>,
    /// 二进制数据
    pub binary: Option<BinaryDataArray>,
}

impl MZMLBinaryDataArray {
    /// 创建新的二进制数据数组
    pub fn new() -> Self {
        Self {
            length: None,
            cv_params: Vec::new(),
            user_params: Vec::new(),
            binary: None,
        }
    }

    /// 添加CV参数
    pub fn add_cv_param(&mut self, param: CVParam) {
        self.cv_params.push(param);
    }

    /// 添加用户参数
    pub fn add_user_param(&mut self, param: UserParam) {
        self.user_params.push(param);
    }

    /// 设置二进制数据
    pub fn set_binary(&mut self, binary: BinaryDataArray) {
        self.binary = Some(binary);
    }

    /// 检查是否为m/z数组
    pub fn is_mz_array(&self) -> bool {
        for param in &self.cv_params {
            if param.is_accession("MS:1000514") {
                return true;
            }
        }
        false
    }

    /// 检查是否为强度数组
    pub fn is_intensity_array(&self) -> bool {
        for param in &self.cv_params {
            if param.is_accession("MS:1000515") {
                return true;
            }
        }
        false
    }

    /// 解码为f64数组
    pub fn decode_f64(&self) -> ParseResult<Vec<f64>> {
        match &self.binary {
            Some(binary) => binary.decode_f64(),
            None => Err(ParseError::EmptyDataArray),
        }
    }

    /// 解码为f32数组
    pub fn decode_f32(&self) -> ParseResult<Vec<f32>> {
        match &self.binary {
            Some(binary) => binary.decode_f32(),
            None => Err(ParseError::EmptyDataArray),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_mzml_spectrum_creation() {
        let spectrum = MZMLSpectrum::new("spectrum1".to_string(), 100);
        assert_eq!(spectrum.id, "spectrum1");
        assert_eq!(spectrum.default_array_length, 100);
    }

    #[test]
    fn test_cv_param_access() {
        let mut spectrum = MZMLSpectrum::new("spectrum1".to_string(), 100);
        spectrum.add_cv_param(CVParam::new("MS:1000511", "ms level", "2"));
        
        assert_eq!(spectrum.get_ms_level().unwrap(), 2);
    }

    #[test]
    fn test_scan_creation() {
        let mut scan = MZMLScan::new();
        scan.add_cv_param(CVParam::new("MS:1000016", "scan start time", "10.5"));
        
        assert_eq!(scan.get_scan_start_time().unwrap(), 10.5);
    }

    #[test]
    fn test_precursor_creation() {
        let mut precursor = MZMLPrecursor::new();
        precursor.add_cv_param(CVParam::new("MS:1000744", "selected ion m/z", "500.0"));
        
        assert_eq!(precursor.get_precursor_mz().unwrap(), 500.0);
    }
}
