//! 编码/解码工具
//!
//! 提供高效的质谱数据编码和解码功能，支持base64、zlib等格式

use crate::core::{Spectrum, CoreResult};
use crate::core::types::*;
use crate::parsers::common::{BinaryDataArray, BinaryDataEncoding, CompressionType};
use base64::{Engine as _, engine::general_purpose};
use std::io::Write;

/// 编码器
pub struct Encoder {
    /// 默认编码类型
    default_encoding: BinaryDataEncoding,
    /// 默认压缩类型
    default_compression: Option<CompressionType>,
}

impl Encoder {
    /// 创建新的编码器
    pub fn new() -> Self {
        Self {
            default_encoding: BinaryDataEncoding::Float64Little,
            default_compression: Some(CompressionType::Zlib),
        }
    }

    /// 设置默认编码
    pub fn with_encoding(mut self, encoding: BinaryDataEncoding) -> Self {
        self.default_encoding = encoding;
        self
    }

    /// 设置默认压缩
    pub fn with_compression(mut self, compression: Option<CompressionType>) -> Self {
        self.default_compression = compression;
        self
    }

    /// 编码m/z数组
    pub fn encode_mz_array(&self, mz_values: &[f64]) -> CoreResult<BinaryDataArray> {
        self.encode_float_array(mz_values, self.default_encoding)
    }

    /// 编码强度数组
    pub fn encode_intensity_array(&self, intensity_values: &[f64]) -> CoreResult<BinaryDataArray> {
        self.encode_float_array(intensity_values, self.default_encoding)
    }

    /// 编码浮点数组
    pub fn encode_float_array(&self, values: &[f64], encoding: BinaryDataEncoding) -> CoreResult<BinaryDataArray> {
        let mut data = Vec::with_capacity(values.len() * encoding.size());

        for &value in values {
            match encoding {
                BinaryDataEncoding::Float32Little => {
                    let bytes = (value as f32).to_le_bytes();
                    data.extend_from_slice(&bytes);
                }
                BinaryDataEncoding::Float64Little => {
                    let bytes = value.to_le_bytes();
                    data.extend_from_slice(&bytes);
                }
                BinaryDataEncoding::Float32Big => {
                    let bytes = (value as f32).to_be_bytes();
                    data.extend_from_slice(&bytes);
                }
                BinaryDataEncoding::Float64Big => {
                    let bytes = value.to_be_bytes();
                    data.extend_from_slice(&bytes);
                }
                _ => {
                    return Err(CoreError::InvalidFormat(
                        "Unsupported encoding for float data".to_string()
                    ));
                }
            }
        }

        // 应用压缩
        if let Some(compression) = self.default_compression {
            data = self.compress_data(&data, compression)?;
        }

        let mut array = BinaryDataArray::new(values.len(), encoding, data);
        array.compression = self.default_compression;

        Ok(array)
    }

    /// 编码整数数组
    pub fn encode_int_array(&self, values: &[i64], encoding: BinaryDataEncoding) -> CoreResult<BinaryDataArray> {
        let mut data = Vec::with_capacity(values.len() * encoding.size());

        for &value in values {
            match encoding {
                BinaryDataEncoding::Int32Little => {
                    let bytes = (value as i32).to_le_bytes();
                    data.extend_from_slice(&bytes);
                }
                BinaryDataEncoding::Int64Little => {
                    let bytes = value.to_le_bytes();
                    data.extend_from_slice(&bytes);
                }
                BinaryDataEncoding::Int32Big => {
                    let bytes = (value as i32).to_be_bytes();
                    data.extend_from_slice(&bytes);
                }
                BinaryDataEncoding::Int64Big => {
                    let bytes = value.to_be_bytes();
                    data.extend_from_slice(&bytes);
                }
                _ => {
                    return Err(CoreError::InvalidFormat(
                        "Unsupported encoding for integer data".to_string()
                    ));
                }
            }
        }

        // 应用压缩
        if let Some(compression) = self.default_compression {
            data = self.compress_data(&data, compression)?;
        }

        let mut array = BinaryDataArray::new(values.len(), encoding, data);
        array.compression = self.default_compression;

        Ok(array)
    }

