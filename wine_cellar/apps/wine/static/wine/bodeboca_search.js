document.addEventListener('DOMContentLoaded', function () {
    const container = document.querySelector('.bodeboca-search');
    if (!container) return;

    const searchUrl = container.dataset.searchUrl;
    const btn = document.getElementById('bodeboca-btn');
    const input = document.getElementById('bodeboca-query');
    const results = document.getElementById('bodeboca-results');
    const hiddenField = document.getElementById('id_bodeboca_image_url');

    if (!btn || !input || !results || !hiddenField) return;

    btn.addEventListener('click', doSearch);
    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') { e.preventDefault(); doSearch(); }
    });

    function doSearch() {
        const q = input.value.trim();
        if (!q) return;
        results.innerHTML = '<span class="bodeboca-search__msg">Searching…</span>';
        fetch(searchUrl + '?q=' + encodeURIComponent(q))
            .then(function (r) { return r.json(); })
            .then(function (data) { renderResults(data.results || []); })
            .catch(function () {
                results.innerHTML = '<span class="bodeboca-search__msg">Search error. Try again.</span>';
            });
    }

    function renderResults(hits) {
        if (!hits.length) {
            results.innerHTML = '<span class="bodeboca-search__msg">No results found.</span>';
            return;
        }
        results.innerHTML = '';
        hits.forEach(function (hit) {
            const div = document.createElement('div');
            div.className = 'bodeboca-result';
            div.title = hit.title;
            const img = document.createElement('img');
            img.src = hit.image_url;
            img.alt = hit.title;
            const label = document.createElement('div');
            label.className = 'bodeboca-result__title';
            label.textContent = hit.title;
            div.appendChild(img);
            div.appendChild(label);
            div.addEventListener('click', function () { selectImage(hit, div); });
            results.appendChild(div);
        });
    }

    function selectImage(hit, el) {
        document.querySelectorAll('.bodeboca-result').forEach(function (d) {
            d.classList.remove('selected');
        });
        el.classList.add('selected');
        hiddenField.value = hit.image_url;
    }
});
