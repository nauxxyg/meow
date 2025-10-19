import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List
from mcp.server import Server
from mcp.types import TextContent, Tool
import mcp.types as types

# 创建MCP服务器实例
server = Server("publishing-agent")

@dataclass
class PublishingTask:
    """发布任务数据类"""
    id: str
    title: str
    content: str
    platform: str
    scheduled_time: datetime
    status: str  # pending, published, failed, cancelled
    tags: List[str]
    created_at: datetime

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """列出发布管理工具"""
    return [
        Tool(
            name="schedule_publication",
            description="安排内容发布任务",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "内容标题",
                        "required": True
                    },
                    "content": {
                        "type": "string",
                        "description": "内容正文", 
                        "required": True
                    },
                    "platform": {
                        "type": "string",
                        "enum": ["微信公众号", "微博", "知乎", "头条", "小红书", "B站"],
                        "description": "发布平台",
                        "required": True
                    },
                    "scheduled_time": {
                        "type": "string", 
                        "description": "计划发布时间 (格式: YYYY-MM-DD HH:MM)",
                        "default": None
                    }
                }
            }
        ),
        Tool(
            name="view_publishing_schedule",
            description="查看发布计划",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "查看特定日期的计划 (格式: YYYY-MM-DD)",
                        "default": None
                    },
                    "platform": {
                        "type": "string", 
                        "description": "筛选特定平台",
                        "default": None
                    }
                }
            }
        ),
        Tool(
            name="get_optimal_posting_times",
            description="获取最佳发布时间建议",
            inputSchema={
                "type": "object",
                "properties": {
                    "platform": {
                        "type": "string",
                        "description": "特定平台的建议",
                        "default": None
                    }
                }
            }
        ),
        Tool(
            name="publishing_analytics",
            description="发布数据统计分析", 
            inputSchema={
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["day", "week", "month", "all"],
                        "description": "统计周期",
                        "default": "week"
                    }
                }
            }
        ),
        Tool(
            name="generate_publishing_calendar",
            description="生成发布日历",
            inputSchema={
                "type": "object", 
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "开始日期 (YYYY-MM-DD)",
                        "required": True
                    },
                    "end_date": {
                        "type": "string",
                        "description": "结束日期 (YYYY-MM-DD)",
                        "required": True
                    }
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """处理工具调用"""
    if name == "schedule_publication":
        result = await schedule_publication(
            arguments["title"],
            arguments["content"],
            arguments["platform"], 
            arguments.get("scheduled_time")
        )
    elif name == "view_publishing_schedule":
        result = await view_publishing_schedule(
            arguments.get("date"),
            arguments.get("platform")
        )
    elif name == "get_optimal_posting_times":
        result = await get_optimal_posting_times(arguments.get("platform"))
    elif name == "publishing_analytics":
        result = await publishing_analytics(arguments.get("period", "week"))
    elif name == "generate_publishing_calendar":
        result = await generate_publishing_calendar(
            arguments["start_date"],
            arguments["end_date"]
        )
    else:
        raise ValueError(f"未知工具: {name}")

    return [TextContent(type="text", text=result)]

class PublishingManager:
    """发布管理核心逻辑"""

    def __init__(self):
        self.tasks: Dict[str, PublishingTask] = {}
        self.task_counter = 0

        self.platforms = ["微信公众号", "微博", "知乎", "头条", "小红书", "B站"]

        self.optimal_times = {
            "微信公众号": ["09:00", "12:00", "17:00", "20:00"],
            "微博": ["07:00", "12:00", "18:00", "22:00"],
            "知乎": ["08:00", "13:00", "19:00", "21:00"], 
            "头条": ["07:00", "12:00", "18:00", "20:00"],
            "小红书": ["10:00", "15:00", "19:00", "21:00"],
            "B站": ["11:00", "17:00", "20:00", "22:00"]
        }

    def create_task(self, title: str, content: str, platform: str, scheduled_time: str = None) -> PublishingTask:
        """创建发布任务"""
        self.task_counter += 1
        task_id = f"task_{self.task_counter:04d}"

        if scheduled_time:
            scheduled_dt = datetime.strptime(scheduled_time, "%Y-%m-%d %H:%M")
        else:
            scheduled_dt = datetime.now() + timedelta(hours=1)

        task = PublishingTask(
            id=task_id,
            title=title,
            content=content,
            platform=platform,
            scheduled_time=scheduled_dt,
            status="pending",
            tags=self._generate_tags(title),
            created_at=datetime.now()
        )

        self.tasks[task_id] = task
        return task

    def _generate_tags(self, title: str) -> List[str]:
        """生成标签"""
        tags = []
        if any(word in title for word in ["AI", "人工智能", "科技"]):
            tags.append("科技")
        if any(word in title for word in ["教育", "学习", "知识"]):
            tags.append("教育")
        if any(word in title for word in ["健康", "医疗", "养生"]):
            tags.append("健康")
        return tags if tags else ["综合"]

    def get_tasks(self, date: str = None, platform: str = None) -> List[PublishingTask]:
        """获取任务列表"""
        tasks = list(self.tasks.values())

        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            tasks = [t for t in tasks if t.scheduled_time.date() == target_date]

        if platform:
            tasks = [t for t in tasks if t.platform == platform]

        return sorted(tasks, key=lambda x: x.scheduled_time)

    def get_optimal_times(self, platform: str = None) -> Dict:
        """获取最佳发布时间"""
        if platform and platform in self.optimal_times:
            return {
                "platform": platform,
                "optimal_times": self.optimal_times[platform],
                "reasoning": self._get_time_reasoning(platform)
            }
        else:
            return {
                "all_platforms": self.optimal_times,
                "recommendation": "不同平台有不同的用户活跃时间段"
            }

    def _get_time_reasoning(self, platform: str) -> str:
        """获取时间选择理由"""
        reasoning = {
            "微信公众号": "上班通勤、午休、下班后、晚间休息时段",
            "微博": "早晨醒来、午休、下班路上、睡前浏览",
            "知乎": "工作时间、午休、晚饭后、睡前学习",
            "头条": "通勤、午休、下班后、晚间娱乐",
            "小红书": "上午活跃、下午茶、晚饭后、睡前购物",
            "B站": "午休、下班后、黄金时段、深夜时段"
        }
        return reasoning.get(platform, "基于用户活跃数据统计")

    def get_analytics(self, period: str = "week") -> Dict:
        """获取分析数据"""
        tasks = self.tasks.values()

        if period != "all":
            if period == "day":
                cutoff = datetime.now() - timedelta(days=1)
            elif period == "week":
                cutoff = datetime.now() - timedelta(weeks=1) 
            elif period == "month":
                cutoff = datetime.now() - timedelta(days=30)
            tasks = [t for t in tasks if t.created_at >= cutoff]

        total_tasks = len(tasks)
        published_tasks = len([t for t in tasks if t.status == "published"])
        pending_tasks = len([t for t in tasks if t.status == "pending"])
        failed_tasks = len([t for t in tasks if t.status == "failed"])

        platform_dist = {}
        for task in tasks:
            platform_dist[task.platform] = platform_dist.get(task.platform, 0) + 1

        hour_dist = {}
        for task in tasks:
            hour = task.scheduled_time.hour
            hour_dist[hour] = hour_dist.get(hour, 0) + 1

        return {
            "total_tasks": total_tasks,
            "published_tasks": published_tasks,
            "pending_tasks": pending_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": published_tasks / total_tasks if total_tasks > 0 else 0,
            "platform_distribution": platform_dist,
            "hour_distribution": hour_dist
        }

    def generate_calendar(self, start_date: str, end_date: str) -> Dict:
        """生成发布日历"""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        calendar = {}
        current_dt = start_dt

        while current_dt <= end_dt:
            date_str = current_dt.strftime("%Y-%m-%d")
            calendar[date_str] = [
                task for task in self.tasks.values()
                if task.scheduled_time.date() == current_dt.date()
            ]
            current_dt += timedelta(days=1)

        return calendar

async def schedule_publication(title: str, content: str, platform: str, scheduled_time: str = None) -> str:
    """安排发布任务"""
    manager = PublishingManager()
    task = manager.create_task(title, content, platform, scheduled_time)

    result = "发布任务安排成功\n"
    result += "=" * 50 + "\n\n"

    result += f"任务ID: {task.id}\n"
    result += f"标题: {task.title}\n"
    result += f"平台: {task.platform}\n"
    result += f"计划时间: {task.scheduled_time.strftime('%Y-%m-%d %H:%M')}\n"
    result += f"状态: {task.status}\n"
    result += f"标签: {', '.join(task.tags)}\n"
    result += f"创建时间: {task.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"

    result += "任务已加入发布队列，将在计划时间自动发布。"

    return result

async def view_publishing_schedule(date: str = None, platform: str = None) -> str:
    """查看发布计划"""
    manager = PublishingManager()
    tasks = manager.get_tasks(date, platform)

    if date:
        result = f"发布计划 - {date}\n"
    else:
        result = "所有发布任务\n"

    if platform:
        result += f"平台: {platform}\n"

    result += "=" * 50 + "\n\n"

    if not tasks:
        result += "暂无发布任务"
        return result

    pending_tasks = [t for t in tasks if t.status == "pending"]
    published_tasks = [t for t in tasks if t.status == "published"]

    if pending_tasks:
        result += "待发布任务:\n\n"
        for task in sorted(pending_tasks, key=lambda x: x.scheduled_time):
            result += f"- {task.scheduled_time.strftime('%m-%d %H:%M')} - {task.title}\n"
            result += f"  平台: {task.platform} | ID: {task.id}\n\n"

    if published_tasks:
        result += "已发布任务:\n\n"
        for task in sorted(published_tasks, key=lambda x: x.scheduled_time, reverse=True)[:5]:
            result += f"- {task.scheduled_time.strftime('%m-%d %H:%M')} - {task.title}\n"
            result += f"  平台: {task.platform}\n\n"

    return result

async def get_optimal_posting_times(platform: str = None) -> str:
    """获取最佳发布时间"""
    manager = PublishingManager()
    optimal_times = manager.get_optimal_times(platform)

    if platform:
        result = f"最佳发布时间 - {platform}\n"
        result += "=" * 50 + "\n\n"

        result += "推荐时段:\n"
        for time in optimal_times["optimal_times"]:
            result += f"- {time}\n"

        result += f"\n理由: {optimal_times['reasoning']}\n"
        result += "基于用户活跃度和互动数据统计"
    else:
        result = "各平台最佳发布时间\n"
        result += "=" * 50 + "\n\n"

        for platform, times in optimal_times["all_platforms"].items():
            result += f"{platform}:\n"
            for time in times:
                result += f"  - {time}\n"
            result += "\n"

        result += "建议根据目标受众的活跃时间选择发布时段"

    return result

async def publishing_analytics(period: str = "week") -> str:
    """发布数据分析"""
    manager = PublishingManager()
    analytics = manager.get_analytics(period)

    period_names = {
        "day": "今日",
        "week": "本周", 
        "month": "本月",
        "all": "全部"
    }

    result = f"发布数据分析 - {period_names.get(period, period)}\n"
    result += "=" * 50 + "\n\n"

    result += "任务统计:\n"
    result += f"- 总任务数: {analytics['total_tasks']}\n"
    result += f"- 已发布: {analytics['published_tasks']}\n"
    result += f"- 待发布: {analytics['pending_tasks']}\n"
    result += f"- 失败: {analytics['failed_tasks']}\n"
    result += f"- 成功率: {analytics['success_rate']:.1%}\n\n"

    if analytics['platform_distribution']:
        result += "平台分布:\n"
        for platform, count in analytics['platform_distribution'].items():
            result += f"- {platform}: {count}个任务\n"

    return result

async def generate_publishing_calendar(start_date: str, end_date: str) -> str:
    """生成发布日历"""
    manager = PublishingManager()
    calendar = manager.generate_calendar(start_date, end_date)

    result = f"发布日历 {start_date} 至 {end_date}\n"
    result += "=" * 50 + "\n\n"

    has_tasks = False
    for date_str, tasks in calendar.items():
        if tasks:
            has_tasks = True
            result += f"{date_str}:\n"
            for task in tasks:
                status_text = "待发布" if task.status == "pending" else "已发布" if task.status == "published" else "失败"
                result += f"  {task.scheduled_time.strftime('%H:%M')} - {task.title}\n"
                result += f"     平台: {task.platform} | 状态: {status_text}\n"
            result += "\n"

    if not has_tasks:
        result += "该时间段内暂无发布任务"

    return result

async def main():
    """主函数"""
    from mcp.cli.stdio import stdio_main
    await stdio_main(server)

if __name__ == "__main__":
    asyncio.run(main())