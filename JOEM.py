import math

# ===================== 计分函数库 =====================
def logistic(x, x0, k):
    try:
        return 1 / (1 + math.exp(-k * (x - x0)))
    except OverflowError:
        return 1.0 if (x - x0) > 0 else 0.0

def exp_decay(x, k):
    return math.exp(-k * x)

def exp_growth(x, k, min_val=0):
    if x < min_val:
        return 0.0
    return 1 - math.exp(-k * x)

def get_factor_score(fid, raw_val):
    """根据因子ID和原始输入计算得分 S (0~1)"""
    if raw_val is None:
        return 0.5

    # ---------- 维度 A ----------
    if fid == 'A1':
        return logistic(raw_val, 10.0, 0.2)
    if fid == 'A2':
        return max(0.0, min(1.0, raw_val))
    if fid == 'A3':
        return 1 - max(0.0, min(1.0, raw_val))
    if fid == 'A4':
        return exp_decay(raw_val, 0.018)

    # ---------- 维度 B ----------
    if fid == 'B1':
        return 1 - (raw_val / 100)
    if fid == 'B2':
        return logistic(raw_val, 0.10, 15)
    if fid == 'B3':
        return max(0.0, min(1.0, raw_val))
    if fid == 'B4':
        return max(0.0, min(1.0, raw_val))

    # ---------- 维度 C ----------
    if fid == 'C1':
        return 1 - math.exp(-0.5 * raw_val)
    if fid == 'C2':
        return 1 - math.exp(-0.4 * raw_val)
    if fid == 'C3':
        return max(0.0, min(1.0, raw_val))  # 已映射为0.3/0.7/1.0
    if fid == 'C4':
        return max(0.0, min(1.0, raw_val))
    if fid == 'C5':
        return logistic(raw_val, 0.15, 10)

    # ---------- 维度 D ----------
    if fid == 'D1':
        return logistic(raw_val, 80.0, 0.02)
    if fid == 'D2':
        return exp_growth(raw_val, 0.10)
    if fid == 'D3':
        return 1 / (1 + 0.05 * (raw_val ** 1.2))
    if fid == 'D4':
        return max(0.0, min(1.0, raw_val))

    # ---------- 维度 E ----------
    if fid in ['E1', 'E2', 'E3', 'E4']:
        return max(0.0, min(1.0, raw_val / 10.0))

    # ---------- 维度 F ----------
    if fid == 'F1':  # 合同年限映射
        if raw_val == 0:  # 无固定期限
            return 1.0
        if raw_val >= 5:
            return 0.95
        if raw_val >= 3:
            return 0.70
        if raw_val >= 1:
            return 0.45
        return 0.20
    if fid == 'F2':  # 单位类型 (已映射为数值)
        return max(0.0, min(1.0, raw_val))
    if fid == 'F3':  # 离职率
        return exp_decay(raw_val, 3.0)

    return 0.5

# ===================== 权重调节 =====================
def get_weights():
    print("\n" + "="*60)
    print("【权重调节】当前默认全局权重:")
    print("  A(地理)=15%, B(平台)=20%, C(前景)=15%, D(生活薪资)=32%, E(主观)=8%, F(稳定性)=10%")
    choice = input("是否调整全局权重？(y/n，直接回车默认n): ").strip().lower()
    if choice != 'y':
        return {'A': 0.15, 'B': 0.20, 'C': 0.15, 'D': 0.32, 'E': 0.08, 'F': 0.10}
    print("\n请依次输入六大维度的权重百分比（整数），总和须为100。")
    try:
        a = float(input("维度A (地理位置与生存成本): "))
        b = float(input("维度B (平台硬实力): "))
        c = float(input("维度C (职业前景): "))
        d = float(input("维度D (生活质量与薪资): "))
        e = float(input("维度E (主观适配): "))
        f = float(input("维度F (稳定性): "))
        total = a + b + c + d + e + f
        if abs(total - 100) > 0.01:
            print(f"⚠️ 总和为{total}，不等于100，系统将自动归一化。")
        return {'A': a/total, 'B': b/total, 'C': c/total, 'D': d/total, 'E': e/total, 'F': f/total}
    except:
        print("输入无效，使用默认权重。")
        return {'A': 0.15, 'B': 0.20, 'C': 0.15, 'D': 0.32, 'E': 0.08, 'F': 0.10}

# ===================== 数据录入 =====================
def ask_confidence():
    while True:
        choice = input("  请选择置信度：高(H) / 中(M) / 低(L) (直接回车默认中): ").strip().upper()
        if choice == '': return 0.6
        if choice in ['H', '高']: return 0.9
        if choice in ['M', '中']: return 0.6
        if choice in ['L', '低']: return 0.3
        print("  输入无效，请重新输入 H/M/L。")

