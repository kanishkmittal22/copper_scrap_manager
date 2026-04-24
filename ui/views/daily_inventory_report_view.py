from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QDateEdit, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QFrame)
from PyQt5.QtCore import Qt, QDate
from collections import defaultdict

class DailyInventoryReportView(QWidget):
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
        
        input_layout.addWidget(QLabel("Opening Scrap Stock:"))
        self.opening_scrap_input = QLineEdit("0.00")
        input_layout.addWidget(self.opening_scrap_input)
        
        input_layout.addWidget(QLabel("Opening Rod Stock:"))
        self.opening_rod_input = QLineEdit("0.00")
        input_layout.addWidget(self.opening_rod_input)
        
        self.generate_btn = QPushButton("Generate Report")
        self.generate_btn.clicked.connect(self.generate_report)
        input_layout.addWidget(self.generate_btn)
        
        input_layout.addStretch()
        main_layout.addWidget(input_frame)
        
        # --- Tables Section ---
        tables_layout = QHBoxLayout()
        
        # Left Table (Scrap Inward)
        left_layout = QVBoxLayout()
        left_header = QLabel("♻️ Scrap Inward (Raw Material)")
        left_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2980b9; margin-top: 10px; margin-bottom: 5px;")
        left_layout.addWidget(left_header)
        
        self.scrap_table = QTableWidget()
        self.scrap_table.setColumnCount(3)
        self.scrap_table.setHorizontalHeaderLabels(["Supplier Name", "Quantity Details", "Total Weight"])
        self.scrap_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.scrap_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.scrap_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.scrap_table.setEditTriggers(QTableWidget.NoEditTriggers)
        left_layout.addWidget(self.scrap_table)
        
        tables_layout.addLayout(left_layout)
        
        # Right Table (Rod Outward)
        right_layout = QVBoxLayout()
        right_header = QLabel("📦 Rod Outward (Finished Goods)")
        right_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #d35400; margin-top: 10px; margin-bottom: 5px;")
        right_layout.addWidget(right_header)
        
        self.rod_table = QTableWidget()
        self.rod_table.setColumnCount(3)
        self.rod_table.setHorizontalHeaderLabels(["Customer Name", "Quantity Details", "Total Weight"])
        self.rod_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.rod_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.rod_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.rod_table.setEditTriggers(QTableWidget.NoEditTriggers)
        right_layout.addWidget(self.rod_table)
        
        tables_layout.addLayout(right_layout)
        
        main_layout.addLayout(tables_layout)
        
        # --- Calculation Section ---
        calc_frame = QFrame()
        calc_frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-radius: 6px;
                padding: 5px;
                margin-top: 5px;
            }
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ecf0f1;
            }
        """)
        calc_layout = QHBoxLayout(calc_frame)
        
        # Scrap Summary
        scrap_layout = QVBoxLayout()
        scrap_title = QLabel("--- Scrap Inventory ---")
        scrap_title.setStyleSheet("color: #3498db; font-size: 18px;")
        scrap_layout.addWidget(scrap_title)
        
        self.lbl_opening_scrap = QLabel("Opening: 0.00")
        self.lbl_inward_scrap = QLabel("Purchased: +0.00")
        self.lbl_inward_scrap.setStyleSheet("color: #2ecc71;")
        self.lbl_total_scrap = QLabel("Available Scrap: 0.00")
        self.lbl_total_scrap.setStyleSheet("font-size: 20px; color: #f1c40f;")
        
        scrap_layout.addWidget(self.lbl_opening_scrap)
        scrap_layout.addWidget(self.lbl_inward_scrap)
        scrap_layout.addWidget(self.lbl_total_scrap)
        
        calc_layout.addLayout(scrap_layout)
        calc_layout.addStretch()
        
        # Rod Summary
        rod_layout = QVBoxLayout()
        rod_title = QLabel("--- Rod Inventory ---")
        rod_title.setStyleSheet("color: #e67e22; font-size: 18px;")
        rod_layout.addWidget(rod_title)
        
        self.lbl_opening_rod = QLabel("Opening: 0.00")
        self.lbl_outward_rod = QLabel("Sold: -0.00")
        self.lbl_outward_rod.setStyleSheet("color: #e74c3c;")
        self.lbl_total_rod = QLabel("Remaining Rods: 0.00")
        self.lbl_total_rod.setStyleSheet("font-size: 20px; color: #f1c40f;")
        
        rod_layout.addWidget(self.lbl_opening_rod)
        rod_layout.addWidget(self.lbl_outward_rod)
        rod_layout.addWidget(self.lbl_total_rod)
        
        calc_layout.addLayout(rod_layout)
        
        main_layout.addWidget(calc_frame)
        
    def generate_report(self):
        date_str = self.date_input.date().toString(Qt.ISODate)
        try:
            opening_scrap = float(self.opening_scrap_input.text() or 0)
            opening_rod = float(self.opening_rod_input.text() or 0)
        except ValueError:
            opening_scrap = 0.0
            opening_rod = 0.0
            
        scrap_inward_data = self.db.get_daily_scrap_inward(date_str)
        rod_outward_data = self.db.get_daily_rod_outward(date_str)
        
        total_scrap_purchased = self.populate_table(self.scrap_table, scrap_inward_data)
        total_rod_sold = self.populate_table(self.rod_table, rod_outward_data)
        
        available_scrap = opening_scrap + total_scrap_purchased
        remaining_rod = opening_rod - total_rod_sold
        
        # Update summary labels
        self.lbl_opening_scrap.setText(f"Opening: {opening_scrap:.2f}")
        self.lbl_inward_scrap.setText(f"Purchased: +{total_scrap_purchased:.2f}")
        self.lbl_total_scrap.setText(f"Available Scrap: {available_scrap:.2f}")
        
        self.lbl_opening_rod.setText(f"Opening: {opening_rod:.2f}")
        self.lbl_outward_rod.setText(f"Sold: -{total_rod_sold:.2f}")
        self.lbl_total_rod.setText(f"Remaining Rods: {remaining_rod:.2f}")
        
    def populate_table(self, table, data):
        # Group data by party name
        grouped = defaultdict(list)
        for name, weight in data:
            grouped[name].append(weight)
            
        table.setRowCount(0)
        grand_total = 0.0
        
        row_idx = 0
        for name, weights in grouped.items():
            table.insertRow(row_idx)
            
            # Name
            table.setItem(row_idx, 0, QTableWidgetItem(name))
            
            # Details string (e.g., "(100 + 200)")
            details_str = ""
            if len(weights) > 1:
                details_str = "(" + " + ".join(f"{w:.2f}" for w in weights) + ")"
            else:
                details_str = f"{weights[0]:.2f}"
                
            table.setItem(row_idx, 1, QTableWidgetItem(details_str))
            
            # Total for this party
            party_total = sum(weights)
            grand_total += party_total
            
            total_item = QTableWidgetItem(f"{party_total:.2f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(row_idx, 2, total_item)
            
            row_idx += 1
            
        return grand_total
