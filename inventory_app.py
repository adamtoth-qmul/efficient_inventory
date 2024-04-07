import streamlit as st
import pandas as pd
from io import BytesIO
import numpy as np
from datetime import datetime
import time
import base64
from st_aggrid import AgGrid, GridOptionsBuilder
from login_page import login_page


st.set_page_config(layout='wide')



# # Add CSS style
# st.write(
#     """
#     <style>
#     .filter-1 { background-color: #ffcccb; } /* Light red */
#     .filter-2 { background-color: #ffebcd; } /* Blanched almond */
#     .filter-3 { background-color: #f0e68c; } /* Khaki */
#     .filter-4 { background-color: #add8e6; } /* Light blue */
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

# # Initialise session state to store input data
# if 'wastage_data' not in st.session_state:
#     st.session_state.wastage_data = []
# if 'variance_data' not in st.session_state:
#     st.session_state.variance_data = []

########################################################################################################
##########################                      LOAD AND FILTER         ################################
########################################################################################################

def load_and_filter_excel(file):
    # Load the Excel file without specifying the header
    df = pd.read_excel(file, header=None)
    
    # Assuming the header starts from the first row, set the first row as the column names
    df.columns = df.iloc[0]
    df = df[1:]  # Exclude the first row which is now the header

    # Clean 'Name' column by trimming leading and trailing whitespace
    # and replacing multiple internal spaces with a single space
    df['Name'] = df['Name'].astype(str).str.strip().replace(r'\s+', ' ', regex=True)

    # Ensure that 'Close Qty' column exists
    if 'Close Qty' in df.columns:
        # Convert 'Close Qty' column to numeric values, coercing errors to NaN for non-numeric values
        df['Close Qty'] = pd.to_numeric(df['Close Qty'], errors='coerce')

        # Drop rows with NaN values in the "Close Qty" column, if needed
        df.dropna(subset=['Close Qty'], inplace=True)

        # Remove rows starting with 'SUBTOTAL (this section)'
        df = df[~df['Name'].str.startswith('SUBTOTAL (this section)')]

        # Replace 'None' values with empty string
        df = df.fillna('')
    else:
        st.error("The 'Close Qty' column does not exist in the uploaded file.")
        return None
    
    return df



########################################################################################################
##########################                    HIGHLIGHT PRODUCTS        ################################
########################################################################################################

def highlight_products(df):
    def highlight_products_cell(cell):
        value = cell[0] if isinstance(cell, tuple) else cell
        color = '#6495ED' if str(value).startswith('Products') or value == '' else ''
        return f'background-color: {color}'
    
    styled_df = df.style.applymap(highlight_products_cell)

    # Apply additional styling to column names (header)
    styled_df.set_table_styles(
        [{'selector': 'th',
          'props': [('background-color', '#FFFF00')]}]
    )
    return styled_df





########################################################################################################
##########################           FILTER DATA FOR SECOND TABLE       ################################
########################################################################################################

