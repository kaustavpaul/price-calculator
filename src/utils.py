import streamlit as st
import requests
import pandas as pd
import io
from fpdf import FPDF
from typing import Dict, List, Optional, Tuple, Any

@st.cache_data(ttl=3600)
def fetch_real_time_exchange_rate() -> Optional[float]:
    """Fetch exchange rate from API."""
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        if response.status_code == 200:
            return float(response.json()["rates"]["INR"])
    except:
        pass
    return None

def convert_currency(amount: float, from_curr: str, to_curr: str, rate: float) -> float:
    """Currency conversion helper."""
    if from_curr == to_curr: return amount
    if from_curr == 'USD' and to_curr == 'INR': return amount * rate
    if from_curr == 'INR' and to_curr == 'USD': return amount / rate
    return amount

def calculate_final_price(data: Dict[str, Any], settings: Dict[str, float]) -> float:
    """Calculate final price based on business rules."""
    rate = settings['usd_to_inr_rate']
    final_curr = data['final_currency']
    
    price = convert_currency(data['price'], data['price_currency'], final_curr, rate)
    shipping = convert_currency(data['shipping'], data['shipping_currency'], final_curr, rate)
    import_cost = convert_currency(data['import_cost'], data['import_currency'], final_curr, rate)
    
    base = price + shipping + import_cost
    if data['margin_type'] == '%':
        final = base * (1 + data['margin'] / 100)
    else:
        margin = convert_currency(data['margin'], data['margin_type'], final_curr, rate)
        final = base + margin
    return round(final, 2)

def generate_excel_export(df: pd.DataFrame) -> bytes:
    """Excel generator."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Price_Calculator_Items')
    return output.getvalue()

def generate_pdf_export(df: pd.DataFrame) -> bytes:
    """PDF generator (Unicode-safe for common chars)."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=12)
        pdf.cell(190, 10, txt="Price Calculator Items Report", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("helvetica", size=10)
        for idx, row in df.iterrows():
            name = str(row['name']).encode('ascii', 'ignore').decode('ascii')
            cat = str(row['category']).encode('ascii', 'ignore').decode('ascii')
            txt = f"{name} ({cat}): INR {row['final_price']:.2f}"
            pdf.cell(190, 10, txt=txt, ln=True)
            if idx > 20:
                pdf.cell(190, 10, txt="... see full report in CSV/Excel", ln=True)
                break
        return bytes(pdf.output())
    except Exception as e:
        st.error(f"PDF Error: {e}")
        return b""
