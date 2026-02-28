# =============================
# Imports
# =============================
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import uuid
from typing import Dict, List, Optional, Tuple, Any
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# Internal Imports
from src.database import (
    init_database, get_settings, update_settings, get_all_items, 
    add_item, update_item_field, delete_item, clear_all_items
)
from src.utils import (
    fetch_real_time_exchange_rate, convert_currency, calculate_final_price,
    generate_excel_export, generate_pdf_export
)

# =============================
# Streamlit Page Configuration
# =============================
st.set_page_config(
    page_title="Price Calculator",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="auto"
)

# =============================
# Load Custom CSS
# =============================
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

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
        st.markdown("""
        <div style="background:rgba(232,244,253,0.7);border-radius:10px;padding:1rem 1.2rem 1rem 1.2rem;margin-bottom:1rem;border:1px solid #1f77b4;box-shadow:0 2px 8px rgba(31,119,180,0.08);">
            <h4 style="color:#1f77b4;margin-bottom:0.7rem;display:flex;align-items:center;"><span style='font-size:1.3em;margin-right:0.5em;'>📋</span> <span>Price Calculation Rules</span></h4>
            <ul style="padding-left:1.2em;margin-bottom:0.7em;">
                <li style="margin-bottom:0.5em;"><span style='color:#2ca02c;font-weight:600;'>💸 Marketing Budget:</span> <span style='color:#333;'>Select <b>5%, 10%, 15%, or 20%</b> (default 10%); applied to (Price + Additional + Shipping + Margin) <b>before</b> adding Delivery Charge.</span></li>
                <li style="margin-bottom:0.5em;"><span style='color:#ff7f0e;font-weight:600;'>🚚 Delivery Charge in US:</span> <span style='color:#333;'>Select from <b>$5, $10, $15, $20, $25</b> (default <b>$15</b>)</span></li>
                <li style="margin-bottom:0.5em;"><span style='color:#d62728;font-weight:600;'>📈 Margin:</span> <span style='color:#333;'>On <b>Item Price + Additional Cost</b> (INR) only; editable in form.</span>
                    <ul style='margin:0.3em 0 0.3em 1.2em;'>
                        <li>50% if <b>≤ 5000</b></li>
                        <li>40% if <b>5000–10000</b></li>
                        <li>30% if <b>&gt; 10000</b></li>
                    </ul>
                </li>
                <li style="margin-bottom:0.5em;"><span style='color:#9467bd;font-weight:600;'>💵 Final Price in USD:</span> <span style='color:#333;'>Includes all costs, margin, and marketing budget</span></li>
                <li style="margin-bottom:0.5em;"><span style='color:#1f77b4;font-weight:600;'>💱 Currency Conversion:</span> <span style='color:#333;'>Default rate <b>85</b>; use Fetch for latest or Reset to 85.</span></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        # Get current settings
        settings = get_settings()
        # Exchange rate
        rate_col1, rate_col2 = st.columns([2, 1])
        with rate_col1:
            usd_to_inr_rate = st.number_input(
                "USD to INR Rate",
                min_value=0.01,
                max_value=200.0,
                value=float(settings['usd_to_inr_rate']),
                step=0.01,
                format="%.2f"
            )
        with rate_col2:
            st.write("") # Spacer
            st.write("") # Spacer
            fetch_btn = st.button("🔄 Fetch", help="Fetch latest rate from API")
            reset_btn = st.button("↩️ Reset", help="Reset rate to 85")
            if fetch_btn:
                new_rate = fetch_real_time_exchange_rate()
                if new_rate:
                    if update_settings(settings['tax_rate'], new_rate):
                        st.success(f"Fetched: {new_rate}")
                        st.rerun()
                else:
                    st.error("API failed")
            if reset_btn:
                if update_settings(settings['tax_rate'], 85.0):
                    st.success("Rate reset to 85")
                    st.rerun()

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
        if (abs(usd_to_inr_rate - settings['usd_to_inr_rate']) > 0.001 or 
            abs(tax_rate - settings['tax_rate']) > 0.001):
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
    tab1, tab2, tab3 = st.tabs(["📝 Item Calculation", "📈 Analytics", "📊 Database"])
    with tab1:
        calculator_tab()
    with tab2:
        analytics_tab()
    with tab3:
        database_tab()

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
    name_col1, name_col2 = st.columns([2, 1])
    with name_col1:
        item_name = st.text_input("Item Name", placeholder="Enter item name")
    with name_col2:
        category = st.selectbox(
            "Category",
            ["Apparel", "Other"],
            index=0
        )
    
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

    # --- Margin: calculated on Item Price + Additional Cost (INR) only; editable ---
    settings = get_settings()
    rate = settings['usd_to_inr_rate']
    base_for_margin_inr = 0.0
    if purchase_price is not None and purchase_price >= 0:
        price_inr = purchase_price if purchase_currency == "INR" else purchase_price * rate
        add_inr = (additional_cost or 0) if additional_cost_currency == "INR" else (additional_cost or 0) * rate
        base_for_margin_inr = price_inr + add_inr
    if base_for_margin_inr <= 5000:
        default_margin_pct = 50
    elif base_for_margin_inr <= 10000:
        default_margin_pct = 40
    else:
        default_margin_pct = 30
    default_margin_inr = base_for_margin_inr * default_margin_pct / 100 if base_for_margin_inr else 0.0
    default_margin_usd = default_margin_inr / rate if rate else 0.0

    margin_col1, margin_col2 = st.columns([3, 1])
    # Render currency dropdown first (col2) so margin_currency is available for the number input
    with margin_col2:
        margin_currency = st.selectbox(
            "Currency",
            ["INR", "USD"],
            index=0,
            key="margin_currency"
        )
    with margin_col1:
        margin_label = "Margin (₹)" if margin_currency == "INR" else "Margin ($)"
        margin_default = default_margin_inr if margin_currency == "INR" else default_margin_usd
        margin_step = 10.0 if margin_currency == "INR" else 1.0
        margin_value = st.number_input(
            margin_label,
            min_value=0.0,
            value=margin_default,
            step=margin_step,
            format="%.2f",
            key="margin_input",
            help="Calculated from Item Price + Additional Cost. Editable."
        )

    # Single margin in INR for all calculations and DB storage
    margin_inr = margin_value if margin_currency == "INR" else (margin_value * rate if rate else 0.0)

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

    # --- Marketing Budget % (after Shipping, before Delivery) ---
    marketing_budget_pct = st.selectbox(
        "Marketing Budget (%)",
        options=[5, 10, 15, 20],
        index=1,
        format_func=lambda x: f"{x}%",
        help="Applied to (Price + Additional + Shipping + Margin); then Delivery Charge is added."
    )

    # --- Delivery Charge in US ---
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

    show_calculations = item_name and purchase_price is not None and purchase_price > 0
    if show_calculations:
        # Costs before delivery (INR): price + additional + shipping; then + margin
        costs_before_delivery = 0.0
        if purchase_currency == "INR" and purchase_price is not None:
            costs_before_delivery += purchase_price
        elif purchase_price is not None:
            costs_before_delivery += purchase_price * rate
        if additional_cost_currency == "INR" and additional_cost is not None:
            costs_before_delivery += additional_cost
        elif additional_cost is not None:
            costs_before_delivery += additional_cost * rate
        if shipping_currency == "INR" and shipping_cost is not None:
            costs_before_delivery += shipping_cost
        elif shipping_cost is not None:
            costs_before_delivery += shipping_cost * rate

        base_with_margin = costs_before_delivery + margin_inr
        marketing_budget = base_with_margin * (marketing_budget_pct / 100)
        delivery_inr = (delivery_charge_us or 0) * rate
        final_inr_with_budget_and_margin = base_with_margin + marketing_budget + delivery_inr
        final_price_usd = final_inr_with_budget_and_margin / rate if rate else 0.0

        margin_pct_display = round(margin_inr / base_for_margin_inr * 100) if base_for_margin_inr else 0
        margin_usd_preview = margin_inr / rate if rate else 0.0
        st.info(f"Costs before delivery (INR): ₹{costs_before_delivery:.2f}")
        st.info(f"Margin: ₹{margin_inr:.2f} INR | ${margin_usd_preview:.2f} USD" + (f" (~{margin_pct_display}% of price+additional)" if base_for_margin_inr else ""))
        st.info(f"Marketing Budget ({marketing_budget_pct}%): ₹{marketing_budget:.2f}")
        st.info(f"Delivery (INR): ₹{delivery_inr:.2f}")
        st.success(f"Final Price in USD: ${final_price_usd:.2f} (₹{final_inr_with_budget_and_margin:.2f})")

    # --- Form for submission only ---
    with st.form("item_form"):
        submitted = st.form_submit_button("Add Item", type="primary")
        if submitted:
            if not item_name or purchase_price is None or purchase_price <= 0:
                st.error("Please enter a valid item name and purchase price!")
            else:
                # Recompute for submission: marketing before delivery
                rate_s = get_settings()['usd_to_inr_rate']
                costs_before_delivery_s = 0.0
                if purchase_currency == "INR":
                    costs_before_delivery_s += purchase_price
                else:
                    costs_before_delivery_s += purchase_price * rate_s
                if additional_cost_currency == "INR":
                    costs_before_delivery_s += (additional_cost or 0)
                else:
                    costs_before_delivery_s += (additional_cost or 0) * rate_s
                if shipping_currency == "INR":
                    costs_before_delivery_s += (shipping_cost or 0)
                else:
                    costs_before_delivery_s += (shipping_cost or 0) * rate_s

                base_with_margin_s = costs_before_delivery_s + margin_inr
                marketing_budget_s = base_with_margin_s * (marketing_budget_pct / 100)
                delivery_inr_s = (delivery_charge_us or 0) * rate_s
                final_inr_s = base_with_margin_s + marketing_budget_s + delivery_inr_s
                final_price_usd_s = final_inr_s / rate_s if rate_s else 0.0
                margin_pct_s = round(margin_inr / base_for_margin_inr * 100) if base_for_margin_inr else 0
                # Total costs (INR) for display: all cost components including delivery
                total_inr_s = costs_before_delivery_s + delivery_inr_s

                item_data = {
                    'id': str(uuid.uuid4()),
                    'name': item_name,
                    'category': category,
                    'price': purchase_price,
                    'price_currency': purchase_currency,
                    'additional_cost': additional_cost,
                    'additional_cost_currency': additional_cost_currency,
                    'shipping': shipping_cost,
                    'shipping_currency': shipping_currency,
                    'delivery_charge_us': delivery_charge_us,
                    'marketing_budget': marketing_budget_s,
                    'import_cost': 0.0,
                    'import_currency': 'INR',
                    'margin': margin_inr,
                    'margin_type': f"{margin_pct_s}%" if base_for_margin_inr else "INR",
                    'final_currency': 'INR',
                    'final_price': total_inr_s,
                    'final_price_usd': final_price_usd_s,
                    'final_inr_with_budget_and_margin': final_inr_s
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
        st.info("💡 **Tip:** Select one or more rows using the checkboxes to delete records.")
        # Prepare display DataFrame with expanded columns
        display_df = items_df[[
            'id',
            'name',
            'category',
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
        rate_grid = get_settings()['usd_to_inr_rate']
        display_df['margin_usd'] = (display_df['margin'] / rate_grid).round(2) if rate_grid else 0.0
        display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        # Configure AG Grid
        gb = GridOptionsBuilder.from_dataframe(display_df)
        gb.configure_selection(selection_mode='multiple', use_checkbox=True)
        
        # Configure columns with proper formatting and headers
        gb.configure_column("id", hide=True)
        gb.configure_column("name", header_name="Name", width=150, editable=True, checkboxSelection=True)
        gb.configure_column("category", header_name="Category", width=120, editable=True, 
                            cellEditor='agSelectCellEditor', 
                            cellEditorParams={'values': ["Apparel", "Other"]})
        gb.configure_column("price", header_name="Purchase Price", type=["numericColumn"], precision=2, width=100, editable=True)
        gb.configure_column("price_currency", header_name="Currency", width=90, editable=True,
                            cellEditor='agSelectCellEditor', cellEditorParams={'values': ["INR", "USD"]})
        gb.configure_column("additional_cost", header_name="Additional Cost", type=["numericColumn"], precision=2, width=120)
        gb.configure_column("additional_cost_currency", header_name="Add. Curr.", width=90)
        gb.configure_column("shipping", header_name="Shipping Cost to US", type=["numericColumn"], precision=2, width=150)
        gb.configure_column("shipping_currency", header_name="Ship Curr.", width=90)
        gb.configure_column("delivery_charge_us", header_name="Delivery Charge in US ($)", type=["numericColumn"], precision=2, width=120)
        gb.configure_column("marketing_budget", header_name="Marketing Budget (₹)", type=["numericColumn"], precision=2, width=120)
        gb.configure_column("margin", header_name="Margin (₹) INR", type=["numericColumn"], precision=2, width=110)
        gb.configure_column("margin_usd", header_name="Margin ($) USD", type=["numericColumn"], precision=2, width=110)
        gb.configure_column("final_inr_with_budget_and_margin", header_name="Final INR (with Budget & Margin)", type=["numericColumn"], precision=2, width=150)
        gb.configure_column("final_price_usd", header_name="Final Price in USD", type=["numericColumn"], precision=2, width=150)
        gb.configure_column("final_price", header_name="Total Costs (INR)", type=["numericColumn"], precision=2, width=130)
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
            update_mode=GridUpdateMode.MODEL_CHANGED | GridUpdateMode.SELECTION_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=False,
            theme='streamlit',
            height=400,
            allow_unsafe_jscode=True
        )

        # Handle in-grid updates
        updated_df = grid_response['data']
        if not items_df.empty and not updated_df.equals(display_df):
            # Find differences and update DB
            for index, row in updated_df.iterrows():
                # Check for changes in the current row compared to original display_df
                # This is a bit simplified, ideally we'd tracking specific cell changes
                original_row = display_df[display_df['id'] == row['id']]
                if not original_row.empty:
                    for col in ['name', 'category', 'price', 'price_currency']:
                        if row[col] != original_row.iloc[0][col]:
                            update_item_field(row['id'], col, row[col])
                            st.success(f"Updated {col} for {row['name']}")
                            st.rerun()

        # Get selected rows
        selected_rows = grid_response['selected_rows']
        selected_ids = []
        # Ensure selected_rows is a list of dicts
        if isinstance(selected_rows, pd.DataFrame):
            selected_rows = selected_rows.to_dict(orient='records')
        if isinstance(selected_rows, list) and selected_rows:
            for row in selected_rows:
                # Match by 'name' and 'created_at' (formatted)
                match = items_df[
                    (items_df['name'] == row['name']) &
                    (pd.to_datetime(items_df['created_at']).dt.strftime('%Y-%m-%d %H:%M') == row['created_at'])
                ]
                if not match.empty:
                    selected_ids.append(match.iloc[0]['id'])
        if selected_ids:
            if st.button("Delete Selected", type="primary"):
                for item_id in selected_ids:
                    delete_item(str(item_id))
                st.success(f"Deleted {len(selected_ids)} selected item(s)!")
                st.rerun()

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
        # Date filter
        items_df['created_at_dt'] = pd.to_datetime(items_df['created_at'])
        min_date = items_df['created_at_dt'].min().date()
        max_date = items_df['created_at_dt'].max().date()
        
        col_date1, col_date2 = st.columns([2, 3])
        with col_date1:
            date_range = st.date_input(
                "Filter by Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="db_date_filter"
            )
            
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            items_df = items_df[
                (items_df['created_at_dt'].dt.date >= start_date) & 
                (items_df['created_at_dt'].dt.date <= end_date)
            ]

        if items_df.empty:
            st.warning("No records found for the selected date range.")
            return

        st.subheader("Items")
        display_df = items_df[[
            'name',
            'category',
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
        rate_db = get_settings()['usd_to_inr_rate']
        display_df['margin_usd'] = (display_df['margin'] / rate_db).round(2) if rate_db else 0.0
        # Show margin_usd next to margin
        cols = [c for c in display_df.columns if c != 'margin_usd']
        cols.insert(cols.index('margin') + 1, 'margin_usd')
        display_df = display_df[cols]
        display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(display_df, use_container_width=True)
        
        # Export functionality
        col1, col2, col3 = st.columns(3)
        with col1:
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 CSV",
                data=csv,
                file_name="price_calculator_items.csv",
                mime="text/csv"
            )
        with col2:
            excel_data = generate_excel_export(display_df)
            st.download_button(
                label="📥 Excel",
                data=excel_data,
                file_name="price_calculator_items.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col3:
            pdf_data = generate_pdf_export(display_df)
            st.download_button(
                label="📥 PDF",
                data=pdf_data,
                file_name="price_calculator_items.pdf",
                mime="application/pdf"
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
        
    # Date filter
    items_df['created_at_dt'] = pd.to_datetime(items_df['created_at'])
    min_date = items_df['created_at_dt'].min().date()
    max_date = items_df['created_at_dt'].max().date()
    
    col_date1, col_date2 = st.columns([2, 3])
    with col_date1:
        date_range = st.date_input(
            "Filter by Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="analytics_date_filter"
        )
        
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        items_df = items_df[
            (items_df['created_at_dt'].dt.date >= start_date) & 
            (items_df['created_at_dt'].dt.date <= end_date)
        ]

    if items_df.empty:
        st.warning("No records found for the selected date range.")
        return
        
    # Summary metrics (use final selling price for value/revenue)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Items", len(items_df))
    with col2:
        total_value = items_df['final_inr_with_budget_and_margin'].sum()
        st.metric("Total Value (₹)", f"₹{total_value:.2f}")
    with col3:
        avg_price = items_df['final_inr_with_budget_and_margin'].mean()
        st.metric("Avg Price (₹)", f"₹{avg_price:.2f}")
    with col4:
        total_revenue = items_df['final_inr_with_budget_and_margin'].sum()
        total_margin = items_df['margin'].sum()
        avg_margin_pct = (total_margin / total_revenue * 100) if total_revenue > 0 else 0.0
        st.metric("Avg Margin %", f"{avg_margin_pct:.1f}%")

    # Charts Row 1
    col1, col2 = st.columns(2)
    with col1:
        # Category distribution
        cat_counts = items_df['category'].value_counts()
        fig_cat = px.pie(
            values=cat_counts.values,
            names=cat_counts.index,
            title="Distribution by Category",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_cat, use_container_width=True)
    
    with col2:
        # Price by category bar chart (final selling price)
        cat_price = items_df.groupby('category')['final_inr_with_budget_and_margin'].sum().reset_index()
        fig_price = px.bar(
            cat_price,
            x='category',
            y='final_inr_with_budget_and_margin',
            title="Total Price by Category",
            labels={'final_inr_with_budget_and_margin': 'Total Price (₹)', 'category': 'Category'},
            color='category',
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        st.plotly_chart(fig_price, use_container_width=True)

    # Charts Row 2
    col3, col4 = st.columns(2)
    with col3:
        # Price Range Histogram (final selling price)
        fig_hist = px.histogram(
            items_df,
            x='final_inr_with_budget_and_margin',
            nbins=10,
            title="Price Range Distribution",
            labels={'final_inr_with_budget_and_margin': 'Final Price (₹)'},
            color_discrete_sequence=['#1f77b4']
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col4:
        # Timeline Chart (final selling price)
        items_df['created_at'] = pd.to_datetime(items_df['created_at'])
        timeline_df = items_df.sort_values('created_at')
        fig_timeline = px.line(
            timeline_df,
            x='created_at',
            y='final_inr_with_budget_and_margin',
            title="Price Trend (Over Time)",
            markers=True,
            labels={'final_inr_with_budget_and_margin': 'Price (₹)', 'created_at': 'Date'}
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

    # Detailed statistics (final selling price and margin)
    with st.expander("📊 View Detailed Statistics", expanded=False):
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            st.write("**Final Price Statistics (₹)**")
            price_stats = items_df['final_inr_with_budget_and_margin'].describe()
            st.dataframe(price_stats.to_frame(), use_container_width=True)
        with s_col2:
            st.write("**Margin Statistics (₹)**")
            margin_stats = items_df['margin'].describe()
            st.dataframe(margin_stats.to_frame(), use_container_width=True)

# =============================
# App Entry Point
# =============================
if __name__ == "__main__":
    main()