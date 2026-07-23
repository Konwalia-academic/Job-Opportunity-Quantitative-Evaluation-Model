import math

# ===================== 全局计分函数 =====================
def logistic(x, x0, k):
    """逻辑斯蒂曲线，用于数值型指标"""
    try:
        return 1 / (1 + math.exp(-k * (x - x0)))
    except OverflowError:
        return 1.0 if (x - x0) > 0 else 0.0

def exp_decay(x, k):
    """指数衰减，用于通勤、离职率等"""
    return math.exp(-k * x)

def exp_growth(x, k, min_val=0):
    """指数增长（用于额外假期等），x>=0"""
    if x < min_val:
        return 0.0
    return 1 - math.exp(-k * x)

# ===================== 因子得分函数 =====================
def get_factor_score(fid, raw_val):
    """
    根据因子ID计算原始得分 S (0~1)
    raw_val 为已转换好的数值（或元组），None 表示完全未知
    """
    if raw_val is None:
        return 0.5

    # ---------- 维度 A ----------
    if fid == 'A1':          # raw_val 为年均结余（万元）
        return logistic(raw_val, 10.0, 0.2)   # 基准10万元结余
    if fid == 'A2':          # 灵活变更城市自由度 (0~1)
        return max(0.0, min(1.0, raw_val))
    if fid == 'A3':          # 强制调动风险系数 (0~1)
        return 1 - max(0.0, min(1.0, raw_val))
    if fid == 'A4':          # 单程通勤分钟数
        return exp_decay(raw_val, 0.018)

    # ---------- 维度 B ----------
    if fid == 'B1':          # 排名百分位 (Top 5% 输入5)
        return 1 - (raw_val / 100)
    if fid == 'B2':          # 营收增速 (0.20 表示20%)
        return logistic(raw_val, 0.10, 15)
    if fid == 'B3':          # 人才密度 (0~1)
        return max(0.0, min(1.0, raw_val))
    if fid == 'B4':          # 国际化指数 (0~1)
        return max(0.0, min(1.0, raw_val))
    if fid == 'B5':          # 主动离职率 (0~1)
        return exp_decay(raw_val, 3.0)

    # ---------- 维度 C ----------
    if fid == 'C1':          # 技能护城河年限
        return 1 - math.exp(-0.5 * raw_val)
    if fid == 'C2':          # 可迁移行业数量
        return 1 - math.exp(-0.4 * raw_val)
    if fid == 'C3':          # 行业生命周期：上行/稳定/下行已映射为 1.0/0.7/0.3
        return max(0.0, min(1.0, raw_val))
    if fid == 'C4':          # 学术溢价 (0~1)
        return max(0.0, min(1.0, raw_val))
    if fid == 'C5':          # 跳槽溢价涨幅 (0.25 表示25%)
        return logistic(raw_val, 0.15, 10)

    # ---------- 维度 D ----------
    if fid == 'D1':          # 实际时薪（元/小时），基准80元
        return logistic(raw_val, 80.0, 0.02)
    if fid == 'D2':          # 额外带薪休假天数（年假+公司假），指数增长
        return exp_growth(raw_val, 0.10)
    if fid == 'D3':          # 每周强制加班小时数
        return 1 / (1 + 0.05 * (raw_val ** 1.2))
    if fid == 'D4':          # 健康保障覆盖系数 (0~1)
        return max(0.0, min(1.0, raw_val))

    # ---------- 维度 E ----------
    if fid in ['E1', 'E2', 'E3', 'E4']:   # 所有主观评分均为 0~10
        return max(0.0, min(1.0, raw_val / 10.0))

    return 0.5

