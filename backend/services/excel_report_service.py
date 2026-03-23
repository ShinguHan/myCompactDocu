"""월말 결산보고서 Excel 생성 서비스 — 원본 파일 기반"""
import os
import shutil
import zipfile
from openpyxl import load_workbook

import schemas

# 미리 비워둔 템플릿 사용, 없으면 원본 참조 파일로 폴백
_TEMPLATE = os.path.join(os.path.dirname(__file__), '..', 'templates', 'report_template.xlsx')
_FALLBACK  = os.path.join(os.path.dirname(__file__), '..', '..', 'ref',
                           '(찐) 26년_3월_부산물 매각 및 폐기물 처리현황.xlsx')
SOURCE_PATH = _TEMPLATE if os.path.exists(_TEMPLATE) else _FALLBACK
OUTPUT_DIR  = os.path.join(os.path.dirname(__file__), '..', '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── 열 인덱스 (1-based) ───────────────────────────────────────────────────────
COL_COMPANY = 2    # B  업체명
COL_ITEM    = 6    # F  품명
COL_UNIT    = 10   # J  단가
COL_QTY     = 12   # L  당월 수량
COL_AMT     = 14   # N  당월 금액
COL_PREV    = 17   # Q  전월 금액
COL_NOTE    = 20   # T  비고

# 요약 섹션 열 (템플릿: 전월=D-H, 당월=I-M 순서)
COL_S_PQTY  = 4    # D  전월 수량
COL_S_PAMT  = 6    # F  전월 금액
COL_S_QTY   = 9    # I  당월 수량
COL_S_AMT   = 11   # K  당월 금액
COL_S_AVG   = 17   # Q  2026 월평균 금액
COL_S_CUM   = 20   # T  누계 금액

# 섹션 행 범위
BY_DATA_START  = 16   # 부산물 첫 데이터 행
BY_TOTAL_ROW   = 37   # 부산물 합계 행
WS_DATA_START  = 42   # 폐기물 첫 데이터 행
WS_TOTAL_ROW   = 56   # 폐기물 합계 행

# 요약 행
ROW_BY = 8    # 매각(부산물)
ROW_WS = 9    # 처리(폐기물)
ROW_NE = 10   # 이익

# 초기화 대상 열 목록
CLEAR_SUMMARY_COLS = [4, 6, 9, 11, 14, 17, 20]   # D F I K N Q T
CLEAR_DETAIL_COLS  = [12, 14, 17, 20]              # L N Q T


def safe_write(ws, row, col, value):
    """병합셀 상단 좌측 셀에만 쓰기 (MergedCell 예외 무시)"""
    try:
        ws.cell(row, col).value = value
    except AttributeError:
        pass


def _clear_section(ws, data_start: int, total_row: int):
    """섹션 데이터 셀 초기화 (업체명·품명·단가는 유지)"""
    for r in range(data_start, total_row + 1):
        for c in CLEAR_DETAIL_COLS:
            safe_write(ws, r, c, None)


def _normalize(name) -> str:
    """공백·개행·언더스코어·괄호·슬래시 등을 제거해 비교용 키 생성
    업체명 슬래시 표기(예: 세진/세진유화) → 첫 번째 이름만 사용
    """
    if not name:
        return ''
    import re
    s = str(name)
    s = s.split('/')[0]                # 슬래시 뒤 제거 (업체 별칭 처리)
    s = re.sub(r'\s+', '', s)          # 모든 공백·개행 제거
    s = s.replace('\xa0', '').replace('\u00a0', '')
    s = s.replace('_', '')             # 언더스코어 제거
    s = s.replace('(', '').replace(')', '')  # 괄호 제거
    return s.lower()


def _scan_section(ws, data_start: int, total_row: int):
    """
    섹션 스캔:
      mapping  : { (company_norm, item_norm) : row_num }
      subtotals: { company_norm : row_num }
    """
    mapping   = {}
    subtotals = {}
    current_cn = None

    for r in range(data_start, total_row + 1):
        b_val = ws.cell(r, COL_COMPANY).value
        f_val = ws.cell(r, COL_ITEM).value
        f_str = _normalize(f_val)

        # 업체명 갱신 (병합으로 None인 경우 이전 값 유지)
        if b_val is not None:
            b_str = _normalize(b_val)
            if b_str and b_str not in ('합계', '소계'):
                current_cn = b_str

        if r == total_row:
            continue  # 합계 행 스킵

        if '소계' in f_str:
            if current_cn:
                subtotals[current_cn] = r
        elif f_str:
            mapping[(current_cn, f_str)] = r

    return mapping, subtotals


def _fill_section(ws, rows, data_start: int, total_row: int):
    """rows(List[ReportRow])를 템플릿 행에 매핑해 값 채우기"""
    mapping, subtotals = _scan_section(ws, data_start, total_row)

    company_acc: dict = {}  # company_norm → {qty, amt, prev}

    for r in rows:
        cn   = _normalize(r.company_name)
        itm  = _normalize(r.item_name)
        key  = (cn, itm)

        if key in mapping:
            row_num = mapping[key]
            safe_write(ws, row_num, COL_QTY,  r.current_quantity or None)
            safe_write(ws, row_num, COL_AMT,  r.current_amount)
            safe_write(ws, row_num, COL_PREV, r.prev_amount)
            if r.note:
                safe_write(ws, row_num, COL_NOTE, r.note)

        if cn not in company_acc:
            company_acc[cn] = {'qty': 0, 'amt': 0, 'prev': 0}
        company_acc[cn]['qty']  += r.current_quantity or 0
        company_acc[cn]['amt']  += r.current_amount
        company_acc[cn]['prev'] += r.prev_amount

    # 소계 행 업데이트
    for cn, st_row in subtotals.items():
        if cn in company_acc:
            t = company_acc[cn]
            safe_write(ws, st_row, COL_QTY,  t['qty'] or None)
            safe_write(ws, st_row, COL_AMT,  t['amt'])
            safe_write(ws, st_row, COL_PREV, t['prev'])

    # 합계 행 업데이트
    safe_write(ws, total_row, COL_QTY,  sum(r.current_quantity or 0 for r in rows) or None)
    safe_write(ws, total_row, COL_AMT,  sum(r.current_amount for r in rows))
    safe_write(ws, total_row, COL_PREV, sum(r.prev_amount for r in rows))


def _update_chart_sheet(wb, year: int, month: int, summary):
    """그래프 시트의 해당 연월 컬럼에 매각/처리/이익 데이터 업데이트"""
    if len(wb.sheetnames) < 2:
        return
    cws = wb.worksheets[1]  # 그래프 시트 (인덱스 1)

    # 레이블 형식: "'26.3월" 또는 "26.3월"
    yy = year % 100
    targets = {
        f"'{yy:02d}.{month}월",
        f"{yy:02d}.{month}월",
        f"'{yy}.{month}월",
        f"{yy}.{month}월",
    }

    col = None
    for cell in cws[16]:
        if cell.value is not None:
            cv = str(cell.value).strip()
            if cv in targets or cv.lstrip("'") in {t.lstrip("'") for t in targets}:
                col = cell.column
                break

    if not col:
        return

    by_qty = sum(r.current_quantity or 0 for r in summary.byproducts)
    ws_qty = sum(r.current_quantity or 0 for r in summary.wastes)

    try:
        cws.cell(17, col).value = by_qty
        cws.cell(18, col).value = summary.total_current_byproduct
        cws.cell(19, col).value = ws_qty
        cws.cell(20, col).value = summary.total_current_waste
        cws.cell(21, col).value = (summary.total_current_byproduct
                                   + summary.total_current_waste)
    except AttributeError:
        pass


def _restore_chart_xml(source_path: str, output_path: str):
    """openpyxl 재직렬화로 손상된 차트/드로잉 XML을 원본 템플릿에서 복원"""
    _CHART_PREFIXES = ('xl/charts/', 'xl/drawings/', 'xl/media/')

    to_restore = {}
    with zipfile.ZipFile(source_path, 'r') as src:
        for name in src.namelist():
            if any(name.startswith(p) for p in _CHART_PREFIXES):
                to_restore[name] = src.read(name)

    if not to_restore:
        return

    all_files = {}
    with zipfile.ZipFile(output_path, 'r') as out:
        for name in out.namelist():
            all_files[name] = out.read(name)

    all_files.update(to_restore)  # 차트 파일만 원본으로 교체

    tmp = output_path + '._tmp'
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as new_zip:
        for name, data in all_files.items():
            new_zip.writestr(name, data)
    os.replace(tmp, output_path)


def generate_monthly_report(summary: schemas.MonthlySummary,
                             trend_data=None) -> str:
    year, month = summary.year, summary.month
    output_path = os.path.join(OUTPUT_DIR,
                               f'월말보고서_{year}년{month:02d}월.xlsx')

    # ── 원본 파일 복사 ────────────────────────────────────────────────────────
    shutil.copy(SOURCE_PATH, output_path)
    wb = load_workbook(output_path, keep_links=False)
    ws = wb.worksheets[0]

    # ── 1. 데이터 셀 초기화 ───────────────────────────────────────────────────
    # 요약 (rows 8-10)
    for r in range(ROW_BY, ROW_NE + 1):
        for c in CLEAR_SUMMARY_COLS:
            safe_write(ws, r, c, None)

    # 부산물 세부 + 합계
    _clear_section(ws, BY_DATA_START, BY_TOTAL_ROW)
    # 폐기물 세부 + 합계
    _clear_section(ws, WS_DATA_START, WS_TOTAL_ROW)

    # ── 2. 제목 (연도·월) ─────────────────────────────────────────────────────
    safe_write(ws, 2, 2, year)
    safe_write(ws, 2, 7, month)

    # ── 3. 요약 섹션 ─────────────────────────────────────────────────────────
    by_curr_qty = sum(r.current_quantity or 0 for r in summary.byproducts)
    ws_curr_qty = sum(r.current_quantity or 0 for r in summary.wastes)

    # 매각 (부산물)
    safe_write(ws, ROW_BY, COL_S_PQTY, summary.total_prev_byproduct_qty or None)
    safe_write(ws, ROW_BY, COL_S_PAMT, summary.total_prev_byproduct)
    safe_write(ws, ROW_BY, COL_S_QTY,  by_curr_qty or None)
    safe_write(ws, ROW_BY, COL_S_AMT,  summary.total_current_byproduct)
    safe_write(ws, ROW_BY, COL_S_AVG,  round(summary.ytd_avg_byproduct) or None)
    safe_write(ws, ROW_BY, COL_S_CUM,  summary.ytd_cum_byproduct or None)

    # 처리 (폐기물)
    safe_write(ws, ROW_WS, COL_S_PQTY, summary.total_prev_waste_qty or None)
    safe_write(ws, ROW_WS, COL_S_PAMT, summary.total_prev_waste)
    safe_write(ws, ROW_WS, COL_S_QTY,  ws_curr_qty or None)
    safe_write(ws, ROW_WS, COL_S_AMT,  summary.total_current_waste)
    safe_write(ws, ROW_WS, COL_S_AVG,  round(summary.ytd_avg_waste) or None)
    safe_write(ws, ROW_WS, COL_S_CUM,  summary.ytd_cum_waste or None)

    # 이익
    net_curr = summary.total_current_byproduct + summary.total_current_waste
    net_prev = summary.total_prev_byproduct    + summary.total_prev_waste
    net_avg  = summary.ytd_avg_byproduct       + summary.ytd_avg_waste
    net_cum  = summary.ytd_cum_byproduct       + summary.ytd_cum_waste
    safe_write(ws, ROW_NE, COL_S_PAMT, net_prev)
    safe_write(ws, ROW_NE, COL_S_AMT,  net_curr)
    safe_write(ws, ROW_NE, COL_S_AVG,  round(net_avg) or None)
    safe_write(ws, ROW_NE, COL_S_CUM,  net_cum or None)

    # ── 4. 부산물 세부현황 ────────────────────────────────────────────────────
    _fill_section(ws, summary.byproducts, BY_DATA_START, BY_TOTAL_ROW)

    # ── 5. 폐기물 세부현황 ────────────────────────────────────────────────────
    _fill_section(ws, summary.wastes, WS_DATA_START, WS_TOTAL_ROW)

    # ── 6. 차트 시트 업데이트 ─────────────────────────────────────────────────
    _update_chart_sheet(wb, year, month, summary)

    wb.save(output_path)

    # ── 7. 차트 XML 복원 (openpyxl 재직렬화 손상 방지) ───────────────────────
    _restore_chart_xml(SOURCE_PATH, output_path)

    return output_path