def filter_data_for_second_table(df):
    # Ensure 'Diff Cost' is numeric
    if 'Diff Cost' in df.columns:
        df['Diff Cost'] = pd.to_numeric(df['Diff Cost'], errors='coerce')
    
    # Filter based on 'Diff Cost' conditions (positive variances)
    filtered_df_pos_1 = df[(df['Diff Cost'] >= 5) & (df['Diff Cost'] <= 10)]
    filtered_df_pos_2 = df[(df['Diff Cost'] > 10) & (df['Diff Cost'] <= 20)]
    filtered_df_pos_3 = df[(df['Diff Cost'] > 20) & (df['Diff Cost'] <= 30)]
    filtered_df_pos_4 = df[df['Diff Cost'] > 30]

    # Filter based on 'Diff Cost' conditions (negative variances)
    filtered_df_neg_1 = df[(df['Diff Cost'] <= -5) & (df['Diff Cost'] > -10)]
    filtered_df_neg_2 = df[(df['Diff Cost'] <= -10) & (df['Diff Cost'] > -20)]
    filtered_df_neg_3 = df[(df['Diff Cost'] <= -20) & (df['Diff Cost'] > -30)]
    filtered_df_neg_4 = df[df['Diff Cost'] <= -30]

    # Combine filtered DataFrames for positive and negative variances
    combined_filtered_df_pos = pd.concat([filtered_df_pos_1, filtered_df_pos_2, filtered_df_pos_3, filtered_df_pos_4])
    combined_filtered_df_neg = pd.concat([filtered_df_neg_1, filtered_df_neg_2, filtered_df_neg_3, filtered_df_neg_4])

    # Create an empty DataFrame for spacing
    empty_space_df = pd.DataFrame(index=range(5), columns=df.columns).fillna("")
    
    # Combine all DataFrames with the empty DataFrame in between
    combined_filtered_sorted_df = pd.concat([combined_filtered_df_pos.sort_values(by='Diff Cost', ascending=False),
                                             empty_space_df,
                                             combined_filtered_df_neg.sort_values(by='Diff Cost', ascending=True)])

    # Add an extra column 
    combined_filtered_sorted_df['Action'] = ""

    # Remove specific columns
    columns_to_remove = ['Open Val', 'Req', 'Close Val', 'Diff Qty Last', 'Diff Weight AVG', 'Wastage Qty', 'Usage Qty']
    combined_filtered_sorted_df = combined_filtered_sorted_df.drop(columns=columns_to_remove)
    
    return combined_filtered_sorted_df








