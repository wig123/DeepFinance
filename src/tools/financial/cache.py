"""数据缓存机制

使用 diskcache 实现持久化缓存，支持：
- 按数据类型设置不同 TTL
- 缓存键自动生成
- 缓存统计
"""

import hashlib
import json
from datetime import timedelta
from pathlib import Path
from typing import Any, Optional, Callable
from functools import wraps

from diskcache import Cache


# 默认缓存目录
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "deepfinance"

# 不同数据类型的默认 TTL（秒）
DEFAULT_TTL = {
    "kline": 3600,          # K线数据：1小时
    "kline_daily": 14400,   # 日K线：4小时
    "financial": 86400,     # 财务报表：1天
    "company_info": 604800, # 公司信息：7天
    "realtime": 60,         # 实时数据：1分钟
}


class FinancialCache:
    """金融数据缓存管理器"""

    def __init__(self, cache_dir: Optional[Path] = None):
        """初始化缓存

        Args:
            cache_dir: 缓存目录，默认 ~/.cache/deepfinance
        """
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache = Cache(str(self.cache_dir))

    def _make_key(self, prefix: str, **kwargs) -> str:
        """生成缓存键

        Args:
            prefix: 键前缀（如 "akshare:kline"）
            **kwargs: 查询参数

        Returns:
            str: 缓存键
        """
        # 排序参数确保相同参数生成相同键
        sorted_params = sorted(kwargs.items())
        params_str = json.dumps(sorted_params, ensure_ascii=False, default=str)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        return f"{prefix}:{params_hash}"

    def get(self, key: str) -> Optional[Any]:
        """获取缓存数据

        Args:
            key: 缓存键

        Returns:
            缓存的数据，未命中返回 None
        """
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存数据

        Args:
            key: 缓存键
            value: 数据
            ttl: 过期时间（秒），默认1小时
        """
        expire = ttl or DEFAULT_TTL.get("kline", 3600)
        self._cache.set(key, value, expire=expire)

    def get_or_fetch(
        self,
        prefix: str,
        fetch_func: Callable[[], Any],
        data_type: str = "kline",
        **kwargs
    ) -> tuple[Any, bool]:
        """获取缓存或调用函数获取数据

        Args:
            prefix: 缓存键前缀
            fetch_func: 数据获取函数
            data_type: 数据类型（决定 TTL）
            **kwargs: 查询参数

        Returns:
            tuple[data, from_cache]: 数据和是否来自缓存
        """
        key = self._make_key(prefix, **kwargs)
        cached = self.get(key)

        if cached is not None:
            return cached, True

        # 调用函数获取新数据
        data = fetch_func()
        if data is not None:
            ttl = DEFAULT_TTL.get(data_type, 3600)
            self.set(key, data, ttl=ttl)

        return data, False

    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()

    def stats(self) -> dict:
        """缓存统计信息"""
        return {
            "size": len(self._cache),
            "volume": self._cache.volume(),
            "directory": str(self.cache_dir),
        }

    def close(self) -> None:
        """关闭缓存"""
        self._cache.close()


# 全局缓存实例
_cache: Optional[FinancialCache] = None


def get_cache() -> FinancialCache:
    """获取全局缓存实例"""
    global _cache
    if _cache is None:
        _cache = FinancialCache()
    return _cache


def cached(prefix: str, data_type: str = "kline"):
    """缓存装饰器

    Usage:
        @cached("akshare:kline", data_type="kline_daily")
        def get_stock_kline(symbol: str, period: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            # 合并位置参数和关键字参数
            all_kwargs = kwargs.copy()
            if args:
                # 获取函数参数名
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                for i, arg in enumerate(args):
                    if i < len(params):
                        all_kwargs[params[i]] = arg

            key = cache._make_key(prefix, **all_kwargs)
            cached_data = cache.get(key)

            if cached_data is not None:
                return cached_data, True

            result = func(*args, **kwargs)
            if result is not None:
                ttl = DEFAULT_TTL.get(data_type, 3600)
                cache.set(key, result, ttl=ttl)

            return result, False

        return wrapper
    return decorator
