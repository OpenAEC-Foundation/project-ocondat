/* Open BIM Library - Canvas Render Engine
   Project OconDat */

function arcCenter(x0, y0, x1, y1, r, la, sf) {
    let dx = x1 - x0, dy = y1 - y0, d = Math.sqrt(dx * dx + dy * dy);
    if (d > 2 * r) r = d / 2 + 0.01;
    let a = d / 2, h = Math.sqrt(Math.max(r * r - a * a, 0));
    let mx = (x0 + x1) / 2, my = (y0 + y1) / 2;
    let cx1 = mx + h * (y0 - y1) / d, cy1 = my + h * (x1 - x0) / d;
    let cx2 = mx - h * (y0 - y1) / d, cy2 = my - h * (x1 - x0) / d;
    if ((la === 0 && sf === 1) || (la === 1 && sf === 0)) return [cx1, cy1, r];
    return [cx2, cy2, r];
}

const DASH_PATTERNS = {
    solid: [], center: [8, 4, 2, 4], hidden: [4, 3], dashed: [5, 5]
};

const STYLE_COLORS = {
    solid: '#333', center: '#c0392b', hidden: '#7f8c8d', dashed: '#555'
};

const HATCH_STYLES = {
    '<Solid fill>':           { fill: '#d0d0d0' },
    '06_DP_prefab_beton_1:5': { a: 45, s: 3, c: '#8899aa', a2: 135 },
    '13_DP_loofhout_1:5':     { a: 45, s: 2, c: '#8B6914' },
    '00_DP_hout_naaldhout':   { a: 30, s: 2.5, c: '#a07030' },
    '00_DP_gips_hor':         { a: 0, s: 2, c: '#b0b0b0' },
    '90_DP_A_veen':           { a: 0, s: 3, c: '#7a6b5a' },
    '00_DP_isolatie':         { a: 45, s: 4, c: '#e8d44d' },
    'default':                { a: 45, s: 3, c: '#999' }
};

function renderCurves(canvas, curves, pad, hatches) {
    pad = pad || 6;
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    let mnX = 1e9, mnY = 1e9, mxX = -1e9, mxY = -1e9;

    for (const c of curves) {
        const p = c.split('|');
        if (p[0] === 'L') {
            for (let k = 1; k <= 3; k += 2) { mnX = Math.min(mnX, +p[k]); mxX = Math.max(mxX, +p[k]); }
            for (let k = 2; k <= 4; k += 2) { mnY = Math.min(mnY, +p[k]); mxY = Math.max(mxY, +p[k]); }
        } else if (p[0] === 'A') {
            for (let k = 1; k <= 3; k += 2) { mnX = Math.min(mnX, +p[k]); mxX = Math.max(mxX, +p[k]); }
            for (let k = 2; k <= 4; k += 2) { mnY = Math.min(mnY, +p[k]); mxY = Math.max(mxY, +p[k]); }
        }
    }

    const dw = mxX - mnX || 1, dh = mxY - mnY || 1;
    const sc = Math.min((W - 2 * pad) / dw, (H - 2 * pad) / dh);
    const ox = (W - dw * sc) / 2, oy = (H - dh * sc) / 2;
    const tx = x => ox + (x - mnX) * sc;
    const ty = y => oy + (mxY - y) * sc;

    ctx.clearRect(0, 0, W, H);

    // Render hatches first (behind curves)
    if (hatches && hatches.length) {
        for (const h of hatches) {
            const hs = HATCH_STYLES[h.pattern] || HATCH_STYLES['default'];
            ctx.save();
            ctx.beginPath();
            let first = true;
            for (const bc of h.boundary) {
                const bp = bc.split('|');
                if (bp[0] === 'FL') {
                    if (first) { ctx.moveTo(tx(+bp[1]), ty(+bp[2])); first = false; }
                    ctx.lineTo(tx(+bp[3]), ty(+bp[4]));
                } else if (bp[0] === 'FA') {
                    let bx0 = +bp[1], by0 = +bp[2], bx1 = +bp[3], by1 = +bp[4], br = +bp[5], bla = +bp[6], bsf = +bp[7];
                    if (first) { ctx.moveTo(tx(bx0), ty(by0)); first = false; }
                    let [bcx, bcy, brr] = arcCenter(bx0, by0, bx1, by1, br, bla, bsf);
                    let bsr = brr * sc;
                    let bsa = Math.atan2(ty(by0) - ty(bcy), tx(bx0) - tx(bcx));
                    let bea = Math.atan2(ty(by1) - ty(bcy), tx(bx1) - tx(bcx));
                    ctx.arc(tx(bcx), ty(bcy), bsr, bsa, bea, bsf === 1);
                }
            }
            ctx.closePath();

            if (hs.fill) {
                ctx.fillStyle = hs.fill;
                ctx.fill();
            } else {
                ctx.clip();
                const spacing = Math.max(hs.s * sc, 2);
                const diag = Math.sqrt(W * W + H * H);
                function drawHatchLines(angle) {
                    const rad = angle * Math.PI / 180;
                    const cos = Math.cos(rad), sin = Math.sin(rad);
                    const n = Math.ceil(diag / spacing) + 2;
                    ctx.beginPath();
                    for (let i = -n; i <= n; i++) {
                        const off = i * spacing;
                        const cx = W / 2 + off * cos;
                        const cy = H / 2 + off * sin;
                        ctx.moveTo(cx - diag * sin, cy + diag * cos);
                        ctx.lineTo(cx + diag * sin, cy - diag * cos);
                    }
                    ctx.stroke();
                }
                ctx.strokeStyle = hs.c || '#999';
                ctx.lineWidth = Math.max(sc * 0.1, 0.3);
                ctx.setLineDash([]);
                drawHatchLines(hs.a || 45);
                if (hs.a2 !== undefined) drawHatchLines(hs.a2);
            }
            ctx.restore();
        }
    }

    // Render curves on top
    for (const c of curves) {
        const p = c.split('|');
        let style = 'solid';
        if (p[0] === 'L' && p.length > 5) style = p[5];
        if (p[0] === 'A' && p.length > 8) style = p[8];

        ctx.strokeStyle = STYLE_COLORS[style] || '#333';
        ctx.lineWidth = style === 'center' ? Math.max(sc * 0.15, 0.3) : Math.max(sc * 0.25, 0.5);
        ctx.setLineDash((DASH_PATTERNS[style] || []).map(d => d * Math.max(sc * 0.15, 0.5)));

        ctx.beginPath();
        if (p[0] === 'L') {
            ctx.moveTo(tx(+p[1]), ty(+p[2]));
            ctx.lineTo(tx(+p[3]), ty(+p[4]));
        } else if (p[0] === 'A') {
            let x0 = +p[1], y0 = +p[2], x1 = +p[3], y1 = +p[4], r = +p[5], la = +p[6], sf = +p[7];
            let [cx, cy, rr] = arcCenter(x0, y0, x1, y1, r, la, sf);
            let sr = rr * sc;
            let sa = Math.atan2(ty(y0) - ty(cy), tx(x0) - tx(cx));
            let ea = Math.atan2(ty(y1) - ty(cy), tx(x1) - tx(cx));
            ctx.arc(tx(cx), ty(cy), sr, sa, ea, sf === 1);
        }
        ctx.stroke();
    }
    ctx.setLineDash([]);
}
