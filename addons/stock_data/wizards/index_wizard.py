import logging
from odoo import _
from odoo.exceptions import UserError
from ssi_fc_data import model


_logger = logging.getLogger(__name__)


def fetch_index_all(wizard, client, sdk_config):
    fetch_index_list(wizard, client, sdk_config)
    fetch_index_components_all(wizard, client, sdk_config)


def fetch_index_list(wizard, client, sdk_config):
    index_model = wizard.env['ssi.index.list']
    total_count = 0
    total_created = 0
    total_updated = 0

    # Map market to exchange: API expects lowercase
    market_to_exchange = {
        'ALL': ['hose', 'hnx', 'upcom'],
        'HOSE': ['hose'],
        'HNX': ['hnx'],
        'UPCOM': ['upcom']
    }
    exchanges_to_fetch = market_to_exchange.get(wizard.market, ['hose'])

    fetched_any = False
    errors_by_exchange = {}

    for exchange in exchanges_to_fetch:
        exchange_total = 0
        current_page = 1
        _logger.info("Starting to fetch index list for exchange: %s", exchange)
        
        while True:
            try:
                # Thử lần 1 với exchange dạng lower
                req = model.index_list(
                    pageIndex=current_page,
                    pageSize=wizard.page_size or 100,
                    exchange=exchange
                )
                response = client.index_list(sdk_config, req)
                _logger.info("Index list response for %s page %s: status=%s, has_data=%s", 
                           exchange, current_page, response.get('status'), bool(response.get('data')))

                # Nếu không có data, thử lại với exchange dạng UPPER
                if not (response.get('status') == 'Success' and response.get('data')):
                    alt_exchange = exchange.upper()
                    _logger.info("Retry index list for %s (upper=%s) page %s", exchange, alt_exchange, current_page)
                    req = model.index_list(
                        pageIndex=current_page,
                        pageSize=wizard.page_size or 100,
                        exchange=alt_exchange
                    )
                    response = client.index_list(sdk_config, req)
                    _logger.info("Retry response for %s page %s: status=%s, has_data=%s", 
                               alt_exchange, current_page, response.get('status'), bool(response.get('data')))

                if response.get('status') == 'Success' and response.get('data'):
                    items = response['data'].get('items', []) if isinstance(response['data'], dict) else response['data']
                    if not items:
                        _logger.info("No more items for exchange %s at page %s - stopping", exchange, current_page)
                        break
                    
                    _logger.info("Processing %d items from page %d for exchange %s", len(items), current_page, exchange)
                    
                    for item in items:
                        # New payload fields: IndexCode, IndexName, Exchange
                        index_code = item.get('IndexCode') or item.get('indexCode', '')
                        if not index_code:
                            continue

                        existing = index_model.search([('index_code', '=', index_code)], limit=1)
                        values = {
                            'index_code': index_code,
                            'exchange': (item.get('Exchange', exchange) or exchange).strip().lower(),
                            'index_name_vn': item.get('IndexName', '') or item.get('indexNameVN', ''),
                            'index_name_en': item.get('IndexName', '') or item.get('indexNameEN', ''),
                            'index_type': item.get('indexType', ''),
                            'base_value': item.get('baseValue', 0.0),
                        }

                        if existing:
                            existing.write(values)
                            total_updated += 1
                        else:
                            index_model.create(values)
                            total_created += 1
                        total_count += 1
                        exchange_total += 1
                    
                    fetched_any = True
                    current_page += 1
                    try:
                        wizard.env.cr.commit()
                    except Exception:
                        pass
                else:
                    error_msg = response.get('message', 'Unknown error')
                    _logger.warning("Failed to fetch index list for %s page %s: %s", 
                                  exchange, current_page, error_msg)
                    if exchange not in errors_by_exchange:
                        errors_by_exchange[exchange] = []
                    errors_by_exchange[exchange].append(f"Page {current_page}: {error_msg}")
                    
                    # Continue to next exchange instead of breaking completely
                    break
            except Exception as e:
                error_msg = str(e)
                _logger.error("Exception fetching index list for %s page %s: %s", 
                            exchange, current_page, error_msg, exc_info=True)
                if exchange not in errors_by_exchange:
                    errors_by_exchange[exchange] = []
                errors_by_exchange[exchange].append(f"Page {current_page}: {error_msg}")
                break
        
        _logger.info("Completed fetching %d index records for exchange %s", exchange_total, exchange)

    if not fetched_any:
        error_details = "\n".join([f"{ex}: {', '.join(errs)}" for ex, errs in errors_by_exchange.items()])
        _logger.error("Failed to fetch index list from any exchange. Errors:\n%s", error_details)
        raise UserError(_("Failed to fetch index list from any exchange. Please check logs for details."))

    exchange_text = "all exchanges" if wizard.market == 'ALL' else f"exchange {wizard.market}"
    wizard.result_message = f"<p>Fetched {total_count} index records from {exchange_text} (Created: {total_created}, Updated: {total_updated})</p>"
    wizard.last_count = total_count


def fetch_index_components_all(wizard, client, sdk_config):
    index_model = wizard.env['ssi.index.list']
    indices = index_model.search([])

    total_components = 0
    error_count = 0

    component_model = wizard.env['ssi.index.components']
    securities_model = wizard.env['ssi.securities']

    for index_record in indices:
        try:
            current_page = 1
            while True:
                req = model.index_components(
                    indexCode=index_record.index_code,
                    pageIndex=current_page,
                    pageSize=wizard.page_size or 100
                )

                response = client.index_components(sdk_config, req)
                if response.get('status') == 'Success' and response.get('data'):
                    # New payload: list of objects with IndexComponent array
                    data_items = response['data'].get('items', []) or response['data']
                    if not data_items:
                        break
                    for data in data_items:
                        components = data.get('IndexComponent', [])
                        if not isinstance(components, list):
                            components = []
                        for comp in components:
                            symbol = comp.get('StockSymbol') or comp.get('symbol')
                            if not symbol:
                                continue
                            security = securities_model.search([('symbol', '=', symbol)], limit=1)
                            if not security:
                                continue
                            existing = component_model.search([
                                ('index_id', '=', index_record.id),
                                ('security_id', '=', security.id)
                            ], limit=1)
                            values = {
                                'index_id': index_record.id,
                                'security_id': security.id,
                                'weight': comp.get('weight', 0.0) or 0.0,
                                'is_active': comp.get('isActive', True),
                            }
                            if existing:
                                existing.write(values)
                            else:
                                component_model.create(values)
                            total_components += 1
                else:
                    break
                current_page += 1
                try:
                    wizard.env.cr.commit()
                except Exception:
                    pass
        except Exception as e:
            _logger.warning("Skip index components for %s due to %s", index_record.index_code, str(e))
            error_count += 1

    wizard.result_message += f"<p>Fetched {total_components} index components (Errors: {error_count})</p>"
    wizard.last_count = total_components


