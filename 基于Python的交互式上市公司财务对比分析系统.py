import akshare as ak
import pandas as pd
import numpy as np
import warnings
import os
import time

warnings.filterwarnings('ignore')

#%% ==================== 基础配置 ====================
def setup_mac_chinese_font():
    import matplotlib.pyplot as plt
    plt.rcParams['axes.unicode_minus'] = False
    fonts = ['Arial Unicode MS', 'PingFang HK', 'SimHei', 'Heiti TC', 'Microsoft YaHei']
    for font in fonts:
        try:
            from matplotlib.font_manager import fontManager
            if font in [f.name for f in fontManager.ttflist]:
                plt.rcParams['font.sans-serif'] = [font]
                return
        except:
            continue
    plt.rcParams['font.sans-serif'] = ['sans-serif']

setup_mac_chinese_font()

# ==================== 工具函数 ====================
def print_header(title):
    print(f"\n{'-'*60}")
    print(f" {title}")
    print(f"{'-'*60}")

def print_section(title):
    print(f"\n🔹 {title}")
    print(f"{'-'*60}")

def format_value(val, indicator):
    if val is None: return "N/A"
    if any(x in indicator for x in ['率', '比', '收入']) and '周转' not in indicator:
        return f"{val:.2f}%"
    return f"{val:,.2f}"

#%% ==================== 步骤1：数据获取 ====================
def get_financial_data_by_code(code, company_name):
    try:
        df = ak.stock_financial_abstract(symbol=code)
        
        # 清洗列名
        if '指标' in df.columns:
            df['指标'] = df['指标'].astype(str).str.strip()
        
        # 智能识别日期列 (兼容 '2023-12-31' 和 '20231231')
        date_cols = []
        for col in df.columns:
            if '12-31' in str(col) or '1231' in str(col):
                date_cols.append(col)
        date_cols = sorted(date_cols, reverse=True)[:5] # 最近5年
        
        # 兜底：如果找不到年报列，找所有20开头的列
        if not date_cols:
            date_cols = sorted([c for c in df.columns if str(c).startswith('20')], reverse=True)[:5]

        indicator_map = {
            '营业收入': '营业总收入', '净利润': '归母净利润',
            '毛利率': '毛利率', '净利率': '销售净利率',
            '净资产收益率': '净资产收益率(ROE)',
            '流动比率': '流动比率', '速动比率': '速动比率', '现金比率': '现金比率',
            '资产负债率': '资产负债率', '权益乘数': '权益乘数', '产权比率': '产权比率',
            '总资产周转率': '总资产周转率', '存货周转率': '存货周转率', '流动资产周转率': '流动资产周转率',
            '经营活动现金流': '经营现金流量净额', '每股自由现金流': '每股企业自由现金流量',
            '现金流营收比': '经营性现金净流量/营业总收入'
        }
        
        result = {'公司名称': company_name, '股票代码': code}
        
        for simple_name, actual_name in indicator_map.items():
            row = df[df['指标'] == actual_name]
            values = []
            if not row.empty:
                for date_col in date_cols:
                    val = row.iloc[0].get(date_col)
                    try:
                        v = float(val) if val not in [None, '', '--'] else None
                    except: v = None
                    values.append(v)
            else:
                values = [None] * len(date_cols)
            
            result[simple_name] = {'values': values, 'years': [str(c)[:4] for c in date_cols]}
            
        return result
    except Exception as e:
        return None

