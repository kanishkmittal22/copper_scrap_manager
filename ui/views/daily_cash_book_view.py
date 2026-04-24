from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QDateEdit, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QFrame)
from PyQt5.QtCore import Qt, QDate
from collections import defaultdict

class DailyCashBookView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- Top Input Section ---
        input_frame = QFrame()
        input_layout = QHBoxLayout(input_frame)
        
        input_layout.addWidget(QLabel("Date:"))
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd-MM-yyyy")
        input_layout.addWidget(self.date_input)
        
        input_layout.addWidget(QLabel("Opening Cash Balance:"))
        self.opening_balance_input = QLineEdit("0.00")
        input_layout.addWidget(self.opening_balance_input)
        
        self.generate_btn = QPushButton("Generate Cash Book")
        self.generate_btn.clicked.connect(self.generate_report)
        input_layout.addWidget(self.generate_btn)
        
        input_layout.addStretch()
        main_layout.addWidget(input_frame)
        
        # --- Tables Section ---
        tables_layout = QHBoxLayout()
        
        # Left Table (Inflows)
        left_layout = QVBoxLayout()
        left_header = QLabel("🟢 Cash Receipts (Inflows)")
        left_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60; margin-top: 10px; margin-bottom: 5px;")
        left_layout.addWidget(left_header)
        
        self.inflows_table = QTableWidget()
        self.inflows_table.setColumnCount(3)
        self.inflows_table.setHorizontalHeaderLabels(["Customer Name", "Amount Details", "Total Amount"])
        self.inflows_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.inflows_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.inflows_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.inflows_table.setEditTriggers(QTableWidget.NoEditTriggers)
        left_layout.addWidget(self.inflows_table)
        
        tables_layout.addLayout(left_layout)
        
        # Right Table (Outflows)
        right_layout = QVBoxLayout()
        right_header = QLabel("🔴 Cash Payments (Outflows)")
        right_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c; margin-top: 10px; margin-bottom: 5px;")
        right_layout.addWidget(right_header)
        
        self.outflows_table = QTableWidget()
        self.outflows_table.setColumnCount(3)
        self.outflows_table.setHorizontalHeaderLabels(["Supplier Name", "Amount Details", "Total Amount"])
        self.outflows_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.outflows_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.outflows_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.outflows_table.setEditTriggers(QTableWidget.NoEditTriggers)
        right_layout.addWidget(self.outflows_table)
        
        tables_layout.addLayout(right_layout)
        
        main_layout.addLayout(tables_layout)
        
        # --- Calculation Section ---
        calc_frame = QFrame()
        calc_frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-radius: 6px;
                padding: 8px;
                margin-top: 10px;
            }
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #ecf0f1;
            }
        """)
        calc_layout = QHBoxLayout(calc_frame)
        
        self.lbl_opening = QLabel("Opening: ₹0.00")
        self.lbl_inflows = QLabel("Inflows: +₹0.00")
        self.lbl_inflows.setStyleSheet("color: #2ecc71;")
        self.lbl_outflows = QLabel("Outflows: -₹0.00")
        self.lbl_outflows.setStyleSheet("color: #e74c3c;")
        self.lbl_closing = QLabel("Closing Balance: ₹0.00")
        self.lbl_closing.setStyleSheet("font-size: 22px; color: #f1c40f;")
        
        calc_layout.addWidget(self.lbl_opening)
        calc_layout.addWidget(self.lbl_inflows)
        calc_layout.addWidget(self.lbl_outflows)
        calc_layout.addStretch()
        calc_layout.addWidget(self.lbl_closing)
        
        main_layout.addWidget(calc_frame)
        
    def generate_report(self):
        date_str = self.date_input.date().toString(Qt.ISODate)
        try:
            opening_balance = float(self.opening_balance_input.text() or 0)
        except ValueError:
            opening_balance = 0.0
            
        inflows_data = self.db.get_daily_cash_inflows(date_str)
        outflows_data = self.db.get_daily_cash_outflows(date_str)
        
        total_inflows = self.populate_table(self.inflows_table, inflows_data)
        total_outflows = self.populate_table(self.outflows_table, outflows_data)
        
        closing_balance = opening_balance + total_inflows - total_outflows
        
        # Update summary labels
        self.lbl_opening.setText(f"Opening: ₹{opening_balance:.2f}")
        self.lbl_inflows.setText(f"Inflows: +₹{total_inflows:.2f}")
        self.lbl_outflows.setText(f"Outflows: -₹{total_outflows:.2f}")
        self.lbl_closing.setText(f"Closing Balance: ₹{closing_balance:.2f}")
        
    def populate_table(self, table, data):
        # Group data by party name
        grouped = defaultdict(list)
        for name, amount in data:
            grouped[name].append(amount)
            
        table.setRowCount(0)
        grand_total = 0.0
        
        row_idx = 0
        for name, amounts in grouped.items():
            table.insertRow(row_idx)
            
            # Name
            table.setItem(row_idx, 0, QTableWidgetItem(name))
            
            # Details string (e.g., "(100 + 200)")
            details_str = ""
            if len(amounts) > 1:
                details_str = "(" + " + ".join(f"{a:.2f}" for a in amounts) + ")"
            else:
                details_str = f"{amounts[0]:.2f}"
                
            table.setItem(row_idx, 1, QTableWidgetItem(details_str))
            
            # Total for this party
            party_total = sum(amounts)
            grand_total += party_total
            
            total_item = QTableWidgetItem(f"{party_total:.2f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(row_idx, 2, total_item)
            
            row_idx += 1
            
        return grand_total
