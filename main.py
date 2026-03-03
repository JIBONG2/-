import os
import time

from kivy.app import App
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from typing import Optional
from storage import Storage, Entitlements
from android_usage import get_usage_last_24h


# -----------------------------
# Font helper (no-crash)
# -----------------------------
def _find_korean_font_path() -> Optional[str]:
    """
    우선순위:
    1) 프로젝트 폴더의 fonts/NotoSansKR-Regular.otf
    2) Windows 기본 한글 폰트(맑은 고딕 등)
    없으면 None
    """
    base_dir = os.path.dirname(__file__)
    noto_path = os.path.join(base_dir, "fonts", "NotoSansKR-Regular.otf")
    if os.path.exists(noto_path):
        return noto_path

    # Windows common font paths
    win_fonts = [
        r"C:\Windows\Fonts\malgun.ttf",        # Malgun Gothic Regular
        r"C:\Windows\Fonts\malgunsl.ttf",      # Malgun Gothic Semilight
        r"C:\Windows\Fonts\NanumGothic.ttf",   # if installed
    ]
    for p in win_fonts:
        if os.path.exists(p):
            return p

    return None


def _build_kv(use_korean_font: bool) -> str:
    font_rules = ""
    if use_korean_font:
        # 전역 기본 폰트 적용(모든 Label/Button)
        font_rules = r"""
<Label>:
    font_name: "KoreanFont"
<Button>:
    font_name: "KoreanFont"
"""

    return r"""
#:kivy 2.3.0
""" + font_rules + r"""

<Header@BoxLayout>:
    title: ""
    size_hint_y: None
    height: dp(56)
    padding: dp(12), 0
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: 0.12, 0.12, 0.12, 1
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: root.title
        bold: True
        color: 1,1,1,1
        halign: "left"
        valign: "middle"
        text_size: self.size

<ReportRow>:
    size_hint_y: None
    height: dp(42)
    padding: dp(12), 0
    spacing: dp(8)
    Label:
        text: root.pkg
        halign: "left"
        valign: "middle"
        text_size: self.size
    Label:
        text: root.mins
        size_hint_x: None
        width: dp(80)
        halign: "right"
        valign: "middle"
        text_size: self.size

<HomeScreen>:
    BoxLayout:
        orientation: "vertical"

        Header:
            title: "부모용 리포트 (MVP)"

        BoxLayout:
            size_hint_y: None
            height: dp(40)
            padding: dp(12), dp(6)
            Label:
                id: status_label
                text: root.status_text
                halign: "left"
                valign: "middle"
                text_size: self.size

        ScrollView:
            BoxLayout:
                id: list_box
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height

        # 무료 버전 배너 영역 (진짜 AdMob은 별도 연동 필요)
        BoxLayout:
            id: banner_box
            size_hint_y: None
            height: dp(52)
            padding: dp(12), dp(8)
            canvas.before:
                Color:
                    rgba: 0.92, 0.92, 0.92, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: "무료 배너 광고 자리(AdMob 연동 시 교체)"
                color: 0.1,0.1,0.1,1

        BoxLayout:
            size_hint_y: None
            height: dp(64)
            padding: dp(12), dp(10)
            spacing: dp(10)

            Button:
                text: "새로고침"
                on_release: root.refresh()

            Button:
                text: "설정/결제"
                on_release: app.root.current = "settings"

<SettingsScreen>:
    BoxLayout:
        orientation: "vertical"
        Header:
            title: "설정 / 결제"

        BoxLayout:
            orientation: "vertical"
            padding: dp(12), dp(12)
            spacing: dp(10)

            Label:
                text: root.status_text
                halign: "left"
                valign: "top"
                text_size: self.width, None
                size_hint_y: None
                height: self.texture_size[1] + dp(6)

            BoxLayout:
                size_hint_y: None
                height: dp(48)
                spacing: dp(10)

                Button:
                    text: "광고 보고 상세통계 24시간"
                    on_release: root.simulate_reward_ad()

                Button:
                    text: "프리미엄 ON(테스트)"
                    on_release: root.set_premium(True)

            BoxLayout:
                size_hint_y: None
                height: dp(48)
                spacing: dp(10)

                Button:
                    text: "프리미엄 OFF(테스트)"
                    on_release: root.set_premium(False)

                Button:
                    text: "홈으로"
                    on_release: app.root.current = "home"

            Label:
                text: "※ 실제 결제(구독)와 AdMob 보상형 광고는 별도 SDK 연동이 필요해요.\\n이 MVP는 정책/흐름 검증용입니다."
                halign: "left"
                valign: "top"
                text_size: self.width, None
"""


