//! MZML核心解析器
//! 
//! 这个模块提供了mzML文件的核心解析逻辑，包括XML解析和二进制数据处理

use crate::core::spectrum::{Spectrum, PrecursorInfo, ScanInfo};
use crate::core::types::*;
use crate::parsers::common::{ParseResult, ParseError, CVParam, UserParam, BinaryDataArray, BinaryDataEncoding, CompressionType};
use crate::parsers::mzml::spectrum::{MZMLSpectrum, MZMLScan, MZMLPrecursor, MZMLIsolationWindow, MZMLActivation, MZMLBinaryDataArray, MZMLScanList};
use quick_xml::events::{BytesStart, Event};
use quick_xml::reader::Reader;
use std::io::BufRead;
use std::collections::HashMap;
use std::str;

/// MZML解析器
pub struct MZMLParser {
    /// 是否启用并行处理
    parallel: bool,
    /// 线程数
    num_threads: usize,
}

impl MZMLParser {
    /// 创建新的MZML解析器
    pub fn new() -> Self {
        Self {
            parallel: false,
            num_threads: 1,
        }
    }

    /// 创建并行MZML解析器
    pub fn new_parallel(num_threads: usize) -> Self {
        Self {
            parallel: true,
            num_threads,
        }
    }

    /// 顺序解析MZML文件
    pub fn parse_sequential(&self, filename: &str) -> ParseResult<Vec<Spectrum>> {
        let file = std::fs::File::open(filename)
            .map_err(ParseError::Io)?;
        let reader = std::io::BufReader::new(file);
        
        let mut xml_reader = Reader::from_reader(reader);
        xml_reader.trim_text(true);
        
        let mut buf = Vec::new();
        let mut spectra = Vec::new();
        let mut current_element = String::new();
        let mut in_spectrum = false;
        let mut current_spectrum: Option<MZMLSpectrum> = None;

        loop {
            match xml_reader.read_event_into(&mut buf) {
                Ok(Event::Start(ref e)) => {
                    current_element = str::from_utf8(e.name().into_inner())
                        .unwrap_or("")
                        .to_string();

                    match current_element.as_str() {
                        "spectrum" => {
                            in_spectrum = true;
                            current_spectrum = Some(self.parse_spectrum_start(e)?);
                        }
                        "binaryDataArray" if in_spectrum => {
                            if let Some(ref mut spectrum) = current_spectrum {
                                let binary_array = self.parse_binary_data_array(&mut xml_reader, e)?;
                                spectrum.add_binary_data_array(binary_array);
                            }
                        }
                        "scanList" if in_spectrum => {
                            if let Some(ref mut spectrum) = current_spectrum {
                                let scan_list = self.parse_scan_list(&mut xml_reader, e)?;
                                spectrum.scan_list = scan_list;
                            }
                        }
                        "precursorList" if in_spectrum => {
                            if let Some(ref mut spectrum) = current_spectrum {
                                let precursors = self.parse_precursor_list(&mut xml_reader, e)?;
                                for precursor in precursors {
                                    spectrum.add_precursor(precursor);
                                }
                            }
                        }
                        _ => {}
                    }
                }
                Ok(Event::End(ref e)) => {
                    let element_name = str::from_utf8(e.name().into_inner())
                        .unwrap_or("");
                    
                    if element_name == "spectrum" && in_spectrum {
                        if let Some(mzml_spectrum) = current_spectrum.take() {
                            let spectrum = self.convert_mzml_to_spectrum(mzml_spectrum)?;
                            spectra.push(spectrum);
                        }
                        in_spectrum = false;
                    }
                }
                Ok(Event::Eof) => break,
                Err(e) => return Err(ParseError::Xml(e.to_string())),
                _ => {}
            }
            buf.clear();
        }

        Ok(spectra)
    }

    /// 并行解析MZML文件
    pub fn parse_parallel(&self, filename: &str, num_threads: usize) -> ParseResult<Vec<Spectrum>> {
        // 简化实现：目前使用顺序解析
        // 在实际实现中，可以将文件分块并行处理
        self.parse_sequential(filename)
    }

