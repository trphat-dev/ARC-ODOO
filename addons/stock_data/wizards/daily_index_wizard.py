from odoo import fields, _
from odoo.exceptions import UserError
from datetime import datetime
import logging
from ssi_fc_data import model


_logger = logging.getLogger(__name__)


def fetch_daily_index(wizard, client, sdk_config):
    if not wizard.symbol:
        index_model = wizard.env['ssi.index.list']
        daily_index_model = wizard.env['ssi.daily.index']

        all_ids = index_model.search([], order='id').ids
        if not all_ids:
            raise UserError(_("No index records found. Please fetch index list first."))

        ICP = wizard.env['ir.config_parameter'].sudo()
        cursor_key = 'ssi.daily_index.cursor'
        batch_key = wizard._BATCH_DAILY_INDEX_KEY
        try:
            cursor = int(ICP.get_param(cursor_key, default='0') or '0')
        except Exception:
            cursor = 0
        try:
            default_batch = wizard.page_size or 50
            batch_size = int(ICP.get_param(batch_key, default=str(default_batch)) or str(default_batch))
        except Exception:
            batch_size = wizard.page_size or 50

        start = max(cursor, 0)
        end = min(start + batch_size, len(all_ids))
        if start >= len(all_ids):
            start = 0
            end = min(batch_size, len(all_ids))
        batch_ids = all_ids[start:end]
        indices = index_model.browse(batch_ids)

        success_count = 0
        error_count = 0

        for idx in indices:
            try:
                current_page = 1
                while True:
                    req = model.daily_index(
                        indexCode=idx.index_code,
                        fromDate=wizard.from_date.strftime('%d/%m/%Y'),
                        toDate=wizard.to_date.strftime('%d/%m/%Y'),
                        pageIndex=current_page,
                        pageSize=wizard.page_size or 100,
                        ascending=True
                    )

                    response = client.daily_index(sdk_config, req)

                    if response.get('status') == 'Success' and response.get('data'):
                        items = response['data'] if isinstance(response['data'], list) else []
                        if not items:
                            break
                        for item in items:
                            # Support both old (Date: YYYY-MM-DD) and new (TradingDate: dd/MM/YYYY)
                            date_str = item.get('TradingDate') or item.get('Date', '')
                            if date_str:
                                try:
                                    try:
                                        date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
                                    except Exception:
                                        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                                except Exception:
                                    date_obj = wizard.from_date
                            else:
                                date_obj = wizard.from_date

                            existing = daily_index_model.search([
                                ('index_code', '=', idx.index_code),
                                ('date', '=', date_obj)
                            ], limit=1)

                            values = {
                                'index_code': item.get('IndexId', idx.index_code),
                                'index_name': item.get('IndexName', idx.index_code),
                                'exchange': item.get('Exchange', ''),
                                'date': date_obj,
                                'index_value': float(item.get('IndexValue', 0.0) or 0.0),
                                'change': float(item.get('Change', 0.0) or 0.0),
                                'ratio_change': float(item.get('RatioChange', 0.0) or 0.0),
                                'total_trade': int(item.get('TotalTrade', 0) or 0),
                                'total_match_vol': float(item.get('TotalMatchVol', 0.0) or 0.0),
                                'total_match_val': float(item.get('TotalMatchVal', 0.0) or 0.0),
                                'total_deal_vol': float(item.get('TotalDealVol', 0.0) or 0.0),
                                'total_deal_val': float(item.get('TotalDealVal', 0.0) or 0.0),
                                'total_vol': float(item.get('TotalVol', 0.0) or 0.0),
                                'total_val': float(item.get('TotalVal', 0.0) or 0.0),
                                'advances': int(item.get('Advances', 0) or 0),
                                'no_changes': int(item.get('NoChanges', 0) or 0),
                                'declines': int(item.get('Declines', 0) or 0),
                                'ceilings': int(item.get('Ceilings', 0) or 0),
                                'floors': int(item.get('Floors', 0) or 0),
                                'trading_session': item.get('TradingSession', ''),
                                'time': item.get('Time', ''),
                                # compatibility fields
                                'close_value': float(item.get('IndexValue', 0.0) or 0.0),
                                'volume': float(item.get('TotalVol', 0.0) or 0.0),
                                'total_value': float(item.get('TotalVal', 0.0) or 0.0),
                                'change_percent': float(item.get('RatioChange', 0.0) or 0.0),
                            }

                            if existing:
                                existing.write(values)
                            else:
                                daily_index_model.create(values)
                    else:
                        break
                    current_page += 1
                    try:
                        wizard.env.cr.commit()
                    except Exception:
                        pass
                success_count += 1
            except Exception as e:
                _logger.warning("Skip daily index for %s due to %s", idx.index_code, str(e))
                error_count += 1

        new_cursor = end if end < len(all_ids) else 0
        try:
            ICP.set_param(cursor_key, str(new_cursor))
        except Exception:
            _logger.debug("Failed to update daily index cursor", exc_info=True)

        remaining = len(all_ids) - new_cursor if new_cursor else 0
        wizard.result_message = f"""
            <p><strong>✅ Fetched daily index for {len(indices)} indices</strong></p>
            <p>Success: {success_count}</p>
            <p>Errors: {error_count}</p>
            {"<p>💡 <strong>" + str(remaining) + "</strong> indices remaining in next batches.</p>" if remaining > 0 else "<p>🎉 <strong>All indices processed!</strong></p>"}
            """
        wizard.last_count = success_count
        return

    index_model = wizard.env['ssi.index.list']
    index_record = index_model.search([('index_code', '=', wizard.symbol)], limit=1)

    if not index_record:
        raise UserError(_("Index with code %s not found. Please fetch index list first.") % wizard.symbol)

    req = model.daily_index(
        indexCode=wizard.symbol,
        fromDate=wizard.from_date.strftime('%d/%m/%Y'),
        toDate=wizard.to_date.strftime('%d/%m/%Y'),
        pageIndex=wizard.page_index,
        pageSize=wizard.page_size,
        ascending=True
    )

    response = client.daily_index(sdk_config, req)
    _logger.info("Daily index response: %s", response)

    if response.get('status') == 'Success' and response.get('data'):
        daily_index_model = wizard.env['ssi.daily.index']
        count = 0
        updated = 0
        created = 0

        items = response['data'] if isinstance(response['data'], list) else []

        for item in items:
            date_str = item.get('TradingDate') or item.get('Date', '')
            if date_str:
                try:
                    try:
                        date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
                    except Exception:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                except Exception:
                    date_obj = wizard.from_date
            else:
                date_obj = wizard.from_date

            existing = daily_index_model.search([
                ('index_code', '=', wizard.symbol),
                ('date', '=', date_obj)
            ], limit=1)

            values = {
                'index_code': item.get('IndexId', wizard.symbol),
                'index_name': item.get('IndexName', wizard.symbol),
                'exchange': item.get('Exchange', ''),
                'date': date_obj,
                'index_value': float(item.get('IndexValue', 0.0) or 0.0),
                'change': float(item.get('Change', 0.0) or 0.0),
                'ratio_change': float(item.get('RatioChange', 0.0) or 0.0),
                'total_trade': int(item.get('TotalTrade', 0) or 0),
                'total_match_vol': float(item.get('TotalMatchVol', 0.0) or 0.0),
                'total_match_val': float(item.get('TotalMatchVal', 0.0) or 0.0),
                'total_deal_vol': float(item.get('TotalDealVol', 0.0) or 0.0),
                'total_deal_val': float(item.get('TotalDealVal', 0.0) or 0.0),
                'total_vol': float(item.get('TotalVol', 0.0) or 0.0),
                'total_val': float(item.get('TotalVal', 0.0) or 0.0),
                'advances': int(item.get('Advances', 0) or 0),
                'no_changes': int(item.get('NoChanges', 0) or 0),
                'declines': int(item.get('Declines', 0) or 0),
                'ceilings': int(item.get('Ceilings', 0) or 0),
                'floors': int(item.get('Floors', 0) or 0),
                'trading_session': item.get('TradingSession', ''),
                'time': item.get('Time', ''),
                # compatibility
                'close_value': float(item.get('IndexValue', 0.0) or 0.0),
                'volume': float(item.get('TotalVol', 0.0) or 0.0),
                'total_value': float(item.get('TotalVal', 0.0) or 0.0),
                'change_percent': float(item.get('RatioChange', 0.0) or 0.0),
            }

            if existing:
                existing.write(values)
                updated += 1
            else:
                daily_index_model.create(values)
                created += 1
            count += 1

        wizard.result_message = f"<p>Fetched {count} daily index records for {wizard.symbol} (Created: {created}, Updated: {updated})</p>"
        wizard.last_count = count
    else:
        raise UserError(_("Failed to fetch daily index data. Status: %s, Data: %s") % (
            response.get('status', 'Unknown'),
            'Has data' if response.get('data') else 'No data'
        ))


