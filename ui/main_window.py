from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget, QLabel, QFrame
from PyQt5.QtCore import Qt

# Import views
from ui.views.supplier_view import SupplierView
from ui.views.procurement_view import ProcurementView
from ui.views.procurement_management_view import ProcurementManagementView
from ui.views.payment_view import PaymentView
from ui.views.payment_management_view import PaymentManagementView
from ui.views.ledger_view import LedgerView

class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Copper Scrap Manager - Admin")
        self.setMinimumSize(1200, 800)
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Sidebar ---
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 0)
        sidebar_layout.setSpacing(5)
        
        # App Title in Sidebar
        app_title = QLabel("Scrap Manager")
        app_title.setStyleSheet("color: #00a8ff; font-size: 20px; font-weight: bold; padding: 10px 20px; margin-bottom: 20px;")
        sidebar_layout.addWidget(app_title)
        
        # Navigation Buttons
        self.nav_buttons = []
        
        self.btn_suppliers = self.create_nav_button("🏢 Suppliers", 0)
        self.btn_procurement = self.create_nav_button("🛒 New Procurement", 1)
        self.btn_proc_mgmt = self.create_nav_button("📋 Manage Procurements", 2)
        self.btn_payments = self.create_nav_button("💳 New Payment", 3)
        self.btn_pay_mgmt = self.create_nav_button("💸 Manage Payments", 4)
        self.btn_ledger = self.create_nav_button("📊 Purchase Ledger", 5)
        
        sidebar_layout.addWidget(self.btn_suppliers)
        sidebar_layout.addWidget(self.btn_procurement)
        sidebar_layout.addWidget(self.btn_proc_mgmt)
        sidebar_layout.addWidget(self.btn_payments)
        sidebar_layout.addWidget(self.btn_pay_mgmt)
        sidebar_layout.addWidget(self.btn_ledger)
        sidebar_layout.addStretch()
        
        # Logout button
        btn_logout = QPushButton("🚪 Logout")
        btn_logout.clicked.connect(self.close)
        sidebar_layout.addWidget(btn_logout)
        
        main_layout.addWidget(self.sidebar)
        
        # --- Main Content Area ---
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        
        self.header_label = QLabel("Dashboard")
        self.header_label.setObjectName("headerLabel")
        content_layout.addWidget(self.header_label)
        
        self.stacked_widget = QStackedWidget()
        
        # Add Views
        self.supplier_view = SupplierView(self.db)
        self.procurement_view = ProcurementView(self.db)
        self.proc_mgmt_view = ProcurementManagementView(self.db)
        self.payment_view = PaymentView(self.db)
        self.pay_mgmt_view = PaymentManagementView(self.db)
        self.ledger_view = LedgerView(self.db)
        
        self.stacked_widget.addWidget(self.supplier_view)
        self.stacked_widget.addWidget(self.procurement_view)
        self.stacked_widget.addWidget(self.proc_mgmt_view)
        self.stacked_widget.addWidget(self.payment_view)
        self.stacked_widget.addWidget(self.pay_mgmt_view)
        self.stacked_widget.addWidget(self.ledger_view)
        
        content_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(content_widget)
        
        # Initialize
        self.switch_page(0)
        
    def create_nav_button(self, text, index):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self.switch_page(index))
        self.nav_buttons.append(btn)
        return btn
        
    def switch_page(self, index):
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
            
        self.stacked_widget.setCurrentIndex(index)
        
        # Update header
        titles = [
            "Supplier Management", 
            "New Scrap Procurement", 
            "Manage Procurement Entries",
            "New Payment Entry", 
            "Manage Payment Entries",
            "Purchase Ledger"
        ]
        self.header_label.setText(titles[index])
        
        # Refresh data in the current view
        current_view = self.stacked_widget.currentWidget()
        if hasattr(current_view, 'refresh_data'):
            current_view.refresh_data()