    /// 压缩数据
    fn compress_data(&self, data: &[u8], compression: CompressionType) -> CoreResult<Vec<u8>> {
        match compression {
            CompressionType::None => Ok(data.to_vec()),
            CompressionType::Zlib => {
                let mut encoder = flate2::write::ZlibEncoder::new(Vec::new(), flate2::Compression::default());
                encoder.write_all(data)
                    .map_err(|e| CoreError::InvalidFormat(format!("Compression error: {}", e)))?;
                encoder.finish()
                    .map_err(|e| CoreError::InvalidFormat(format!("Compression finish error: {}", e)))
            }
            CompressionType::Gzip => {
                let mut encoder = flate2::write::GzEncoder::new(Vec::new(), flate2::Compression::default());
                encoder.write_all(data)
                    .map_err(|e| CoreError::InvalidFormat(format!("Compression error: {}", e)))?;
                encoder.finish()
                    .map_err(|e| CoreError::InvalidFormat(format!("Compression finish error: {}", e)))
            }
        }
    }

    /// 编码为base64字符串
    pub fn encode_to_base64(&self, data: &[u8]) -> String {
        general_purpose::STANDARD.encode(data)
    }

    /// 编码谱图为二进制格式
    pub fn encode_spectrum(&self, spectrum: &Spectrum) -> CoreResult<EncodedSpectrum> {
        let mz_array = self.encode_mz_array(&spectrum.peaks.iter().map(|(mz, _)| *mz).collect::<Vec<_>>())?;
        let intensity_array = self.encode_intensity_array(&spectrum.peaks.iter().map(|(_, intensity)| *intensity).collect::<Vec<_>>())?;

        Ok(EncodedSpectrum {
            level: spectrum.level,
            scan_number: spectrum.scan.scan_number,
            retention_time: spectrum.scan.retention_time,
            drift_time: spectrum.scan.drift_time,
            mz_array,
            intensity_array,
        })
    }
}

/// 解码器
pub struct Decoder {
    /// 默认编码类型
    default_encoding: BinaryDataEncoding,
}

impl Decoder {
    /// 创建新的解码器
    pub fn new() -> Self {
        Self {
            default_encoding: BinaryDataEncoding::Float64Little,
        }
    }

    /// 设置默认编码
    pub fn with_encoding(mut self, encoding: BinaryDataEncoding) -> Self {
        self.default_encoding = encoding;
        self
    }

    /// 解码m/z数组
    pub fn decode_mz_array(&self, array: &BinaryDataArray) -> CoreResult<Vec<f64>> {
        array.decode_f64()
            .map_err(|_| CoreError::InvalidFormat("Failed to decode m/z array".to_string()))
    }

    /// 解码强度数组
    pub fn decode_intensity_array(&self, array: &BinaryDataArray) -> CoreResult<Vec<f64>> {
        array.decode_f64()
            .map_err(|_| CoreError::InvalidFormat("Failed to decode intensity array".to_string()))
    }

    /// 从base64解码
    pub fn decode_from_base64(&self, encoded: &str) -> CoreResult<Vec<u8>> {
        general_purpose::STANDARD.decode(encoded)
            .map_err(|e| CoreError::InvalidFormat(format!("Base64 decode error: {}", e)))
    }

    /// 解码谱图
    pub fn decode_spectrum(&self, encoded: &EncodedSpectrum) -> CoreResult<Spectrum> {
        let mz_values = self.decode_mz_array(&encoded.mz_array)?;
        let intensity_values = self.decode_intensity_array(&encoded.intensity_array)?;

        if mz_values.len() != intensity_values.len() {
            return Err(CoreError::InvalidFormat(
                "m/z and intensity arrays have different lengths".to_string()
            ));
        }

        let mut spectrum = match encoded.level {
            1 => Spectrum::ms1()?,
            2 => Spectrum::ms2()?,
            _ => return Err(CoreError::InvalidFormat(
                format!("Unsupported MS level: {}", encoded.level)
            )),
        };

        spectrum.set_scan_number(encoded.scan_number);
        if encoded.retention_time > 0.0 {
            spectrum.set_retention_time(encoded.retention_time)?;
        }
        if encoded.drift_time > 0.0 {
            spectrum.set_drift_time(encoded.drift_time)?;
        }

        // 添加峰数据
        for (mz, intensity) in mz_values.iter().zip(intensity_values.iter()) {
            spectrum.add_peak(*mz, *intensity)?;
        }

        Ok(spectrum)
    }

