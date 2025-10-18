//! 通用解析工具
//! 
//! 这个模块提供了所有解析器共用的工具函数和数据结构

use crate::core::types::*;
use serde::{Deserialize, Serialize};
use std::io;
use thiserror::Error;

/// 解析错误类型
#[derive(Debug, Error)]
pub enum ParseError {
    #[error("IO error: {0}")]
    Io(#[from] io::Error),
    
    #[error("XML parsing error: {0}")]
    Xml(String),
    
    #[error("Invalid format: {0}")]
    InvalidFormat(String),
    
    #[error("Missing required field: {field}")]
    MissingField { field: String },
    
    #[error("Invalid data type: {expected}, got {actual}")]
    InvalidDataType { expected: String, actual: String },
    
    #[error("Base64 decoding error: {0}")]
    Base64Decode(#[from] base64::DecodeError),
    
    #[error("Zlib decompression error: {0}")]
    ZlibDecompress(String),
    
    #[error("Invalid binary data encoding: {0}")]
    InvalidBinaryEncoding(String),
    
    #[error("Invalid precision: {0}")]
    InvalidPrecision(String),
    
    #[error("Index out of bounds: {index} in array of length {length}")]
    IndexOutOfBounds { index: usize, length: usize },
    
    #[error("Invalid CV parameter: {accession} - {name}")]
    InvalidCVParam { accession: String, name: String },
    
    #[error("Unsupported version: {version}")]
    UnsupportedVersion { version: String },
    
    #[error("Empty data array")]
    EmptyDataArray,
    
    #[error("Corrupted data: {0}")]
    CorruptedData(String),
}

impl From<crate::core::types::CoreError> for ParseError {
    fn from(error: crate::core::types::CoreError) -> Self {
        ParseError::InvalidFormat(error.to_string())
    }
}

/// 解析结果类型
pub type ParseResult<T> = Result<T, ParseError>;

/// 二进制数据编码类型
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum BinaryDataEncoding {
    /// 32位浮点数，小端序
    Float32Little,
    /// 64位浮点数，小端序
    Float64Little,
    /// 32位浮点数，大端序
    Float32Big,
    /// 64位浮点数，大端序
    Float64Big,
    /// 32位整数，小端序
    Int32Little,
    /// 64位整数，小端序
    Int64Little,
    /// 32位整数，大端序
    Int32Big,
    /// 64位整数，大端序
    Int64Big,
}

impl BinaryDataEncoding {
    /// 从字符串解析编码类型
    pub fn from_string(encoding: &str) -> ParseResult<Self> {
        match encoding.to_lowercase().as_str() {
            "32-bit float" => Ok(BinaryDataEncoding::Float32Little),
            "64-bit float" => Ok(BinaryDataEncoding::Float64Little),
            "32-bit integer" => Ok(BinaryDataEncoding::Int32Little),
            "64-bit integer" => Ok(BinaryDataEncoding::Int64Little),
            _ => Err(ParseError::InvalidBinaryEncoding(encoding.to_string())),
        }
    }

    /// 获取数据类型大小（字节）
    pub fn size(&self) -> usize {
        match self {
            BinaryDataEncoding::Float32Little | BinaryDataEncoding::Float32Big => 4,
            BinaryDataEncoding::Float64Little | BinaryDataEncoding::Float64Big => 8,
            BinaryDataEncoding::Int32Little | BinaryDataEncoding::Int32Big => 4,
            BinaryDataEncoding::Int64Little | BinaryDataEncoding::Int64Big => 8,
        }
    }

    /// 检查是否为浮点数类型
    pub fn is_float(&self) -> bool {
        matches!(self, 
            BinaryDataEncoding::Float32Little | BinaryDataEncoding::Float64Little |
            BinaryDataEncoding::Float32Big | BinaryDataEncoding::Float64Big
        )
    }

    /// 检查是否为小端序
    pub fn is_little_endian(&self) -> bool {
        matches!(self, 
            BinaryDataEncoding::Float32Little | BinaryDataEncoding::Float64Little |
            BinaryDataEncoding::Int32Little | BinaryDataEncoding::Int64Little
        )
    }
}

/// CV参数（控制词汇表参数）
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CVParam {
    /// CV访问号
    pub accession: String,
    /// CV名称
    pub name: String,
    /// CV值
    pub value: String,
    /// 数据类型
    pub data_type: Option<String>,
    /// 单位
    pub unit: Option<String>,
}

impl CVParam {
    /// 创建新的CV参数
    pub fn new(accession: impl Into<String>, name: impl Into<String>, 
               value: impl Into<String>) -> Self {
        Self {
            accession: accession.into(),
            name: name.into(),
            value: value.into(),
            data_type: None,
            unit: None,
        }
    }

    /// 设置数据类型
    pub fn with_data_type(mut self, data_type: impl Into<String>) -> Self {
        self.data_type = Some(data_type.into());
        self
    }

    /// 设置单位
    pub fn with_unit(mut self, unit: impl Into<String>) -> Self {
        self.unit = Some(unit.into());
        self
    }

    /// 获取浮点数值
    pub fn as_f64(&self) -> ParseResult<f64> {
        self.value.parse::<f64>()
            .map_err(|_| ParseError::InvalidDataType {
                expected: "float".to_string(),
                actual: format!("'{}'", self.value),
            })
    }

    /// 获取整数值
    pub fn as_i64(&self) -> ParseResult<i64> {
        self.value.parse::<i64>()
            .map_err(|_| ParseError::InvalidDataType {
                expected: "integer".to_string(),
                actual: format!("'{}'", self.value),
            })
    }

    /// 获取字符串值
    pub fn as_string(&self) -> &str {
        &self.value
    }

    /// 检查是否匹配给定的访问号
    pub fn is_accession(&self, accession: &str) -> bool {
        self.accession == accession
    }

    /// 检查是否匹配给定的名称
    pub fn is_name(&self, name: &str) -> bool {
        self.name == name
    }
}

/// 用户参数
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserParam {
    /// 参数名称
    pub name: String,
    /// 参数值
    pub value: String,
    /// 数据类型
    pub data_type: Option<String>,
    /// 单位
    pub unit: Option<String>,
}

impl UserParam {
    /// 创建新的用户参数
    pub fn new(name: impl Into<String>, value: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            value: value.into(),
            data_type: None,
            unit: None,
        }
    }

    /// 设置数据类型
    pub fn with_data_type(mut self, data_type: impl Into<String>) -> Self {
        self.data_type = Some(data_type.into());
        self
    }

    /// 设置单位
    pub fn with_unit(mut self, unit: impl Into<String>) -> Self {
        self.unit = Some(unit.into());
        self
    }
}

/// 二进制数据数组
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BinaryDataArray {
    /// 数组长度
    pub length: usize,
    /// 编码类型
    pub encoding: BinaryDataEncoding,
    /// 压缩类型
    pub compression: Option<CompressionType>,
    /// 精度（浮点数位数）
    pub precision: Option<u8>,
    /// 原始数据（base64编码）
    pub data: Vec<u8>,
}

/// 压缩类型
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CompressionType {
    /// 无压缩
    None,
    /// Zlib压缩
    Zlib,
    /// Gzip压缩
    Gzip,
}

impl CompressionType {
    /// 从字符串解析压缩类型
    pub fn from_string(compression: &str) -> ParseResult<Self> {
        match compression.to_lowercase().as_str() {
            "none" | "no compression" => Ok(CompressionType::None),
            "zlib" => Ok(CompressionType::Zlib),
            "gzip" => Ok(CompressionType::Gzip),
            _ => Err(ParseError::InvalidFormat(format!(
                "Unknown compression type: {}", compression
            ))),
        }
    }
}

impl BinaryDataArray {
    /// 创建新的二进制数据数组
    pub fn new(length: usize, encoding: BinaryDataEncoding, data: Vec<u8>) -> Self {
        Self {
            length,
            encoding,
            compression: None,
            precision: None,
            data,
        }
    }

