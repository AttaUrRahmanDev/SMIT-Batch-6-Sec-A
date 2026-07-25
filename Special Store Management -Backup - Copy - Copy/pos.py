import sys
from flask import Blueprint, render_template, render_template_string, redirect, url_for, request, flash, session, jsonify, send_file, abort
from functools import wraps
from werkzeug.security import check_password_hash
from io import BytesIO

pos_bp = Blueprint('pos', __name__)

def get_app_module():
    return sys.modules.get('app') or sys.modules.get('__main__')


def get_model(name):
    app_module = get_app_module()
    if app_module is None:
        import app as app_module
    return getattr(app_module, name)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        Store = get_model('Store')

        store_id = session.get('store_id')
        if not store_id:
            flash('🔒 Please login first!')
            return redirect(url_for('login'))

        store = Store.query.get(store_id)
        if not store:
            session.clear()
            flash('❌ Store not found. Please login again.')
            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated_function


@pos_bp.route('/pos')
@login_required
def pos_dashboard():
    Store = get_model('Store')

    store = Store.query.get(session['store_id'])
    customers = store.customers if store else []
    return render_template('pos.html', store=store, customers=customers)



@pos_bp.route('/cashier/login', methods=['GET', 'POST'])
def cashier_login():
    Cashier = get_model('Cashier')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cashier = Cashier.query.filter_by(username=username).first()

        if cashier and check_password_hash(cashier.password_hash, password):
            session.clear()
            session['cashier_id'] = cashier.id
            session['store_id'] = cashier.store_id
            session['role'] = 'cashier'
            session['cashier_name'] = cashier.name

            flash('✅ Cashier login successful')
            return redirect(url_for('pos.pos_dashboard'))

        flash('❌ Invalid cashier credentials')

    return render_template('cashier_login.html')


@pos_bp.route('/cashier/logout')
def cashier_logout():
    session.clear()
    flash('Logged out')
    return redirect(url_for('pos.cashier_login'))


@pos_bp.route('/pos/products', methods=['GET'])
@login_required
def get_products():
    Product = get_model('Product')

    store_id = session.get('store_id')
    query = request.args.get('q', '').strip()
    products = Product.query.filter_by(store_id=store_id)

    if query:
        products = products.filter(
            (Product.name.ilike(f'%{query}%')) |
            (Product.product_code.ilike(f'%{query}%')) |
            (Product.imei.ilike(f'%{query}%'))
        )

    products = products.order_by(Product.id.desc()).limit(80).all()

    return jsonify({
        'products': [
            {
                'id': product.id,
                'code': product.product_code,
                'name': product.name,
                'price': product.sell_price,
                'stock': product.calculated_stock,
                'category': product.category or 'General'
            }
            for product in products
        ]
    })


@pos_bp.route('/pos/search', methods=['GET'])
@login_required
def search_products():
    Product = get_model('Product')

    query = request.args.get('q', '').strip()
    store_id = session.get('store_id')
    if not query:
        return jsonify({'products': []})

    products = Product.query.filter(
        Product.store_id == store_id,
        (Product.name.ilike(f'%{query}%')) |
        (Product.product_code.ilike(f'%{query}%')) |
        (Product.imei.ilike(f'%{query}%'))
    ).limit(40).all()

    return jsonify({
        'products': [
            {
                'id': product.id,
                'code': product.product_code,
                'name': product.name,
                'price': product.sell_price,
                'stock': product.calculated_stock,
                'category': product.category or 'General'
            }
            for product in products
        ]
    })


