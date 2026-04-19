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
            cursor.execute("SELECT COUNT(*) FROM procurements")
            count = cursor.fetchone()[0]
            return f"PUR-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"

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
            
            # Procurements
            cursor.execute('''
                SELECT date, 'Procurement' as type, entry_number as reference, grand_total as credit, 0 as debit
                FROM procurements
                WHERE supplier_id = ? AND date >= ? AND date <= ?
            ''', (supplier_id, from_date, to_date))
            procurements = cursor.fetchall()
            
            # Payments
            cursor.execute('''
                SELECT date, 'Payment' as type, remarks as reference, 0 as credit, amount as debit
                FROM payments
                WHERE supplier_id = ? AND date >= ? AND date <= ?
            ''', (supplier_id, from_date, to_date))
            payments = cursor.fetchall()
            
            # Combine and sort by date
            all_entries = procurements + payments
            all_entries.sort(key=lambda x: x[0])
            
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