    /// 设置压缩类型
    pub fn with_compression(mut self, compression: CompressionType) -> Self {
        self.compression = Some(compression);
        self
    }

    /// 设置精度
    pub fn with_precision(mut self, precision: u8) -> Self {
        self.precision = Some(precision);
        self
    }

    /// 解码为f64数组
    pub fn decode_f64(&self) -> ParseResult<Vec<f64>> {
        if !self.encoding.is_float() {
            return Err(ParseError::InvalidDataType {
                expected: "float encoding".to_string(),
                actual: format!("{:?}", self.encoding),
            });
        }

        let decompressed = self.decompress()?;
        self.decode_to_f64(&decompressed)
    }

    /// 解码为f32数组
    pub fn decode_f32(&self) -> ParseResult<Vec<f32>> {
        if !self.encoding.is_float() {
            return Err(ParseError::InvalidDataType {
                expected: "float encoding".to_string(),
                actual: format!("{:?}", self.encoding),
            });
        }

        let decompressed = self.decompress()?;
        self.decode_to_f32(&decompressed)
    }

    /// 解码为i64数组
    pub fn decode_i64(&self) -> ParseResult<Vec<i64>> {
        if self.encoding.is_float() {
            return Err(ParseError::InvalidDataType {
                expected: "integer encoding".to_string(),
                actual: format!("{:?}", self.encoding),
            });
        }

        let decompressed = self.decompress()?;
        self.decode_to_i64(&decompressed)
    }

