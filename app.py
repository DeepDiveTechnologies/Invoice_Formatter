import streamlit as st
import pandas as pd

st.set_page_config(page_title="Invoice Formatter", layout="wide")
st.title("📄 Invoice Formatter App")

uploaded_file = st.file_uploader(
    "Upload your Invoice Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Fill forward for Invoice Date, Number, GST Treatment
    df['Invoice Date'] = df['Invoice Date'].ffill()
    df['Invoice Number'] = df['Invoice Number'].ffill()
    df['GST Treatment'] = df['GST Treatment'].ffill()

    # Create a result list
    result = []
    used_hsn = set()
    first_row = True

    for index, row in df.iterrows():
        hsn = row['HSN/SAC']
        if pd.isna(hsn):
            hsn = ''
        new_row = row.copy()

        if hsn not in used_hsn:
            used_hsn.add(hsn)
            same_hsn_rows = df[df['HSN/SAC'] == hsn]

            # Sum Quantity, CGST, SGST for this HSN
            new_row['Quantity'] = same_hsn_rows['Quantity'].sum()
            new_row['CGST'] = same_hsn_rows['CGST'].sum()
            new_row['SGST'] = same_hsn_rows['SGST'].sum()
        else:
            new_row['Quantity'] = ''
            new_row['CGST'] = ''
            new_row['SGST'] = ''

        # Clear duplicate HSN/SAC from second time onwards
        hsn_indices = df[df['HSN/SAC'] == hsn].index.tolist()
        if index != hsn_indices[0]:
            new_row['HSN/SAC'] = ''

        # Clear first columns except first row
        if not first_row:
            new_row['Invoice Date'] = ''
            new_row['Invoice Number'] = ''
            new_row['SubTotal'] = ''
            new_row['Total'] = ''
        else:
            first_row = False

        result.append(new_row)

    final_df = pd.DataFrame(result)

    # Show result
    st.subheader("🧾 Formatted Invoice Preview")
    st.dataframe(final_df)

    # Download option
    @st.cache_data
    def convert_df_to_excel(df):
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Formatted Invoice")
        return output.getvalue()

    excel_bytes = convert_df_to_excel(final_df)
    st.download_button(
        label="📥 Download Formatted Excel",
        data=excel_bytes,
        file_name="formatted_invoice.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
