# =============================
# Imports
# =============================
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import uuid
from typing import Dict
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# =============================
# Streamlit Page Configuration
# =============================
st.set_page_config(
    page_title="Price Calculator",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================
# Custom CSS for Styling
# =============================
st.markdown("""
<style>
    /* Glass Effect and Animations */
    .glass-effect {
        background: rgba(255, 255, 255, 0.7) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        border-radius: 10px !important;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37) !important;
    }
    
    .slide-in {
        animation: slideIn 0.5s ease-out;
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    .scale-in {
        animation: scaleIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(-20px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes scaleIn {
        from {
            transform: scale(0.95);
            opacity: 0;
        }
        to {
            transform: scale(1);
            opacity: 1;
        }
    }
    
    /* Header Styling */
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
        animation: fadeIn 1s ease-out;
    }
    
    /* Card Styling */
    .metric-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        padding: 1.2rem;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2);
        transition: all 0.3s ease;
        animation: scaleIn 0.5s ease-out;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.25);
    }
    
    .summary-box {
        background: rgba(232, 244, 253, 0.8);
        backdrop-filter: blur(10px);
        padding: 1.2rem;
        border-radius: 10px;
        border: 1px solid rgba(31, 119, 180, 0.2);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
        transition: all 0.3s ease;
        animation: slideIn 0.5s ease-out;
    }
    
    /* Button Styling */
    .stButton > button {
        width: 100%;
        margin-top: 1rem;
        background: rgba(31, 119, 180, 0.8) !important;
        backdrop-filter: blur(5px) !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 16px 0 rgba(31, 38, 135, 0.2) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px 0 rgba(31, 38, 135, 0.25) !important;
    }
    
    /* Input Styling */
    .currency-input {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Streamlit Elements Override */
    .stSelectbox, .stNumberInput {
        animation: fadeIn 0.5s ease-out;
    }
    
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.7) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 8px !important;
    }
    
    /* AG Grid Styling */
    .ag-theme-streamlit {
        --ag-background-color: rgba(255, 255, 255, 0.8) !important;
        --ag-header-background-color: rgba(240, 242, 246, 0.9) !important;
        --ag-odd-row-background-color: rgba(249, 250, 251, 0.6) !important;
        --ag-row-hover-color: rgba(232, 244, 253, 0.8) !important;
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        transition: all 0.3s ease;
        background: rgba(31, 119, 180, 0.8) !important;
        color: rgba(255, 255, 255, 0.9) !important;
        padding: 8px 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        backdrop-filter: blur(5px) !important;
        box-shadow: 0 4px 16px 0 rgba(31, 38, 135, 0.2) !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px 0 rgba(31, 38, 135, 0.25) !important;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: rgba(255, 255, 255, 0.9) !important;
        color: rgba(31, 119, 180, 1) !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 16px 0 rgba(31, 38, 135, 0.15) !important;
    }
</style>
""", unsafe_allow_html=True)

# =============================
# Database Utility Functions
# =============================
def init_database() -> bool:
    """
    Initialize the SQLite database with required tables for items and settings.
    Returns True if successful, False otherwise.
    """
    try:
        conn = sqlite3.connect('price_calculator.db')
        cursor = conn.cursor()
        # Create items table with new columns for marketing_budget and delivery_charge_us
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                price_currency TEXT NOT NULL,
                additional_cost REAL NOT NULL DEFAULT 0.0,
                additional_cost_currency TEXT,
                shipping REAL NOT NULL,
                shipping_currency TEXT NOT NULL,
                delivery_charge_us REAL NOT NULL DEFAULT 15.0,
                marketing_budget REAL NOT NULL DEFAULT 0.0,
                import_cost REAL NOT NULL,
                import_currency TEXT NOT NULL,
                margin REAL NOT NULL,
                margin_type TEXT NOT NULL,
                final_currency TEXT NOT NULL,
                final_price REAL NOT NULL,
                final_price_usd REAL NOT NULL DEFAULT 0.0,
                final_inr_with_budget_and_margin REAL NOT NULL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Create settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                tax_rate REAL NOT NULL DEFAULT 8.25,
                usd_to_inr_rate REAL NOT NULL DEFAULT 83.25,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Initialize default settings if not exists
        cursor.execute('SELECT COUNT(*) FROM settings')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO settings (id, tax_rate, usd_to_inr_rate) VALUES (1, 8.25, 83.25)')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database initialization error: {e}")
        return False

def get_db_connection():
    """
    Get a connection to the SQLite database.
    Returns a connection object or None if connection fails.
    """
    try:
        return sqlite3.connect('price_calculator.db')
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def get_settings() -> Dict:
    """
    Retrieve the current settings (tax rate and exchange rate) from the database.
    Returns a dictionary with 'tax_rate' and 'usd_to_inr_rate'.
    """
    try:
        conn = get_db_connection()
        if conn is None:
            return {'tax_rate': 8.25, 'usd_to_inr_rate': 83.25}
        settings = pd.read_sql_query('SELECT * FROM settings WHERE id = 1', conn)
        conn.close()
        if settings.empty:
            return {'tax_rate': 8.25, 'usd_to_inr_rate': 83.25}
        return {
            'tax_rate': float(settings.iloc[0]['tax_rate']),
            'usd_to_inr_rate': float(settings.iloc[0]['usd_to_inr_rate'])
        }
    except Exception as e:
        st.error(f"Error getting settings: {e}")
        return {'tax_rate': 8.25, 'usd_to_inr_rate': 83.25}

def update_settings(tax_rate: float, usd_to_inr_rate: float) -> bool:
    """
    Update the tax rate and exchange rate in the database.
    Returns True if successful, False otherwise.
    """
    try:
        conn = get_db_connection()
        if conn is None:
            return False
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE settings 
            SET tax_rate = ?, usd_to_inr_rate = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = 1
        ''', (tax_rate, usd_to_inr_rate))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error updating settings: {e}")
        return False

def get_all_items() -> pd.DataFrame:
    """
    Retrieve all items from the database as a DataFrame.
    Returns an empty DataFrame if there are no items or on error.
    """
    try:
        conn = get_db_connection()
        if conn is None:
            return pd.DataFrame()
        items = pd.read_sql_query('SELECT * FROM items ORDER BY created_at DESC', conn)
        conn.close()
        return items
    except Exception as e:
        st.error(f"Error getting items: {e}")
        return pd.DataFrame()

def add_item(item_data: Dict) -> bool:
    """
    Add a new item to the database.
    Returns True if successful, False otherwise.
    """
    try:
        conn = get_db_connection()
        if conn is None:
            return False
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO items (
                id, name, price, price_currency, additional_cost, additional_cost_currency,
                shipping, shipping_currency, delivery_charge_us, marketing_budget,
                import_cost, import_currency, margin, margin_type, final_currency,
                final_price, final_price_usd, final_inr_with_budget_and_margin, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (
            item_data['id'], item_data['name'], item_data['price'], item_data['price_currency'],
            item_data['additional_cost'], item_data['additional_cost_currency'],
            item_data['shipping'], item_data['shipping_currency'], item_data['delivery_charge_us'], item_data['marketing_budget'],
            item_data['import_cost'], item_data['import_currency'], item_data['margin'], item_data['margin_type'],
            item_data['final_currency'], item_data['final_price'], item_data['final_price_usd'], item_data['final_inr_with_budget_and_margin']
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error adding item: {e}")
        return False

def delete_item(item_id: str) -> bool:
    """
    Delete an item from the database by its ID.
    Returns True if successful, False otherwise.
    """
    try:
        conn = get_db_connection()
        if conn is None:
            return False
        cursor = conn.cursor()
        cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error deleting item: {e}")
        return False

def clear_all_items() -> bool:
    """
    Remove all items from the database.
    Returns True if successful, False otherwise.
    """
    try:
        conn = get_db_connection()
        if conn is None:
            return False
        cursor = conn.cursor()
        cursor.execute('DELETE FROM items')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error clearing items: {e}")
        return False

# =============================
# Currency and Price Calculation
# =============================
def convert_currency(amount: float, from_currency: str, to_currency: str, exchange_rate: float) -> float:
    """
    Convert currency between USD and INR using the provided exchange rate.
    """
    if from_currency == to_currency:
        return amount
    elif from_currency == 'USD' and to_currency == 'INR':
        return amount * exchange_rate
    elif from_currency == 'INR' and to_currency == 'USD':
        return amount / exchange_rate
    else:
        return amount

def calculate_final_price(item_data: Dict, settings: Dict) -> float:
    """
    Calculate the final price for an item, including margin and currency conversion.
    """
    final_currency = item_data['final_currency']
    exchange_rate = settings['usd_to_inr_rate']
    # Convert all costs to final currency
    price_in_final = convert_currency(
        item_data['price'], item_data['price_currency'], final_currency, exchange_rate
    )
    shipping_in_final = convert_currency(
        item_data['shipping'], item_data['shipping_currency'], final_currency, exchange_rate
    )
    import_in_final = convert_currency(
        item_data['import_cost'], item_data['import_currency'], final_currency, exchange_rate
    )
    # Calculate base cost
    base_cost = price_in_final + shipping_in_final + import_in_final
    # Apply margin
    if item_data['margin_type'] == '%':
        final_price = base_cost * (1 + item_data['margin'] / 100)
    else:
        # Margin is in currency
        margin_in_final = convert_currency(
            item_data['margin'], item_data['margin_type'], final_currency, exchange_rate
        )
        final_price = base_cost + margin_in_final
    return round(final_price, 2)

# =============================
# Main Streamlit App
# =============================
def main():
    """
    Main function to run the Streamlit Price Calculator app.
    Handles sidebar settings, tab navigation, and initializes the database.
    """
    # Initialize database on first run
    if 'db_initialized' not in st.session_state:
        st.session_state.db_initialized = init_database()
    st.markdown('<h1 class="main-header slide-in">🧮 Price Calculator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="fade-in" style="text-align: center; color: #666; animation-delay: 0.3s;">Calculate prices with tax, shipping, and import costs</p>', unsafe_allow_html=True)
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        # Get current settings
        settings = get_settings()
        # Exchange rate
        usd_to_inr_rate = st.number_input(
            "USD to INR Exchange Rate",
            min_value=0.01,
            max_value=200.0,
            value=float(settings['usd_to_inr_rate']),
            step=0.01,
            format="%.2f"
        )
        # Tax rate
        tax_rate = st.number_input(
            "Tax Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(settings['tax_rate']),
            step=0.01,
            format="%.2f"
        )
        # Update settings if changed
        if (usd_to_inr_rate != settings['usd_to_inr_rate'] or 
            tax_rate != settings['tax_rate']):
            if update_settings(tax_rate, usd_to_inr_rate):
                st.success("Settings updated!")
                st.rerun()
        st.divider()
        # Clear all items button
        if st.button("🗑️ Clear All Items", type="secondary"):
            if clear_all_items():
                st.success("All items cleared!")
                st.rerun()
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📝 Item Calculation", "📊 Database", "📈 Analytics"])
    with tab1:
        calculator_tab()
    with tab2:
        database_tab()
    with tab3:
        analytics_tab()

# =============================
# Item Calculation Tab
# =============================
def calculator_tab():
    """
    Item Calculation tab: Add new items, view item list, and see summary.
    Organized into three vertical sections for clarity.
    """
    # --- Add New Item Section ---
    st.subheader("➕ Add New Item")
    # --- Real-time input fields ---
    item_name = st.text_input("Item Name", placeholder="Enter item name")
    price_col1, price_col2 = st.columns([3, 1])
    with price_col1:
        purchase_price = st.number_input("Purchase Price", min_value=0.0, step=0.01, format="%.2f", value=None, placeholder="Enter purchase price")
    with price_col2:
        purchase_currency = st.selectbox("Currency", ["INR", "USD"], key="purchase_currency", index=0)

    add_cost_col1, add_cost_col2 = st.columns([3, 1])
    with add_cost_col1:
        additional_cost = st.selectbox(
            "Additional Cost",
            options=[150, 50, 100, 200, 250],
            index=0,
            format_func=lambda x: f"₹{x}" if x else str(x)
        )
    with add_cost_col2:
        additional_cost_currency = st.selectbox("Currency", ["INR", "USD"], key="additional_cost_currency", index=0)

    ship_us_col1, ship_us_col2 = st.columns([3, 1])
    with ship_us_col1:
        shipping_cost = st.selectbox(
            "Shipping Cost to US",
            options=[1000, 500, 750, 1250, 1500],
            index=0,
            format_func=lambda x: f"₹{x}" if x else str(x)
        )
    with ship_us_col2:
        shipping_currency = st.selectbox("Currency", ["INR", "USD"], key="shipping_us_currency", index=0)

    # --- Delivery Charge in US (display after shipping) ---
    delivery_us_col1, delivery_us_col2 = st.columns([3, 1])
    with delivery_us_col1:
        delivery_charge_us = st.selectbox(
            "Delivery Charge in US",
            options=[5, 10, 15, 20, 25],
            index=2,
            format_func=lambda x: f"${x}" if x else str(x)
        )
    with delivery_us_col2:
        st.markdown("<span style='color: #1f77b4; font-weight: 600;'>USD</span>", unsafe_allow_html=True)
    settings = get_settings()
    total_inr = 0.0
    if purchase_currency == "INR" and purchase_price is not None:
        total_inr += purchase_price
    if additional_cost_currency == "INR" and additional_cost is not None:
        total_inr += additional_cost
    if shipping_currency == "INR" and shipping_cost is not None:
        total_inr += shipping_cost
    # Add Delivery Charge in US converted to INR
    if delivery_charge_us is not None:
        total_inr += delivery_charge_us * settings['usd_to_inr_rate']
    usd_equiv = total_inr / settings['usd_to_inr_rate'] if settings['usd_to_inr_rate'] else 0.0

    # Marketing Budget: 10% of Total Price in INR
    marketing_budget = total_inr * 0.10

    # Margin logic
    if total_inr <= 5000:
        margin_percent = 50
    elif total_inr > 5000 and total_inr <= 10000:
        margin_percent = 40
    elif total_inr > 10000:
        margin_percent = 30
    else:
        margin_percent = 0
    margin_value = total_inr * margin_percent / 100

    # Final Price in INR including Marketing Budget and Margin
    final_inr_with_budget_and_margin = total_inr + marketing_budget + margin_value
    final_price_usd = final_inr_with_budget_and_margin / settings['usd_to_inr_rate'] if settings['usd_to_inr_rate'] else 0.0

    st.info(f"Total Price in INR: ₹{total_inr:.2f}")
    st.info(f"Marketing Budget (10%): ₹{marketing_budget:.2f}")
    st.info(f"Margin: {margin_percent}% (₹{margin_value:.2f})")
    st.success(f"Final Price in USD: ${final_price_usd:.2f} (₹{final_inr_with_budget_and_margin:.2f})")

    # --- Form for submission only ---
    with st.form("item_form"):
        submitted = st.form_submit_button("Add Item", type="primary")
        if submitted:
            if not item_name or purchase_price is None or purchase_price <= 0:
                st.error("Please enter a valid item name and purchase price!")
            else:
                item_data = {
                    'id': str(uuid.uuid4()),
                    'name': item_name,
                    'price': purchase_price,
                    'price_currency': purchase_currency,
                    'additional_cost': additional_cost,
                    'additional_cost_currency': additional_cost_currency,
                    'shipping': shipping_cost,
                    'shipping_currency': shipping_currency,
                    'delivery_charge_us': delivery_charge_us,
                    'marketing_budget': marketing_budget,
                    'import_cost': 0.0,
                    'import_currency': 'INR',
                    'margin': margin_value,
                    'margin_type': f"{margin_percent}%",
                    'final_currency': 'INR',
                    'final_price': total_inr,
                    'final_price_usd': final_price_usd,
                    'final_inr_with_budget_and_margin': final_inr_with_budget_and_margin
                }
                if add_item(item_data):
                    st.success(f"Item '{item_name}' added successfully!")
                    st.rerun()

    st.divider()
    # --- Items List Section ---
    st.subheader("📋 Items List")
    items_df = get_all_items()
    if items_df.empty:
        st.info("No items added yet. Add your first item to get started!")
    else:
        # Prepare display DataFrame with expanded columns
        display_df = items_df[[
            'name',
            'price', 'price_currency',
            'additional_cost', 'additional_cost_currency',
            'shipping', 'shipping_currency',
            'delivery_charge_us',
            'marketing_budget',
            'margin',
            'final_inr_with_budget_and_margin',
            'final_price_usd',
            'final_price',
            'created_at']].copy()
        display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        # Configure AG Grid
        gb = GridOptionsBuilder.from_dataframe(display_df)
        gb.configure_selection(selection_mode='multiple', use_checkbox=True)
        
        # Configure columns with proper formatting and headers
        gb.configure_column("name", header_name="Name", width=150)
        gb.configure_column("price", header_name="Purchase Price", type=["numericColumn"], precision=2, width=100)
        gb.configure_column("price_currency", header_name="Currency", width=90)
        gb.configure_column("additional_cost", header_name="Additional Cost", type=["numericColumn"], precision=2, width=120)
        gb.configure_column("additional_cost_currency", header_name="Add. Curr.", width=90)
        gb.configure_column("shipping", header_name="Shipping Cost to US", type=["numericColumn"], precision=2, width=150)
        gb.configure_column("shipping_currency", header_name="Ship Curr.", width=90)
        gb.configure_column("delivery_charge_us", header_name="Delivery Charge in US ($)", type=["numericColumn"], precision=2, width=120)
        gb.configure_column("marketing_budget", header_name="Marketing Budget (₹)", type=["numericColumn"], precision=2, width=120)
        gb.configure_column("margin", header_name="Margin (₹)", type=["numericColumn"], precision=2, width=120)
        gb.configure_column("final_inr_with_budget_and_margin", header_name="Final INR (with Budget & Margin)", type=["numericColumn"], precision=2, width=150)
        gb.configure_column("final_price_usd", header_name="Final Price in USD", type=["numericColumn"], precision=2, width=150)
        gb.configure_column("final_price", header_name="Total Price in INR", type=["numericColumn"], precision=2, width=130)
        gb.configure_column("created_at", header_name="Created At", width=130)
        
        # Configure grid properties
        gb.configure_grid_options(
            domLayout='normal',
            headerHeight=45,
            rowHeight=35,
            enableRangeSelection=True,
            pagination=True,
            paginationAutoPageSize=True,
            animateRows=True,
            rowClass='fade-in',
            suppressMovableColumns=False,
            enableCellTextSelection=True,
            overlayLoadingTemplate='<span class="scale-in">Loading...</span>',
            overlayNoRowsTemplate='<span class="fade-in">No records found</span>'
        )
        
        grid_options = gb.build()
        grid_response = AgGrid(
            display_df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=False,  # Don't auto-fit columns
            theme='streamlit',
            height=400,  # Fixed height to ensure scrolling
            allow_unsafe_jscode=True  # Enable advanced features
        )

        # Get selected rows
        selected_rows = grid_response['selected_rows']
        selected_ids = [items_df.iloc[display_df.index.get_loc(row['_selectedRowNodeInfo']['nodeRowIndex'])]['id'] 
                       for row in selected_rows] if selected_rows else []
            
        if selected_ids:
            if st.button("Delete Selected", type="primary"):
                for item_id in selected_ids:
                    delete_item(str(item_id))
                st.success(f"Deleted {len(selected_ids)} selected item(s)!")
                st.rerun()

    st.divider()
    # --- Summary Section ---
    st.subheader("💰 Summary")
    settings = get_settings()
    subtotal = items_df['final_price'].sum() if not items_df.empty else 0.0
    tax_amount = subtotal * (settings['tax_rate'] / 100)
    total = subtotal + tax_amount
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    with summary_col1:
        st.metric("Subtotal", f"${subtotal:.2f}")
    with summary_col2:
        st.metric(f"Tax ({settings['tax_rate']}%)", f"${tax_amount:.2f}")
    with summary_col3:
        st.metric("Total", f"${total:.2f}", delta=f"+${tax_amount:.2f}")

# =============================
# Database Tab
# =============================
def database_tab():
    """
    Database tab: View all items in a table and export data as CSV.
    """
    st.subheader("📊 Database Records")
    items_df = get_all_items()
    if not items_df.empty:
        st.subheader("Items")
        display_df = items_df[[
            'name',
            'price', 'price_currency',
            'additional_cost', 'additional_cost_currency',
            'shipping', 'shipping_currency',
            'delivery_charge_us',
            'marketing_budget',
            'margin',
            'final_inr_with_budget_and_margin',
            'final_price_usd',
            'final_price',
            'created_at']].copy()
        display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(display_df, use_container_width=True)
        # Export functionality
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="price_calculator_items.csv",
            mime="text/csv"
        )
    else:
        st.info("No items in database")

# =============================
# Analytics Tab
# =============================
def analytics_tab():
    """
    Analytics tab: View summary metrics and charts for all items.
    """
    st.subheader("📈 Analytics Dashboard")
    items_df = get_all_items()
    if items_df.empty:
        st.info("No data available for analytics. Add some items first!")
        return
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Items", len(items_df))
    with col2:
        total_value = items_df['final_price'].sum()
        st.metric("Total Value", f"${total_value:.2f}")
    with col3:
        avg_price = items_df['final_price'].mean()
        st.metric("Average Price", f"${avg_price:.2f}")
    with col4:
        avg_margin = items_df['margin'].mean()
        st.metric("Average Margin", f"{avg_margin:.2f}")
    # Charts
    col1, col2 = st.columns(2)
    with col1:
        # Currency distribution
        currency_counts = items_df['final_currency'].value_counts()
        fig_currency = px.pie(
            values=currency_counts.values,
            names=currency_counts.index,
            title="Final Price Currency Distribution"
        )
        st.plotly_chart(fig_currency, use_container_width=True)
        # Price range distribution
        fig_price_range = px.histogram(
            items_df,
            x='final_price',
            nbins=10,
            title="Price Range Distribution"
        )
        st.plotly_chart(fig_price_range, use_container_width=True)
    with col2:
        # Margin type distribution
        margin_counts = items_df['margin_type'].value_counts()
        fig_margin = px.bar(
            x=margin_counts.index,
            y=margin_counts.values,
            title="Margin Type Distribution"
        )
        st.plotly_chart(fig_margin, use_container_width=True)
        # Recent items timeline
        items_df['created_at'] = pd.to_datetime(items_df['created_at'])
        recent_items = items_df.head(10).sort_values('created_at')
        fig_timeline = px.line(
            recent_items,
            x='created_at',
            y='final_price',
            title="Recent Items Timeline"
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
    # Detailed statistics
    st.subheader("📊 Detailed Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Price Statistics**")
        price_stats = items_df['final_price'].describe()
        st.dataframe(price_stats.to_frame(), use_container_width=True)
    with col2:
        st.write("**Margin Statistics**")
        margin_stats = items_df['margin'].describe()
        st.dataframe(margin_stats.to_frame(), use_container_width=True)

# =============================
# App Entry Point
# =============================
if __name__ == "__main__":
    main()