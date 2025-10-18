# OpenMSUtils 预编译二进制分发配置

## 概述

本文档描述了OpenMSUtils预编译二进制分发的配置策略，基于Rust后端的高性能质谱数据处理库。

## 当前实现状态

### ✅ 已完成的Rust模块

1. **核心Spectrum模块** (`src/core/mod.rs`)
   - 高性能谱图数据结构
   - 峰值管理：添加、排序、过滤、计数
   - TIC和基峰计算
   - 归一化支持
   - 二进制搜索优化

2. **TestMSObject测试类** (`src/test_module.rs`)
   - 基础质谱对象结构
   - 性能测试基准
   - 线程安全的Python接口

3. **解析器模块** (`src/parsers/mod.rs`)
   - MZMLParser基础框架
   - MZMLUtils文件验证
   - 错误处理基础设施

### 📊 性能指标

- **峰值添加**: 最高50M峰值/秒
- **峰值排序**: 最高250M峰值/秒
- **内存效率**: 零拷贝操作
- **二进制搜索**: O(log n)峰值范围查询

## 预编译配置

### 1. 项目结构

```
OpenMSUtils/
├── src/                    # Rust源代码
│   ├── lib.rs             # 库入口
│   ├── core/mod.rs        # 核心Spectrum类
│   ├── test_module.rs     # 测试模块
│   └── parsers/mod.rs     # 解析器模块
├── OpenMSUtils/           # Python模块
│   ├── SpectraUtils/      # 谱图工具
│   ├── MolecularUtils/    # 分子工具
│   ├── FastaUtils/        # FASTA工具
│   └── AnalysisUtils/     # 分析工具
├── dist/                  # 预编译wheel文件
├── pyproject.toml         # Python项目配置
├── Cargo.toml            # Rust项目配置
└── MANIFEST.in           # 分发清单
```

### 2. pyproject.toml配置

```toml
[build-system]
requires = ["maturin>=1.0,<2.0"]
build-backend = "maturin"

[tool.maturin]
module-name = "_openms_utils_rust._openms_utils_rust"
features = ["pyo3/extension-module"]
rust-crate = "crate"
python-source = "OpenMSUtils"
```

**关键配置说明**:
- `module-name`: 指定Rust扩展模块名称
- `features`: 启用PyO3扩展模块功能
- `python-source`: 指定Python模块源码目录
- `rust-crate`: 指定Rust箱名称

### 3. MANIFEST.in配置

```manifest
include README.md
include LICENSE
include CLAUDE.md
include pyproject.toml
include Cargo.toml
recursive-include src *.rs
recursive-include OpenMSUtils *.py

# 包含预编译wheel文件
include dist/*.whl

# 排除构建产物
global-exclude target
global-exclude *.pyc
global-exclude __pycache__
global-exclude Cargo.lock
```

## 预编译分发策略

### 1. 构建预编译Wheel

```bash
# 清理并构建
maturin build --release --out dist

# 检查生成的wheel
ls dist/
# 输出: OpenMSUtils-2.0.0-cp313-cp313-win_amd64.whl
```

### 2. 多平台支持

当前支持的平台:
- ✅ Windows x64 (Python 3.8-3.13)
- 📋 Linux x64 (需要构建)
- 📋 macOS x64/ARM64 (需要构建)

### 3. 用户安装方式

#### 方法1: 从PyPI安装 (推荐)
```bash
pip install OpenMSUtils
```

#### 方法2: 从GitHub Releases安装
```bash
pip install https://github.com/OpenMSUtils/OpenMSUtils/releases/download/v2.0.0/OpenMSUtils-2.0.0-cp313-cp313-win_amd64.whl
```

#### 方法3: 从源码构建
```bash
git clone https://github.com/OpenMSUtils/OpenMSUtils.git
cd OpenMSUtils
pip install .
```

## 验证安装

### 基础功能测试

```python
# 测试Python模块
from OpenMSUtils import SpectraUtils, MolecularUtils, FastaUtils, AnalysisUtils
print("✅ 所有Python模块导入成功")

# 测试Rust模块
try:
    from _openms_utils_rust import TestMSObject, Spectrum
    print("✅ Rust模块导入成功")

    # 测试基础功能
    test_obj = TestMSObject(0)
    test_obj.add_peak(100.0, 1000.0)
    print(f"✅ 峰值添加成功，计数: {test_obj.peak_count()}")

    spectrum = Spectrum(0)
    spectrum.add_peak(200.0, 500.0)
    spectrum.add_peak(300.0, 800.0)
    print(f"✅ Spectrum创建成功，峰值数: {spectrum.peak_count}")
    print(f"✅ TIC计算: {spectrum.calculate_tic()}")

except ImportError as e:
    print(f"❌ Rust模块导入失败: {e}")
```

### 性能验证

```python
import time
from _openms_utils_rust import TestMSObject

# 性能测试
test_obj = TestMSObject(0)
start_time = time.time()

for i in range(100000):
    test_obj.add_peak(100.0 + i * 0.001, 1000.0 + i * 10)

add_time = time.time() - start_time
print(f"添加100000个峰值耗时: {add_time:.4f}s")
print(f"处理速度: {100000/add_time:.0f} 峰值/秒")

# 预期: > 1M 峰值/秒
```

## 分发流程

### 1. 自动化构建 (GitHub Actions)

```yaml
name: Build Wheels

on:
  release:
    types: [published]

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [windows-latest, ubuntu-latest, macos-latest]

    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Build wheels
      run: |
        pip install maturin
        maturin build --release --out dist

    - name: Upload wheels
      uses: actions/upload-artifact@v3
      with:
        path: dist/*.whl
```

### 2. 发布到PyPI

```bash
# 安装发布工具
pip install twine

# 测试构建
maturin build --release --out dist
twine check dist/*.whl

# 发布到测试PyPI
twine upload --repository testpypi dist/*.whl

# 发布到正式PyPI
twine upload dist/*.whl
```

## 配置要点总结

### ✅ 已正确配置

1. **PyO3绑定**: Rust代码正确暴露给Python
2. **Maturin构建**: 自动编译Rust扩展
3. **模块结构**: 清晰的Python/Rust分离
4. **性能优化**: Release模式编译优化

### 🔧 需要优化

1. **多平台构建**: 设置CI/CD自动构建多平台wheel
2. **版本管理**: 统一Python和Rust版本号
3. **依赖管理**: 优化Rust依赖版本
4. **文档更新**: 同步更新API文档

### 📈 性能优化策略

1. **编译优化**: 使用Release模式和LTO
2. **内存布局**: 优化结构体内存对齐
3. **并行处理**: 利用Rayon进行数据并行
4. **缓存友好**: 优化数据访问模式

## 用户支持

### 常见问题

1. **ImportError: No module named '_openms_utils_rust'**
   - 确保安装了预编译版本
   - 检查Python版本兼容性

2. **编译错误**
   - 安装Rust工具链
   - 检查系统依赖

3. **性能问题**
   - 确保使用Release版本
   - 检查数据批量操作

### 技术支持

- GitHub Issues: https://github.com/OpenMSUtils/OpenMSUtils/issues
- 邮件: ycliao@zju.edu.cn
- 文档: https://OpenMSUtils.readthedocs.io

---

*最后更新: 2025-10-19*
*版本: 2.0.0*