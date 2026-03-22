import sys, json, traceback
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, KeepTogether, PageBreak, HRFlowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.platypus import Flowable

# \u2500\u2500 Minimal palette: black/grey always, colour only for priority \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
INK      = colors.HexColor('#1A1A1A')   # headings
BODY     = colors.HexColor('#3D3D3D')   # body text
MUTED    = colors.HexColor('#767676')   # labels, captions
RULE     = colors.HexColor('#D4D4D4')   # lines, borders
SURFACE  = colors.HexColor('#F7F7F7')   # header backgrounds
WHITE    = colors.white
# Colour only used for severity indicators
C_RED    = colors.HexColor('#C0392B')   # high priority text
C_RED_BG = colors.HexColor('#FDF2F2')   # high priority row bg
C_AMB    = colors.HexColor('#B7710A')   # medium text
C_AMB_BG = colors.HexColor('#FDF8F0')   # medium row bg
C_GRN    = colors.HexColor('#1E7B45')   # nothing noted
C_BRAND  = colors.HexColor('#E8001D')   # logo only

W, H = A4
ML = MR = 18*mm
MT = MB = 16*mm
AW = W - ML - MR

def mk(n, **k): return ParagraphStyle(n, **k)

S = {
    'logo':   mk('logo',  fontName='Helvetica-Bold', fontSize=13, textColor=INK),
    'meta':   mk('meta',  fontName='Helvetica', fontSize=7, textColor=MUTED,
                           alignment=TA_RIGHT, leading=10),
    'addr_h': mk('ah',    fontName='Helvetica-Bold', fontSize=17, textColor=INK, leading=20),
    'addr_s': mk('as',    fontName='Helvetica', fontSize=8.5, textColor=MUTED, leading=12),
    'pg_h':   mk('ph',    fontName='Helvetica-Bold', fontSize=11, textColor=INK, spaceAfter=2),
    'pg_d':   mk('pd',    fontName='Helvetica', fontSize=8, textColor=MUTED, spaceAfter=6, leading=11),
    'sec':    mk('sec',   fontName='Helvetica-Bold', fontSize=7, textColor=MUTED,
                           spaceBefore=10, spaceAfter=3, letterSpacing=0.8),
    'body':   mk('body',  fontName='Helvetica', fontSize=8.5, textColor=BODY, leading=13),
    'body_s': mk('bs',    fontName='Helvetica', fontSize=8, textColor=MUTED, leading=11),
    'kv_k':   mk('kvk',   fontName='Helvetica', fontSize=8, textColor=MUTED),
    'kv_v':   mk('kvv',   fontName='Helvetica', fontSize=8, textColor=INK),
    'kv_r':   mk('kvr',   fontName='Helvetica-Bold', fontSize=8, textColor=C_RED),
    'kv_a':   mk('kva',   fontName='Helvetica-Bold', fontSize=8, textColor=C_AMB),
    'kv_g':   mk('kvg',   fontName='Helvetica', fontSize=8, textColor=C_GRN),
    'flag_s': mk('fls',   fontName='Helvetica-Bold', fontSize=6.5, textColor=MUTED,
                           leading=9, letterSpacing=0.5),
    'flag_h': mk('flh',   fontName='Helvetica-Bold', fontSize=8.5, textColor=BODY,
                           leading=12, spaceAfter=2),
    'flag_b': mk('flb',   fontName='Helvetica', fontSize=8, textColor=BODY, leading=12),
    'q_n':    mk('qn',    fontName='Helvetica-Bold', fontSize=8.5, textColor=C_BRAND),
    'q_b':    mk('qb',    fontName='Helvetica', fontSize=8.5, textColor=BODY, leading=13),
    'disc':   mk('disc',  fontName='Helvetica', fontSize=8, textColor=MUTED, leading=12),
    'notice': mk('ntc',   fontName='Helvetica', fontSize=8, textColor=C_AMB, leading=12),
    'notice_h':mk('nth',  fontName='Helvetica-Bold', fontSize=7, textColor=C_AMB,
                           leading=10, letterSpacing=0.5, spaceAfter=2),
    'pos':    mk('pos',   fontName='Helvetica', fontSize=8, textColor=C_GRN, leading=12),
    'verdict':mk('vrd',   fontName='Helvetica', fontSize=8.5, textColor=BODY, leading=13),
}

# \u2500\u2500 Severity config \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
SEV = {
    'high':   ('HIGH PRIORITY',   C_RED, C_RED_BG),
    'medium': ('WORTH REVIEWING', C_AMB, C_AMB_BG),
    'low':    ('GOOD TO KNOW',    MUTED,  SURFACE),
}

def safe(v, d=''): return str(v).strip() if v else d

# \u2500\u2500 Flowables \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

class Rule(Flowable):
    def __init__(self, color=RULE, thickness=0.5, space_before=0, space_after=4):
        super().__init__()
        self.color = color; self.thickness = thickness
        self.spaceBefore = space_before; self.spaceAfter = space_after
    def wrap(self, aw, ah): self.width = aw; self.height = self.thickness; return aw, self.thickness
    def draw(self):
        self.canv.setStrokeColor(self.color); self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)

