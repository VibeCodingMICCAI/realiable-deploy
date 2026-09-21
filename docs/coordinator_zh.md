# 展台协调员手册（中文）

## 电梯稿

> 这是什么工具？输入 3D 膝盖 MRI，输出多结构分割标签。  
> 展台默认走 **cached** 样例（不是现场全量 nnU-Net）。  
> 核心挑战：测试全绿，但 **换病例、同输出目录** 时可能复用旧预测。  
> 不是临床认证。

## 开场准备

```powershell
cd <仓库根目录>
python -m pip install -e ".[test]"
python scripts/export_intro_slices.py
python scripts/tutorial_lab.py
```

打开 `http://127.0.0.1:8000`，Ctrl+F5。确认 Intro 切片可滑动；Core 第 6 步 faulty 回归失败、corrected 通过。

## 路线

| 路线 | 时长 | 流程 |
|---|---|---|
| Quick | 5–10 分 | 工具介绍 → 陈旧结果挑战 → Evidence |
| Full | ~30 分 | 介绍 → 核心 → 测试菜单 → README → Summary |

## 带场要点

### 0 工具介绍（2–3 分钟）
- 输入：3D `.nii.gz`；屏上是 2D 切片子集。  
- 输出：分割 NIfTI ≠ 彩图 overlay；GT 是参考标注，不是推理输入。  
- Live lab = 本机跑了白名单 Python，**仍可能是 cached 预测**。

### 1 核心挑战（必做）
故事：AI 被要求 “若已有 prediction 文件就跳过分割”。  
弱测试用**各自新目录** → 全绿。  
A→B **同一目录** → B 可能拿到 A 的结果。  
预期失败 = 抓住埋点。  
参考修复：**总是处理当前输入并覆盖输出**（完整缓存失效是进阶话题，本展台未实现全套）。

### 2 / 3
分层菜单选做；README 先找缺口再揭晓。

## 收场
区分：Live 执行 / 预录 sample / 预期失败 / 揭晓 ≠ 验证。  
研究可分享 ≠ 生产 ≠ 临床。
