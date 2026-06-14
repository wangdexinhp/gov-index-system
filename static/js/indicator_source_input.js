/**
 * 指标录入：数据来源类别下拉 + 可编辑具体名称
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

    function placeNameForCode(city, province, code) {
        const opt = options.find(o => o.code === code);
        const cityName = (city || '').trim();
        const provName = (province || '').trim();
        if (!code || !opt) return cityName;
        if (opt.scope === 'province') return provName;
        if (opt.scope === 'city') return cityName;
        return cityName || provName;
    }

    function composeDisplay(city, province, code) {
        const opt = options.find(o => o.code === code);
        if (!opt) return '';
        return opt.suffix || opt.label || '';
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

    function buildCellHtml(nameAttr, city, province) {
        const opts = options.map(o =>
            `<option value="${escapeHtml(o.code)}">${escapeHtml(o.label)}</option>`
        ).join('');
        const place = (city || '').trim();
        return `<div class="source-input-wrap" data-city="${escapeHtml(city)}" data-province="${escapeHtml(province)}">
            <input type="text" class="source-place-input" readonly value="${escapeHtml(place)}" title="地市/省份">
            <div class="source-main">
                <select class="source-type-select" title="来源类别">
                    <option value="">来源类别</option>${opts}
                </select>
                <input type="text" class="source-detail-input" placeholder="来源名称" title="来源名称（仅展示）">
            </div>
        </div>`;
    }

    function syncPlaceAndDetail(wrapEl, city, province, code) {
        if (!wrapEl) return;
        const placeInput = wrapEl.querySelector('.source-place-input');
        const input = wrapEl.querySelector('.source-detail-input');
        if (placeInput) {
            placeInput.value = placeNameForCode(city, province, code);
        }
        if (input && code) {
            input.value = composeDisplay(city, province, code);
        }
    }

    function bindCell(wrapEl, city, province) {
        if (!wrapEl) return;
        const select = wrapEl.querySelector('.source-type-select');
        const input = wrapEl.querySelector('.source-detail-input');
        if (!select || !input) return;
        select.addEventListener('change', function () {
            if (!select.value) {
                const placeInput = wrapEl.querySelector('.source-place-input');
                if (placeInput) placeInput.value = (city || '').trim();
                input.value = '';
                return;
            }
            syncPlaceAndDetail(wrapEl, city, province, select.value);
        });
    }

    function bindAllIn(container) {
        if (!container) return;
        container.querySelectorAll('.source-input-wrap').forEach(function (wrap) {
            bindCell(wrap, wrap.dataset.city, wrap.dataset.province);
        });
    }

    function applyLoadedValue(wrapEl, sourceValue, city, province) {
        if (!wrapEl) return;
        const select = wrapEl.querySelector('.source-type-select');
        const input = wrapEl.querySelector('.source-detail-input');
        if (!input) return;
        const text = (sourceValue || '').trim();
        if (!text) return;
        const code = guessCodeFromDisplay(text);
        if (code) {
            if (select) select.value = code;
            syncPlaceAndDetail(wrapEl, city, province, code);
            if (text !== code && !text.endsWith(composeDisplay(city, province, code))) {
                input.value = text;
            }
        } else {
            if (select) select.value = '';
            input.value = text;
        }
    }

    function readSubmitCode(sourceTd) {
        const select = sourceTd && sourceTd.querySelector('.source-type-select');
        return select ? select.value.trim() : '';
    }

    /** @deprecated 入库请用 readSubmitCode；文本框仅供界面展示 */
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
                syncPlaceAndDetail(wrap, wrap.dataset.city, province, select.value);
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
        readSubmitValue,
        refreshProvinceScoped,
        guessCodeFromDisplay,
    };
})();
