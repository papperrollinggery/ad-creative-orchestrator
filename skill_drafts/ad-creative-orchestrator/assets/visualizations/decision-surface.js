(() => {
  const root = document.getElementById('__ROOT_ID__');
  const dataNode = document.getElementById('__DATA_ID__');
  if (!root || !dataNode) return;
  const spec = JSON.parse(dataNode.textContent);
  const options = new Map((spec.presentation.options || []).map((item) => [item.id, item]));
  let selectedId = spec.presentation.recommendation?.option_id || spec.presentation.options?.[0]?.id || null;
  const status = root.querySelector('[data-adco-status]');
  const detail = root.querySelector('[data-adco-detail]');
  const focusLabels = {
    'asset-role': '画面任务',
    'reference-boundary': '参考边界',
    'customer-moment': '消费者时刻',
    'product-proof': '产品证明',
    'brand-memory': '品牌记忆',
    'region-findings': '画面区域判断',
    'channel-placement': '渠道落位',
    'source-and-authorization': '来源与使用授权',
  };

  function selectOption(optionId) {
    if (!options.has(optionId)) return;
    selectedId = optionId;
    root.querySelectorAll('[data-adco-option]').forEach((button) => {
      button.setAttribute('aria-pressed', String(button.dataset.adcoOption === optionId));
    });
    const option = options.get(optionId);
    if (detail) detail.textContent = `${option.label}：${option.summary}；权衡：${option.tradeoff}`;
    if (status) status.textContent = `已选择“${option.label}”；尚未提交。`;
  }

  root.querySelectorAll('[data-adco-option]').forEach((button) => {
    button.addEventListener('click', () => selectOption(button.dataset.adcoOption));
  });

  root.querySelectorAll('[data-adco-hotspot]').forEach((button) => {
    button.addEventListener('click', () => {
      const findingId = button.dataset.adcoHotspot;
      root.querySelectorAll('[data-adco-hotspot], [data-adco-finding]').forEach((item) => {
        item.classList.toggle('is-active',
          item.dataset.adcoHotspot === findingId || item.dataset.adcoFinding === findingId);
        if (item.dataset.adcoHotspot) {
          item.setAttribute('aria-pressed', String(item.dataset.adcoHotspot === findingId));
        }
      });
      const finding = root.querySelector(`[data-adco-finding="${findingId}"]`);
      const motion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
      finding?.scrollIntoView({ block: 'nearest', behavior: motion });
      if (status && finding) status.textContent = `正在查看画面判断 ${findingId}：${finding.innerText.replace(/\s+/g, ' ').trim()}`;
    });
  });

  root.querySelectorAll('[data-adco-action]').forEach((button) => {
    button.addEventListener('click', async () => {
      const action = spec.interactions.actions.find((item) => item.id === button.dataset.adcoAction);
      if (!action) return;
      const selected = selectedId ? options.get(selectedId) : null;
      const selection = selected ? ` 我的选择是：${selected.label}。` : '';
      const focus = (action.review_focus || []).map((item) => focusLabels[item]).filter(Boolean);
      const reviewScope = focus.length ? ` 本次请重点检查：${focus.join('、')}。` : '';
      const prompt = `${action.conversation_intent}${selection}${reviewScope} 请先确认我看到的是最新内容，再告诉我：记录了什么、哪些内容会保留、哪些内容需要重新检查，以及下一步是什么。这次点击本身不代表对外发送或项目完成。`;
      if (window.openai && typeof window.openai.sendFollowUpMessage === 'function') {
        await window.openai.sendFollowUpMessage({ prompt, title: action.label });
        if (status) status.textContent = '已发送到对话；正在确认最新内容。';
      } else if (status) {
        status.textContent = `当前表面不支持提交；请在聊天中输入：${prompt}`;
      }
    });
  });
})();
