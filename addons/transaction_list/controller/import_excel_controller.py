from odoo.addons.order_matching.utils import mround
from odoo import http
from odoo.http import request
import json
import pandas as pd
import io
import random
import os


class ImportExcelController(http.Controller):
    
    @http.route('/api/transaction-list/import-excel', type='http', auth='user', methods=['POST'], csrf=False)
    def import_excel_transactions(self, **kwargs):
        """Import transactions from Excel/CSV file với đầy đủ field data"""
        
        try:
            # Lấy file từ request
            file = request.httprequest.files.get('file')
            if not file:
                return request.make_response(
                    json.dumps({
                        "success": False,
                        "message": "Không có file được upload"
                    }, ensure_ascii=False),
                    headers=[("Content-Type", "application/json")]
                )
            
            # Lấy tên file và extension
            filename = file.filename or 'unknown'
            file_extension = os.path.splitext(filename)[1].lower()
            print(f"Uploaded file: {filename}, extension: {file_extension}")
            
            # Đọc file Excel/CSV
            try:
                file_content = file.read()
                
                if file_extension == '.csv':
                    # Đọc CSV với encoding UTF-8
                    df = pd.read_csv(io.BytesIO(file_content), encoding='utf-8')
                elif file_extension in ['.xlsx', '.xls']:
                    # Đọc Excel
                    df = pd.read_excel(io.BytesIO(file_content))
                else:
                    # Thử đọc như Excel trước, nếu không được thì thử CSV
                    try:
                        df = pd.read_excel(io.BytesIO(file_content))
                    except:
                        df = pd.read_csv(io.BytesIO(file_content), encoding='utf-8')
                
                print(f"File columns: {list(df.columns)}")
                print(f"File shape: {df.shape}")
                print(f"First few rows: {df.head()}")
                
                # Chuẩn hóa tên cột - loại bỏ khoảng trắng và chuyển về lowercase
                df.columns = df.columns.str.strip().str.lower()
                print(f"Normalized columns: {list(df.columns)}")
                
            except Exception as e:
                print(f"Error reading file: {str(e)}")
                return request.make_response(
                    json.dumps({
                        "success": False,
                        "message": f"Lỗi đọc file: {str(e)}"
                    }, ensure_ascii=False),
                    headers=[("Content-Type", "application/json")]
                )
            
            # Lấy danh sách fund có sẵn - không tự tạo fund mới
            funds = request.env['portfolio.fund'].sudo().search([])
            print(f"Found {len(funds)} portfolio.fund in database")
            
            if not funds:
                return request.make_response(
                    json.dumps({
                        "success": False,
                        "message": "Không có fund nào trong database. Vui lòng tạo fund trước khi import."
                    }, ensure_ascii=False),
                    headers=[("Content-Type", "application/json")]
                )
            
            # Tạo mapping fund theo ticker và name
            fund_mapping = {}
            for f in funds:
                fund_mapping[f.ticker] = f
                fund_mapping[f.name] = f
                print(f"Added fund to mapping: {f.ticker} -> {f.name}")
            
            print(f"Fund mapping keys: {list(fund_mapping.keys())}")
            
            transactions = []
            user_id = request.env.user.id
            errors = []
            
            # Tạo mapping linh hoạt cho các cột Excel
            def get_field_value(row, field_mappings, default_value=''):
                """Lấy giá trị từ row với nhiều tên cột khác nhau"""
                for mapping in field_mappings:
                    if mapping in row and pd.notna(row[mapping]):
                        return str(row[mapping]).strip() if isinstance(row[mapping], str) else row[mapping]
                return default_value
            
            def get_numeric_field_value(row, field_mappings, default_value=0):
                """Lấy giá trị số từ row với nhiều tên cột khác nhau"""
                for mapping in field_mappings:
                    if mapping in row and pd.notna(row[mapping]):
                        try:
                            return float(row[mapping])
                        except (ValueError, TypeError):
                            continue
                return default_value
            
            # Debug: In ra thông tin về DataFrame
            print(f"DataFrame info: {df.info()}")
            print(f"DataFrame dtypes: {df.dtypes}")
            
            # Xử lý từng dòng trong Excel
            print(f"Total rows to process: {len(df)}")
            for index, row in df.iterrows():
                try:
                    print(f"Processing row {index + 1}: {row.to_dict()}")
                    print(f"Row {index + 1} columns: {list(row.index)}")
                    # Ticker/Fund mapping - ưu tiên ticker từ Excel
                    ticker = get_field_value(row, [
                        'ticker', 'fund_ticker', 'fund_code', 'mã_quỹ', 'ma_quy', 'fund_symbol',
                        'ticker_fund', 'ticker fund', 'ticker_quỹ', 'ticker_quy', 'ticker fund',
                        'ticker fund', 'mã_ccq', 'ma_ccq', 'mã ccq', 'ma ccq'  # Từ file test
                    ])
                    fund_name = get_field_value(row, [
                        'fund_name', 'fund', 'tên_quỹ', 'ten_quy', 'quỹ_đầu_tư', 'quy_dau_tu'
                    ])
                    print(f"Row {index+1} - ticker: '{ticker}', fund_name: '{fund_name}'")
                    
                    # Transaction type mapping - linh hoạt với tiếng Việt và tiếng Anh
                    transaction_type_raw = get_field_value(row, [
                        'transaction_type', 'order_type', 'type', 'loại_lệnh', 'loai_lenh',
                        'loại_giao_dịch', 'loai_giao_dich', 'transaction_kind', 'loại lệnh',
                        'loại lệnh'  # Từ file test
                    ], 'buy').lower()
                    
                    # Status mapping
                    status = get_field_value(row, [
                        'status', 'trạng_thái', 'trang_thai', 'state', 'trạng thái',
                        'trạng thái'  # Từ file test
                    ], 'pending').lower()
                    
                    # Term months mapping
                    term_months = get_numeric_field_value(row, [
                        'term_months', 'kỳ_hạn', 'ky_han', 'kỳ_hạn_tháng', 'ky_han_thang',
                        'kỳ hạn', 'ky han', 'kỳ hạn (tháng)', 'ky han (thang)', 'kỳ hạn (tháng)',
                        'kỳ hạn (tháng)'  # Từ file test
                    ], 1)
                    
                    transaction_type_map = {
                        'mua': 'buy', 'buy': 'buy', 'mua_ccq': 'buy',
                        'bán': 'sell', 'sell': 'sell', 'bán_ccq': 'sell',
                        'hoán_đổi': 'exchange', 'hoan_doi': 'exchange', 'exchange': 'exchange', 'swap': 'exchange'
                    }
                    transaction_type = transaction_type_map.get(transaction_type_raw, 'buy')
                    
                    # Units mapping - linh hoạt với nhiều tên cột
                    units = get_numeric_field_value(row, [
                        'units', 'quantity', 'ccq', 'total_ccq', 'số_lượng_ccq', 'so_luong_ccq',
                        'số_lượng', 'so_luong', 'quantity_ccq', 'ccq_quantity', 'số lượng ccq',
                        'số lượng ccq'  # Từ file test
                    ])
                    
                    # Amount mapping - linh hoạt với nhiều tên cột
                    amount = get_numeric_field_value(row, [
                        'amount', 'total_amount', 'gross_amount', 'net_amount', 'giá_trị_mua', 'gia_tri_mua',
                        'giá_trị_bán', 'gia_tri_ban', 'giá_trị', 'gia_tri', 'value', 'total_value', 'giá trị lệnh',
                        'giá trị lệnh'  # Từ file test
                    ])
                    
                    # Price/NAV mapping - linh hoạt với nhiều tên cột
                    price = get_numeric_field_value(row, [
                        'price', 'nav', 'current_nav', 'unit_price', 'giá_ccq', 'gia_ccq',
                        'giá_đơn_vị', 'gia_don_vi', 'nav_price', 'unit_nav', 'giá nav',
                        'giá nav'  # Từ file test
                    ])
                    
                    # Fee mapping - đơn giản
                    fee = get_numeric_field_value(row, ['fee', 'phí', 'phi'], 0)
                    
                    # Tax mapping - đơn giản
                    tax = get_numeric_field_value(row, ['tax', 'thuế', 'thue'], 0)
                    
                    # Account number mapping - đơn giản
                    account_number = get_field_value(row, ['account_number', 'so_tk', 'số_tài_khoản'], '')
                    
                    # Investor name mapping - đơn giản
                    investor_name = get_field_value(row, ['investor_name', 'tên_khách_hàng', 'nhà đầu tư'], '')
                    
                    # Trade code mapping - đơn giản
                    trade_code = get_field_value(row, ['trade_code', 'mã_lệnh', 'ma_lenh'], '')
                    
                    # Kỳ hạn mapping - đơn giản
                    term_months = get_numeric_field_value(row, [
                        'term_months', 'kỳ_hạn', 'ky_han', 'kỳ hạn (tháng)', 'kỳ hạn (tháng)'
                    ], 1)
                    
                    # Lãi suất mapping - đơn giản
                    interest_rate = get_numeric_field_value(row, [
                        'interest_rate', 'lãi_suất', 'lai_suat', 'lãi suất'
                    ], 0)
                    
                    # Đơn giản hóa - không tính toán phức tạp
                    
                    # Validate required fields
                    if not ticker and not fund_name:
                        errors.append(f"Dòng {index+1}: Thiếu ticker hoặc fund_name")
                        continue
                    
                    if units <= 0:
                        errors.append(f"Dòng {index+1}: Số lượng phải > 0")
                        continue
                    
                    # Tìm fund theo ticker hoặc name
                    print(f"Looking for fund with ticker='{ticker}' or name='{fund_name}'")
                    print(f"Available funds: {list(fund_mapping.keys())}")
                    
                    # Ưu tiên tìm theo ticker
                    fund = None
                    if ticker:
                        fund = fund_mapping.get(ticker)
                        if fund:
                            print(f"Found fund by ticker: {fund.name} (ticker: {fund.ticker})")
                        else:
                            print(f"Fund not found by ticker: '{ticker}'")
                    
                    # Nếu không tìm thấy theo ticker, tìm theo name
                    if not fund and fund_name:
                        fund = fund_mapping.get(fund_name)
                        if fund:
                            print(f"Found fund by name: {fund.name} (name: {fund.name})")
                        else:
                            print(f"Fund not found by name: '{fund_name}'")
                    
                    if not fund:
                        errors.append(f"Dòng {index+1}: Không tìm thấy fund với ticker='{ticker}' hoặc name='{fund_name}'")
                        print(f"Fund not found for row {index+1}")
                        continue
                    
                    print(f"Using fund: {fund.name} (ID: {fund.id}, ticker: {fund.ticker})")
                    
                    # Làm tròn số lượng CCQ về bội số của 50
                    if units > 0:
                        units = mround(units, 50)
                        if units < 50:
                            units = 50
                    
                    # Xử lý giá mua cho lệnh mua - chỉ lấy data từ Excel
                    if transaction_type == 'buy':
                        # Lấy giá từ Excel
                        if price > 0:
                            current_nav = price
                        else:
                            # Nếu không có price từ Excel, lấy từ fund hiện tại
                            current_nav = fund.current_nav or 10000
                        
                        # Tính toán giá mua theo logic: nếu thấp hơn giá tính toán thì lấy giá tính toán
                        # Ví dụ: import 20,000 CCQ, nếu thấp hơn giá tính toán 21,000 thì lấy 21,000
                        calculated_price_per_unit = amount / units if units > 0 else 0
                        
                        if calculated_price_per_unit > 0 and calculated_price_per_unit < current_nav:
                            # Nếu giá tính toán thấp hơn NAV, sử dụng NAV (giá cao hơn)
                            final_price = current_nav
                            final_amount = units * final_price
                            errors.append(f"Dòng {index+1}: Giá tính toán ({calculated_price_per_unit:,.0f}) thấp hơn NAV ({current_nav:,.0f}), sử dụng NAV")
                        else:
                            # Nếu giá tính toán cao hơn hoặc bằng NAV, chấp nhận giá tính toán
                            final_price = calculated_price_per_unit
                            final_amount = amount
                        
                        # Cập nhật amount với giá cuối cùng
                        amount = final_amount
                        current_nav = final_price
                        
                    else:
                        # Lệnh bán/hoán đổi: sử dụng NAV hiện tại của fund
                        current_nav = fund.current_nav or 10000
                    amount = units * current_nav
                    
                    # Tạo transaction với đầy đủ field data bao gồm kỳ hạn, lãi suất và tính toán NAV
                    # CHỈ IMPORT LỆNH, KHÔNG THỰC HIỆN KHỚP LỆNH TỰ ĐỘNG
                    print(f"Creating transaction for row {index+1} with data:")
                    print(f"  - fund_id: {fund.id}")
                    print(f"  - transaction_type: {transaction_type}")
                    print(f"  - units: {units}")
                    print(f"  - amount: {amount}")
                    print(f"  - current_nav: {current_nav}")
                    print(f"  - status: {status}")
                    print(f"  - term_months: {term_months}")
                    print(f"  - interest_rate: {interest_rate}")
                    
                    print(f"Creating transaction with fund_id: {fund.id}")
                    try:
                        # Tạo transaction với các field cơ bản trước
                        transaction_data = {
                            'user_id': user_id,
                            'fund_id': fund.id,
                            'transaction_type': transaction_type,
                            'units': units,
                            'price': current_nav,
                            'amount': amount,
                            'current_nav': current_nav,
                            'matched_units': 0,
                            'status': status,  # Sử dụng status từ Excel
                            'description': f"Import từ Excel - {trade_code}" if trade_code else "Import từ Excel"
                        }
                        
                        # Thêm các field optional nếu có - chỉ thêm các field cơ bản
                        if account_number:
                            transaction_data['account_number'] = account_number
                        if investor_name:
                            transaction_data['investor_name'] = investor_name
                        if trade_code:
                            transaction_data['trade_code'] = trade_code
                        
                        transaction = request.env['portfolio.transaction'].sudo().create(transaction_data)
                        print(f"Successfully created transaction {transaction.id}")
                    except Exception as create_error:
                        print(f"Error creating transaction: {str(create_error)}")
                        errors.append(f"Dòng {index+1}: Lỗi tạo transaction - {str(create_error)}")
                        continue
                    
                    # KHÔNG THỰC HIỆN KHỚP LỆNH TỰ ĐỘNG
                    # Các lệnh sẽ được khớp thủ công thông qua giao diện khớp lệnh
                    
                    transactions.append({
                        "id": transaction.id,
                        "fund_name": fund.name,
                        "fund_ticker": fund.ticker,
                        "transaction_type": transaction_type,
                        "units": units,
                        "price": current_nav,
                        "amount": amount,
                        "status": status,
                        "created_at": transaction.create_date.strftime('%Y-%m-%d %H:%M:%S'),
                        "term_months": term_months,
                        "interest_rate": interest_rate
                    })
                    
                except Exception as e:
                    errors.append(f"Dòng {index+1}: Lỗi xử lý - {str(e)}")
                    continue
            
            # Debug: In ra thông tin về transactions đã tạo
            print(f"Total transactions created: {len(transactions)}")
            print(f"Total errors: {len(errors)}")
            if errors:
                print(f"Errors: {errors}")
            
            # Debug: In ra thông tin kết quả
            print(f"Import completed. Created {len(transactions)} transactions, {len(errors)} errors")
            print(f"Transactions created: {[t['id'] for t in transactions]}")
            
            # Tạo response với thông tin chi tiết
            response_data = {
                    "success": True,
                "message": f"Đã import {len(transactions)} lệnh từ Excel (trạng thái pending, chưa khớp lệnh)",
                    "transactions": transactions,
                    "funds_used": [{"id": f.id, "name": f.name, "ticker": f.ticker, "current_nav": f.current_nav} for f in funds],
                "import_summary": {
                    "total_rows": len(df),
                    "successful_imports": len(transactions),
                    "errors": len(errors),
                    "error_details": errors
                },
                "supported_columns": {
                    "ticker": ["ticker", "fund_ticker", "fund_code", "mã_quỹ", "ma_quy", "fund_symbol", "ticker_fund", "ticker fund", "ticker_quỹ", "ticker_quy"],
                    "fund_name": ["fund_name", "fund", "tên_quỹ", "ten_quy", "quỹ_đầu_tư", "quy_dau_tu"],
                    "transaction_type": ["transaction_type", "order_type", "type", "loại_lệnh", "loai_lenh"],
                    "units": ["units", "quantity", "ccq", "total_ccq", "số_lượng_ccq", "so_luong_ccq"],
                    "amount": ["amount", "total_amount", "gross_amount", "net_amount", "giá_trị_mua", "gia_tri_mua"],
                    "price": ["price", "nav", "current_nav", "unit_price", "giá_ccq", "gia_ccq"],
                    "status": ["status", "trạng_thái", "trang_thai", "state"],
                    "term_months": ["term_months", "kỳ_hạn", "ky_han", "kỳ_hạn_tháng", "ky_han_thang", "kỳ hạn", "ky han", "kỳ hạn (tháng)", "ky han (thang)"],
                    "interest_rate": ["interest_rate", "lãi_suất", "lai_suat", "lãi_suất_năm", "lai_suat_nam"],
                    "maturity_date": ["maturity_date", "ngày_đáo_hạn", "ngay_dao_han", "expiry_date"],
                    "number_of_days": ["number_of_days", "số_ngày", "so_ngay", "days", "duration_days"],
                    "net_interest_rate": ["net_interest_rate", "lãi_suất_net", "lai_suat_net", "net_rate"],
                    "interest_rate_difference": ["interest_rate_difference", "chênh_lệch_lãi_suất", "chenh_lech_lai_suat"],
                    "converted_interest_rate": ["converted_interest_rate", "ls_quy_đổi", "ls_quy_doi", "lãi_suất_quy_đổi"],
                    "order_value": ["order_value", "giá_trị_lệnh", "gia_tri_lenh", "trade_value"],
                    "trade_value": ["trade_value", "giá_trị_mua_bán", "gia_tri_mua_ban", "buy_sell_value"],
                    "price1": ["price1", "giá_mua_bán_1", "gia_mua_ban_1", "unit_price_1"],
                    "price2": ["price2", "giá_mua_bán_2", "gia_mua_ban_2", "unit_price_2"]
                },
                "note": "CHỈ IMPORT LỆNH - KHÔNG TỰ ĐỘNG KHỚP LỆNH. Mapping linh hoạt với nhiều tên cột tiếng Việt và tiếng Anh. Logic giá mua: nếu giá tính toán thấp hơn NAV thì sử dụng NAV. Tự động tính toán LS quy đổi, giá bán 1, giá bán 2 từ nav_management nếu không có trong Excel. Các lệnh sẽ ở trạng thái pending và cần khớp thủ công."
            }
            
            # Thêm cảnh báo về giá mua nếu có
            if errors:
                response_data["warnings"] = errors
                if len(transactions) == 0:
                    response_data["message"] = f"Import thất bại! Không tạo được lệnh nào. Có {len(errors)} lỗi."
                else:
                    response_data["message"] += f" (Có {len(errors)} cảnh báo)"
            
            # Nếu không có transaction nào được tạo, đánh dấu là thất bại
            if len(transactions) == 0:
                response_data["success"] = False
                if not errors:
                    response_data["message"] = "Import thất bại! Không tạo được lệnh nào. Vui lòng kiểm tra lại file Excel và đảm bảo ticker khớp với fund trong database."
            
            return request.make_response(
                json.dumps(response_data, ensure_ascii=False),
                headers=[("Content-Type", "application/json")]
            )
            
        except Exception as e:
            return request.make_response(
                json.dumps({"success": False, "message": str(e)}, ensure_ascii=False),
                headers=[("Content-Type", "application/json")],
                status=500
            )
