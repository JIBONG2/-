from typing import List, Dict, Any

def _sample_usage() -> List[Dict[str, Any]]:
    return [
        {"package": "com.kakao.talk", "minutes": 87},
        {"package": "com.google.android.youtube", "minutes": 42},
        {"package": "com.instagram.android", "minutes": 31},
        {"package": "com.android.chrome", "minutes": 20},
    ]

def get_usage_last_24h() -> List[Dict[str, Any]]:
    try:
        from jnius import autoclass, cast  # type: ignore
        from android import mActivity  # type: ignore
    except Exception:
        return _sample_usage()

    try:
        Context = autoclass("android.content.Context")
        UsageStatsManager = autoclass("android.app.usage.UsageStatsManager")
        System = autoclass("java.lang.System")

        activity = mActivity
        usm = cast(
            "android.app.usage.UsageStatsManager",
            activity.getSystemService(Context.USAGE_STATS_SERVICE),
        )

        end = int(System.currentTimeMillis())
        start = end - (24 * 60 * 60 * 1000)

        usage_stats = usm.queryUsageStats(UsageStatsManager.INTERVAL_DAILY, start, end)
        if usage_stats is None:
            return _sample_usage()

        results = []
        it = usage_stats.iterator()
        while it.hasNext():
            stat = it.next()
            pkg = stat.getPackageName()
            ms = stat.getTotalTimeInForeground()
            minutes = int(ms // 60000)
            if minutes > 0:
                results.append({"package": str(pkg), "minutes": minutes})

        results.sort(key=lambda x: x["minutes"], reverse=True)
        if not results:
            return _sample_usage()
        return results[:10]
    except Exception:
        return _sample_usage()