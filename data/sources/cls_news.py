from typing import List, Optional
from datetime import datetime
import re
import requests
from bs4 import BeautifulSoup
from loguru import logger
from core.models import News


class ClsNewsSource:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.cls.cn/"
        }
        self.api_url = "https://www.cls.cn/api/sw"
        self.news_url = "https://www.cls.cn/telegraph"
        logger.info("[财联社] 初始化成功")
    
    def get_latest_news(self, limit: int = 50) -> List[News]:
        try:
            data = {
                "app": "CailianpressWeb",
                "os": "web",
                "sv": "8.4.6",
                "sign": "1",
                "rn": str(limit),
                "refresh_type": "1",
                "last_time": ""
            }
            
            response = requests.post(
                f"{self.api_url}?api=Telegraph/List",
                headers=self.headers,
                data=data,
                timeout=10
            )
            
            result = response.json()
            
            if result.get("errno") != 0 or not result.get("data"):
                return self._crawl_news(limit)
            
            news_list = []
            for item in result["data"].get("roll_data", [])[:limit]:
                news_list.append(News(
                    title=item.get("title", "") or item.get("content", "")[:100],
                    content=item.get("content", ""),
                    source="财联社",
                    publish_time=datetime.fromtimestamp(item.get("ctime", 0))
                ))
            
            logger.info(f"[财联社] 获取 {len(news_list)} 条新闻")
            return news_list
        except Exception as e:
            logger.error(f"[财联社] API获取新闻失败: {e}")
            return self._crawl_news(limit)
    
    def _crawl_news(self, limit: int = 50) -> List[News]:
        try:
            response = requests.get(self.news_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'lxml')
            
            news_list = []
            items = soup.select('.telegraph-content')[:limit]
            
            for item in items:
                title_elem = item.select_one('.content-title')
                content_elem = item.select_one('.content-text')
                time_elem = item.select_one('.time')
                
                title = title_elem.text.strip() if title_elem else ""
                content = content_elem.text.strip() if content_elem else title
                
                publish_time = datetime.now()
                if time_elem:
                    time_str = time_elem.text.strip()
                    try:
                        hour, minute = map(int, time_str.split(':'))
                        publish_time = datetime.now().replace(hour=hour, minute=minute)
                    except:
                        pass
                
                news_list.append(News(
                    title=title or content[:100],
                    content=content,
                    source="财联社",
                    publish_time=publish_time
                ))
            
            logger.info(f"[财联社] 爬取 {len(news_list)} 条新闻")
            return news_list
        except Exception as e:
            logger.error(f"[财联社] 爬取新闻失败: {e}")
            return []
    
    def get_market_news(self, keywords: List[str] = None) -> List[News]:
        all_news = self.get_latest_news(100)
        
        if not keywords:
            keywords = ["央行", "证监会", "美联储", "北向资金", "降息", "降准", "政策", "宏观"]
        
        filtered = []
        for news in all_news:
            for keyword in keywords:
                if keyword in news.title or keyword in news.content:
                    filtered.append(news)
                    break
        
        return filtered[:20]


cls_news_source = ClsNewsSource()
