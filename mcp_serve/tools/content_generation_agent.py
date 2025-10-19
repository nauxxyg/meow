import asyncio
import random
from datetime import datetime
from mcp.server import Server
from mcp.types import TextContent, Tool
import mcp.types as types

# 创建MCP服务器实例
server = Server("content-generation-agent")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """列出内容生成工具"""
    return [
        Tool(
            name="generate_article",
            description="根据主题生成完整的文章内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "文章主题",
                        "required": True
                    },
                    "content_type": {
                        "type": "string",
                        "enum": ["news", "blog", "social_media", "report"],
                        "description": "内容类型",
                        "default": "news"
                    },
                    "tone": {
                        "type": "string", 
                        "enum": ["formal", "casual", "professional", "friendly"],
                        "description": "语气风格",
                        "default": "formal"
                    },
                    "length": {
                        "type": "string",
                        "enum": ["short", "medium", "long"],
                        "description": "内容长度", 
                        "default": "medium"
                    }
                }
            }
        ),
        Tool(
            name="generate_content_variants",
            description="为同一主题生成多个内容变体",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "内容主题",
                        "required": True
                    },
                    "num_variants": {
                        "type": "number",
                        "description": "变体数量",
                        "default": 3
                    },
                    "content_type": {
                        "type": "string",
                        "enum": ["news", "blog", "social_media"],
                        "description": "内容类型",
                        "default": "news"
                    }
                }
            }
        ),
        Tool(
            name="brainstorm_ideas",
            description="基于关键词进行创意头脑风暴",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "核心关键词", 
                        "required": True
                    },
                    "num_ideas": {
                        "type": "number",
                        "description": "创意数量",
                        "default": 5
                    }
                }
            }
        ),
        Tool(
            name="rewrite_content",
            description="重写优化现有内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "原始内容",
                        "required": True
                    },
                    "style": {
                        "type": "string",
                        "enum": ["more_formal", "more_casual", "more_concise", "more_detailed"],
                        "description": "改写风格",
                        "default": "more_concise"
                    }
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """处理工具调用"""
    if name == "generate_article":
        result = await generate_article(
            arguments["topic"],
            arguments.get("content_type", "news"),
            arguments.get("tone", "formal"),
            arguments.get("length", "medium")
        )
    elif name == "generate_content_variants":
        result = await generate_content_variants(
            arguments["topic"],
            arguments.get("num_variants", 3),
            arguments.get("content_type", "news")
        )
    elif name == "brainstorm_ideas":
        result = await brainstorm_ideas(
            arguments["keyword"],
            arguments.get("num_ideas", 5)
        )
    elif name == "rewrite_content":
        result = await rewrite_content(
            arguments["content"],
            arguments.get("style", "more_concise")
        )
    else:
        raise ValueError(f"未知工具: {name}")

    return [TextContent(type="text", text=result)]