class FlagCard(Flowable):
    """Clean flag card: thin left rule, no background fill except very subtle."""
    def __init__(self, severity, category, issue, recommendation, aw):
        super().__init__()
        label, tc, bg = SEV.get(severity, SEV['low'])
        self.tc = tc; self.bg = bg; self.label = label
        self.category = safe(category)
        self.issue = safe(issue)
        self.rec = safe(recommendation)
        self._aw = aw; self._h = 0

    def wrap(self, aw, ah):
        self.width = aw
        pad = 6; sw = 2*mm; inner = aw - sw - pad * 2
        ps = [
            Paragraph(self.label + ('  \u00b7  ' + self.category if self.category else ''), S['flag_s']),
            Paragraph(self.issue, S['flag_h']),
            Paragraph(self.rec,   S['flag_b']),
        ]
        total = pad
        for p in ps:
            _, h = p.wrapOn(self.canv, inner, 9999)
            total += h + 1.5
        total += pad
        self._h = total; self.height = total
        self._ps = ps; self._pad = pad; self._sw = sw; self._inner = inner
        return aw, total

    def draw(self):
        c = self.canv; w, h = self.width, self._h
        # No fill \u2014 white background only
        c.setFillColor(WHITE); c.rect(0, 0, w, h, fill=1, stroke=0)
        # Left accent stripe only (3pt wide)
        c.setFillColor(self.tc); c.rect(0, 0, self._sw, h, fill=1, stroke=0)
        # Very light border
        c.setStrokeColor(RULE); c.setLineWidth(0.3); c.rect(0, 0, w, h, fill=0, stroke=1)
        x = self._sw + self._pad; y = h - self._pad
        for p in self._ps:
            _, ph = p.wrapOn(c, self._inner, 9999)
            y -= ph; p.drawOn(c, x, y); y -= 1.5

class SeverityBadge(Flowable):
    """Small pill badge - fits within its bounds properly."""
    def __init__(self, severity):
        super().__init__()
        label, tc, bg = SEV.get(severity, SEV['low'])
        self.label = label; self.tc = tc; self.bg = bg
        self.width = 58; self.height = 14
    def wrap(self, aw, ah): return self.width, self.height
    def draw(self):
        c = self.canv
        c.setFillColor(self.bg); c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        c.setStrokeColor(self.tc); c.setLineWidth(0.5)
        c.rect(0, 0, self.width, self.height, fill=0, stroke=1)
        c.setFont('Helvetica-Bold', 6); c.setFillColor(self.tc)
        c.drawCentredString(self.width / 2, 4, self.label)

class SectionBox(Flowable):
    """Headed box for 'nothing noted' sections."""
    def __init__(self, title, tag, tag_color, rows):
        super().__init__()
        self.title = title; self.tag = tag; self.tc = tag_color; self.rows = rows; self._h = 0
    def wrap(self, aw, ah):
        self.width = aw; self._bi(aw); return aw, self._h
    def _bi(self, aw):
        hh = 15; pad = 8; cw = 90; vw = aw - pad*2 - cw - 8
        total = hh + 4; self._rd = []; self._hh = hh
        for cat, val, note in self.rows:
            cp = Paragraph(safe(cat), S['kv_k'])
            vp = Paragraph(safe(val), S['body_s'])
            np_ = Paragraph(safe(note), mk('n2', fontName='Helvetica', fontSize=7,
                              textColor=MUTED, leading=10)) if note else None
            _, ch = cp.wrapOn(self.canv, cw, 9999)
            _, vh = vp.wrapOn(self.canv, vw, 9999)
            nh = 0
            if np_: _, nh = np_.wrapOn(self.canv, vw, 9999)
            rh = max(ch, vh + (nh + 1 if np_ else 0)) + 7
            self._rd.append((cp, vp, np_, ch, vh, nh, rh, cw, vw))
            total += rh
        total += 4; self._h = total; self.height = total

    def draw(self):
        c = self.canv; aw = self.width; h = self._h; pad = 8
        c.setStrokeColor(RULE); c.setLineWidth(0.4); c.rect(0, 0, aw, h, fill=0, stroke=1)
        c.setFillColor(SURFACE); c.rect(0, h-self._hh, aw, self._hh, fill=1, stroke=0)
        c.setStrokeColor(RULE); c.setLineWidth(0.4); c.line(0, h-self._hh, aw, h-self._hh)
        c.setFont('Helvetica-Bold', 7.5); c.setFillColor(INK)
        c.drawString(pad, h - self._hh + 4, self.title.upper())
        # Tag
        tw = len(self.tag) * 5 + 10
        tx = aw - pad - tw; ty = h - self._hh + 2
        c.setFillColor(SURFACE); c.rect(tx, ty, tw, 11, fill=1, stroke=0)
        c.setStrokeColor(self.tc); c.setLineWidth(0.4); c.rect(tx, ty, tw, 11, fill=0, stroke=1)
        c.setFont('Helvetica-Bold', 6.5); c.setFillColor(self.tc)
        c.drawCentredString(tx + tw/2, ty + 2.5, self.tag.upper())
        y = h - self._hh - 4
        for cp, vp, np_, ch, vh, nh, rh, cw, vw in self._rd:
            y -= rh
            c.setStrokeColor(RULE); c.setLineWidth(0.3); c.line(pad, y, aw-pad, y)
            cp.drawOn(c, pad, y + rh - ch - 4)
            vp.drawOn(c, pad + cw + 8, y + rh - vh - 4)
            if np_: np_.drawOn(c, pad + cw + 8, y + rh - vh - nh - 5)