def get_user_input():
    # 因子列表格式: (fid, 描述, 提示字符串, 类型标识)
    factor_list = [
        # 维度 A
        ('A1', '前三年平均年终结余',
         "  请选择输入方式：1-直接输入余额(万元) 2-分别输入总包+成本(万元): ",
         'A1_mode'),
        ('A2', '灵活变更城市自由度 (0~1)',
         "  请输入 0~1 之间的数值: ",
         'float'),
        ('A3', '强制调动风险 (0=无, 1=强制全球调配)',
         "  请输入 0~1 之间的数值: ",
         'float'),
        ('A4', '通勤效率',
         "  请输入单程通勤分钟数: ",
         'float'),
        # 维度 B
        ('B1', '细分行业排名百分位',
         "  请输入排名百分位 (如 Top5% 则输入 5): ",
         'float'),
        ('B2', '近3年营收增速',
         "  请输入 CAGR (如 20% 则输入 0.20): ",
         'float'),
        ('B3', '人才资本密度',
         "  请输入占比 (如 70% 则输入 0.70): ",
         'float'),
        ('B4', '国际化实质指数',
         "  请输入占比 (如 40% 则输入 0.40): ",
         'float'),
        # 维度 C
        ('C1', '技能护城河深度',
         "  请输入该技能行业平均掌握年限: ",
         'float'),
        ('C2', '技能可迁移广度',
         "  请输入可适用的行业数量: ",
         'float'),
        ('C3', '行业生命周期位置',
         "  请输入 U(上行) / S(稳定) / D(下行): ",
         'C3_choice'),
        ('C4', '学术/知识溢价',
         "  请输入 0~1 之间的数值 (0=严禁, 1=鼓励发表): ",
         'float'),
        ('C5', '跳槽溢价系数',
         "  请输入离职后平均薪资涨幅 (如 25% 则输入 0.25): ",
         'float'),
        # 维度 D
        ('D1', '实际时薪水平',
         "  请输入您的实际时薪 (元/小时): ",
         'float'),
        ('D2', '额外带薪休假',
         "  请输入除法定假日外的年假+公司假总天数: ",
         'float'),
        ('D3', '加班刚性 (惩罚项)',
         "  请输入每周平均强制加班小时数: ",
         'float'),
        ('D4', '健康保障覆盖率',
         "  请输入 0~1 之间的数值 (1=全覆盖直系): ",
         'float'),
        # 维度 E
        ('E1', '工作内容兴趣强度 (0~10)',
         "  设想日常情境，请评分 (0~10): ",
         'float'),
        ('E2', '团队氛围满意度 (0~10)',
         "  设想相处情境，请评分 (0~10): ",
         'float'),
        ('E3', '长期愿景一致性 (0~10)',
         "  请评分 (0~10): ",
         'float'),
        ('E4', '所在城市主观倾向 (0~10)',
         "  请评分 (0~10): ",
         'float'),
        # 维度 F
        ('F1', '合同期限保障',
         "  请输入合同年限 (无固定期限请输入 0): ",
         'float'),
        ('F2', '单位类型',
         "  请输入数字: 1-公务员 2-事业编 3-垄断央企 4-市场化国企 5-事业无编 6-大型民企 7-初创民企 8-外包: ",
         'F2_menu'),
        ('F3', '组织稳定性 (离职率)',
         "  请输入近1年主动离职率 (如 15% 则输入 0.15): ",
         'float'),
    ]

    data = {}
    print("\n" + "="*60)
    print("JOEM v2.3 数据录入".center(60))
    print("="*60)
    print("📌 输入规范：数值直接输入，选项按字母/数字，未知输 'u' 或直接回车。")
    print("-"*60)

    idx = 0
    for fid, desc, prompt, typ in factor_list:   # 注意解包顺序
        idx += 1
        print(f"\n[{idx}/{len(factor_list)}] {fid} - {desc}")

        # ---- 特殊处理 A1 (类型标识 'A1_mode') ----
        if typ == 'A1_mode':
            mode = input("  " + prompt).strip().lower()
            if mode in ['u', 'unknown', '']:
                data[fid] = (None, 0.1, True)
                continue
            if mode == '1':
                val = input("  请输入年均结余 (万元): ").strip()
                if val.lower() in ['u', 'unknown', '']:
                    data[fid] = (None, 0.1, True)
                    continue
                try:
                    raw = float(val)
                except:
                    print("  ⚠️ 输入无效，设为未知。")
                    data[fid] = (None, 0.1, True)
                    continue
            elif mode == '2':
                inc = input("  请输入年均总包 (万元): ").strip()
                cost = input("  请输入年均生活成本 (万元): ").strip()
                if inc.lower() in ['u', 'unknown', ''] or cost.lower() in ['u', 'unknown', '']:
                    data[fid] = (None, 0.1, True)
                    continue
                try:
                    raw = float(inc) - float(cost)
                except:
                    print("  ⚠️ 输入无效，设为未知。")
                    data[fid] = (None, 0.1, True)
                    continue
            else:
                print("  ⚠️ 无效选择，设为未知。")
                data[fid] = (None, 0.1, True)
                continue
            # 数据有效，询问置信度
            conf = ask_confidence()
            data[fid] = (raw, conf, False)
            continue

        # ---- 特殊处理 C3 (类型标识 'C3_choice') ----
        if typ == 'C3_choice':
            inp = input("  " + prompt).strip().lower()
            if inp in ['u', 'unknown', '']:
                data[fid] = (None, 0.1, True)
                continue
            if inp == 'u':
                raw = 1.0
            elif inp == 's':
                raw = 0.7
            elif inp == 'd':
                raw = 0.3
            else:
                print("  ⚠️ 无效选择，设为未知。")
                data[fid] = (None, 0.1, True)
                continue
            conf = ask_confidence()
            data[fid] = (raw, conf, False)
            continue

        # ---- 特殊处理 F2 (类型标识 'F2_menu') ----
        if typ == 'F2_menu':
            inp = input("  " + prompt).strip().lower()
            if inp in ['u', 'unknown', '']:
                data[fid] = (None, 0.1, True)
                continue
            try:
                num = int(inp)
                mapping = {1:1.0, 2:0.92, 3:0.82, 4:0.65, 5:0.50, 6:0.40, 7:0.25, 8:0.10}
                if num in mapping:
                    raw = mapping[num]
                else:
                    raise ValueError
            except:
                print("  ⚠️ 无效选择，设为未知。")
                data[fid] = (None, 0.1, True)
                continue
            conf = ask_confidence()
            data[fid] = (raw, conf, False)
            continue

        # ---- 普通数值类型 (typ == 'float') ----
        inp = input("  " + prompt).strip()
        if inp.lower() in ['u', 'unknown', '']:
            data[fid] = (None, 0.1, True)
            continue
        try:
            raw = float(inp)
        except ValueError:
            print("  ⚠️ 输入无效，设为未知。")
            data[fid] = (None, 0.1, True)
            continue
        conf = ask_confidence()
        data[fid] = (raw, conf, False)

    return data

