from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QComboBox, 
                             QLineEdit, QDateEdit, QPushButton, QMessageBox, QLabel, QCompleter)
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
        self.supplier_combo.setEditable(True)
        form_layout.addRow("Supplier:", self.supplier_combo)
        
        self.current_balance_label = QLabel("0.00")
        self.current_balance_label.setStyleSheet("font-weight: bold; color: #2f3640;")
        form_layout.addRow("Current Balance:", self.current_balance_label)
        
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd-MM-yyyy")
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
        try:
            self.supplier_combo.currentTextChanged.disconnect(self.on_supplier_changed)
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
        self.supplier_combo.currentTextChanged.connect(self.on_supplier_changed)
        self.on_supplier_changed()
            
    def get_selected_supplier_id(self):
        text = self.supplier_combo.currentText().strip()
        index = self.supplier_combo.findText(text, Qt.MatchFixedString)
        if index >= 0:
            return self.supplier_combo.itemData(index)
        return None
        
    def on_supplier_changed(self):
        supplier_id = self.get_selected_supplier_id()
        if supplier_id:
            sup = self.db.get_supplier_by_id(supplier_id)
            if sup:
                self.current_balance_label.setText(f"{sup[2]:.2f}")
        else:
            self.current_balance_label.setText("0.00")
                
    def record_payment(self):
        supplier_id = self.get_selected_supplier_id()
        amount_str = self.amount_input.text().strip()
        
        if not supplier_id or not amount_str:
            QMessageBox.warning(self, "Validation", "Please select a valid supplier and fill all required fields.")
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
