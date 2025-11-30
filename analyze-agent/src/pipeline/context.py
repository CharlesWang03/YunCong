from dataclasses import dataclass
from typing import Optional, Any

import pandas as pd


@dataclass
class SessionDataContext:
    """会话级数据上下文，存放上传 Excel 的数据及索引。"""

    df: pd.DataFrame
    bm25_index: Optional[Any] = None
    vector_index: Optional[Any] = None