    /// 批量解码谱图
    pub fn batch_decode_spectra(&self, encoded_spectra: &[EncodedSpectrum]) -> CoreResult<Vec<Spectrum>> {
        let mut spectra = Vec::with_capacity(encoded_spectra.len());

        for encoded in encoded_spectra {
            spectra.push(self.decode_spectrum(encoded)?);
        }

        Ok(spectra)
    }
}

/// 编码后的谱图
#[derive(Debug, Clone)]
pub struct EncodedSpectrum {
    pub level: u8,
    pub scan_number: u32,
    pub retention_time: f64,
    pub drift_time: f64,
    pub mz_array: BinaryDataArray,
    pub intensity_array: BinaryDataArray,
}

impl Default for Encoder {
    fn default() -> Self {
        Self::new()
    }
}

impl Default for Decoder {
    fn default() -> Self {
        Self::new()
    }
}

/// 编码/解码统计信息
#[derive(Debug, Clone)]
pub struct EncodingStats {
    pub original_size: usize,
    pub compressed_size: usize,
    pub compression_ratio: f64,
    pub encoding_time_ms: u64,
    pub decoding_time_ms: u64,
}

impl EncodingStats {
    /// 计算压缩比
    pub fn compression_ratio(&self) -> f64 {
        if self.original_size > 0 {
            self.compressed_size as f64 / self.original_size as f64
        } else {
            1.0
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::spectrum::Spectrum;

    #[test]
    fn test_encoder_creation() {
        let encoder = Encoder::new();
        assert!(matches!(encoder.default_encoding, BinaryDataEncoding::Float64Little));
        assert!(encoder.default_compression.is_some());
    }

    #[test]
    fn test_base64_encoding() {
        let encoder = Encoder::new();
        let data = b"Hello, World!";
        let encoded = encoder.encode_to_base64(data);
        let decoded = general_purpose::STANDARD.decode(encoded).unwrap();
        assert_eq!(data, decoded.as_slice());
    }

    #[test]
    fn test_spectrum_encoding_decoding() {
        let mut spectrum = Spectrum::ms1().unwrap();
        spectrum.add_peak(100.0, 1000.0).unwrap();
        spectrum.add_peak(200.0, 2000.0).unwrap();

        let encoder = Encoder::new();
        let decoder = Decoder::new();

        let encoded = encoder.encode_spectrum(&spectrum).unwrap();
        let decoded = decoder.decode_spectrum(&encoded).unwrap();

        assert_eq!(decoded.level, spectrum.level);
        assert_eq!(decoded.peaks().len(), spectrum.peaks().len());
        assert_eq!(decoded.peaks()[0].0, 100.0);
        assert_eq!(decoded.peaks()[0].1, 1000.0);
    }

    #[test]
    fn test_batch_decode() {
        let mut spectrum1 = Spectrum::ms1().unwrap();
        spectrum1.add_peak(100.0, 1000.0).unwrap();

        let mut spectrum2 = Spectrum::ms1().unwrap();
        spectrum2.add_peak(200.0, 2000.0).unwrap();

        let encoder = Encoder::new();
        let decoder = Decoder::new();

        let encoded1 = encoder.encode_spectrum(&spectrum1).unwrap();
        let encoded2 = encoder.encode_spectrum(&spectrum2).unwrap();

        let decoded = decoder.batch_decode_spectra(&[encoded1, encoded2]).unwrap();
        assert_eq!(decoded.len(), 2);
    }
}