# ===================== 权重调节 =====================
def get_weights():
    print("\n" + "="*60)
    print("【权重调节】当前默认全局权重: A=15%, B=30%, C=25%, D=20%, E=10%")
    choice = input("是否调整全局权重？(y/n，直接回车默认n): ").strip().lower()
    if choice != 'y':
        return {'A': 0.15, 'B': 0.30, 'C': 0.25, 'D': 0.20, 'E': 0.10}
    print("\n请依次输入五大维度的权重百分比（整数），总和须为100。")
    try:
        a = float(input("维度A (地理与生存成本): "))
        b = float(input("维度B (平台硬实力): "))
        c = float(input("维度C (职业资产增值): "))
        d = float(input("维度D (生活质量): "))
        e = float(input("维度E (主观适配): "))
        total = a + b + c + d + e
        if abs(total - 100) > 0.01:
            print(f"⚠️ 总和为{total}，不等于100，系统将自动归一化。")
        return {'A': a/total, 'B': b/total, 'C': c/total, 'D': d/total, 'E': e/total}
    except:
        print("输入无效，使用默认权重。")
        return {'A': 0.15, 'B': 0.30, 'C': 0.25, 'D': 0.20, 'E': 0.10}

# ===================== 数据录入 =====================
def get_user_input():
    """
    返回字典 {fid: (raw_val, conf, is_unknown)}
    raw_val 为已转换好的数值（或元组），None 表示未知
    conf 为置信度数值 (0.9/0.6/0.3/0.1)
    """
    factor_list = [
        # 维度 A
        ('A1', '前三年平均年终结余',
         "  请选择输入方式：\n"
         "    1. 直接输入年均结余（万元）\n"
         "    2. 分别输入平均年总包和平均年生活成本（万元）\n"
         "  请输入序号 (1 或 2): ",
         'A1_mode'),
        ('A2', '灵活变更工作城市自由度',
         "  请输入 0~1 之间的数值 (0=完全固定，1=可随时主动申请全球任意变更): ",
         'float'),
        ('A3', '强制调动风险 (惩罚项)',
         "  请输入 0~1 之间的数值 (0=无调动条款，0.5=协商制，1=强制全球调配): ",
         'float'),
        ('A4', '通勤效率',
         "  请输入单程通勤分钟数: ",
         'float'),

        # 维度 B
        ('B1', '细分行业排名',
         "  请输入排名百分位 (如 Top 5% 则输入 5): ",
         'float'),
        ('B2', '近3年营收增速',
         "  请输入 CAGR (如 20% 则输入 0.20): ",
         'float'),
        ('B3', '人才资本密度',
         "  请输入硕博+高工占比 (如 70% 则输入 0.70): ",
         'float'),
        ('B4', '国际化实质指数',
         "  请输入海外营收或外籍员工占比 (如 40% 则输入 0.40): ",
         'float'),
        ('B5', '组织稳定性',
         "  请输入近1年主动离职率 (如 15% 则输入 0.15): ",
         'float'),

        # 维度 C
        ('C1', '技能护城河深度',
         "  请输入该技能行业平均掌握年限 (如 4): ",
         'float'),
        ('C2', '技能可迁移广度',
         "  请输入该技能可适用的行业数量 (如 5): ",
         'float'),
        ('C3', '行业生命周期位置',
         "  请选择当前行业所处阶段：上行 (U) / 稳定 (S) / 下行 (D)\n"
         "  输入对应字母: ",
         'C3_choice'),
        ('C4', '学术/知识溢价',
         "  请输入 0~1 之间的数值 (0=严禁分享，1=鼓励发表): ",
         'float'),
        ('C5', '跳槽溢价系数',
         "  请输入离职后平均薪资涨幅 (如 25% 则输入 0.25): ",
         'float'),

        # 维度 D
        ('D1', '实际时薪水平',
         "  请输入您的实际时薪（元/小时）: ",
         'float'),
        ('D2', '带薪休息总量 (额外)',
         "  请输入除法定节假日外的额外带薪休假天数（年假+公司假）: ",
         'float'),
        ('D3', '加班刚性 (惩罚项)',
         "  请输入每周平均强制加班小时数: ",
         'float'),
        ('D4', '健康保障覆盖率',
         "  请输入 0~1 之间的数值 (1=全覆盖直系，0.5=仅本人): ",
         'float'),

        # 维度 E
        ('E1', '对工作内容的兴趣强度',
         "  设想未来进行日常工作时的情境，你对该工作内容的意义感和兴趣评分为 (0~10): ",
         'float'),
        ('E2', '团队工作氛围评价',
         "  设想未来在该团队工作相处时的情境，你对该团队工作氛围的满意度评分为 (0~10): ",
         'float'),
        ('E3', '长期愿景一致性',
         "  请自我评分 0~10 (10=该经历是5年规划的必备一环): ",
         'float'),
        ('E4', '所在城市主观倾向',
         "  请自我评分 0~10 (10=对该城市人文/气候/社交圈极其向往): ",
         'float'),
    ]

    data = {}
    print("\n" + "="*60)
    print("JOEM v2.2 数据录入".center(60))
    print("="*60)
    print("📌 输入规范：")
    print("  - 普通数值直接输入数字（如 35、0.2）。")
    print("  - 选项类输入按提示输入字母或数字。")
    print("  - 若该项【完全未知】，请输入小写字母 'u' 或直接按 Enter 留空。")
    print("  - 置信度档次：高(H) / 中(M) / 低(L)，请根据信息来源可靠性选择。")
    print("-"*60)

    idx = 0
    for fid, desc, prompt, typ in factor_list:
        idx += 1
        print(f"\n[{idx}/{len(factor_list)}] {fid} - {desc}")

        # --- 特殊处理 A1 模式选择 ---
        if typ == 'A1_mode':
            while True:
                mode = input(prompt).strip().lower()
                if mode in ['u', 'unknown', '']:
                    data[fid] = (None, 0.1, True)
                    break
                if mode == '1':
                    # 直接输入余额
                    val = input("  请输入年均结余（万元）: ").strip()
                    if val.lower() in ['u', 'unknown', '']:
                        data[fid] = (None, 0.1, True)
                    else:
                        try:
                            balance = float(val)
                            data[fid] = (balance, None, False)   # conf稍后询问
                        except:
                            print("  ⚠️ 输入无效，设为未知。")
                            data[fid] = (None, 0.1, True)
                    break
                elif mode == '2':
                    # 分别输入总包和生活成本
                    income_str = input("  请输入平均年总包（万元）: ").strip()
                    cost_str = input("  请输入平均年生活成本（万元）: ").strip()
                    if (income_str.lower() in ['u', 'unknown', ''] or
                        cost_str.lower() in ['u', 'unknown', '']):
                        data[fid] = (None, 0.1, True)
                    else:
                        try:
                            income = float(income_str)
                            cost = float(cost_str)
                            balance = income - cost
                            data[fid] = (balance, None, False)
                        except:
                            print("  ⚠️ 输入无效，设为未知。")
                            data[fid] = (None, 0.1, True)
                    break
                else:
                    print("  输入无效，请重新选择 1 或 2。")
            # 若未知，则跳过置信度询问
            if data[fid][2]:  # is_unknown
                continue
            # 否则询问置信度
            raw_val = data[fid][0]
            conf = ask_confidence()
            data[fid] = (raw_val, conf, False)
            continue

        # --- 特殊处理 C3 三档选择 ---
        if typ == 'C3_choice':
            raw_input = input(prompt).strip().lower()
            if raw_input in ['u', 'unknown', '']:
                data[fid] = (None, 0.1, True)
                continue
            if raw_input == 'u':
                data[fid] = (1.0, None, False)  # 上行
            elif raw_input == 's':
                data[fid] = (0.7, None, False)  # 稳定
            elif raw_input == 'd':
                data[fid] = (0.3, None, False)  # 下行
            else:
                print("  ⚠️ 无效选择，设为未知。")
                data[fid] = (None, 0.1, True)
                continue
            # 询问置信度
            raw_val = data[fid][0]
            conf = ask_confidence()
            data[fid] = (raw_val, conf, False)
            continue

        # --- 普通数值输入 ---
        raw_input = input(prompt).strip()
        if raw_input.lower() in ['u', 'unknown', '']:
            data[fid] = (None, 0.1, True)
            continue

        try:
            raw_val = float(raw_input)
        except ValueError:
            print("  ⚠️ 输入无效，设为未知。")
            data[fid] = (None, 0.1, True)
            continue

        # 询问置信度
        conf = ask_confidence()
        data[fid] = (raw_val, conf, False)

    return data

