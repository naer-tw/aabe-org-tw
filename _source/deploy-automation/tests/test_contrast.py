"""③ 橙色文字對比：首頁、活動、行動、聯絡四頁所有可見橙色文字節點 ≥4.5:1（大字 ≥3:1）。

修法前 `--brand-orange` #EB9B31 on 白底 = 2.267:1，全站不合格。修法後文字
專用 `--brand-orange-text` #9A5A0C，實測 5.47:1。這裡不假設頁面上還剩多少
處橙色文字，而是直接掃描四頁所有「computed color 落在橙色系」的文字節點，
逐一算 WCAG 對比，只要有一個不合格就整條測試失敗並列出節點與數值。
"""
import pytest

PAGES = ["/", "/events/", "/act/", "/contact/"]

# 掃描腳本：找出所有可見、有文字內容、顏色偏橙的葉節點，回傳 [{tag, cls, text, color, bg, fontSize, bold}]
#
# 背景色解析（2026-09-14 修正）：第一版只看 computed backgroundColor，遇到
# rgba() 半透明或 background-image 漸層（例如 /act/ 的 .reform-entry 深色卡）
# 就誤判成白底，把「亮橘字在近黑卡片上、實測 6-8:1」的合格案例錯報成
# 2.27:1 不合格。改為：往上walk 收集每一層的顏色（rgba 保留 alpha；
# background-image 是 linear-gradient 時取色標平均、視為不透明的一層），
# 再由最外層往內做 alpha 合成，逼近瀏覽器實際畫面。
SCAN_JS = r"""
() => {
  function isOrange([r, g, b]) {
    // 偏橙色系：紅通道明顯高於藍，且不是灰階，也不是純紅/純黃
    return r > 140 && r - b > 40 && r >= g && g > b;
  }
  function parseRGBA(str) {
    const m = str.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
    if (!m) return null;
    return [parseInt(m[1]), parseInt(m[2]), parseInt(m[3]), m[4] !== undefined ? parseFloat(m[4]) : 1];
  }
  function hexToRgb(h) {
    h = h.replace('#', '');
    if (h.length === 3) h = h.split('').map(c => c + c).join('');
    const num = parseInt(h, 16);
    return [(num >> 16) & 255, (num >> 8) & 255, num & 255];
  }
  function gradientLayer(bgImage) {
    // 把漸層的每個色標視為 [r,g,b,a]（hex 無 alpha 視為 1），
    // 用「各色標自己的 alpha」當權重取加權平均色，layer 的有效 alpha
    // 取色標 alpha 的最大值——半透明色標（如 6% 橘）加權平均後仍該
    // 是「幾乎透明的淡橘」，不能把 rgba(0,0,0,0) 這種完全透明的停駐點
    // 當成不透明黑去拉低平均值（這是第一版最初的 bug：兩個停駐點各佔
    // 50% 直接平均 RGB，把「幾乎看不見的漸層」誤判成一半不透明的深色）。
    const stops = [];
    (bgImage.match(/#[0-9a-fA-F]{3,6}/g) || []).forEach(h => stops.push([...hexToRgb(h), 1]));
    (bgImage.match(/rgba?\([^)]+\)/g) || []).forEach(s => {
      const c = parseRGBA(s);
      if (c) stops.push(c);
    });
    if (!stops.length) return null;
    const totalA = stops.reduce((s, c) => s + c[3], 0);
    if (totalA <= 0) return [0, 0, 0, 0]; // 全部停駐點都透明，等於沒畫東西
    const avg = [0, 0, 0];
    stops.forEach(c => { avg[0] += c[0] * c[3]; avg[1] += c[1] * c[3]; avg[2] += c[2] * c[3]; });
    const maxA = Math.max(...stops.map(c => c[3]));
    return [avg[0] / totalA, avg[1] / totalA, avg[2] / totalA, maxA];
  }
  function compositeOver(fg, bgRgb) {
    const a = fg[3];
    return [fg[0] * a + bgRgb[0] * (1 - a), fg[1] * a + bgRgb[1] * (1 - a), fg[2] * a + bgRgb[2] * (1 - a)];
  }
  function effectiveBg(el) {
    let node = el;
    const chain = []; // 由近到遠（el 自己最先）
    while (node) {
      const cs = getComputedStyle(node);
      let layer = null;
      if (cs.backgroundImage && cs.backgroundImage !== 'none') {
        layer = gradientLayer(cs.backgroundImage);
      }
      if (!layer) {
        const rgba = parseRGBA(cs.backgroundColor);
        if (rgba && rgba[3] > 0) layer = rgba;
      }
      if (layer) {
        chain.push(layer);
        if (layer[3] >= 0.999) break; // 已經完全不透明，上面的層畫不出來了
      }
      node = node.parentElement;
    }
    if (!chain.length) return [255, 255, 255];
    let result = [255, 255, 255]; // 找不到不透明層時的預設畫布（白）
    for (let i = chain.length - 1; i >= 0; i--) {
      result = compositeOver(chain[i], result);
    }
    return result;
  }
  const results = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
  let node;
  while ((node = walker.nextNode())) {
    const text = node.textContent.trim();
    if (!text) continue;
    const el = node.parentElement;
    if (!el) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) continue;
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) continue;
    const color = parseRGBA(cs.color);
    if (!color || !isOrange(color)) continue;
    const bg = effectiveBg(el);
    results.push({
      tag: el.tagName,
      cls: el.className && el.className.toString ? el.className.toString() : '',
      text: text.slice(0, 30),
      color: color.slice(0, 3), bg,
      fontSize: parseFloat(cs.fontSize),
      bold: parseInt(cs.fontWeight) >= 700,
    });
  }
  return results;
}
"""


def _luminance(rgb):
    def chan(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)


def _contrast(c1, c2):
    l1, l2 = _luminance(c1), _luminance(c2)
    l1, l2 = max(l1, l2), min(l1, l2)
    return (l1 + 0.05) / (l2 + 0.05)


@pytest.mark.parametrize("path", PAGES)
def test_orange_text_meets_wcag(page, local_site, path):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(local_site + path)
    page.wait_for_timeout(200)

    nodes = page.evaluate(SCAN_JS)
    failures = []
    for n in nodes:
        ratio = _contrast(tuple(n["color"]), tuple(n["bg"]))
        is_large = n["fontSize"] >= 24 or (n["fontSize"] >= 18.66 and n["bold"])
        threshold = 3.0 if is_large else 4.5
        if ratio < threshold:
            failures.append(
                f"{n['tag']}.{n['cls']!r} \"{n['text']}\" "
                f"color={n['color']} bg={n['bg']} ratio={ratio:.2f} "
                f"threshold={threshold} (large={is_large})"
            )

    assert not failures, (
        f"{path} 有 {len(failures)} 個橙色文字節點對比不足：\n" + "\n".join(failures)
    )
    assert len(nodes) > 0 or path == "/contact/", (
        f"{path} 完全沒掃到橙色文字節點，掃描腳本可能失效，需要人工確認"
    )
