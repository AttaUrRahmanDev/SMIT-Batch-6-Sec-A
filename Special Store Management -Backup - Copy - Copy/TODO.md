# TODO - Customer/Supplier Dues + Smart Exports + Email Reminders

## Completed
- [x] POS: load existing customers by `customer_number` and provide dropdown (existing or new) in POS UI.
- [x] Navbar access points: Customer Dues + Supplier Dues.
- [x] Admin Dashboard basic KPI + products table.
- [x] Cashier Dashboard (last 20 sales) page + route.
- [x] Admin Dashboard advanced interactive filters + KPI Excel/PDF exports.
- [x] Dashboard UI enhancements (background + glass style) via `templates/base.html`.
- [x] Customer/Purchase/Dues/Sales templates upgraded to advanced interactive UI.

## Next (to implement)
- [ ] Remaining payments (dues) system
  - [x] Add DB tables for customer ledger + supplier ledger
  - [x] Admin pages to manage dues (view + record payment/settle)
  - [x] Excel/PDF exports for dues (ALL-export)
  - [x] Customer/Supplier list pages upgraded with due tables
  - [ ] Email reminders to customers/suppliers with due balances
    - [ ] Add `Customer.email` + `Supplier.email` columns (migration)
    - [ ] Update customer/supplier add/edit forms to capture email
    - [ ] Admin manual reminder buttons (send for all open dues)
    - [ ] Scheduled reminder script (send only overdue: `due_date <= now`)
    - [ ] Script uses existing SMTP env vars: `EMAIL_USER`, `EMAIL_PASSWORD`, optional `SMTP_SERVER`, `SMTP_PORT`
    - [ ] Ensure reminders do not crash if email missing (skip + log)
- [ ] Ensure existing system remains unchanged (sales/purchases/receipts/POS checkout)

