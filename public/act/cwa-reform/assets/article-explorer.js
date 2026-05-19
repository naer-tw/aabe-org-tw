// 互動式 A 級 22 條表 — 官網風格 (#EB9B31)
// 章節篩選 / 關鍵字搜尋 / 三欄滑動切換 / 複製條號 / hash 分享單條 URL

(function () {
  const A_LEVEL_22 = [
    {no:'§ 1',ch:'1 總則',topic:'立法目的',bench:{aabe:'建議補列「兒少最佳利益作為解釋與適用之最高原則」，對應 CRC 第 3 條。',draft:'草案維持原條文「為促進兒童及少年身心健全發展，特制定本法」。',intl:'CRC 第 3 條兒少最佳利益原則為締約國立法之基準；英國 Children Act 1989 §1 明列 paramountcy principle。'}},
    {no:'§ 2',ch:'1 總則',topic:'中央主管機關身份（雙條同修第一條）',bench:{aabe:'本盟主張改為「兒童家庭部」，作為行政院所屬二級機關（部會層級）。雙條同修第一條。',draft:'草案維持中央主管機關為衛生福利部，下設兒少及家庭支持署（三級機關）。',intl:'日本 2023 こども家庭庁設置法第 1 條（內閣府外局）、愛爾蘭 2014 Tusla Act、英國 2004 Children Act 第 11 條。'}},
    {no:'§ 3',ch:'1 總則',topic:'主管機關權責劃分（雙條同修第二條）',bench:{aabe:'本盟主張增訂兒童家庭部對 19 款目的事業主管機關之資料提出要求、說明要求、必要協力請求權，以及政策企劃、立案與綜合調整之法定權限。',draft:'草案列 19 款目的事業主管機關各自分工。維持「應全力配合」之非強制協調語。',intl:'日本こども家庭庁設置法第 5 條明定對相關行政機關之資料提出要求、說明要求與必要協力請求權。'}},
    {no:'§ 6',ch:'1 總則',topic:'兒少工作者定義',bench:{aabe:'本盟主張擴大納入服務、休閒、宗教教養機構人員、運動教練、補習班教師等實質接觸兒少之領域（採人本基金會主張）。',draft:'草案維持以「依本法或其他法令辦理兒少福利相關業務之人員」為定義，未明列宗教教養、運動教練、補習班等。',intl:'澳洲 Working with Children Check（維多利亞州 2006）強制涵蓋宗教教養、運動教練、補習班；英國 DBS Enhanced Check 涵蓋宗教與教育場域。'}},
    {no:'§ 22',ch:'2 身分及家庭',topic:'收出養媒合服務機構之資格與管理',bench:{aabe:'建議補列兒少最佳利益審查機制；對跨國收養之特別要件連動海牙公約標準。',draft:'草案規定收出養媒合服務機構之資格、管理、評鑑與監督。',intl:'CRC 第 21 條收養兒童；海牙國際收養公約（1993）建立跨國收養之中央主管機關制度。'}},
    {no:'§ 23',ch:'2 身分及家庭',topic:'收養人於收養兒少前之要件',bench:{aabe:'建議第 2 項補列「收養申請人之審查應以兒童最佳利益為最高考量，並接受社工專業評估」；明定跨國收養應符合海牙公約標準。',draft:'草案規定收養人於收養前應向收出養媒合服務機構提供媒合服務，並規定申請人應符合條件。',intl:'CRC 第 21 條收養兒童；海牙國際收養公約（1993）。'}},
    {no:'§ 46',ch:'3 健康及安全',topic:'心理健康促進與自殺防治（新增條）',bench:{aabe:'5 項補強：跨機關協調機制、ACEs 篩檢、學校心理健康整合、自殺防治整合、跨部會升格。',draft:'新增條，明定中央主管機關依精神衛生法與自殺防治法，會同教育主管機關規劃兒少心理健康促進與自殺防治策略。僅 1 段文字無執行細節。',intl:'WHO/UNICEF Mental Health of Children Service Guidance（2024）；CRC GC No. 15（2013）；CDC ACEs Public Health Strategy；日本こども家庭庁健康成育局。'}},
    {no:'§ 48',ch:'3 健康及安全',topic:'環境污染檢舉與兒少健康保護',bench:{aabe:'於 §48 補列環境主管機關應於重大公共建設或環境政策時，辦理兒少健康影響評估；連動環境權利集體救濟之程序。',draft:'草案規定任何人發現環境污染足以危害兒少健康時，得向中央及地方環境主管機關檢舉，受理機關應為檢舉人身分保密。',intl:'CRC 第 24 條健康權涵蓋環境品質；CRC GC No. 15（2013）；歐盟 Environmental Action Programme for Children。'}},
    {no:'§ 59',ch:'4 教育文化就業',topic:'網路內容防護',bench:{aabe:'5 項補強：平台預先安全設計（Safety by Design）、性私密影像/深偽專條、兒少資料保護、AI 風險防制、§97 媒體強化。',draft:'草案委託民間團體成立內容防護機構，辦理網路行為觀察、申訴、上網安全教育、適齡識別、自律機制。',intl:'CRC GC No. 25（2021）；OECD Towards Digital Safety by Design for Children（2024）；歐盟 DSA；英國 OSA 2023；澳洲 OSA 2021；韓國《青少年保護法》2024 修正。'}},
    {no:'§ 62',ch:'4 教育文化就業',topic:'勞工主管機關對少年就業服務',bench:{aabe:'於 §62 將追蹤期延長為 6 個月，並明列追蹤輔導服務內容標準；連動 §3 跨部會統整權限（勞動、教育、社政）；參考歐盟 Youth Guarantee 設立「青少年保證制度」。',draft:'草案規定勞工主管機關對於缺乏技術及學歷而有就業需求之少年，應結合教育及社政主管機關提供個別化就業服務，並於推介就業後提供至少 3 個月就業追蹤輔導。',intl:'ILO Convention No. 138（最低工作年齡）、No. 182（最惡劣形式童工）；德國 Berufsausbildung 雙軌制 16-25 歲；歐盟 Youth Guarantee。'}},
    {no:'§ 70',ch:'5 偏差行為預防輔導',topic:'學校對少事法少年之轉銜及復學教育',bench:{aabe:'於 §70 母法明列轉銜計畫基本要件（專案社工、心理輔導、學業補救、生涯規劃）；連動 §71 福利服務之強制承接；增訂跨機關案件管理會議。',draft:'草案規定高級中等以下學校及專科學校五年制前三年，對依少年事件處理法處理之少年，應執行轉銜及復學教育計畫。轉銜計畫之具體標準授權子法。',intl:'CRC 第 28 條受教權與第 40 條少年司法；Beijing Rules 第 24 條服刑後再融合；美國各州 Reentry Programs。'}},
    {no:'§ 71',ch:'5 偏差行為預防輔導',topic:'地方主管機關對少年保護處遇後之福利服務',bench:{aabe:'於 §71 母法明列福利服務基本內涵（心理諮商、家庭支持、職業輔導、住居協助）；明定追蹤期至少 1 年，並由地方主管機關每 3 個月進行案件管理會議；連動 §70 學校復學銜接。',draft:'草案規定地方主管機關對於依少年事件處理法處理之少年及其家庭，應持續提供必要福利服務。「必要福利服務」內涵未明。',intl:'Beijing Rules 第 28 條條件式釋放後追蹤支持；美國 OJJDP Aftercare Services Framework；愛爾蘭 Probation Service；蘇格蘭 GIRFEC 框架。'}},
    {no:'§ 72',ch:'6 保護安置服務',topic:'虐待類型化（本次修法重點）',bench:{aabe:'肯定虐待類型化；補列「目睹家暴」、「網路霸凌」、「機構性虐待」三類，並於子法訂定具體認定標準。',draft:'草案明確列舉兒少身心虐待四類型：身體暴力、精神暴力、疏忽照顧、性不當對待。',intl:'WHO Violence Against Children Surveys（VACS）；Council of Europe Lanzarote Convention 涵蓋網路與機構性虐待；澳洲 Royal Commission 確立機構性虐待之獨立類型。'}},
    {no:'§ 75',ch:'6 保護安置服務',topic:'六歲以下兒童未獲適當照顧情形之關懷查訪',bench:{aabe:'於 §75 母法明列「未獲適當照顧之虞」客觀指標；明定查訪後跨機關回饋機制（14 日內回報）；強制通報義務人擴大（補習班、運動教練、宗教教養機構）應對應 §73 處理。',draft:'草案規定戶政、衛生、教育、警政、矯正等公務人員於執行業務時，知悉六歲以下兒童有未辦理出生登記、未依規定預防接種、未納入全民健康保險等情形時，應由各目的事業主管機關進行關懷、輔導、查訪或調查。',intl:'澳洲 NSW Reportable Conduct Scheme（2014）；愛爾蘭 Children First Act 2015 強制通報義務人清單；英國 Working Together to Safeguard Children 2018 之 Early Help Assessment。'}},
    {no:'§ 80',ch:'6 保護安置服務',topic:'違反 § 72 各款情節輕微之處置',bench:{aabe:'於 § 80 母法明列「情節輕微」認定指標；延長中度違反者處置時數至 24 小時；連動 § 75 通報後家庭服務強制承接；增訂行為人再犯預防追蹤義務。',draft:'草案對違反 § 72 各款情節輕微者，主管機關得令行為人接受 3-12 小時之兒少輔導管教、情緒管理、性平等課程。「情節輕微」認定標準不明。',intl:'美國 Batterer Intervention Programs（通常 40 小時以上）；德國 Familienberatung 強制家庭治療；紐西蘭 Family Group Conference；Council of Europe Rec(2006)19。'}},
    {no:'§ 87',ch:'6 保護安置服務',topic:'安置期間訪談、偵訊、訊問之兒少保護',bench:{aabe:'於 § 87 補列陪同社工之專業要求（Barnahus 模式培訓）；明定訪談全程影音紀錄義務；增訂主管機關應評估設置我國 Barnahus 模式之可行性。',draft:'草案規定安置期間，非依法律規定或為保護兒少，不得使其接受訪談、偵訊、訊問或身體檢查；前項應由社會工作人員陪同。陪同社工之專業要求未明。',intl:'CRC 第 12 條兒少表意權與第 37 條司法權利；Council of Europe 兒少友善司法指引（2010）；英國 ABE 指引；Barnahus 模式（冰島首創，北歐普及）。'}},
    {no:'§ 96',ch:'6 保護安置服務',topic:'地方主管機關訪視評估遭拒之強制處理',bench:{aabe:'於 § 96 母法明列強制處理具體程序步驟；明定警察協助啟動要件；增訂委託機構遭拒之 24 小時內回報義務（對應第八章六大議題之議題五委外責任鏈）。',draft:'草案規定地方主管機關或受其委託之機構、團體、專業人員，進行訪視、評估、調查或服務遭拒時，地方主管機關得採強制處理措施。「強制處理」之具體程序未明。',intl:'英國 Children Act 1989 之 Emergency Protection Order 與 Child Assessment Order；美國 CPS 強制接觸權標準；愛爾蘭 Tusla 強制訪視程序。'}},
    {no:'§ 97',ch:'6 保護安置服務',topic:'媒體報導不得揭露兒少身分（擴大條）',bench:{aabe:'補列網路平台與主管機關之配合下架義務、平台主動偵測之義務。',draft:'草案擴大不得揭露之情形與對象。未明定網路平台之配合下架義務。',intl:'英國 OSA 2023 之 mandatory takedown；歐盟 DSA 之 trusted flagger；澳洲 eSafety Commissioner 下架令。'}},
    {no:'§ 109',ch:'8 消極資格與調查',topic:'消極資格',bench:{aabe:'本盟主張補列嚴重家庭暴力、非人道待遇之資格限制（採人本基金會主張）。',draft:'草案規定有特定情事者不得擔任兒少工作者。未涵蓋嚴重家庭暴力、非人道待遇。',intl:'澳洲 WWCC 涵蓋家暴與兒少非人道待遇；英國 DBS Barred List 涵蓋。'}},
    {no:'§ 116',ch:'8 消極資格與調查',topic:'雇主查證義務',bench:{aabe:'本盟主張「得」改「應」，並明定查證頻率與紀錄保存（採人本基金會主張）。',draft:'草案規定雇主「得」查證消極資格。為授權性規範，非強制義務。',intl:'澳洲 WWCC、英國 DBS、加拿大 VSC 三制度皆為雇主之強制查證義務。'}},
    {no:'§ 131',ch:'9 罰則',topic:'雇主未查證罰則',bench:{aabe:'本盟主張區分初犯與累犯，加重累犯之罰則（採人本基金會主張）。',draft:'草案規定雇主違反查證義務之罰則。未區分初犯與累犯。',intl:'澳洲 WWCC 違反者最高 2 年徒刑或 24 萬澳幣罰款；英國 DBS 違反之刑事責任。'}},
    {no:'§ 156-165',ch:'10 附則章',topic:'施行細則、過渡條款',bench:{aabe:'建議補列「重大兒少事件檢討法制化」條款，要求主管機關於重大事件發生後 30 日內成立檢討委員會，6 個月內公布報告。',draft:'草案規定施行細則授權、過渡條款。未涵蓋重大事件檢討機制。',intl:'英國 Child Safeguarding Practice Reviews（CSPR）；美國 Child Fatality Review Teams；紐西蘭 OTA Independent Review。'}},
  ];

  // SVG icons
  const ICON_COPY = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
  const ICON_SHARE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>';
  const ICON_SEARCH = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="16" height="16"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>';
  const ICON_CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="20 6 9 17 4 12"/></svg>';

  function renderExplorer(container) {
    container.innerHTML = `
      <div class="article-explorer">
        <div class="ae-controls">
          <label class="ae-search-wrap">
            <span class="ae-search-icon" aria-hidden="true">${ICON_SEARCH}</span>
            <input type="text" class="ae-search" placeholder="搜尋條號或關鍵字（例如 § 46、心理健康、收出養）" aria-label="搜尋條號或關鍵字">
          </label>
          <select class="ae-chapter" aria-label="章節篩選">
            <option value="">全部章節</option>
            <option value="1">第 1 章 總則</option>
            <option value="2">第 2 章 身分及家庭</option>
            <option value="3">第 3 章 健康及安全</option>
            <option value="4">第 4 章 教育文化就業</option>
            <option value="5">第 5 章 偏差行為預防輔導</option>
            <option value="6">第 6 章 保護安置服務</option>
            <option value="8">第 8 章 消極資格與調查</option>
            <option value="9">第 9 章 罰則</option>
            <option value="10">第 10 章 附則章</option>
          </select>
        </div>
        <ol class="ae-list">
          ${A_LEVEL_22.map((a, i) => {
            const slug = a.no.replace(/[§\s]/g, '').toLowerCase();
            return `
              <li class="ae-card" id="section-${slug}" data-chapter="${a.ch.charAt(0)}" data-search="${a.no} ${a.topic}">
                <div class="ae-card-head">
                  <span class="ae-no">${a.no}</span>
                  <span class="ae-chapter-tag">${a.ch}</span>
                  <h3 class="ae-title">${a.topic}</h3>
                </div>
                <div class="ae-tabs" role="tablist">
                  <button class="ae-tab active" data-tab="aabe-${i}" role="tab">本盟主張</button>
                  <button class="ae-tab" data-tab="draft-${i}" role="tab">草案內容</button>
                  <button class="ae-tab" data-tab="intl-${i}" role="tab">國際對標</button>
                </div>
                <div class="ae-tab-content active" id="aabe-${i}">${a.bench.aabe}</div>
                <div class="ae-tab-content" id="draft-${i}">${a.bench.draft}</div>
                <div class="ae-tab-content" id="intl-${i}">${a.bench.intl}</div>
                <div class="ae-actions">
                  <button class="ae-action copy-no" data-no="${a.no}">${ICON_COPY}<span>複製條號</span></button>
                  <button class="ae-action share-url" data-slug="${slug}">${ICON_SHARE}<span>分享此條 URL</span></button>
                </div>
              </li>
            `;
          }).join('')}
        </ol>
        <p class="ae-footer-note">A 級核心 22 條完整評估。B 級 30 條與其他 113 條請見 <a href="downloads/written-opinion-v2.pdf" target="_blank" rel="noopener">完整書面意見書 PDF</a>。</p>
      </div>
    `;

    // tab 切換
    container.querySelectorAll('.ae-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const card = tab.closest('.ae-card');
        card.querySelectorAll('.ae-tab').forEach(t => t.classList.remove('active'));
        card.querySelectorAll('.ae-tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab).classList.add('active');
      });
    });

    // 篩選 + 搜尋
    const filter = () => {
      const q = container.querySelector('.ae-search').value.trim().toLowerCase();
      const ch = container.querySelector('.ae-chapter').value;
      container.querySelectorAll('.ae-card').forEach(card => {
        const matchSearch = !q || card.dataset.search.toLowerCase().includes(q);
        const matchCh = !ch || card.dataset.chapter === ch;
        card.classList.toggle('hidden', !(matchSearch && matchCh));
      });
    };
    container.querySelector('.ae-search').addEventListener('input', filter);
    container.querySelector('.ae-chapter').addEventListener('change', filter);

    // 複製條號
    container.querySelectorAll('.copy-no').forEach(btn => {
      btn.addEventListener('click', () => {
        navigator.clipboard.writeText(btn.dataset.no).then(() => {
          const span = btn.querySelector('span');
          const orig = span.textContent;
          btn.innerHTML = ICON_CHECK + '<span>已複製 ' + btn.dataset.no + '</span>';
          setTimeout(() => { btn.innerHTML = ICON_COPY + '<span>' + orig + '</span>'; }, 1800);
        });
      });
    });

    // 分享 URL
    container.querySelectorAll('.share-url').forEach(btn => {
      btn.addEventListener('click', () => {
        const url = window.location.origin + window.location.pathname + '#section-' + btn.dataset.slug;
        navigator.clipboard.writeText(url).then(() => {
          const span = btn.querySelector('span');
          const orig = span.textContent;
          btn.innerHTML = ICON_CHECK + '<span>已複製 URL</span>';
          setTimeout(() => { btn.innerHTML = ICON_SHARE + '<span>' + orig + '</span>'; }, 1800);
        });
      });
    });

    // hash anchor highlight
    function highlightHash() {
      if (window.location.hash) {
        const target = document.querySelector(window.location.hash);
        if (target && target.classList.contains('ae-card')) {
          document.querySelectorAll('.ae-card.highlighted').forEach(c => c.classList.remove('highlighted'));
          target.classList.add('highlighted');
          target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    }
    highlightHash();
    window.addEventListener('hashchange', highlightHash);
  }

  function init() {
    const c = document.getElementById('article-explorer-mount');
    if (c) renderExplorer(c);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
