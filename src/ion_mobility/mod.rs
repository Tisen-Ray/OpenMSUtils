//! 离子迁移率模块
//! 
//! 这个模块提供了离子迁移率谱数据处理功能，包括：
//! - 离子迁移率解析
//! - 峰合并算法

pub mod parser;
pub mod merger;

// 重新导出主要类型
pub use parser::*;
pub use merger::*;
