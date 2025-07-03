from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

DATABASE = 'inventory.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            quantity INTEGER NOT NULL DEFAULT 0,
            price REAL NOT NULL DEFAULT 0.0,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    products = conn.execute('''
        SELECT * FROM products ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    
    # Calculate summary statistics
    total_products = len(products)
    total_value = sum(product['quantity'] * product['price'] for product in products)
    low_stock = sum(1 for product in products if product['quantity'] < 10)
    
    return render_template('index.html', 
                         products=products, 
                         total_products=total_products,
                         total_value=total_value,
                         low_stock=low_stock)

@app.route('/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        category = request.form['category']
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO products (name, description, quantity, price, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, description, quantity, price, category))
        conn.commit()
        conn.close()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add_product.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        category = request.form['category']
        
        conn.execute('''
            UPDATE products 
            SET name = ?, description = ?, quantity = ?, price = ?, category = ?, 
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (name, description, quantity, price, category, id))
        conn.commit()
        conn.close()
        
        flash('Product updated successfully!', 'success')
        return redirect(url_for('index'))
    
    product = conn.execute('SELECT * FROM products WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if product is None:
        flash('Product not found!', 'error')
        return redirect(url_for('index'))
    
    return render_template('edit_product.html', product=product)

@app.route('/delete/<int:id>')
def delete_product(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if query:
        conn = get_db_connection()
        products = conn.execute('''
            SELECT * FROM products 
            WHERE name LIKE ? OR description LIKE ? OR category LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
        conn.close()
    else:
        products = []
    
    return render_template('search.html', products=products, query=query)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=8000)
