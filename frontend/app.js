const uploadForm = document.getElementById('upload-form');
const uploadResults = document.getElementById('upload-results');
const queryForm = document.getElementById('query-form');
const queryError = document.getElementById('query-error');
const answerEl = document.getElementById('answer');
const citationsEl = document.getElementById('citations');

uploadForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  uploadResults.innerHTML = 'Uploading...';

  const response = await fetch('/upload', {
    method: 'POST',
    body: new FormData(uploadForm),
  });
  const results = await response.json();

  uploadResults.innerHTML = '';
  for (const result of results) {
    const div = document.createElement('div');
    div.className = 'upload-result';
    if (result.success) {
      const name = result.metadata ? result.metadata.filename : '';
      div.textContent = result.is_duplicate
        ? `${name}: already uploaded (duplicate)`
        : `${name}: uploaded successfully`;
    } else {
      div.textContent = `Failed: ${result.error_message}`;
    }
    uploadResults.appendChild(div);
  }
});

queryForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  queryError.textContent = '';
  answerEl.textContent = '';
  citationsEl.innerHTML = '';

  const question = document.getElementById('question').value;
  const response = await fetch('/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    const errorBody = await response.json();
    queryError.textContent = errorBody.detail;
    return;
  }

  const data = await response.json();
  answerEl.textContent = data.answer;

  for (const citation of data.citations) {
    const card = document.createElement('div');
    card.className = 'citation-card';

    const header = document.createElement('div');
    const strong = document.createElement('strong');
    strong.textContent = citation.document_name;
    header.appendChild(strong);
    header.append(` — page ${citation.page_number}, chunk ${citation.chunk_index} (relevance ${citation.relevance_score})`);

    const text = document.createElement('pre');
    text.textContent = citation.chunk_text;

    card.appendChild(header);
    card.appendChild(text);
    citationsEl.appendChild(card);
  }
});
