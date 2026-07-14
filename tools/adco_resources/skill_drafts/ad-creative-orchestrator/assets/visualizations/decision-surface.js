(() => {
  const root = document.getElementById('__ROOT_ID__');
  const dataNode = document.getElementById('__DATA_ID__');
  if (!root || !dataNode) return;
  const spec = JSON.parse(dataNode.textContent);
  const options = new Map((spec.presentation.options || []).map((item) => [item.id, item]));
  let selectedId = spec.presentation.recommendation?.option_id || spec.presentation.options?.[0]?.id || null;
  const status = root.querySelector('[data-adco-status]');
  const detail = root.querySelector('[data-adco-detail]');

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

  root.querySelectorAll('[data-adco-action]').forEach((button) => {
    button.addEventListener('click', async () => {
      const action = spec.interactions.actions.find((item) => item.id === button.dataset.adcoAction);
      if (!action) return;
      const selected = selectedId ? options.get(selectedId) : null;
      const selection = selected ? ` 我的选择是：${selected.label}。` : '';
      const prompt = `${action.conversation_intent}${selection} 请先确认我看到的是最新内容，再告诉我：记录了什么、哪些内容会保留、哪些内容需要重新检查，以及下一步是什么。这次点击本身不代表对外发送或项目完成。`;
      if (window.openai && typeof window.openai.sendFollowUpMessage === 'function') {
        await window.openai.sendFollowUpMessage({ prompt, title: action.label });
        if (status) status.textContent = '已发送到对话；正在确认最新内容。';
      } else if (status) {
        status.textContent = `当前表面不支持提交；请在聊天中输入：${prompt}`;
      }
    });
  });
})();
