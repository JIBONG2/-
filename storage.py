import json
import os
import time
from dataclasses import dataclass
from typing import Dict, Any

TRIAL_DAYS = 14
AD_UNLOCK_HOURS = 24  # 광고 시청 시 "상세 통계" 24시간 열기

@dataclass
class Entitlements:
    first_launch_ts: int
    is_premium: bool
    ad_unlock_until_ts: int  # 상세통계 임시 해제 만료 시각(에폭초)

    @property
    def now_ts(self) -> int:
        return int(time.time())

    @property
    def trial_active(self) -> bool:
        seconds = TRIAL_DAYS * 24 * 60 * 60
        return self.now_ts < self.first_launch_ts + seconds

    @property
    def ad_unlock_active(self) -> bool:
        return self.now_ts < self.ad_unlock_until_ts

    @property
    def access_level(self) -> str:
        if self.is_premium or self.trial_active:
            return "FULL"
        if self.ad_unlock_active:
            return "REPORT_PLUS"
        return "REPORT_ONLY"

class Storage:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def load(self) -> Entitlements:
        if not os.path.exists(self.path):
            ent = Entitlements(
                first_launch_ts=int(time.time()),
                is_premium=False,
                ad_unlock_until_ts=0,
            )
            self.save(ent)
            return ent

        with open(self.path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)

        return Entitlements(
            first_launch_ts=int(data.get("first_launch_ts", int(time.time()))),
            is_premium=bool(data.get("is_premium", False)),
            ad_unlock_until_ts=int(data.get("ad_unlock_until_ts", 0)),
        )

    def save(self, ent: Entitlements) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "first_launch_ts": ent.first_launch_ts,
                    "is_premium": ent.is_premium,
                    "ad_unlock_until_ts": ent.ad_unlock_until_ts,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    def grant_ad_unlock(self) -> Entitlements:
        ent = self.load()
        ent.ad_unlock_until_ts = int(time.time()) + AD_UNLOCK_HOURS * 3600
        self.save(ent)
        return ent

    def set_premium(self, enabled: bool) -> Entitlements:
        ent = self.load()
        ent.is_premium = enabled
        self.save(ent)
        return ent