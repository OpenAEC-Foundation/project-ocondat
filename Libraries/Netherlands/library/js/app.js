/* Open BIM Library - Application Logic
   Project OconDat
   Expects: DB (from data.js), renderCurves (from renderer.js) */

(function () {
    'use strict';

    let db = DB || { components: [] };

    function init() {
        document.getElementById('subtitle').textContent =
            db.total + ' componenten | ' + (db.source || '');
        buildFilters();
        applyFilters();
    }

    function buildFilters() {
        const bar = document.querySelector('.toolbar-inner');
        const prefixes = [...new Set(db.components.map(c => {
            const m = c.family.trim().match(/^(\d{2})/);
            return m ? m[1] : '??';
        }))].sort();
        prefixes.forEach(p => {
            const b = document.createElement('button');
            b.className = 'filter-btn';
            b.dataset.f = p;
            b.textContent = p;
            b.onclick = () => setFilter(b);
            bar.insertBefore(b, document.getElementById('stats'));
        });
    }

    function setFilter(btn) {
        const all = document.querySelector('[data-f="all"]');
        if (btn.dataset.f === 'all') {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        } else {
            all.classList.remove('active');
            btn.classList.toggle('active');
            if (!document.querySelector('.filter-btn.active')) all.classList.add('active');
        }
        applyFilters();
    }
    // Expose for inline onclick
    window.setFilter = setFilter;

    function applyFilters() {
        const q = document.getElementById('search').value.toLowerCase();
        const active = [...document.querySelectorAll('.filter-btn.active:not([data-f="all"])')].map(b => b.dataset.f);
        const all = document.querySelector('[data-f="all"]').classList.contains('active');
        render(db.components.filter(c => {
            const match = !q || c.family.toLowerCase().includes(q) || c.type.toLowerCase().includes(q);
            const m = c.family.trim().match(/^(\d{2})/);
            const pf = m ? m[1] : '??';
            return match && (all || active.includes(pf));
        }));
    }

    function render(items) {
        document.getElementById('stats').textContent = items.length + ' componenten';
        const grid = document.getElementById('grid');
        const empty = document.getElementById('empty');
        if (!items.length) { grid.innerHTML = ''; empty.style.display = 'block'; return; }
        empty.style.display = 'none';
        grid.innerHTML = items.map((c, i) => {
            const idx = db.components.indexOf(c);
            return `
            <div class="card" onclick="openModal(${idx})">
                <div class="preview"><canvas id="cv${idx}" width="180" height="130"></canvas></div>
                <div class="info">
                    <div class="family">${c.family}</div>
                    <div class="name" title="${c.type}">${c.type}</div>
                    <div class="dims">${c.width_mm} x ${c.height_mm} mm</div>
                </div>
            </div>`;
        }).join('');

        items.forEach(c => {
            const idx = db.components.indexOf(c);
            const cv = document.getElementById('cv' + idx);
            if (cv && c.curves) renderCurves(cv, c.curves, 8, c.hatches);
        });
    }

    function openModal(i) {
        const c = db.components[i];
        document.getElementById('m-title').textContent = c.family + ' : ' + c.type;
        document.getElementById('m-fam').textContent = c.family;
        document.getElementById('m-type').textContent = c.type;
        document.getElementById('m-w').textContent = c.width_mm + ' mm';
        document.getElementById('m-h').textContent = c.height_mm + ' mm';
        document.getElementById('m-c').textContent = c.curves.length;
        const mc = document.getElementById('m-canvas');
        if (c.curves) renderCurves(mc, c.curves, 15, c.hatches);
        document.getElementById('m-foot').innerHTML =
            (c.dxf ? '<a class="dl-btn dxf" href="' + c.dxf + '" download>Download DXF</a>' : '') +
            '<span class="dl-btn off">IFC</span>';
        document.getElementById('overlay').classList.add('active');
    }
    window.openModal = openModal;

    function closeModal() {
        document.getElementById('overlay').classList.remove('active');
    }
    window.closeModal = closeModal;

    // Event listeners
    document.getElementById('search').addEventListener('input', applyFilters);
    document.getElementById('overlay').addEventListener('click', function (e) {
        if (e.target === this) closeModal();
    });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

    init();
})();