# Define dictionary containing information about items
items_info = {
    # AMATHUS ORDER LIST
    'Cider - sassy 0%, 275ML': {'par_level': 12.0, 'supplier': 'Amathus'},
    'Cider - Sassy Apple 330ml, 330ML': {'par_level': 36.0, 'supplier': 'Amathus'},
    'Bar - Luxardo Cherries 400g, 400GR': {'par_level': 0.5, 'supplier': 'Amathus'},
    'Cordial - Bottle green Elderflower 500ML, 500ML': {'par_level': 0.5, 'supplier': 'Amathus'},
    'Cordial - Bottle Green Ginger & Lemongrass 50cl, 500ML	': {'par_level': 0.7, 'supplier': 'Amathus'},

    'CJuice - Cloudy Apple [Eager] 1000ML, 1000ML': {'par_level': 8.0, 'supplier': 'Amathus'},
    'Juice - Cranberry [Ocean Spray] 1000ML SUB, 1000ML': {'par_level': 6.0, 'supplier': 'Amathus'},
    'Juice - Orange [Eager] 1000ML, 1000ML': {'par_level': 10.0, 'supplier': 'Amathus'},
    'Juice - Pineapple [Eager] 1000ML, 1000ML': {'par_level': 15.0, 'supplier': 'Amathus'},
    'Juice - Pink Grapefruit [Eager] 1000ML, 1000ML': {'par_level': 7.0, 'supplier': 'Amathus'},
    'Juice - Tomato [Eager] 1000ML, 1000ML': {'par_level': 12.0, 'supplier': 'Amathus'},
    'Crodino N/A Aperitif 175ml (1 x 175ML)': {'par_level': 12.0, 'supplier': 'Amathus'},

    'Fever-Tree - Elderflower Tonic 24 x 200ML (1 x 200ML)': {'par_level': 12.0, 'supplier': 'Amathus'},
    'Fever-Tree - Ginger Ale 200ML (1 x 200ML)': {'par_level': 48.0, 'supplier': 'Amathus'},
    'Fever-Tree - Ginger Beer 200ML (1 x 200ML)': {'par_level': 48.0, 'supplier': 'Amathus'},
    'Fever-Tree - Ginger Ale 200ML (1 x 200ML)': {'par_level': 240.0, 'supplier': 'Amathus'},
    'Fever-Tree - Lemonade 24 x 200ML (1 x 200ML)': {'par_level': 72.0, 'supplier':  'Amathus'},
    'Fever-Tree - Soda 24 x 200ML (1 x 200ML)': {'par_level': 120.0, 'supplier': 'Amathus'},
    'Fever-Tree - Refreshingly Light Tonic 200ML, 200ML': {'par_level': 24.0, 'supplier': 'Amathus'},
    'Fever-Tree - Tonic 24 x 200ML (1 x 200ML)': {'par_level': 120.0, 'supplier': 'Amathus'},

    'Coca-Cola - Coke Glass Bottles 24 x 20CL (Amathus) (1 x 200ML)': {'par_level': 144.0, 'supplier': 'Amathus'},
    'Coca-Cola - Diet Coke Glass Bottles 24 x 20CL (Amathus) (1 x 200ML)': {'par_level': 144.0, 'supplier': 'Amathus'},
    'REAL - Sparkling Tea Peony Blush 750ml, 750ML': {'par_level': 2.0, 'supplier': 'Amathus'},


    'APERITIF - Aperol 11% 700ML (1 x 700ML))': {'par_level': 10.0, 'supplier': 'Amathus'},
    'APERITIF - Botivo (Non-Alcoholic) (1 x 500ML))': {'par_level': 0.6, 'supplier': 'Amathus'},
    'APERITIF - Campari 25% 700ML (1 x 700ML))': {'par_level': 8.0, 'supplier': 'Amathus'},
    'APERITIF - Pentire Coastal Spritz (1 x 500ML)': {'par_level': 2.0, 'supplier': 'Amathus'},

    'Bitters - Angostura 44.7% 200ML, 200ML': {'par_level': 1.5, 'supplier': 'Amathus'},
    'Bitters - Angostura Orange 28% 100ML (1 x 100ML)': {'par_level': 0.5, 'supplier': 'Amathus'},

    'COGNAC - Courvoisier VS 700ML, 700ML': {'par_level': 0.5, 'supplier': 'Amathus'},
    'COGNAC - H By Hine 40% VSOP 700ML, 700ML': {'par_level': 0.4, 'supplier': 'Amathus'},
    'COGNAC - Martell VS 40% 700ML, 700ML': {'par_level': 0.5, 'supplier': 'Amathus'},

    'DIGESTIF - Absinthe Pernod 68% 700ML (1 x 700ML)': {'par_level': 0.5, 'supplier': 'Amathus'},
    'DIGESTIF - Amaro Montenegro Liquore Italiano 23% 700ML (1 x 700ML)': {'par_level': 0.5, 'supplier': 'Amathus'},
    'DIGESTIF - Fernet Branca 39% 700ML, 700ML': {'par_level': 0.5, 'supplier': 'Amathus'},


    'GIN - Beefeater Gin 40% 700ML (1 x 700ML)': {'par_level': 10.0, 'supplier': 'Amathus'},
    'GIN - Beefeater Twenty Four Gin 45% 700ML, 700ML': {'par_level': 0.5, 'supplier': 'Amathus'},
    'GIN - Hendricks 41.4% 700ML (1 x 700ML)': {'par_level': 1.0, 'supplier': 'Amathus'},
    'GIN - Malfy Con Arancia 700ML (1 x 700ML)': {'par_level': 0.8, 'supplier': 'Amathus'},
    'GIN - Malfy Rosa 700ML (1 x 700ML)': {'par_level': 0.8, 'supplier': 'Amathus'},
    'GIN - Monkey 47 47% 500ML (1 x 500ML)': {'par_level': 0.8, 'supplier': 'Amathus'},

    'GRAPPA - Marolo Grappa di Moscato NV 700ML, 700ML	': {'par_level': 0.5, 'supplier': 'Amathus'},

    'DIGESTIF - Benedictine 40% 700ML, 700ML': {'par_level': 0.5, 'supplier': 'Amathus'},
    'LIQUEUR - Antica Sambuca Classic (SUB) 700ML (1 x 700ML)': {'par_level': 0.5, 'supplier': 'Amathus'},
    'LIQUEUR - Baileys Irish Cream 17% 700ML (1 x 700ML)': {'par_level': 0.7, 'supplier': 'Amathus'},
    'LIQUEUR - Cartron Creme de Peche de Vigne 18% 500ML (1 x 500ML)': {'par_level': 6.0, 'supplier': 'Amathus'},
    'LIQUEUR - Chambord Raspberry 16.5% 700ML, 700ML': {'par_level': 0.3, 'supplier': 'Amathus'},
    'LIQUEUR - Chartreuse Green 55% 700ML, 700ML': {'par_level': 0.3, 'supplier': 'Amathus'},
    'LIQUEUR - Chartreuse Yellow 40% 700ML, 700ML': {'par_level': 0.3, 'supplier': 'Amathus'},
    'LIQUEUR - Cointreau 40% 700ML, 700ML': {'par_level': 0.5, 'supplier': 'Amathus'},
    'LIQUEUR - Cointreau 40% 700ML, 700ML': {'par_level': 0.5, 'supplier': 'Amathus'},
    'LIQUEUR - Cartron Curacao Triple Sec 25% 700ML (1 x 700ML)': {'par_level': 8.0, 'supplier': 'Amathus'},
    'LIQUEUR - Jagermeister 35% 700ML, 700ML': {'par_level': 0.7, 'supplier': 'Amathus'},
    'LIQUEUR - Disaronno 28% 700ML (1 x 700ML)': {'par_level': 0.8, 'supplier': 'Amathus'},
    'LIQUEUR - Kahlua 20% 700ML (1 x 700ML)': {'par_level': 8.0, 'supplier': 'Amathus'},
    'LIQUEUR - Luxardo Limoncello 27% 70cl (1 x 700ML)': {'par_level': 1.0, 'supplier': 'Amathus'},
    'LIQUEUR - Lyres Amaretti': {'par_level': 0.4, 'supplier': 'Amathus'},
    'LIQUEUR - Lyres Coffee Originale (Non-Alcoholic) 700ml, 700ML': {'par_level': 0.4, 'supplier': 'Amathus'},
    'LIQUEUR - Pimms No. 1 The Original 25% 700ML, 700ML': {'par_level': 0.8, 'supplier': 'Amathus'},
    'PISCO - 1615 Quebranta 40% 700ML, 700ML': {'par_level': 0.5, 'supplier': 'Amathus'},
    'LIQUEUR - Parafante fig leaf liqueur (1 x 700ML)': {'par_level': 4.0, 'supplier': 'Amathus'},


    'Plantation Pineapple Stiggins Fancy Rum 70CL (1 x 700ML)': {'par_level': 3.0, 'supplier': 'Amathus'},
    'RUM - Chairmans Reserved Spiced Rum - 700ML, 700ML': {'par_level': 0.6, 'supplier': 'Amathus'},
    'RUM - El Dorado 12yr 40% 700ML, 700ML': {'par_level': 0.3, 'supplier': 'Amathus'},
    'RUM - Gosling Black Seal 40% 700ML (1 x 700ML)': {'par_level': 0.6, 'supplier': 'Amathus'},
    'RUM - Havana Club 3yr 40% 700ML (1 x 700ML)': {'par_level': 8.0, 'supplier': 'Amathus'},
    'RUM - Havana Club Anejo Especial 40% 700ML (1 x 700ML)': {'par_level': 8.0, 'supplier': 'Amathus'},
    'RUM - Havana Club 7yr 40% 700ML, 700ML': {'par_level': 0.4, 'supplier': 'Amathus'},
    'RUM - Havana Spiced, 700ML': {'par_level': 0.4, 'supplier': 'Amathus'},
    'RUM - Wray & Nephew Overproof 63% 700ML, 700ML': {'par_level': 0.5, 'supplier': 'Amathus'},
    'SCOTCH - The Glenlivet Carribean Reserve, 700ML': {'par_level': 0.5, 'supplier': 'Amathus'},


    'MEZCAL - Del Maguey Vida Puebla 42% 700ML (1 x 700ML)': {'par_level': 6.0, 'supplier': 'Amathus'},
    'TEQUILA - Cabrito Blanco 40% 100% Agave 700ML (1 x 700ML)': {'par_level': 12.0, 'supplier': 'Amathus'},
    'TEQUILA - Cabrito Reposado 40% 100% Agave 700ML (1 x 700ML)': {'par_level': 12.0, 'supplier': 'Amathus'},
    'TEQUILA - Patron Anejo 40% 700ML (1 x 700ML)': {'par_level': 0.5, 'supplier': 'Amathus'},
    'TEQUILA Cazcabel Coffee 70cl (1 x 700ML)': {'par_level': 0.8, 'supplier': 'Amathus'},


    'VERMOUTH - Dolin Chambery Rouge 16% 750ML (1 x 750ML)': {'par_level': 2.0, 'supplier': 'Amathus'},
    'VERMOUTH - Lillet Rose (1 x 750ML)': {'par_level': 3.0, 'supplier': 'Amathus'},


    'VODKA - Absolut Blue 40% 700ML (1 x 700ML)': {'par_level': 10.0, 'supplier': 'Amathus'},
    'VODKA - Absolut Vanilla 40% 700ML (1 x 700ML)': {'par_level': 0.6, 'supplier': 'Amathus'},
    'VODKA - Belvedere 40% 700ML, 700ML': {'par_level': 0.4, 'supplier': 'Amathus'},



    'BOURBON - Wild Turkey 81 - 40.5% 700ML (1 x 700ML)': {'par_level': 8.0, 'supplier': 'Amathus'},
    'BOURBON - Wild Turkey 101 50.5% 700ML, 700ML': {'par_level': 0.4, 'supplier': 'Amathus'},
    'BOURBON - Woodford Reserve 43.2% 700ML (1 x 700ML)': {'par_level': 0.5, 'supplier': 'Amathus'},
    'IRISH - Jameson 40% 700ML (1 x 700ML)': {'par_level': 0.6, 'supplier': 'Amathus'},
    'JAPANESE - Suntory Hibiki Harmony 43% max 1 per order 700ML (1 x 700ML)': {'par_level': 0.6, 'supplier': 'Amathus'},
    'JAPANESE - Nikka from the Barrel 51.4% 500ML, 500ML': {'par_level': 0.5, 'supplier': 'Amathus'},
    'RYE - Rittenhouse BIB 50% 100 proof 750ML, 750ML': {'par_level': 0.4, 'supplier': 'Amathus'},
    'RYE - Wild Turkey 40.5% 700ML, 700ML': {'par_level': 0.4, 'supplier': 'Amathus'},
    'SCOTCH - Ardbeg 10yr 46% 700ML, 700ML': {'par_level': 0.4, 'supplier': 'Amathus'},
    'SCOTCH - Chivas Regal 12yr 40% 700ML (1 x 700ML)': {'par_level': 0.8, 'supplier': 'Amathus'},
    'SCOTCH - Glenfiddich 12yr 40% 700ML, 700ML': {'par_level': 0.5, 'supplier': 'Amathus'},
    'SCOTCH - Old Pulteney 12yr 40% 700ML, 700ML': {'par_level': 0.3, 'supplier': 'Amathus'},
    'TENNESSEE - Jack Daniels 40% 700ML (1 x 700ML)': {'par_level': 0.8, 'supplier': 'Amathus'},
    'WHISKY - Redbreast 12yo, 700ML': {'par_level': 0.3, 'supplier': 'Amathus'},


    'NV 10-Year-Old Tawny Port, Sandeman 75cl (1 x 750ML)': {'par_level': 0.6, 'supplier': 'Amathus'},


    # BIERCRAFT ORDER
    'Ale - Beavertown Neck Oil 330ML, 330ML': {'par_level': 18, 'supplier': 'Biercraft'},
    'Ale - Farmhouse Ale, Hop Hand Fallacy, Lost & Grounded 440ml Can, 440ML	': {'par_level': 18, 'supplier': 'Biercraft'},
    'Ale - Beavertown Neck Oil 330ML, 330ML': {'par_level': 18, 'supplier': 'Biercraft'},
    'Ale - Neck Oil - 30L, 1LT': {'par_level': 1000.0, 'supplier': 'Biercraft'},
    'Power Plant Natural Lager 330ML (1 x 330ML)': {'par_level': 200.0, 'supplier': 'Biercraft'},
    'Stout - Guinness 50L, 1LT': {'par_level': 150.0, 'supplier': 'Biercraft'},
    'Lager - Lucky Saint 0.5% 330ml, 330ML': {'par_level': 24.0, 'supplier': 'Biercraft'},


    # LOST AND GROUNDED ORDER
    'Pale Ale - Lost and Grounded Pale Ale (Wanna Go to the Sun) 30L, 30LT': {'par_level': 5.0, 'supplier': 'Lost and Grounded'},
    'Lager - Lost and Grounded Helles 30L, 30LT': {'par_level': 6.0, 'supplier': 'Lost and Grounded'},

    # STORES SUPPLY WAREHOUSE
    'Agua de Madre - Pink Grapefruit + Lime Water Kefir - Case - 12 x 330ml Cans, 330ML': {'par_level': 144.0, 'supplier': 'Stores Supply Warehouse'},
    'Karma - Gingerella Can 24 x 250ML, 250ML': {'par_level': 24.0, 'supplier': 'Stores Supply Warehouse'},
    'LA Brewery Kombucha - Ginger - Case - 12 x 330ml, 330ML': {'par_level': 72.0, 'supplier': 'Stores Supply Warehouse'},
    'Sparkling Mate, Charitea CASE 24 x 330ML, 330ML': {'par_level': 24.0, 'supplier': 'Stores Supply Warehouse'}

}


