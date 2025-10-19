import asyncio
import re
from mcp.server import Server
from mcp.types import TextContent, Tool
import mcp.types as types

# 创建MCP服务器实例
server = Server("content-moderation-agent")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """列出内容审核工具"""
    return [
        Tool(
            name="moderate_content",
            description="全面审核文本内容的安全性",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string", 
                        "description": "需要审核的文本内容",
                        "required": True
                    }
                }
            }
        ),
        Tool(
            name="check_sensitive_words",
            description="专门检查敏感词汇",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "需要检查的文本内容", 
                        "required": True
                    }
                }
            }
        ),
        Tool(
            name="analyze_content_risk",
            description="分析内容风险等级",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "需要分析的文本内容",
                        "required": True
                    }
                }
            }
        ),
        Tool(
            name="bulk_moderate",
            description="批量审核多条内容",
            inputSchema={
                "type": "object", 
                "properties": {
                    "contents": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "需要审核的内容列表",
                        "required": True
                    }
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """处理工具调用"""
    if name == "moderate_content":
        result = await moderate_content(arguments["content"])
    elif name == "check_sensitive_words":
        result = await check_sensitive_words(arguments["content"])
    elif name == "analyze_content_risk":
        result = await analyze_content_risk(arguments["content"])
    elif name == "bulk_moderate":
        result = await bulk_moderate(arguments["contents"])
    else:
        raise ValueError(f"未知工具: {name}")

    return [TextContent(type="text", text=result)]

class ContentModerator:
    """内容审核核心逻辑"""

    def __init__(self):
        self.sensitive_words = {
            "political": ["政府", "政策", "领导", "国家", "政治", "党"],
            "violence": ["暴力", "攻击", "伤害", "武器", "战争", "恐怖"],
            "pornographic": ["色情", "淫秽", "性爱", "裸体", "成人"],
            "discrimination": ["种族", "性别", "地域", "歧视", "偏见"],
            "illegal": ["赌博", "毒品", "诈骗", "犯罪", "违法"]
        }

        self.ad_keywords = ["购买", "折扣", "优惠", "促销", "微信号", "电话", "点击链接", "立即咨询"]

        self.spam_patterns = [
            r"\d{11}",  # 手机号
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",  # URL
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # 邮箱
        ]

    async def comprehensive_moderation(self, content: str) -> dict:
        """全面内容审核"""
        basic_checks = self._perform_basic_checks(content)
        sensitive_results = self._check_sensitive_words(content)
        ad_detection = self._detect_advertisement(content)
        spam_detection = self._detect_spam(content)

        overall_score = self._calculate_overall_score(
            basic_checks, sensitive_results, ad_detection, spam_detection
        )

        return {
            "overall_score": overall_score,
            "status": "approved" if overall_score >= 70 else "review" if overall_score >= 40 else "rejected",
            "basic_checks": basic_checks,
            "sensitive_words": sensitive_results,
            "ad_detection": ad_detection,
            "spam_detection": spam_detection,
            "suggestions": self._generate_suggestions(
                basic_checks, sensitive_results, ad_detection, spam_detection
            )
        }

    def _perform_basic_checks(self, content: str) -> dict:
        """执行基础检查"""
        char_count = len(content)
        word_count = len(content.strip())

        if char_count < 10:
            length_status = "too_short"
        elif char_count > 5000:
            length_status = "too_long"
        else:
            length_status = "appropriate"

        symbol_count = len(re.findall(r'[^\w\s]', content))
        symbol_ratio = symbol_count / char_count if char_count > 0 else 0

        if symbol_ratio > 0.3:
            symbol_status = "high"
        elif symbol_ratio > 0.1:
            symbol_status = "medium"
        else:
            symbol_status = "low"

        return {
            "length_status": length_status,
            "char_count": char_count,
            "word_count": word_count,
            "symbol_ratio": round(symbol_ratio, 3),
            "symbol_status": symbol_status
        }

    def _check_sensitive_words(self, content: str) -> dict:
        """检查敏感词"""
        found_words = {}
        total_count = 0

        for category, words in self.sensitive_words.items():
            category_words = []
            for word in words:
                if word in content:
                    category_words.append(word)
                    total_count += 1
            if category_words:
                found_words[category] = category_words

        severity = "high" if total_count > 3 else "medium" if total_count > 0 else "low"

        return {
            "found_words": found_words,
            "total_count": total_count,
            "severity": severity
        }

    def _detect_advertisement(self, content: str) -> dict:
        """检测广告内容"""
        ad_keywords_found = []
        for keyword in self.ad_keywords:
            if keyword in content:
                ad_keywords_found.append(keyword)

        ad_score = len(ad_keywords_found) * 15
        is_likely_ad = ad_score >= 30

        return {
            "ad_keywords_found": ad_keywords_found,
            "ad_score": ad_score,
            "is_likely_ad": is_likely_ad
        }

    def _detect_spam(self, content: str) -> dict:
        """检测垃圾内容"""
        spam_indicators = []

        for pattern in self.spam_patterns:
            matches = re.findall(pattern, content)
            if matches:
                spam_indicators.append({
                    "pattern": pattern,
                    "matches": matches[:3]
                })

        words = content.split()
        unique_words = set(words)
        repetition_ratio = 1 - (len(unique_words) / len(words)) if words else 0

        is_likely_spam = len(spam_indicators) > 0 or repetition_ratio > 0.6

        return {
            "spam_indicators": spam_indicators,
            "repetition_ratio": round(repetition_ratio, 3),
            "is_likely_spam": is_likely_spam
        }

    def _calculate_overall_score(self, basic_checks: dict, sensitive_results: dict, 
                               ad_detection: dict, spam_detection: dict) -> int:
        """计算综合评分"""
        score = 100

        if basic_checks["length_status"] == "too_short":
            score -= 30
        elif basic_checks["length_status"] == "too_long":
            score -= 15

        if basic_checks["symbol_status"] == "high":
            score -= 20
        elif basic_checks["symbol_status"] == "medium":
            score -= 10

        if sensitive_results["severity"] == "high":
            score -= 50
        elif sensitive_results["severity"] == "medium":
            score -= 25

        if ad_detection["is_likely_ad"]:
            score -= 40

        if spam_detection["is_likely_spam"]:
            score -= 60

        return max(0, score)

    def _generate_suggestions(self, basic_checks: dict, sensitive_results: dict,
                            ad_detection: dict, spam_detection: dict) -> list:
        """生成改进建议"""
        suggestions = []

        if basic_checks["length_status"] == "too_short":
            suggestions.append("内容过短，建议补充更多有效信息")
        elif basic_checks["length_status"] == "too_long":
            suggestions.append("内容过长，建议适当精简突出重点")

        if basic_checks["symbol_status"] in ["medium", "high"]:
            suggestions.append("特殊符号使用较多，建议减少使用")

        if sensitive_results["total_count"] > 0:
            suggestions.append(f"发现{sensitive_results['total_count']}个敏感词汇，建议修改相关表述")

        if ad_detection["is_likely_ad"]:
            suggestions.append("内容疑似广告，建议调整表述方式")

        if spam_detection["is_likely_spam"]:
            suggestions.append("内容疑似垃圾信息，建议重新编写")

        if not suggestions:
            suggestions.append("内容质量良好，符合发布标准")

        return suggestions

async def moderate_content(content: str) -> str:
    """全面内容审核"""
    moderator = ContentModerator()
    result = await moderator.comprehensive_moderation(content)

    report = "内容审核报告\n"
    report += "=" * 50 + "\n\n"

    status_text = {
        "approved": "通过",
        "review": "需要审核", 
        "rejected": "拒绝"
    }

    report += f"总体评分: {result['overall_score']}/100\n"
    report += f"审核状态: {status_text[result['status']]}\n\n"

    report += "基础检查:\n"
    basic = result['basic_checks']
    report += f"  内容长度: {basic['char_count']}字符 ({basic['length_status']})\n"
    report += f"  符号比例: {basic['symbol_ratio']} ({basic['symbol_status']})\n\n"

    sensitive = result['sensitive_words']
    report += f"敏感词检测: {sensitive['total_count']}个 ({sensitive['severity']})\n"
    if sensitive['found_words']:
        for category, words in sensitive['found_words'].items():
            report += f"  {category}: {', '.join(words)}\n"
    report += "\n"

    ad = result['ad_detection']
    report += f"广告检测: {'疑似广告' if ad['is_likely_ad'] else '正常'}\n"
    if ad['ad_keywords_found']:
        report += f"  广告关键词: {', '.join(ad['ad_keywords_found'][:3])}\n"
    report += "\n"

    spam = result['spam_detection']
    report += f"垃圾检测: {'疑似垃圾' if spam['is_likely_spam'] else '正常'}\n"
    report += f"  内容重复率: {spam['repetition_ratio']}\n\n"

    report += "改进建议:\n"
    for suggestion in result['suggestions']:
        report += f"- {suggestion}\n"

    return report

async def check_sensitive_words(content: str) -> str:
    """检查敏感词"""
    moderator = ContentModerator()
    result = await moderator.comprehensive_moderation(content)
    sensitive = result['sensitive_words']

    if sensitive['total_count'] == 0:
        return "未检测到敏感词汇"

    report = "敏感词检测结果\n"
    report += "=" * 50 + "\n\n"

    report += f"发现 {sensitive['total_count']} 个敏感词汇:\n\n"
    for category, words in sensitive['found_words'].items():
        report += f"- {category}: {', '.join(words)}\n"

    report += f"\n严重程度: {sensitive['severity']}"

    return report

async def analyze_content_risk(content: str) -> str:
    """分析内容风险"""
    moderator = ContentModerator()
    result = await moderator.comprehensive_moderation(content)

    risk_level = "低风险" if result['overall_score'] >= 80 else "中风险" if result['overall_score'] >= 60 else "高风险"

    report = "内容风险分析\n"
    report += "=" * 50 + "\n\n"

    report += f"风险等级: {risk_level}\n"
    report += f"安全评分: {result['overall_score']}/100\n\n"

    report += "主要风险点:\n"

    risks = []
    if result['sensitive_words']['total_count'] > 0:
        risks.append(f"敏感内容 ({result['sensitive_words']['total_count']}个敏感词)")
    if result['ad_detection']['is_likely_ad']:
        risks.append("广告嫌疑")
    if result['spam_detection']['is_likely_spam']:
        risks.append("垃圾内容")
    if result['basic_checks']['length_status'] == "too_short":
        risks.append("内容过短")

    if risks:
        for risk in risks:
            report += f"- {risk}\n"
    else:
        report += "- 无显著风险\n"

    return report

async def bulk_moderate(contents: list) -> str:
    """批量审核"""
    moderator = ContentModerator()

    report = "批量内容审核报告\n"
    report += "=" * 50 + "\n\n"

    approved_count = 0
    review_count = 0
    rejected_count = 0

    for i, content in enumerate(contents, 1):
        result = await moderator.comprehensive_moderation(content)

        status_text = "通过" if result['status'] == "approved" else "待审核" if result['status'] == "review" else "拒绝"

        report += f"{i}. 评分: {result['overall_score']}/100 - {status_text}\n"
        report += f"   预览: {content[:30]}...\n\n"

        if result['status'] == "approved":
            approved_count += 1
        elif result['status'] == "review":
            review_count += 1
        else:
            rejected_count += 1

    report += "统计摘要:\n"
    report += f"通过: {approved_count}条\n"
    report += f"待审核: {review_count}条\n" 
    report += f"拒绝: {rejected_count}条\n"
    report += f"总计: {len(contents)}条"

    return report

async def main():
    """主函数"""
    from mcp.cli.stdio import stdio_main
    await stdio_main(server)

if __name__ == "__main__":
    asyncio.run(main())