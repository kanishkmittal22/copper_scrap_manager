from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                             QDateEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLabel)
from PyQt5.QtCore import Qt, QDate

class LedgerView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Supplier:"))
        self.supplier_combo = QComboBox()
        controls_layout.addWidget(self.supplier_combo)
        
        controls_layout.addWidget(QLabel("From:"))
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        self.from_date.setCalendarPopup(True)
        controls_layout.addWidget(self.from_date)
        
        controls_layout.addWidget(QLabel("To:"))
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
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
        self.supplier_combo.clear()
        suppliers = self.db.get_all_suppliers()
        for sup in suppliers:
            self.supplier_combo.addItem(sup[1], sup[0])
            
    def generate_ledger(self):
        supplier_id = self.supplier_combo.currentData()
        if not supplier_id:
            return
            
        from_d = self.from_date.date().toString(Qt.ISODate)
        to_d = self.to_date.date().toString(Qt.ISODate)
        
        entries = self.db.get_ledger(supplier_id, from_d, to_d)
        opening_balance = self.db.get_opening_balance_for_ledger(supplier_id, from_d)
        
        self.table.setRowCount(0)
        
        # Add Opening Balance Row
        self.table.insertRow(0)
        self.table.setItem(0, 0, QTableWidgetItem(from_d))
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
            
            # Credit means supplier balance increases (We bought from them)
            # Debit means supplier balance decreases (We paid them)
            current_balance += (credit - debit)
            
            self.table.setItem(row, 0, QTableWidgetItem(date))
            self.table.setItem(row, 1, QTableWidgetItem(e_type))
            self.table.setItem(row, 2, QTableWidgetItem(ref))
            
            cr_item = QTableWidgetItem(f"{credit:.2f}" if credit else "")
            cr_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, cr_item)
            
            db_item = QTableWidgetItem(f"{debit:.2f}" if debit else "")
            db_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 4, db_item)
            
            bal_item = QTableWidgetItem(f"{current_balance:.2f}")
            bal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 5, bal_item)
