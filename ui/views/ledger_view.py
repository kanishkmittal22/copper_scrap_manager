from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                             QDateEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QCompleter)
from PyQt5.QtCore import Qt, QDate

class LedgerView(QWidget):
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
        
        # Controls
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
        
        layout.addLayout(controls_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Date", "Type", "Reference", "Credit (Purchase)", "Debit (Payment)", "Balance"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.table)
        
    def refresh_data(self):
        try:
            self.supplier_combo.currentTextChanged.disconnect(self.update_balance_header)
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
        self.supplier_combo.currentTextChanged.connect(self.update_balance_header)
        self.update_balance_header()
        
    def get_selected_supplier_id(self):
        text = self.supplier_combo.currentText().strip()
        index = self.supplier_combo.findText(text, Qt.MatchFixedString)
        if index >= 0:
            return self.supplier_combo.itemData(index)
        return None
            
    def update_balance_header(self):
        supplier_id = self.get_selected_supplier_id()
        if supplier_id:
            sup = self.db.get_supplier_by_id(supplier_id)
            if sup:
                balance = sup[2]
                color = "#27ae60" if balance >= 0 else "#e74c3c"
                self.balance_header.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {color}; margin-bottom: 10px;")
                self.balance_header.setText(f"Current Balance: ₹{balance:.2f}")
        else:
            self.balance_header.setStyleSheet("font-size: 22px; font-weight: bold; color: #27ae60; margin-bottom: 10px;")
            self.balance_header.setText("Current Balance: ₹0.00")
            
    def generate_ledger(self):
        supplier_id = self.get_selected_supplier_id()
        if not supplier_id:
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
        
        for idx, entry in enumerate(entries):
            row = idx + 1
            self.table.insertRow(row)
            
            date, e_type, ref, credit, debit = entry
            
            # Format Date
            date_obj = QDate.fromString(date, Qt.ISODate)
            f_date = date_obj.toString("dd-MM-yyyy") if date_obj.isValid() else date
            
            # Credit means supplier balance increases (We bought from them)
            # Debit means supplier balance decreases (We paid them)
            current_balance += (credit - debit)
            
            self.table.setItem(row, 0, QTableWidgetItem(f_date))
            self.table.setItem(row, 1, QTableWidgetItem(e_type))
            self.table.setItem(row, 2, QTableWidgetItem(ref))
            
            cr_item = QTableWidgetItem(f"{credit:.2f}" if credit else "")
            cr_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            # Styling for credit
            if credit:
                cr_item.setForeground(Qt.darkGreen)
            self.table.setItem(row, 3, cr_item)
            
            db_item = QTableWidgetItem(f"{debit:.2f}" if debit else "")
            db_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            # Styling for debit
            if debit:
                db_item.setForeground(Qt.red)
            self.table.setItem(row, 4, db_item)
            
            bal_item = QTableWidgetItem(f"{current_balance:.2f}")
            bal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if current_balance < 0:
                bal_item.setForeground(Qt.red)
            self.table.setItem(row, 5, bal_item)
