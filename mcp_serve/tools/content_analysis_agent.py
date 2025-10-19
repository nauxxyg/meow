import asyncio
import re
import jieba
import jieba.analyse
from collections import Counter
from mcp.server import Server
from mcp.types import TextContent, Tool
import mcp.types as types

# 创建MCP服务器实例
server = Server("content-analysis-agent")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """列出内容分析工具"""
    return [
        Tool(
            name="analyze_content",
            description="全面分析文本内容的质量和特征",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "要分析的文本内容",
                        "required": True
                    }
                }
            }
        ),
        Tool(
            name="extract_keywords", 
            description="从文本中提取关键词",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "文本内容",
                        "required": True
                    },
                    "top_k": {
                        "type": "number",
                        "description": "关键词数量",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="analyze_readability",
            description="分析文本可读性",
            inputSchema={
                "type": "object", 
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "文本内容", 
                        "required": True
                    }
                }
            }
        ),
        Tool(
            name="sentiment_analysis",
            description="分析文本情感倾向",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "文本内容",
                        "required": True
                    }
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """处理工具调用"""
    if name == "analyze_content":
        result = await analyze_content(arguments["content"])
    elif name == "extract_keywords":
        result = await extract_keywords(
            arguments["content"],
            arguments.get("top_k", 10)
        )
    elif name == "analyze_readability":
        result = await analyze_readability(arguments["content"])
    elif name == "sentiment_analysis":
        result = await sentiment_analysis(arguments["content"])
    else:
        raise ValueError(f"未知工具: {name}")

    return [TextContent(type="text", text=result)]

class ContentAnalyzer:
    """内容分析核心逻辑"""

    def __init__(self):
        jieba.initialize()
        self._load_custom_dict()

    def _load_custom_dict(self):
        """加载自定义词典"""
        custom_words = [
            "人工智能 AI", "机器学习", "深度学习", "大数据",
            "云计算", "物联网", "区块链", "数字化转型"
        ]
        for word in custom_words:
            jieba.add_word(word)

    async def comprehensive_analysis(self, content: str) -> dict:
        """全面内容分析"""
        stats = self._get_basic_stats(content)
        keywords = self._extract_keywords(content, 10)
        readability = self._analyze_readability(content, stats)
        sentiment = self._analyze_sentiment(content)
        topics = self._identify_topics(content)

        return {
            "stats": stats,
            "keywords": keywords,
            "readability": readability, 
            "sentiment": sentiment,
            "topics": topics
        }

    def _get_basic_stats(self, content: str) -> dict:
        """获取基础统计"""
        char_count = len(content)
        word_count = len(content.strip())
        sentence_count = len(re.split(r'[。！？!?]', content))
        paragraph_count = len([p for p in content.split('\n') if p.strip()])

        return {
            "char_count": char_count,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "paragraph_count": paragraph_count
        }

    def _extract_keywords(self, content: str, top_k: int) -> list:
        """提取关键词"""
        keywords = jieba.analyse.extract_tags(content, topK=top_k, withWeight=True)
        return [{"word": word, "weight": weight} for word, weight in keywords]

    def _analyze_readability(self, content: str, stats: dict) -> dict:
        """分析可读性"""
        if stats["sentence_count"] == 0:
            avg_sentence_len = 0
        else:
            avg_sentence_len = stats["char_count"] / stats["sentence_count"]

        if avg_sentence_len < 25:
            level = "容易阅读"
        elif avg_sentence_len < 40:
            level = "中等难度" 
        else:
            level = "需要专注阅读"

        return {
            "avg_sentence_length": round(avg_sentence_len, 1),
            "readability_level": level,
            "score": max(0, 100 - avg_sentence_len)
        }

    def _analyze_sentiment(self, content: str) -> dict:
        """情感分析"""
        positive_words = ["好", "优秀", "精彩", "喜欢", "成功", "满意", "高兴", "爱"]
        negative_words = ["坏", "差", "讨厌", "失败", "糟糕", "失望", "伤心", "恨"]

        pos_count = sum(1 for word in positive_words if word in content)
        neg_count = sum(1 for word in negative_words if word in content)
        total = pos_count + neg_count

        if total == 0:
            score = 0.5
        else:
            score = pos_count / total

        if score > 0.7:
            sentiment = "积极"
        elif score < 0.3:
            sentiment = "消极"
        else:
            sentiment = "中性"

        return {
            "sentiment": sentiment,
            "score": round(score, 2),
            "positive_words": pos_count,
            "negative_words": neg_count
        }

    def _identify_topics(self, content: str) -> list:
        """识别主题"""
        topic_keywords = {
            "科技": ["科技", "技术", "创新", "数字", "智能", "AI", "互联网"],
            "经济": ["经济", "市场", "金融", "投资", "商业", "贸易"],
            "教育": ["教育", "学习", "学校", "学生", "教师", "培训"],
            "健康": ["健康", "医疗", "医生", "医院", "疾病", "养生"]
        }

        topics = []
        for topic, keywords in topic_keywords.items():
            if any(keyword in content for keyword in keywords):
                topics.append(topic)

        return topics if topics else ["综合"]

