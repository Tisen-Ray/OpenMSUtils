//! 搜索和索引模块
//! 
//! 这个模块提供了高效的质谱数据搜索和索引功能，包括：
//! - 二进制索引实现
//! - 并行搜索算法
//! - 范围查询优化

pub mod binned_index;
pub mod parallel_search;
pub mod range_query;

// 重新导出主要类型
pub use binned_index::*;
pub use parallel_search::*;
pub use range_query::*;
