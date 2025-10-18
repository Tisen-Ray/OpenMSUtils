//! OpenMSUtils Spectra模块Rust重写
//!
//! 这个模块提供了质谱数据处理功能，与原Python接口1:1兼容：
//! - MZML文件解析
//! - XIC提取
//! - 谱图搜索和索引
//! - 离子迁移率工具
//! - 格式转换

// 导入各个子模块
pub mod test_module;
pub mod core;
pub mod parsers;

// 导入各个子模块 - 即将实现
// pub mod search;
// pub mod xic;
// pub mod conversion;
// pub mod ion_mobility;
// pub mod utils;

// 重新导出测试接口
#[cfg(feature = "python")]
pub use test_module::TestMSObject;

// 重新导出主要的Rust接口
#[cfg(feature = "python")]
pub use core::{Spectrum};
#[cfg(feature = "python")]
pub use parsers::{MZMLParser, MZMLUtils};

// Python模块注册
#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pymodule]
fn _openms_utils_rust(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Test module
    m.add_class::<test_module::TestMSObject>()?;

    // Re-export core and parser classes
    m.add_class::<core::Spectrum>()?;
    m.add_class::<parsers::MZMLParser>()?;
    m.add_class::<parsers::MZMLUtils>()?;

    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}