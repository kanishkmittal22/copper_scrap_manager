from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                             QDateEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QMessageBox, QCheckBox, QDialog, QFormLayout, QLineEdit)
from PyQt5.QtCore import Qt, QDate

class PaymentEditDialog(QDialog):
    def __init__(self, db, payment_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.payment_id = payment_id
        self.setWindowTitle("Edit Payment")
        self.setFixedSize(400, 300)
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.supplier_combo = QComboBox()
        form_layout.addRow("Supplier:", self.supplier_combo)
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        form_layout.addRow("Date:", self.date_input)
        
        self.amount_input = QLineEdit()
        form_layout.addRow("Amount:", self.amount_input)
        
        self.remarks_input = QLineEdit()
        form_layout.addRow("Remarks:", self.remarks_input)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.clicked.connect(self.save_payment)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        # Populate suppliers
        suppliers = self.db.get_all_suppliers()
        for sup in suppliers:
            self.supplier_combo.addItem(sup[1], sup[0])

    def load_data(self):
        data = self.db.get_payment_by_id(self.payment_id)
        if not data:
            return
            
        index = self.supplier_combo.findData(data['supplier_id'])
        if index >= 0:
            self.supplier_combo.setCurrentIndex(index)
            
        self.date_input.setDate(QDate.fromString(data['date'], Qt.ISODate))
        self.amount_input.setText(str(data['amount']))
        self.remarks_input.setText(data['remarks'] or "")
        
    def save_payment(self):
        supplier_id = self.supplier_combo.currentData()
        amount_str = self.amount_input.text().strip()
        
        if not supplier_id or not amount_str:
            QMessageBox.warning(self, "Validation", "Please fill required fields.")
            return
            
        try:
            amount = float(amount_str)
        except ValueError:
            QMessageBox.warning(self, "Validation", "Amount must be a number.")
            return
            
        data = {
            'supplier_id': supplier_id,
            'date': self.date_input.date().toString(Qt.ISODate),
            'amount': amount,
            'remarks': self.remarks_input.text()
        }
        
        success, msg = self.db.update_payment(self.payment_id, data)
        if success:
            QMessageBox.information(self, "Success", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Error", msg)


class PaymentManagementView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # --- Filters ---
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Supplier:"))
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("All Suppliers", None)
        filter_layout.addWidget(self.supplier_combo)
        
        self.date_checkbox = QCheckBox("Filter by Date:")
        filter_layout.addWidget(self.date_checkbox)
        
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setEnabled(False)
        self.date_checkbox.toggled.connect(self.date_input.setEnabled)
        filter_layout.addWidget(self.date_input)
        
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(self.search_btn)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Payment ID", "Date", "Supplier", "Amount", "Remarks"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        
        # --- Actions ---
        action_layout = QHBoxLayout()
        
        self.edit_btn = QPushButton("Edit Payment")
        self.edit_btn.clicked.connect(self.edit_entry)
        action_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete Payment")
        self.delete_btn.setObjectName("danger_btn")
        self.delete_btn.setProperty("class", "danger")
        self.delete_btn.clicked.connect(self.delete_entry)
        action_layout.addWidget(self.delete_btn)
        
        layout.addLayout(action_layout)
        
    def refresh_data(self):
        self.supplier_combo.clear()
        self.supplier_combo.addItem("All Suppliers", None)
        suppliers = self.db.get_all_suppliers()
        for sup in suppliers:
            self.supplier_combo.addItem(sup[1], sup[0])
        self.load_data()
        
    def load_data(self):
        supplier_id = self.supplier_combo.currentData()
        date = self.date_input.date().toString(Qt.ISODate) if self.date_checkbox.isChecked() else None
        
        entries = self.db.get_payments(supplier_id, date)
        
        self.table.setRowCount(0)
        for row_idx, row_data in enumerate(entries):
            # p.id, p.date, s.name, p.amount, p.remarks
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(row_data[1]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(row_data[2]))
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"{row_data[3]:.2f}"))
            self.table.setItem(row_idx, 4, QTableWidgetItem(row_data[4] or ""))
            
    def get_selected_id(self):
        selected = self.table.selectedItems()
        if selected:
            return int(self.table.item(selected[0].row(), 0).text())
        return None
        
    def edit_entry(self):
        payment_id = self.get_selected_id()
        if not payment_id:
            QMessageBox.warning(self, "Selection", "Please select a payment to edit.")
            return
            
        dialog = PaymentEditDialog(self.db, payment_id, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()
            
    def delete_entry(self):
        payment_id = self.get_selected_id()
        if not payment_id:
            QMessageBox.warning(self, "Selection", "Please select a payment to delete.")
            return
            
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     "Are you sure you want to delete this payment?\nThis will update the supplier's balance.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                     
        if reply == QMessageBox.Yes:
            success, msg = self.db.delete_payment(payment_id)
            if success:
                QMessageBox.information(self, "Success", msg)
                self.load_data()
            else:
                QMessageBox.warning(self, "Error", msg)