def find_stock_code(user_input, stock_list):
    """
    将用户输入转换为股票代码（含交互优化）
    修复点：当匹配到多个股票时，暂停程序等待用户输入编号确认的功能
    """
    user_input = user_input.strip()
    
    # 1. 代码直接匹配 (如果输入的是6位数字)
    if user_input.isdigit() and len(user_input) == 6:
        matched = stock_list[stock_list['code'] == user_input]
        if not matched.empty:
            return matched.iloc[0]['name'], user_input
    
    # 2. 名称模糊筛选
    cleaned_input = user_input.replace(' ', '').replace('　', '')
    
    # 先筛选出所有包含关键词的行
    mask = stock_list['name'].str.contains(cleaned_input, na=False) 
    candidates_df = stock_list[mask]
    
    # 3. 尝试精确匹配 (如果名字完全一样，直接返回，不问用户)
    for _, row in candidates_df.iterrows():
        if row['name'].replace(' ', '') == cleaned_input:
            return row['name'], row['code']
    
    # 4. 收集候选名单
    candidates = []
    for _, row in candidates_df.iterrows():
        candidates.append((row['name'], row['code']))
    
    if not candidates:
        return None
    
    # 如果只找到1个，直接返回
    if len(candidates) == 1:
        return candidates[0]
    
    # 5. [核心交互逻辑恢复]：找到多个匹配，打印列表并等待用户输入
    print(f"\n   ⚠️  输入 '{user_input}' 找到多个匹配，请确认：")
    for i, (name, code) in enumerate(candidates[:5]): # 只显示前5个
        print(f"      {i+1}. {name:<10} ({code})")
    
    try:
        # 这里使用了 input()，会暂停程序等待用户操作
        choice = input(f"   👉 请输入编号 (1-{len(candidates[:5])})，回车默认选1: ")
        
        # 如果用户直接回车，默认选第一个
        if not choice.strip():
            return candidates[0] 
            
        if choice.isdigit():
            choice_num = int(choice) - 1
            if 0 <= choice_num < len(candidates[:5]):
                return candidates[choice_num]
    except:
        pass
    
    # 如果用户乱输，默认返回第一个，保证程序不崩
    return candidates[0]

def step1_main():
    print_header("上市公司财务对比系统")
    try: stock_list = ak.stock_info_a_code_name()
    except: print("❌ 网络错误"); return None

    while True:
        inp = input("\n👉 请输入对比公司 (逗号分隔): ").strip()
        if inp: break
    
    inputs = [x.strip() for x in inp.replace('，', ',').split(',') if x.strip()]
    print_section("获取数据")
    all_data = {}
    
    for item in inputs:
        res = find_stock_code(item, stock_list)
        if not res: print(f"   ❌ 未找到: {item}"); continue
        name, code = res
        print(f"   ⏳ 获取 {name} ... ", end='', flush=True)
        data = get_financial_data_by_code(code, name)
        
        is_valid = False
        if data and '营业收入' in data:
            if any(v is not None for v in data['营业收入']['values']): is_valid = True
        
        if is_valid:
            all_data[name] = data
            print("✅")
        else:
            print("❌ 无数据")
            
    return all_data

#%% ==================== 步骤2：雷达图绘制  ====================
def calculate_radar_vals(data, company, selected_years):
    # 维度映射
    map_dict = {
        '盈利': '净资产收益率', '流动': '流动比率', '偿债': '资产负债率',
        '运营': '总资产周转率', '现金': '现金流营收比'
    }
    vals = []
    for k, ind in map_dict.items():
        val = 0
        if ind in data[company]:
            data_info = data[company][ind]
            valid_vals = []
            
            # 判断是列表(多年平均)还是单个年份
            if isinstance(selected_years, list):
                for y in selected_years:
                    if y in data_info['years']:
                        idx = data_info['years'].index(y)
                        v = data_info['values'][idx]
                        if v is not None: valid_vals.append(v)
            else:
                if selected_years in data_info['years']:
                    idx = data_info['years'].index(selected_years)
                    v = data_info['values'][idx]
                    if v is not None: valid_vals.append(v)
            
            if valid_vals:
                val = sum(valid_vals) / len(valid_vals)
        vals.append(val)
    return vals