    /// 解析谱图开始元素
    fn parse_spectrum_start(&self, event: &BytesStart) -> ParseResult<MZMLSpectrum> {
        let mut id = String::new();
        let mut default_array_length = 0;
        let mut index = None;

        for attr in event.attributes() {
            let attr = attr.map_err(|e| ParseError::Xml(e.to_string()))?;
            let key = str::from_utf8(attr.key.into_inner()).unwrap_or("");
            let value = str::from_utf8(&attr.value).unwrap_or("");

            match key {
                "id" => id = value.to_string(),
                "defaultArrayLength" => {
                    default_array_length = value.parse()
                        .map_err(|_| ParseError::InvalidDataType {
                            expected: "integer".to_string(),
                            actual: format!("'{}'", value),
                        })?;
                }
                "index" => {
                    index = Some(value.parse().map_err(|_| {
                        ParseError::InvalidDataType {
                            expected: "integer".to_string(),
                            actual: format!("'{}'", value),
                        }
                    })?);
                }
                _ => {}
            }
        }

        Ok(MZMLSpectrum::new(id, default_array_length).with_index(index))
    }

    /// 解析二进制数据数组
    fn parse_binary_data_array<B: BufRead>(
        &self,
        reader: &mut Reader<B>,
        event: &BytesStart,
    ) -> ParseResult<MZMLBinaryDataArray> {
        let mut array = MZMLBinaryDataArray::new();
        
        // 解析属性
        for attr in event.attributes() {
            let attr = attr.map_err(|e| ParseError::Xml(e.to_string()))?;
            let key = str::from_utf8(attr.key.into_inner()).unwrap_or("");
            let value = str::from_utf8(&attr.value).unwrap_or("");

            if key == "encodedLength" {
                if let Ok(length) = value.parse::<usize>() {
                    array.length = Some(length);
                }
            }
        }

        let mut buf = Vec::new();
        let mut in_binary = false;
        let mut binary_data = String::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(ref e)) => {
                    let element_name = str::from_utf8(e.name().into_inner()).unwrap_or("");
                    
                    match element_name {
                        "cvParam" => {
                            let cv_param = self.parse_cv_param(e)?;
                            array.add_cv_param(cv_param);
                        }
                        "userParam" => {
                            let user_param = self.parse_user_param(e)?;
                            array.add_user_param(user_param);
                        }
                        "binary" => {
                            in_binary = true;
                        }
                        _ => {}
                    }
                }
                Ok(Event::Text(ref e)) => {
                    if in_binary {
                        binary_data.push_str(str::from_utf8(e).unwrap_or(""));
                    }
                }
                Ok(Event::End(ref e)) => {
                    let element_name = str::from_utf8(e.name().into_inner()).unwrap_or("");
                    
                    if element_name == "binary" {
                        in_binary = false;
                    } else if element_name == "binaryDataArray" {
                        break;
                    }
                }
                Err(e) => return Err(ParseError::Xml(e.to_string())),
                _ => {}
            }
            buf.clear();
        }

        // 解析二进制数据
        if !binary_data.is_empty() {
            let binary_array = self.parse_binary_data(&array, &binary_data)?;
            array.set_binary(binary_array);
        }

        Ok(array)
    }

    /// 解析扫描列表
    fn parse_scan_list<B: BufRead>(
        &self,
        reader: &mut Reader<B>,
        _event: &BytesStart,
    ) -> ParseResult<MZMLScanList> {
        let mut scan_list = MZMLScanList::new();
        let mut buf = Vec::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(ref e)) => {
                    let element_name = str::from_utf8(e.name().into_inner()).unwrap_or("");
                    
                    if element_name == "scan" {
                        let scan = self.parse_scan(reader, e)?;
                        scan_list.add_scan(scan);
                    }
                }
                Ok(Event::End(ref e)) => {
                    let element_name = str::from_utf8(e.name().into_inner()).unwrap_or("");
                    
                    if element_name == "scanList" {
                        break;
                    }
                }
                Err(e) => return Err(ParseError::Xml(e.to_string())),
                _ => {}
            }
            buf.clear();
        }

        Ok(scan_list)
    }

    /// 解析扫描
    fn parse_scan<B: BufRead>(
        &self,
        reader: &mut Reader<B>,
        event: &BytesStart,
    ) -> ParseResult<MZMLScan> {
        let mut scan = MZMLScan::new();
        
        // 解析属性
        for attr in event.attributes() {
            let attr = attr.map_err(|e| ParseError::Xml(e.to_string()))?;
            let key = str::from_utf8(attr.key.into_inner()).unwrap_or("");
            let value = str::from_utf8(&attr.value).unwrap_or("");

            match key {
                "id" => scan.id = Some(value.to_string()),
                "scanNumber" => {
                    scan.scan_number = Some(value.parse().map_err(|_| {
                        ParseError::InvalidDataType {
                            expected: "integer".to_string(),
                            actual: format!("'{}'", value),
                        }
                    })?);
                }
                _ => {}
            }
        }

        let mut buf = Vec::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(ref e)) => {
                    let element_name = str::from_utf8(e.name().into_inner()).unwrap_or("");
                    
                    match element_name {
                        "cvParam" => {
                            let cv_param = self.parse_cv_param(e)?;
                            scan.add_cv_param(cv_param);
                        }
                        "userParam" => {
                            let user_param = self.parse_user_param(e)?;
                            scan.add_user_param(user_param);
                        }
                        _ => {}
                    }
                }
                Ok(Event::End(ref e)) => {
                    let element_name = str::from_utf8(e.name().into_inner()).unwrap_or("");
                    
                    if element_name == "scan" {
                        break;
                    }
                }
                Err(e) => return Err(ParseError::Xml(e.to_string())),
                _ => {}
            }
            buf.clear();
        }

        Ok(scan)
    }

    /// 解析前体离子列表
    fn parse_precursor_list<B: BufRead>(
        &self,
        reader: &mut Reader<B>,
        _event: &BytesStart,
    ) -> ParseResult<Vec<MZMLPrecursor>> {
        let mut precursors = Vec::new();
        let mut buf = Vec::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(ref e)) => {
                    let element_name = str::from_utf8(e.name().into_inner()).unwrap_or("");
                    
                    if element_name == "precursor" {
                        let precursor = self.parse_precursor(reader, e)?;
                        precursors.push(precursor);
                    }
                }
                Ok(Event::End(ref e)) => {
                    let element_name = str::from_utf8(e.name().into_inner()).unwrap_or("");
                    
                    if element_name == "precursorList" {
                        break;
                    }
                }
                Err(e) => return Err(ParseError::Xml(e.to_string())),
                _ => {}
            }
            buf.clear();
        }

        Ok(precursors)
    }

    /// 解析前体离子
    fn parse_precursor<B: BufRead>(
        &self,
        reader: &mut Reader<B>,
        event: &BytesStart,
    ) -> ParseResult<MZMLPrecursor> {
        let mut precursor = MZMLPrecursor::new();
        
        // 解析属性
        for attr in event.attributes() {
            let attr = attr.map_err(|e| ParseError::Xml(e.to_string()))?;
            let key = str::from_utf8(attr.key.into_inner()).unwrap_or("");
            let value = str::from_utf8(&attr.value).unwrap_or("");

            if key == "spectrumRef" {
                precursor.spectrum_ref = Some(value.to_string());
            }
        }

        let mut buf = Vec::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(ref e)) => {
                    let element_name = str::from_utf8(e.name().into_inner()).unwrap_or("");
                    
                    match element_name {
                        "cvParam" => {
                            let cv_param = self.parse_cv_param(e)?;
                            precursor.add_cv_param(cv_param);
                        }
                        "userParam" => {
                            let user_param = self.parse_user_param(e)?;
                            precursor.add_user_param(user_param);
                        }
                        "isolationWindow" => {
                            let window = self.parse_isolation_window(reader, e)?;
                            precursor.add_isolation_window(window);
                        }
                        "activation" => {
                            let activation = self.parse_activation(reader, e)?;
                            precursor.set_activation(activation);
                        }
                        _ => {}
                    }
                }
                Ok(Event::End(ref e)) => {
                    let element_name = str::from_utf8(e.name().into_inner()).unwrap_or("");
                    
                    if element_name == "precursor" {
                        break;
                    }
                }
                Err(e) => return Err(ParseError::Xml(e.to_string())),
                _ => {}
            }
            buf.clear();
        }

        Ok(precursor)
    }

    /// 解析分离窗口
    fn parse_isolation_window<B: BufRead>(
        &self,
        reader: &mut Reader<B>,
        _event: &BytesStart,
    ) -> ParseResult<MZMLIsolationWindow> {
        let mut window = MZMLIsolationWindow::new();
        let mut buf = Vec::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(ref e)) => {
                    let element_name = str::from_utf8(e.name().into_inner()).unwrap_or("");
                    
                    match element_name {
                        "cvParam" => {
                            let cv_param = self.parse_cv_param(e)?;
                            window.add_cv_param(cv_param);
                        }
                        "userParam" => {
                            let user_param = self.parse_user_param(e)?;
                            window.add_user_param(user_param);
                        }
                        _ => {}
                    }
                }
                Ok(Event::End(ref e)) => {
                    let element_name = str::from_utf8(e.name().into_inner()).unwrap_or("");
                    
                    if element_name == "isolationWindow" {
                        break;
                    }
                }
                Err(e) => return Err(ParseError::Xml(e.to_string())),
                _ => {}
            }
            buf.clear();
        }

        Ok(window)
    }

    /// 解析激活信息
    fn parse_activation<B: BufRead>(
        &self,
        reader: &mut Reader<B>,
        _event: &BytesStart,
    ) -> ParseResult<MZMLActivation> {
        let mut activation = MZMLActivation::new();
        let mut buf = Vec::new();

        loop {
            match reader.read_event_into(&mut buf) {
                Ok(Event::Start(ref e)) => {
                    let element_name = str::from_utf8(e.name().into_inner()).unwrap_or("");
                    
                    match element_name {
                        "cvParam" => {
                            let cv_param = self.parse_cv_param(e)?;
                            activation.add_cv_param(cv_param);
                        }
                        "userParam" => {
                            let user_param = self.parse_user_param(e)?;
                            activation.add_user_param(user_param);
                        }
                        _ => {}
                    }
                }
                Ok(Event::End(ref e)) => {
                    let element_name = str::from_utf8(e.name().into_inner()).unwrap_or("");
                    
                    if element_name == "activation" {
                        break;
                    }
                }
                Err(e) => return Err(ParseError::Xml(e.to_string())),
                _ => {}
            }
            buf.clear();
        }

        Ok(activation)
    }

    /// 解析CV参数
    fn parse_cv_param(&self, event: &BytesStart) -> ParseResult<CVParam> {
        let mut accession = String::new();
        let mut name = String::new();
        let mut value = String::new();
        let mut unit = None;

        for attr in event.attributes() {
            let attr = attr.map_err(|e| ParseError::Xml(e.to_string()))?;
            let key = str::from_utf8(attr.key.into_inner()).unwrap_or("");
            let value_str = str::from_utf8(&attr.value).unwrap_or("");

            match key {
                "accession" => accession = value_str.to_string(),
                "name" => name = value_str.to_string(),
                "value" => value = value_str.to_string(),
                "unitCvRef" | "unitName" => unit = Some(value_str.to_string()),
                _ => {}
            }
        }

        let mut cv_param = CVParam::new(accession, name, value);
        if let Some(unit_str) = unit {
            cv_param = cv_param.with_unit(unit_str);
        }

        Ok(cv_param)
    }

    /// 解析用户参数
    fn parse_user_param(&self, event: &BytesStart) -> ParseResult<UserParam> {
        let mut name = String::new();
        let mut value = String::new();
        let mut unit = None;

        for attr in event.attributes() {
            let attr = attr.map_err(|e| ParseError::Xml(e.to_string()))?;
            let key = str::from_utf8(attr.key.into_inner()).unwrap_or("");
            let value_str = str::from_utf8(&attr.value).unwrap_or("");

            match key {
                "name" => name = value_str.to_string(),
                "value" => value = value_str.to_string(),
                "unitCvRef" | "unitName" => unit = Some(value_str.to_string()),
                _ => {}
            }
        }

        let mut user_param = UserParam::new(name, value);
        if let Some(unit_str) = unit {
            user_param = user_param.with_unit(unit_str);
        }

        Ok(user_param)
    }

    /// 解析二进制数据
    fn parse_binary_data(&self, array: &MZMLBinaryDataArray, binary_data: &str) -> ParseResult<BinaryDataArray> {
        // 解码base64
        let decoded_data = base64::decode(binary_data.trim())?;
        
        // 获取编码类型
        let mut encoding = BinaryDataEncoding::Float64Little;
        let mut compression = None;
        let mut length = array.length.unwrap_or(0);

        for param in &array.cv_params {
            if param.is_accession("MS:1000523") { // 64-bit float
                encoding = BinaryDataEncoding::Float64Little;
            } else if param.is_accession("MS:1000521") { // 32-bit float
                encoding = BinaryDataEncoding::Float32Little;
            } else if param.is_accession("MS:1000576") { // zlib compression
                compression = Some(CompressionType::Zlib);
            } else if param.is_accession("MS:1000574") { // no compression
                compression = Some(CompressionType::None);
            }
        }

        let mut binary_array = BinaryDataArray::new(length, encoding, decoded_data);
        if let Some(comp) = compression {
            binary_array = binary_array.with_compression(comp);
        }

        Ok(binary_array)
    }

    /// 将MZML谱图转换为标准Spectrum
    fn convert_mzml_to_spectrum(&self, mzml_spectrum: MZMLSpectrum) -> ParseResult<Spectrum> {
        let ms_level = mzml_spectrum.get_ms_level()?;
        let peaks = mzml_spectrum.get_peaks()?;
        
        let mut spectrum = Spectrum::new(ms_level)?;
        
        // 添加质谱峰
        for (mz, intensity) in peaks {
            spectrum.add_peak(mz, intensity)?;
        }

        // 设置扫描信息
        let mut scan_info = ScanInfo::default();
        if let Some(scan) = mzml_spectrum.scan_list.first_scan() {
            if let Some(scan_number) = scan.scan_number {
                scan_info.scan_number = scan_number;
            }
            if let Some(rt) = scan.get_scan_start_time() {
                scan_info.retention_time = rt;
            }
            if let Some(window) = scan.get_scan_window() {
                scan_info.scan_window = window;
            }
        }
        spectrum.set_scan_info(scan_info);

        // 设置前体离子信息（仅MS2+）
        if ms_level > 1 {
            for precursor in &mzml_spectrum.precursors {
                let mut precursor_info = PrecursorInfo::default();
                
                if let Some(mz) = precursor.get_precursor_mz() {
                    precursor_info.mz = mz;
                }
                if let Some(charge) = precursor.get_precursor_charge() {
                    precursor_info.charge = charge;
                }
                if let Some(intensity) = precursor.get_precursor_intensity() {
                    precursor_info.intensity = Some(intensity);
                }
                
                // 获取激活信息
                if let Some(activation) = &precursor.activation {
                    if let Some(method) = activation.get_activation_method() {
                        precursor_info.activation_method = method;
                    }
                    if let Some(energy) = activation.get_collision_energy() {
                        precursor_info.activation_energy = energy;
                    }
                }

                // 获取分离窗口
                for window in &precursor.isolation_windows {
                    if let Some(target_mz) = window.get_isolation_window_target_mz() {
                        precursor_info.isolation_window = (target_mz, target_mz);
                    }
                }

                spectrum.set_precursor(precursor_info);
                break; // 只取第一个前体离子
            }
        }

        // 添加额外信息
        if let Some(spectrum_type) = mzml_spectrum.get_spectrum_type() {
            spectrum.add_additional_info("spectrum_type".to_string(), spectrum_type)?;
        }
        if let Some(tic) = mzml_spectrum.get_total_ion_current() {
            spectrum.add_additional_info("total_ion_current".to_string(), tic.to_string())?;
        }
        if let Some(base_peak_mz) = mzml_spectrum.get_base_peak_mz() {
            spectrum.add_additional_info("base_peak_mz".to_string(), base_peak_mz.to_string())?;
        }
        if let Some(base_peak_intensity) = mzml_spectrum.get_base_peak_intensity() {
            spectrum.add_additional_info("base_peak_intensity".to_string(), base_peak_intensity.to_string())?;
        }

        Ok(spectrum)
    }
}

// 为MZMLSpectrum添加with_index方法
impl MZMLSpectrum {
    pub fn with_index(mut self, index: Option<usize>) -> Self {
        self.index = index;
        self
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parser_creation() {
        let parser = MZMLParser::new();
        assert!(!parser.parallel);
        assert_eq!(parser.num_threads, 1);

        let parallel_parser = MZMLParser::new_parallel(4);
        assert!(parallel_parser.parallel);
        assert_eq!(parallel_parser.num_threads, 4);
    }

    #[test]
    fn test_cv_param_parsing() {
        let parser = MZMLParser::new();
        
        // 创建模拟的XML事件
        let xml = r#"<cvParam accession="MS:1000511" name="ms level" value="2"/>"#;
        let mut reader = Reader::from_str(xml);
        let mut buf = Vec::new();
        
        if let Ok(Event::Start(e)) = reader.read_event_into(&mut buf) {
            let cv_param = parser.parse_cv_param(&e).unwrap();
            assert_eq!(cv_param.accession, "MS:1000511");
            assert_eq!(cv_param.name, "ms level");
            assert_eq!(cv_param.value, "2");
        }
    }
}