@pos_bp.route('/pos/add-to-cart', methods=['POST'])
@login_required
def add_to_cart():
    Product = get_model('Product')

    payload = request.get_json(silent=True) or request.form
    code = payload.get('code') or payload.get('product_code')
    quantity = payload.get('quantity') or payload.get('qty') or 1
    discount = payload.get('discount') or 0

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        quantity = 1

    try:
        discount = float(discount)
    except (TypeError, ValueError):
        discount = 0.0

    if quantity < 1:
        quantity = 1
    if discount < 0:
        discount = 0.0
    if discount > 100:
        discount = 100.0

    if not code:
        return jsonify({'error': 'Product code or IMEI is required'}), 400

    product = Product.query.filter(
        Product.store_id == session.get('store_id'),
        (Product.product_code == code) | (Product.imei == code)
    ).first()
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    if product.calculated_stock < quantity:
        return jsonify({'error': f'Not enough stock for {product.name}'}), 400

    cart = session.get('cart', {})
    item = cart.get(str(product.id), {
        'type': 'product',
        'code': product.product_code,
        'name': product.name,
        'price': product.sell_price,
        'qty': 0,
        'discount': discount
    })
    item['qty'] += quantity
    item['discount'] = discount
    cart[str(product.id)] = item
    session['cart'] = cart

    return jsonify({
        'success': True,
        'product_name': product.name,
        'quantity': quantity,
        'cart': cart
    })


@pos_bp.route('/pos/cart', methods=['GET'])
@login_required
def get_cart():
    cart = session.get('cart', {})
    items = []
    total = 0.0

    for pid, item in cart.items():
        discount_pct = float(item.get('discount', 0) or 0)
        unit_price = float(item['price'])
        discounted_price = unit_price * (1 - discount_pct / 100)
        subtotal = discounted_price * item['qty']
        total += subtotal
        cart_key = pid
        underlying_pid = item.get('product_id')

        # product lines use numeric key (product id as string), device lines use `device:<id>`
        try:
            numeric_id = int(cart_key)
        except (TypeError, ValueError):
            numeric_id = None

        product_id = None
        if underlying_pid is not None:
            try:
                product_id = int(underlying_pid)
            except (TypeError, ValueError):
                product_id = None
        elif numeric_id is not None:
            product_id = numeric_id

        items.append({
            'cart_key': str(cart_key),
            # keep legacy fields for existing UI
            'id': numeric_id if numeric_id is not None else None,
            'type': item.get('type', 'product'),
            'product_id': product_id,
            'device_id': item.get('device_id'),
            'imei': item.get('imei'),
            'product_code': item.get('code'),
            'product_name': item.get('name'),
            'quantity': item.get('qty'),
            'unit_price': unit_price,
            'discount': discount_pct,
            'discounted_price': round(discounted_price, 2),
            'total': round(subtotal, 2)
        })


    return jsonify({
        'items': items,
        'total': round(total, 2),
        'count': len(items)
    })


@pos_bp.route('/pos/cart/update/<cart_key>', methods=['POST'])
@login_required
def update_cart_item(cart_key):

    cart = session.get('cart', {})
    payload = request.get_json(silent=True) or request.form

    qty = payload.get('quantity') or payload.get('qty')
    discount = payload.get('discount')

    try:
        qty = int(qty)
    except (TypeError, ValueError):
        qty = None

    try:
        discount = float(discount)
    except (TypeError, ValueError):
        discount = None

    item = cart.get(str(cart_key))

    if not item:
        return jsonify({'error': 'Cart item not found'}), 404

    if qty is not None:
        if qty < 1:
            qty = 1
        item['qty'] = qty

    if discount is not None:
        if discount < 0:
            discount = 0.0
        if discount > 100:
            discount = 100.0
        item['discount'] = discount

    cart[str(cart_key)] = item

    session['cart'] = cart
    return jsonify({'success': True, 'item': item})


@pos_bp.route('/pos/cart/remove/<cart_key>', methods=['POST'])
@login_required
def remove_from_cart(cart_key):

    cart = session.get('cart', {})
    cart.pop(str(cart_key), None)

    session['cart'] = cart
    return jsonify({'success': True})


