from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                             QDateEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QMessageBox, QCheckBox, QDialog, QGridLayout, QLineEdit, QCompleter)
from PyQt5.QtCore import Qt, QDate

class ProcurementEditDialog(QDialog):
    def __init__(self, db, procurement_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.procurement_id = procurement_id
        self.setWindowTitle("Edit Procurement")
        self.setMinimumSize(800, 600)
        self.init_ui()
        self.load_data()
        
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
        
        main_layout.addLayout(calc_layout)
        
        # --- Action Buttons ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.calc_btn = QPushButton("Calculate")
        self.calc_btn.clicked.connect(self.calculate_totals)
        btn_layout.addWidget(self.calc_btn)
        
        self.submit_btn = QPushButton("Save Changes")
        self.submit_btn.clicked.connect(self.submit_entry)
        self.submit_btn.setEnabled(False) # Disabled until calculated
        btn_layout.addWidget(self.submit_btn)
        
        main_layout.addLayout(btn_layout)
        
        # Populate suppliers
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

    def load_data(self):
        record = self.db.get_procurement_by_id(self.procurement_id)
        if not record:
            return
            
        data = record['data']
        self.entry_num_input.setText(data['entry_number'])
        self.date_input.setDate(QDate.fromString(data['date'], Qt.ISODate))
        
        index = self.supplier_combo.findData(data['supplier_id'])
        if index >= 0:
            self.supplier_combo.setCurrentIndex(index)
            
        self.total_weight_input.setText(str(data['total_weight']))
        self.rate_input.setText(str(data['rate']))
        self.base_amount_input.setText(str(data['base_amount']))
        self.remarks_input.setText(data['remarks'] or "")
        self.net_adj_input.setText(str(data['net_adjustment']))
        self.grand_total_input.setText(str(data['grand_total']))
        
        items = record['items']
        self.table.setRowCount(0)
        for item in items:
            row_count = self.table.rowCount()
            self.table.insertRow(row_count)
            self.table.setItem(row_count, 0, QTableWidgetItem(item['scrap_type']))
            self.table.setItem(row_count, 1, QTableWidgetItem(str(item['weight'])))
            self.table.setItem(row_count, 2, QTableWidgetItem(str(item['rate'])))
            self.table.setItem(row_count, 3, QTableWidgetItem(str(item['amount'])))
            self.table.setItem(row_count, 4, QTableWidgetItem(item['adjustment_type']))
            
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
            
            self.net_adj_input.setText(f"{net_adj:.2f}")
            self.grand_total_input.setText(f"{grand_total:.2f}")
            
            self.submit_btn.setEnabled(True)
        except ValueError as e:
            QMessageBox.warning(self, "Calculation Error", "Please ensure all numeric fields are valid.")
            
    def submit_entry(self):
        if not self.total_weight_input.text() or not self.rate_input.text():
            QMessageBox.warning(self, "Validation", "Total weight and rate are required.")
            return
            
        text = self.supplier_combo.currentText().strip()
        index = self.supplier_combo.findText(text, Qt.MatchFixedString)
        supplier_id = self.supplier_combo.itemData(index) if index >= 0 else None
        
        if not supplier_id:
            QMessageBox.warning(self, "Validation", "Please select a valid supplier from the list.")
            return
            
        data = {
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
            
        success, msg = self.db.update_procurement(self.procurement_id, data, items)
        if success:
            QMessageBox.information(self, "Success", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Error", msg)


class ProcurementManagementView(QWidget):
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
        self.supplier_combo.setEditable(True)
        self.supplier_combo.addItem("All Suppliers", None)
        filter_layout.addWidget(self.supplier_combo)
        
        self.date_checkbox = QCheckBox("Filter by Date:")
        filter_layout.addWidget(self.date_checkbox)
        
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd-MM-yyyy")
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
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Entry Number", "Date", "Supplier", "Base Amount", "Net Adj", "Grand Total"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        
        # --- Actions ---
        action_layout = QHBoxLayout()
        
        self.edit_btn = QPushButton("Edit Entry")
        self.edit_btn.clicked.connect(self.edit_entry)
        action_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("Delete Entry")
        self.delete_btn.setObjectName("danger_btn")
        self.delete_btn.setProperty("class", "danger")
        self.delete_btn.clicked.connect(self.delete_entry)
        action_layout.addWidget(self.delete_btn)
        
        layout.addLayout(action_layout)
        
    def refresh_data(self):
        self.supplier_combo.clear()
        self.supplier_combo.addItem("All Suppliers", None)
        suppliers = self.db.get_all_suppliers()
        names = ["All Suppliers"]
        for sup in suppliers:
            self.supplier_combo.addItem(sup[1], sup[0])
            names.append(sup[1])
            
        completer = QCompleter(names)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.supplier_combo.setCompleter(completer)
        
        self.load_data()
        
    def get_selected_filter_supplier_id(self):
        text = self.supplier_combo.currentText().strip()
        index = self.supplier_combo.findText(text, Qt.MatchFixedString)
        if index >= 0:
            return self.supplier_combo.itemData(index)
        return None
        
    def load_data(self):
        supplier_id = self.get_selected_filter_supplier_id()
        date = self.date_input.date().toString(Qt.ISODate) if self.date_checkbox.isChecked() else None
        
        entries = self.db.get_procurements(supplier_id, date)
        
        self.table.setRowCount(0)
        for row_idx, row_data in enumerate(entries):
            # p.id, p.entry_number, p.date, s.name, p.base_amount, p.net_adjustment, p.grand_total, s.id
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(row_data[1]))
            
            # Format Date
            date_obj = QDate.fromString(row_data[2], Qt.ISODate)
            f_date = date_obj.toString("dd-MM-yyyy") if date_obj.isValid() else row_data[2]
            
            self.table.setItem(row_idx, 2, QTableWidgetItem(f_date))
            self.table.setItem(row_idx, 3, QTableWidgetItem(row_data[3]))
            self.table.setItem(row_idx, 4, QTableWidgetItem(f"{row_data[4]:.2f}"))
            self.table.setItem(row_idx, 5, QTableWidgetItem(f"{row_data[5]:.2f}"))
            self.table.setItem(row_idx, 6, QTableWidgetItem(f"{row_data[6]:.2f}"))
            
    def get_selected_id(self):
        selected = self.table.selectedItems()
        if selected:
            return int(self.table.item(selected[0].row(), 0).text())
        return None
        
    def edit_entry(self):
        procurement_id = self.get_selected_id()
        if not procurement_id:
            QMessageBox.warning(self, "Selection", "Please select an entry to edit.")
            return
            
        dialog = ProcurementEditDialog(self.db, procurement_id, self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()
            
    def delete_entry(self):
        procurement_id = self.get_selected_id()
        if not procurement_id:
            QMessageBox.warning(self, "Selection", "Please select an entry to delete.")
            return
            
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     "Are you sure you want to delete this procurement entry?\nThis will update the supplier's balance.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                     
        if reply == QMessageBox.Yes:
            success, msg = self.db.delete_procurement(procurement_id)
            if success:
                QMessageBox.information(self, "Success", msg)
                self.load_data()
            else:
                QMessageBox.warning(self, "Error", msg)