# \u2500\u2500 Helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def rb():
    return Table([['']], colWidths=[AW], rowHeights=[3],
        style=TableStyle([('BACKGROUND',(0,0),(-1,-1),C_BRAND),
                          ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))

def logo_row(right):
    return Table(
        [[Paragraph('<b>PropertyOwl</b> <font color="#E8001D">AI</font>', S['logo']),
          Paragraph(right, S['meta'])]],
        colWidths=[AW*0.5, AW*0.5],
        style=TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                          ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
                          ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))

def rule(): return Rule()

def sec_label(t):
    return Paragraph(t.upper(), S['sec'])

def kv_table(rows, aw=None):
    aw = aw or AW
    kw = aw * 0.36; vw = aw * 0.64
    hint_map = {'r': S['kv_r'], 'a': S['kv_a'], 'g': S['kv_g']}
    trows = [[Paragraph(safe(k), S['kv_k']),
              Paragraph(safe(v) if v else '\u2014', hint_map.get(h, S['kv_v']))]
             for k, v, h in rows]
    t = Table(trows, colWidths=[kw, vw])
    t.setStyle(TableStyle([
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),
        ('LINEBELOW',(0,0),(-1,-1),0.3,RULE),('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))
    return t

def flag_table(flags):
    """Compact table of all flags for cover page \u2014 subtle, readable, not busy."""
    if not flags:
        return Spacer(1, 1)
    
    sev_labels = {'high': 'High priority', 'medium': 'Worth reviewing', 'low': 'Good to know'}
    sev_colors = {'high': C_RED, 'medium': C_AMB, 'low': MUTED}
    
    rows = []
    for f in flags:
        sev = f.get('severity', 'low')
        tc = sev_colors.get(sev, MUTED)
        label = sev_labels.get(sev, 'Note')
        cat = safe(f.get('category', ''))
        issue = safe(f.get('issue', ''))
        
        # Severity pill \u2014 coloured text label only (no inline XML colour tricks)
        sev_p = Paragraph(label, mk(
            'fp_s', fontName='Helvetica-Bold', fontSize=7.5, textColor=tc, leading=10))
        cat_p = Paragraph(cat, mk('fp_c', fontName='Helvetica', fontSize=7.5,
                                   textColor=MUTED, leading=10))
        iss_p = Paragraph(issue, mk('fp_i', fontName='Helvetica', fontSize=8,
                                     textColor=BODY, leading=12))
        
        rows.append([sev_p, cat_p, iss_p])
    
    # Col widths: severity, category, issue
    cw = [72, 72, AW - 148]
    t = Table(rows, colWidths=cw, repeatRows=0)
    ts_cmds = [
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LINEBELOW',(0,0),(-1,-1),0.3,RULE),
        ('LINEABOVE',(0,0),(-1,0),0.3,RULE),
    ]
    # Subtle background on high priority rows
    for i, f in enumerate(flags):
        if f.get('severity') == 'high':
            ts_cmds.append(('BACKGROUND',(0,i),(-1,i),colors.HexColor('#FDF8F8')))
    t.setStyle(TableStyle(ts_cmds))
    return t


def stat_row(stats):
    """Clean stat pills: (count, label, color)"""
    cells = []
    for n, lbl, color in stats:
        inner = Table(
            [[Paragraph(f'<b>{n}</b>', mk('sn', fontName='Helvetica-Bold', fontSize=18,
                         textColor=color, alignment=TA_CENTER))],
             [Paragraph(lbl.upper(), mk('sl', fontName='Helvetica-Bold', fontSize=6.5,
                         textColor=MUTED, alignment=TA_CENTER, letterSpacing=0.4))]],
            colWidths=[AW/4 - 2])
        cells.append(inner)
    t = Table([cells], colWidths=[AW/4]*4)
    t.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,RULE),('INNERGRID',(0,0),(-1,-1),0.5,RULE),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3),
    ]))
    return t

def notice_box(text):
    # Single cell \u2014 label inline with text, no split columns
    full = Paragraph('<b>Note</b>  ' + text, mk('ntc2',
        fontName='Helvetica', fontSize=8, textColor=C_AMB, leading=12))
    return Table([[full]],
                 colWidths=[AW],
                 style=TableStyle([
                     ('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#FFFBF0')),
                     ('LINEBELOW',(0,0),(-1,-1),0.4,colors.HexColor('#E9C46A')),
                     ('LINETOP',(0,0),(-1,-1),0.4,colors.HexColor('#E9C46A')),
                     ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
                     ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
                 ]))

