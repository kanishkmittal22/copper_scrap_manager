from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt

class CustomerManagementView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Form Layout for Inputs
        form_layout = QHBoxLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Customer Name")
        
        self.balance_input = QLineEdit()
        self.balance_input.setPlaceholderText("Opening Balance")
        
        self.add_btn = QPushButton("Add Customer")
        self.add_btn.clicked.connect(self.add_customer)
        
        self.update_btn = QPushButton("Update Selected")
        self.update_btn.clicked.connect(self.update_customer)
        
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setObjectName("danger_btn")
        self.delete_btn.setProperty("class", "danger")
        self.delete_btn.clicked.connect(self.delete_customer)
        
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.balance_input)
        form_layout.addWidget(self.add_btn)
        form_layout.addWidget(self.update_btn)
        form_layout.addWidget(self.delete_btn)
        
        layout.addLayout(form_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Customer Name", "Current Balance", "Opening Balance"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        layout.addWidget(self.table)
        
        self.refresh_data()
        
    def refresh_data(self):
        self.table.setRowCount(0)
        customers = self.db.get_all_customers()
        
        for row_idx, row_data in enumerate(customers):
            self.table.insertRow(row_idx)
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                if col_idx in [2, 3]: # format balance
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    item.setText(f"{float(value):.2f}")
                self.table.setItem(row_idx, col_idx, item)
                
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
        
    def add_customer(self):
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
            
        success, msg = self.db.add_customer(name, balance)
        if success:
            self.name_input.clear()
            self.balance_input.clear()
            self.refresh_data()
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.warning(self, "Error", msg)
            
    def update_customer(self):
        customer_id = self.get_selected_id()
        if not customer_id:
            QMessageBox.warning(self, "Selection Error", "Please select a customer to update.")
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
            
        success, msg = self.db.update_customer(customer_id, name, balance)
        if success:
            self.name_input.clear()
            self.balance_input.clear()
            self.refresh_data()
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.warning(self, "Error", msg)
            
    def delete_customer(self):
        customer_id = self.get_selected_id()
        if not customer_id:
            QMessageBox.warning(self, "Selection Error", "Please select a customer to delete.")
            return
            
        reply = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this customer?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                     
        if reply == QMessageBox.Yes:
            success, msg = self.db.delete_customer(customer_id)
            if success:
                self.name_input.clear()
                self.balance_input.clear()
                self.refresh_data()
                QMessageBox.information(self, "Success", msg)
            else:
                QMessageBox.warning(self, "Error", msg)