@pos_bp.route('/pos/cart/clear', methods=['POST'])
@login_required
def clear_cart():
    session['cart'] = {}
    return jsonify({'success': True})


@pos_bp.route('/pos/customer/lookup', methods=['GET'])
@login_required
def customer_lookup():
    Customer = get_model('Customer')

    store_id = session.get('store_id')
    customer_number = (request.args.get('customer_number') or '').strip()

    if not customer_number:
        return jsonify({'error': 'customer_number is required'}), 400

    customer = Customer.query.filter_by(
        customer_number=customer_number,
        store_id=store_id
    ).first()

    if not customer:
        return jsonify({'found': False})

    return jsonify({
        'found': True,
        'id': customer.id,
        'name': customer.name,
        'customer_number': customer.customer_number
    })


@pos_bp.route('/pos/checkout', methods=['POST'])
@login_required
def checkout():

    Store = get_model('Store')
    Customer = get_model('Customer')
    Product = get_model('Product')
    Sale = get_model('Sale')
    DeviceInventory = get_model('DeviceInventory')
    db = get_model('db')

    store = Store.query.get(session['store_id'])
    cart = session.get('cart', {})

    if not cart:
        return jsonify({'error': 'Cart is empty'}), 400

    data = request.get_json(silent=True) or request.form
    customer_name = data.get('customer_name', 'Walk-in')
    customer_number = data.get('customer_number', '')
    payment_method = data.get('payment_method', 'cash')

    customer = None
    if customer_number:
        customer = Customer.query.filter_by(
            customer_number=customer_number,
            store_id=store.id
        ).first()

    if not customer:
        customer = Customer(
            name=customer_name or 'Walk-in',
            customer_number=customer_number,
            store_id=store.id
        )
        db.session.add(customer)
        db.session.flush()

    # validate
    for _cart_key, item in cart.items():
        item_type = item.get('type', 'product')

        if item_type == 'device':
            device_id = item.get('device_id')
            if not device_id:
                return jsonify({'error': 'Device cart item missing device_id'}), 400

            device = DeviceInventory.query.get(int(device_id))
            if not device or getattr(device, 'status', None) == 'sold':
                return jsonify({'error': 'Device not available (already sold or not found)'}), 400

            product_id = item.get('product_id')
            product = Product.query.get(int(product_id)) if product_id else None
            if not product:
                return jsonify({'error': 'Underlying product not found for device'}), 404
            # IMPORTANT: product.calculated_stock should be decremented for device sale too
            if product.calculated_stock < item['qty']:
                return jsonify({'error': f'Not enough stock for {product.name}'}), 400
            
        else:
            # normal product line: cart key is product id
            pid = _cart_key
            product = Product.query.get(int(pid))
            if not product:
                return jsonify({'error': f'Product with id {pid} not found'}), 404
            if product.calculated_stock < item['qty']:
                return jsonify({'error': f'Not enough stock for {product.name}'}), 400

    sale_ids = []
    for _cart_key, item in cart.items():
        item_type = item.get('type', 'product')
        discount_pct = float(item.get('discount', 0) or 0)
        selling_price = float(item['price']) * (1 - discount_pct / 100)

        if item_type == 'device':
            device = DeviceInventory.query.get(int(item['device_id']))
            if not device or getattr(device, 'status', None) == 'sold':
                return jsonify({'error': 'Device not available (already sold or not found)'}), 400

            product = Product.query.get(int(item.get('product_id'))) 
            if not product:
                return jsonify({'error': 'Underlying product not found for device'}), 404

            # Create Sale for underlying product
            sale = Sale(
                product_id=product.id,
                customer_id=customer.id,
                customer_name=customer.name,
                customer_number=customer.customer_number,
                quantity=item['qty'],
                selling_price=round(selling_price, 2),
                discount=discount_pct,
                profit=round((selling_price - (device.cost_price or 0)) * item['qty'], 2),
                payment_method=payment_method,
                store_id=store.id
            )
            db.session.add(sale)
            db.session.flush()
            sale_ids.append(sale.id)

            # Mark device sold
            device.status = 'sold'
            device.customer_id = customer.id
            # increase sold count
            product.sold = (product.sold or 0) + item['qty']

        else:
            # existing behavior for product cart lines
            product = Product.query.get(int(_cart_key))
            # product.stock -= item['qty']
            if not product:
                return jsonify({'error': f'Product not found'}), 404

             # increase sold count
            product.sold = (product.sold or 0) + item['qty']


            sale = Sale(
                product_id=product.id,
                customer_id=customer.id,
                customer_name=customer.name,
                customer_number=customer.customer_number,
                quantity=item['qty'],
                selling_price=round(selling_price, 2),
                discount=discount_pct,
                profit=round((selling_price - product.buy_price) * item['qty'], 2),
                payment_method=payment_method,
                store_id=store.id
            )
            db.session.add(sale)
            db.session.flush()
            sale_ids.append(sale.id)

    db.session.commit()
    session['cart'] = {}

    return jsonify({'success': True, 'sale_id': sale_ids[-1], 'payment_method': payment_method})