def footer_fn(addr, total_pages):
    def fn(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(RULE); canvas.setLineWidth(0.4)
        canvas.line(ML, 11*mm, W-MR, 11*mm)
        canvas.setFont('Helvetica', 6.5); canvas.setFillColor(MUTED)
        canvas.drawCentredString(W/2, 8*mm,
            f'PropertyOwl AI  \u00b7  Conveyancer Pack  \u00b7  {addr}  \u00b7  Page {doc.page} of {total_pages}')
        canvas.restoreState()
    return fn

# \u2500\u2500 Page 1: Cover \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def page1(story, prop, s32, con, addr, today):
    story += [rb(), Spacer(1, 4*mm),
              logo_row(f'Conveyancer Review Pack  \u00b7  {today}<br/>For buyer reference only \u2014 not legal advice'),
              Spacer(1, 5*mm)]

    sec = s32.get('sections') or {}
    csec = con.get('sections') or {}
    ts = sec.get('title_and_ownership') or {}
    ps = sec.get('planning_and_zoning') or {}
    bp = sec.get('building_permits') or {}
    ec = sec.get('easements_and_covenants') or {}
    pd = (csec.get('price_and_deposit') or {})
    st = (csec.get('settlement') or {})
    co = (csec.get('cooling_off') or {})
    sp = (csec.get('special_conditions') or {})

    # Address block
    addr_parts = [safe(prop.get('address')), safe(prop.get('suburb')) +
                  (' VIC ' + safe(prop.get('postcode')) if prop.get('postcode') else ' VIC')]
    story.append(Paragraph(', '.join(filter(None, addr_parts)), S['addr_h']))

    sub_parts = []
    if ts.get('lot_plan'): sub_parts.append(safe(ts['lot_plan']))
    if ts.get('volume_folio'): sub_parts.append('Vol ' + safe(ts['volume_folio']))
    if s32.get('vendor_names'): sub_parts.append('Vendor: ' + safe(s32['vendor_names']))
    if sub_parts: story.append(Paragraph('  \u00b7  '.join(sub_parts), S['addr_s']))
    story.append(Spacer(1, 5*mm))

    # Stats
    af = (s32.get('red_flags') or []) + (con.get('red_flags') or [])
    hf = [f for f in af if f.get('severity') == 'high']
    mf = [f for f in af if f.get('severity') == 'medium']
    lf = [f for f in af if f.get('severity') == 'low']
    pf = s32.get('positive_findings') or []

    story.append(stat_row([
        (str(len(hf)), 'High priority', C_RED),
        (str(len(mf)), 'Worth reviewing', C_AMB),
        (str(len(lf)), 'Good to know', MUTED),
        (str(len(pf)), 'Nothing noted', C_GRN),
    ]))
    story.append(Spacer(1, 4*mm))

    # Notice
    story.append(notice_box(
        'This is an AI-assisted summary of the uploaded documents. It is not legal advice. '
        'Flags are starting points for questions \u2014 your conveyancer is the final authority before signing.'))
    story.append(Spacer(1, 3*mm))

    # Summary
    parts = []
    if hf: parts.append(f'{len(hf)} item{"s" if len(hf)>1 else ""} warrant{"" if len(hf)==1 else ""} attention before exchange')
    if mf: parts.append(f'{len(mf)} item{"s" if len(mf)>1 else ""} worth discussing with your conveyancer')
    if lf: parts.append(f'{len(lf)} minor item{"s" if len(lf)>1 else ""} noted for awareness')
    if not parts:
        summary = 'No significant items identified. Your conveyancer should still review all details before exchange.'
    else:
        summary = '. '.join(p.capitalize() for p in parts) + '. Your conveyancer is the final authority on all matters before signing.'
    story.append(Paragraph(summary, S['verdict']))
    story.append(Spacer(1, 4*mm))

    # Flags \u2014 compact table on cover page
    if af:
        story.append(sec_label('Items flagged for your attention'))
        story.append(rule())
        story.append(flag_table(af))

    story.append(Spacer(1, 2*mm))

    # Two-column summary tables
    hw = AW / 2 - 5
    left = [
        ('Purchase price', pd.get('purchase_price'), None),
        ('Deposit', (safe(pd.get('deposit_amount')) + (' \u2014 ' + safe(pd['deposit_holder']) if pd.get('deposit_holder') else '')) if pd.get('deposit_amount') else None, None),
        ('Settlement', st.get('settlement_date') or 'TBC', None),
        ('Cooling off', (co.get('period') or '3 business days') + (' \u2014 WAIVED' if co.get('waived') else ''), None),
        ('Special conditions', str(len(sp.get('conditions') or [])) + ' identified' if (sp.get('conditions') or []) else 'None identified', None),
    ]
    right = [
        ('Volume / Folio', ts.get('volume_folio'), None),
        ('Lot / Plan', ts.get('lot_plan'), None),
        ('Planning zone', ps.get('zone'), None),
        ('Encumbrances', 'Mortgage ' + (ts.get('encumbrances') or [{}])[0].get('reference','') if (ts.get('encumbrances') or []) else 'None', 'r' if ts.get('encumbrances') else None),
        ('Easements', str(len(ec.get('items') or [])) + ' recorded' if (ec.get('items') or []) else 'None noted', None),
        ('Building permits', 'None in 7-yr lookback' if bp.get('status') == 'clear' else safe(bp.get('summary'), '\u2014')[:60], None),
    ]
    two = Table([
        [Table([[sec_label('Contract & settlement')], [rule()], [kv_table(left, hw)]], colWidths=[hw]),
         Table([[sec_label('Title snapshot')],        [rule()], [kv_table(right, hw)]], colWidths=[hw])]
    ], colWidths=[hw+5, hw+5])
    two.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
        ('RIGHTPADDING',(0,0),(0,0),10),
    ]))
    story.append(two)

