import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Invoice Formatter", layout="wide")
st.title("📄 Invoice Formatter with CGST/SGST Merge")

uploaded_file = st.file_uploader("Upload your Invoice Excel file", type=['xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Step 1: Forward fill 'Invoice Number'
    df['Invoice Number'] = df['Invoice Number'].ffill()

    # Step 2: Forward fill invoice-level fields within each invoice group
    invoice_fields = ['Invoice Date', 'GST Treatment', 'SubTotal', 'Total']
    df[invoice_fields] = df.groupby('Invoice Number')[invoice_fields].ffill()

    # Step 3: Process and format
    result = []
    used_hsn = set()
    previous_invoice = None

    for index, row in df.iterrows():
        hsn = row['HSN/SAC']
        if pd.isna(hsn):
            hsn = ''

        new_row = row.copy()
        current_invoice = row['Invoice Number']
        invoice_hsn_key = (current_invoice, hsn)

        if invoice_hsn_key not in used_hsn:
            used_hsn.add(invoice_hsn_key)

            mask = (df['Invoice Number'] == current_invoice) & (df['HSN/SAC'] == hsn)
            new_row['Quantity'] = df.loc[mask, 'Quantity'].sum()
            new_row['CGST'] = df.loc[mask, 'CGST'].sum()
            new_row['SGST'] = df.loc[mask, 'SGST'].sum()
        else:
            new_row['Quantity'] = ''
            new_row['CGST'] = ''
            new_row['SGST'] = ''

        hsn_indexes = df[(df['Invoice Number'] == current_invoice) & (df['HSN/SAC'] == hsn)].index.tolist()
        if index != hsn_indexes[0]:
            new_row['HSN/SAC'] = ''

        if current_invoice != previous_invoice:
            previous_invoice = current_invoice
        else:
            new_row['Invoice Date'] = ''
            new_row['Invoice Number'] = ''
            new_row['SubTotal'] = ''
            new_row['Total'] = ''
            new_row['GST Treatment'] = ''

        result.append(new_row)

    # Create final DataFrame
    final_df = pd.DataFrame(result)

    # Show preview
    st.success("✅ Invoice processed successfully!")
    st.dataframe(final_df, use_container_width=True)

    # Prepare download
    output = BytesIO()
    final_df.to_excel(output, index=False, engine='openpyxl')
    st.download_button(
        label="📥 Download Formatted Invoice",
        data=output.getvalue(),
        file_name='formatted_invoice.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
