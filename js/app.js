const MAX_LENGTH = 1000;
const elements = {
  form: document.querySelector('#analysis-form'),
  input: document.querySelector('#message-input'),
  fileInput: document.querySelector('#file-input'),
  count: document.querySelector('#character-count'),
  uploadStatus: document.querySelector('#upload-status'),
  analyze: document.querySelector('#analyze-button'),
  empty: document.querySelector('#empty-state'),
  loading: document.querySelector('#loading-state'),
  result: document.querySelector('#result-state'),
  error: document.querySelector('#error-state'),
  resultHeading: document.querySelector('#result-heading'),
  resultIcon: document.querySelector('#result-icon'),
  language: document.querySelector('#result-language'),
  categories: document.querySelector('#result-categories'),
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

function getConfiguredApiBaseUrl() {
  const configured = window.__CHILDGUARD_API_BASE__;
  if (typeof configured === 'string' && configured.trim()) {
    return configured.trim().replace(/\/+$/, '');
  }

  if (window.location.protocol === 'http:' || window.location.protocol === 'https:') {
    return window.location.origin;
  }

  return '';
}

function getAnalyzeUrl() {
  const baseUrl = getConfiguredApiBaseUrl();
  return baseUrl ? `${baseUrl}/analyze` : '/analyze';
}

function formatConfidence(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '—';
  }

  const percentage = Math.min(Math.max(value, 0), 1) * 100;
  return `${percentage.toFixed(1).replace(/\.0$/, '')}%`;
}

function formatCategory(value) {
  if (typeof value !== 'string' || value.trim() === '') {
    return 'Unknown';
  }

  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

function normalizeLanguage(value) {
  return value === 'ar' || value === 'en' ? value : 'en';
}

function toDisplayResult(apiResult) {
  const safeResult = apiResult && apiResult.is_harmful === false ? mockResults.safe : mockResults.harmful;
  const result = { ...safeResult };

  result.status = apiResult && apiResult.is_harmful === false ? 'Safe' : 'Potentially harmful';
  result.language = normalizeLanguage(apiResult && apiResult.language).toUpperCase();
  const apiCategories = apiResult && Array.isArray(apiResult.categories) ? apiResult.categories : [];
  const fallbackCategory = apiResult && apiResult.category && apiResult.category !== 'safe'
    ? [apiResult.category]
    : [];
  result.categories = (apiCategories.length ? apiCategories : fallbackCategory).map(formatCategory);
  result.severityClass = apiResult && apiResult.severity ? apiResult.severity.toLowerCase() : 'safe';
  result.severity = apiResult && apiResult.severity ? formatCategory(apiResult.severity) : result.severity;
  result.confidence = apiResult && typeof apiResult.confidence === 'number' ? formatConfidence(apiResult.confidence) : result.confidence;
  result.explanation = apiResult && apiResult.explanation ? apiResult.explanation : result.explanation;
  result.icon = apiResult && apiResult.is_harmful === false ? '✓' : '!';

  return result;
}

function updateInputState() {
  const length = elements.input.value.length;
  elements.count.textContent = `${length.toLocaleString()} / ${MAX_LENGTH.toLocaleString()}`;
  elements.analyze.disabled = elements.input.value.trim().length === 0;
}

function setUploadStatus(message, isError = false) {
  elements.uploadStatus.textContent = message;
  elements.uploadStatus.classList.toggle('is-error', isError);
}

async function loadTextFile(file) {
  if (!file) return;

  try {
    const text = await file.text();
    if (text.length > MAX_LENGTH) {
      elements.fileInput.value = '';
      setUploadStatus('File must be 1,000 characters or fewer.', true);
      return;
    }

    elements.input.value = text;
    updateInputState();
    setUploadStatus(file.name);
  } catch (error) {
    console.error('File upload failed:', error);
    setUploadStatus('Unable to read this file.', true);
  }
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
  elements.input.disabled = false;
  elements.fileInput.disabled = false;
  elements.analyze.disabled = false;
  elements.input.value = '';
  elements.fileInput.value = '';
  setUploadStatus('');
  updateInputState();
  elements.input.focus();
}

function showError(message = 'The analysis service is unavailable. Please check that the backend is running and try again.') {
  hideFeedback();
  elements.empty.hidden = true;
  elements.form.hidden = true;
  elements.error.querySelector('p').textContent = message;
  elements.error.hidden = false;
}

function selectMockResult(message) {
  // Demo-only keyword matching to make both visual states easy to preview.
  const harmfulWords = /\b(hate|stupid|ugly|loser|hurt you|kill|threat|idiot|nobody likes you)\b/i;
  return harmfulWords.test(message) ? mockResults.harmful : mockResults.safe;
}

function showResult(result) {
  hideFeedback();
  const isHarmful = Boolean(result && result.status === 'Potentially harmful');
  elements.result.classList.toggle('is-harmful', isHarmful);
  elements.result.classList.remove('severity-safe', 'severity-medium', 'severity-high');
  elements.result.classList.add(`severity-${result.severityClass || 'safe'}`);
  elements.resultHeading.textContent = result.status;
  elements.resultIcon.textContent = result.icon;
  elements.language.textContent = `Language: ${result.language}`;
  elements.categories.replaceChildren();
  if (result.categories.length === 0) {
    const safeTag = document.createElement('span');
    safeTag.className = 'category-tag category-tag-safe';
    safeTag.textContent = 'Safe';
    elements.categories.append(safeTag);
  } else {
    result.categories.forEach((category) => {
      const tag = document.createElement('span');
      tag.className = 'category-tag';
      tag.textContent = category;
      elements.categories.append(tag);
    });
  }
  elements.severity.textContent = result.severity;
  elements.confidence.textContent = result.confidence;
  elements.explanation.textContent = result.explanation;
  elements.result.hidden = false;
  elements.result.querySelector('h2').focus?.();
}

async function analyzeMessage(message) {
  const response = await fetch(getAnalyzeUrl(), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ text: message })
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || 'Analysis request failed.');
  }

  const payload = await response.json();

  if (!payload || typeof payload.is_harmful !== 'boolean' || typeof payload.explanation !== 'string') {
    throw new Error('Invalid response from analysis API.');
  }
  if (payload.categories !== undefined && (!Array.isArray(payload.categories) || payload.categories.some((category) => typeof category !== 'string'))) {
    throw new Error('Invalid category data from analysis API.');
  }
  if (payload.confidence !== undefined && (typeof payload.confidence !== 'number' || Number.isNaN(payload.confidence))) {
    throw new Error('Invalid confidence data from analysis API.');
  }
  return payload;
}

elements.input.addEventListener('input', updateInputState);
elements.fileInput.addEventListener('change', (event) => loadTextFile(event.target.files[0]));
elements.form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const message = elements.input.value.trim();
  if (!message) return;

  hideFeedback();
  elements.empty.hidden = true;
  elements.form.hidden = true;
  elements.loading.hidden = false;
  elements.analyze.disabled = true;
  elements.input.disabled = true;
  elements.fileInput.disabled = true;

  try {
    const result = await analyzeMessage(message);
    showResult(toDisplayResult(result));
  } catch (error) {
    console.error('Analysis request failed:', error);
    showError(error instanceof TypeError ? 'Unable to reach the analysis service. Please check that the backend is running.' : error.message);
  }
});
elements.another.addEventListener('click', resetToInput);
elements.retry.addEventListener('click', resetToInput);

// Testing hook for the prototype: run ChildGuard.showError() from the browser console.
window.ChildGuard = { showError, getAnalyzeUrl, getConfiguredApiBaseUrl };
updateInputState();