# \u2500\u2500 Page 2: Nothing noted \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def page2(story, s32, addr):
    story.append(PageBreak())
    story += [rb(), Spacer(1,4*mm), logo_row(addr), Spacer(1,2*mm),
              Paragraph('Areas with nothing of concern noted', S['pg_h']),
              Paragraph('The following areas did not produce any flags based on the documents provided. '
                        'This does not constitute legal clearance \u2014 verify independently with your conveyancer.', S['pg_d'])]

    story.append(notice_box(
        'Absence of a flag means the AI review did not identify anything requiring attention in the documents uploaded. '
        'Documents may be incomplete. Always rely on your conveyancer\'s independent verification before exchange.'))
    story.append(Spacer(1, 4*mm))

    sec = s32.get('sections') or {}
    ps  = sec.get('planning_and_zoning') or {}
    os_ = sec.get('outgoings') or {}
    bp  = sec.get('building_permits') or {}
    ec  = sec.get('easements_and_covenants') or {}
    vd  = sec.get('vendor_disclosure') or {}

    for title, tag, tc, rows in [
        ('Title & Ownership', 'Nothing noted', C_GRN, [
            ('Estate type', 'Fee simple \u2014 freehold title in registered proprietors\' names.', 'Verify current ownership at LANDATA before exchange.'),
            ('Caveats', 'No caveats recorded at time of S32 preparation.', 'Caveats can be lodged at any time \u2014 confirm with fresh title search before settlement.'),
            ('Covenants', 'No restrictive covenants noted on title or plan of subdivision.', 'Review plan with conveyancer to confirm no OC rules affect intended use.'),
        ]),
        ('Planning & Zoning', 'Nothing noted', C_GRN, [
            ('Zone', safe(ps.get('zone'), 'General Residential Zone') + ' \u2014 permits standard residential use.', 'Check with council if significant alterations or subdivision are intended.'),
            ('Overlays', 'None detected.', 'Verify via council planning portal. Overlays affect renovation costs and insurance.'),
            ('GAIC', 'Growth Areas Infrastructure Contribution not applicable.', None),
        ]),
        ('Land Tax & Government Levies', 'Nothing noted', C_GRN, [
            ('Land tax', safe(os_.get('land_tax'), '$0.00') + ' \u2014 vendor PPOR exemption applies.', 'This exemption belongs to the vendor. Consider your own land tax position if purchasing as investment.'),
            ('Windfall gains tax', safe(os_.get('windfall_gains_tax'), 'NIL') + ' \u2014 confirmed by SRO Clearance Certificate.', 'Applies to rezoning events \u2014 none applicable here.'),
        ]),
        ('GST & Vendor Disclosure', 'Nothing noted', C_GRN, [
            ('GST withholding', 'No GST withholding obligation \u2014 standard residential sale.', None),
            ('Services', ', '.join(vd.get('services_connected') or ['Water','Sewerage','Electricity','Gas','Telephone']) + ' \u2014 all noted as connected.', 'Physically verify at inspection.'),
        ]),
        ('Building Permits (7-year lookback)', 'Verify physically', C_AMB, [
            ('Permits recorded', safe(bp.get('summary'), 'No building permits recorded in the 7-year lookback period.'),
             'Absence of permits does not confirm no works were performed. Ask the vendor directly and inspect physically.'),
        ]),
    ]:
        story.append(SectionBox(title, tag, tc, rows))
        story.append(Spacer(1, 3*mm))

    ec_items = ec.get('items') or []
    if ec_items:
        story.append(SectionBox('Easements', 'Note for reference', MUTED, [
            ('Recorded easement', str(len(ec_items)) + ' easement(s) recorded \u2014 refer to plan of subdivision for diagram.',
             'Review with your conveyancer to confirm the easement does not affect intended use.'),
        ]))
    else:
        story.append(SectionBox('Easements', 'Nothing noted', C_GRN, [
            ('Easements', 'No easements recorded on title.', 'Verify via plan of subdivision.'),
        ]))