def step2_radar(all_data):
    if not all_data: return
    sample = list(all_data.keys())[0]
    years = all_data[sample]['营业收入']['years']
    
    print("\n" + "-"*30)
    print(" 🔹 步骤 2: 雷达图对比")
    print("-" * 30)

    while True:
        print("\n👇 请选择数据统计口径:")
        print(f"   1. 最新一年 ({years[0] if years else 'N/A'})")
        print(f"   2. 三年平均")
        print(f"   3. 五年平均")
        
        choice = input("\n👉 请输入编号 (按回车键默认1): ").strip()
        if choice == '2':
            selected_years = years[:3]
            year_str = "3年平均"
        elif choice == '3':
            selected_years = years
            year_str = "5年平均"
        else:
            selected_years = years[0] if years else None
            year_str = str(selected_years)

        if not selected_years:
            print("❌ 年份数据异常，跳过绘图")
            return

        print(f"⏳ 正在生成 {year_str} 雷达图...")
        
        # 绘图逻辑
        import matplotlib.pyplot as plt
        labels = ['盈利(ROE)', '流动(流动比)', '偿债(负债率)', '运营(周转率)', '现金(营收比)']
        angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
        angles += angles[:1]
        
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))
        
        # 计算最大值归一化
        raw_vals = [calculate_radar_vals(all_data, c, selected_years) for c in all_data]
        max_vals = []
        for i in range(len(labels)):
            col = [abs(row[i]) for row in raw_vals]
            m = max(col) if col else 1
            max_vals.append(m if m!=0 else 1)
            
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        for i, comp in enumerate(all_data):
            vals = raw_vals[i]
            norm = [v/m for v,m in zip(vals, max_vals)]
            norm += norm[:1]
            c = colors[i % len(colors)]
            ax.plot(angles, norm, linewidth=2, label=comp, color=c)
            ax.fill(angles, norm, alpha=0.1, color=c)
            
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels)
        ax.set_yticklabels([])
        plt.title(f"财务健康度 ({year_str})", y=1.08)
        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        plt.show()
        
        # 交互逻辑恢复
        print("\n" + "-"*40)
        print("操作选择:")
        print("   1. ✅ 继续下一步 (趋势分析)")
        print("   2. 🔄 重新选择年份绘制雷达图")
        nxt = input("\n👉 请输入 (1/2, 默认1): ").strip()
        if nxt != '2': break

#%% ==================== 步骤3：趋势分析与数据明细  ====================
def select_companies_for_trend(all_data, indicator):
    """恢复用户要求的特定公司选择逻辑"""
    # 筛选有数据的公司
    available = []
    for c in all_data:
        if indicator in all_data[c]:
            # 只要有一个非空值就算可用
            if any(v is not None for v in all_data[c][indicator]['values']):
                available.append(c)
    
    if not available:
        print("❌ 无公司有此数据"); return []
    
    if len(available) == 1: return available

    print(f"\n👇 请选择要对比 '{indicator}' 的公司:")
    for i, company in enumerate(available, 1):
        print(f"   {i}. {company}")
    print("   a. 所有公司")
    print("   d. 默认 (前3家)")
    
    choice = input(f"\n👉 请输入 (编号用逗号隔开/a/d，默认d): ").strip().lower()
    
    selected = []
    if choice == 'a':
        selected = available
    elif choice == '' or choice == 'd':
        selected = available[:3]
    else:
        try:
            idxs = [int(x)-1 for x in choice.replace('，', ',').split(',') if x.strip()]
            for i in idxs:
                if 0 <= i < len(available): selected.append(available[i])
        except:
            selected = available[:3]
    
    print(f"✅ 已选择: {', '.join(selected)}")
    return selected

