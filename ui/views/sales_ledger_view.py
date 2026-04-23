from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox, 
                             QDateEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLabel, QCompleter, QMessageBox, QDialog, QSizePolicy)
from PyQt5.QtCore import Qt, QDate
from .sales_entry_dialog import SalesEntryDialog, PaymentReceivedDialog

class SalesLedgerView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # --- Top Filters ---
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Customer:"))
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        self.customer_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        controls_layout.addWidget(self.customer_combo)
        
        controls_layout.addWidget(QLabel("From:"))
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        self.from_date.setCalendarPopup(True)
        self.from_date.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.from_date.setDisplayFormat("dd-MM-yyyy")
        controls_layout.addWidget(self.from_date)
        
        controls_layout.addWidget(QLabel("To:"))
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        self.to_date.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.to_date.setDisplayFormat("dd-MM-yyyy")
        controls_layout.addWidget(self.to_date)
        
        self.gen_btn = QPushButton("Generate Ledger")
        self.gen_btn.clicked.connect(self.generate_ledger)
        controls_layout.addWidget(self.gen_btn)
        
        self.add_sale_btn = QPushButton("Create Sales Entry")
        self.add_sale_btn.clicked.connect(self.create_sale)
        controls_layout.addWidget(self.add_sale_btn)
        
        self.add_pay_btn = QPushButton("Create Payment Received Entry")
        self.add_pay_btn.clicked.connect(self.create_payment)
        controls_layout.addWidget(self.add_pay_btn)
        
        layout.addLayout(controls_layout)
        
        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Date", "Type", "Reference", "Debit (Sales)", "Credit (Payment)", "Balance"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.table)
        
        # --- Summary Panel ---
        summary_layout = QHBoxLayout()
        
        self.lbl_tot_sales = QLabel("Total Sales\n₹0.00")
        self.lbl_tot_pay = QLabel("Total Payment Received\n₹0.00")
        self.lbl_cur_bal = QLabel("Current Balance\n₹0.00")
        
        self.card_style = """
            QLabel {
                background-color: #2c3e50;
                color: white;
                border-radius: 8px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
        """
        self.lbl_tot_sales.setStyleSheet(self.card_style)
        self.lbl_tot_pay.setStyleSheet(self.card_style)
        self.lbl_cur_bal.setStyleSheet(self.card_style)
        
        self.lbl_tot_sales.setAlignment(Qt.AlignCenter)
        self.lbl_tot_pay.setAlignment(Qt.AlignCenter)
        self.lbl_cur_bal.setAlignment(Qt.AlignCenter)
        
        summary_layout.addWidget(self.lbl_tot_sales)
        summary_layout.addWidget(self.lbl_tot_pay)
        summary_layout.addWidget(self.lbl_cur_bal)
        
        layout.addLayout(summary_layout)
        
        # --- Bottom Actions ---
        action_layout = QHBoxLayout()
        
        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.edit_btn.clicked.connect(self.edit_entry)
        action_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.delete_btn.setObjectName("danger_btn")
        self.delete_btn.setProperty("class", "danger")
        self.delete_btn.clicked.connect(self.delete_entry)
        action_layout.addWidget(self.delete_btn)
        
        layout.addLayout(action_layout)
        
    def refresh_data(self):
        try:
            self.customer_combo.currentTextChanged.disconnect(self.update_summary)
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
        self.customer_combo.currentTextChanged.connect(self.update_summary)
        self.update_summary()
        
    def get_selected_customer_id(self):
        text = self.customer_combo.currentText().strip()
        index = self.customer_combo.findText(text, Qt.MatchFixedString)
        if index >= 0:
            return self.customer_combo.itemData(index)
        return None
            
    def update_summary(self, *args):
        customer_id = self.get_selected_customer_id()
        if not customer_id:
            self.lbl_tot_sales.setText("Total Sales\n₹0.00")
            self.lbl_tot_pay.setText("Total Payment Received\n₹0.00")
            self.lbl_cur_bal.setText("Current Balance\n₹0.00")
            
    def get_selected_entry_info(self):
        selected = self.table.selectedItems()
        if not selected:
            return None, None
            
        row = selected[0].row()
        if row == 0:
            return None, None # Opening balance row
            
        t_type = self.table.item(row, 1).text()
        t_id = self.table.item(row, 0).data(Qt.UserRole)
        return t_type, t_id

    def create_sale(self):
        dialog = SalesEntryDialog(self.db, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.generate_ledger()

    def create_payment(self):
        dialog = PaymentReceivedDialog(self.db, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.generate_ledger()

    def edit_entry(self):
        t_type, t_id = self.get_selected_entry_info()
        if not t_id:
            QMessageBox.warning(self, "Selection", "Please select a valid transaction to edit.")
            return
            
        if t_type == "Sale":
            dialog = SalesEntryDialog(self.db, sale_id=t_id, parent=self)
        elif t_type == "Payment Received":
            dialog = PaymentReceivedDialog(self.db, payment_id=t_id, parent=self)
        else:
            return
            
        if dialog.exec_() == QDialog.Accepted:
            self.generate_ledger()

    def delete_entry(self):
        t_type, t_id = self.get_selected_entry_info()
        if not t_id:
            QMessageBox.warning(self, "Selection", "Please select a valid transaction to delete.")
            return
            
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete this {t_type}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                     
        if reply == QMessageBox.Yes:
            if t_type == "Sale":
                success, msg = self.db.delete_sale(t_id)
            elif t_type == "Payment Received":
                success, msg = self.db.delete_payment_received(t_id)
            else:
                return
                
            if success:
                QMessageBox.information(self, "Success", msg)
                self.generate_ledger()
            else:
                QMessageBox.warning(self, "Error", msg)

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
        total_sales = 0.0
        total_payment = 0.0
        
        for idx, entry in enumerate(entries):
            row = idx + 1
            self.table.insertRow(row)
            
            # db_manager returns: id, date, type, reference, weight, rate, remarks, debit, credit
            t_id, date, e_type, ref, weight, rate, remarks, debit, credit = entry
            
            # Format Date
            date_obj = QDate.fromString(date, Qt.ISODate)
            f_date = date_obj.toString("dd-MM-yyyy") if date_obj.isValid() else date
            
            # Sales (debit) increases customer balance, Payments (credit) decrease
            current_balance += (debit - credit)
            total_sales += debit
            total_payment += credit
            
            # Formatting Reference Details
            ref_str = ""
            if e_type == "Sale":
                ref_str = f"{ref} | {weight:.2f} kg @ {rate:.2f}"
                if remarks and remarks.strip():
                    ref_str += f" | {remarks.strip()}"
            elif e_type == "Payment Received":
                ref_str = f"PayID - {ref}"
                if remarks and remarks.strip():
                    ref_str += f" | {remarks.strip()}"
            
            item_date = QTableWidgetItem(f_date)
            item_date.setData(Qt.UserRole, t_id) # Store ID silently for edit/delete
            self.table.setItem(row, 0, item_date)
            
            self.table.setItem(row, 1, QTableWidgetItem(e_type))
            self.table.setItem(row, 2, QTableWidgetItem(ref_str))
            
            db_item = QTableWidgetItem(f"{debit:.2f}" if debit > 0 else "")
            db_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if debit > 0:
                db_item.setForeground(Qt.red) # Debit means they owe us
            self.table.setItem(row, 3, db_item)
            
            cr_item = QTableWidgetItem(f"{credit:.2f}" if credit > 0 else "")
            cr_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if credit > 0:
                cr_item.setForeground(Qt.darkGreen) # Credit means they paid
            self.table.setItem(row, 4, cr_item)
            
            bal_item = QTableWidgetItem(f"{current_balance:.2f}")
            bal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if current_balance < 0:
                bal_item.setForeground(Qt.darkGreen) # Negative balance means we owe them
            self.table.setItem(row, 5, bal_item)
            
        # Update summary label
        cust = self.db.get_customer_by_id(customer_id)
        final_balance = cust[2] if cust else 0.0
        
        color = "#2ecc71" if final_balance > 0 else "#e74c3c" # Green if they owe us (positive), red if good (<= 0)
        
        self.lbl_tot_sales.setText(f"Total Sales\n₹{total_sales:.2f}")
        self.lbl_tot_pay.setText(f"Total Payment Received\n₹{total_payment:.2f}")
        
        self.lbl_cur_bal.setText(f"Current Balance\n₹{final_balance:.2f}")
        self.lbl_cur_bal.setStyleSheet(f"""
            QLabel {{
                background-color: #2c3e50;
                color: {color};
                border-radius: 8px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }}
        """)