# \u2500\u2500 Page 3: Title details \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def page3(story, s32, addr):
    story.append(PageBreak())
    story += [rb(), Spacer(1,4*mm), logo_row(addr), Spacer(1,2*mm),
              Paragraph('Property & Title Details', S['pg_h']),
              Paragraph('Extracted from Section 32 Vendor Statement and LANDATA title search. '
                        'Verify all details with your conveyancer before exchange.', S['pg_d'])]

    sec = s32.get('sections') or {}
    t  = sec.get('title_and_ownership') or {}
    p  = sec.get('planning_and_zoning') or {}
    oc = sec.get('owners_corporation') or {}
    ec = sec.get('easements_and_covenants') or {}
    bp = sec.get('building_permits') or {}

    encs = t.get('encumbrances') or []
    enc_str = '; '.join(safe(e.get('type')).upper() + ' ' + safe(e.get('reference')) +
                        (' \u2014 ' + safe(e.get('detail')) if e.get('detail') else '')
                        for e in encs) if encs else 'None recorded'

    story.append(sec_label('Title & ownership')); story.append(rule())
    story.append(kv_table([
        ('Volume / Folio', t.get('volume_folio'), None),
        ('Lot / Plan', t.get('lot_plan'), None),
        ('Estate type', 'Fee simple \u2014 freehold', None),
        ('Registered proprietors', t.get('registered_proprietors'), None),
        ('Encumbrances on title', enc_str, 'r' if encs else None),
        ('Caveats', 'None recorded', None),
        ('Covenants', 'None recorded on title or plan', None),
    ])); story.append(Spacer(1, 4*mm))

    story.append(sec_label('Planning & zoning')); story.append(rule())
    overlays = ', '.join(p.get('overlays') or []) or 'None detected'
    story.append(kv_table([
        ('Planning zone', p.get('zone'), None),
        ('Overlays', overlays, None),
        ('GAIC applicable', 'Yes \u2014 ' + safe(p.get('gaic_amount')) if p.get('gaic_applicable') else 'Not applicable', None),
        ('Planning certificate', 'Issued by council \u2014 attached to S32', None),
    ])); story.append(Spacer(1, 4*mm))

    story.append(sec_label('Owners corporation')); story.append(rule())
    if oc.get('applicable'):
        fee = safe(oc.get('annual_fee'), '\u2014')
        fee_h = 'a' if (not oc.get('annual_fee') or 'not' in fee.lower()) else None
        story.append(kv_table([
            ('OC applicable', 'Yes', None),
            ('OC registration', oc.get('oc_number'), None),
            ('Annual levy', fee, fee_h),
            ('Lot liability', oc.get('lot_liability'), None),
            ('Special levies', safe(oc.get('special_levies'), 'Not disclosed \u2014 request OC certificate'), 'a'),
        ]))
    else:
        story.append(kv_table([('OC applicable', 'No', None)]))
    story.append(Spacer(1, 4*mm))

    story.append(sec_label('Easements & covenants')); story.append(rule())
    ei = ec.get('items') or []
    story.append(kv_table([
        ('Easements', str(len(ei)) + ' recorded \u2014 refer to plan of subdivision' if ei else 'None noted', None),
        ('Restrictive covenants', 'None recorded on title', None),
    ])); story.append(Spacer(1, 4*mm))

    story.append(sec_label('Building permits \u2014 7-year lookback')); story.append(rule())
    permits = bp.get('permits') or []
    story.append(kv_table([
        ('Permits recorded', str(len(permits)) + ' permit(s)' if permits else 'None in 7-year lookback', None),
        ('Note', 'Absence of permits does not confirm no works were carried out. Inspect physically.', None),
    ]))

# \u2500\u2500 Page 4: Outgoings \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def page4(story, s32, con, addr):
    story.append(PageBreak())
    story += [rb(), Spacer(1,4*mm), logo_row(addr), Spacer(1,2*mm),
              Paragraph('Outgoings & Financial', S['pg_h']),
              Paragraph('Extracted from council rate notice, water statement, SRO clearance certificate and OC certificate. '
                        'All figures to be verified at settlement.', S['pg_d'])]

    sec = s32.get('sections') or {}
    o  = sec.get('outgoings') or {}
    oc = sec.get('owners_corporation') or {}
    rw = any(str(f.get('category','')).lower() in ['council rates','outgoings'] and
             f.get('severity') == 'high' for f in (s32.get('red_flags') or []))

    story.append(sec_label('Council rates')); story.append(rule())
    story.append(kv_table([
        ('Council', o.get('council_name'), None),
        ('Capital improved value', o.get('civ'), None),
        ('Annual council rates', o.get('council_rates'), 'r' if rw else None),
        ('Status', 'Outstanding at time of S32 \u2014 vendor to clear before settlement' if rw else 'No arrears noted', 'r' if rw else 'g'),
    ])); story.append(Spacer(1, 4*mm))

    story.append(sec_label('Water & sewerage')); story.append(rule())
    story.append(kv_table([
        ('Water authority', o.get('water_authority'), None),
        ('Water charges', o.get('water_charges'), None),
        ('Current balance', safe(o.get('unpaid_water_balance'), '$0.00'), 'g'),
    ])); story.append(Spacer(1, 4*mm))

    story.append(sec_label('Land tax & windfall gains tax')); story.append(rule())
    story.append(kv_table([
        ('Land tax', o.get('land_tax'), 'g'),
        ('Windfall gains tax', o.get('windfall_gains_tax'), 'g'),
        ('Note', 'Vendor PPOR exemption does not transfer. Consider your own position if purchasing as investment.', None),
    ])); story.append(Spacer(1, 4*mm))

    story.append(sec_label('Owners corporation fees')); story.append(rule())
    if oc.get('applicable'):
        fee = safe(oc.get('annual_fee'), '\u2014')
        fh = 'a' if (not oc.get('annual_fee') or 'not' in fee.lower() or fee == '\u2014') else None
        story.append(kv_table([
            ('Annual levy', fee, fh),
            ('Special levies', safe(oc.get('special_levies'), 'Not disclosed \u2014 obtain OC certificate'), 'a'),
            ('Lot liability', oc.get('lot_liability'), None),
        ]))
    else:
        story.append(kv_table([('OC fees', 'No owners corporation applicable', 'g')]))
    story.append(Spacer(1, 4*mm))

    story.append(sec_label('GST')); story.append(rule())
    story.append(kv_table([
        ('GST applicable', 'No \u2014 residential sale, no GST withholding required', 'g'),
    ]))

