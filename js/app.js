const MAX_LENGTH = 1000;
const ANALYSIS_DELAY = 1100;

const elements = {
  form: document.querySelector('#analysis-form'),
  input: document.querySelector('#message-input'),
  count: document.querySelector('#character-count'),
  analyze: document.querySelector('#analyze-button'),
  empty: document.querySelector('#empty-state'),
  loading: document.querySelector('#loading-state'),
  result: document.querySelector('#result-state'),
  error: document.querySelector('#error-state'),
  resultHeading: document.querySelector('#result-heading'),
  resultIcon: document.querySelector('#result-icon'),
  category: document.querySelector('#result-category'),
  severity: document.querySelector('#result-severity'),
  confidence: document.querySelector('#result-confidence'),
  explanation: document.querySelector('#result-explanation'),
  another: document.querySelector('#analyze-another'),
  retry: document.querySelector('#try-again')
};

const mockResults = {
  safe: { status: 'Safe', category: 'Safe', severity: 'Low', confidence: '96%', explanation: 'This message appears respectful and does not show indicators of harmful content in this prototype.', icon: '✓' },
  harmful: { status: 'Potentially harmful', category: 'Harassment', severity: 'Medium', confidence: '89%', explanation: 'This message contains language that could be upsetting or targeted at another person. Consider reviewing the context and responding with care.', icon: '!' }
};

function updateInputState() {
  const length = elements.input.value.length;
  elements.count.textContent = `${length.toLocaleString()} / ${MAX_LENGTH.toLocaleString()}`;
  elements.analyze.disabled = elements.input.value.trim().length === 0;
}

function hideFeedback() {
  elements.loading.hidden = true;
  elements.result.hidden = true;
  elements.error.hidden = true;
}

function resetToInput() {
  hideFeedback();
  elements.empty.hidden = false;
  elements.form.hidden = false;
  elements.input.value = '';
  updateInputState();
  elements.input.focus();
}

function showError() {
  hideFeedback();
  elements.empty.hidden = true;
  elements.form.hidden = true;
  elements.error.hidden = false;
}

function selectMockResult(message) {
  // Demo-only keyword matching to make both visual states easy to preview.
  const harmfulWords = /\b(hate|stupid|ugly|loser|hurt you|kill|threat|idiot|nobody likes you)\b/i;
  return harmfulWords.test(message) ? mockResults.harmful : mockResults.safe;
}

function showResult(result) {
  hideFeedback();
  elements.result.classList.toggle('is-harmful', result === mockResults.harmful);
  elements.resultHeading.textContent = result.status;
  elements.resultIcon.textContent = result.icon;
  elements.category.textContent = result.category;
  elements.severity.textContent = result.severity;
  elements.confidence.textContent = result.confidence;
  elements.explanation.textContent = result.explanation;
  elements.result.hidden = false;
  elements.result.querySelector('h2').focus?.();
}

elements.input.addEventListener('input', updateInputState);
elements.form.addEventListener('submit', (event) => {
  event.preventDefault();
  const message = elements.input.value.trim();
  if (!message) return;
  hideFeedback();
  elements.empty.hidden = true;
  elements.form.hidden = true;
  elements.loading.hidden = false;
  window.setTimeout(() => showResult(selectMockResult(message)), ANALYSIS_DELAY);
});
elements.another.addEventListener('click', resetToInput);
elements.retry.addEventListener('click', resetToInput);

// Testing hook for the prototype: run ChildGuard.showError() from the browser console.
window.ChildGuard = { showError };
updateInputState();