# ===================== 评分引擎 =====================
def calculate_and_print(data, global_w):
    W_A_INNER = {'A1': 0.45, 'A2': 0.30, 'A4': 0.25}
    W_E_INNER = {'E1': 0.30, 'E2': 0.20, 'E3': 0.20, 'E4': 0.30}
    W_F_INNER = {'F1': 0.30, 'F2': 0.40, 'F3': 0.30}
    TOTAL = len(data)

    unknown_count = 0
    dim_groups = {'A': [], 'B': [], 'C': [], 'D': [], 'E': [], 'F': []}

    for fid, (raw_val, conf, is_unknown) in data.items():
        if is_unknown:
            unknown_count += 1
            s = 0.5
            conf = 0.1
        else:
            s = get_factor_score(fid, raw_val)
            s = max(0.0, min(1.0, s))
        dim = fid[0]
        dim_groups[dim].append((fid, s, conf, s * conf))

    dim_mu = {}
    dim_sigma2 = {}

    # ---- 维度 A (加权 + 惩罚) ----
    items = dim_groups['A']
    a3_score, a3_conf = 1.0, 1.0
    for fid, s, conf, _ in items:
        if fid == 'A3':
            a3_score, a3_conf = s, conf
    # 计算 A1,A2,A4 的加权均值和方差
    sum_w_eff = 0.0
    sum_w_conf = 0.0
    for fid, s, conf, _ in items:
        if fid != 'A3':
            w = W_A_INNER.get(fid, 0.25)
            sum_w_eff += w * s * conf
            sum_w_conf += w * conf
    mu_raw = sum_w_eff / (sum_w_conf + 1e-6) if sum_w_conf > 0 else 0.5
    mu_A = mu_raw * a3_score if a3_conf > 0.3 else mu_raw
    var_A = 0.0
    for fid, s, conf, _ in items:
        if fid != 'A3':
            w = W_A_INNER.get(fid, 0.25)
            var_A += (w ** 2) * conf * ((s - mu_raw) ** 2)
    var_A = var_A / (sum_w_conf + 1e-6) if sum_w_conf > 0 else 0.1
    var_A += 0.05 * (1 - a3_conf)  # A3 不确定性贡献
    dim_mu['A'], dim_sigma2['A'] = mu_A, var_A

    # ---- 维度 B, C, D (等权) ----
    for dim in ['B', 'C', 'D']:
        items = dim_groups[dim]
        if not items:
            dim_mu[dim], dim_sigma2[dim] = 0.5, 0.1
            continue
        sum_eff = sum([eff for _, _, _, eff in items])
        sum_conf = sum([conf for _, _, conf, _ in items]) + 1e-6
        mu = sum_eff / sum_conf
        var = sum([conf * ((s - mu) ** 2) for _, s, conf, _ in items]) / sum_conf
        dim_mu[dim], dim_sigma2[dim] = mu, var

    # ---- 维度 E (加权) ----
    items = dim_groups['E']
    sum_eff = 0.0
    sum_conf = 0.0
    for fid, s, conf, eff in items:
        w = W_E_INNER.get(fid, 0.25)
        sum_eff += w * eff
        sum_conf += w * conf
    mu_E = sum_eff / (sum_conf + 1e-6) if sum_conf > 0 else 0.5
    var_E = 0.0
    for fid, s, conf, _ in items:
        w = W_E_INNER.get(fid, 0.25)
        var_E += (w ** 2) * conf * ((s - mu_E) ** 2)
    var_E = var_E / (sum_conf + 1e-6) if sum_conf > 0 else 0.1
    dim_mu['E'], dim_sigma2['E'] = mu_E, var_E

    # ---- 维度 F (加权) ----
    items = dim_groups['F']
    sum_eff = 0.0
    sum_conf = 0.0
    for fid, s, conf, eff in items:
        w = W_F_INNER.get(fid, 0.33)
        sum_eff += w * eff
        sum_conf += w * conf
    mu_F = sum_eff / (sum_conf + 1e-6) if sum_conf > 0 else 0.5
    var_F = 0.0
    for fid, s, conf, _ in items:
        w = W_F_INNER.get(fid, 0.33)
        var_F += (w ** 2) * conf * ((s - mu_F) ** 2)
    var_F = var_F / (sum_conf + 1e-6) if sum_conf > 0 else 0.1
    dim_mu['F'], dim_sigma2['F'] = mu_F, var_F

    # ---- 全局得分 ----
    robust = sum([global_w[dim] * dim_mu[dim] for dim in global_w])
    sigma = math.sqrt(sum([(global_w[dim] ** 2) * dim_sigma2[dim] for dim in global_w]))
    iip = 1 - (unknown_count / TOTAL) * 0.15
    final = robust * iip * 100
    lower = max(0, (robust - 1.645 * sigma) * iip * 100)
    upper = min(100, (robust + 1.645 * sigma) * iip * 100)

    # ---- 输出 ----
    print("\n" + "="*60)
    print("📊 JOEM v2.3 评估报告".center(60))
    print("="*60)
    print("\n【维度分解】")
    for dim in ['A', 'B', 'C', 'D', 'E', 'F']:
        print(f"  {dim} (权重{global_w[dim]*100:.1f}%): 得分 {dim_mu[dim]:.3f}  | 方差 {dim_sigma2[dim]:.4f}")
    print(f"\n【信息完整度】已知 {TOTAL - unknown_count}/{TOTAL}，IIP={iip:.4f}")
    print(f"\n【★ 最终结果】")
    print(f"  稳健得分: {robust:.4f}")
    print(f"  **推荐指数: {final:.2f} 分**")
    print(f"  90% CI: [{lower:.2f}, {upper:.2f}] (宽度 {upper - lower:.2f})")
    print("\n【建议】")
    if upper - lower > 25:
        print("  ⚠️ 区间过宽，数据不足，建议补充未知项。")
    elif upper - lower > 15:
        print("  ⚠️ 区间偏宽，核实置信度为低的项。")
    else:
        print("  ✅ 数据质量良好，结果可信。")
    if final >= 80:
        print("  🌟 A级 (强烈推荐)")
    elif final >= 65:
        print("  👍 B级 (推荐)")
    elif final >= 50:
        print("  📊 C级 (及格)")
    else:
        print("  🔻 D级 (谨慎)")
    print("="*60)

# ===================== 主程序 =====================
if __name__ == "__main__":
    print("\n🚀 启动 JOEM v2.3")
    gw = get_weights()
    print(f"\n使用权重: A={gw['A']*100:.0f}% B={gw['B']*100:.0f}% C={gw['C']*100:.0f}% D={gw['D']*100:.0f}% E={gw['E']*100:.0f}% F={gw['F']*100:.0f}%")
    input("\n按 Enter 录入数据...")
    data = get_user_input()
    calculate_and_print(data, gw)