@pos_bp.route('/pos/product/<int:id>/qr-preview', methods=['GET'])
@login_required
def product_qr_page(id):
    Product = get_model('Product')
    product = Product.query.get_or_404(id)
    if product.store_id != session.get('store_id'):
        abort(404)
    return render_template('product_qr.html', product=product, code=product.product_code)


@pos_bp.route('/pos/product-qr', methods=['GET'])
@login_required
def product_qr_generator():
    Product = get_model('Product')
    code = request.args.get('code', '').strip()
    product = None
    if code:
        product = Product.query.filter(
            Product.store_id == session.get('store_id'),
            (Product.product_code == code) | (Product.imei == code)
        ).first()
    return render_template('product_qr.html', product=product, code=code)


@pos_bp.route('/product/<int:id>/qr', methods=['GET'])
def product_qr(id):
    Product = get_model('Product')
    import qrcode

    product = Product.query.get_or_404(id)
    qr = qrcode.make(product.product_code)
    buf = BytesIO()
    qr.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@pos_bp.route('/product/<int:id>/qr-add', methods=['GET'])
def product_qr_add(id):
    Product = get_model('Product')
    import qrcode

    product = Product.query.get_or_404(id)
    # Build an absolute URL that, when opened, will add this product to the cart for the product's store
    add_url = url_for('pos.qr_add', store=product.store_id, code=(product.imei or product.product_code), _external=True)
    qr = qrcode.make(add_url)
    buf = BytesIO()
    qr.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@pos_bp.route('/pos/qr-add', methods=['GET'])
def qr_add():
    Product = get_model('Product')

    code = request.args.get('code')
    store_id = request.args.get('store')
    if not code or not store_id:
        return render_template_string('<p>Missing code or store parameter.</p>'), 400

    try:
        store_id_int = int(store_id)
    except (TypeError, ValueError):
        return render_template_string('<p>Invalid store id.</p>'), 400

    product = Product.query.filter(
        Product.store_id == store_id_int,
        (Product.product_code == code) | (Product.imei == code)
    ).first()

    if not product:
        return render_template_string('<p>Product not found.</p>'), 404

    # ensure session points to this store so cart and other flows work
    session['store_id'] = store_id_int

    # add one quantity to cart
    cart = session.get('cart', {})
    item = cart.get(str(product.id), {
        'code': product.product_code,
        'name': product.name,
        'price': product.sell_price,
        'qty': 0,
        'discount': 0
    })
    item['qty'] = item.get('qty', 0) + 1
    cart[str(product.id)] = item
    session['cart'] = cart

    pos_url = url_for('pos.pos_dashboard', _external=True)
    # small confirmation page with redirect back to POS dashboard
    html = f"""
    <html><head>
      <meta http-equiv="refresh" content="2;url={pos_url}">
      <title>Added to Cart</title>
    </head>
    <body style="font-family:Arial,Helvetica,sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;">
      <div style="text-align:center;">
        <h2>✅ Added <em>{product.name}</em> to cart</h2>
        <p>Redirecting to POS...</p>
        <p><a href="{pos_url}">Open POS</a></p>
      </div>
    </body></html>
    """
    return html


