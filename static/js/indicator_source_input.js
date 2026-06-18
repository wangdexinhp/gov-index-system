/**
 * 指标录入：来源类别下拉 + 合并展示「城市名+来源」
 * 入库仅存类别代码；合并名称仅用于界面展示。
 */
window.IndicatorSourceInput = (function () {
    let options = [];

    function setOptions(opts) {
        options = Array.isArray(opts) ? opts : [];
    }

    function escapeHtml(str) {
        return String(str || '')
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    function composeDisplay(city, province, code) {
        const opt = options.find(o => o.code === code);
        if (!opt) return '';
        const scope = opt.scope || 'manual';
        const suffix = opt.suffix || opt.label || '';
        const cityName = (city || '').trim();
        const provName = (province || '').trim();
        if (scope === 'province') {
            if (!provName) return suffix;
            return provName.endsWith(suffix) ? provName : provName + suffix;
        }
        if (scope === 'city') {
            if (!cityName) return suffix;
            return cityName.endsWith(suffix) ? cityName : cityName + suffix;
        }
        return cityName ? (cityName + suffix) : suffix;
    }

    function guessCodeFromDisplay(text) {
        const value = (text || '').trim();
        if (!value) return '';
        if (options.some(o => o.code === value)) return value;
        for (const opt of options) {
            const suffix = opt.suffix || '';
            if (suffix && value.endsWith(suffix)) return opt.code;
        }
        return '';
    }

    function buildCellHtml(nameAttr, city, province, role) {
        const opts = options.map(o =>
            `<option value="${escapeHtml(o.code)}">${escapeHtml(o.label)}</option>`
        ).join('');
        const roleAttr = role ? ` data-role="${escapeHtml(role)}"` : '';
        return `<div class="source-input-wrap"${roleAttr} data-city="${escapeHtml(city)}" data-province="${escapeHtml(province)}">
            <select class="source-type-select w-full bg-white border border-slate-300 rounded-lg px-1 py-0.5 text-xs" title="来源类别">
                <option value="">来源类别</option>${opts}
            </select>
            <input type="text" class="source-merged-input w-full bg-slate-50 border border-slate-300 rounded-lg px-1 py-1 text-xs" readonly placeholder="城市名+来源" title="城市名+来源（自动合并展示）">
        </div>`;
    }

    function syncMergedDisplay(wrapEl, city, province, code) {
        if (!wrapEl) return;
        const input = wrapEl.querySelector('.source-merged-input');
        if (!input) return;
        input.value = code ? composeDisplay(city, province, code) : '';
    }

    function bindCell(wrapEl, city, province) {
        if (!wrapEl || wrapEl.dataset.bound === '1') return;
        wrapEl.dataset.bound = '1';
        const select = wrapEl.querySelector('.source-type-select');
        if (!select) return;
        select.addEventListener('change', function () {
            syncMergedDisplay(wrapEl, city, province, select.value);
        });
    }

    function bindIndicatorSourceWrap(wrapEl) {
        if (!wrapEl || wrapEl.dataset.bound === '1') return;
        wrapEl.dataset.bound = '1';
        const select = wrapEl.querySelector('.source-type-select');
        if (!select) return;
        const city = wrapEl.dataset.city;
        const province = wrapEl.dataset.province;
        select.addEventListener('change', function () {
            if (!select.value) {
                delete wrapEl.dataset.overridden;
                const tr = wrapEl.closest('tr');
                const rowSelect = tr && tr.querySelector('.source-input-wrap[data-role="row-source"] .source-type-select');
                if (rowSelect && rowSelect.value) {
                    select.value = rowSelect.value;
                    syncMergedDisplay(wrapEl, city, province, rowSelect.value);
                } else {
                    syncMergedDisplay(wrapEl, city, province, '');
                }
                return;
            }
            wrapEl.dataset.overridden = 'true';
            syncMergedDisplay(wrapEl, city, province, select.value);
        });
    }

    function syncRowSourceToIndicators(tr) {
        if (!tr) return;
        const rowWrap = tr.querySelector('.source-input-wrap[data-role="row-source"]');
        if (!rowWrap) return;
        const rowSelect = rowWrap.querySelector('.source-type-select');
        if (!rowSelect) return;
        const code = rowSelect.value;
        tr.querySelectorAll('.source-input-wrap[data-role="indicator-source"]').forEach(function (wrap) {
            if (wrap.dataset.overridden === 'true') return;
            const indSelect = wrap.querySelector('.source-type-select');
            if (!indSelect) return;
            indSelect.value = code;
            syncMergedDisplay(wrap, wrap.dataset.city, wrap.dataset.province, code);
        });
    }

    function bindRowSourceWrap(tr, rowWrap) {
        if (!rowWrap || rowWrap.dataset.bound === '1') return;
        rowWrap.dataset.bound = '1';
        const select = rowWrap.querySelector('.source-type-select');
        if (!select) return;
        const city = rowWrap.dataset.city;
        const province = rowWrap.dataset.province;
        select.addEventListener('change', function () {
            syncMergedDisplay(rowWrap, city, province, select.value);
            syncRowSourceToIndicators(tr);
        });
    }

    function bindAllIn(container) {
        if (!container) return;
        container.querySelectorAll('tr').forEach(function (tr) {
            const rowWrap = tr.querySelector('.source-input-wrap[data-role="row-source"]');
            if (rowWrap) bindRowSourceWrap(tr, rowWrap);
            tr.querySelectorAll('.source-input-wrap[data-role="indicator-source"]').forEach(bindIndicatorSourceWrap);
            tr.querySelectorAll('.source-input-wrap:not([data-role])').forEach(function (wrap) {
                bindCell(wrap, wrap.dataset.city, wrap.dataset.province);
            });
        });
    }

    function applyLoadedValue(wrapEl, sourceValue, city, province, options) {
        if (!wrapEl) return;
        const select = wrapEl.querySelector('.source-type-select');
        const input = wrapEl.querySelector('.source-merged-input');
        if (!input) return;
        const text = (sourceValue || '').trim();
        if (!text) return;
        const code = guessCodeFromDisplay(text);
        if (code) {
            if (select) select.value = code;
            input.value = (text === code)
                ? composeDisplay(city, province, code)
                : text;
        } else {
            if (select) select.value = '';
            input.value = text;
        }
        if (options && options.markOverridden) {
            wrapEl.dataset.overridden = 'true';
        }
    }

    function readSubmitCode(sourceTd) {
        const select = sourceTd && sourceTd.querySelector('.source-type-select');
        return select ? select.value.trim() : '';
    }

    function readSubmitCodeWithFallback(indicatorTd, rowTd) {
        const indicatorCode = readSubmitCode(indicatorTd);
        if (indicatorCode) return indicatorCode;
        return readSubmitCode(rowTd);
    }

    function readSubmitValue(sourceTd) {
        return readSubmitCode(sourceTd);
    }

    function refreshProvinceScoped(container, province) {
        if (!container) return;
        container.querySelectorAll('.source-input-wrap').forEach(function (wrap) {
            const select = wrap.querySelector('.source-type-select');
            if (!select || !select.value) return;
            const opt = options.find(o => o.code === select.value);
            if (opt && opt.scope === 'province') {
                syncMergedDisplay(wrap, wrap.dataset.city, province, select.value);
            }
            wrap.dataset.province = province || '';
        });
    }

    return {
        setOptions,
        buildCellHtml,
        bindCell,
        bindAllIn,
        composeDisplay,
        applyLoadedValue,
        readSubmitCode,
        readSubmitCodeWithFallback,
        readSubmitValue,
        refreshProvinceScoped,
        syncRowSourceToIndicators,
        guessCodeFromDisplay,
    };
})();
