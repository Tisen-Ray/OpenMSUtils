//! XIC提取模块
//! 
//! 这个模块提供了提取离子色谱图(XIC)的功能，包括：
//! - XIC提取器
//! - SIMD优化搜索
//! - XIC结果数据结构

pub mod extractor;
pub mod simd_search;
pub mod result;

// 重新导出主要类型
pub use extractor::*;
pub use simd_search::*;
pub use result::*;
