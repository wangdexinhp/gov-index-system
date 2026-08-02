/**
 * 从后端加载指标分组目录（查询/录入/校验页共用）
 */
window.IndicatorCatalog = (function () {
    let cache = null;
    let promise = null;

    function loadFull() {
        if (cache) return Promise.resolve(cache);
        if (!promise) {
            promise = fetch('/dashboard/api/indicator-catalog/', { credentials: 'same-origin' })
                .then(function (res) { return res.json(); })
                .then(function (json) {
                    if (json.success) {
                        cache = json;
                        return cache;
                    }
                    throw new Error((json && json.message) || '加载指标目录失败');
                })
                .catch(function (err) {
                    promise = null;
                    throw err;
                });
        }
        return promise;
    }

    function load() {
        return loadFull().then(function (full) { return full.data || {}; });
    }

    function loadArea() {
        return loadFull().then(function (full) { return full.area_data || {}; });
    }

    function loadFormCategories() {
        return loadFull().then(function (full) { return full.form_categories || {}; });
    }

    function loadAreaFormCategories() {
        return loadFull().then(function (full) { return full.area_form_categories || {}; });
    }

    function renderGroupTree(treeEl, filterEl, groups, activeCode) {
        if (!treeEl || !groups || !groups.length) return activeCode || null;
        treeEl.innerHTML = '';
        if (filterEl) filterEl.innerHTML = '';
        var firstCode = activeCode || groups[0].code;
        groups.forEach(function (g) {
            var div = document.createElement('div');
            div.className = 'drc-tree-item' + (g.code === firstCode ? ' active' : '');
            div.setAttribute('data-group', g.code);
            div.textContent = g.name;
            treeEl.appendChild(div);
            if (filterEl) {
                var opt = document.createElement('option');
                opt.value = g.code;
                opt.textContent = g.name;
                if (g.code === firstCode) opt.selected = true;
                filterEl.appendChild(opt);
            }
        });
        return firstCode;
    }

    return {
        load: load,
        loadFull: loadFull,
        loadArea: loadArea,
        loadFormCategories: loadFormCategories,
        loadAreaFormCategories: loadAreaFormCategories,
        renderGroupTree: renderGroupTree,
    };
})();
