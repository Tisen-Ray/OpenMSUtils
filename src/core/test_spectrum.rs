//! 谱图测试模块

use crate::core::types::*;
use crate::core::spectrum::Spectrum;
use crate::core::CoreResult;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_spectrum_creation() -> CoreResult<()> {
        let mut spectrum = Spectrum::ms1()?;
        assert_eq!(spectrum.level, 1);
        assert_eq!(spectrum.peaks.len(), 0);
        Ok(())
    }

    #[test]
    fn test_peak_addition() -> CoreResult<()> {
        let mut spectrum = Spectrum::ms1()?;

        // 添加峰
        spectrum.add_peak(100.0, 1000.0)?;
        spectrum.add_peak(200.0, 2000.0)?;

        assert_eq!(spectrum.peaks.len(), 2);
        assert_eq!(spectrum.peaks[0], (100.0, 1000.0));
        assert_eq!(spectrum.peaks[1], (200.0, 2000.0));

        Ok(())
    }

    #[test]
    fn test_basic_operations() -> CoreResult<()> {
        let mut spectrum = Spectrum::ms1()?;

        // 添加测试峰
        spectrum.add_peak(100.0, 1000.0)?;
        spectrum.add_peak(200.0, 2000.0)?;
        spectrum.add_peak(300.0, 1500.0)?;

        // 测试总离子流
        let tic = spectrum.total_ion_current();
        assert_eq!(tic, 4500.0);

        // 测试基峰查找
        let base_peak = spectrum.base_peak();
        assert_eq!(base_peak, Some((200.0, 2000.0)));

        // 测试峰数
        assert_eq!(spectrum.peak_count(), 3);

        Ok(())
    }

    #[test]
    fn test_scan_info() -> CoreResult<()> {
        let mut spectrum = Spectrum::ms1()?;

        // 设置扫描信息
        spectrum.set_scan_number(12345)?;
        spectrum.set_retention_time(60.5)?;
        spectrum.set_drift_time(12.3)?;

        assert_eq!(spectrum.scan.scan_number, 12345);
        assert_eq!(spectrum.scan.retention_time, 60.5);
        assert_eq!(spectrum.scan.drift_time, 12.3);

        Ok(())
    }

    #[test]
    fn test_peak_sorting() -> CoreResult<()> {
        let mut spectrum = Spectrum::ms1()?;

        // 添加未排序的峰
        spectrum.add_peak(300.0, 1500.0)?;
        spectrum.add_peak(100.0, 1000.0)?;
        spectrum.add_peak(200.0, 2000.0)?;

        // 检查是否按m/z排序
        assert_eq!(spectrum.peaks[0].0, 100.0);
        assert_eq!(spectrum.peaks[1].0, 200.0);
        assert_eq!(spectrum.peaks[2].0, 300.0);

        // 测试排序方法
        spectrum.sort_peaks();
        assert_eq!(spectrum.peaks[0].0, 100.0);
        assert_eq!(spectrum.peaks[1].0, 200.0);
        assert_eq!(spectrum.peaks[2].0, 300.0);

        Ok(())
    }
}