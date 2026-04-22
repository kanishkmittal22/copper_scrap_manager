from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                             QDateEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLabel, QCompleter, QMessageBox, QDialog)
from PyQt5.QtCore import Qt, QDate
from .sales_entry_dialog import SalesEntryDialog, PaymentReceivedDialog

class SalesLedgerView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # --- Top Balance Label ---
        self.balance_header = QLabel("Current Balance: ₹0.00")
        self.balance_header.setStyleSheet("font-size: 22px; font-weight: bold; color: #27ae60; margin-bottom: 10px;")
        self.balance_header.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.balance_header)
        
        # --- Filters ---
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Customer:"))
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        controls_layout.addWidget(self.customer_combo)
        
        controls_layout.addWidget(QLabel("From:"))
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        self.from_date.setCalendarPopup(True)
        self.from_date.setDisplayFormat("dd-MM-yyyy")
        controls_layout.addWidget(self.from_date)
        
        controls_layout.addWidget(QLabel("To:"))
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        self.to_date.setDisplayFormat("dd-MM-yyyy")
        controls_layout.addWidget(self.to_date)
        
        self.gen_btn = QPushButton("Generate Ledger")
        self.gen_btn.clicked.connect(self.generate_ledger)
        controls_layout.addWidget(self.gen_btn)
        
        layout.addLayout(controls_layout)
        
        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(7) # Hidden column for ID at end
        self.table.setHorizontalHeaderLabels(["Date", "Type", "Reference", "Debit (Sales)", "Credit (Payment)", "Balance", "ID"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnHidden(6, True) # Hide ID
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        
        # --- Actions ---
        action_layout = QHBoxLayout()
        
        self.create_sale_btn = QPushButton("Create Sales Entry")
        self.create_sale_btn.clicked.connect(self.create_sale)
        action_layout.addWidget(self.create_sale_btn)
        
        self.create_payment_btn = QPushButton("Create Payment Received Entry")
        self.create_payment_btn.clicked.connect(self.create_payment)
        action_layout.addWidget(self.create_payment_btn)
        
        action_layout.addStretch()
        
        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.clicked.connect(self.edit_entry)
        action_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setObjectName("danger_btn")
        self.delete_btn.setProperty("class", "danger")
        self.delete_btn.clicked.connect(self.delete_entry)
        action_layout.addWidget(self.delete_btn)
        
        layout.addLayout(action_layout)
        
    def refresh_data(self):
        try:
            self.customer_combo.currentTextChanged.disconnect(self.update_balance_header)
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
        self.customer_combo.currentTextChanged.connect(self.update_balance_header)
        self.update_balance_header()
        
    def get_selected_customer_id(self):
        text = self.customer_combo.currentText().strip()
        index = self.customer_combo.findText(text, Qt.MatchFixedString)
        if index >= 0:
            return self.customer_combo.itemData(index)
        return None
            
    def update_balance_header(self):
        customer_id = self.get_selected_customer_id()
        if customer_id:
            cust = self.db.get_customer_by_id(customer_id)
            if cust:
                balance = cust[2]
                color = "#27ae60" if balance >= 0 else "#e74c3c"
                self.balance_header.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {color}; margin-bottom: 10px;")
                self.balance_header.setText(f"Current Balance: ₹{balance:.2f}")
        else:
            self.balance_header.setStyleSheet("font-size: 22px; font-weight: bold; color: #27ae60; margin-bottom: 10px;")
            self.balance_header.setText("Current Balance: ₹0.00")
            
    def generate_ledger(self):
        customer_id = self.get_selected_customer_id()
        if not customer_id:
            QMessageBox.warning(self, "Validation", "Please select a valid customer.")
            return
            
        from_d = self.from_date.date().toString(Qt.ISODate)
        to_d = self.to_date.date().toString(Qt.ISODate)
        
        entries = self.db.get_sales_ledger(customer_id, from_d, to_d)
        opening_balance = self.db.get_opening_balance_for_sales_ledger(customer_id, from_d)
        
        self.table.setRowCount(0)
        
        # Add Opening Balance Row
        self.table.insertRow(0)
        f_from_d = QDate.fromString(from_d, Qt.ISODate).toString("dd-MM-yyyy")
        self.table.setItem(0, 0, QTableWidgetItem(f_from_d))
        self.table.setItem(0, 1, QTableWidgetItem("Opening Balance"))
        self.table.setItem(0, 2, QTableWidgetItem("-"))
        self.table.setItem(0, 3, QTableWidgetItem(""))
        self.table.setItem(0, 4, QTableWidgetItem(""))
        
        bal_item = QTableWidgetItem(f"{opening_balance:.2f}")
        bal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(0, 5, bal_item)
        
        current_balance = opening_balance
        
        for idx, entry in enumerate(entries):
            row = idx + 1
            self.table.insertRow(row)
            
            date, e_type, ref, debit, credit, entry_id = entry
            
            # Format Date
            date_obj = QDate.fromString(date, Qt.ISODate)
            f_date = date_obj.toString("dd-MM-yyyy") if date_obj.isValid() else date
            
            # Sales (debit) increases customer balance, Payments (credit) decrease
            current_balance += (debit - credit)
            
            self.table.setItem(row, 0, QTableWidgetItem(f_date))
            
            type_item = QTableWidgetItem(e_type)
            type_item.setData(Qt.UserRole, entry_id) # Store ID for editing/deleting
            self.table.setItem(row, 1, type_item)
            
            self.table.setItem(row, 2, QTableWidgetItem(ref))
            
            db_item = QTableWidgetItem(f"{debit:.2f}" if debit else "")
            db_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if debit:
                db_item.setForeground(Qt.red) # Debit means they owe us
            self.table.setItem(row, 3, db_item)
            
            cr_item = QTableWidgetItem(f"{credit:.2f}" if credit else "")
            cr_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if credit:
                cr_item.setForeground(Qt.darkGreen) # Credit means they paid
            self.table.setItem(row, 4, cr_item)
            
            bal_item = QTableWidgetItem(f"{current_balance:.2f}")
            bal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if current_balance < 0:
                bal_item.setForeground(Qt.darkGreen) # Negative balance means we owe them
            self.table.setItem(row, 5, bal_item)
            
            self.table.setItem(row, 6, QTableWidgetItem(str(entry_id)))

    # --- Actions ---
    def create_sale(self):
        dialog = SalesEntryDialog(self.db, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.update_balance_header()
            self.generate_ledger()

    def create_payment(self):
        dialog = PaymentReceivedDialog(self.db, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.update_balance_header()
            self.generate_ledger()

    def get_selected_entry_info(self):
        selected = self.table.selectedItems()
        if not selected:
            return None, None
            
        row = selected[0].row()
        if row == 0:
            return None, None # Opening balance row
            
        e_type = self.table.item(row, 1).text()
        entry_id = self.table.item(row, 1).data(Qt.UserRole)
        return e_type, entry_id

    def edit_entry(self):
        e_type, entry_id = self.get_selected_entry_info()
        if not entry_id:
            QMessageBox.warning(self, "Selection", "Please select a valid transaction to edit.")
            return
            
        if e_type == "Sale":
            dialog = SalesEntryDialog(self.db, sale_id=entry_id, parent=self)
        elif e_type == "Payment Received":
            dialog = PaymentReceivedDialog(self.db, payment_id=entry_id, parent=self)
        else:
            return
            
        if dialog.exec_() == QDialog.Accepted:
            self.update_balance_header()
            self.generate_ledger()

    def delete_entry(self):
        e_type, entry_id = self.get_selected_entry_info()
        if not entry_id:
            QMessageBox.warning(self, "Selection", "Please select a valid transaction to delete.")
            return
            
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete this {e_type}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                     
        if reply == QMessageBox.Yes:
            if e_type == "Sale":
                success, msg = self.db.delete_sale(entry_id)
            elif e_type == "Payment Received":
                success, msg = self.db.delete_payment_received(entry_id)
                
            if success:
                QMessageBox.information(self, "Success", msg)
                self.update_balance_header()
                self.generate_ledger()
            else:
                QMessageBox.warning(self, "Error", msg)