def ask_confidence():
    """询问置信度档次，返回数值 0.9/0.6/0.3"""
    while True:
        choice = input("  请选择该数据的置信度：高(H) / 中(M) / 低(L) (直接回车默认中): ").strip().upper()
        if choice == '':
            return 0.6
        if choice in ['H', '高']:
            return 0.9
        if choice in ['M', '中']:
            return 0.6
        if choice in ['L', '低']:
            return 0.3
        print("  输入无效，请重新输入 H/M/L。")

# ===================== 评分与输出 =====================
def calculate_and_print(data, global_weights):
    # 内部权重
    W_A_INNER = {'A1': 0.45, 'A2': 0.30, 'A4': 0.25}
    W_E_INNER = {'E1': 0.30, 'E2': 0.20, 'E3': 0.20, 'E4': 0.30}
    TOTAL_FACTORS = len(data)

    # 1. 计算有效得分
    factor_scores = {}
    unknown_count = 0
    dim_groups = {'A': [], 'B': [], 'C': [], 'D': [], 'E': []}

    for fid, (raw_val, conf, is_unknown) in data.items():
        if is_unknown:
            unknown_count += 1
            s = 0.5
            conf = 0.1   # 未知置信度固定为0.1
        else:
            s = get_factor_score(fid, raw_val)
            s = max(0.0, min(1.0, s))
        effective = s * conf
        dim = fid[0]
        factor_scores[fid] = (s, conf, effective)
        dim_groups[dim].append((fid, s, conf, effective))

    # 2. 各维度聚合
    dim_mu = {}
    dim_sigma2 = {}

    # ---- 维度 A (特殊处理加权+惩罚) ----
    items_A = dim_groups['A']
    # 提取A3
    a3_score = 1.0
    a3_conf = 1.0
    for fid, s, conf, eff in items_A:
        if fid == 'A3':
            a3_score = s
            a3_conf = conf
            break
    # 加权平均 (A1,A2,A4)
    sum_w_eff = 0.0
    sum_w_conf = 0.0
    for fid, s, conf, eff in items_A:
        if fid == 'A3':
            continue
        w = W_A_INNER.get(fid, 0.25)
        sum_w_eff += w * eff
        sum_w_conf += w * conf
    mu_A_raw = sum_w_eff / (sum_w_conf + 1e-6) if sum_w_conf > 0 else 0.5
    # 应用A3惩罚（若A3置信度低，则减弱惩罚）
    if a3_conf > 0.3:
        mu_A = mu_A_raw * a3_score
    else:
        mu_A = mu_A_raw   # 未知时不缩放
    # 方差
    var_A = 0.0
    for fid, s, conf, eff in items_A:
        if fid == 'A3':
            continue
        w = W_A_INNER.get(fid, 0.25)
        var_A += (w**2) * conf * ((s - mu_A_raw)**2)
    if sum_w_conf > 0:
        var_A = var_A / sum_w_conf
    else:
        var_A = 0.1
    # 叠加A3不确定性
    var_A += 0.05 * (1 - a3_conf)
    dim_mu['A'] = mu_A
    dim_sigma2['A'] = var_A

    # ---- 维度 B, C, D (等权聚合) ----
    for dim in ['B', 'C', 'D']:
        items = dim_groups[dim]
        if not items:
            dim_mu[dim] = 0.5
            dim_sigma2[dim] = 0.1
            continue
        sum_eff = sum([eff for _, _, _, eff in items])
        sum_conf = sum([conf for _, _, conf, _ in items]) + 1e-6
        mu = sum_eff / sum_conf
        dim_mu[dim] = mu
        var = sum([conf * ((s - mu)**2) for _, s, conf, _ in items]) / sum_conf
        dim_sigma2[dim] = var

    # ---- 维度 E (加权) ----
    items_E = dim_groups['E']
    sum_eff_E = 0.0
    sum_conf_E = 0.0
    for fid, s, conf, eff in items_E:
        w = W_E_INNER.get(fid, 0.25)
        sum_eff_E += w * eff
        sum_conf_E += w * conf
    mu_E = sum_eff_E / (sum_conf_E + 1e-6) if sum_conf_E > 0 else 0.5
    var_E = 0.0
    for fid, s, conf, eff in items_E:
        w = W_E_INNER.get(fid, 0.25)
        var_E += (w**2) * conf * ((s - mu_E)**2)
    var_E = var_E / (sum_conf_E + 1e-6) if sum_conf_E > 0 else 0.1
    dim_mu['E'] = mu_E
    dim_sigma2['E'] = var_E

    # 3. 全局稳健得分
    robust_score = 0.0
    for dim, mu in dim_mu.items():
        robust_score += global_weights[dim] * mu

    # 4. 全局不确定性
    sigma_total = 0.0
    for dim, var in dim_sigma2.items():
        sigma_total += (global_weights[dim]**2) * var
    sigma_total = math.sqrt(sigma_total)

    # 5. IIP 惩罚
    iip = 1 - (unknown_count / TOTAL_FACTORS) * 0.15

    # 6. 最终得分与区间
    final_score = robust_score * iip * 100
    lower = (robust_score - 1.645 * sigma_total) * iip * 100
    upper = (robust_score + 1.645 * sigma_total) * iip * 100
    lower = max(0, lower)
    upper = min(100, upper)
    width = upper - lower

    # ===== 打印报告 =====
    print("\n" + "="*60)
    print("📊 JOEM v2.2 评估结果报告".center(60))
    print("="*60)
    print("\n【维度分解得分 (稳健均值)】")
    for dim in ['A', 'B', 'C', 'D', 'E']:
        mu = dim_mu.get(dim, 0.5)
        var = dim_sigma2.get(dim, 0.1)
        w = global_weights[dim]
        print(f"  维度 {dim} (权重 {w*100:.1f}%): 得分 {mu:.3f}  | 内部不确定性 σ²={var:.4f}")

    print(f"\n【信息完整度】")
    print(f"  已知项: {TOTAL_FACTORS - unknown_count}/{TOTAL_FACTORS}")
    print(f"  未知惩罚系数 (IIP): {iip:.4f}")

    print(f"\n【★ 最终核心指标】")
    print(f"  稳健得分 (Robust): {robust_score:.4f}")
    print(f"  全局标准差 (σ_total): {sigma_total:.4f}")
    print(f"  **最终推荐指数: {final_score:.2f} 分**")
    print(f"  90% 置信区间: [{lower:.2f}, {upper:.2f}]")
    print(f"  区间宽度: {width:.2f} 分")

    print("\n【🧠 智能决策建议】")
    if width > 25:
        print("  ⚠️ 区间过宽 (>25分)，信息不足。强烈建议优先补充高权重未知项。")
    elif width > 15:
        print("  ⚠️ 区间偏宽 (15-25分)，存在一定风险。建议核实置信度为“低”的关键项。")
    else:
        print("  ✅ 区间较窄，数据质量良好，结果可信度高。")

    if final_score >= 80:
        print("  🌟 评级：A (强烈推荐) —— 综合条件卓越。")
    elif final_score >= 65:
        print("  👍 评级：B (推荐) —— 整体不错，有取舍空间。")
    elif final_score >= 50:
        print("  📊 评级：C (及格) —— 风险与机遇并存。")
    else:
        print("  🔻 评级：D (谨慎) —— 低于基准，若无特殊理由建议放弃。")
    print("="*60 + "\n")

# ===================== 主程序 =====================
if __name__ == "__main__":
    print("\n🚀 启动 JOEM v2.2 职业机会量化评估系统")
    global_w = get_weights()
    print(f"\n当前使用的全局权重: A={global_w['A']*100:.1f}%, B={global_w['B']*100:.1f}%, C={global_w['C']*100:.1f}%, D={global_w['D']*100:.1f}%, E={global_w['E']*100:.1f}%")
    input("\n按 Enter 键开始录入数据...")
    user_data = get_user_input()
    calculate_and_print(user_data, global_w)
