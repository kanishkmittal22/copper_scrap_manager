import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="scrap_manager.db"):
        self.db_path = os.path.join(os.path.dirname(__file__), "..", db_name)
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Suppliers Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    opening_balance REAL DEFAULT 0,
                    current_balance REAL DEFAULT 0
                )
            ''')
            
            # Procurements Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS procurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_number TEXT UNIQUE NOT NULL,
                    date TEXT NOT NULL,
                    supplier_id INTEGER NOT NULL,
                    total_weight REAL DEFAULT 0,
                    rate REAL DEFAULT 0,
                    base_amount REAL DEFAULT 0,
                    remarks TEXT,
                    net_adjustment REAL DEFAULT 0,
                    grand_total REAL DEFAULT 0,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                )
            ''')
            
            # Procurement Line Items Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS procurement_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    procurement_id INTEGER NOT NULL,
                    scrap_type TEXT NOT NULL,
                    weight REAL NOT NULL,
                    rate REAL NOT NULL,
                    amount REAL NOT NULL,
                    adjustment_type TEXT NOT NULL, -- 'Add' or 'Deduct'
                    FOREIGN KEY (procurement_id) REFERENCES procurements(id) ON DELETE CASCADE
                )
            ''')
            
            # Payments Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    supplier_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    remarks TEXT,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                )
            ''')
            
            # Customers Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    opening_balance REAL DEFAULT 0,
                    current_balance REAL DEFAULT 0
                )
            ''')
            
            # Sales Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_number TEXT UNIQUE NOT NULL,
                    date TEXT NOT NULL,
                    customer_id INTEGER NOT NULL,
                    total_weight REAL DEFAULT 0,
                    rate REAL DEFAULT 0,
                    total_amount REAL DEFAULT 0,
                    remarks TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            ''')
            
            # Payments Received Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments_received (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    customer_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    remarks TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            ''')
            
            # Enable Foreign Keys
            cursor.execute("PRAGMA foreign_keys = ON")
            conn.commit()

    # --- Supplier Operations ---
    def add_supplier(self, name, opening_balance):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO suppliers (name, opening_balance, current_balance) VALUES (?, ?, ?)",
                    (name, opening_balance, opening_balance)
                )
                conn.commit()
                return True, "Supplier added successfully."
            except sqlite3.IntegrityError:
                return False, "Supplier name already exists."

    def update_supplier(self, supplier_id, name, new_opening_balance):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Calculate new current balance based on difference in opening balance
            cursor.execute("SELECT opening_balance FROM suppliers WHERE id = ?", (supplier_id,))
            row = cursor.fetchone()
            if not row:
                return False, "Supplier not found."
            
            old_opening_balance = row[0]
            diff = new_opening_balance - old_opening_balance
            
            try:
                cursor.execute(
                    "UPDATE suppliers SET name = ?, opening_balance = ?, current_balance = current_balance + ? WHERE id = ?",
                    (name, new_opening_balance, diff, supplier_id)
                )
                conn.commit()
                return True, "Supplier updated successfully."
            except sqlite3.IntegrityError:
                return False, "Supplier name already exists."

    def delete_supplier(self, supplier_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Check if there are transactions
            cursor.execute("SELECT COUNT(*) FROM procurements WHERE supplier_id = ?", (supplier_id,))
            if cursor.fetchone()[0] > 0:
                return False, "Cannot delete supplier with existing procurements."
                
            cursor.execute("SELECT COUNT(*) FROM payments WHERE supplier_id = ?", (supplier_id,))
            if cursor.fetchone()[0] > 0:
                return False, "Cannot delete supplier with existing payments."
                
            cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
            conn.commit()
            return True, "Supplier deleted successfully."

    def get_all_suppliers(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, current_balance, opening_balance FROM suppliers ORDER BY name")
            return cursor.fetchall()
            
    def get_supplier_by_id(self, supplier_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, current_balance, opening_balance FROM suppliers WHERE id = ?", (supplier_id,))
            return cursor.fetchone()

    # --- Procurement Operations ---
    def generate_entry_number(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            prefix = f"PUR-{datetime.now().strftime('%Y%m')}-"
            cursor.execute("SELECT entry_number FROM procurements WHERE entry_number LIKE ? ORDER BY entry_number DESC LIMIT 1", (f"{prefix}%",))
            row = cursor.fetchone()
            if row:
                try:
                    seq = int(row[0].split('-')[-1])
                    return f"{prefix}{seq + 1:04d}"
                except ValueError:
                    return f"{prefix}0001"
            return f"{prefix}0001"

    def add_procurement(self, data, items):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Insert main procurement
                cursor.execute('''
                    INSERT INTO procurements 
                    (entry_number, date, supplier_id, total_weight, rate, base_amount, remarks, net_adjustment, grand_total)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['entry_number'], data['date'], data['supplier_id'], 
                    data['total_weight'], data['rate'], data['base_amount'], 
                    data['remarks'], data['net_adjustment'], data['grand_total']
                ))
                
                procurement_id = cursor.lastrowid
                
                # Insert items
                for item in items:
                    cursor.execute('''
                        INSERT INTO procurement_items 
                        (procurement_id, scrap_type, weight, rate, amount, adjustment_type)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        procurement_id, item['scrap_type'], item['weight'], 
                        item['rate'], item['amount'], item['adjustment_type']
                    ))
                
                # Update supplier balance
                cursor.execute(
                    "UPDATE suppliers SET current_balance = current_balance + ? WHERE id = ?",
                    (data['grand_total'], data['supplier_id'])
                )
                
                conn.commit()
                return True, "Procurement entry saved successfully."
            except Exception as e:
                conn.rollback()
                return False, f"Error saving entry: {str(e)}"

    def get_procurement_items(self, procurement_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT scrap_type, weight, rate, amount, adjustment_type FROM procurement_items WHERE procurement_id = ?", (procurement_id,))
            return cursor.fetchall()

    # --- Payment Operations ---
    def add_payment(self, data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO payments (date, supplier_id, amount, remarks)
                    VALUES (?, ?, ?, ?)
                ''', (data['date'], data['supplier_id'], data['amount'], data['remarks']))
                
                # Deduct payment from supplier balance
                cursor.execute(
                    "UPDATE suppliers SET current_balance = current_balance - ? WHERE id = ?",
                    (data['amount'], data['supplier_id'])
                )
                
                conn.commit()
                return True, "Payment recorded successfully."
            except Exception as e:
                conn.rollback()
                return False, f"Error recording payment: {str(e)}"
                
    # --- Ledger Operations ---
    def get_ledger(self, supplier_id, from_date, to_date):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Procurements (Debit = Purchase Amount)
            cursor.execute('''
                SELECT id, date, 'Procurement' as type, entry_number as reference, total_weight, rate, remarks, grand_total as debit, 0 as credit
                FROM procurements
                WHERE supplier_id = ? AND date >= ? AND date <= ?
            ''', (supplier_id, from_date, to_date))
            procurements = cursor.fetchall()
            
            # Payments (Credit = Payment Amount)
            cursor.execute('''
                SELECT id, date, 'Payment' as type, id as reference, 0 as total_weight, 0 as rate, remarks, 0 as debit, amount as credit
                FROM payments
                WHERE supplier_id = ? AND date >= ? AND date <= ?
            ''', (supplier_id, from_date, to_date))
            payments = cursor.fetchall()
            
            # Combine and sort by date
            all_entries = procurements + payments
            all_entries.sort(key=lambda x: x[1]) # date is at index 1
            
            return all_entries
            
    def get_opening_balance_for_ledger(self, supplier_id, from_date):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT opening_balance FROM suppliers WHERE id = ?", (supplier_id,))
            row = cursor.fetchone()
            if not row:
                return 0
            base_ob = row[0]
            
            # Procurements before from_date
            cursor.execute("SELECT SUM(grand_total) FROM procurements WHERE supplier_id = ? AND date < ?", (supplier_id, from_date))
            proc_sum = cursor.fetchone()[0] or 0
            
            # Payments before from_date
            cursor.execute("SELECT SUM(amount) FROM payments WHERE supplier_id = ? AND date < ?", (supplier_id, from_date))
            pay_sum = cursor.fetchone()[0] or 0
            
            return base_ob + proc_sum - pay_sum

    # --- Extended Procurement Operations ---
    def get_procurements(self, supplier_id=None, date=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT p.id, p.entry_number, p.date, s.name, p.base_amount, p.net_adjustment, p.grand_total, s.id 
                FROM procurements p
                JOIN suppliers s ON p.supplier_id = s.id
                WHERE 1=1
            """
            params = []
            if supplier_id:
                query += " AND p.supplier_id = ?"
                params.append(supplier_id)
            if date:
                query += " AND p.date = ?"
                params.append(date)
            query += " ORDER BY p.date DESC, p.id DESC"
            
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
            
    def get_procurement_by_id(self, procurement_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM procurements WHERE id = ?", (procurement_id,))
            procurement = cursor.fetchone()
            if not procurement:
                return None
            
            # Map columns to dictionary
            col_names = [description[0] for description in cursor.description]
            data = dict(zip(col_names, procurement))
            
            cursor.execute("SELECT * FROM procurement_items WHERE procurement_id = ?", (procurement_id,))
            items = []
            item_cols = [description[0] for description in cursor.description]
            for row in cursor.fetchall():
                items.append(dict(zip(item_cols, row)))
                
            return {"data": data, "items": items}
            
    def delete_procurement(self, procurement_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Get the grand_total and supplier_id
                cursor.execute("SELECT grand_total, supplier_id FROM procurements WHERE id = ?", (procurement_id,))
                row = cursor.fetchone()
                if not row:
                    return False, "Procurement not found."
                grand_total, supplier_id = row
                
                # Delete procurement (cascade will delete items)
                cursor.execute("DELETE FROM procurements WHERE id = ?", (procurement_id,))
                
                # Reverse the balance: subtract grand_total
                cursor.execute(
                    "UPDATE suppliers SET current_balance = current_balance - ? WHERE id = ?",
                    (grand_total, supplier_id)
                )
                
                conn.commit()
                return True, "Procurement deleted successfully."
            except Exception as e:
                conn.rollback()
                return False, f"Error deleting procurement: {str(e)}"
                
    def update_procurement(self, procurement_id, data, items):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # 1. Get old details to reverse balance
                cursor.execute("SELECT grand_total, supplier_id FROM procurements WHERE id = ?", (procurement_id,))
                row = cursor.fetchone()
                if not row:
                    return False, "Procurement not found."
                old_grand_total, old_supplier_id = row
                
                # 2. Reverse old balance
                cursor.execute("UPDATE suppliers SET current_balance = current_balance - ? WHERE id = ?", (old_grand_total, old_supplier_id))
                
                # 3. Update main procurement
                cursor.execute('''
                    UPDATE procurements 
                    SET date=?, supplier_id=?, total_weight=?, rate=?, base_amount=?, remarks=?, net_adjustment=?, grand_total=?
                    WHERE id=?
                ''', (
                    data['date'], data['supplier_id'], data['total_weight'], data['rate'], 
                    data['base_amount'], data['remarks'], data['net_adjustment'], data['grand_total'],
                    procurement_id
                ))
                
                # 4. Delete old items and insert new ones
                cursor.execute("DELETE FROM procurement_items WHERE procurement_id = ?", (procurement_id,))
                for item in items:
                    cursor.execute('''
                        INSERT INTO procurement_items 
                        (procurement_id, scrap_type, weight, rate, amount, adjustment_type)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        procurement_id, item['scrap_type'], item['weight'], 
                        item['rate'], item['amount'], item['adjustment_type']
                    ))
                
                # 5. Apply new balance
                cursor.execute("UPDATE suppliers SET current_balance = current_balance + ? WHERE id = ?", (data['grand_total'], data['supplier_id']))
                
                conn.commit()
                return True, "Procurement updated successfully."
            except Exception as e:
                conn.rollback()
                return False, f"Error updating procurement: {str(e)}"

    # --- Extended Payment Operations ---
    def get_payments(self, supplier_id=None, date=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT p.id, p.date, s.name, p.amount, p.remarks, s.id
                FROM payments p
                JOIN suppliers s ON p.supplier_id = s.id
                WHERE 1=1
            """
            params = []
            if supplier_id:
                query += " AND p.supplier_id = ?"
                params.append(supplier_id)
            if date:
                query += " AND p.date = ?"
                params.append(date)
            query += " ORDER BY p.date DESC, p.id DESC"
            
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
            
    def get_payment_by_id(self, payment_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
            payment = cursor.fetchone()
            if not payment:
                return None
            col_names = [description[0] for description in cursor.description]
            return dict(zip(col_names, payment))
            
    def delete_payment(self, payment_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT amount, supplier_id FROM payments WHERE id = ?", (payment_id,))
                row = cursor.fetchone()
                if not row:
                    return False, "Payment not found."
                amount, supplier_id = row
                
                cursor.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
                
                # Reverse balance: adding amount back to supplier
                cursor.execute(
                    "UPDATE suppliers SET current_balance = current_balance + ? WHERE id = ?",
                    (amount, supplier_id)
                )
                
                conn.commit()
                return True, "Payment deleted successfully."
            except Exception as e:
                conn.rollback()
                return False, f"Error deleting payment: {str(e)}"
                
    def update_payment(self, payment_id, data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT amount, supplier_id FROM payments WHERE id = ?", (payment_id,))
                row = cursor.fetchone()
                if not row:
                    return False, "Payment not found."
                old_amount, old_supplier_id = row
                
                # Reverse old balance
                cursor.execute("UPDATE suppliers SET current_balance = current_balance + ? WHERE id = ?", (old_amount, old_supplier_id))
                
                # Update payment
                cursor.execute('''
                    UPDATE payments SET date=?, supplier_id=?, amount=?, remarks=? WHERE id=?
                ''', (data['date'], data['supplier_id'], data['amount'], data['remarks'], payment_id))
                
                # Apply new balance
                cursor.execute("UPDATE suppliers SET current_balance = current_balance - ? WHERE id = ?", (data['amount'], data['supplier_id']))
                
                conn.commit()
                return True, "Payment updated successfully."
            except Exception as e:
                conn.rollback()
                return False, f"Error updating payment: {str(e)}"

    # ==========================================================
    # --- SALES SIDE OPERATIONS ---
    # ==========================================================

    # --- Customer Operations ---
    def add_customer(self, name, opening_balance):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO customers (name, opening_balance, current_balance) VALUES (?, ?, ?)",
                    (name, opening_balance, opening_balance)
                )
                conn.commit()
                return True, "Customer added successfully."
            except sqlite3.IntegrityError:
                return False, "Customer name already exists."

    def update_customer(self, customer_id, name, new_opening_balance):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT opening_balance FROM customers WHERE id = ?", (customer_id,))
            row = cursor.fetchone()
            if not row:
                return False, "Customer not found."
            
            old_opening_balance = row[0]
            diff = new_opening_balance - old_opening_balance
            
            try:
                cursor.execute(
                    "UPDATE customers SET name = ?, opening_balance = ?, current_balance = current_balance + ? WHERE id = ?",
                    (name, new_opening_balance, diff, customer_id)
                )
                conn.commit()
                return True, "Customer updated successfully."
            except sqlite3.IntegrityError:
                return False, "Customer name already exists."

    def delete_customer(self, customer_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sales WHERE customer_id = ?", (customer_id,))
            if cursor.fetchone()[0] > 0:
                return False, "Cannot delete customer with existing sales."
                
            cursor.execute("SELECT COUNT(*) FROM payments_received WHERE customer_id = ?", (customer_id,))
            if cursor.fetchone()[0] > 0:
                return False, "Cannot delete customer with existing payments."
                
            cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
            conn.commit()
            return True, "Customer deleted successfully."

    def get_all_customers(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, current_balance, opening_balance FROM customers ORDER BY name")
            return cursor.fetchall()
            
    def get_customer_by_id(self, customer_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, current_balance, opening_balance FROM customers WHERE id = ?", (customer_id,))
            return cursor.fetchone()

    # --- Sales Operations ---
    def generate_sales_entry_number(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            prefix = f"SAL-{datetime.now().strftime('%Y%m')}-"
            cursor.execute("SELECT entry_number FROM sales WHERE entry_number LIKE ? ORDER BY entry_number DESC LIMIT 1", (f"{prefix}%",))
            row = cursor.fetchone()
            if row:
                try:
                    seq = int(row[0].split('-')[-1])
                    return f"{prefix}{seq + 1:04d}"
                except ValueError:
                    return f"{prefix}0001"
            return f"{prefix}0001"

    def add_sale(self, data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO sales 
                    (entry_number, date, customer_id, total_weight, rate, total_amount, remarks)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['entry_number'], data['date'], data['customer_id'], 
                    data['total_weight'], data['rate'], data['total_amount'], 
                    data['remarks']
                ))
                
                # Sales increase customer balance
                cursor.execute(
                    "UPDATE customers SET current_balance = current_balance + ? WHERE id = ?",
                    (data['total_amount'], data['customer_id'])
                )
                
                conn.commit()
                return True, "Sales entry saved successfully."
            except Exception as e:
                conn.rollback()
                return False, f"Error saving entry: {str(e)}"

    def get_sales(self, customer_id=None, date=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT s.id, s.entry_number, s.date, c.name, s.total_weight, s.rate, s.total_amount, s.remarks, c.id 
                FROM sales s
                JOIN customers c ON s.customer_id = c.id
                WHERE 1=1
            """
            params = []
            if customer_id:
                query += " AND s.customer_id = ?"
                params.append(customer_id)
            if date:
                query += " AND s.date = ?"
                params.append(date)
            query += " ORDER BY s.date DESC, s.id DESC"
            
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
            
    def get_sale_by_id(self, sale_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sales WHERE id = ?", (sale_id,))
            sale = cursor.fetchone()
            if not sale:
                return None
            col_names = [description[0] for description in cursor.description]
            return dict(zip(col_names, sale))

    def update_sale(self, sale_id, data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # 1. Get old details
                cursor.execute("SELECT total_amount, customer_id FROM sales WHERE id = ?", (sale_id,))
                row = cursor.fetchone()
                if not row:
                    return False, "Sales entry not found."
                old_total_amount, old_customer_id = row
                
                # 2. Reverse old balance
                cursor.execute("UPDATE customers SET current_balance = current_balance - ? WHERE id = ?", (old_total_amount, old_customer_id))
                
                # 3. Update main sales entry
                cursor.execute('''
                    UPDATE sales 
                    SET date=?, customer_id=?, total_weight=?, rate=?, total_amount=?, remarks=?
                    WHERE id=?
                ''', (
                    data['date'], data['customer_id'], data['total_weight'], data['rate'], 
                    data['total_amount'], data['remarks'], sale_id
                ))
                
                # 4. Apply new balance
                cursor.execute("UPDATE customers SET current_balance = current_balance + ? WHERE id = ?", (data['total_amount'], data['customer_id']))
                
                conn.commit()
                return True, "Sales entry updated successfully."
            except Exception as e:
                conn.rollback()
                return False, f"Error updating sales entry: {str(e)}"

    def delete_sale(self, sale_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT total_amount, customer_id FROM sales WHERE id = ?", (sale_id,))
                row = cursor.fetchone()
                if not row:
                    return False, "Sales entry not found."
                total_amount, customer_id = row
                
                cursor.execute("DELETE FROM sales WHERE id = ?", (sale_id,))
                
                # Reverse balance: subtract amount
                cursor.execute(
                    "UPDATE customers SET current_balance = current_balance - ? WHERE id = ?",
                    (total_amount, customer_id)
                )
                
                conn.commit()
                return True, "Sales entry deleted successfully."
            except Exception as e:
                conn.rollback()
                return False, f"Error deleting sales entry: {str(e)}"

    # --- Payment Received Operations ---
    def add_payment_received(self, data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO payments_received (date, customer_id, amount, remarks)
                    VALUES (?, ?, ?, ?)
                ''', (data['date'], data['customer_id'], data['amount'], data['remarks']))
                
                # Deduct payment from customer balance (reduces receivable)
                cursor.execute(
                    "UPDATE customers SET current_balance = current_balance - ? WHERE id = ?",
                    (data['amount'], data['customer_id'])
                )
                
                conn.commit()
                return True, "Payment received recorded successfully."
            except Exception as e:
                conn.rollback()
                return False, f"Error recording payment received: {str(e)}"

    def get_payments_received(self, customer_id=None, date=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT p.id, p.date, c.name, p.amount, p.remarks, c.id
                FROM payments_received p
                JOIN customers c ON p.customer_id = c.id
                WHERE 1=1
            """
            params = []
            if customer_id:
                query += " AND p.customer_id = ?"
                params.append(customer_id)
            if date:
                query += " AND p.date = ?"
                params.append(date)
            query += " ORDER BY p.date DESC, p.id DESC"
            
            cursor.execute(query, tuple(params))
            return cursor.fetchall()

    def get_payment_received_by_id(self, payment_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM payments_received WHERE id = ?", (payment_id,))
            payment = cursor.fetchone()
            if not payment:
                return None
            col_names = [description[0] for description in cursor.description]
            return dict(zip(col_names, payment))

    def update_payment_received(self, payment_id, data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT amount, customer_id FROM payments_received WHERE id = ?", (payment_id,))
                row = cursor.fetchone()
                if not row:
                    return False, "Payment received not found."
                old_amount, old_customer_id = row
                
                # Reverse old balance (add back to receivable)
                cursor.execute("UPDATE customers SET current_balance = current_balance + ? WHERE id = ?", (old_amount, old_customer_id))
                
                # Update payment
                cursor.execute('''
                    UPDATE payments_received SET date=?, customer_id=?, amount=?, remarks=? WHERE id=?
                ''', (data['date'], data['customer_id'], data['amount'], data['remarks'], payment_id))
                
                # Apply new balance (subtract from receivable)
                cursor.execute("UPDATE customers SET current_balance = current_balance - ? WHERE id = ?", (data['amount'], data['customer_id']))
                
                conn.commit()
                return True, "Payment received updated successfully."
            except Exception as e:
                conn.rollback()
                return False, f"Error updating payment received: {str(e)}"

    def delete_payment_received(self, payment_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT amount, customer_id FROM payments_received WHERE id = ?", (payment_id,))
                row = cursor.fetchone()
                if not row:
                    return False, "Payment received not found."
                amount, customer_id = row
                
                cursor.execute("DELETE FROM payments_received WHERE id = ?", (payment_id,))
                
                # Reverse balance: adding amount back to customer receivable
                cursor.execute(
                    "UPDATE customers SET current_balance = current_balance + ? WHERE id = ?",
                    (amount, customer_id)
                )
                
                conn.commit()
                return True, "Payment received deleted successfully."
            except Exception as e:
                conn.rollback()
                return False, f"Error deleting payment received: {str(e)}"

    # --- Daily Cash Book Operations ---
    def get_daily_cash_inflows(self, date):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.name, p.amount 
                FROM payments_received p
                JOIN customers c ON p.customer_id = c.id
                WHERE p.date = ?
            ''', (date,))
            return cursor.fetchall()
            
    def get_daily_cash_outflows(self, date):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.name, p.amount 
                FROM payments p
                JOIN suppliers s ON p.supplier_id = s.id
                WHERE p.date = ?
            ''', (date,))
            return cursor.fetchall()

    # --- Daily Inventory Report Operations ---
    def get_daily_scrap_inward(self, date):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.name, p.total_weight 
                FROM procurements p
                JOIN suppliers s ON p.supplier_id = s.id
                WHERE p.date = ?
            ''', (date,))
            return cursor.fetchall()
            
    def get_daily_rod_outward(self, date):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.name, s.total_weight 
                FROM sales s
                JOIN customers c ON s.customer_id = c.id
                WHERE s.date = ?
            ''', (date,))
            return cursor.fetchall()

    # --- Sales Ledger Operations ---
    def get_sales_ledger(self, customer_id, from_date, to_date):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Sales (Debits to Customer Account)
            cursor.execute('''
                SELECT date, 'Sale' as type, entry_number as reference, total_amount as debit, 0 as credit, id
                FROM sales
                WHERE customer_id = ? AND date >= ? AND date <= ?
            ''', (customer_id, from_date, to_date))
            sales = cursor.fetchall()
            
            # Payments Received (Credits to Customer Account)
            cursor.execute('''
                SELECT date, 'Payment Received' as type, remarks as reference, 0 as debit, amount as credit, id
                FROM payments_received
                WHERE customer_id = ? AND date >= ? AND date <= ?
            ''', (customer_id, from_date, to_date))
            payments = cursor.fetchall()
            
            # Combine and sort by date
            all_entries = sales + payments
            all_entries.sort(key=lambda x: x[0])
            
            return all_entries
            
    def get_opening_balance_for_sales_ledger(self, customer_id, from_date):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT opening_balance FROM customers WHERE id = ?", (customer_id,))
            row = cursor.fetchone()
            if not row:
                return 0
            base_ob = row[0]
            
            # Sales before from_date
            cursor.execute("SELECT SUM(total_amount) FROM sales WHERE customer_id = ? AND date < ?", (customer_id, from_date))
            sales_sum = cursor.fetchone()[0] or 0
            
            # Payments Received before from_date
            cursor.execute("SELECT SUM(amount) FROM payments_received WHERE customer_id = ? AND date < ?", (customer_id, from_date))
            pay_sum = cursor.fetchone()[0] or 0
            
            return base_ob + sales_sum - pay_sum