def compare_names(df, items_info):
    # Convert DataFrame names to a set for efficient comparison
    df_names = set(df['Name'].astype(str).str.strip())
    
    # Convert items_info keys to a set
    items_info_names = set(items_info.keys())
    
    # Find names in df not in items_info
    missing_in_items_info = df_names - items_info_names
    if missing_in_items_info:
        print("Names in df but not in items_info:", missing_in_items_info)
    else:
        print("All names in df are present in items_info.")
    
    # Find names in items_info not in df
    missing_in_df = items_info_names - df_names
    if missing_in_df:
        print("Names in items_info but not in df:", missing_in_df)
    else:
        print("All names in items_info are present in df.")



########################################################################################################
##########################           CALCULATE ORDER AMOUNTS            ################################
########################################################################################################

def check_inventory_needs(df, items_info):
    items_to_order = []

    for item, info in items_info.items():
        par_level = info.get('par_level')
        supplier = info.get('supplier')

        if par_level is None or supplier is None:
            # Skip items with missing information
            continue

        item_row = df[df['Name'] == item]
        if not item_row.empty:
            close_qty = item_row['Close Qty'].iloc[0]
            # Check if the 'Close Qty' value is numeric
            if pd.notnull(close_qty) and isinstance(close_qty, (int, float)):
                if close_qty < par_level:
                    quantity_needed = par_level - close_qty
                    items_to_order.append({'Item': item, 'Quantity Needed': quantity_needed, 'Supplier': supplier})
            else:
                # Skip items with non-numeric or missing 'Close Qty'
                continue
        else:
            # Skip items not found in the DataFrame
            continue

    items_to_order_df = pd.DataFrame(items_to_order)
    return items_to_order_df



