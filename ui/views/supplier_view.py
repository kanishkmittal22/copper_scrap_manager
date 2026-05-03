from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QLabel, QFrame)
from PyQt5.QtCore import Qt

class SupplierView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Form Layout for Inputs
        form_layout = QHBoxLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Supplier Name")
        
        self.balance_input = QLineEdit()
        self.balance_input.setPlaceholderText("Opening Balance")
        
        self.add_btn = QPushButton("Add Supplier")
        self.add_btn.clicked.connect(self.add_supplier)
        
        self.update_btn = QPushButton("Update Selected")
        self.update_btn.clicked.connect(self.update_supplier)
        
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setObjectName("danger_btn")
        self.delete_btn.setProperty("class", "danger")
        self.delete_btn.clicked.connect(self.delete_supplier)
        
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.balance_input)
        form_layout.addWidget(self.add_btn)
        form_layout.addWidget(self.update_btn)
        form_layout.addWidget(self.delete_btn)
        
        layout.addLayout(form_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Supplier Name", "Current Balance", "Opening Balance"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        layout.addWidget(self.table)
        
        # Total Summary Section
        self.summary_frame = QFrame()
        self.summary_frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-radius: 6px;
                padding: 4px;
                margin-top: 3px;
            }
        """)
        summary_layout = QHBoxLayout(self.summary_frame)
        self.lbl_total_balance = QLabel("Total Supplier Balance: ₹0.0")
        self.lbl_total_balance.setStyleSheet("""
            font-size: 25px;
            font-weight: bold;
            color: #ecf0f1;
        """)
        self.lbl_total_balance.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        summary_layout.addStretch()
        summary_layout.addWidget(self.lbl_total_balance)
        layout.addWidget(self.summary_frame)
        
        self.refresh_data()
        
    def refresh_data(self):
        self.table.setRowCount(0)
        suppliers = self.db.get_all_suppliers()
        
        total_balance = 0.0
        
        for row_idx, row_data in enumerate(suppliers):
            self.table.insertRow(row_idx)
            # row_data is typically: id, name, current_balance, opening_balance
            total_balance += float(row_data[2])
            
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                if col_idx in [2, 3]: # format balance
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    item.setText(f"{float(value):.1f}")
                self.table.setItem(row_idx, col_idx, item)
                
        # Determine color (positive might mean they owe us or we owe them depending on accounting direction, typically green for safe, red for owe)
        # For suppliers, positive balance usually means we owe them (liability). Let's use standard coloring: red if we owe, green if safe/0.
        color = "#e74c3c" if total_balance > 0 else "#2ecc71"
        self.lbl_total_balance.setText(f"Total Supplier Balance: ₹{total_balance:.1f}")
        self.lbl_total_balance.setStyleSheet(f"""
            font-size: 25px;
            font-weight: bold;
            color: {color};
        """)
                
    def on_selection_changed(self):
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            name = self.table.item(row, 1).text()
            opening_balance = self.table.item(row, 3).text()
            
            self.name_input.setText(name)
            self.balance_input.setText(opening_balance)
            
    def get_selected_id(self):
        selected = self.table.selectedItems()
        if selected:
            return int(self.table.item(selected[0].row(), 0).text())
        return None
        
    def add_supplier(self):
        name = self.name_input.text().strip()
        balance_str = self.balance_input.text().strip()
        
        if not name or not balance_str:
            QMessageBox.warning(self, "Validation Error", "Please fill all fields.")
            return
            
        try:
            balance = float(balance_str)
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Opening balance must be a number.")
            return
            
        success, msg = self.db.add_supplier(name, balance)
        if success:
            self.name_input.clear()
            self.balance_input.clear()
            self.refresh_data()
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.warning(self, "Error", msg)
            
    def update_supplier(self):
        supplier_id = self.get_selected_id()
        if not supplier_id:
            QMessageBox.warning(self, "Selection Error", "Please select a supplier to update.")
            return
            
        name = self.name_input.text().strip()
        balance_str = self.balance_input.text().strip()
        
        if not name or not balance_str:
            QMessageBox.warning(self, "Validation Error", "Please fill all fields.")
            return
            
        try:
            balance = float(balance_str)
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Opening balance must be a number.")
            return
            
        success, msg = self.db.update_supplier(supplier_id, name, balance)
        if success:
            self.name_input.clear()
            self.balance_input.clear()
            self.refresh_data()
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.warning(self, "Error", msg)
            
    def delete_supplier(self):
        supplier_id = self.get_selected_id()
        if not supplier_id:
            QMessageBox.warning(self, "Selection Error", "Please select a supplier to delete.")
            return
            
        reply = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this supplier?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                     
        if reply == QMessageBox.Yes:
            success, msg = self.db.delete_supplier(supplier_id)
            if success:
                self.name_input.clear()
                self.balance_input.clear()
                self.refresh_data()
                QMessageBox.information(self, "Success", msg)
            else:
                QMessageBox.warning(self, "Error", msg)
