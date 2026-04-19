from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QComboBox, 
                             QLineEdit, QDateEdit, QPushButton, QMessageBox, QLabel)
from PyQt5.QtCore import Qt, QDate

class PaymentView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        self.supplier_combo = QComboBox()
        self.supplier_combo.currentIndexChanged.connect(self.on_supplier_changed)
        form_layout.addRow("Supplier:", self.supplier_combo)
        
        self.current_balance_label = QLabel("0.00")
        self.current_balance_label.setStyleSheet("font-weight: bold; color: #2f3640;")
        form_layout.addRow("Current Balance:", self.current_balance_label)
        
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        form_layout.addRow("Date:", self.date_input)
        
        self.amount_input = QLineEdit()
        form_layout.addRow("Amount:", self.amount_input)
        
        self.remarks_input = QLineEdit()
        form_layout.addRow("Remarks:", self.remarks_input)
        
        self.submit_btn = QPushButton("Record Payment")
        self.submit_btn.clicked.connect(self.record_payment)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.submit_btn)
        
    def refresh_data(self):
        self.supplier_combo.clear()
        suppliers = self.db.get_all_suppliers()
        for sup in suppliers:
            self.supplier_combo.addItem(sup[1], sup[0])
            
        self.on_supplier_changed()
            
    def on_supplier_changed(self):
        supplier_id = self.supplier_combo.currentData()
        if supplier_id:
            sup = self.db.get_supplier_by_id(supplier_id)
            if sup:
                self.current_balance_label.setText(f"{sup[2]:.2f}")
                
    def record_payment(self):
        supplier_id = self.supplier_combo.currentData()
        amount_str = self.amount_input.text().strip()
        
        if not supplier_id or not amount_str:
            QMessageBox.warning(self, "Validation", "Please fill all required fields.")
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
        
        success, msg = self.db.add_payment(data)
        if success:
            QMessageBox.information(self, "Success", msg)
            self.amount_input.clear()
            self.remarks_input.clear()
            self.refresh_data()
        else:
            QMessageBox.warning(self, "Error", msg)
