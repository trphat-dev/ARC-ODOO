#!/bin/bash
# Run Odoo unit tests for ARC-FMS modules
cd /

python3 /usr/bin/odoo \
    -d ARC-v1 \
    -u custom_auth,fund_management,order_matching \
    --test-enable \
    --test-tags=custom_auth,fund_management,order_matching \
    --stop-after-init \
    --xmlrpc-port=8099 \
    --log-level=test \
    --db_host=db \
    --db_user=odoo \
    --db_password=odoo18@2024 \
    --addons-path=/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons \
    --logfile=/tmp/odoo_test.log

EXIT_CODE=$?
echo "===== TEST RESULT ====="
echo "Exit code: $EXIT_CODE"
echo ""
echo "--- Test lines ---"
grep -iE 'test_|FAIL|ERROR|Running|ok|Ran ' /tmp/odoo_test.log 2>/dev/null | tail -40
echo ""
echo "--- Last 20 lines ---"
tail -20 /tmp/odoo_test.log
echo ""
echo "--- Total lines ---"
wc -l /tmp/odoo_test.log
