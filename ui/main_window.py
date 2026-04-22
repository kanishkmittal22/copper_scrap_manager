from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget, QLabel, QFrame
from PyQt5.QtCore import Qt

# Import views
from ui.views.supplier_view import SupplierView
from ui.views.procurement_view import ProcurementView
from ui.views.procurement_management_view import ProcurementManagementView
from ui.views.payment_view import PaymentView
from ui.views.payment_management_view import PaymentManagementView
from ui.views.ledger_view import LedgerView
from ui.views.customer_management_view import CustomerManagementView
from ui.views.sales_ledger_view import SalesLedgerView
from ui.views.daily_cash_book_view import DailyCashBookView
from ui.views.daily_inventory_report_view import DailyInventoryReportView

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
        
        # --- Sales Section ---
        sales_label = QLabel("--- SALES ---")
        sales_label.setStyleSheet("color: #7f8fa6; font-size: 12px; font-weight: bold; padding-left: 20px; margin-top: 15px; margin-bottom: 5px;")
        sidebar_layout.addWidget(sales_label)
        
        self.btn_customers = self.create_nav_button("👥 Customers", 6)
        self.btn_sales_ledger = self.create_nav_button("📈 Sales Ledger", 7)
        
        sidebar_layout.addWidget(self.btn_customers)
        sidebar_layout.addWidget(self.btn_sales_ledger)
        
        # --- Reports Section ---
        reports_label = QLabel("--- REPORTS ---")
        reports_label.setStyleSheet("color: #7f8fa6; font-size: 12px; font-weight: bold; padding-left: 20px; margin-top: 15px; margin-bottom: 5px;")
        sidebar_layout.addWidget(reports_label)
        
        self.btn_cash_book = self.create_nav_button("📒 Daily Cash Book", 8)
        self.btn_inventory_report = self.create_nav_button("📦 Daily Inventory", 9)
        
        sidebar_layout.addWidget(self.btn_cash_book)
        sidebar_layout.addWidget(self.btn_inventory_report)
        
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
        self.customer_view = CustomerManagementView(self.db)
        self.sales_ledger_view = SalesLedgerView(self.db)
        self.cash_book_view = DailyCashBookView(self.db)
        self.inventory_report_view = DailyInventoryReportView(self.db)
        
        self.stacked_widget.addWidget(self.supplier_view)
        self.stacked_widget.addWidget(self.procurement_view)
        self.stacked_widget.addWidget(self.proc_mgmt_view)
        self.stacked_widget.addWidget(self.payment_view)
        self.stacked_widget.addWidget(self.pay_mgmt_view)
        self.stacked_widget.addWidget(self.ledger_view)
        self.stacked_widget.addWidget(self.customer_view)
        self.stacked_widget.addWidget(self.sales_ledger_view)
        self.stacked_widget.addWidget(self.cash_book_view)
        self.stacked_widget.addWidget(self.inventory_report_view)
        
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
            "Purchase Ledger",
            "Customer Management",
            "Sales Ledger",
            "Daily Cash Book",
            "Daily Inventory Report"
        ]
        self.header_label.setText(titles[index])
        
        # Refresh data in the current view
        current_view = self.stacked_widget.currentWidget()
        if hasattr(current_view, 'refresh_data'):
            current_view.refresh_data()