# \u2500\u2500 Pages 5+: Issue detail \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def page5_issues(story, af, addr):
    hf = [f for f in af if f.get('severity') == 'high']
    mf = [f for f in af if f.get('severity') == 'medium']
    lf = [f for f in af if f.get('severity') == 'low']

    for f in hf:
        story.append(PageBreak())
        story += [rb(), Spacer(1,4*mm), logo_row(addr), Spacer(1,2*mm)]

        # Title row with badge on right
        cat = safe(f.get('category'))
        title_t = Table(
            [[Paragraph('Issue detail \u2014 ' + cat, S['pg_h']),
              Table([[Paragraph('HIGH PRIORITY',
                                mk('hp', fontName='Helvetica-Bold', fontSize=6.5,
                                   textColor=C_RED, alignment=TA_CENTER))]],
                    colWidths=[58], rowHeights=[14],
                    style=TableStyle([
                        ('BACKGROUND',(0,0),(-1,-1),C_RED_BG),
                        ('BOX',(0,0),(-1,-1),0.5,C_RED),
                        ('ALIGN',(0,0),(-1,-1),'CENTER'),
                        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                        ('TOPPADDING',(0,0),(-1,-1),0),
                        ('BOTTOMPADDING',(0,0),(-1,-1),0),
                    ]))]],
            colWidths=[AW-65, 65],
            style=TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                              ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
                              ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
        story.append(title_t)
        story.append(Paragraph('High priority \u2014 requires attention before exchange', S['pg_d']))
        story.append(rule())
        story.append(Spacer(1, 2*mm))

        story.append(sec_label('What was found')); story.append(rule())
        story.append(Paragraph(safe(f.get('issue')), S['body'])); story.append(Spacer(1, 4*mm))

        story.append(sec_label('What to consider')); story.append(rule())
        story.append(Paragraph(safe(f.get('recommendation')), S['body'])); story.append(Spacer(1, 4*mm))

        story.append(sec_label('Document reference')); story.append(rule())
        story.append(kv_table([
            ('Category', cat, None),
            ('Severity', 'High priority', 'r'),
            ('Source', 'Section 32 Vendor Statement / LANDATA title search', None),
        ])); story.append(Spacer(1, 4*mm))

        # Action boxes \u2014 plain grey, no strong colours
        for label, text in [
            ('Questions for your conveyancer',
             'Discuss this item before exchange. Ask: Is this standard for this transaction type? '
             'What steps are needed before settlement? Are there risks if not resolved beforehand?'),
            ('Keep in mind',
             'This flag is based on AI analysis of the uploaded documents. '
             'Your conveyancer is the appropriate authority to assess significance and advise on action required.'),
        ]:
            box_t = Table([[Paragraph(label.upper(), mk('al', fontName='Helvetica-Bold',
                              fontSize=7, textColor=MUTED, leading=10, letterSpacing=0.5)),
                            Paragraph(text, S['body'])]],
                          colWidths=[85, AW-90])
            box_t.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,-1),SURFACE),
                ('LINEBELOW',(0,0),(-1,-1),0.4,RULE),
                ('LINETOP',(0,0),(-1,-1),0.4,RULE),
                ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
                ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
                ('VALIGN',(0,0),(-1,-1),'TOP'),
            ]))
            story.append(box_t); story.append(Spacer(1, 3*mm))

    if mf or lf:
        if hf:  # Only page break if high flags already used a page
            story.append(PageBreak())
            story += [rb(), Spacer(1,4*mm), logo_row(addr), Spacer(1,2*mm),
                      Paragraph('Further items to review', S['pg_h']),
                      Paragraph('Items worth discussing with your conveyancer before exchange.', S['pg_d'])]
        else:
            story += [Spacer(1,4*mm),
                      Paragraph('Further items to review', S['pg_h']),
                      Paragraph('Items worth discussing with your conveyancer before exchange.', S['pg_d'])]

        for group, flags in [('Worth reviewing', mf), ('Good to know', lf)]:
            if not flags: continue
            story.append(sec_label(group)); story.append(rule())
            for f in flags:
                story.append(FlagCard(f.get('severity','low'), f.get('category',''),
                                      f.get('issue',''), f.get('recommendation',''), AW))
                story.append(Spacer(1, 2*mm))
            story.append(Spacer(1, 3*mm))

# \u2500\u2500 Questions page \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def page_questions(story, s32, con, addr, add_break=True):
    if add_break:
        story.append(PageBreak())
    story += [rb(), Spacer(1,4*mm), logo_row(addr), Spacer(1,2*mm),
              Paragraph('Questions to raise before signing', S['pg_h']),
              Paragraph('Bring this page to your conveyancer meeting and when speaking with the agent or vendor. '
                        'These are starting points only.', S['pg_d'])]

    qs  = (s32.get('conveyancer_questions') or []) + (con.get('conveyancer_questions') or [])
    neg = (s32.get('negotiation_points') or []) + (con.get('negotiation_points') or [])
    pos = s32.get('positive_findings') or []

    if qs:
        story.append(sec_label('For your conveyancer')); story.append(rule())
        for i, q in enumerate(qs, 1):
            t = Table([[Paragraph(str(i), S['q_n']), Paragraph(safe(q), S['q_b'])]],
                      colWidths=[12, AW-12])
            t.setStyle(TableStyle([
                ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),
                ('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),2),
                ('BOTTOMPADDING',(0,0),(-1,-1),2),('LINEBELOW',(0,0),(-1,-1),0.3,RULE),
            ])); story.append(t)
        story.append(Spacer(1, 5*mm))

    if neg:
        story.append(sec_label('Negotiation points to consider')); story.append(rule())
        for i, n in enumerate(neg, 1):
            t = Table([[Paragraph(str(i), S['q_n']), Paragraph(safe(n), S['q_b'])]],
                      colWidths=[12, AW-12])
            t.setStyle(TableStyle([
                ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),
                ('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),2),
                ('BOTTOMPADDING',(0,0),(-1,-1),2),('LINEBELOW',(0,0),(-1,-1),0.3,RULE),
            ])); story.append(t)
        story.append(Spacer(1, 5*mm))

    if pos:
        story.append(sec_label('Areas with nothing of concern noted')); story.append(rule())
        hw = AW/2 - 4
        for row in [pos[i:i+2] for i in range(0, len(pos), 2)]:
            cells = [Paragraph('\u2713  ' + safe(item), S['pos']) for item in row]
            while len(cells) < 2: cells.append(Paragraph('', S['body']))
            t = Table([cells], colWidths=[hw+4, hw+4])
            t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                                   ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
                                   ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2)]))
            story.append(t)