class ContentGenerator:
    """内容生成核心逻辑"""

    def __init__(self):
        self.templates = {
            "news": {
                "title": [
                    "{topic}最新进展引发关注",
                    "专家解读{topic}发展趋势", 
                    "{topic}：行业迎来新机遇"
                ],
                "content": [
                    "近日，关于{topic}的讨论持续升温。{perspective}业内人士认为，这一趋势将推动{sector}领域的创新发展。",
                    "在当前的{sector}环境下，{topic}成为各方关注的焦点。{perspective}这为相关产业带来了新的发展机遇。"
                ]
            },
            "blog": {
                "title": [
                    "我的{topic}实践与思考",
                    "如何更好地理解{topic}",
                    "{topic}的实用指南"
                ],
                "content": [
                    "今天我想和大家分享关于{topic}的一些经验。{insight}希望这些内容对大家有所帮助。",
                    "在探索{topic}的过程中，我发现了{insight}这些经验值得与大家分享。"
                ]
            },
            "social_media": {
                "title": [
                    "{topic}太重要了！",
                    "关于{topic}，我的看法是...",
                    "{topic}冲上热搜！你怎么看？"
                ],
                "content": [
                    "大家最近关注{topic}了吗？{opinion}欢迎在评论区分享你的想法！",
                    "刚刚看到{topic}的相关讨论，真的很有启发！{opinion}一起来聊聊吧。"
                ]
            },
            "report": {
                "title": [
                    "{topic}分析报告",
                    "{topic}调研总结", 
                    "关于{topic}的深入研究"
                ],
                "content": [
                    "本报告针对{topic}进行了全面分析。研究发现，{finding}基于此，我们建议{recommendation}",
                    "通过对{topic}的深入调研，我们得出以下结论：{finding}这些发现对{sector}具有重要启示。"
                ]
            }
        }

        self.perspectives = [
            "这体现了技术发展的新趋势",
            "反映了市场需求的重大变化",
            "展示了创新应用的广阔前景", 
            "预示着行业格局的深刻变革"
        ]

        self.sectors = [
            "科技", "教育", "医疗", "金融", "制造", "零售", "娱乐"
        ]

        self.insights = [
            "实践表明，正确的方法论至关重要",
            "关键在于把握核心原理和实际应用",
            "需要平衡理论深度和实践操作性"
        ]

        self.opinions = [
            "我认为这代表了重要的发展方向",
            "这确实是一个值得深入探讨的话题",
            "从多个角度来看都很有启发意义"
        ]

        self.findings = [
            "当前存在显著的发展机遇和挑战",
            "相关技术已经趋于成熟和实用化", 
            "市场需求正在快速增长和多样化"
        ]

        self.recommendations = [
            "采取积极的创新策略",
            "加强技术研发和市场应用",
            "推动产业链协同发展"
        ]

    def generate_article_content(self, topic: str, content_type: str, tone: str, length: str) -> dict:
        """生成文章内容"""
        template = self.templates.get(content_type, self.templates["news"])

        title_template = random.choice(template["title"])
        content_template = random.choice(template["content"])

        variables = {
            "topic": topic,
            "perspective": random.choice(self.perspectives),
            "sector": random.choice(self.sectors),
            "insight": random.choice(self.insights),
            "opinion": random.choice(self.opinions),
            "finding": random.choice(self.findings),
            "recommendation": random.choice(self.recommendations)
        }

        title = title_template.format(**variables)
        content = content_template.format(**variables)

        if length == "short":
            content = content[:100] + "..."
        elif length == "long":
            content += " " + self._generate_additional_content()

        content = self._adjust_tone(content, tone)

        return {
            "title": title,
            "content": content,
            "type": content_type,
            "tone": tone,
            "length": length,
            "word_count": len(content),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    def _generate_additional_content(self) -> str:
        """生成额外内容"""
        additional_points = [
            "此外，还需要关注相关的政策环境和用户反馈。",
            "同时，技术创新的速度正在不断加快。",
            "值得注意的是，生态系统的完善至关重要。"
        ]
        return " ".join(random.sample(additional_points, 2))

    def _adjust_tone(self, content: str, tone: str) -> str:
        """调整语气风格"""
        if tone == "casual":
            content = content.replace("近日", "最近").replace("认为", "觉得")
        elif tone == "friendly":
            content = content.replace("。", "。").replace("！", "！")
        return content

async def generate_article(topic: str, content_type: str = "news", 
                          tone: str = "formal", length: str = "medium") -> str:
    """生成文章"""
    generator = ContentGenerator()
    article = generator.generate_article_content(topic, content_type, tone, length)

    result = f"生成的内容\n"
    result += "=" * 50 + "\n\n"

    result += f"标题: {article['title']}\n"
    result += f"类型: {article['type']} | 风格: {article['tone']}\n"
    result += f"长度: {article['length']} | 字数: {article['word_count']}\n"
    result += f"生成时间: {article['created_at']}\n\n"
    result += "正文:\n"
    result += article['content']

    return result

async def generate_content_variants(topic: str, num_variants: int = 3, 
                                   content_type: str = "news") -> str:
    """生成内容变体"""
    generator = ContentGenerator()

    result = f"内容变体 (主题: {topic}, 数量: {num_variants})\n"
    result += "=" * 50 + "\n\n"

    for i in range(num_variants):
        article = generator.generate_article_content(topic, content_type, "formal", "medium")
        result += f"变体 {i+1}:\n"
        result += f"标题: {article['title']}\n"
        result += f"内容: {article['content']}\n\n"
        result += "-" * 30 + "\n\n"

    return result

async def brainstorm_ideas(keyword: str, num_ideas: int = 5) -> str:
    """创意头脑风暴"""
    content_types = ["news", "blog", "social_media"]
    angles = [
        "技术原理深度解析",
        "行业应用案例分析", 
        "未来发展趋势预测",
        "实用技巧和方法论",
        "专家观点和见解"
    ]

    result = f"创意头脑风暴 (关键词: {keyword})\n"
    result += "=" * 50 + "\n\n"

    for i in range(num_ideas):
        content_type = random.choice(content_types)
        angle = random.choice(angles)

        result += f"创意 {i+1}:\n"
        result += f"- 类型: {content_type}\n"
        result += f"- 角度: {angle}\n"
        result += f"- 标题建议: 《{keyword}的{angle}》\n"
        result += f"- 内容方向: 探讨{keyword}在{angle}方面的价值和意义\n\n"

    return result

async def rewrite_content(content: str, style: str = "more_concise") -> str:
    """重写内容"""
    styles = {
        "more_formal": "经过深入分析和研究，我们认为",
        "more_casual": "我觉得吧，这个事情",
        "more_concise": "简而言之，",
        "more_detailed": "具体来说，这涉及到多个方面的考虑，包括"
    }

    prefix = styles.get(style, "")

    result = f"内容重写 (风格: {style})\n"
    result += "=" * 50 + "\n\n"

    result += "原始内容:\n"
    result += content + "\n\n"

    result += "重写版本:\n"
    result += prefix + content[:50] + "... [优化后的内容更加" + style.replace("more_", "") + "]"

    return result

async def main():
    """主函数"""
    from mcp.cli.stdio import stdio_main
    await stdio_main(server)

if __name__ == "__main__":
    asyncio.run(main())