    /// 解码为i32数组
    pub fn decode_i32(&self) -> ParseResult<Vec<i32>> {
        if self.encoding.is_float() {
            return Err(ParseError::InvalidDataType {
                expected: "integer encoding".to_string(),
                actual: format!("{:?}", self.encoding),
            });
        }

        let decompressed = self.decompress()?;
        self.decode_to_i32(&decompressed)
    }

    /// 解压缩数据
    fn decompress(&self) -> ParseResult<Vec<u8>> {
        match self.compression {
            Some(CompressionType::None) => Ok(self.data.clone()),
            Some(CompressionType::Zlib) => {
                use flate2::read::ZlibDecoder;
                use std::io::Read;
                
                let mut decoder = ZlibDecoder::new(&self.data[..]);
                let mut decompressed = Vec::new();
                decoder.read_to_end(&mut decompressed)
                    .map_err(|e| ParseError::ZlibDecompress(e.to_string()))?;
                Ok(decompressed)
            }
            Some(CompressionType::Gzip) => {
                use flate2::read::GzDecoder;
                use std::io::Read;
                
                let mut decoder = GzDecoder::new(&self.data[..]);
                let mut decompressed = Vec::new();
                decoder.read_to_end(&mut decompressed)
                    .map_err(|e| ParseError::ZlibDecompress(e.to_string()))?;
                Ok(decompressed)
            }
            None => Ok(self.data.clone()),
        }
    }

    /// 解码为f64数组（内部方法）
    fn decode_to_f64(&self, data: &[u8]) -> ParseResult<Vec<f64>> {
        let expected_size = self.length * self.encoding.size();
        if data.len() < expected_size {
            return Err(ParseError::CorruptedData(format!(
                "Data size mismatch: expected {}, got {}", expected_size, data.len()
            )));
        }

        let mut result = Vec::with_capacity(self.length);
        let chunk_size = self.encoding.size();

        for chunk in data.chunks_exact(chunk_size) {
            let value = if self.encoding.is_little_endian() {
                match self.encoding {
                    BinaryDataEncoding::Float32Little => {
                        f32::from_le_bytes(chunk.try_into().unwrap()) as f64
                    }
                    BinaryDataEncoding::Float64Little => {
                        f64::from_le_bytes(chunk.try_into().unwrap())
                    }
                    _ => unreachable!(),
                }
            } else {
                match self.encoding {
                    BinaryDataEncoding::Float32Big => {
                        f32::from_be_bytes(chunk.try_into().unwrap()) as f64
                    }
                    BinaryDataEncoding::Float64Big => {
                        f64::from_be_bytes(chunk.try_into().unwrap())
                    }
                    _ => unreachable!(),
                }
            };
            result.push(value);
        }

        Ok(result)
    }

    /// 解码为f32数组（内部方法）
    fn decode_to_f32(&self, data: &[u8]) -> ParseResult<Vec<f32>> {
        let expected_size = self.length * self.encoding.size();
        if data.len() < expected_size {
            return Err(ParseError::CorruptedData(format!(
                "Data size mismatch: expected {}, got {}", expected_size, data.len()
            )));
        }

        let mut result = Vec::with_capacity(self.length);
        let chunk_size = self.encoding.size();

        for chunk in data.chunks_exact(chunk_size) {
            let value = if self.encoding.is_little_endian() {
                match self.encoding {
                    BinaryDataEncoding::Float32Little => {
                        f32::from_le_bytes(chunk.try_into().unwrap())
                    }
                    BinaryDataEncoding::Float64Little => {
                        f64::from_le_bytes(chunk.try_into().unwrap()) as f32
                    }
                    _ => unreachable!(),
                }
            } else {
                match self.encoding {
                    BinaryDataEncoding::Float32Big => {
                        f32::from_be_bytes(chunk.try_into().unwrap())
                    }
                    BinaryDataEncoding::Float64Big => {
                        f64::from_be_bytes(chunk.try_into().unwrap()) as f32
                    }
                    _ => unreachable!(),
                }
            };
            result.push(value);
        }

        Ok(result)
    }

