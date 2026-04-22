from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QLineEdit, QComboBox, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDateEdit, QCompleter)
from PyQt5.QtCore import Qt, QDate

class ProcurementView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- Header Section ---
        header_layout = QGridLayout()
        
        header_layout.addWidget(QLabel("Entry Number:"), 0, 0)
        self.entry_num_input = QLineEdit()
        self.entry_num_input.setReadOnly(True)
        header_layout.addWidget(self.entry_num_input, 0, 1)
        
        header_layout.addWidget(QLabel("Date:"), 0, 2)
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd-MM-yyyy")
        header_layout.addWidget(self.date_input, 0, 3)
        
        header_layout.addWidget(QLabel("Supplier:"), 1, 0)
        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(True)
        header_layout.addWidget(self.supplier_combo, 1, 1)
        
        header_layout.addWidget(QLabel("Total Weight:"), 1, 2)
        self.total_weight_input = QLineEdit()
        self.total_weight_input.textChanged.connect(self.calculate_base_amount)
        header_layout.addWidget(self.total_weight_input, 1, 3)
        
        header_layout.addWidget(QLabel("Rate:"), 2, 0)
        self.rate_input = QLineEdit()
        self.rate_input.textChanged.connect(self.calculate_base_amount)
        header_layout.addWidget(self.rate_input, 2, 1)
        
        header_layout.addWidget(QLabel("Base Amount:"), 2, 2)
        self.base_amount_input = QLineEdit()
        self.base_amount_input.setReadOnly(True)
        header_layout.addWidget(self.base_amount_input, 2, 3)
        
        header_layout.addWidget(QLabel("Remarks:"), 3, 0)
        self.remarks_input = QLineEdit()
        header_layout.addWidget(self.remarks_input, 3, 1, 1, 3)
        
        main_layout.addLayout(header_layout)
        
        # --- Line Items Section ---
        main_layout.addWidget(QLabel("<b>Line Items (Adjustments)</b>"))
        
        item_layout = QHBoxLayout()
        self.scrap_type_input = QLineEdit()
        self.scrap_type_input.setPlaceholderText("Scrap Type")
        item_layout.addWidget(self.scrap_type_input)
        
        self.item_weight_input = QLineEdit()
        self.item_weight_input.setPlaceholderText("Weight")
        self.item_weight_input.textChanged.connect(self.calculate_item_amount)
        item_layout.addWidget(self.item_weight_input)
        
        self.item_rate_input = QLineEdit()
        self.item_rate_input.setPlaceholderText("Rate")
        self.item_rate_input.textChanged.connect(self.calculate_item_amount)
        item_layout.addWidget(self.item_rate_input)
        
        self.item_amount_input = QLineEdit()
        self.item_amount_input.setPlaceholderText("Amount")
        self.item_amount_input.setReadOnly(True)
        item_layout.addWidget(self.item_amount_input)
        
        self.adj_type_combo = QComboBox()
        self.adj_type_combo.addItems(["Add", "Deduct"])
        item_layout.addWidget(self.adj_type_combo)
        
        add_item_btn = QPushButton("Add Item")
        add_item_btn.clicked.connect(self.add_line_item)
        item_layout.addWidget(add_item_btn)
        
        del_item_btn = QPushButton("Remove Selected")
        del_item_btn.clicked.connect(self.remove_line_item)
        item_layout.addWidget(del_item_btn)
        
        main_layout.addLayout(item_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Scrap Type", "Weight", "Rate", "Amount", "Adj Type"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.table)
        
        # --- Calculations Section ---
        calc_layout = QGridLayout()
        
        calc_layout.addWidget(QLabel("Net Adjustment:"), 0, 0)
        self.net_adj_input = QLineEdit("0.00")
        self.net_adj_input.setReadOnly(True)
        calc_layout.addWidget(self.net_adj_input, 0, 1)
        
        calc_layout.addWidget(QLabel("Grand Total:"), 0, 2)
        self.grand_total_input = QLineEdit("0.00")
        self.grand_total_input.setReadOnly(True)
        calc_layout.addWidget(self.grand_total_input, 0, 3)
        
        calc_layout.addWidget(QLabel("Previous Balance:"), 1, 0)
        self.prev_balance_input = QLineEdit("0.00")
        self.prev_balance_input.setReadOnly(True)
        calc_layout.addWidget(self.prev_balance_input, 1, 1)
        
        calc_layout.addWidget(QLabel("New Balance:"), 1, 2)
        self.new_balance_input = QLineEdit("0.00")
        self.new_balance_input.setReadOnly(True)
        calc_layout.addWidget(self.new_balance_input, 1, 3)
        
        main_layout.addLayout(calc_layout)
        
        # --- Action Buttons ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.calc_btn = QPushButton("Calculate")
        self.calc_btn.clicked.connect(self.calculate_totals)
        btn_layout.addWidget(self.calc_btn)
        
        self.submit_btn = QPushButton("Submit Entry")
        self.submit_btn.clicked.connect(self.submit_entry)
        self.submit_btn.setEnabled(False) # Disabled until calculated
        btn_layout.addWidget(self.submit_btn)
        
        main_layout.addLayout(btn_layout)
        
    def refresh_data(self):
        self.entry_num_input.setText(self.db.generate_entry_number())
        
        try:
            self.supplier_combo.currentTextChanged.disconnect(self.on_supplier_changed)
        except TypeError:
            pass
            
        # Populate suppliers
        self.supplier_combo.clear()
        suppliers = self.db.get_all_suppliers()
        names = []
        for sup in suppliers:
            # id, name, current_balance, opening_balance
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
                self.prev_balance_input.setText(f"{sup[2]:.2f}")
        else:
            self.prev_balance_input.setText("0.00")
        self.submit_btn.setEnabled(False)
        
    def calculate_base_amount(self):
        try:
            w = float(self.total_weight_input.text() or 0)
            r = float(self.rate_input.text() or 0)
            self.base_amount_input.setText(f"{w * r:.2f}")
            self.submit_btn.setEnabled(False)
        except ValueError:
            pass
            
    def calculate_item_amount(self):
        try:
            w = float(self.item_weight_input.text() or 0)
            r = float(self.item_rate_input.text() or 0)
            self.item_amount_input.setText(f"{w * r:.2f}")
        except ValueError:
            pass
            
    def add_line_item(self):
        stype = self.scrap_type_input.text().strip()
        weight = self.item_weight_input.text().strip()
        rate = self.item_rate_input.text().strip()
        amount = self.item_amount_input.text().strip()
        adj_type = self.adj_type_combo.currentText()
        
        if not all([stype, weight, rate, amount]):
            QMessageBox.warning(self, "Validation", "Please fill all line item fields.")
            return
            
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        self.table.setItem(row_count, 0, QTableWidgetItem(stype))
        self.table.setItem(row_count, 1, QTableWidgetItem(weight))
        self.table.setItem(row_count, 2, QTableWidgetItem(rate))
        self.table.setItem(row_count, 3, QTableWidgetItem(amount))
        self.table.setItem(row_count, 4, QTableWidgetItem(adj_type))
        
        # Clear inputs
        self.scrap_type_input.clear()
        self.item_weight_input.clear()
        self.item_rate_input.clear()
        self.item_amount_input.clear()
        self.submit_btn.setEnabled(False)
        
    def remove_line_item(self):
        selected = self.table.selectedItems()
        if selected:
            self.table.removeRow(selected[0].row())
            self.submit_btn.setEnabled(False)
            
    def calculate_totals(self):
        try:
            base_amount = float(self.base_amount_input.text() or 0)
            
            net_adj = 0.0
            for row in range(self.table.rowCount()):
                amount = float(self.table.item(row, 3).text())
                adj_type = self.table.item(row, 4).text()
                if adj_type == "Add":
                    net_adj += amount
                else:
                    net_adj -= amount
                    
            grand_total = base_amount + net_adj
            prev_balance = float(self.prev_balance_input.text() or 0)
            new_balance = prev_balance + grand_total
            
            self.net_adj_input.setText(f"{net_adj:.2f}")
            self.grand_total_input.setText(f"{grand_total:.2f}")
            self.new_balance_input.setText(f"{new_balance:.2f}")
            
            self.submit_btn.setEnabled(True)
        except ValueError as e:
            QMessageBox.warning(self, "Calculation Error", "Please ensure all numeric fields are valid.")
            
    def submit_entry(self):
        if not self.total_weight_input.text() or not self.rate_input.text():
            QMessageBox.warning(self, "Validation", "Total weight and rate are required.")
            return
            
        supplier_id = self.get_selected_supplier_id()
        if not supplier_id:
            QMessageBox.warning(self, "Validation", "Please select a valid supplier from the list.")
            return
            
        data = {
            'entry_number': self.entry_num_input.text(),
            'date': self.date_input.date().toString(Qt.ISODate),
            'supplier_id': supplier_id,
            'total_weight': float(self.total_weight_input.text()),
            'rate': float(self.rate_input.text()),
            'base_amount': float(self.base_amount_input.text()),
            'remarks': self.remarks_input.text(),
            'net_adjustment': float(self.net_adj_input.text()),
            'grand_total': float(self.grand_total_input.text())
        }
        
        items = []
        for row in range(self.table.rowCount()):
            items.append({
                'scrap_type': self.table.item(row, 0).text(),
                'weight': float(self.table.item(row, 1).text()),
                'rate': float(self.table.item(row, 2).text()),
                'amount': float(self.table.item(row, 3).text()),
                'adjustment_type': self.table.item(row, 4).text()
            })
            
        success, msg = self.db.add_procurement(data, items)
        if success:
            QMessageBox.information(self, "Success", msg)
            self.clear_form()
            self.refresh_data()
        else:
            QMessageBox.warning(self, "Error", msg)
            
    def clear_form(self):
        self.total_weight_input.clear()
        self.rate_input.clear()
        self.base_amount_input.clear()
        self.remarks_input.clear()
        self.table.setRowCount(0)
        self.net_adj_input.setText("0.00")
        self.grand_total_input.setText("0.00")
        self.new_balance_input.setText("0.00")
        self.submit_btn.setEnabled(False)
