
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

LOW_STOCK_LIMIT = 5

class Part(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    company = db.Column(db.String(100))
    category = db.Column(db.String(100))
    stock = db.Column(db.Integer)
    cost_price = db.Column(db.Float)
    selling_price = db.Column(db.Float)
    active = db.Column(db.Boolean, default=True)

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer)
    part_name = db.Column(db.String(200))
    action = db.Column(db.String(10))
    qty = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def dashboard():
    parts = Part.query.filter_by(active=True).all()
    total_cost = sum(p.stock * p.cost_price for p in parts)
    total_sell = sum(p.stock * p.selling_price for p in parts)
    low_stock_parts = [p for p in parts if p.stock <= LOW_STOCK_LIMIT]
    return render_template('dashboard.html',
                           parts=parts,
                           total_parts=len(parts),
                           total_cost=total_cost,
                           total_sell=total_sell,
                           low_stock_count=len(low_stock_parts),
                           low_limit=LOW_STOCK_LIMIT)

@app.route('/history')
def history():
    records = History.query.order_by(History.timestamp.desc()).all()
    return render_template('history.html', records=records)

@app.route('/add', methods=['POST'])
def add():
    p = Part(
        name=request.form['name'],
        company=request.form['company'],
        category=request.form['category'],
        stock=int(request.form['stock']),
        cost_price=float(request.form['cost']),
        selling_price=float(request.form['sell'])
    )
    db.session.add(p)
    db.session.commit()
    return redirect('/')

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    p = Part.query.get_or_404(id)
    qty = abs(int(request.form['qty']))
    action = request.form['type']

    if action == 'in':
        p.stock += qty
    else:
        if qty <= p.stock:
            p.stock -= qty

    h = History(part_id=p.id,
                part_name=f"{p.name} ({p.company})",
                action=action.upper(),
                qty=qty)

    db.session.add(h)
    db.session.commit()
    return redirect('/')

@app.route('/remove/<int:id>')
def remove(id):
    p = Part.query.get_or_404(id)
    p.active = False
    db.session.commit()
    return redirect('/')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
