/* Model and source text is always rendered as text, never executable HTML. */
const api = acquireVsCodeApi();
const byId = id => document.getElementById(id);
for (const type of ['setup', 'cancel']) byId(type).addEventListener('click', () => api.postMessage({ type }));
byId('run').addEventListener('click', () => api.postMessage({ type: 'run', mode: byId('mode').value, prompt: byId('prompt').value }));
function add(parent, tag, text, className) {
  const element = document.createElement(tag); element.textContent = text;
  if (className) element.className = className;
  parent.appendChild(element); return element;
}
window.addEventListener('message', ({ data }) => {
  if (data.type === 'busy') { byId('run').disabled = data.value; byId('setup').disabled = data.value; byId('notice').textContent = data.value ? 'Reading sources and running the local model… Stop cancels this request.' : ''; }
  if (data.type === 'notice') byId('notice').textContent = data.message;
  if (data.type !== 'result') return;
  const output = byId('output'); output.replaceChildren();
  const result = data.result;
  if (!result) { add(output, 'p', 'Run Setup once, then ask a question about your open repository.', 'muted'); return; }
  add(output, 'h3', result.prompt);
  add(output, 'p', result.status, 'status');
  add(output, 'p', 'Model: ' + result.model, 'muted');
  for (const claim of result.answer.claims) {
    const card = add(output, 'div', '', 'claim'); add(card, 'p', claim.text);
    for (const id of claim.source_ids) {
      const source = result.sources.find(item => item.id === id);
      const button = add(card, 'button', `${id} · ${source?.path ?? 'unknown'}${source?.start_line ? ':' + source.start_line : source?.unit ? ' · ' + source.unit + ' ' + source.start_unit + '–' + source.end_unit : ''}`, 'source');
      button.addEventListener('click', () => api.postMessage({ type: 'source', id }));
    }
  }
  for (const [title, items] of [['Uncertainties', result.answer.uncertainties], ['Suggested checks — not executed', result.answer.suggested_checks]]) {
    if (items.length) { add(output, 'h3', title); const list = add(output, 'ul', ''); for (const item of items) add(list, 'li', item); }
  }
  if (result.proposal) {
    add(output, 'h3', `Changes · ${result.decision}`);
    add(output, 'p', result.proposal.files.map(file => file.path).join('\n'));
    if (result.decision === 'pending') add(output, 'button', 'Review proposed changes').addEventListener('click', () => api.postMessage({ type: 'review' }));
  }
  const coverage = add(output, 'details', ''); add(coverage, 'summary', 'Source coverage and limits'); add(coverage, 'pre', JSON.stringify(result.coverage, null, 2));
});
api.postMessage({ type: 'ready' });
