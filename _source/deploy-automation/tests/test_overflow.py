"""④ 小螢幕橫向溢出：代表頁在 320／390／768／1024／1440 寬 scrollWidth == innerWidth。

修法前：首頁 320px 時 scrollWidth=332（`.article-card` min-width:300 撐開）；
policy.aabe.org.tw 營養午餐懶人包 390px 時 scrollWidth=543（`.sr-only` 表格
table-layout:auto 沒有真的縮到 1px）。這裡驗 aabe-deploy 的代表頁；
_policy-deploy 那頁的溢出測試在 `_policy-deploy` repo 自己的測試裡跑
（見規劃書「政策頁另跑」）。
"""
import pytest

WIDTHS = [320, 390, 768, 1024, 1440]
PAGES = ["/", "/events/", "/act/"]


@pytest.mark.parametrize("path", PAGES)
@pytest.mark.parametrize("width", WIDTHS)
def test_no_horizontal_overflow(page, local_site, path, width):
    page.set_viewport_size({"width": width, "height": 900})
    page.goto(local_site + path)
    page.wait_for_timeout(150)

    scroll_width = page.evaluate("document.documentElement.scrollWidth")
    inner_width = page.evaluate("window.innerWidth")

    assert scroll_width <= inner_width, (
        f"{path} 在 {width}px 寬度發生橫向溢出："
        f"scrollWidth={scroll_width} > innerWidth={inner_width}"
    )
