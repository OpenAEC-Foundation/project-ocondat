/* Fabrikanten page - Application Logic
   Project OconDat
   Expects: DB global from data.js */

(function () {
    'use strict';

    var db = null;
    var manufacturers = [];
    var activeFilter = 'all';

    // Country code to flag/name mapping
    var COUNTRIES = {
        'LU': 'Luxemburg',
        'DE': 'Duitsland',
        'NL': 'Nederland',
        'CH': 'Zwitserland',
        'FI': 'Finland',
        'BE': 'Belgi\u00eb',
        'FR': 'Frankrijk',
        'UK': 'Verenigd Koninkrijk',
        'US': 'Verenigde Staten',
        'AT': '\u00d6ostenrijk',
        'SE': 'Zweden',
        'DK': 'Denemarken',
        'NO': 'Noorwegen',
        'IT': 'Itali\u00eb',
        'ES': 'Spanje',
        'PL': 'Polen',
        'CZ': 'Tsjechi\u00eb',
    };

    // ── Init ──────────────────────────────────────────────────────
    function init() {
        if (typeof DB !== 'undefined') {
            db = DB;
        } else {
            document.getElementById('fab-grid').innerHTML =
                '<div class="empty">Kan fabrikant-gegevens niet laden.</div>';
            return;
        }

        manufacturers = db.manufacturers || [];

        document.getElementById('subtitle').textContent =
            manufacturers.length + ' fabrikanten | ' +
            db.metadata.total + ' componenten | ' +
            db.metadata.project;

        renderGrid(manufacturers);

        // Search
        document.getElementById('fab-search').addEventListener('input', applyFilters);

        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                document.querySelectorAll('.filter-btn').forEach(function (b) {
                    b.classList.remove('active');
                });
                btn.classList.add('active');
                activeFilter = btn.dataset.filter;
                applyFilters();
            });
        });

        // Modal close
        document.getElementById('fab-overlay').addEventListener('click', function (e) {
            if (e.target === this) closeFabModal();
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') closeFabModal();
        });
    }

    // ── Filtering ─────────────────────────────────────────────────
    function applyFilters() {
        var q = document.getElementById('fab-search').value.toLowerCase().trim();
        var filtered = manufacturers.filter(function (fab) {
            // Status filter
            if (activeFilter !== 'all') {
                var status = fab.status || 'active';
                if (status !== activeFilter) return false;
            }
            // Search filter
            if (!q) return true;
            if (fab.name.toLowerCase().indexOf(q) >= 0) return true;
            if ((fab.description || '').toLowerCase().indexOf(q) >= 0) return true;
            if ((fab.country || '').toLowerCase().indexOf(q) >= 0) return true;
            // Search in series names
            var series = fab.series || [];
            for (var i = 0; i < series.length; i++) {
                if (series[i].name.toLowerCase().indexOf(q) >= 0) return true;
            }
            return false;
        });
        renderGrid(filtered);
    }

    // ── Grid ──────────────────────────────────────────────────────
    function renderGrid(items) {
        document.getElementById('fab-stats').textContent = items.length + ' fabrikanten';
        var grid = document.getElementById('fab-grid');
        var empty = document.getElementById('fab-empty');

        if (!items.length) {
            grid.innerHTML = '';
            empty.style.display = 'block';
            return;
        }
        empty.style.display = 'none';

        grid.innerHTML = items.map(function (fab, idx) {
            var status = fab.status || 'active';
            var statusLabel = status === 'active' ? 'Actief' :
                              status === 'inactive' ? 'Inactief' : 'Historisch';
            var country = fab.country || '';
            var countryName = COUNTRIES[country] || country;
            var series = fab.series || [];
            var maxPills = 4;

            // Series pills
            var pillsHtml = '';
            for (var i = 0; i < Math.min(series.length, maxPills); i++) {
                pillsHtml += '<span class="serie-pill">' +
                    escapeHtml(series[i].name) +
                    '<span class="pill-count">(' + series[i].count + ')</span>' +
                    '</span>';
            }
            if (series.length > maxPills) {
                pillsHtml += '<span class="serie-more">+' + (series.length - maxPills) + ' meer</span>';
            }

            var foundedText = fab.founded ? 'Opgericht ' + fab.founded : '';

            // Find actual index in manufacturers array for modal
            var realIdx = manufacturers.indexOf(fab);

            return '<div class="fab-card ' + status + '" onclick="openFabModal(' + realIdx + ')">' +
                '<div class="fab-card-head">' +
                    '<h3>' + escapeHtml(fab.name) + '</h3>' +
                    (country ? '<span class="country-flag">' + country + '</span>' : '') +
                '</div>' +
                '<div class="fab-card-body">' +
                    '<div style="margin-bottom:0.4rem">' +
                        '<span class="status-badge ' + status + '">' + statusLabel + '</span>' +
                    '</div>' +
                    (fab.description
                        ? '<div class="fab-desc">' + escapeHtml(fab.description) + '</div>'
                        : '') +
                    '<div class="fab-card-series">' + pillsHtml + '</div>' +
                '</div>' +
                '<div class="fab-card-foot">' +
                    '<span class="fab-count-total">' + fab.count + ' componenten</span>' +
                    '<span class="fab-founded">' + foundedText + '</span>' +
                '</div>' +
            '</div>';
        }).join('');
    }

    // ── Modal ─────────────────────────────────────────────────────
    function openFabModal(idx) {
        var fab = manufacturers[idx];
        if (!fab) return;

        var status = fab.status || 'active';
        var statusLabel = status === 'active' ? 'Actief' :
                          status === 'inactive' ? 'Inactief' : 'Historisch';
        var country = fab.country || '';
        var countryName = COUNTRIES[country] || country;

        // Header
        document.getElementById('fm-name').textContent = fab.name;
        var metaParts = [];
        if (countryName) metaParts.push(countryName);
        if (fab.founded) metaParts.push('Opgericht ' + fab.founded);
        document.getElementById('fm-meta').textContent = metaParts.join(' \u2022 ');

        var statusEl = document.getElementById('fm-status');
        statusEl.textContent = statusLabel;
        statusEl.className = 'status-badge ' + status;

        // Description
        document.getElementById('fm-description').textContent =
            fab.description || fab.name + ' componenten.';

        // Properties table
        var propsHtml = '';
        propsHtml += '<tr><th>Componenten</th><td>' + fab.count + '</td></tr>';
        if (fab.series) {
            propsHtml += '<tr><th>Productfamilies</th><td>' + fab.series.length + '</td></tr>';
        }
        if (country) {
            propsHtml += '<tr><th>Land</th><td>' + countryName + ' (' + country + ')</td></tr>';
        }
        if (fab.founded) {
            propsHtml += '<tr><th>Opgericht</th><td>' + fab.founded + '</td></tr>';
        }
        propsHtml += '<tr><th>Status</th><td>' + statusLabel + '</td></tr>';
        document.getElementById('fm-props').innerHTML = propsHtml;

        // Series list
        var series = fab.series || [];
        var seriesHtml = '';
        if (series.length === 0) {
            seriesHtml = '<p style="color:var(--text-light);font-size:0.85rem">Geen productfamilies beschikbaar</p>';
        } else {
            series.forEach(function (s) {
                seriesHtml += '<div class="fm-series-item" onclick="browseSerieComponents(\'' +
                    escapeAttr(fab.name) + '\', \'' + escapeAttr(s.name) + '\')">' +
                    '<span class="serie-name">' + escapeHtml(s.name) + '</span>' +
                    (s.ifc_class ? '<span class="serie-ifc">' + escapeHtml(s.ifc_class) + '</span>' : '') +
                    '<span class="serie-count">' + s.count + '</span>' +
                '</div>';
            });
        }
        document.getElementById('fm-series-list').innerHTML = seriesHtml;

        // Footer links
        var websiteEl = document.getElementById('fm-website');
        if (fab.website) {
            websiteEl.href = fab.website;
            websiteEl.style.display = '';
        } else {
            websiteEl.style.display = 'none';
        }

        var browseEl = document.getElementById('fm-browse');
        browseEl.href = 'index.html?fab=' + encodeURIComponent(fab.name);

        // Show modal
        document.getElementById('fab-overlay').classList.add('active');
    }
    window.openFabModal = openFabModal;

    function closeFabModal() {
        document.getElementById('fab-overlay').classList.remove('active');
    }
    window.closeFabModal = closeFabModal;

    function browseSerieComponents(fabName, serieName) {
        window.location.href = 'index.html?fab=' + encodeURIComponent(fabName) +
            '&serie=' + encodeURIComponent(serieName);
    }
    window.browseSerieComponents = browseSerieComponents;

    // ── Utility ───────────────────────────────────────────────────
    function escapeHtml(str) {
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function escapeAttr(str) {
        return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
    }

    // ── Start ─────────────────────────────────────────────────────
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