    /// 解码为i64数组（内部方法）
    fn decode_to_i64(&self, data: &[u8]) -> ParseResult<Vec<i64>> {
        let expected_size = self.length * self.encoding.size();
        if data.len() < expected_size {
            return Err(ParseError::CorruptedData(format!(
                "Data size mismatch: expected {}, got {}", expected_size, data.len()
            )));
        }

        let mut result = Vec::with_capacity(self.length);
        let chunk_size = self.encoding.size();

        for chunk in data.chunks_exact(chunk_size) {
            let value = if self.encoding.is_little_endian() {
                match self.encoding {
                    BinaryDataEncoding::Int32Little => {
                        i32::from_le_bytes(chunk.try_into().unwrap()) as i64
                    }
                    BinaryDataEncoding::Int64Little => {
                        i64::from_le_bytes(chunk.try_into().unwrap())
                    }
                    _ => unreachable!(),
                }
            } else {
                match self.encoding {
                    BinaryDataEncoding::Int32Big => {
                        i32::from_be_bytes(chunk.try_into().unwrap()) as i64
                    }
                    BinaryDataEncoding::Int64Big => {
                        i64::from_be_bytes(chunk.try_into().unwrap())
                    }
                    _ => unreachable!(),
                }
            };
            result.push(value);
        }

        Ok(result)
    }

    /// 解码为i32数组（内部方法）
    fn decode_to_i32(&self, data: &[u8]) -> ParseResult<Vec<i32>> {
        let expected_size = self.length * self.encoding.size();
        if data.len() < expected_size {
            return Err(ParseError::CorruptedData(format!(
                "Data size mismatch: expected {}, got {}", expected_size, data.len()
            )));
        }

        let mut result = Vec::with_capacity(self.length);
        let chunk_size = self.encoding.size();

        for chunk in data.chunks_exact(chunk_size) {
            let value = if self.encoding.is_little_endian() {
                match self.encoding {
                    BinaryDataEncoding::Int32Little => {
                        i32::from_le_bytes(chunk.try_into().unwrap())
                    }
                    BinaryDataEncoding::Int64Little => {
                        i64::from_le_bytes(chunk.try_into().unwrap()) as i32
                    }
                    _ => unreachable!(),
                }
            } else {
                match self.encoding {
                    BinaryDataEncoding::Int32Big => {
                        i32::from_be_bytes(chunk.try_into().unwrap())
                    }
                    BinaryDataEncoding::Int64Big => {
                        i64::from_be_bytes(chunk.try_into().unwrap()) as i32
                    }
                    _ => unreachable!(),
                }
            };
            result.push(value);
        }

        Ok(result)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_binary_data_encoding() {
        let encoding = BinaryDataEncoding::from_string("32-bit float").unwrap();
        assert_eq!(encoding, BinaryDataEncoding::Float32Little);
        assert_eq!(encoding.size(), 4);
        assert!(encoding.is_float());
        assert!(encoding.is_little_endian());
    }

    #[test]
    fn test_cv_param() {
        let param = CVParam::new("MS:1000514", "m/z array", "100.0");
        assert_eq!(param.accession, "MS:1000514");
        assert_eq!(param.name, "m/z array");
        assert_eq!(param.as_string(), "100.0");
        assert_eq!(param.as_f64().unwrap(), 100.0);
        assert!(param.is_accession("MS:1000514"));
        assert!(param.is_name("m/z array"));
    }

    #[test]
    fn test_binary_data_array() {
        let data = vec![0x00, 0x00, 0x28, 0x42]; // 42.0 in f32 little endian
        let array = BinaryDataArray::new(1, BinaryDataEncoding::Float32Little, data);
        
        let decoded = array.decode_f32().unwrap();
        assert_eq!(decoded.len(), 1);
        assert_eq!(decoded[0], 42.0);
    }

    #[test]
    fn test_compression_type() {
        let compression = CompressionType::from_string("zlib").unwrap();
        assert_eq!(compression, CompressionType::Zlib);
        
        let compression = CompressionType::from_string("none").unwrap();
        assert_eq!(compression, CompressionType::None);
    }
}
