from odoo import http
from odoo.http import request, Response
import json
import logging
import base64

_logger = logging.getLogger(__name__)


class FundManagementProduct(http.Controller):
    # Route của chứng chỉ quỹ
    @http.route("/fund_certificate_list", type="http", auth="user", website=True)
    def fund_certificate_list_page(self, **kwargs):
        """Hiển thị trang danh sách Chứng chỉ quỹ."""
        return request.render(
            "fund_management_control.fund_certificate_list",
            {"active_page": "fund_certificate"},
        )

    @http.route(
        "/get_fund_certificate_data",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    def get_fund_certificate_data(self, page=1, limit=10, search="", **kwargs):
        """
        API endpoint để lấy danh sách Chứng chỉ quỹ có phân trang và tìm kiếm.
        """
        _logger.info(f">>> API được gọi: page={page}, limit={limit}, search='{search}'")

        try:
            # Xây dựng domain động cho tìm kiếm
            domain = []
            if search:
                # Tìm kiếm trong các trường symbol, short_name_vn, short_name_en
                domain = [
                    "|",
                    "|",
                    ("symbol", "ilike", search),
                    ("short_name_vn", "ilike", search),
                    ("short_name_en", "ilike", search),
                ]

            total_records = request.env["fund.certificate"].search_count(domain)
            offset = (int(page) - 1) * int(limit)
            fund_certificates = request.env["fund.certificate"].search(
                domain, limit=int(limit), offset=offset
            )

            data = []
            for cert in fund_certificates:
                data.append(
                    {
                        "id": cert.id,
                        "symbol": cert.symbol or "",
                        "short_name_vn": cert.short_name_vn or "",
                        "short_name_en": cert.short_name_en or "",
                        "fund_color": cert.fund_color or "#FFFFFF",
                        "current_price": cert.current_price or 0.0,
                        "reference_price": cert.reference_price or 0.0,
                        "product_type": dict(
                            cert._fields["product_type"].selection
                        ).get(cert.product_type, ""),
                        "product_status": dict(
                            cert._fields["product_status"].selection
                        ).get(cert.product_status, ""),
                        "inception_time": (
                            cert.inception_date.strftime("%H:%M")
                            if cert.inception_date
                            else ""
                        ),
                        "report_website": cert.report_website or "#",
                        # FIX: Đường dẫn hình ảnh fallback đúng trong module này
                        "fund_image": (
                            f"/web/image?model=fund.certificate&field=fund_image&id={cert.id}"
                            if cert.fund_image
                            else "/fund_management_control/static/src/img/placeholder.png"
                        ),
                    }
                )

            response_data = {"records": data, "total_records": total_records}

            return Response(json.dumps(response_data), content_type="application/json")

        except Exception as e:
            _logger.error(
                f"!!! Lỗi trong /get_fund_certificate_data: {str(e)}", exc_info=True
            )
            return Response(
                json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500,
            )

    @http.route("/fund_certificate/new", type="http", auth="user", website=True)
    def fund_certificate_form_page(self, **kwargs):
        """
        Hiển thị trang form để tạo mới Chứng chỉ quỹ.
        Cũng lấy các tùy chọn từ các trường Selection trong model.
        """
        # Lấy model 'fund.certificate'
        FundCertificate = request.env["fund.certificate"]

        # Lấy các tùy chọn từ các trường Selection trong model
        selection_options = {
            "fund_types": FundCertificate._fields["fund_type"].selection,
            "risk_levels": FundCertificate._fields["risk_level"].selection,
            "product_types": FundCertificate._fields["product_type"].selection,
            "product_statuses": FundCertificate._fields["product_status"].selection,
            "active_page": "fund_certificate",  # Truyền biến 'active_page'
        }

        # Truyền các tùy chọn này vào template
        return request.render(
            "fund_management_control.fund_certificate_form", selection_options
        )

    # Thêm route này để xử lý việc tạo mới
    @http.route(
        "/fund_certificate/create",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def create_fund_certificate(self, **post):
        """
        API endpoint để nhận dữ liệu form và tạo mới Chứng chỉ quỹ.
        """
        try:
            _logger.info("Nhận dữ liệu cho chứng chỉ quỹ mới: %s", post)

            # Xử lý các trường boolean (ngày trong tuần)
            weekdays = {
                "monday": post.get("monday") == "on",
                "tuesday": post.get("tuesday") == "on",
                "wednesday": post.get("wednesday") == "on",
                "thursday": post.get("thursday") == "on",
                "friday": post.get("friday") == "on",
                "saturday": post.get("saturday") == "on",
                "sunday": post.get("sunday") == "on",
            }

            # Xử lý hình ảnh (nếu có)
            fund_image_data = False
            if "fund_image" in request.httprequest.files:
                image_file = request.httprequest.files.get("fund_image")
                if image_file:
                    fund_image_data = image_file.read()

            # Chuẩn bị dữ liệu để tạo bản ghi
            vals = {
                "symbol": post.get("symbol"),
                "market": post.get("market") or "HOSE",
                "short_name_vn": post.get("short_name_vn"),
                "short_name_en": post.get("short_name_en"),
                "fund_color": post.get("fund_color"),
                "current_price": float(post.get("current_price", 0)),
                "reference_price": float(post.get("reference_price", 0)),
                # Odoo tự động chuyển đổi chuỗi ngày/giờ sang định dạng Datetime
                "inception_date": (
                    post.get("inception_date") if post.get("inception_date") else None
                ),
                "closure_date": (
                    post.get("closure_date") if post.get("closure_date") else None
                ),
                "receive_money_time": (
                    post.get("receive_money_time")
                    if post.get("receive_money_time")
                    else None
                ),
                "payment_deadline": int(post.get("payment_deadline", 0)),
                "redemption_time": int(post.get("redemption_time", 0)),
                "report_website": post.get("report_website"),
                "fund_type": post.get("fund_type"),
                "risk_level": post.get("risk_level"),
                "product_type": post.get("product_type"),
                "product_status": post.get("product_status"),
                "fund_description": post.get("fund_description"),
                "fund_image": fund_image_data,
                **weekdays,
            }

            # Tạo bản ghi mới
            new_cert = request.env["fund.certificate"].sudo().create(vals)
            _logger.info(
                "Tạo thành công chứng chỉ quỹ mới với ID: %s", new_cert.id
            )

            # Chuyển hướng về trang danh sách sau khi tạo thành công
            return request.redirect("/fund_certificate_list")

        except Exception as e:
            _logger.error(
                "!!! Lỗi khi tạo chứng chỉ quỹ: %s", str(e), exc_info=True
            )
            # Nếu có lỗi, có thể trả về một trang lỗi hoặc quay lại form với thông báo
            # Tạm thời chuyển hướng về trang danh sách
            return request.redirect("/fund_certificate_list")

    @http.route(
        "/fund_certificate/edit/<int:cert_id>", type="http", auth="user", website=True
    )
    def fund_certificate_edit_page(self, cert_id, **kwargs):
        """
        Hiển thị trang để chỉnh sửa Chứng chỉ quỹ đã tồn tại.
        """
        try:
            # Lấy bản ghi chứng chỉ quỹ cụ thể
            certificate = request.env["fund.certificate"].sudo().browse(cert_id)
            if not certificate.exists():
                _logger.warning(
                    f"Thử chỉnh sửa chứng chỉ quỹ không tồn tại với ID: {cert_id}"
                )
                return request.redirect("/fund_certificate_list")

            # Lấy các tùy chọn Selection từ model
            FundCertificate = request.env["fund.certificate"]
            render_values = {
                "cert": certificate,  # Truyền bản ghi vào template
                "fund_types": FundCertificate._fields["fund_type"].selection,
                "risk_levels": FundCertificate._fields["risk_level"].selection,
                "product_types": FundCertificate._fields["product_type"].selection,
                "product_statuses": FundCertificate._fields["product_status"].selection,
                "active_page": "fund_certificate",
            }

            return request.render(
                "fund_management_control.fund_certificate_edit_form", render_values
            )
        except Exception as e:
            _logger.error(
                f"!!! Lỗi khi hiển thị trang chỉnh sửa cho chứng chỉ quỹ ID {cert_id}: {str(e)}",
                exc_info=True,
            )
            return request.redirect("/fund_certificate_list")

    @http.route(
        "/fund_certificate/sync_stock_data",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def sync_stock_data(self, **kwargs):
        """
        API endpoint to sync Fund Certificates from Stock Data.
        Receives JSON: { "market_selection": "all"|"HOSE"..., "sync_option": "both"|"create"... }
        """
        try:
            data = json.loads(request.httprequest.data)
            market_selection = data.get("market_selection", "all")
            sync_option = data.get("sync_option", "both")

            _logger.info(f"Received sync request: market={market_selection}, option={sync_option}")

            # Call the shared sync batch method
            stats = request.env["fund.certificate"].sudo().sync_batch(market_selection, sync_option)

            return Response(
                json.dumps({"success": True, "stats": stats}),
                content_type="application/json"
            )

        except Exception as e:
            _logger.error(f"Error in /fund_certificate/sync_stock_data: {e}", exc_info=True)
            return Response(
                json.dumps({"success": False, "error": str(e)}),
                content_type="application/json",
                status=500,
            )

    # === NEW: Route để xử lý logic cập nhật ===
    @http.route(
        "/fund_certificate/update",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def update_fund_certificate(self, **post):
        """
        API endpoint để nhận dữ liệu form và cập nhật Chứng chỉ quỹ đã tồn tại.
        """
        cert_id = post.get("cert_id")
        if not cert_id:
            _logger.error("!!! Cập nhật thất bại: cert_id không được cung cấp trong dữ liệu POST.")
            return request.redirect("/fund_certificate_list")

        try:
            _logger.info(
                f"Nhận dữ liệu để cập nhật chứng chỉ quỹ ID {cert_id}: {post}"
            )
            certificate = request.env["fund.certificate"].sudo().browse(int(cert_id))
            if not certificate.exists():
                _logger.error(
                    f"!!! Cập nhật thất bại: Không tìm thấy Chứng chỉ quỹ với ID {cert_id}."
                )
                return request.redirect("/fund_certificate_list")

            weekdays = {
                "monday": post.get("monday") == "on",
                "tuesday": post.get("tuesday") == "on",
                "wednesday": post.get("wednesday") == "on",
                "thursday": post.get("thursday") == "on",
                "friday": post.get("friday") == "on",
                "saturday": post.get("saturday") == "on",
                "sunday": post.get("sunday") == "on",
            }

            vals = {
                "symbol": post.get("symbol"),
                "market": post.get("market") or "HOSE",
                "short_name_vn": post.get("short_name_vn"),
                "short_name_en": post.get("short_name_en"),
                "fund_color": post.get("fund_color"),
                "current_price": float(post.get("current_price", 0)),
                "reference_price": float(post.get("reference_price", 0)),
                "inception_date": (
                    post.get("inception_date") if post.get("inception_date") else None
                ),
                "closure_date": (
                    post.get("closure_date") if post.get("closure_date") else None
                ),
                "receive_money_time": (
                    post.get("receive_money_time")
                    if post.get("receive_money_time")
                    else None
                ),
                "payment_deadline": int(post.get("payment_deadline", 0)),
                "redemption_time": int(post.get("redemption_time", 0)),
                "report_website": post.get("report_website"),
                "fund_type": post.get("fund_type"),
                "risk_level": post.get("risk_level"),
                "product_type": post.get("product_type"),
                "product_status": post.get("product_status"),
                "fund_description": post.get("fund_description"),
                **weekdays,
            }

            # Chỉ cập nhật hình ảnh nếu có hình mới được upload
            if "fund_image" in request.httprequest.files:
                image_file = request.httprequest.files.get("fund_image")
                if image_file and image_file.filename:
                    vals["fund_image"] = base64.b64encode(image_file.read())

            certificate.write(vals)
            _logger.info(f"Cập nhật thành công chứng chỉ quỹ với ID: {cert_id}")
            return request.redirect("/fund_certificate_list")

        except Exception as e:
            _logger.error(
                f"!!! Lỗi khi cập nhật chứng chỉ quỹ ID {cert_id}: {str(e)}",
                exc_info=True,
            )
            return request.redirect(
                f"/fund_certificate/edit/{cert_id}"
            )  # Chuyển hướng về trang chỉnh sửa khi có lỗi

    @http.route(
        "/fund_certificate/delete",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def delete_fund_certificate(self, **kwargs):
        """
        API endpoint để xóa Chứng chỉ quỹ.
        Sử dụng type='http' để trả về JSON response mà frontend có thể xử lý dễ dàng.
        """
        try:
            # Lấy dữ liệu từ body của request HTTP
            data = json.loads(request.httprequest.data)
            cert_id = data.get("cert_id")

            if not cert_id:
                _logger.error("!!! Xóa thất bại: cert_id không được cung cấp trong dữ liệu JSON.")
                error_payload = json.dumps(
                    {"success": False, "error": "ID Chứng chỉ quỹ không được cung cấp."}
                )
                return Response(
                    error_payload, content_type="application/json", status=400
                )

            _logger.info(f"Đang thử xóa chứng chỉ quỹ với ID: {cert_id}")

            certificate = request.env["fund.certificate"].sudo().browse(int(cert_id))

            if not certificate.exists():
                _logger.warning(
                    f"Thử xóa chứng chỉ quỹ không tồn tại với ID: {cert_id}"
                )
                error_payload = json.dumps(
                    {"success": False, "error": "Không tìm thấy bản ghi để xóa."}
                )
                return Response(
                    error_payload, content_type="application/json", status=404
                )

            cert_name = certificate.short_name_vn or certificate.symbol or f"ID: {cert_id}"

            certificate.unlink()

            _logger.info(f"Xóa thành công chứng chỉ quỹ: {cert_name}")
            success_payload = json.dumps(
                {"success": True, "message": f"Đã xóa thành công {cert_name}"}
            )
            return Response(success_payload, content_type="application/json")

        except ValueError as ve:
            _logger.error(f"!!! ValueError khi xóa chứng chỉ quỹ: {str(ve)}")
            error_payload = json.dumps({"success": False, "error": "ID không hợp lệ."})
            return Response(error_payload, content_type="application/json", status=400)
        except Exception as e:
            _logger.error(
                f"!!! Lỗi khi xóa chứng chỉ quỹ: {str(e)}", exc_info=True
            )
            error_payload = json.dumps(
                {"success": False, "error": f"Lỗi máy chủ: {str(e)}"}
            )
            return Response(error_payload, content_type="application/json", status=500)

    # Route của loại chương trình
    @http.route("/scheme_type_list", type="http", auth="user", website=True)
    def scheme_type_list_page(self, **kwargs):
        """
        Renders the page layout for the Scheme Type list.
        """
        return request.render(
            "fund_management_control.scheme_type_list", {"active_page": "scheme_type"}
        )

    @http.route(
        "/get_scheme_type_data",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    def get_scheme_type_data(self, page=1, limit=10, search="", **kwargs):
        """
        API endpoint to fetch a paginated and searchable list of Scheme Types.
        """
        _logger.info(
            f">>> API Scheme Type called: page={page}, limit={limit}, search='{search}'"
        )

        try:
            domain = []
            if search:
                domain = [
                    "|",
                    ("name", "ilike", search),
                    ("name_acronym", "ilike", search),
                ]

            total_records = request.env["fund.scheme.type"].search_count(domain)
            offset = (int(page) - 1) * int(limit)

            # Sắp xếp theo tên để đảm bảo thứ tự nhất quán
            scheme_types = request.env["fund.scheme.type"].search(
                domain, limit=int(limit), offset=offset, order="name asc"
            )

            data = []
            for st in scheme_types:
                data.append(
                    {
                        "id": st.id,
                        "name": st.name or "",
                        "name_acronym": st.name_acronym or "",
                        "auto_invest": st.auto_invest,
                        "activate_scheme": st.activate_scheme,
                    }
                )

            response_data = {"records": data, "total_records": total_records}

            return Response(json.dumps(response_data), content_type="application/json")

        except Exception as e:
            _logger.error(
                f"!!! Error in /get_scheme_type_data: {str(e)}", exc_info=True
            )
            return Response(
                json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500,
            )

    @http.route("/scheme_type/new", type="http", auth="user", website=True)
    def scheme_type_form_page(self, **kwargs):
        """
        Renders the page with the form to create a new Scheme Type.
        """
        return request.render(
            "fund_management_control.scheme_type_form", {"active_page": "scheme_type"}
        )

    @http.route(
        "/scheme_type/create",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def create_scheme_type(self, **post):
        """
        API endpoint to receive form data and create a new Scheme Type.
        """
        try:
            _logger.info("Received data for new scheme type: %s", post)

            # Xử lý các giá trị boolean từ form (checkbox/switch)
            # Nếu checkbox được tick, giá trị sẽ là 'on'. Nếu không, nó sẽ không có trong `post`.
            vals = {
                "name": post.get("name"),
                "name_acronym": post.get("name_acronym"),
                "scheme_code": post.get("scheme_code"),
                "auto_invest": post.get("auto_invest") == "on",
                "activate_scheme": post.get("activate_scheme") == "on",
                "first_transaction_fee": post.get("first_transaction_fee") == "on",
            }

            # Tạo bản ghi mới
            request.env["fund.scheme.type"].sudo().create(vals)
            _logger.info("Successfully created new scheme type.")

            # Chuyển hướng về trang danh sách sau khi tạo thành công
            return request.redirect("/scheme_type_list")

        except Exception as e:
            _logger.error("!!! Error creating scheme type: %s", str(e), exc_info=True)
            # Chuyển hướng về trang danh sách nếu có lỗi
            return request.redirect("/scheme_type_list")

    @http.route("/scheme_type/edit/<int:st_id>", type="http", auth="user", website=True)
    def scheme_type_edit_page(self, st_id, **kwargs):
        """
        Renders the page to edit an existing Scheme Type.
        """
        try:
            scheme_type = request.env["fund.scheme.type"].sudo().browse(st_id)
            if not scheme_type.exists():
                _logger.warning(
                    f"Attempted to edit non-existent scheme type with ID: {st_id}"
                )
                return request.redirect("/scheme_type_list")

            render_values = {
                "st": scheme_type,
                "active_page": "scheme_type",
            }

            return request.render(
                "fund_management_control.scheme_type_edit_form", render_values
            )
        except Exception as e:
            _logger.error(
                f"!!! Error rendering edit page for scheme type ID {st_id}: {str(e)}",
                exc_info=True,
            )
            return request.redirect("/scheme_type_list")

    # === NEW: Route to handle the update logic ===
    @http.route(
        "/scheme_type/update", type="http", auth="user", methods=["POST"], csrf=False
    )
    def update_scheme_type(self, **post):
        """
        API endpoint to receive form data and update an existing Scheme Type.
        """
        st_id = post.get("scheme_type_id")
        if not st_id:
            _logger.error(
                "!!! Update failed: scheme_type_id not provided in POST data."
            )
            return request.redirect("/scheme_type_list")

        try:
            scheme_type = request.env["fund.scheme.type"].sudo().browse(int(st_id))
            if not scheme_type.exists():
                _logger.error(
                    f"!!! Update failed: Scheme type with ID {st_id} not found."
                )
                return request.redirect("/scheme_type_list")

            vals = {
                "name": post.get("name"),
                "name_acronym": post.get("name_acronym"),
                "scheme_code": post.get("scheme_code"),
                "auto_invest": post.get("auto_invest") == "on",
                "activate_scheme": post.get("activate_scheme") == "on",
                "first_transaction_fee": post.get("first_transaction_fee") == "on",
            }

            scheme_type.write(vals)
            _logger.info(f"Successfully updated scheme type with ID: {st_id}")
            return request.redirect("/scheme_type_list")

        except Exception as e:
            _logger.error(
                f"!!! Error updating scheme type ID {st_id}: {str(e)}", exc_info=True
            )
            return request.redirect(f"/scheme_type/edit/{st_id}")

    # === NEW: Route to handle delete logic ===
    @http.route(
        "/scheme_type/delete",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def delete_scheme_type(self, **kwargs):
        """
        API endpoint to delete a scheme type.
        """
        try:
            data = json.loads(request.httprequest.data)
            st_id = data.get("id")

            if not st_id:
                return Response(
                    json.dumps({"success": False, "error": "ID không được cung cấp."}),
                    status=400,
                )

            scheme_type = request.env["fund.scheme.type"].sudo().browse(int(st_id))

            if not scheme_type.exists():
                return Response(
                    json.dumps({"success": False, "error": "Không tìm thấy bản ghi."}),
                    status=404,
                )

            st_name = scheme_type.name or f"ID {st_id}"
            scheme_type.unlink()

            _logger.info(f"Successfully deleted scheme type: {st_name}")
            return Response(
                json.dumps({"success": True, "message": f"Đã xóa thành công {st_name}"})
            )

        except Exception as e:
            _logger.error(f"!!! Error deleting scheme type: {str(e)}", exc_info=True)
            return Response(
                json.dumps({"success": False, "error": f"Lỗi máy chủ: {str(e)}"}),
                status=500,
            )

    # Route của chương trình
    @http.route("/scheme_list", type="http", auth="user", website=True)
    def scheme_list_page(self, **kwargs):
        """Renders the page layout for the Scheme list."""
        return request.render(
            "fund_management_control.scheme_list", {"active_page": "scheme"}
        )

    @http.route(
        "/get_scheme_data",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    def get_scheme_data(self, page=1, limit=10, search="", **kwargs):
        """
        API endpoint to fetch a paginated and searchable list of Schemes.
        """
        _logger.info(
            f">>> API Scheme called: page={page}, limit={limit}, search='{search}'"
        )
        try:
            domain = []
            if search:
                domain = [
                    "|",
                    ("name", "ilike", search),
                    ("transaction_code", "ilike", search),
                ]

            total_records = request.env["fund.scheme"].search_count(domain)
            offset = (int(page) - 1) * int(limit)
            schemes = request.env["fund.scheme"].search(
                domain, limit=int(limit), offset=offset, order="name asc"
            )

            data = []
            for s in schemes:
                data.append(
                    {
                        "id": s.id,
                        "name": s.name or "",
                        "transaction_code": s.transaction_code or "",
                        "min_purchase_value": s.min_purchase_value,
                        "min_sell_quantity": s.min_sell_quantity,
                        "min_conversion_quantity": s.min_conversion_quantity,
                        "min_holding_quantity": s.min_holding_quantity,
                        "can_purchase": s.can_purchase,
                        "can_sell": s.can_sell,
                        "can_convert": s.can_convert,
                        "active_status": dict(s._fields["active_status"].selection).get(
                            s.active_status, ""
                        ),
                    }
                )

            response_data = {"records": data, "total_records": total_records}
            return Response(json.dumps(response_data), content_type="application/json")
        except Exception as e:
            _logger.error(f"!!! Error in /get_scheme_data: {str(e)}", exc_info=True)
            return Response(
                json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500,
            )

    @http.route("/scheme/new", type="http", auth="user", website=True)
    def scheme_form_page(self, **kwargs):
        """Renders the form to create a new Scheme."""
        funds = request.env["fund.certificate"].search([])
        scheme_types = request.env["fund.scheme.type"].search([])
        Scheme = request.env["fund.scheme"]

        render_values = {
            "funds": funds,
            "scheme_types": scheme_types,
            "active_statuses": Scheme._fields["active_status"].selection,
            "active_page": "scheme",
        }
        return request.render("fund_management_control.scheme_form", render_values)

    @http.route(
        "/scheme/create",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def create_scheme(self, **post):
        """Handles the creation of a new Scheme."""
        try:
            _logger.info("Received data for new scheme: %s", post)
            vals = {
                "name": post.get("name"),
                "name_acronym": post.get("name_acronym"),
                "transaction_code": post.get("transaction_code"),
                "min_purchase_value": float(post.get("min_purchase_value", 0)),
                "min_sell_quantity": float(post.get("min_sell_quantity", 0)),
                "min_conversion_quantity": float(
                    post.get("min_conversion_quantity", 0)
                ),
                "min_holding_quantity": float(post.get("min_holding_quantity", 0)),
                "select_fund_id": (
                    int(post.get("select_fund_id"))
                    if post.get("select_fund_id")
                    else False
                ),
                "scheme_type_id": (
                    int(post.get("scheme_type_id"))
                    if post.get("scheme_type_id")
                    else False
                ),
                "amc_fee": float(post.get("amc_fee", 0)),
                "fund_fee": float(post.get("fund_fee", 0)),
                "active_status": post.get("active_status"),
                "can_purchase": post.get("can_purchase") == "on",
                "can_sell": post.get("can_sell") == "on",
                "can_convert": post.get("can_convert") == "on",
            }
            request.env["fund.scheme"].sudo().create(vals)
            return request.redirect("/scheme_list")
        except Exception as e:
            _logger.error("!!! Error creating scheme: %s", str(e), exc_info=True)
            return request.redirect("/scheme_list")

    @http.route("/scheme/edit/<int:scheme_id>", type="http", auth="user", website=True)
    def scheme_edit_page(self, scheme_id, **kwargs):
        """Renders the page to edit an existing Scheme."""
        try:
            scheme = request.env["fund.scheme"].sudo().browse(scheme_id)
            if not scheme.exists():
                _logger.warning(
                    f"Attempted to edit non-existent scheme with ID: {scheme_id}"
                )
                return request.redirect("/scheme_list")

            funds = request.env["fund.certificate"].search([])
            scheme_types = request.env["fund.scheme.type"].search([])
            Scheme = request.env["fund.scheme"]

            render_values = {
                "scheme": scheme,
                "funds": funds,
                "scheme_types": scheme_types,
                "active_statuses": Scheme._fields["active_status"].selection,
                "active_page": "scheme",
            }

            return request.render(
                "fund_management_control.scheme_edit_form", render_values
            )
        except Exception as e:
            _logger.error(
                f"!!! Error rendering edit page for scheme ID {scheme_id}: {str(e)}",
                exc_info=True,
            )
            return request.redirect("/scheme_list")

    # === NEW: Route to handle the update logic for a Scheme ===
    @http.route(
        "/scheme/update", type="http", auth="user", methods=["POST"], csrf=False
    )
    def update_scheme(self, **post):
        """Handles the update of an existing Scheme."""
        scheme_id = post.get("scheme_id")
        if not scheme_id:
            _logger.error("!!! Update failed: scheme_id not provided in POST data.")
            return request.redirect("/scheme_list")

        try:
            scheme = request.env["fund.scheme"].sudo().browse(int(scheme_id))
            if not scheme.exists():
                _logger.error(
                    f"!!! Update failed: Scheme with ID {scheme_id} not found."
                )
                return request.redirect("/scheme_list")

            vals = {
                "name": post.get("name"),
                "name_acronym": post.get("name_acronym"),
                "transaction_code": post.get("transaction_code"),
                "min_purchase_value": float(post.get("min_purchase_value", 0)),
                "min_sell_quantity": float(post.get("min_sell_quantity", 0)),
                "min_conversion_quantity": float(
                    post.get("min_conversion_quantity", 0)
                ),
                "min_holding_quantity": float(post.get("min_holding_quantity", 0)),
                "select_fund_id": (
                    int(post.get("select_fund_id"))
                    if post.get("select_fund_id")
                    else False
                ),
                "scheme_type_id": (
                    int(post.get("scheme_type_id"))
                    if post.get("scheme_type_id")
                    else False
                ),
                "amc_fee": float(post.get("amc_fee", 0)),
                "fund_fee": float(post.get("fund_fee", 0)),
                "active_status": post.get("active_status"),
                "can_purchase": post.get("can_purchase") == "on",
                "can_sell": post.get("can_sell") == "on",
                "can_convert": post.get("can_convert") == "on",
            }

            scheme.write(vals)
            _logger.info(f"Successfully updated scheme with ID: {scheme_id}")
            return request.redirect("/scheme_list")

        except Exception as e:
            _logger.error(
                f"!!! Error updating scheme ID {scheme_id}: {str(e)}", exc_info=True
            )
            return request.redirect(f"/scheme/edit/{scheme_id}")

    # === NEW: Route to handle delete logic for a Scheme ===
    @http.route(
        "/scheme/delete",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def delete_scheme(self, **kwargs):
        """API endpoint to delete a scheme."""
        try:
            data = json.loads(request.httprequest.data)
            scheme_id = data.get("id")

            if not scheme_id:
                return Response(
                    json.dumps({"success": False, "error": "ID không được cung cấp."}),
                    status=400,
                )

            scheme = request.env["fund.scheme"].sudo().browse(int(scheme_id))

            if not scheme.exists():
                return Response(
                    json.dumps({"success": False, "error": "Không tìm thấy bản ghi."}),
                    status=404,
                )

            scheme_name = scheme.name or f"ID {scheme_id}"
            scheme.unlink()

            _logger.info(f"Successfully deleted scheme: {scheme_name}")
            return Response(
                json.dumps(
                    {"success": True, "message": f"Đã xóa thành công {scheme_name}"}
                )
            )

        except Exception as e:
            _logger.error(f"!!! Error deleting scheme: {str(e)}", exc_info=True)
            return Response(
                json.dumps({"success": False, "error": f"Lỗi máy chủ: {str(e)}"}),
                status=500,
            )

    # Route của Biểu phí
    @http.route("/fee_schedule_list", type="http", auth="user", website=True)
    def fee_schedule_list_page(self, **kwargs):
        """Renders the page layout for the Fee Schedule list."""
        return request.render(
            "fund_management_control.fee_schedule_list", {"active_page": "fee_schedule"}
        )

    @http.route(
        "/get_fee_schedule_data",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    def get_fee_schedule_data(self, page=1, limit=10, search="", **kwargs):
        """
        API endpoint to fetch a paginated and searchable list of Fee Schedules.
        """
        _logger.info(
            f">>> API Fee Schedule called: page={page}, limit={limit}, search='{search}'"
        )
        try:
            domain = []
            if search:
                domain = [
                    "|",
                    ("fee_name", "ilike", search),
                    ("fee_code", "ilike", search),
                ]

            total_records = request.env["fund.fee.schedule"].search_count(domain)
            offset = (int(page) - 1) * int(limit)
            fees = request.env["fund.fee.schedule"].search(
                domain, limit=int(limit), offset=offset, order="fee_name asc"
            )

            data = []
            for f in fees:
                data.append(
                    {
                        "id": f.id,
                        "fee_name": f.fee_name or "",
                        "fee_code": f.fee_code or "",
                        "scheme_name": f.scheme_id.name or "N/A",
                        "initial_value": f.initial_value,
                        "end_value": f.end_value,
                        "fee_type": dict(f._fields["fee_type"].selection).get(
                            f.fee_type, ""
                        ),
                        "fee_rate": f.fee_rate,
                        "activate": f.activate,
                    }
                )

            response_data = {"records": data, "total_records": total_records}
            return Response(json.dumps(response_data), content_type="application/json")
        except Exception as e:
            _logger.error(
                f"!!! Error in /get_fee_schedule_data: {str(e)}", exc_info=True
            )
            return Response(
                json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500,
            )

    @http.route("/fee_schedule/new", type="http", auth="user", website=True)
    def fee_schedule_form_page(self, **kwargs):
        """Renders the form to create a new Fee Schedule."""
        schemes = request.env["fund.scheme"].search([])
        FeeSchedule = request.env["fund.fee.schedule"]

        render_values = {
            "schemes": schemes,
            "fee_types": FeeSchedule._fields["fee_type"].selection,
            "operators": FeeSchedule._fields[
                "operator_1"
            ].selection,  # Giả sử operator_1 và 2 giống nhau
            "active_page": "fee_schedule",
        }
        return request.render(
            "fund_management_control.fee_schedule_form", render_values
        )

    @http.route(
        "/fee_schedule/create",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def create_fee_schedule(self, **post):
        """Handles the creation of a new Fee Schedule."""
        try:
            _logger.info("Received data for new fee schedule: %s", post)
            vals = {
                "fee_name": post.get("fee_name"),
                "fee_code": post.get("fee_code"),
                "fee_type": post.get("fee_type"),
                "scheme_id": (
                    int(post.get("scheme_id")) if post.get("scheme_id") else False
                ),
                "operator_1": post.get("operator_1"),
                "initial_value": float(post.get("initial_value", 0)),
                "operator_2": post.get("operator_2"),
                "end_value": post.get("end_value"),
                "fee_rate": float(post.get("fee_rate", 0)),
                "activate": post.get("activate") == "on",
            }
            request.env["fund.fee.schedule"].sudo().create(vals)
            return request.redirect("/fee_schedule_list")
        except Exception as e:
            _logger.error("!!! Error creating fee schedule: %s", str(e), exc_info=True)
            return request.redirect("/fee_schedule_list")

    # === NEW: Route to render the edit form for Fee Schedule ===
    @http.route(
        "/fee_schedule/edit/<int:fee_id>", type="http", auth="user", website=True
    )
    def fee_schedule_edit_page(self, fee_id, **kwargs):
        """Renders the page to edit an existing Fee Schedule."""
        try:
            fee = request.env["fund.fee.schedule"].sudo().browse(fee_id)
            if not fee.exists():
                _logger.warning(
                    f"Attempted to edit non-existent fee schedule with ID: {fee_id}"
                )
                return request.redirect("/fee_schedule_list")

            schemes = request.env["fund.scheme"].search([])
            FeeSchedule = request.env["fund.fee.schedule"]

            render_values = {
                "fee": fee,
                "schemes": schemes,
                "fee_types": FeeSchedule._fields["fee_type"].selection,
                "operators": FeeSchedule._fields["operator_1"].selection,
                "active_page": "fee_schedule",
            }

            return request.render(
                "fund_management_control.fee_schedule_edit_form", render_values
            )
        except Exception as e:
            _logger.error(
                f"!!! Error rendering edit page for fee schedule ID {fee_id}: {str(e)}",
                exc_info=True,
            )
            return request.redirect("/fee_schedule_list")

    # === NEW: Route to handle the update logic for Fee Schedule ===
    @http.route(
        "/fee_schedule/update", type="http", auth="user", methods=["POST"], csrf=False
    )
    def update_fee_schedule(self, **post):
        """Handles the update of an existing Fee Schedule."""
        fee_id = post.get("fee_id")
        if not fee_id:
            _logger.error("!!! Update failed: fee_id not provided in POST data.")
            return request.redirect("/fee_schedule_list")

        try:
            fee = request.env["fund.fee.schedule"].sudo().browse(int(fee_id))
            if not fee.exists():
                _logger.error(
                    f"!!! Update failed: Fee Schedule with ID {fee_id} not found."
                )
                return request.redirect("/fee_schedule_list")

            vals = {
                "fee_name": post.get("fee_name"),
                "fee_code": post.get("fee_code"),
                "fee_type": post.get("fee_type"),
                "scheme_id": (
                    int(post.get("scheme_id")) if post.get("scheme_id") else False
                ),
                "operator_1": post.get("operator_1"),
                "initial_value": float(post.get("initial_value", 0)),
                "operator_2": post.get("operator_2"),
                "end_value": post.get("end_value"),
                "fee_rate": float(post.get("fee_rate", 0)),
                "activate": post.get("activate") == "on",
            }

            fee.write(vals)
            _logger.info(f"Successfully updated fee schedule with ID: {fee_id}")
            return request.redirect("/fee_schedule_list")

        except Exception as e:
            _logger.error(
                f"!!! Error updating fee schedule ID {fee_id}: {str(e)}", exc_info=True
            )
            return request.redirect(f"/fee_schedule/edit/{fee_id}")

    # === NEW: Route to handle delete logic for Fee Schedule ===
    @http.route(
        "/fee_schedule/delete",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def delete_fee_schedule(self, **kwargs):
        """API endpoint to delete a fee schedule."""
        try:
            data = json.loads(request.httprequest.data)
            fee_id = data.get("id")

            if not fee_id:
                return Response(
                    json.dumps({"success": False, "error": "ID không được cung cấp."}),
                    status=400,
                )

            fee = request.env["fund.fee.schedule"].sudo().browse(int(fee_id))

            if not fee.exists():
                return Response(
                    json.dumps({"success": False, "error": "Không tìm thấy bản ghi."}),
                    status=404,
                )

            fee_name = fee.fee_name or f"ID {fee_id}"
            fee.unlink()

            _logger.info(f"Successfully deleted fee schedule: {fee_name}")
            return Response(
                json.dumps(
                    {"success": True, "message": f"Đã xóa thành công {fee_name}"}
                )
            )

        except Exception as e:
            _logger.error(f"!!! Error deleting fee schedule: {str(e)}", exc_info=True)
            return Response(
                json.dumps({"success": False, "error": f"Lỗi máy chủ: {str(e)}"}),
                status=500,
            )

    # Route của Cài đặt SIP
    @http.route("/sip_settings_list", type="http", auth="user", website=True)
    def sip_settings_list_page(self, **kwargs):
        """Renders the page layout for the SIP Settings list."""
        return request.render(
            "fund_management_control.sip_settings_list", {"active_page": "sip_settings"}
        )

    @http.route(
        "/get_sip_settings_data",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    def get_sip_settings_data(self, page=1, limit=10, search="", **kwargs):
        """
        API endpoint to fetch a paginated and searchable list of SIP Settings.
        """
        _logger.info(
            f">>> API SIP Settings called: page={page}, limit={limit}, search='{search}'"
        )
        try:
            domain = []
            # Searching by the related scheme name
            if search:
                domain = [("sip_scheme_id.name", "ilike", search)]

            total_records = request.env["fund.sip.settings"].search_count(domain)
            offset = (int(page) - 1) * int(limit)
            sip_settings = request.env["fund.sip.settings"].search(
                domain, limit=int(limit), offset=offset
            )

            data = []
            for s in sip_settings:
                data.append(
                    {
                        "id": s.id,
                        "sip_scheme_name": s.sip_scheme_id.name or "N/A",
                        "max_non_consecutive_periods": s.max_non_consecutive_periods,
                        "min_monthly_amount": s.min_monthly_amount,
                        "min_maintenance_periods": s.min_maintenance_periods,
                        "cycle_code": s.cycle_code or "",
                        "allow_multiple_investments": s.allow_multiple_investments,
                        "active": s.active,
                    }
                )

            response_data = {"records": data, "total_records": total_records}
            return Response(json.dumps(response_data), content_type="application/json")
        except Exception as e:
            _logger.error(
                f"!!! Error in /get_sip_settings_data: {str(e)}", exc_info=True
            )
            return Response(
                json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500,
            )

    @http.route("/sip_settings/new", type="http", auth="user", website=True)
    def sip_settings_form_page(self, **kwargs):
        """Renders the form to create a new SIP Setting."""
        # <<< SỬA LỖI: Bỏ điều kiện lọc theo tên 'SIP' để lấy tất cả các chương trình >>>
        # Bạn có thể thêm các bộ lọc khác nếu cần, ví dụ: lọc các chương trình đang hoạt động
        # schemes = request.env['fund.scheme'].search([('active_status', '=', 'active')])
        schemes = request.env["fund.scheme"].search([])
        SipSettings = request.env["fund.sip.settings"]

        render_values = {
            "schemes": schemes,
            "program_periods": SipSettings._fields["program_period"].selection,
            "active_page": "sip_settings",
        }
        return request.render(
            "fund_management_control.sip_settings_form", render_values
        )

    @http.route(
        "/sip_settings/create",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def create_sip_setting(self, **post):
        """Handles the creation of a new SIP Setting."""
        try:
            _logger.info("Received data for new SIP setting: %s", post)
            vals = {
                "sip_scheme_id": (
                    int(post.get("sip_scheme_id"))
                    if post.get("sip_scheme_id")
                    else False
                ),
                "max_non_consecutive_periods": int(
                    post.get("max_non_consecutive_periods", 0)
                ),
                "min_monthly_amount": float(post.get("min_monthly_amount", 0)),
                "min_maintenance_periods": int(post.get("min_maintenance_periods", 0)),
                "cycle_code": post.get("cycle_code"),
                "program_period": post.get("program_period"),
                "allow_multiple_investments": post.get("allow_multiple_investments")
                == "on",
                "active": post.get("active") == "on",
            }
            request.env["fund.sip.settings"].sudo().create(vals)
            return request.redirect("/sip_settings_list")
        except Exception as e:
            _logger.error("!!! Error creating SIP setting: %s", str(e), exc_info=True)
            return request.redirect("/sip_settings_list")

    # === NEW: Route to render the edit form for SIP Settings ===
    @http.route(
        "/sip_settings/edit/<int:setting_id>", type="http", auth="user", website=True
    )
    def sip_settings_edit_page(self, setting_id, **kwargs):
        """Renders the page to edit an existing SIP Setting."""
        try:
            setting = request.env["fund.sip.settings"].sudo().browse(setting_id)
            if not setting.exists():
                _logger.warning(
                    f"Attempted to edit non-existent SIP setting with ID: {setting_id}"
                )
                return request.redirect("/sip_settings_list")

            schemes = request.env["fund.scheme"].search([])
            SipSettings = request.env["fund.sip.settings"]

            render_values = {
                "setting": setting,
                "schemes": schemes,
                "program_periods": SipSettings._fields["program_period"].selection,
                "active_page": "sip_settings",
            }

            return request.render(
                "fund_management_control.sip_settings_edit_form", render_values
            )
        except Exception as e:
            _logger.error(
                f"!!! Error rendering edit page for SIP setting ID {setting_id}: {str(e)}",
                exc_info=True,
            )
            return request.redirect("/sip_settings_list")

    # === NEW: Route to handle the update logic for SIP Settings ===
    @http.route(
        "/sip_settings/update", type="http", auth="user", methods=["POST"], csrf=False
    )
    def update_sip_setting(self, **post):
        """Handles the update of an existing SIP Setting."""
        setting_id = post.get("setting_id")
        if not setting_id:
            _logger.error("!!! Update failed: setting_id not provided in POST data.")
            return request.redirect("/sip_settings_list")

        try:
            setting = request.env["fund.sip.settings"].sudo().browse(int(setting_id))
            if not setting.exists():
                _logger.error(
                    f"!!! Update failed: SIP Setting with ID {setting_id} not found."
                )
                return request.redirect("/sip_settings_list")

            vals = {
                "sip_scheme_id": (
                    int(post.get("sip_scheme_id"))
                    if post.get("sip_scheme_id")
                    else False
                ),
                "max_non_consecutive_periods": int(
                    post.get("max_non_consecutive_periods", 0)
                ),
                "min_monthly_amount": float(post.get("min_monthly_amount", 0)),
                "min_maintenance_periods": int(post.get("min_maintenance_periods", 0)),
                "cycle_code": post.get("cycle_code"),
                "program_period": post.get("program_period"),
                "allow_multiple_investments": post.get("allow_multiple_investments")
                == "on",
                "active": post.get("active") == "on",
            }

            setting.write(vals)
            _logger.info(f"Successfully updated SIP setting with ID: {setting_id}")
            return request.redirect("/sip_settings_list")

        except Exception as e:
            _logger.error(
                f"!!! Error updating SIP setting ID {setting_id}: {str(e)}",
                exc_info=True,
            )
            return request.redirect(f"/sip_settings/edit/{setting_id}")

    # === NEW: Route to handle delete logic for SIP Settings ===
    @http.route(
        "/sip_settings/delete",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def delete_sip_setting(self, **kwargs):
        """API endpoint to delete a SIP setting."""
        try:
            data = json.loads(request.httprequest.data)
            setting_id = data.get("id")

            if not setting_id:
                return Response(
                    json.dumps({"success": False, "error": "ID không được cung cấp."}),
                    status=400,
                )

            setting = request.env["fund.sip.settings"].sudo().browse(int(setting_id))

            if not setting.exists():
                return Response(
                    json.dumps({"success": False, "error": "Không tìm thấy bản ghi."}),
                    status=404,
                )

            # Lấy tên để hiển thị trong thông báo
            setting_name = setting.sip_scheme_id.name or f"ID {setting_id}"
            setting.unlink()

            _logger.info(f"Successfully deleted SIP setting: {setting_name}")
            return Response(
                json.dumps(
                    {
                        "success": True,
                        "message": f'Đã xóa thành công Cài đặt SIP cho chương trình "{setting_name}"',
                    }
                )
            )

        except Exception as e:
            _logger.error(f"!!! Error deleting SIP setting: {str(e)}", exc_info=True)
            return Response(
                json.dumps({"success": False, "error": f"Lỗi máy chủ: {str(e)}"}),
                status=500,
            )

    # Route của cài đặt thuế
    @http.route("/tax_settings_list", type="http", auth="user", website=True)
    def tax_settings_list_page(self, **kwargs):
        """Renders the page layout for the Tax Settings list."""
        return request.render(
            "fund_management_control.tax_settings_list", {"active_page": "tax_settings"}
        )

    @http.route(
        "/get_tax_settings_data",
        type="http",
        auth="user",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    def get_tax_settings_data(
        self,
        page=1,
        limit=10,
        search="",
        filter="",
        sort="tax_name",
        order="asc",
        **kwargs,
    ):
        """
        API endpoint to fetch a paginated and searchable list of Tax Settings.
        """
        _logger.info(
            f">>> API Tax Settings called: page={page}, limit={limit}, search='{search}', filter='{filter}'"
        )
        try:
            domain = []
            if search:
                domain.extend(
                    ["|", ("tax_name", "ilike", search), ("tax_code", "ilike", search)]
                )

            # Add filtering logic for 'active' status
            if filter == "active":
                domain.append(("active", "=", True))
            elif filter == "inactive":
                domain.append(("active", "=", False))

            # Validate sort and order parameters to prevent injection
            order_string = (
                f"{sort} {order}" if order in ["asc", "desc"] else "tax_name asc"
            )

            # --- FIX: Add with_context to ignore default active=True filter ---
            Model = request.env["fund.tax.settings"].with_context(active_test=False)

            total_records = Model.search_count(domain)
            offset = (int(page) - 1) * int(limit)
            tax_settings = Model.search(
                domain, limit=int(limit), offset=offset, order=order_string
            )

            data = []
            for t in tax_settings:
                data.append(
                    {
                        "id": t.id,
                        "tax_name": t.tax_name or "",
                        "tax_english_name": t.tax_english_name or "",
                        "tax_code": t.tax_code or "",
                        "rate": t.rate,
                        "active": t.active,  # This field is crucial for the frontend
                    }
                )

            response_data = {"records": data, "total_records": total_records}
            return Response(json.dumps(response_data), content_type="application/json")

        except Exception as e:
            _logger.error(
                f"!!! Error in /get_tax_settings_data: {str(e)}", exc_info=True
            )
            return Response(
                json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500,
            )

    @http.route("/tax_settings/new", type="http", auth="user", website=True)
    def tax_settings_form_page(self, **kwargs):
        """Renders the form to create a new Tax Setting."""
        return request.render(
            "fund_management_control.tax_settings_form", {"active_page": "tax_settings"}
        )

    @http.route(
        "/tax_settings/create",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def create_tax_setting(self, **post):
        """Handles the creation of a new Tax Setting."""
        try:
            _logger.info("Received data for new tax setting: %s", post)
            vals = {
                "tax_name": post.get("tax_name"),
                "tax_english_name": post.get("tax_english_name"),
                "tax_code": post.get("tax_code"),
                "rate": float(post.get("rate", 0)),
                "active": post.get("active") == "on",
            }
            request.env["fund.tax.settings"].sudo().create(vals)
            return request.redirect("/tax_settings_list")
        except Exception as e:
            _logger.error("!!! Error creating tax setting: %s", str(e), exc_info=True)
            return request.redirect("/tax_settings_list")

    @http.route(
        "/tax_settings/edit/<int:tax_id>", type="http", auth="user", website=True
    )
    def tax_settings_edit_page(self, tax_id, **kwargs):
        """Renders the page to edit an existing Tax Setting."""
        try:
            # --- FIX: Add with_context to ensure inactive records can be fetched for editing ---
            tax_setting = (
                request.env["fund.tax.settings"]
                .with_context(active_test=False)
                .sudo()
                .browse(tax_id)
            )
            if not tax_setting.exists():
                _logger.warning(
                    f"Attempted to edit non-existent tax setting with ID: {tax_id}"
                )
                return request.redirect("/tax_settings_list")

            render_values = {
                "tax": tax_setting,
                "active_page": "tax_settings",
            }
            return request.render(
                "fund_management_control.tax_settings_edit_form", render_values
            )
        except Exception as e:
            _logger.error(
                f"!!! Error rendering edit page for tax setting ID {tax_id}: {str(e)}",
                exc_info=True,
            )
            return request.redirect("/tax_settings_list")

    @http.route(
        "/tax_settings/update", type="http", auth="user", methods=["POST"], csrf=False
    )
    def update_tax_setting(self, **post):
        """Handles the update of an existing Tax Setting."""
        tax_id = post.get("tax_id")
        if not tax_id:
            _logger.error("!!! Update failed: tax_id not provided in POST data.")
            return request.redirect("/tax_settings_list")

        try:
            # --- FIX: Add with_context to ensure inactive records can be found for update ---
            tax_setting = (
                request.env["fund.tax.settings"]
                .with_context(active_test=False)
                .sudo()
                .browse(int(tax_id))
            )
            if not tax_setting.exists():
                _logger.error(
                    f"!!! Update failed: Tax setting with ID {tax_id} not found."
                )
                return request.redirect("/tax_settings_list")

            vals = {
                "tax_name": post.get("tax_name"),
                "tax_english_name": post.get("tax_english_name"),
                "tax_code": post.get("tax_code"),
                "rate": float(post.get("rate", 0)),
                "active": post.get("active") == "on",
            }

            tax_setting.write(vals)
            _logger.info(f"Successfully updated tax setting with ID: {tax_id}")
            return request.redirect("/tax_settings_list")

        except Exception as e:
            _logger.error(
                f"!!! Error updating tax setting ID {tax_id}: {str(e)}", exc_info=True
            )
            return request.redirect(f"/tax_settings/edit/{tax_id}")

    @http.route(
        "/tax_settings/delete",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def delete_tax_setting(self, **kwargs):
        """API endpoint to delete a tax setting."""
        try:
            data = json.loads(request.httprequest.data)
            tax_id = data.get("id")

            if not tax_id:
                return Response(
                    json.dumps({"success": False, "error": "ID không được cung cấp."}),
                    status=400,
                )

            # --- FIX: Add with_context to ensure inactive records can be found for deletion ---
            tax_setting = (
                request.env["fund.tax.settings"]
                .with_context(active_test=False)
                .sudo()
                .browse(int(tax_id))
            )

            if not tax_setting.exists():
                return Response(
                    json.dumps({"success": False, "error": "Không tìm thấy bản ghi."}),
                    status=404,
                )

            tax_name = tax_setting.tax_name or f"ID {tax_id}"
            tax_setting.unlink()

            _logger.info(f"Successfully deleted tax setting: {tax_name}")
            return Response(
                json.dumps(
                    {"success": True, "message": f"Đã xóa thành công {tax_name}"}
                )
            )

        except Exception as e:
            _logger.error(f"!!! Error deleting tax setting: {str(e)}", exc_info=True)
            return Response(
                json.dumps({"success": False, "error": f"Lỗi máy chủ: {str(e)}"}),
                status=500,
            )
