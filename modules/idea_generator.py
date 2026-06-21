"""Chinese-first, rule-based business and content suggestions."""

from __future__ import annotations

import pandas as pd


IDEA_LIBRARY: dict[str, dict[str, str]] = {
    "Time cost pain": {
        "ai_agent_idea": "时间成本优化 Agent：识别耗时步骤并生成优先级改进清单。",
        "ai_skill_idea": "任务耗时诊断 Skill：从流程描述中提取瓶颈、等待点和可简化步骤。",
        "automation_workflow_idea": "收集任务记录 → 识别高耗时环节 → 生成每周节省时间报告。",
        "short_video_topic": "为什么每天很忙却没有产出？先找出这 3 个时间黑洞。",
        "xiaohongshu_douyin_angle": "用一张“自动化前后”时间对比表展示可量化的效率提升。",
        "paid_service_idea": "为个人或小团队提供流程时间审计与优化服务。",
        "target_user_group": "高频处理重复任务的职场人、小团队和内容创作者。",
        "recommended_next_action": "访谈 5 位目标用户，记录他们每周最耗时的重复任务。",
    },
    "Money cost pain": {
        "ai_agent_idea": "成本比较 Agent：整理价格、订阅与隐性成本并生成选择建议。",
        "ai_skill_idea": "费用结构提取 Skill：从账单或方案中提取收费项目和续费风险。",
        "automation_workflow_idea": "汇总订阅 → 标记重复或闲置支出 → 生成月度成本提醒。",
        "short_video_topic": "别只看月费：购买软件前要检查的 5 个隐性成本。",
        "xiaohongshu_douyin_angle": "用真实感但完全合成的账单案例做透明成本拆解。",
        "paid_service_idea": "个人创作者或小企业工具栈与订阅审计服务。",
        "target_user_group": "预算敏感的个人创作者、自由职业者和小企业。",
        "recommended_next_action": "收集用户最常质疑的 10 类费用，并验证实际损失金额。",
    },
    "Learning difficulty": {
        "ai_agent_idea": "个性化学习教练 Agent：按基础水平拆解知识并安排复习。",
        "ai_skill_idea": "课程内容拆解 Skill：把复杂课程拆成重点、例子、复习卡片和测试题。",
        "automation_workflow_idea": "导入学习材料 → 生成知识地图 → 制定每日任务 → 自动复习提醒。",
        "short_video_topic": "新手为什么学不会？可能是材料没有被拆成可执行步骤。",
        "xiaohongshu_douyin_angle": "展示一段复杂材料如何变成 7 天学习清单。",
        "paid_service_idea": "面向课程作者或学习者的内容拆解与微课设计服务。",
        "target_user_group": "学生、转行学习者、课程创作者和企业培训团队。",
        "recommended_next_action": "选取一个难点做学习拆解原型，并邀请 5 位新手试学。",
    },
    "Tool usability problem": {
        "ai_agent_idea": "软件使用帮助 Agent：根据问题描述定位常见故障并提供验证步骤。",
        "ai_skill_idea": "错误诊断 Skill：将用户描述转成可复现步骤、可能原因和检查清单。",
        "automation_workflow_idea": "收集报错 → 分类问题 → 匹配知识库 → 必要时升级人工支持。",
        "short_video_topic": "软件不好用时，先检查这 4 个最常见的设置问题。",
        "xiaohongshu_douyin_angle": "用录屏做一分钟故障排查，突出步骤清楚、结果可验证。",
        "paid_service_idea": "软件上手辅导、知识库整理与客服流程优化。",
        "target_user_group": "非技术用户、SaaS 新用户和小型软件团队。",
        "recommended_next_action": "整理出现频率最高且可复现的 10 个使用问题。",
    },
    "Information gap": {
        "ai_agent_idea": "研究与信息整理 Agent：从授权资料中汇总答案、来源和待确认问题。",
        "ai_skill_idea": "信息摘要 Skill：提取关键事实、差异点、证据来源和行动建议。",
        "automation_workflow_idea": "导入资料 → 分类与去重 → 生成摘要 → 输出定期监控报告。",
        "short_video_topic": "信息越多越迷茫？用这个框架把资料变成决策依据。",
        "xiaohongshu_douyin_angle": "制作可收藏的研究清单，演示如何减少信息过载。",
        "paid_service_idea": "行业资料整理、竞品信息摘要或本地知识库搭建服务。",
        "target_user_group": "研究者、学习者、咨询顾问、营销与客户支持团队。",
        "recommended_next_action": "列出用户最难快速回答的 10 个问题，并确认可信资料来源。",
    },
    "Trust issue": {
        "ai_agent_idea": "评论与评价分析 Agent：自动汇总用户评价、识别风险点和可信度信号。",
        "ai_skill_idea": "声明核验 Skill：提取关键承诺并标记证据不足、隐私或收费风险。",
        "automation_workflow_idea": "收集授权评价 → 识别信任主题 → 生成人工复核清单。",
        "short_video_topic": "买课、买工具前，如何判断是不是割韭菜？",
        "xiaohongshu_douyin_angle": "用合成案例拆解隐藏费用、虚假承诺和隐私红旗。",
        "paid_service_idea": "产品透明度、用户评价与信任信号审计服务。",
        "target_user_group": "谨慎消费者、在线教育团队和数字产品商家。",
        "recommended_next_action": "验证哪些信任信号最能影响目标用户的购买决定。",
    },
    "Service complaint": {
        "ai_agent_idea": "客服分流 Agent：识别问题类型、紧急程度并生成回复草稿。",
        "ai_skill_idea": "投诉摘要 Skill：提取问题、情绪、期望结果和升级条件。",
        "automation_workflow_idea": "接收反馈 → 分类优先级 → 草拟回复 → 超时自动提醒与升级。",
        "short_video_topic": "同一个投诉，差的客服回复和好的回复差在哪里？",
        "xiaohongshu_douyin_angle": "用前后对比展示如何写出清楚、负责且有下一步的回复。",
        "paid_service_idea": "客服知识库、回复模板和工单自动化实施服务。",
        "target_user_group": "电商、小型 SaaS、课程团队和客户支持部门。",
        "recommended_next_action": "统计重复咨询原因、平均响应时间和需要人工升级的比例。",
    },
    "Anxiety / uncertainty": {
        "ai_agent_idea": "决策清晰度 Agent：整理选项、约束、风险和下一步行动。",
        "ai_skill_idea": "选择比较 Skill：将模糊担忧转换为可比较的决策标准。",
        "automation_workflow_idea": "收集目标与限制 → 比较方案 → 生成行动清单和复盘提醒。",
        "short_video_topic": "选择太多时，如何用一张表降低决策焦虑？",
        "xiaohongshu_douyin_angle": "分享可保存的决策模板，避免使用制造焦虑的表达。",
        "paid_service_idea": "结构化规划、选择比较和行动陪跑服务。",
        "target_user_group": "面临学习、职业或创作选择的用户。",
        "recommended_next_action": "找出用户最常拖延的 3 类决定，并测试一个决策模板。",
    },
    "Repeated manual work": {
        "ai_agent_idea": "重复任务自动处理 Agent：自动整理、分类、汇总和生成报告。",
        "ai_skill_idea": "结构化数据提取 Skill：从日常文本、表格或邮件中提取标准字段。",
        "automation_workflow_idea": "收集表单或文件 → 清洗分类 → 汇总数据 → 自动发送周报。",
        "short_video_topic": "这 5 类重复工作，最适合先做轻量自动化。",
        "xiaohongshu_douyin_angle": "展示同一任务手动处理与自动工作流的时间对比。",
        "paid_service_idea": "为小商家或内容创作者搭建每周自动报表工作流。",
        "target_user_group": "运营人员、小商家、自由职业者和内容创作者。",
        "recommended_next_action": "选择一个输入稳定、规则清晰的重复任务，画出完整流程。",
    },
    "Need for automation": {
        "ai_agent_idea": "工作流自动化 Agent：根据流程描述生成触发、处理、审批和异常步骤。",
        "ai_skill_idea": "流程设计 Skill：把自然语言需求转换为可实施的自动化规格。",
        "automation_workflow_idea": "需求收集 → 流程映射 → 风险检查 → 小范围运行 → 人工复核。",
        "short_video_topic": "第一次做自动化，应该选哪个流程？用 3 个标准判断。",
        "xiaohongshu_douyin_angle": "公开记录一个低风险自动化从需求到测试的完整过程。",
        "paid_service_idea": "面向小团队的 AI 工作流设计、实施和培训服务。",
        "target_user_group": "正在增长的创作者业务、小企业和运营团队。",
        "recommended_next_action": "优先原型化高频、低风险且结果容易验证的工作流。",
    },
}


IDEA_COLUMNS = ["pain_category", *next(iter(IDEA_LIBRARY.values())).keys()]


def generate_ideas(opportunities: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    """Return practical suggestion sets for the highest-ranked categories."""
    rows = [
        {"pain_category": category, **IDEA_LIBRARY[category]}
        for category in opportunities.head(limit)["pain_category"]
        if category in IDEA_LIBRARY
    ]
    return pd.DataFrame(rows, columns=IDEA_COLUMNS)