class ReportRow(BoxLayout):
    pkg = StringProperty("")
    mins = StringProperty("")


class HomeScreen(Screen):
    status_text = StringProperty("")
    usage_items = ListProperty([])

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        ent = app.entitlements
        access = ent.access_level

        # 무료 배너는 프리미엄/체험에는 숨김
        banner = self.ids.banner_box
        banner.height = dp(52) if (not ent.is_premium and not ent.trial_active) else 0

        usage = get_usage_last_24h()
        total_minutes = sum(x["minutes"] for x in usage)

        if access == "REPORT_ONLY":
            shown = usage[:3]
            note = "무료(제한): 리포트만(상위 3개)"
        elif access == "REPORT_PLUS":
            shown = usage[:10]
            note = "광고해제: 상세 리포트(24시간)"
        else:
            shown = usage[:10]
            note = "체험/프리미엄: 전체 기능"

        self.status_text = f"{note}  |  총 사용: {total_minutes}분"

        box = self.ids.list_box
        box.clear_widgets()
        for item in shown:
            box.add_widget(ReportRow(pkg=item["package"], mins=f'{item["minutes"]}분'))


class SettingsScreen(Screen):
    status_text = StringProperty("")

    def on_pre_enter(self, *args):
        self._refresh_status()

    def _refresh_status(self):
        app = App.get_running_app()
        ent = app.entitlements

        now = int(time.time())
        trial_end = ent.first_launch_ts + 14 * 24 * 3600
        trial_left_days = max(0, trial_end - now) // (24 * 3600)

        ad_left_h = max(0, ent.ad_unlock_until_ts - now) // 3600

        self.status_text = (
            f"- 프리미엄: {'ON' if ent.is_premium else 'OFF'}\n"
            f"- 체험: {'ON' if ent.trial_active else 'OFF'} (남은 일수: {trial_left_days}일)\n"
            f"- 광고해제(상세통계): {'ON' if ent.ad_unlock_active else 'OFF'} (남은 시간: {ad_left_h}시간)\n"
            f"- 현재 접근 레벨: {ent.access_level}\n"
            f"\n가격 정책 예시:\n"
            f"  · 14일 무료체험\n"
            f"  · 월 3,900원 / 연 29,000원\n"
            f"  · 무료는 리포트만, 광고 시청 시 24시간 상세통계"
        )

    def simulate_reward_ad(self):
        app = App.get_running_app()
        app.entitlements = app.storage.grant_ad_unlock()
        self._refresh_status()

    def set_premium(self, enabled: bool):
        app = App.get_running_app()
        app.entitlements = app.storage.set_premium(enabled)
        self._refresh_status()


class Root(ScreenManager):
    pass


class ParentalReportApp(App):
    def build(self):
        # 폰트가 있으면 등록하고 KV에 전역 폰트 적용
        font_path = _find_korean_font_path()
        use_korean_font = font_path is not None

        if use_korean_font:
            from kivy.core.text import LabelBase
            LabelBase.register(name="KoreanFont", fn_regular=font_path)

        kv = _build_kv(use_korean_font)
        Builder.load_string(kv)

        data_dir = self.user_data_dir
        path = os.path.join(data_dir, "entitlements.json")
        self.storage = Storage(path)
        self.entitlements: Entitlements = self.storage.load()

        sm = Root()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(SettingsScreen(name="settings"))
        return sm


if __name__ == "__main__":
    ParentalReportApp().run()