"""② 選單鍵盤可達：Playwright 390×844 實測 Tab 序列與 Enter/Space/Esc 行為。

修法前（2026-09-14 複驗紀錄）：開關是 `<label>`，Tab 從 Logo 直接跳到「加入」
按鈕，Enter/Space 完全無法觸發。修法後：`<button aria-expanded aria-controls>`
應該進入 Tab 序列、可用 Enter 或 Space 開關、Esc 可關閉並把焦點送回按鈕。
"""
import pytest

VIEWPORT = {"width": 390, "height": 844}
PAGES = ["/", "/act/", "/contact/", "/events/"]


@pytest.mark.parametrize("path", PAGES)
def test_menu_button_is_focusable_and_toggles(page, local_site, path):
    page.set_viewport_size(VIEWPORT)
    page.goto(local_site + path)

    btn = page.locator(".nav-toggle-btn")
    assert btn.count() == 1, f"{path} 找不到唯一的 .nav-toggle-btn"
    assert btn.evaluate("el => el.tagName") == "BUTTON", "開關必須是真正可聚焦的 <button>，不是 <label>"

    nav_id = btn.get_attribute("aria-controls")
    assert nav_id, "按鈕缺少 aria-controls，螢幕報讀軟體不知道它控制哪個選單"
    nav = page.locator(f"#{nav_id}")
    assert nav.count() == 1, f"aria-controls={nav_id!r} 對應不到任何元素"

    assert btn.get_attribute("aria-expanded") == "false"

    btn.focus()
    assert page.evaluate("document.activeElement === document.querySelector('.nav-toggle-btn')"), (
        "按鈕應該可以被程式化 focus（label 原生做不到這件事）"
    )

    # Enter 開啟
    page.keyboard.press("Enter")
    assert btn.get_attribute("aria-expanded") == "true", "Enter 應該能展開選單"
    assert nav.evaluate("el => getComputedStyle(el).display") == "flex", "aria-expanded=true 時選單應可見"

    # Esc 關閉並把焦點送回按鈕
    page.keyboard.press("Escape")
    assert btn.get_attribute("aria-expanded") == "false", "Esc 應該能收合選單"
    assert page.evaluate("document.activeElement === document.querySelector('.nav-toggle-btn')"), (
        "Esc 關閉後焦點應回到開關按鈕"
    )

    # Space 也要能開啟（原生 <button> 預設行為，不靠額外 JS）
    btn.focus()
    page.keyboard.press("Space")
    assert btn.get_attribute("aria-expanded") == "true", "Space 應該也能展開選單"


def test_tab_sequence_reaches_menu_button(page, local_site):
    """複驗報告的原始症狀：從 Logo 開始 Tab，選單開關必須出現在序列中。"""
    page.set_viewport_size(VIEWPORT)
    page.goto(local_site + "/")

    logo = page.locator(".topbar-logo")
    logo.focus()

    seen_tags = []
    found = False
    for _ in range(6):
        page.keyboard.press("Tab")
        info = page.evaluate(
            "() => { const el = document.activeElement;"
            " return {tag: el.tagName, cls: el.className, expanded: el.getAttribute('aria-expanded')}; }"
        )
        seen_tags.append(info)
        if "nav-toggle-btn" in (info.get("cls") or ""):
            found = True
            assert info["tag"] == "BUTTON"
            break

    assert found, f"Tab 6 次都沒有聚焦到選單開關，實際序列：{seen_tags}"
