from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox, QDateEdit, QCompleter)
from PyQt5.QtCore import Qt, QDate

class SalesEntryDialog(QDialog):
    def __init__(self, db, sale_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.sale_id = sale_id
        
        title = "Edit Sales Entry" if sale_id else "New Sales Entry"
        self.setWindowTitle(title)
        self.setMinimumSize(600, 400)
        
        self.init_ui()
        if self.sale_id:
            self.load_data()
        else:
            self.refresh_data()
            
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        grid = QGridLayout()
        
        grid.addWidget(QLabel("Entry Number:"), 0, 0)
        self.entry_num_input = QLineEdit()
        self.entry_num_input.setReadOnly(True)
        grid.addWidget(self.entry_num_input, 0, 1)
        
        grid.addWidget(QLabel("Date:"), 0, 2)
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd-MM-yyyy")
        grid.addWidget(self.date_input, 0, 3)
        
        grid.addWidget(QLabel("Customer:"), 1, 0)
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        grid.addWidget(self.customer_combo, 1, 1)
        
        grid.addWidget(QLabel("Total Weight:"), 1, 2)
        self.weight_input = QLineEdit()
        self.weight_input.textChanged.connect(self.calculate_total)
        grid.addWidget(self.weight_input, 1, 3)
        
        grid.addWidget(QLabel("Rate:"), 2, 0)
        self.rate_input = QLineEdit()
        self.rate_input.textChanged.connect(self.calculate_total)
        grid.addWidget(self.rate_input, 2, 1)
        
        grid.addWidget(QLabel("Total Amount:"), 2, 2)
        self.total_amount_input = QLineEdit("0.00")
        self.total_amount_input.setReadOnly(True)
        grid.addWidget(self.total_amount_input, 2, 3)
        
        grid.addWidget(QLabel("Remarks:"), 3, 0)
        self.remarks_input = QLineEdit()
        grid.addWidget(self.remarks_input, 3, 1, 1, 3)
        
        main_layout.addLayout(grid)
        
        # --- Balances ---
        bal_layout = QGridLayout()
        bal_layout.addWidget(QLabel("Previous Balance:"), 0, 0)
        self.prev_balance_input = QLineEdit("0.00")
        self.prev_balance_input.setReadOnly(True)
        bal_layout.addWidget(self.prev_balance_input, 0, 1)
        
        bal_layout.addWidget(QLabel("Updated Balance:"), 0, 2)
        self.new_balance_input = QLineEdit("0.00")
        self.new_balance_input.setReadOnly(True)
        bal_layout.addWidget(self.new_balance_input, 0, 3)
        
        main_layout.addLayout(bal_layout)
        
        # --- Actions ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.calc_btn = QPushButton("Calculate Balance")
        self.calc_btn.clicked.connect(self.calculate_balance)
        btn_layout.addWidget(self.calc_btn)
        
        self.submit_btn = QPushButton("Submit Entry")
        self.submit_btn.clicked.connect(self.submit_entry)
        self.submit_btn.setEnabled(False)
        btn_layout.addWidget(self.submit_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(btn_layout)
        
    def refresh_data(self):
        self.entry_num_input.setText(self.db.generate_sales_entry_number())
        self.populate_customers()
        
    def populate_customers(self):
        try:
            self.customer_combo.currentTextChanged.disconnect(self.on_customer_changed)
        except TypeError:
            pass
            
        self.customer_combo.clear()
        customers = self.db.get_all_customers()
        names = []
        for cust in customers:
            self.customer_combo.addItem(cust[1], cust[0])
            names.append(cust[1])
            
        completer = QCompleter(names)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.customer_combo.setCompleter(completer)
        
        self.customer_combo.setCurrentIndex(-1)
        self.customer_combo.currentTextChanged.connect(self.on_customer_changed)
        
    def load_data(self):
        self.populate_customers()
        data = self.db.get_sale_by_id(self.sale_id)
        if not data:
            return
            
        self.entry_num_input.setText(data['entry_number'])
        self.date_input.setDate(QDate.fromString(data['date'], Qt.ISODate))
        
        index = self.customer_combo.findData(data['customer_id'])
        if index >= 0:
            self.customer_combo.setCurrentIndex(index)
            
        self.weight_input.setText(str(data['total_weight']))
        self.rate_input.setText(str(data['rate']))
        self.total_amount_input.setText(str(data['total_amount']))
        self.remarks_input.setText(data['remarks'] or "")
        
        # Manually calculate previous balance
        cust = self.db.get_customer_by_id(data['customer_id'])
        if cust:
            # Revert current transaction effect to show prev balance accurately
            prev_balance = cust[2] - data['total_amount']
            self.prev_balance_input.setText(f"{prev_balance:.2f}")
            
        self.calculate_balance()

    def get_selected_customer_id(self):
        text = self.customer_combo.currentText().strip()
        index = self.customer_combo.findText(text, Qt.MatchFixedString)
        if index >= 0:
            return self.customer_combo.itemData(index)
        return None

    def on_customer_changed(self):
        self.submit_btn.setEnabled(False)
        cust_id = self.get_selected_customer_id()
        if cust_id:
            cust = self.db.get_customer_by_id(cust_id)
            if cust:
                # If editing, we adjust for the current sale amount
                if self.sale_id:
                    data = self.db.get_sale_by_id(self.sale_id)
                    if data and data['customer_id'] == cust_id:
                        prev_balance = cust[2] - data['total_amount']
                    else:
                        prev_balance = cust[2]
                else:
                    prev_balance = cust[2]
                    
                self.prev_balance_input.setText(f"{prev_balance:.2f}")
        else:
            self.prev_balance_input.setText("0.00")
            
    def calculate_total(self):
        self.submit_btn.setEnabled(False)
        try:
            w = float(self.weight_input.text() or 0)
            r = float(self.rate_input.text() or 0)
            self.total_amount_input.setText(f"{w * r:.2f}")
        except ValueError:
            pass

    def calculate_balance(self):
        cust_id = self.get_selected_customer_id()
        if not cust_id:
            QMessageBox.warning(self, "Validation", "Please select a valid customer.")
            return
            
        try:
            total = float(self.total_amount_input.text())
            prev = float(self.prev_balance_input.text())
            self.new_balance_input.setText(f"{prev + total:.2f}")
            self.submit_btn.setEnabled(True)
        except ValueError:
            QMessageBox.warning(self, "Calculation Error", "Please ensure weight and rate are valid numbers.")

    def submit_entry(self):
        cust_id = self.get_selected_customer_id()
        if not cust_id:
            QMessageBox.warning(self, "Validation", "Please select a valid customer.")
            return
            
        if not self.weight_input.text() or not self.rate_input.text():
            QMessageBox.warning(self, "Validation", "Total weight and rate are required.")
            return
            
        data = {
            'entry_number': self.entry_num_input.text(),
            'date': self.date_input.date().toString(Qt.ISODate),
            'customer_id': cust_id,
            'total_weight': float(self.weight_input.text()),
            'rate': float(self.rate_input.text()),
            'total_amount': float(self.total_amount_input.text()),
            'remarks': self.remarks_input.text()
        }
        
        if self.sale_id:
            success, msg = self.db.update_sale(self.sale_id, data)
        else:
            success, msg = self.db.add_sale(data)
            
        if success:
            QMessageBox.information(self, "Success", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Error", msg)


class PaymentReceivedDialog(QDialog):
    def __init__(self, db, payment_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.payment_id = payment_id
        
        title = "Edit Payment Received" if payment_id else "New Payment Received"
        self.setWindowTitle(title)
        self.setMinimumSize(400, 300)
        
        self.init_ui()
        if self.payment_id:
            self.load_data()
        else:
            self.refresh_data()
            
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        grid = QGridLayout()
        
        grid.addWidget(QLabel("Date:"), 0, 0)
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd-MM-yyyy")
        grid.addWidget(self.date_input, 0, 1)
        
        grid.addWidget(QLabel("Customer:"), 1, 0)
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        grid.addWidget(self.customer_combo, 1, 1)
        
        grid.addWidget(QLabel("Amount:"), 2, 0)
        self.amount_input = QLineEdit()
        self.amount_input.textChanged.connect(self.calculate_balance)
        grid.addWidget(self.amount_input, 2, 1)
        
        grid.addWidget(QLabel("Remarks:"), 3, 0)
        self.remarks_input = QLineEdit()
        grid.addWidget(self.remarks_input, 3, 1)
        
        main_layout.addLayout(grid)
        
        # --- Balances ---
        bal_layout = QGridLayout()
        bal_layout.addWidget(QLabel("Previous Balance:"), 0, 0)
        self.prev_balance_input = QLineEdit("0.00")
        self.prev_balance_input.setReadOnly(True)
        bal_layout.addWidget(self.prev_balance_input, 0, 1)
        
        bal_layout.addWidget(QLabel("Updated Balance:"), 1, 0)
        self.new_balance_input = QLineEdit("0.00")
        self.new_balance_input.setReadOnly(True)
        bal_layout.addWidget(self.new_balance_input, 1, 1)
        
        main_layout.addLayout(bal_layout)
        
        # --- Actions ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.submit_btn = QPushButton("Record Payment")
        self.submit_btn.clicked.connect(self.submit_entry)
        btn_layout.addWidget(self.submit_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(btn_layout)
        
    def populate_customers(self):
        try:
            self.customer_combo.currentTextChanged.disconnect(self.on_customer_changed)
        except TypeError:
            pass
            
        self.customer_combo.clear()
        customers = self.db.get_all_customers()
        names = []
        for cust in customers:
            self.customer_combo.addItem(cust[1], cust[0])
            names.append(cust[1])
            
        completer = QCompleter(names)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.customer_combo.setCompleter(completer)
        
        self.customer_combo.setCurrentIndex(-1)
        self.customer_combo.currentTextChanged.connect(self.on_customer_changed)

    def refresh_data(self):
        self.populate_customers()

    def load_data(self):
        self.populate_customers()
        data = self.db.get_payment_received_by_id(self.payment_id)
        if not data:
            return
            
        self.date_input.setDate(QDate.fromString(data['date'], Qt.ISODate))
        
        index = self.customer_combo.findData(data['customer_id'])
        if index >= 0:
            self.customer_combo.setCurrentIndex(index)
            
        self.amount_input.setText(str(data['amount']))
        self.remarks_input.setText(data['remarks'] or "")
        
        # Manually calculate previous balance
        cust = self.db.get_customer_by_id(data['customer_id'])
        if cust:
            prev_balance = cust[2] + data['amount']
            self.prev_balance_input.setText(f"{prev_balance:.2f}")
            
        self.calculate_balance()

    def get_selected_customer_id(self):
        text = self.customer_combo.currentText().strip()
        index = self.customer_combo.findText(text, Qt.MatchFixedString)
        if index >= 0:
            return self.customer_combo.itemData(index)
        return None

    def on_customer_changed(self):
        cust_id = self.get_selected_customer_id()
        if cust_id:
            cust = self.db.get_customer_by_id(cust_id)
            if cust:
                if self.payment_id:
                    data = self.db.get_payment_received_by_id(self.payment_id)
                    if data and data['customer_id'] == cust_id:
                        prev_balance = cust[2] + data['amount']
                    else:
                        prev_balance = cust[2]
                else:
                    prev_balance = cust[2]
                    
                self.prev_balance_input.setText(f"{prev_balance:.2f}")
        else:
            self.prev_balance_input.setText("0.00")
            
        self.calculate_balance()

    def calculate_balance(self):
        try:
            amt = float(self.amount_input.text() or 0)
            prev = float(self.prev_balance_input.text())
            self.new_balance_input.setText(f"{prev - amt:.2f}")
        except ValueError:
            pass

    def submit_entry(self):
        cust_id = self.get_selected_customer_id()
        if not cust_id:
            QMessageBox.warning(self, "Validation", "Please select a valid customer.")
            return
            
        amt_str = self.amount_input.text().strip()
        if not amt_str:
            QMessageBox.warning(self, "Validation", "Amount is required.")
            return
            
        try:
            amount = float(amt_str)
        except ValueError:
            QMessageBox.warning(self, "Validation", "Amount must be a number.")
            return
            
        data = {
            'date': self.date_input.date().toString(Qt.ISODate),
            'customer_id': cust_id,
            'amount': amount,
            'remarks': self.remarks_input.text()
        }
        
        if self.payment_id:
            success, msg = self.db.update_payment_received(self.payment_id, data)
        else:
            success, msg = self.db.add_payment_received(data)
            
        if success:
            QMessageBox.information(self, "Success", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Error", msg)
