# Price Calculator

## Features
- Modern UI with glassmorphism and animations
- Real-time price calculation with tax, shipping, import costs, margin, marketing budget, and currency conversion
- Interactive AG Grid table for item management
- Analytics dashboard with charts and statistics
- Export data as CSV

## Requirements

All required Python packages are listed in `requirements.txt`. Key packages:
- streamlit
- st-aggrid
- pandas
- plotly

## Deploying on Streamlit Community Cloud

1. Ensure your `requirements.txt` includes:
   - `st-aggrid`
   - `streamlit`
   - `pandas`
   - `plotly`
2. Push your code to GitHub.
3. Go to [streamlit.io/cloud](https://streamlit.io/cloud) and connect your repo.
4. The app will auto-deploy. If you see a missing package error, check `requirements.txt`.

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## License
See LICENSE file.
# Price Calculator - Streamlit Version

A modern, interactive price calculator built with Streamlit that helps calculate final prices including tax, shipping, import costs, and profit margins with multi-currency support.

![Price Calculator Demo](screenshots/demo.gif)

## Features

- **Multi-Currency Support**: USD and INR with real-time exchange rate conversion
- **Comprehensive Pricing**: Base price, shipping, import costs, and profit margins
- **Flexible Margins**: Percentage-based or fixed amount margins
- **Real-time Calculations**: Instant price updates as you modify inputs
- **Database Storage**: SQLite database for persistent data storage
- **Advanced Data Grid**: 
  - Sortable and filterable columns
  - Multi-select row operations
  - Pagination for large datasets
  - Customizable column widths
- **Analytics Dashboard**: Interactive charts and statistics
- **Modern UI**: Clean, responsive interface with Streamlit
  - Tab navigation now uses button-style tabs with clear active/inactive states
  - Glassmorphism and animation effects for a polished look

## Technical Requirements

- Python 3.9 or higher
- Modern web browser (Chrome, Firefox, Safari, or Edge)
- 512MB RAM minimum
- Internet connection for currency exchange rates (optional)

## Installation

1. **Clone or download the project files**

2. **Create and activate a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   
   Required packages:
   - streamlit
   - streamlit-aggrid
   - pandas
   - plotly
   - sqlite3 (included with Python)

4. **Run the application**:
   ```bash
   streamlit run app.py
   ```

5. **Open your browser** and navigate to the URL shown in the terminal (usually `http://localhost:8501`)

## Usage

### Calculator Tab
- **Add Items**: Fill in the form with item details
  - Item name and base price
  - Shipping costs (optional)
  - Import costs (optional)
  - Profit margin (percentage or fixed amount)
  - Final currency selection
- **Interactive Items List**:
  - Sort any column by clicking header
  - Filter items using the column filters
  - Select multiple items for bulk operations
  - Adjustable column widths
  - Paginated view for better performance
- **Bulk Operations**:
  - Select multiple items using checkboxes
  - Delete selected items in one click
  - Filter and select for batch operations
- **Summary**: View subtotal, tax, and total calculations with real-time updates

### Settings (Sidebar)
- **Exchange Rate**: Update USD to INR conversion rate
- **Tax Rate**: Set the tax percentage for calculations
- **Clear All**: Remove all items from the database

### Database Tab
- **View Records**: 
  - Comprehensive data grid with all stored items
  - Sort and filter capabilities
  - Responsive table with horizontal scrolling
  - Formatted number displays with proper precision
- **Export Data**: Download filtered or complete data as CSV file
- **Settings**: View and modify application settings

### Analytics Tab
**Summary Metrics**: Total items, value, average price, and margin
**Interactive Charts**:
  - Currency distribution pie chart
  - Price range histogram
  - Margin type distribution
  - Recent items timeline
**Statistics**: Detailed price and margin statistics

### Tab Navigation (UI Update)
- Tabs are now styled as individual buttons for improved clarity and usability
- The active tab features a lighter background and bold, dark font
- Inactive tabs have a darker background with lighter font
- Smooth transitions and glass effect applied for a modern look

## Database Schema

### Items Table
- `id`: Unique identifier
- `name`: Item name
- `price`: Base price
- `price_currency`: Currency of base price
- `shipping`: Shipping cost
- `shipping_currency`: Currency of shipping cost
- `import_cost`: Import cost
- `import_currency`: Currency of import cost
- `margin`: Profit margin amount
- `margin_type`: Margin type ('%', 'USD', or 'INR')
- `final_currency`: Currency for final price
- `final_price`: Calculated final price
- `created_at`: Timestamp of creation
- `updated_at`: Timestamp of last update

### Settings Table
- `tax_rate`: Current tax rate percentage
- `usd_to_inr_rate`: Current USD to INR exchange rate

## Key Features

### Currency Conversion
The app automatically converts between USD and INR using the configured exchange rate:
- USD to INR: `amount × exchange_rate`
- INR to USD: `amount ÷ exchange_rate`

### Price Calculation
Final price is calculated as:
1. Convert all costs (price, shipping, import) to final currency
2. Sum all costs to get base cost
3. Apply margin:
   - Percentage: `base_cost × (1 + margin/100)`
   - Fixed amount: `base_cost + margin_converted_to_final_currency`

### Tax Calculation
Tax is applied to the subtotal of all items:
- `tax_amount = subtotal × (tax_rate / 100)`
- `total = subtotal + tax_amount`

## Customization

### Adding New Currencies
To add support for additional currencies:
1. Modify the `convert_currency` function in `app.py`
2. Update currency selection dropdowns
3. Add exchange rate settings

### Styling
The app uses custom CSS for styling, including:
- Glassmorphism effects
- Animated transitions
- Button-style tab navigation (see `app.py` CSS section)
Modify the CSS section in the main function to further customize the appearance.

### Database
The app uses SQLite by default. To use a different database:
1. Modify the `get_db_connection` function
2. Update table creation SQL statements
3. Ensure proper connection handling

## Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   streamlit run app.py --server.port 8502
   ```

2. **Database errors**: Delete `price_calculator.db` to reset the database

3. **Missing dependencies**: Ensure all packages are installed:
   ```bash
   pip install streamlit pandas plotly
   ```

### Performance Tips

- The app automatically refreshes when data changes
- Large datasets may slow down the analytics charts
- Consider pagination for very large item lists

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the same license as the original Flask version. 