########################################################################################################
##########################                    MAIN FUNCTION             ################################
########################################################################################################

def main():
    st.title('Good morning!')

    uploaded_file = st.file_uploader("Choose an Excel file", type=["xls", "xlsx"])

    # Initialize session state for storing actions for each item
    if 'actions_for_items' not in st.session_state:
        st.session_state.actions_for_items = {}

    if uploaded_file is not None:
        df = load_and_filter_excel(uploaded_file)
        compare_names(df, items_info)

        st.write("Original dataset:")
        # Display the original dataframe with full width in the first row
        st.dataframe(df)  # Display the DataFrame without styling for simplicity

        # with first_row_cols[1]:
        st.write("Filtered dataset:")
        # Display each filtered table in a column
        filtered_df = filter_data_for_second_table(df)
        st.dataframe(filtered_df)
        # st.dataframe(filtered_df)

        if not filtered_df.empty:
            # Render AgGrid for user to make edits, before submitting
            grid_result = AgGrid(filtered_df, editable=True, key='grid1')



        if st.button('Submit'):
            # Use the data from the grid after submitting
            edited_df = grid_result['data']
            edited_df['Action'] = edited_df['Action'].astype(str)

            # Assuming 'Action' is the column based on which you are separating the tables
            unique_actions = edited_df['Action'].unique()

            # Calculate the number of columns needed based on the number of unique actions
            columns = st.columns(max(len(unique_actions), 1))

            # Iterate over each unique action to display separate dataframes
            for i, action in enumerate(unique_actions):
                action_df = edited_df[edited_df['Action'] == action]

                with columns[i]:
                    st.write(f"Data for Action: {action}")
                    st.dataframe(action_df, height=300)  # Corrected line
        else:
            st.write("No data matches the filtering criteria.")


        # Check inventory needs and generate order list
        items_to_order = []
        for item, info in items_info.items():
            par_level = info.get('par_level')
            supplier = info.get('supplier')

            if par_level is None or supplier is None:
                print(f"Skipping item {item}: Missing par_level or supplier.")
                continue

            item_row = df[df['Name'] == item]
            if not item_row.empty:
                close_qty = item_row['Close Qty'].iloc[0]
                print(f"Item: {item}, Close Qty: {close_qty}, Par Level: {par_level}")
                if pd.notnull(close_qty) and isinstance(close_qty, (int, float)):
                    if close_qty < par_level:
                        print(f"Item {item} needs ordering.")
                        quantity_needed = par_level - close_qty
                        items_to_order.append({'Item': item, 'Quantity Needed': quantity_needed, 'Supplier': supplier})
                else:
                    print(f"Skipping item {item}: Close Qty is not numeric.")
            else:
                print(f"Skipping item {item}: No data found.")
            

        # Display the table containing items that need to be ordered
        st.write("Items to Order:")
        
        # Group items by supplier
        grouped_by_supplier = {}
        for item, info in items_info.items():
            supplier = info['supplier']
            if supplier not in grouped_by_supplier:
                grouped_by_supplier[supplier] = []
            grouped_by_supplier[supplier].append((item, info))

        # Create layout for the ordering tables
        ordering_tables_cols = st.columns(len(grouped_by_supplier))

        # Display separate tables for items from each supplier next to each other
        for i, (supplier, items) in enumerate(grouped_by_supplier.items()):
            with ordering_tables_cols[i]:
                st.subheader(f"Order List for {supplier}")
                items_info_supplier = {item: info for item, info in items}
                supplier_order_df = check_inventory_needs(df, items_info_supplier)
                st.dataframe(supplier_order_df)

# Initialize session state for login status
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Conditional logic to display the login page or the main app content
if not st.session_state['logged_in']:
    login_page()  # Show login page if not logged in
else:
    main()