# \u2500\u2500 Disclaimer page \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def page_disclaimer(story, s32, con, prop, addr, today):
    story.append(PageBreak())
    story += [rb(), Spacer(1,4*mm), logo_row(addr), Spacer(1,2*mm),
              Paragraph('Important disclaimer', S['pg_h']), rule()]
    story.append(Paragraph(
        'This Conveyancer Pack is produced by PropertyOwl AI, an AI-assisted property document review service. '
        'It is provided solely to help buyers organise information and prepare questions for their conveyancer. '
        'It is not legal advice, financial advice, or professional conveyancing advice of any kind.<br/><br/>'
        'PropertyOwl AI is not a licensed conveyancer, solicitor, legal practitioner, or financial adviser. '
        'The information in this pack is extracted and interpreted by an artificial intelligence system from the '
        'documents provided by the user. It may contain errors, omissions, or misinterpretations. '
        'The review is only as complete as the documents uploaded.<br/><br/>'
        'Nothing in this pack should be treated as a complete or accurate statement of the legal or financial '
        'position of the property. The absence of a flag does not mean that item is legally clear or free of risk. '
        'Flags and observations are starting points for inquiry \u2014 not conclusions.<br/><br/>'
        'You must engage a qualified and licensed Victorian conveyancer or solicitor before exchanging contracts, '
        'paying any deposit, or making any financial commitment. Your conveyancer is the final authority on all '
        'matters relating to the purchase.<br/><br/>'
        'By using this pack, you acknowledge that PropertyOwl AI accepts no liability for any loss, damage, '
        'costs, or adverse outcome arising from reliance on this document.',
        S['disc'])); story.append(Spacer(1, 8*mm))

    story.append(sec_label('Document details')); story.append(rule())
    dr = 'Section 32 Vendor Statement' + (' + Contract of Sale' if con.get('sections') else '')
    story.append(kv_table([
        ('Generated by', 'PropertyOwl AI', None),
        ('Generation date', today, None),
        ('Property', addr, None),
        ('Documents reviewed', dr, None),
        ('Report type', 'S32 & Contract Review \u2014 Conveyancer Pack', None),
    ]))

# \u2500\u2500 Main \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def build(data, out):
    prop = data.get('property') or {}
    s32  = data.get('s32') or {}
    con  = data.get('contract') or {}
    try:    today = date.today().strftime('%-d %B %Y')
    except: today = date.today().strftime('%d %B %Y')

    addr = safe(prop.get('address')) + ', ' + safe(prop.get('suburb')) + \
           ((' ' + safe(prop.get('postcode'))) if prop.get('postcode') else '') + ' VIC'

    af = (s32.get('red_flags') or []) + (con.get('red_flags') or [])
    hf = [f for f in af if f.get('severity') == 'high']
    has_med_low = any(f.get('severity') in ('medium','low') for f in af)
    total_pages = 5 + len(hf) + (1 if has_med_low else 0)

    doc = SimpleDocTemplate(out, pagesize=A4,
                            leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
                            title='PropertyOwl AI \u2014 Conveyancer Pack', author='PropertyOwl AI')
    story = []
    page1(story, prop, s32, con, addr, today)
    page2(story, s32, addr)
    page3(story, s32, addr)
    page4(story, s32, con, addr)
    page5_issues(story, af, addr)
    # If no high flags, further items page may be sparse \u2014 don't add extra break before questions
    only_med_low = bool(af) and not bool(hf)
    page_questions(story, s32, con, addr, add_break=not only_med_low)
    page_disclaimer(story, s32, con, prop, addr, today)

    fn = footer_fn(addr, total_pages)
    doc.build(story, onFirstPage=fn, onLaterPages=fn)

try:
    out_path  = sys.argv[1] if len(sys.argv) > 1 else '/tmp/pack.pdf'
    json_path = sys.argv[2] if len(sys.argv) > 2 else None
    data = json.loads(open(json_path).read()) if json_path else json.load(sys.stdin)
    build(data, out_path)
    sys.stdout.write('OK\
'); sys.stdout.flush()
except Exception:
    sys.stderr.write('PYTHON_ERROR:\
' + traceback.format_exc() + '\
')
    sys.stderr.flush()
    sys.exit(1)
