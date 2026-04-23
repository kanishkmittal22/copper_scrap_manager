from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox, QDateEdit, QCompleter)
from PyQt5.QtCore import Qt, QDate

class PaymentEntryDialog(QDialog):
    def __init__(self, db, payment_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.payment_id = payment_id
        
        title = "Edit Payment Entry" if payment_id else "New Payment Entry"
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
        
        grid.addWidget(QLabel("Supplier:"), 1, 0)
        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(True)
        grid.addWidget(self.supplier_combo, 1, 1)
        
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
        
    def populate_suppliers(self):
        try:
            self.supplier_combo.currentTextChanged.disconnect(self.on_supplier_changed)
        except TypeError:
            pass
            
        self.supplier_combo.clear()
        suppliers = self.db.get_all_suppliers()
        names = []
        for sup in suppliers:
            self.supplier_combo.addItem(sup[1], sup[0])
            names.append(sup[1])
            
        completer = QCompleter(names)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.supplier_combo.setCompleter(completer)
        
        self.supplier_combo.setCurrentIndex(-1)
        self.supplier_combo.currentTextChanged.connect(self.on_supplier_changed)

    def refresh_data(self):
        self.populate_suppliers()

    def load_data(self):
        self.populate_suppliers()
        data = self.db.get_payment_by_id(self.payment_id)
        if not data:
            return
            
        self.date_input.setDate(QDate.fromString(data['date'], Qt.ISODate))
        
        index = self.supplier_combo.findData(data['supplier_id'])
        if index >= 0:
            self.supplier_combo.setCurrentIndex(index)
            
        self.amount_input.setText(str(data['amount']))
        self.remarks_input.setText(data['remarks'] or "")
        
        # Manually calculate previous balance
        sup = self.db.get_supplier_by_id(data['supplier_id'])
        if sup:
            # Payment reduced supplier balance. To revert: add it back.
            prev_balance = sup[2] + data['amount']
            self.prev_balance_input.setText(f"{prev_balance:.2f}")
            
        self.calculate_balance()

    def get_selected_supplier_id(self):
        text = self.supplier_combo.currentText().strip()
        index = self.supplier_combo.findText(text, Qt.MatchFixedString)
        if index >= 0:
            return self.supplier_combo.itemData(index)
        return None

    def on_supplier_changed(self):
        sup_id = self.get_selected_supplier_id()
        if sup_id:
            sup = self.db.get_supplier_by_id(sup_id)
            if sup:
                if self.payment_id:
                    data = self.db.get_payment_by_id(self.payment_id)
                    if data and data['supplier_id'] == sup_id:
                        prev_balance = sup[2] + data['amount']
                    else:
                        prev_balance = sup[2]
                else:
                    prev_balance = sup[2]
                    
                self.prev_balance_input.setText(f"{prev_balance:.2f}")
        else:
            self.prev_balance_input.setText("0.00")
            
        self.calculate_balance()

    def calculate_balance(self):
        try:
            amt = float(self.amount_input.text() or 0)
            prev = float(self.prev_balance_input.text())
            # For supplier, payment reduces the balance owed
            self.new_balance_input.setText(f"{prev - amt:.2f}")
        except ValueError:
            pass

    def submit_entry(self):
        sup_id = self.get_selected_supplier_id()
        if not sup_id:
            QMessageBox.warning(self, "Validation", "Please select a valid supplier.")
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
            'supplier_id': sup_id,
            'amount': amount,
            'remarks': self.remarks_input.text()
        }
        
        if self.payment_id:
            success, msg = self.db.update_payment(self.payment_id, data)
        else:
            success, msg = self.db.add_payment(data)
            
        if success:
            QMessageBox.information(self, "Success", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Error", msg)
