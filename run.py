#!/usr/bin/env python3
"""
上市公司财务对比分析系统 - 启动脚本
GitHub Codespace 专用

功能：
1. 检查必要依赖
2. 启动主程序
3. 提供友好的错误提示
"""

import sys
import subprocess
import os

def check_dependencies():
    """检查必要的 Python 包是否已安装"""
    required_packages = ['akshare', 'pandas', 'numpy', 'matplotlib']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    return missing

def main():
    print("=" * 60)
    print("   📊 上市公司财务对比分析系统")
    print("=" * 60)
    
    # 检查依赖
    print("\n🔍 检查系统依赖...")
    missing = check_dependencies()
    
    if missing:
        print(f"❌ 缺少必要的包: {', '.join(missing)}")
        print("正在尝试自动安装...")
        
        # 尝试安装缺失的包
        for package in missing:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ 已安装 {package}")
            except Exception as e:
                print(f"❌ 安装 {package} 失败: {e}")
                return
    
    # 检查主程序文件是否存在
    main_file = "12.12.2.py"
    if not os.path.exists(main_file):
        print(f"❌ 找不到主程序文件: {main_file}")
        print("请确保 '12.12.2.py' 在同一个目录下")
        return
    
    print("\n✅ 环境检查通过")
    print("\n📋 使用说明:")
    print("   • 输入公司名称（如：茅台）或代码（如：600519）")
    print("   • 多个公司用逗号分隔")
    print("   • 示例：贵州茅台, 泸州老窖")
    print("\n⚠️  注意：数据获取需要网络连接，首次运行可能较慢")
    print("-" * 60)
    
    # 询问是否继续
    try:
        input("\n按回车键开始运行，或按 Ctrl+C 取消...")
    except KeyboardInterrupt:
        print("\n\n👋 程序已取消")
        return
    
    # 运行主程序
    print("\n🚀 启动主程序...")
    print("-" * 60)
    try:
        # 直接导入并运行主程序
        import importlib.util
        spec = importlib.util.spec_from_file_location("main_module", main_file)
        module = importlib.util.module_from_spec(spec)
        
        # 重定向到当前模块的 __name__
        original_name = module.__name__
        module.__name__ = "__main__"
        
        # 执行模块
        spec.loader.exec_module(module)
        
        # 恢复原始名称
        module.__name__ = original_name
        
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")
        print("\n💡 备用方案：尝试直接运行...")
        try:
            subprocess.run([sys.executable, main_file])
        except Exception as e2:
            print(f"❌ 备用方案也失败: {e2}")
            print("\n🔧 请检查：")
            print("   1. 代码文件是否完整")
            print("   2. 网络连接是否正常")
            print("   3. 尝试手动运行: python 12.12.2.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
    except Exception as e:
        print(f"\n💥 未预期的错误: {e}")
        print("\n📞 请将错误信息提供给开发者")
