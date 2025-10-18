//! MZML解析器模块
//! 
//! 这个模块提供了mzML格式文件的解析功能，包括：
//! - MZMLReader：Python兼容的mzML读取器
//! - MZMLParser：核心解析逻辑
//! - MZMLSpectrum：mzML特定的谱图数据结构

pub mod reader;
pub mod parser;
pub mod spectrum;

// 重新导出主要类型
#[cfg(feature = "python")]
pub use reader::{MZMLReader};
pub use parser::{MZMLParser};
pub use spectrum::{MZMLSpectrum, MZMLScanList, MZMLBinaryDataArray};
