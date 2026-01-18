from odoo import http, _
from odoo.http import request, Response
import json
import logging
import re
import requests

_logger = logging.getLogger(__name__)

from odoo.exceptions import UserError


class DataManagementController(http.Controller):
    # ----------- HOLIDAY -----------
    @http.route("/holiday_list", type="http", auth="user", website=True)
    def holiday_list_page(self, **kwargs):
        return request.render(
            "fund_management_control.holiday_list", {"active_page": "holiday"}
        )

    @http.route(
        "/get_holiday_data",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    def get_holiday_data(self, page=1, limit=10, search="", **kwargs):
        _logger.info(f">>> API called: page={page}, limit={limit}, search='{search}'")
        try:
            domain = []
            if search:
                domain = ["|", ("name", "ilike", search), ("code", "ilike", search)]
            total_records = request.env["data.holiday"].search_count(domain)
            offset = (int(page) - 1) * int(limit)
            holidays = request.env["data.holiday"].search(
                domain, limit=int(limit), offset=offset
            )
            data = []
            for h in holidays:
                data.append(
                    {
                        "id": h.id,
                        "name": h.name or "",
                        "code": h.code or "",
                        "date": str(h.date) if h.date else "",
                        "value": h.value or "",
                        "active": h.active,
                    }
                )
            response_data = {"records": data, "total_records": total_records}
            return Response(json.dumps(response_data), content_type="application/json")
        except Exception as e:
            _logger.error(f"!!! Error in /get_holiday_data: {str(e)}", exc_info=True)
            return Response(
                json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500,
            )

    @http.route("/holiday/new", type="http", auth="user", website=True)
    def holiday_form_page(self, **kwargs):
        return request.render(
            "fund_management_control.holiday_form", {"active_page": "holiday"}
        )

    @http.route(
        "/holiday/create",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def create_holiday(self, **post):
        vals = {
            "name": post.get("name"),
            "code": post.get("code"),
            "date": post.get("date"),
            "value": post.get("value"),
            "active": post.get("active") == "on",
        }
        request.env["data.holiday"].sudo().create(vals)
        return request.redirect("/holiday_list")

    @http.route(
        "/holiday/sync",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def holiday_sync(self, **kwargs):
        payload = {}
        try:
            payload = request.get_json_data(force=False, silent=True) or {}
        except Exception as exc:  # noqa: BLE001
            _logger.warning("Không thể parse JSON đầu vào khi đồng bộ ngày lễ: %s", exc)

        year = payload.get("year")
        country_code = payload.get("country_code", "VN")

        try:
            result = (
                request.env["data.holiday"]
                .sudo()
                .sync_public_holidays(year=year, country_code=country_code)
            )
            return Response(json.dumps(result), content_type="application/json")
        except UserError as exc:
            return Response(
                json.dumps({"success": False, "error": str(exc)}),
                content_type="application/json",
                status=400,
            )
        except Exception as exc:  # noqa: BLE001
            _logger.error("Lỗi đồng bộ ngày lễ: %s", exc, exc_info=True)
            return Response(
                json.dumps(
                    {
                        "success": False,
                        "error": _("Không thể đồng bộ ngày lễ: %s") % str(exc),
                    }
                ),
                content_type="application/json",
                status=500,
            )

    @http.route(
        "/holiday/sync/internal",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def holiday_sync_internal(self, **kwargs):
        payload = {}
        try:
            payload = request.get_json_data(force=False, silent=True) or {}
        except Exception as exc:  # noqa: BLE001
            _logger.warning("Không thể parse JSON đầu vào khi đồng bộ nội bộ ngày lễ: %s", exc)

        year = payload.get("year")

        try:
            result = (
                request.env["data.holiday"].sudo().sync_local_holidays(year=year)
            )
            return Response(json.dumps(result), content_type="application/json")
        except UserError as exc:
            return Response(
                json.dumps({"success": False, "error": str(exc)}),
                content_type="application/json",
                status=400,
            )
        except Exception as exc:  # noqa: BLE001
            _logger.error("Lỗi đồng bộ nội bộ ngày lễ: %s", exc, exc_info=True)
            return Response(
                json.dumps(
                    {
                        "success": False,
                        "error": _("Không thể đồng bộ nội bộ ngày lễ: %s") % str(exc),
                    }
                ),
                content_type="application/json",
                status=500,
            )

    @http.route(
        "/holiday/edit/<int:holiday_id>", type="http", auth="user", website=True
    )
    def holiday_edit_page(self, holiday_id, **kwargs):
        holiday = request.env["data.holiday"].sudo().browse(holiday_id)
        return request.render(
            "fund_management_control.holiday_form",
            {"holiday": holiday, "edit_mode": True, "active_page": "holiday"},
        )

    @http.route(
        "/holiday/update/<int:holiday_id>",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def update_holiday(self, holiday_id, **post):
        holiday = request.env["data.holiday"].sudo().browse(holiday_id)
        vals = {
            "name": post.get("name"),
            "code": post.get("code"),
            "date": post.get("date"),
            "value": post.get("value"),
            "active": post.get("active") == "on",
        }
        holiday.write(vals)
        return request.redirect("/holiday_list")

    @http.route(
        "/holiday/delete/<int:holiday_id>",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def delete_holiday(self, holiday_id, **post):
        holiday = request.env["data.holiday"].sudo().browse(holiday_id)
        holiday.unlink()
        return request.redirect("/holiday_list")

    # ----------- BANK -----------
    @http.route("/bank_list", type="http", auth="user", website=True)
    def bank_list_page(self, **kwargs):
        return request.render(
            "fund_management_control.bank_list", {"active_page": "bank"}
        )

    @http.route(
        "/get_bank_data",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    def get_bank_data(self, page=1, limit=10, search="", **kwargs):
        domain = []
        if search:
            domain = ["|", ("name", "ilike", search), ("short_name", "ilike", search)]
        total_records = request.env["data.bank"].search_count(domain)
        offset = (int(page) - 1) * int(limit)
        banks = request.env["data.bank"].search(domain, limit=int(limit), offset=offset)
        data = []
        for b in banks:
            data.append(
                {
                    "id": b.id,
                    "name": b.name or "",
                    "english_name": b.english_name or "",
                    "short_name": b.short_name or "",
                    "code": b.code or "",
                    "swift_code": b.swift_code or "",
                    "website": b.website or "",
                    "active": b.active,
                }
            )
        return Response(
            json.dumps({"records": data, "total_records": total_records}),
            content_type="application/json",
        )

    @http.route(
        "/bank/sync/vietqr",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def bank_sync_vietqr(self, **kwargs):
        try:
            result = request.env["data.bank"].sudo().sync_vietqr_banks()
            return Response(json.dumps(result), content_type="application/json")
        except UserError as exc:
            return Response(
                json.dumps({"success": False, "error": str(exc)}),
                content_type="application/json",
                status=400,
            )
        except Exception as exc:  # noqa: BLE001
            _logger.error("Lỗi đồng bộ ngân hàng VietQR: %s", exc, exc_info=True)
            return Response(
                json.dumps(
                    {
                        "success": False,
                        "error": _("Không thể đồng bộ ngân hàng VietQR: %s")
                        % str(exc),
                    }
                ),
                content_type="application/json",
                status=500,
            )

    @http.route("/bank/new", type="http", auth="user", website=True)
    def bank_form_page(self, **kwargs):
        return request.render(
            "fund_management_control.bank_form", {"active_page": "bank"}
        )

    @http.route(
        "/bank/create", type="http", auth="user", methods=["POST"], csrf=False, cors="*"
    )
    def create_bank(self, **post):
        vals = {
            "name": post.get("name"),
            "english_name": post.get("english_name"),
            "short_name": post.get("short_name"),
            "code": post.get("code"),
            "swift_code": post.get("swift_code"),
            "website": post.get("website"),
            "active": post.get("active") == "on",
        }
        request.env["data.bank"].sudo().create(vals)
        return request.redirect("/bank_list")

    @http.route("/bank/edit/<int:bank_id>", type="http", auth="user", website=True)
    def bank_edit_page(self, bank_id, **kwargs):
        bank = request.env["data.bank"].sudo().browse(bank_id)
        return request.render(
            "fund_management_control.bank_form",
            {"bank": bank, "edit_mode": True, "active_page": "bank"},
        )

    @http.route(
        "/bank/update/<int:bank_id>",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def update_bank(self, bank_id, **post):
        bank = request.env["data.bank"].sudo().browse(bank_id)
        vals = {
            "name": post.get("name"),
            "english_name": post.get("english_name"),
            "short_name": post.get("short_name"),
            "code": post.get("code"),
            "swift_code": post.get("swift_code"),
            "website": post.get("website"),
            "active": post.get("active") == "on",
        }
        bank.write(vals)
        return request.redirect("/bank_list")

    @http.route(
        "/bank/delete/<int:bank_id>",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def delete_bank(self, bank_id, **post):
        bank = request.env["data.bank"].sudo().browse(bank_id)
        bank.unlink()
        return request.redirect("/bank_list")

    # ----------- UTILITIES: BUSINESS LOOKUP BY TAX CODE -----------
    @http.route(
        "/utils/business_lookup",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def business_lookup(self, **kwargs):
        payload = {}
        try:
            payload = request.get_json_data(force=False, silent=True) or {}
        except Exception:
            pass

        raw_tax_code = (payload.get("tax_code") or payload.get("taxCode") or "").strip()
        tax_code = re.sub(r"[^0-9]", "", raw_tax_code)
        if not tax_code:
            return Response(
                json.dumps({"success": False, "error": _("Mã số thuế không hợp lệ.")}),
                content_type="application/json",
                status=400,
            )

        api_url = f"https://api.vietqr.io/v2/business/{tax_code}"
        headers = {"User-Agent": "HDC-FMS/1.0"}

        try:
            resp = requests.get(api_url, headers=headers, timeout=8)
        except requests.RequestException as exc:  # noqa: BLE001
            return Response(
                json.dumps({"success": False, "error": str(exc)}),
                content_type="application/json",
                status=502,
            )

        if resp.status_code == 429:
            return Response(
                json.dumps({
                    "success": False,
                    "error": _("Quá giới hạn gọi API (429). Vui lòng thử lại sau."),
                }),
                content_type="application/json",
                status=429,
            )

        if not resp.ok:
            return Response(
                json.dumps({
                    "success": False,
                    "error": _("Không thể tra cứu MST (HTTP %s).") % resp.status_code,
                }),
                content_type="application/json",
                status=resp.status_code,
            )

        try:
            payload = resp.json()
        except ValueError:
            payload = {"code": "99", "desc": "Invalid JSON", "data": {}}

        result = {
            "success": True,
            "code": payload.get("code"),
            "desc": payload.get("desc"),
            "data": payload.get("data", {}),
        }
        return Response(json.dumps(result), content_type="application/json")

    # ----------- BANK BRANCH -----------
    @http.route("/bank_branch_list", type="http", auth="user", website=True)
    def bank_branch_list_page(self, **kwargs):
        return request.render(
            "fund_management_control.bank_branch_list", {"active_page": "bank_branch"}
        )

    @http.route(
        "/get_bank_branch_data",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    def get_bank_branch_data(self, page=1, limit=10, search="", **kwargs):
        domain = []
        if search:
            domain = ["|", ("name", "ilike", search), ("code", "ilike", search)]
        total_records = request.env["data.bank.branch"].search_count(domain)
        offset = (int(page) - 1) * int(limit)
        branches = request.env["data.bank.branch"].search(
            domain, limit=int(limit), offset=offset
        )
        data = []
        for br in branches:
            data.append(
                {
                    "id": br.id,
                    "name": br.name or "",
                    "bank_id": br.bank_id.name if br.bank_id else "",
                    "code": br.code or "",
                    "active": br.active,
                }
            )
        return Response(
            json.dumps({"records": data, "total_records": total_records}),
            content_type="application/json",
        )

    @http.route(
        "/data/seed/vietnam_cities",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def seed_vietnam_cities(self, **kwargs):
        try:
            result = request.env["data.country"].sudo().seed_vietnam_with_cities()
            return Response(json.dumps(result), content_type="application/json")
        except UserError as exc:
            return Response(
                json.dumps({"success": False, "error": str(exc)}),
                content_type="application/json",
                status=400,
            )
        except Exception as exc:  # noqa: BLE001
            _logger.error("Lỗi seed tỉnh/thành: %s", exc, exc_info=True)
            return Response(
                json.dumps({
                    "success": False,
                    "error": _("Không thể seed tỉnh/thành: %s") % str(exc),
                }),
                content_type="application/json",
                status=500,
            )

    @http.route(
        "/bank_branch/sync/basic",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def bank_branch_sync_basic(self, **kwargs):
        try:
            result = request.env["data.bank.branch"].sudo().sync_basic_branches()
            return Response(json.dumps(result), content_type="application/json")
        except UserError as exc:
            return Response(
                json.dumps({"success": False, "error": str(exc)}),
                content_type="application/json",
                status=400,
            )
        except Exception as exc:  # noqa: BLE001
            _logger.error("Lỗi đồng bộ chi nhánh ngân hàng: %s", exc, exc_info=True)
            return Response(
                json.dumps({
                    "success": False,
                    "error": _("Không thể đồng bộ chi nhánh ngân hàng: %s") % str(exc),
                }),
                content_type="application/json",
                status=500,
            )

    @http.route(
        "/bank_branch/sync/nationwide",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def bank_branch_sync_nationwide(self, **kwargs):
        try:
            result = request.env["data.bank.branch"].sudo().sync_branches_nationwide()
            return Response(json.dumps(result), content_type="application/json")
        except UserError as exc:
            return Response(
                json.dumps({"success": False, "error": str(exc)}),
                content_type="application/json",
                status=400,
            )
        except Exception as exc:  # noqa: BLE001
            _logger.error("Lỗi đồng bộ chi nhánh toàn quốc: %s", exc, exc_info=True)
            return Response(
                json.dumps({
                    "success": False,
                    "error": _("Không thể đồng bộ chi nhánh toàn quốc: %s") % str(exc),
                }),
                content_type="application/json",
                status=500,
            )

    @http.route("/bank_branch/new", type="http", auth="user", website=True)
    def bank_branch_form_page(self, **kwargs):
        return request.render(
            "fund_management_control.bank_branch_form", {"active_page": "bank_branch"}
        )

    @http.route(
        "/bank_branch/create",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def create_bank_branch(self, **post):
        bank_id = post.get("bank_id")
        bank_obj = request.env["data.bank"].search([("name", "=", bank_id)], limit=1)
        vals = {
            "name": post.get("name"),
            "bank_id": bank_obj.id if bank_obj else False,
            "code": post.get("code"),
            "active": post.get("active") == "on",
        }
        request.env["data.bank.branch"].sudo().create(vals)
        return request.redirect("/bank_branch_list")

    @http.route(
        "/bank_branch/edit/<int:branch_id>", type="http", auth="user", website=True
    )
    def bank_branch_edit_page(self, branch_id, **kwargs):
        branch = request.env["data.bank.branch"].sudo().browse(branch_id)
        return request.render(
            "fund_management_control.bank_branch_form",
            {"bank_branch": branch, "edit_mode": True, "active_page": "bank_branch"},
        )

    @http.route(
        "/bank_branch/update/<int:branch_id>",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def update_bank_branch(self, branch_id, **post):
        branch = request.env["data.bank.branch"].sudo().browse(branch_id)
        bank_obj = request.env["data.bank"].search(
            [("name", "=", post.get("bank_id"))], limit=1
        )
        vals = {
            "name": post.get("name"),
            "bank_id": bank_obj.id if bank_obj else False,
            "code": post.get("code"),
            "active": post.get("active") == "on",
        }
        branch.write(vals)
        return request.redirect("/bank_branch_list")

    @http.route(
        "/bank_branch/delete/<int:branch_id>",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def delete_bank_branch(self, branch_id, **post):
        branch = request.env["data.bank.branch"].sudo().browse(branch_id)
        branch.unlink()
        return request.redirect("/bank_branch_list")

    # ----------- COUNTRY -----------
    @http.route("/country_list", type="http", auth="user", website=True)
    def country_list_page(self, **kwargs):
        return request.render(
            "fund_management_control.country_list", {"active_page": "country"}
        )

    @http.route(
        "/get_country_data",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    def get_country_data(self, page=1, limit=10, search="", **kwargs):
        domain = []
        if search:
            domain = ["|", ("name", "ilike", search), ("code", "ilike", search)]
        total_records = request.env["data.country"].search_count(domain)
        offset = (int(page) - 1) * int(limit)
        countries = request.env["data.country"].search(
            domain, limit=int(limit), offset=offset
        )
        data = []
        for c in countries:
            data.append(
                {
                    "id": c.id,
                    "name": c.name or "",
                    "english_name": c.english_name or "",
                    "code": c.code or "",
                    "phone_code": c.phone_code or "",
                    "postal_code": c.postal_code or "",
                    "vsd_code": c.vsd_code or "",
                    "sort_order": c.sort_order,
                    "active": c.active,
                }
            )
        return Response(
            json.dumps({"records": data, "total_records": total_records}),
            content_type="application/json",
        )

    @http.route("/country/new", type="http", auth="user", website=True)
    def country_form_page(self, **kwargs):
        return request.render(
            "fund_management_control.country_form", {"active_page": "country"}
        )

    @http.route(
        "/country/create",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def create_country(self, **post):
        vals = {
            "name": post.get("name"),
            "english_name": post.get("english_name"),
            "code": post.get("code"),
            "phone_code": post.get("phone_code"),
            "postal_code": post.get("postal_code"),
            "vsd_code": post.get("vsd_code"),
            "sort_order": int(post.get("sort_order", 0)),
            "active": post.get("active") == "on",
        }
        request.env["data.country"].sudo().create(vals)
        return request.redirect("/country_list")

    @http.route(
        "/country/edit/<int:country_id>", type="http", auth="user", website=True
    )
    def country_edit_page(self, country_id, **kwargs):
        country = request.env["data.country"].sudo().browse(country_id)
        return request.render(
            "fund_management_control.country_form",
            {"country": country, "edit_mode": True, "active_page": "country"},
        )

    @http.route(
        "/country/update/<int:country_id>",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def update_country(self, country_id, **post):
        country = request.env["data.country"].sudo().browse(country_id)
        vals = {
            "name": post.get("name"),
            "english_name": post.get("english_name"),
            "code": post.get("code"),
            "phone_code": post.get("phone_code"),
            "postal_code": post.get("postal_code"),
            "vsd_code": post.get("vsd_code"),
            "sort_order": int(post.get("sort_order", 0)),
            "active": post.get("active") == "on",
        }
        country.write(vals)
        return request.redirect("/country_list")

    @http.route(
        "/country/delete/<int:country_id>",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def delete_country(self, country_id, **post):
        country = request.env["data.country"].sudo().browse(country_id)
        country.unlink()
        return request.redirect("/country_list")

    # ----------- CITY -----------
    @http.route("/city_list", type="http", auth="user", website=True)
    def city_list_page(self, **kwargs):
        return request.render(
            "fund_management_control.city_list", {"active_page": "city"}
        )

    @http.route(
        "/get_city_data",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    def get_city_data(self, page=1, limit=10, search="", **kwargs):
        domain = []
        if search:
            domain = ["|", ("name", "ilike", search), ("code", "ilike", search)]
        total_records = request.env["data.city"].search_count(domain)
        offset = (int(page) - 1) * int(limit)
        cities = request.env["data.city"].search(
            domain, limit=int(limit), offset=offset
        )
        data = []
        for c in cities:
            data.append(
                {
                    "id": c.id,
                    "name": c.name or "",
                    "english_name": c.english_name or "",
                    "country_id": c.country_id.name if c.country_id else "",
                    "code": c.code or "",
                    "sort_order": c.sort_order,
                    "active": c.active,
                }
            )
        return Response(
            json.dumps({"records": data, "total_records": total_records}),
            content_type="application/json",
        )

    @http.route("/city/new", type="http", auth="user", website=True)
    def city_form_page(self, **kwargs):
        return request.render(
            "fund_management_control.city_form", {"active_page": "city"}
        )

    @http.route(
        "/city/create", type="http", auth="user", methods=["POST"], csrf=False, cors="*"
    )
    def create_city(self, **post):
        country_id = post.get("country_id")
        country_obj = request.env["data.country"].search(
            [("name", "=", country_id)], limit=1
        )
        vals = {
            "name": post.get("name"),
            "english_name": post.get("english_name"),
            "country_id": country_obj.id if country_obj else False,
            "code": post.get("code"),
            "sort_order": int(post.get("sort_order", 0)),
            "active": post.get("active") == "on",
        }
        request.env["data.city"].sudo().create(vals)
        return request.redirect("/city_list")

    @http.route("/city/edit/<int:city_id>", type="http", auth="user", website=True)
    def city_edit_page(self, city_id, **kwargs):
        city = request.env["data.city"].sudo().browse(city_id)
        return request.render(
            "fund_management_control.city_form",
            {"city": city, "edit_mode": True, "active_page": "city"},
        )

    @http.route(
        "/city/update/<int:city_id>",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def update_city(self, city_id, **post):
        city = request.env["data.city"].sudo().browse(city_id)
        country_obj = request.env["data.country"].search(
            [("name", "=", post.get("country_id"))], limit=1
        )
        vals = {
            "name": post.get("name"),
            "english_name": post.get("english_name"),
            "country_id": country_obj.id if country_obj else False,
            "code": post.get("code"),
            "sort_order": int(post.get("sort_order", 0)),
            "active": post.get("active") == "on",
        }
        city.write(vals)
        return request.redirect("/city_list")

    @http.route(
        "/city/delete/<int:city_id>",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def delete_city(self, city_id, **post):
        city = request.env["data.city"].sudo().browse(city_id)
        city.unlink()
        return request.redirect("/city_list")

    # ----------- WARD -----------
    @http.route("/ward_list", type="http", auth="user", website=True)
    def ward_list_page(self, **kwargs):
        return request.render(
            "fund_management_control.ward_list", {"active_page": "ward"}
        )

    @http.route(
        "/get_ward_data",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    def get_ward_data(self, page=1, limit=10, search="", **kwargs):
        domain = []
        if search:
            domain = ["|", ("name", "ilike", search), ("district", "ilike", search)]
        total_records = request.env["data.ward"].search_count(domain)
        offset = (int(page) - 1) * int(limit)
        wards = request.env["data.ward"].search(domain, limit=int(limit), offset=offset)
        data = []
        for w in wards:
            data.append(
                {
                    "id": w.id,
                    "name": w.name or "",
                    "english_name": w.english_name or "",
                    "district": w.district or "",
                    "code": w.code or "",
                    "sort_order": w.sort_order,
                    "active": w.active,
                }
            )
        return Response(
            json.dumps({"records": data, "total_records": total_records}),
            content_type="application/json",
        )

    @http.route("/ward/new", type="http", auth="user", website=True)
    def ward_form_page(self, **kwargs):
        return request.render(
            "fund_management_control.ward_form", {"active_page": "ward"}
        )

    @http.route(
        "/ward/create", type="http", auth="user", methods=["POST"], csrf=False, cors="*"
    )
    def create_ward(self, **post):
        vals = {
            "name": post.get("name"),
            "english_name": post.get("english_name"),
            "district": post.get("district"),
            "code": post.get("code"),
            "sort_order": int(post.get("sort_order", 0)),
            "active": post.get("active") == "on",
        }
        request.env["data.ward"].sudo().create(vals)
        return request.redirect("/ward_list")

    @http.route("/ward/edit/<int:ward_id>", type="http", auth="user", website=True)
    def ward_edit_page(self, ward_id, **kwargs):
        ward = request.env["data.ward"].sudo().browse(ward_id)
        return request.render(
            "fund_management_control.ward_form",
            {"ward": ward, "edit_mode": True, "active_page": "ward"},
        )

    @http.route(
        "/ward/update/<int:ward_id>",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def update_ward(self, ward_id, **post):
        ward = request.env["data.ward"].sudo().browse(ward_id)
        vals = {
            "name": post.get("name"),
            "english_name": post.get("english_name"),
            "district": post.get("district"),
            "code": post.get("code"),
            "sort_order": int(post.get("sort_order", 0)),
            "active": post.get("active") == "on",
        }
        ward.write(vals)
        return request.redirect("/ward_list")

    @http.route(
        "/ward/delete/<int:ward_id>",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def delete_ward(self, ward_id, **post):
        ward = request.env["data.ward"].sudo().browse(ward_id)
        ward.unlink()
        return request.redirect("/ward_list")
