from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox, 
                             QDateEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QCompleter, QMessageBox)
from PyQt5.QtCore import Qt, QDate

from ui.views.procurement_entry_dialog import ProcurementEntryDialog
from ui.views.payment_entry_dialog import PaymentEntryDialog

class LedgerView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # --- Top Filters ---
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Supplier:"))
        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(True)
        controls_layout.addWidget(self.supplier_combo)
        
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
        
        self.add_proc_btn = QPushButton("Create Procurement")
        self.add_proc_btn.clicked.connect(self.create_procurement)
        controls_layout.addWidget(self.add_proc_btn)
        
        self.add_pay_btn = QPushButton("Create Payment")
        self.add_pay_btn.clicked.connect(self.create_payment)
        controls_layout.addWidget(self.add_pay_btn)
        
        layout.addLayout(controls_layout)
        
        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Date", "Type", "Reference", "Debit (Purchase)", "Credit (Payment)", "Balance"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.table)
        
        # --- Summary Panel ---
        summary_layout = QHBoxLayout()
        
        self.lbl_tot_proc = QLabel("Total Procurement\n₹0.00")
        self.lbl_tot_pay = QLabel("Total Payment\n₹0.00")
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
        self.lbl_tot_proc.setStyleSheet(self.card_style)
        self.lbl_tot_pay.setStyleSheet(self.card_style)
        self.lbl_cur_bal.setStyleSheet(self.card_style)
        
        self.lbl_tot_proc.setAlignment(Qt.AlignCenter)
        self.lbl_tot_pay.setAlignment(Qt.AlignCenter)
        self.lbl_cur_bal.setAlignment(Qt.AlignCenter)
        
        summary_layout.addWidget(self.lbl_tot_proc)
        summary_layout.addWidget(self.lbl_tot_pay)
        summary_layout.addWidget(self.lbl_cur_bal)
        
        layout.addLayout(summary_layout)
        
        # --- Bottom Actions ---
        action_layout = QHBoxLayout()
        
        from PyQt5.QtWidgets import QSizePolicy
        
        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.edit_btn.clicked.connect(self.edit_entry)
        # self.edit_btn.setEnabled(False)
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
            self.supplier_combo.currentTextChanged.disconnect(self.update_summary)
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
        self.supplier_combo.currentTextChanged.connect(self.update_summary)
        self.update_summary()
        
    def get_selected_supplier_id(self):
        text = self.supplier_combo.currentText().strip()
        index = self.supplier_combo.findText(text, Qt.MatchFixedString)
        if index >= 0:
            return self.supplier_combo.itemData(index)
        return None
            
    def update_summary(self, *args):
        supplier_id = self.get_selected_supplier_id()
        if not supplier_id:
            self.lbl_tot_proc.setText("Total Procurement\n₹0.00")
            self.lbl_tot_pay.setText("Total Payment\n₹0.00")
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

    def create_procurement(self):
        dialog = ProcurementEntryDialog(self.db, parent=self)
        if dialog.exec_():
            self.generate_ledger()

    def create_payment(self):
        dialog = PaymentEntryDialog(self.db, parent=self)
        if dialog.exec_():
            self.generate_ledger()

    def edit_entry(self):
        t_type, t_id = self.get_selected_entry_info()
        if not t_id:
            QMessageBox.warning(self, "Selection", "Please select a valid transaction to edit.")
            return
        
        if t_type == "Procurement":
            dialog = ProcurementEntryDialog(self.db, procurement_id=t_id, parent=self)
            if dialog.exec_():
                self.generate_ledger()
        elif t_type == "Payment":
            dialog = PaymentEntryDialog(self.db, payment_id=t_id, parent=self)
            if dialog.exec_():
                self.generate_ledger()

    def delete_entry(self):
        t_type, t_id = self.get_selected_entry_info()
        if not t_id:
            QMessageBox.warning(self, "Selection", "Please select a valid transaction to delete.")
            return
        
        reply = QMessageBox.question(self, 'Confirm Deletion', 
                                     f"Are you sure you want to delete this {t_type}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                     
        if reply == QMessageBox.Yes:
            if t_type == "Procurement":
                success, msg = self.db.delete_procurement(t_id)
            elif t_type == "Payment":
                success, msg = self.db.delete_payment(t_id)
            else:
                return
                
            if success:
                QMessageBox.information(self, "Success", msg)
                self.generate_ledger()
            else:
                QMessageBox.warning(self, "Error", msg)

    def generate_ledger(self):
        supplier_id = self.get_selected_supplier_id()
        if not supplier_id:
            QMessageBox.warning(self, "Warning", "Please select a valid supplier.")
            return
            
        from_d = self.from_date.date().toString(Qt.ISODate)
        to_d = self.to_date.date().toString(Qt.ISODate)
        
        entries = self.db.get_ledger(supplier_id, from_d, to_d)
        opening_balance = self.db.get_opening_balance_for_ledger(supplier_id, from_d)
        
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
        total_procurement = 0.0
        total_payment = 0.0
        
        for idx, entry in enumerate(entries):
            row = idx + 1
            self.table.insertRow(row)
            
            # db_manager returns: id, date, type, entry_number/id, weight, rate, remarks, debit, credit
            t_id, date, e_type, ref, weight, rate, remarks, debit, credit = entry
            
            date_obj = QDate.fromString(date, Qt.ISODate)
            f_date = date_obj.toString("dd-MM-yyyy") if date_obj.isValid() else date
            
            # Debit = Purchase Amount (Procurement) -> Supplier balance increases
            # Credit = Payment Amount -> Supplier balance decreases
            current_balance += (debit - credit)
            total_procurement += debit
            total_payment += credit
            
            # Formatting Reference Details
            ref_str = ""
            if e_type == "Procurement":
                ref_str = f"{ref} | {weight:.2f} kg @ {rate:.2f}"
                if remarks and remarks.strip():
                    ref_str += f" | {remarks.strip()}"
            elif e_type == "Payment":
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
                db_item.setForeground(Qt.red)
            self.table.setItem(row, 3, db_item)
            
            cr_item = QTableWidgetItem(f"{credit:.2f}" if credit > 0 else "")
            cr_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if credit > 0:
                cr_item.setForeground(Qt.darkGreen)
            self.table.setItem(row, 4, cr_item)
            
            bal_item = QTableWidgetItem(f"{current_balance:.2f}")
            bal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if current_balance < 0:
                bal_item.setForeground(Qt.darkGreen) # Supplier balance is our liability, negative means they owe us
            self.table.setItem(row, 5, bal_item)
            
        # Update summary label
        sup = self.db.get_supplier_by_id(supplier_id)
        final_balance = sup[2] if sup else 0.0 # Or current_balance if only for date range
        
        color = "#2ecc71" if final_balance <= 0 else "#e74c3c" # green if we are good, red if we owe them
        
        self.lbl_tot_proc.setText(f"Total Procurement\n₹{total_procurement:.2f}")
        self.lbl_tot_pay.setText(f"Total Payment\n₹{total_payment:.2f}")
        
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
