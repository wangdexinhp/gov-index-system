/**
 * 指标录入：来源类别下拉 + 可编辑的具体来源名称。
 * 选择类别后自动填入默认名称；用户可修改具体名称（如国家级专业年鉴全称）。
 * 提交时优先保存具体名称文本。
 */
window.IndicatorSourceInput = (function () {
    let options = [];

    function setOptions(opts) {
        options = Array.isArray(opts) ? opts : [];
    }

    function getOptions() {
        return options.slice();
    }

    function initFromScript(scriptId) {
        const el = document.getElementById(scriptId || 'form-source-options');
        if (!el || !el.textContent) return;
        try {
            const parsed = JSON.parse(el.textContent);
            if (Array.isArray(parsed) && parsed.length) setOptions(parsed);
        } catch (e) {
            console.warn('解析数据来源配置失败', e);
        }
    }

    async function loadFromApi(url) {
        try {
            const res = await fetch(url, { credentials: 'same-origin' });
            const json = await res.json();
            if (json.success && Array.isArray(json.sources) && json.sources.length) {
                setOptions(json.sources);
            }
        } catch (e) {
            console.warn('加载数据来源选项失败，使用页面初始配置', e);
        }
        return options;
    }

    function escapeHtml(str) {
        return String(str || '')
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    function getOptionMeta(code) {
        return options.find(o => o.code === code) || null;
    }

    function composeDisplay(city, province, code) {
        const opt = getOptionMeta(code);
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
        // manual：仅给出类别后缀作为初始值，由用户改成具体名称
        return suffix;
    }

    function guessCodeFromDisplay(text) {
        const value = (text || '').trim();
        if (!value) return '';
        if (options.some(o => o.code === value)) return value;
        for (const opt of options) {
            const suffix = opt.suffix || '';
            if (suffix && value.endsWith(suffix)) return opt.code;
            if (opt.label && value === opt.label) return opt.code;
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
            <input type="text" class="source-merged-input w-full bg-white border border-slate-300 rounded-lg px-1 py-1 text-xs" placeholder="具体来源名称（可编辑）" title="可修改为具体年鉴/报告名称，如国家级专业年鉴全称">
        </div>`;
    }

    function syncMergedDisplay(wrapEl, city, province, code, force) {
        if (!wrapEl) return;
        const input = wrapEl.querySelector('.source-merged-input');
        if (!input) return;
        // 用户已手改过名称时，切换类别才强制刷新；否则保留手改内容
        if (!force && wrapEl.dataset.nameEdited === 'true' && input.value.trim()) {
            return;
        }
        input.value = code ? composeDisplay(city, province, code) : '';
        delete wrapEl.dataset.nameEdited;
    }

    function bindMergedInputEdit(wrapEl) {
        const input = wrapEl.querySelector('.source-merged-input');
        if (!input || input.dataset.editBound === '1') return;
        input.dataset.editBound = '1';
        input.addEventListener('input', function () {
            wrapEl.dataset.nameEdited = 'true';
            if (wrapEl.dataset.role === 'indicator-source') {
                wrapEl.dataset.overridden = 'true';
            }
        });
    }

    function bindCell(wrapEl, city, province) {
        if (!wrapEl || wrapEl.dataset.bound === '1') return;
        wrapEl.dataset.bound = '1';
        const select = wrapEl.querySelector('.source-type-select');
        if (!select) return;
        bindMergedInputEdit(wrapEl);
        select.addEventListener('change', function () {
            syncMergedDisplay(wrapEl, city, province, select.value, true);
        });
    }

    function bindIndicatorSourceWrap(wrapEl) {
        if (!wrapEl || wrapEl.dataset.bound === '1') return;
        wrapEl.dataset.bound = '1';
        const select = wrapEl.querySelector('.source-type-select');
        if (!select) return;
        const city = wrapEl.dataset.city;
        const province = wrapEl.dataset.province;
        bindMergedInputEdit(wrapEl);
        select.addEventListener('change', function () {
            if (!select.value) {
                delete wrapEl.dataset.overridden;
                delete wrapEl.dataset.nameEdited;
                const tr = wrapEl.closest('tr');
                const rowSelect = tr && tr.querySelector('.source-input-wrap[data-role="row-source"] .source-type-select');
                if (rowSelect && rowSelect.value) {
                    select.value = rowSelect.value;
                    syncMergedDisplay(wrapEl, city, province, rowSelect.value, true);
                } else {
                    syncMergedDisplay(wrapEl, city, province, '', true);
                }
                return;
            }
            wrapEl.dataset.overridden = 'true';
            syncMergedDisplay(wrapEl, city, province, select.value, true);
        });
    }

    function syncRowSourceToIndicators(tr) {
        if (!tr) return;
        const rowWrap = tr.querySelector('.source-input-wrap[data-role="row-source"]');
        if (!rowWrap) return;
        const rowSelect = rowWrap.querySelector('.source-type-select');
        if (!rowSelect) return;
        const code = rowSelect.value;
        const rowInput = rowWrap.querySelector('.source-merged-input');
        const rowDisplay = rowInput ? rowInput.value.trim() : '';
        tr.querySelectorAll('.source-input-wrap[data-role="indicator-source"]').forEach(function (wrap) {
            if (wrap.dataset.overridden === 'true') return;
            const indSelect = wrap.querySelector('.source-type-select');
            const indInput = wrap.querySelector('.source-merged-input');
            if (!indSelect) return;
            indSelect.value = code;
            if (indInput) {
                // 行级若已手改名称，同步到未单独覆盖的指标
                if (rowWrap.dataset.nameEdited === 'true' && rowDisplay) {
                    indInput.value = rowDisplay;
                    wrap.dataset.nameEdited = 'true';
                } else {
                    syncMergedDisplay(wrap, wrap.dataset.city, wrap.dataset.province, code, true);
                }
            }
        });
    }

    function bindRowSourceWrap(tr, rowWrap) {
        if (!rowWrap || rowWrap.dataset.bound === '1') return;
        rowWrap.dataset.bound = '1';
        const select = rowWrap.querySelector('.source-type-select');
        if (!select) return;
        const city = rowWrap.dataset.city;
        const province = rowWrap.dataset.province;
        bindMergedInputEdit(rowWrap);
        select.addEventListener('change', function () {
            syncMergedDisplay(rowWrap, city, province, select.value, true);
            syncRowSourceToIndicators(tr);
        });
        const input = rowWrap.querySelector('.source-merged-input');
        if (input) {
            input.addEventListener('input', function () {
                syncRowSourceToIndicators(tr);
            });
        }
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
            if (text === code) {
                input.value = composeDisplay(city, province, code);
            } else {
                input.value = text;
                wrapEl.dataset.nameEdited = 'true';
            }
        } else {
            if (select) select.value = '';
            input.value = text;
            wrapEl.dataset.nameEdited = 'true';
        }
        if (options && options.markOverridden) {
            wrapEl.dataset.overridden = 'true';
        }
    }

    function readSubmitCode(sourceTd) {
        const select = sourceTd && sourceTd.querySelector('.source-type-select');
        return select ? select.value.trim() : '';
    }

    function readDisplayName(sourceTd) {
        const wrap = sourceTd && sourceTd.querySelector('.source-input-wrap');
        if (!wrap) return '';
        const input = wrap.querySelector('.source-merged-input');
        const select = wrap.querySelector('.source-type-select');
        const display = input ? input.value.trim() : '';
        if (display) return display;
        const code = select ? select.value.trim() : '';
        if (!code) return '';
        return composeDisplay(wrap.dataset.city, wrap.dataset.province, code) || code;
    }

    function readSubmitCodeWithFallback(indicatorTd, rowTd) {
        const indicatorCode = readSubmitCode(indicatorTd);
        if (indicatorCode) return indicatorCode;
        return readSubmitCode(rowTd);
    }

    /** 提交用：始终保存具体来源文字，不再落类别 code。 */
    function readSubmitValue(sourceTd) {
        return readDisplayName(sourceTd);
    }

    function readSubmitValueWithFallback(indicatorTd, rowTd) {
        const ind = readDisplayName(indicatorTd);
        if (ind) return ind;
        const indCode = readSubmitCode(indicatorTd);
        if (indCode) {
            const wrap = indicatorTd && indicatorTd.querySelector('.source-input-wrap');
            return composeDisplay(
                wrap && wrap.dataset.city,
                wrap && wrap.dataset.province,
                indCode
            ) || '';
        }
        const row = readDisplayName(rowTd);
        if (row) return row;
        const rowCode = readSubmitCode(rowTd);
        if (!rowCode) return '';
        const rowWrap = rowTd && rowTd.querySelector('.source-input-wrap');
        return composeDisplay(
            rowWrap && rowWrap.dataset.city,
            rowWrap && rowWrap.dataset.province,
            rowCode
        ) || '';
    }

    function refreshProvinceScoped(container, province) {
        if (!container) return;
        container.querySelectorAll('.source-input-wrap').forEach(function (wrap) {
            const select = wrap.querySelector('.source-type-select');
            if (!select || !select.value) return;
            const opt = getOptionMeta(select.value);
            if (opt && opt.scope === 'province' && wrap.dataset.nameEdited !== 'true') {
                syncMergedDisplay(wrap, wrap.dataset.city, province, select.value, true);
            }
            wrap.dataset.province = province || '';
        });
    }

    return {
        setOptions,
        getOptions,
        initFromScript,
        loadFromApi,
        buildCellHtml,
        bindCell,
        bindAllIn,
        composeDisplay,
        applyLoadedValue,
        readSubmitCode,
        readSubmitCodeWithFallback,
        readSubmitValue,
        readSubmitValueWithFallback,
        refreshProvinceScoped,
        syncRowSourceToIndicators,
        guessCodeFromDisplay,
    };
})();