@pos_bp.route('/pos/device-qr-add', methods=['GET'])
def device_qr_add():
    """Add a device by IMEI to POS cart.

    Dual-mode support:
    - Adds a cart line of type='device' with unique key device:<device_id>
    - Checkout will create Sale for underlying product and mark this device as sold.
    """
    DeviceInventory = get_model('DeviceInventory')
    Product = get_model('Product')

    imei = (request.args.get('imei') or '').strip()
    store_id = request.args.get('store')
    if not imei or not store_id:
        return render_template_string('<p>Missing imei or store parameter.</p>'), 400

    try:
        store_id_int = int(store_id)
    except (TypeError, ValueError):
        return render_template_string('<p>Invalid store id.</p>'), 400

    # ensure session points to this store
    session['store_id'] = store_id_int

    device = DeviceInventory.query.filter(
        DeviceInventory.store_id == store_id_int,
        DeviceInventory.imei == imei,
    ).first()

    if not device:
        return render_template_string('<p>Device not found for this IMEI.</p>'), 404

    if getattr(device, 'status', None) == 'sold':
        return render_template_string('<p>Device already sold.</p>'), 409

    # DeviceInventory.variant -> ProductVariant -> Product
    product = Product.query.filter(Product.id == device.variant.product_id).first()
    if not product:
        return render_template_string('<p>Underlying product not found.</p>'), 404

    cart = session.get('cart', {})
    cart_key = f"device:{device.id}"

    item = cart.get(cart_key, {
        'type': 'device',
        'code': product.product_code,
        'name': product.name,
        'price': device.sell_price,
        'qty': 0,
        'discount': 0,
        'product_id': product.id,
        'device_id': device.id,
        'imei': device.imei,
    })

    item['qty'] = item.get('qty', 0) + 1
    cart[cart_key] = item
    session['cart'] = cart

    pos_url = url_for('pos.pos_dashboard', _external=True)
    html = f"""
    <html><head>
      <meta http-equiv="refresh" content="2;url={pos_url}">
      <title>Added to Cart</title>
    </head>
    <body style="font-family:Arial,Helvetica,sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;">
      <div style="text-align:center;">
        <h2>✅ Added <em>{product.name}</em> to cart</h2>
        <p>Redirecting to POS...</p>
        <p><a href="{pos_url}">Open POS</a></p>
      </div>
    </body></html>
    """
    return html



@pos_bp.route('/api/scan-product', methods=['POST'])
@login_required
def scan_product():
    Product = get_model('Product')

    data = request.get_json(silent=True) or {}
    code = data.get('code')
    if not code:
        return jsonify({'error': 'Product code is required'}), 400

    product = Product.query.filter(
        Product.store_id == session.get('store_id'),
        (Product.product_code == code) | (Product.imei == code)
    ).first()
    if not product:
        return jsonify({'error': 'Not found'}), 404

    return jsonify({
        'id': product.id,
        'name': product.name,
        'price': product.sell_price,
        'stock': product.stock,
        'category': product.category or 'General'
    })


@pos_bp.route('/cashier/dashboard')
@login_required
def cashier_dashboard():
    Cashier = get_model('Cashier')
    Sale = get_model('Sale')

    cashier = Cashier.query.get(session['cashier_id'])
    sales = Sale.query.filter_by(store_id=cashier.store_id).order_by(Sale.id.desc()).limit(20).all()
    return render_template('cashier_dashboard.html', sales=sales)