def step3_trend(all_data):
    # 指标菜单定义
    menu = {
        '盈利能力': ['营业收入', '净利润', '毛利率', '净利率', '净资产收益率'],
        '流动性': ['流动比率', '速动比率', '现金比率'],
        '偿债能力': ['资产负债率', '权益乘数', '产权比率'],
        '运营效率': ['总资产周转率', '存货周转率', '流动资产周转率'],
        '现金流': ['经营活动现金流', '每股自由现金流', '现金流营收比']
    }
    
    while True:
        print("\n" + "="*40)
        print(" 📊 指标选择菜单")
        flat_inds = []
        i = 1
        for cat, inds in menu.items():
            print(f" {cat}")
            for ind in inds:
                # 简单统计数据覆盖率
                cnt = sum(1 for c in all_data if ind in all_data[c] and any(x is not None for x in all_data[c][ind]['values']))
                status = f"[{cnt}/{len(all_data)}]" if cnt>0 else "[无数据]"
                print(f"   {i}. {ind:<10} {status}")
                flat_inds.append(ind)
                i += 1
                
        c = input("\n👉 请输入指标编号 (输入 q 退出): ").strip().lower()
        if c == 'q': break
        
        try:
            target = flat_inds[int(c)-1]
        except:
            print("❌ 输入无效"); continue
            
        # 调用选择公司逻辑
        selected_comps = select_companies_for_trend(all_data, target)
        if not selected_comps: continue
        
        # 绘图逻辑
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 5))
        has_plot = False
        
        table_rows = [] 
        years_head = []
        
        for comp in selected_comps:
            if target in all_data[comp]:
                ys = all_data[comp][target]['years']
                vs = all_data[comp][target]['values']
                
                px, py = [], []
                for x, y in zip(ys[::-1], vs[::-1]):
                    if y is not None: px.append(x); py.append(y)
                
                if px:
                    ax.plot(px, py, 'o-', label=comp)
                    for x, y in zip(px, py):
                        ax.annotate(f"{y:.2f}", (x, y), xytext=(0, 8), textcoords='offset points', ha='center', fontsize=8)
                    has_plot = True
                    if not years_head: years_head = ys
                    table_rows.append((comp, vs))

        if has_plot:
            ax.set_title(f"{target} - 趋势分析")
            ax.legend()
            ax.grid(True, linestyle='--', alpha=0.5)
            plt.tight_layout()
            plt.show()
            
            # 打印数据表
            print(f"\n--- {target} 数据明细 ---")
            header = f"{'公司':<10}" + "".join([f"|{y:^10}" for y in years_head])
            print(header)
            print("-" * len(header))
            for comp, vals in table_rows:
                row = f"{comp:<10}" + "".join([f"|{format_value(v, target):^10}" for v in vals])
                print(row)
                
            # 交互操作菜单
            print("\n👇 操作: 1.导出Excel  2.继续分析  3.退出")
            op = input("👉 请输入: ").strip()
            
            if op == '1':
                try:
                    # 准备数据
                    df = pd.DataFrame()
                    df['年份'] = years_head
                    for comp, vals in table_rows: df[comp] = vals
                    
                    # === 修改开始：灵活的文件名定义逻辑 ===
                    default_name = f"{target}_财务数据.xlsx"
                    print(f"\n📂 请输入保存路径或文件名 (直接回车默认: {default_name})")
                    user_path = input("👉 路径: ").strip()
                    
                    if not user_path:
                        save_path = default_name
                    else:
                        # 自动补全后缀
                        if not user_path.lower().endswith(('.xlsx', '.xls')):
                            save_path = user_path + ".xlsx"
                        else:
                            save_path = user_path
                            
                    print(f"⏳ 正在写入: {save_path} ...")
                    df.to_excel(save_path, index=False)
                    print(f"✅ 导出成功！文件位置: {os.path.abspath(save_path)}")
                    
                    # 尝试自动打开文件 (仅限Mac/Windows)
                    try:
                        if os.name == 'nt': os.startfile(save_path)
                        else: import subprocess; subprocess.call(('open', save_path))
                    except: pass
                    # === 修改结束 ===
                    
                except Exception as e:
                    print(f"❌ 导出失败: {e}")
                    
            elif op == '3': break
        else:
            print(f"❌ 选中公司没有 {target} 数据")
#%% ==================== 主程序入口 ====================
if __name__ == "__main__":
    
    # 1. 运行第一步：数据获取
    all_data = step1_main()
    
    if all_data:
        # 2. 运行第二步：雷达图
        # 注意：这里必须用定义好的 step2_radar，而不是 step2_radar_analysis
        step2_radar(all_data)
        
        # 3. 运行第三步：趋势分析 (包含导出功能)
        # 注意：这里必须用 step3_trend，而不是 step3_trend_analysis
        # 现在的 step3_trend 函数内部已经包含了导出逻辑，不需要额外的 step4
        step3_trend(all_data)
            
    else:
        print("\n❌ 程序异常退出。")