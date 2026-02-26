/* Component Library - Application Logic
   Project OconDat v3 - IFC-first classification
   Expects: DB global from data.js, SHAPES global from shapes.js */

(function () {
    'use strict';

    let db = null;
    let activeIfcClass = null;  // null = all
    let activeCategory = null;  // NL-SfB filter (secondary)
    let activeManufacturer = null;  // null = all
    var PAGE_SIZE = 1000;
    var filteredItems = [];
    var displayedCount = 0;

    // ── Init ──────────────────────────────────────────────────────
    function init() {
        if (typeof DB !== 'undefined') {
            db = DB;
        } else {
            document.getElementById('grid').innerHTML =
                '<div class="empty">Failed to load component data.</div>';
            return;
        }

        var fabCount = (db.manufacturers || []).length;
        document.getElementById('subtitle').textContent =
            db.metadata.total + ' componenten | ' +
            fabCount + ' fabrikanten | ' +
            db.metadata.project;

        buildSidebar();

        // Handle URL parameters for deep-linking
        var urlParams = new URLSearchParams(window.location.search);
        var urlFab = urlParams.get('fab');
        var urlSerie = urlParams.get('serie');
        var urlIfc = urlParams.get('ifc');
        if (urlIfc) {
            activeIfcClass = urlIfc;
            document.querySelectorAll('.ifc-item').forEach(function (el) {
                el.classList.remove('active');
                if (el.dataset.ifc === urlIfc) el.classList.add('active');
            });
        }
        if (urlFab) {
            activeManufacturer = urlFab;
            document.querySelectorAll('.fab-item').forEach(function (el) {
                el.classList.remove('active');
                if (el.dataset.fab === urlFab) el.classList.add('active');
            });
            if (urlSerie) {
                document.getElementById('search').value = urlSerie;
            }
            updateFilterBadge();
        }

        applyFilters();

        document.getElementById('search').addEventListener('input', applyFilters);
        document.getElementById('overlay').addEventListener('click', function (e) {
            if (e.target === this) closeModal();
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') closeModal();
        });
    }

    // ── Sidebar ───────────────────────────────────────────────────
    function buildSidebar() {
        buildManufacturerList();
        buildIfcClassList();
        buildCategoryList();
    }

    function buildManufacturerList() {
        var container = document.getElementById('fab-list');
        if (!container) return;

        // "All" item
        var allItem = document.createElement('div');
        allItem.className = 'fab-item active';
        allItem.dataset.fab = '';
        allItem.innerHTML =
            '<span class="fab-name">Alle fabrikanten</span>' +
            '<span class="fab-count">' + db.metadata.total + '</span>';
        allItem.onclick = function () { selectManufacturer(null, this); };
        container.appendChild(allItem);

        // Manufacturer items
        (db.manufacturers || []).forEach(function (fab) {
            var item = document.createElement('div');
            item.className = 'fab-item';
            item.dataset.fab = fab.name;
            item.innerHTML =
                '<span class="fab-name">' + fab.name + '</span>' +
                '<span class="fab-count">' + fab.count + '</span>';
            item.onclick = function () { selectManufacturer(fab.name, this); };
            container.appendChild(item);
        });
    }

    function buildIfcClassList() {
        var container = document.getElementById('ifc-list');
        if (!container || !db.ifc_classes) return;

        // "All" item
        var allItem = document.createElement('div');
        allItem.className = 'ifc-item active';
        allItem.dataset.ifc = '';
        allItem.innerHTML =
            '<span class="ifc-item-name">Alle IFC klassen</span>' +
            '<span class="ifc-item-count">' + db.metadata.total + '</span>';
        allItem.onclick = function () { selectIfcClass(null, this); };
        container.appendChild(allItem);

        // Group the IFC classes
        var groups = {};
        var groupOrder = ['Structure', 'Enclosure', 'Opening', 'Finishing', 'Fastener', 'MEP', 'Furnishing', 'Site', 'Annotation', 'Other'];
        db.ifc_classes.forEach(function (cls) {
            var g = cls.group || 'Other';
            if (!groups[g]) groups[g] = [];
            groups[g].push(cls);
        });

        groupOrder.forEach(function (groupName) {
            if (!groups[groupName]) return;

            // Group header
            var header = document.createElement('div');
            header.className = 'ifc-group-header';
            header.textContent = groupName;
            container.appendChild(header);

            // Class items
            groups[groupName].forEach(function (cls) {
                var item = document.createElement('div');
                item.className = 'ifc-item';
                item.dataset.ifc = cls.id;
                var shortName = cls.id.replace('Ifc', '');
                item.innerHTML =
                    '<span class="ifc-item-name" title="' + cls.id + ' - ' + cls.name_nl + '">' + shortName + '</span>' +
                    '<span class="ifc-item-count">' + cls.count + '</span>';
                item.onclick = function () { selectIfcClass(cls.id, this); };
                container.appendChild(item);
            });
        });
    }

    function buildCategoryList() {
        var container = document.getElementById('cat-list');
        if (!container) return;

        // "All" item
        var allItem = document.createElement('div');
        allItem.className = 'cat-item active';
        allItem.dataset.cat = '';
        allItem.innerHTML =
            '<span class="cat-code"></span>' +
            '<span class="cat-name">Alle categorieën</span>' +
            '<span class="cat-count">' + db.metadata.total + '</span>';
        allItem.onclick = function () { selectCategory(null, this); };
        container.appendChild(allItem);

        // Category items
        (db.categories || []).forEach(function (cat) {
            var item = document.createElement('div');
            item.className = 'cat-item';
            item.dataset.cat = cat.id;
            item.innerHTML =
                '<span class="cat-code">' + cat.id + '</span>' +
                '<span class="cat-name">' + cat.name_nl + '</span>' +
                '<span class="cat-count">' + cat.count + '</span>';
            item.onclick = function () { selectCategory(cat.id, this); };
            container.appendChild(item);
        });
    }

    function selectManufacturer(fabName, el) {
        activeManufacturer = fabName;
        document.querySelectorAll('.fab-item').forEach(function (c) {
            c.classList.remove('active');
        });
        el.classList.add('active');
        applyFilters();
        updateFilterBadge();
    }

    function selectIfcClass(ifcId, el) {
        activeIfcClass = ifcId;
        document.querySelectorAll('.ifc-item').forEach(function (c) {
            c.classList.remove('active');
        });
        el.classList.add('active');
        applyFilters();
        updateFilterBadge();
    }

    function selectCategory(catId, el) {
        activeCategory = catId;
        document.querySelectorAll('.cat-item').forEach(function (c) {
            c.classList.remove('active');
        });
        el.classList.add('active');
        applyFilters();
        updateFilterBadge();
    }

    function updateFilterBadge() {
        var badge = document.getElementById('filter-badge');
        var parts = [];

        if (activeManufacturer) {
            parts.push(activeManufacturer);
        }
        if (activeIfcClass) {
            var cls = (db.ifc_classes || []).find(function (c) { return c.id === activeIfcClass; });
            parts.push(activeIfcClass.replace('Ifc', '') + (cls ? ' (' + cls.name_nl + ')' : ''));
        }
        if (activeCategory) {
            var cat = (db.categories || []).find(function (c) { return c.id === activeCategory; });
            parts.push('NL-SfB ' + activeCategory + (cat ? ' ' + cat.name_nl : ''));
        }

        if (parts.length > 0) {
            badge.style.display = 'inline-flex';
            badge.querySelector('.filter-text').textContent = parts.join(' / ');
        } else {
            badge.style.display = 'none';
        }
    }

    function clearFilter() {
        activeIfcClass = null;
        activeCategory = null;
        activeManufacturer = null;
        document.querySelectorAll('.ifc-item').forEach(function (c) {
            c.classList.remove('active');
        });
        document.querySelectorAll('.cat-item').forEach(function (c) {
            c.classList.remove('active');
        });
        document.querySelectorAll('.fab-item').forEach(function (c) {
            c.classList.remove('active');
        });
        var allIfc = document.querySelector('.ifc-item[data-ifc=""]');
        if (allIfc) allIfc.classList.add('active');
        var allCat = document.querySelector('.cat-item[data-cat=""]');
        if (allCat) allCat.classList.add('active');
        var allFab = document.querySelector('.fab-item[data-fab=""]');
        if (allFab) allFab.classList.add('active');
        applyFilters();
        updateFilterBadge();
    }
    window.clearFilter = clearFilter;

    // ── NL-SfB toggle ────────────────────────────────────────────
    function toggleNlSfb() {
        var content = document.getElementById('nlsfb-content');
        var arrow = document.getElementById('nlsfb-arrow');
        if (content.style.display === 'none') {
            content.style.display = 'block';
            arrow.innerHTML = '&#9660;';
        } else {
            content.style.display = 'none';
            arrow.innerHTML = '&#9654;';
        }
    }
    window.toggleNlSfb = toggleNlSfb;

    // ── Filtering ─────────────────────────────────────────────────
    function applyFilters() {
        var q = document.getElementById('search').value.toLowerCase().trim();
        filteredItems = db.components.filter(function (c) {
            // Manufacturer filter
            if (activeManufacturer && c.manufacturer !== activeManufacturer) return false;
            // IFC class filter
            if (activeIfcClass && c.ifc_class !== activeIfcClass) return false;
            // NL-SfB category filter
            if (activeCategory && (c.classification.nl_sfb || '91') !== activeCategory) return false;
            // Search filter
            if (!q) return true;
            if (c.name.toLowerCase().indexOf(q) >= 0) return true;
            if (c.ifc_class.toLowerCase().indexOf(q) >= 0) return true;
            if ((c.manufacturer || '').toLowerCase().indexOf(q) >= 0) return true;
            if ((c.serie || '').toLowerCase().indexOf(q) >= 0) return true;
            if (c.classification.description_nl.toLowerCase().indexOf(q) >= 0) return true;
            if (c.classification.description_en.toLowerCase().indexOf(q) >= 0) return true;
            for (var i = 0; i < c.tags.length; i++) {
                if (c.tags[i].toLowerCase().indexOf(q) >= 0) return true;
            }
            return false;
        });
        displayedCount = 0;
        document.getElementById('grid').innerHTML = '';
        renderPage();
    }

    // ── Grid ──────────────────────────────────────────────────────
    function renderCardHtml(c) {
        var idx = db.components.indexOf(c);
        var w = c.geometry.width_mm;
        var h = c.geometry.height_mm;
        var dimStr = w + ' x ' + h + ' mm';
        var fabLabel = c.manufacturer && c.manufacturer !== 'Generic'
            ? '<span class="fab-label">' + c.manufacturer + '</span>'
            : '';
        var profileBadge = c.ifc_profile
            ? '<span class="ifc-profile-card-badge">' + c.ifc_profile.type.replace('Ifc','').replace('ProfileDef','') + '</span>'
            : '';
        // IFC badge: strip "Ifc" prefix
        var ifcShort = c.ifc_class.replace('Ifc', '');
        // Predefined type badge (only if not USERDEFINED)
        var predBadge = c.ifc_predefined_type && c.ifc_predefined_type !== 'USERDEFINED'
            ? '<span class="pred-badge">' + c.ifc_predefined_type + '</span>'
            : '';
        // Material badge
        var matBadge = c.material
            ? '<span class="mat-badge">' + c.material.category + '</span>'
            : '';
        return '<div class="card" onclick="openModal(' + idx + ')">' +
            '<div class="preview">' +
                '<img src="' + c.geometry.svg + '" alt="' + c.name + '" loading="lazy">' +
            '</div>' +
            '<div class="info">' +
                '<div class="info-top">' +
                    '<span class="ifc-badge">' + ifcShort + '</span>' +
                    predBadge +
                    profileBadge +
                    matBadge +
                    fabLabel +
                '</div>' +
                '<div class="name" title="' + c.name + '">' + c.name + '</div>' +
                '<div class="dims">' + dimStr + '</div>' +
            '</div>' +
        '</div>';
    }

    function renderPage() {
        var grid = document.getElementById('grid');
        var empty = document.getElementById('empty');
        var total = filteredItems.length;

        // Update stats
        if (total > PAGE_SIZE) {
            var showing = Math.min(displayedCount + PAGE_SIZE, total);
            document.getElementById('stats').textContent =
                showing + ' / ' + total + ' componenten';
        } else {
            document.getElementById('stats').textContent = total + ' componenten';
        }

        if (!total) {
            grid.innerHTML = '';
            empty.style.display = 'block';
            removePager();
            return;
        }
        empty.style.display = 'none';

        // Render next batch
        var batch = filteredItems.slice(displayedCount, displayedCount + PAGE_SIZE);
        var html = batch.map(renderCardHtml).join('');

        // Append to grid (first page replaces, subsequent pages append)
        if (displayedCount === 0) {
            grid.innerHTML = html;
        } else {
            grid.insertAdjacentHTML('beforeend', html);
        }
        displayedCount += batch.length;

        // Update stats after render
        if (total > PAGE_SIZE) {
            document.getElementById('stats').textContent =
                displayedCount + ' / ' + total + ' componenten';
        }

        // Show/hide pager
        updatePager();
    }

    function updatePager() {
        removePager();
        var remaining = filteredItems.length - displayedCount;
        if (remaining <= 0) return;

        var pager = document.createElement('div');
        pager.id = 'pager';
        pager.className = 'pager';
        var nextBatch = Math.min(remaining, PAGE_SIZE);
        pager.innerHTML =
            '<button class="load-more-btn" onclick="loadMore()">' +
                'Laad meer (' + nextBatch + ' van ' + remaining + ' resterend)' +
            '</button>';
        document.getElementById('grid').parentNode.appendChild(pager);
    }

    function removePager() {
        var old = document.getElementById('pager');
        if (old) old.remove();
    }

    function loadMore() {
        renderPage();
    }
    window.loadMore = loadMore;

    // ── Modal ─────────────────────────────────────────────────────
    function openModal(i) {
        var c = db.components[i];
        // Header
        document.getElementById('m-title').textContent = c.name;
        document.getElementById('m-ifc-tag').textContent =
            c.ifc_class + '.' + c.ifc_predefined_type;

        // SVG preview
        document.getElementById('m-svg').innerHTML =
            '<img src="' + c.geometry.svg + '" alt="' + c.name + '">';

        // Base properties
        var baseHtml =
            '<table class="prop-table">';
        if (c.manufacturer) {
            baseHtml += '<tr><th>Fabrikant</th><td>' + c.manufacturer + '</td></tr>';
        }
        if (c.serie) {
            baseHtml += '<tr><th>Serie</th><td>' + c.serie + '</td></tr>';
        }
        if (c.product) {
            baseHtml += '<tr><th>Product</th><td>' + c.product + '</td></tr>';
        }
        baseHtml +=
            '<tr><th>IFC Class</th><td>' + c.ifc_class + '</td></tr>' +
            '<tr><th>Predefined Type</th><td>' + c.ifc_predefined_type + '</td></tr>';
        if (c.ifc_profile) {
            baseHtml += '<tr><th>Profile Type</th><td><span class="ifc-profile-badge">' +
                c.ifc_profile.type + '</span></td></tr>';
        }
        if (c.material) {
            baseHtml += '<tr><th>Materiaal</th><td>' + c.material.material + '</td></tr>';
        }
        if (c.classification.nl_sfb) {
            baseHtml += '<tr><th>NL-SfB</th><td>' + c.classification.nl_sfb + ' ' + c.classification.description_nl + '</td></tr>';
        }
        baseHtml +=
            '<tr><th>Breedte</th><td>' + c.geometry.width_mm + ' mm</td></tr>' +
            '<tr><th>Hoogte</th><td>' + c.geometry.height_mm + ' mm</td></tr>' +
            '</table>';

        // IFC Pset section
        if (c.ifc_pset && db.pset_definitions && db.pset_definitions[c.ifc_pset]) {
            var psetDef = db.pset_definitions[c.ifc_pset];
            baseHtml += '<div class="section-label" style="margin-top:1rem">' + c.ifc_pset + '</div>' +
                '<p class="pset-desc">' + psetDef.description_nl + '</p>' +
                '<table class="prop-table pset-table">';
            psetDef.properties.forEach(function(prop) {
                var val = (c.pset_values && c.pset_values[prop.name]) || '—';
                baseHtml += '<tr><th>' + prop.name + '</th>' +
                    '<td>' + val + ' <span class="pset-type">' + prop.type + '</span></td></tr>';
            });
            baseHtml += '</table>';
        }

        // IFC Profile parameters section
        if (c.ifc_profile && c.ifc_profile.params) {
            baseHtml += '<div class="section-label" style="margin-top:1rem">IFC Profile Parameters</div>' +
                '<div class="ifc-profile-info">' +
                '<span class="ifc-profile-type">' + c.ifc_profile.type + '</span>' +
                '<span class="ifc-profile-desc">' + (c.ifc_profile.description || '') + '</span>' +
                '</div>' +
                '<table class="prop-table ifc-params">';
            c.ifc_profile.params.forEach(function(param) {
                baseHtml += '<tr><th>' + param + '</th><td class="param-placeholder">—</td></tr>';
            });
            baseHtml += '</table>';
        }

        document.getElementById('m-base-props').innerHTML = baseHtml;

        // Regional property tabs
        var regions = Object.keys(c.properties);
        var tabsEl = document.getElementById('m-prop-tabs');
        var propsEl = document.getElementById('m-region-props');

        tabsEl.innerHTML = regions.map(function (r, idx) {
            return '<div class="prop-tab' + (idx === 0 ? ' active' : '') +
                '" data-region="' + r + '" onclick="switchRegionTab(this)">' + r + '</div>';
        }).join('');

        if (regions.length > 0) {
            renderRegionProps(c.properties[regions[0]], propsEl);
        } else {
            propsEl.innerHTML = '<em>No regional properties</em>';
        }

        // Tags
        var tagsHtml = c.tags.map(function (t) {
            return '<span class="tag">' + t + '</span>';
        }).join('');
        document.getElementById('m-tags').innerHTML = tagsHtml;

        // Source attribution
        var sourceEl = document.getElementById('m-source');
        if (sourceEl) {
            var sourceHtml = '<span class="source-label">Bron:</span> ' + (c.dxf_source || 'Unknown');
            if (c.manufacturer) {
                sourceHtml += ' | <span class="source-label">Fabrikant:</span> ' + c.manufacturer;
            }
            sourceEl.innerHTML = sourceHtml;
        }

        // Store component ref for tab switching
        document.getElementById('overlay').dataset.compIdx = i;

        // Footer
        var hasShapes = typeof SHAPES !== 'undefined' && SHAPES[c.id] && SHAPES[c.id].length > 0;
        document.getElementById('m-foot').innerHTML =
            (c.dxf_source
                ? '<a class="dl-btn dxf" href="../' + c.dxf_source + '" download>DXF</a>'
                : '') +
            (hasShapes
                ? '<button class="dl-btn o2d" onclick="exportToO2D(\'' + c.id + '\')">' +
                  '<span class="o2d-icon">&#9998;</span> Open 2D Studio</button>'
                : '') +
            '<span class="dl-btn off">IFC (coming soon)</span>';

        // Show
        document.getElementById('overlay').classList.add('active');
    }
    window.openModal = openModal;

    function renderRegionProps(props, container) {
        var html = '<table class="prop-table">';
        Object.keys(props).forEach(function (key) {
            var label = key.replace(/_/g, ' ');
            label = label.charAt(0).toUpperCase() + label.slice(1);
            html += '<tr><th>' + label + '</th><td>' + props[key] + '</td></tr>';
        });
        html += '</table>';
        container.innerHTML = html;
    }

    function switchRegionTab(el) {
        var region = el.dataset.region;
        el.parentElement.querySelectorAll('.prop-tab').forEach(function (t) {
            t.classList.remove('active');
        });
        el.classList.add('active');
        var idx = parseInt(document.getElementById('overlay').dataset.compIdx, 10);
        var c = db.components[idx];
        renderRegionProps(c.properties[region], document.getElementById('m-region-props'));
    }
    window.switchRegionTab = switchRegionTab;

    function closeModal() {
        document.getElementById('overlay').classList.remove('active');
    }
    window.closeModal = closeModal;

    // ── Open 2D Studio Export ────────────────────────────────────
    var O2D_URL = 'http://127.0.0.1:49100';
    var O2D_BATCH = 80;

    function exportToO2D(compId) {
        var shapes = (typeof SHAPES !== 'undefined') ? SHAPES[compId] : null;
        if (!shapes || !shapes.length) {
            alert('Geen shape-data beschikbaar voor dit component.');
            return;
        }

        var btn = document.querySelector('.dl-btn.o2d');
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Verbinden...';
        }

        fetch(O2D_URL + '/health', { method: 'GET', mode: 'cors' })
            .then(function (r) { return r.json(); })
            .then(function () {
                if (btn) btn.textContent = 'Exporteren...';
                sendShapesToO2D(shapes, compId, btn);
            })
            .catch(function () {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<span class="o2d-icon">&#9998;</span> Open 2D Studio';
                }
                alert('Open 2D Studio is niet actief.\nStart de applicatie en probeer opnieuw.');
            });
    }
    window.exportToO2D = exportToO2D;

    function sendShapesToO2D(shapes, compId, btn) {
        var layerSet = {};
        shapes.forEach(function (s) {
            if (s.layer && s.layer !== '0' && !layerSet[s.layer]) {
                layerSet[s.layer] = s.style ? s.style.stroke : '#333333';
            }
        });

        var layerPromises = Object.keys(layerSet).map(function (name) {
            var js = 'try{cad.addLayer(' + JSON.stringify({ name: name, color: layerSet[name] }) + ')}catch(e){}';
            return o2dEval(js);
        });

        Promise.all(layerPromises)
            .then(function () {
                return sendBatches(shapes, 0, btn);
            })
            .then(function (total) {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<span class="o2d-icon">&#10003;</span> Verstuurd! (' + total + ')';
                    setTimeout(function () {
                        btn.innerHTML = '<span class="o2d-icon">&#9998;</span> Open 2D Studio';
                    }, 3000);
                }
            })
            .catch(function (err) {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<span class="o2d-icon">&#9998;</span> Open 2D Studio';
                }
                alert('Export mislukt: ' + err.message);
            });
    }

    function sendBatches(shapes, offset, btn) {
        if (offset >= shapes.length) return Promise.resolve(shapes.length);

        var batch = shapes.slice(offset, offset + O2D_BATCH);
        var js = '(function(){var s=' + JSON.stringify(batch) + ';var n=0;' +
            'for(var i=0;i<s.length;i++){try{cad.addShape(s[i]);n++}catch(e){}}' +
            'return JSON.stringify({added:n})})()';

        return o2dEval(js).then(function () {
            var next = offset + O2D_BATCH;
            if (btn) {
                var pct = Math.min(100, Math.round(next / shapes.length * 100));
                btn.textContent = 'Exporteren... ' + pct + '%';
            }
            return sendBatches(shapes, next, btn);
        });
    }

    function o2dEval(jsCode) {
        return fetch(O2D_URL + '/eval', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: jsCode })
        }).then(function (r) { return r.json(); });
    }

    // ── Start ─────────────────────────────────────────────────────
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