async def analyze_content(content: str) -> str:
    """全面内容分析"""
    analyzer = ContentAnalyzer()
    analysis = await analyzer.comprehensive_analysis(content)

    result = "内容分析报告\n"
    result += "=" * 50 + "\n\n"

    stats = analysis["stats"]
    result += "基础统计:\n"
    result += f"  字符数: {stats['char_count']}\n"
    result += f"  词数: {stats['word_count']}\n"
    result += f"  句子数: {stats['sentence_count']}\n"
    result += f"  段落数: {stats['paragraph_count']}\n\n"

    result += "关键词:\n"
    for i, kw in enumerate(analysis["keywords"][:5], 1):
        result += f"  {i}. {kw['word']} ({kw['weight']:.3f})\n"
    result += "\n"

    readability = analysis["readability"]
    result += f"可读性: {readability['readability_level']}\n"
    result += f"  平均句长: {readability['avg_sentence_length']} 字符\n"
    result += f"  可读性分数: {readability['score']:.1f}/100\n\n"

    sentiment = analysis["sentiment"]
    result += f"情感分析: {sentiment['sentiment']}\n"
    result += f"  情感得分: {sentiment['score']:.2f}\n"
    result += f"  积极词: {sentiment['positive_words']}, 消极词: {sentiment['negative_words']}\n\n"

    result += f"主题分类: {', '.join(analysis['topics'])}\n"

    return result

async def extract_keywords(content: str, top_k: int = 10) -> str:
    """提取关键词"""
    analyzer = ContentAnalyzer()
    keywords = analyzer._extract_keywords(content, top_k)

    result = f"关键词提取 (前{top_k}个)\n"
    result += "=" * 50 + "\n\n"

    for i, kw in enumerate(keywords, 1):
        result += f"{i}. {kw['word']} - 权重: {kw['weight']:.3f}\n"

    return result

async def analyze_readability(content: str) -> str:
    """分析可读性"""
    analyzer = ContentAnalyzer()
    stats = analyzer._get_basic_stats(content)
    readability = analyzer._analyze_readability(content, stats)

    result = "可读性分析\n"
    result += "=" * 50 + "\n\n"

    result += f"可读性等级: {readability['readability_level']}\n"
    result += f"平均句子长度: {readability['avg_sentence_length']} 字符\n"
    result += f"可读性分数: {readability['score']:.1f}/100\n\n"

    result += "改进建议:\n"
    if readability['avg_sentence_length'] > 40:
        result += "- 句子偏长，建议拆分复杂句子\n"
    if stats['paragraph_count'] < 2:
        result += "- 建议增加段落划分，提高可读性\n"

    return result

async def sentiment_analysis(content: str) -> str:
    """情感分析"""
    analyzer = ContentAnalyzer()
    sentiment = analyzer._analyze_sentiment(content)

    result = "情感分析报告\n"
    result += "=" * 50 + "\n\n"

    result += f"情感倾向: {sentiment['sentiment']}\n"
    result += f"情感得分: {sentiment['score']:.2f}\n"
    result += f"积极词汇: {sentiment['positive_words']} 个\n"
    result += f"消极词汇: {sentiment['negative_words']} 个\n\n"

    if sentiment['score'] > 0.7:
        result += "情绪状态: 积极向上\n"
    elif sentiment['score'] < 0.3:
        result += "情绪状态: 较为消极\n"
    else:
        result += "情绪状态: 中性客观\n"

    return result

async def main():
    """主函数"""
    from mcp.cli.stdio import stdio_main
    await stdio_main(server)

if __name__ == "__main__":
    asyncio.run(main())