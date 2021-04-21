# Nancy Tran
# Creating a GUI for SJCOC with Streamlit

import streamlit as st
import pandas as pd
from datetime import datetime
import base64
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import numpy as np
from fpdf import FPDF
from tempfile import NamedTemporaryFile
from plotly.subplots import make_subplots


# =============================================================================
# Step 1: Go to Anaconda Prompt
# Step 2: cd Desktop/Capstone/Capstone_Code (or where you saved this py script)
# Step 3: streamlit run testing_out_streamlit.py
# Step 4: Open http://localhost:8501 in web browser

# Youtube video: https://www.youtube.com/watch?v=w2PwerViVbA&t=14s
# Download Excel File: https://discuss.streamlit.io/t/how-to-download-file-in-streamlit/1806/11

# =============================================================================
# Configurations
st.set_option('deprecation.showfileUploaderEncoding', False)

# Title of the web app
st.markdown("<h1 style='text-align: center; color: black;'>SJCoC Report</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: black;'>University of the Pacific Data Science Team</h3>", unsafe_allow_html=True)

# =============================================================================

# Function that creates the Performance Report Table
def performance(d_entry, d_exit):

    # Removing the tailing spaces behind the column names
    d_entry.columns = d_entry.columns.str.strip()
    d_exit.columns = d_exit.columns.str.strip()

    # Removing duplicate rows in the entry and exit data
    d_entry = d_entry.drop_duplicates()
    d_exit = d_exit.drop_duplicates()
    
    # Focusing only on the attributes provided in the sample data
    d_entry = d_entry[["Unique ID", "Enrollment Start Date", "Enrollment Exit Date", "DOB", "Household ID", "Gender", "Race", "Ethnicity", "Relationship to Head of Household", "Housing Move-In Date"]]
    d_exit = d_exit[["Unique ID", "Enrollment Start Date", "Enrollment Exit Date", "DOB", "Household ID", "Gender", "Race", "Ethnicity", "Destination", "Specify Other Exit Destination"]]

    # Identifying the column names that the entry and exit data have in common
    common_columns = list(d_entry.columns.intersection(d_exit.columns))

    # Merging the entry and exit data on the common columns
    d = pd.merge(d_entry, d_exit, how='left', left_on = common_columns, right_on = common_columns)


    # Subset dataframe that has move in dates corresponding to its respective household id
    move_date = d[d['Housing Move-In Date'].notna()][['Household ID','Housing Move-In Date']]
    
    # Merging the dataframe with the move_date df to fill in the date
    # When merging the dataframes it repeats column names so it uses suffixes(ie. Housing_x, Housing_y)
    # So I reassined the suffixes for the subsequent to be "_x" and "" the second column will be filled with dates, we don't need the "_x" column so it will be dropped 
    d = d.merge(move_date, on = 'Household ID', how = 'left', suffixes=["_x",""]).drop(['Housing Move-In Date_x'], axis=1)


    # We want to calculate indiviual's ages at the time they left the program. so we will focus on those that have an exit date
    d = d[(d['Enrollment Exit Date'].notna())]

    #----------------------------------
    # Creating a function the calculates age
    def calculate_age(s,e):
        if s is None:
            return(float('NaN'))
        if (s != float('NaN')) & (e != float('NaN')):
            born = datetime.strptime(s, "%m/%d/%Y").date()      # Converting DOB string to a date time using datetime library
            exit = datetime.strptime(e, "%m/%d/%Y").date()      # Today's date
            return exit.year - born.year - ((exit.month, exit.day) < (born.month, born.day))
        else:
            return(float('NaN'))
    #----------------------------------

    # Creating a new column that contains the individual's age upon their exit from the program
    d['Age'] = d.apply(lambda x: calculate_age(x['DOB'], x['Enrollment Exit Date']), axis=1)

    # Dataframe of Adult and Child counts in each household
    adults = d.groupby('Household ID')['Age'].apply(lambda x: (x>=18).sum()).reset_index(name='Adults per Household')
    children = d.groupby('Household ID')['Age'].apply(lambda x: (x < 18).sum()).reset_index(name='Children per Household')

    # Counting records with NaN ages to account for Unknown Household types
    na_ages = d.groupby('Household ID')['Age'].apply(lambda x: (x.isna()).sum()).reset_index(name='na_ages')

    # Merging the merged dataframe with the adult first and then merge new df with children count dataframe
    d = pd.merge(pd.merge(d,adults,on='Household ID',how='outer'),children,on='Household ID', how='outer')
    d = pd.merge(d,na_ages,on='Household ID',how='outer')

    #----------------------------------
    # Creating a function to determine household type
    def household(s):
        if (s["Adults per Household"] > 0) and (s["Children per Household"] == 0) and (s["na_ages"] == 0):
            return("Without Children")
        if (s["Adults per Household"] > 0) and (s["Children per Household"] > 0):
            return("With Children and Adults")
        if (s["Adults per Household"] == 0) and (s["Children per Household"] > 0) and (s["na_ages"] == 0):
            return("With Only Children")
        else:
            return("Unknown")
    #----------------------------------

    # Creating a column that assigns household type using the household() function we created
    d["Household Type"] = d.apply(household, axis=1)

    # List of permanent housing categories
    permanent_category = ["Moved from one HOPWA funded project to HOPWA PH",
                          "Owned by client, no ongoing housing subsidy",
                          "Owned by client, with ongoing housing subsidy",
                          "Rental by client, no ongoing housing subsidy",
                          "Rental by client, with VASH housing subsidy",
                          "Rental by client, with GPD TIP housing subsidy",
                          "Rental by client, with other ongoing housing subsidy",
                          "Permanent housing (other than RRH) for formerly homeless persons",
                          "Staying or living with family, permanent tenure",
                          "Staying or living with friends, permanent tenure",
                          "Rental by client, with RRH or equivalent subsidy",
                          "Rental by client, with HCV voucher (tenant or project based)",
                          "Rental by client in a public housing unit"]

    # List of temporary housing categories
    temporary_category = ["Emergency shelter, including hotel or motel paid for with emergency shelter voucher, or RHY-funded Host Home shelter",
                          "Moved from one HOPWA funded project to HOPWA TH",
                          "Transitional housing for homeless persons (including homeless youth)",
                          "Staying or living with family, temporary tenure (e.g. room, apartment or house)",
                          "Staying or living with friends, temporary tenure (e.g. room, apartment or house)",
                          "Place not meant for habitation (e.g., a vehicle, an abandoned building, bus / train / subway station / airport or anywhere outside)",
                          "Safe Haven",
                          "Hotel or motel paid for without emergency shelter voucher",
                          "Host Home (non-crisis)"]

    # List of institutional setting housing categories
    institutional_setting_category = ["Foster care home or group foster care home",
                                      "Psychiatric hospital or other psychiatric facility",
                                      "Substance abuse treatment facility or detox center",
                                      "Hospital or other residential non-psychiatric medical facility",
                                      "Jail, prison, or juvenile detention facility",
                                      "Long-term care facility or nursing home"]

    # List of other housing categories
    other_category= ["Residential project or halfway house with no homeless criteria",
                     "Deceased",
                     "Other",
                     "Client Doesn't Know/Client Refused",
                     "Data Not Collected (no exit interview completed)"]

    #----------------------------------
    # Creating a function that assigns housing destination types based on two conditions:
    #    (1) "Destination" entry
    def housing(s):
        if (s["Destination"] in permanent_category) and (s["Housing Move-In Date"] != None):
            return("Permanent Destinations")
        if (s["Destination"] in temporary_category) and (s["Housing Move-In Date"] != None):
            return("Temporary Destinations")
        if (s["Destination"] in institutional_setting_category) and (s["Housing Move-In Date"] != None):
            return("Institutional Settings")
        if (s["Destination"] in other_category) and (s["Housing Move-In Date"] != None):
            return("Other Destinations")
        else:
            return(float("NaN"))
    #----------------------------------

    # Creating a column that assigns housing destination type using the housing() function we created
    d['Destination Type'] = d.apply(housing, axis=1)
    
    # Creating a copy of the cleaned data that we can call for subsequent data visualizations
    d_complete = d.copy()

    # This subset excludes those that do NOT have a move-in date
    d = d[(d['Housing Move-In Date'].notna()) & (d['Relationship to Head of Household']=='Self (head of household)')]

    #----------------------------------
    # Function that counts households
    def destination_table(dest_type, housing_destination_category):

        df_list = [[dest_type]]

        for dest in housing_destination_category:

            # Dataframe that subsets by destination category and Destination Type
            dd = d[(d["Destination"] == dest) & (d["Destination Type"] == dest_type)]   # subset df belonging to destination in permanent list and Permanent Destination       

            # Determining total number of households
            total = len(dd["Household ID"].unique())

            # Determining household counts by the length of unique households from dataframes subsetted by Household Type
            wo_c = len(dd[dd["Household Type"] == "Without Children"]['Household ID'].unique())        # Number of households without children and adults
            w_ca = len(dd[dd["Household Type"] == "With Children and Adults"]['Household ID'].unique())# Number of households with children and adults
            w_c = len(dd[dd["Household Type"] == "With Only Children"]['Household ID'].unique())       # Number of households with only children
            u = len(dd[dd["Household Type"] == "Unknown"]['Household ID'].unique())                    # Number of unknown households

            # Creating a list out of the household counts from each Household Type
            count_list = [dest, total, wo_c, w_ca, w_c, u]

            # Appending the count_list to the main list
            df_list.append(count_list)

        # List of table column names from the performance report (we will use this to rename columns when we convert counts to a pd dataframe)
        table_col_names = ['Destination', 'Total', 'Without Children','With Children and Adults', "With Only Children","Unknown Household Type"]

        # Converts the list of Destination type lists to a Pandas dataframe
        df = pd.DataFrame(df_list, columns = table_col_names)

        # Creating the subtotal row by summing the df column wise(excludes the first row and first column bc those are headers)
        df.loc[len(df)] = ["Subtotal"] + list(df.iloc[1:, 1:].sum(axis = 0))

        return(df)
    #----------------------------------

    # Permanent Table using the destination_table() function
    permanent_table = destination_table("Permanent Destinations", permanent_category)

    # Temporary Table using the destination_table() function
    temporary_table = destination_table("Temporary Destinations", temporary_category)

    # Institutional Setting Table using the destination_table() function
    institutional_table = destination_table("Institutional Settings", institutional_setting_category)

    # Other Destinations Table using the destination_table() function
    other_table = destination_table("Other Destinations", other_category)

    # Concatenating the 4 tables to make a collective table
    performance_table = pd.concat([permanent_table, temporary_table, institutional_table, other_table]).reset_index(drop=True)

    # Total Row: Sums all of the subtotal rows to get overall Total
    performance_table.loc[len(performance_table)] = ["Total"] + list(performance_table[performance_table['Destination']=="Subtotal"].iloc[:,1:].sum(axis=0))

    # Total persons exiting to positive housing destinations: Column sums on a subset dataframe that contains "Permananent Destinations" housing
    performance_table.loc[len(performance_table)] = ["Total persons exiting to positive housing destinations"] + list(performance_table[performance_table['Destination'].isin(permanent_category)].iloc[:,1:].sum(axis=0))

    # Total persons whose destinations excluded them from the calculation: Everyone else that is not in "Permanent Destinations"
    performance_table.loc[len(performance_table)] = ["Total persons whose destinations excluded them from the calculation"] + list(performance_table[performance_table['Destination'].isin(temporary_category+institutional_setting_category+other_category)].iloc[:,1:].sum(axis=0))

    # Percentage: Number of households per category divided by the total number of households with a move-in date
    performance_table.loc[len(performance_table)] = ["Percentage"] + list(round(performance_table[performance_table["Destination"]=="Total"].iloc[:, 1:].sum(axis=0) / d[d['Destination Type'].notna()].shape[0] *100,2).astype(str)+ '%')

    # performance() fuction returns a pandas dataframe
    return(d_complete,performance_table)


# =============================================================================
# =============================================================================
# # Original Function to convert the pandas performance_table df to an excel file
# def to_excel(df):
#     output = BytesIO()
#     writer = pd.ExcelWriter(output, engine='xlsxwriter')
#     df.to_excel(writer, index=False, sheet_name='Sheet1')
#     writer.save()
#     processed_data = output.getvalue()
#     return(processed_data)
# =============================================================================

# Function that converts the pandas performance_table df to an excel fe
from SJCoC_Worksheet_Format import writeToWorksheet  # Jose's formatting function
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    writeToWorksheet(writer, df,'Q23c')
    writer.save()
    processed_data = output.getvalue()
    return(processed_data) 


# Function used produce a download link of the performance_table excel file
def get_table_download_link(df):
    val = to_excel(df)
    b64 = base64.b64encode(val)  # val looks like b'...'
    return(f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="Performance_Report.xlsx">Download Performance Report Excel File</a>')


# Function used produce a pdf download link of the data visualizations
def create_pdf_download_link(val):
    b64 = base64.b64encode(val)  # val looks like b'...'
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="Performance_Report_Charts.pdf">Download Performance Report Charts PDF</a>'


# =============================================================================
# Function that produces the line plot of indviduals/household counts with move-in dates
def line_plots(dff):
    # Making sure pandas recognizes Housing move-in date as a datetime type
    dff["Housing Move-In Date"] = pd.to_datetime(dff["Housing Move-In Date"])
    
    # List of all month+year between first and last housing move in date (allows us to capture months without move-in dates too)
    a = pd.date_range(min(dff["Housing Move-In Date"]),max(dff["Housing Move-In Date"]),freq='D').strftime('%B %Y').unique() 
    
    # Coverting move in dates to month+year for each unique id
    unique_ID = dff[["Unique ID", "Housing Move-In Date"]].sort_values("Housing Move-In Date").drop_duplicates()
    unique_ID['Month Year'] = pd.to_datetime(unique_ID['Housing Move-In Date']).dt.strftime('%B %Y')
    
    # Coverting move in dates to month+year for each household id
    household_ID = dff[["Household ID", "Housing Move-In Date"]].sort_values("Housing Move-In Date").drop_duplicates()
    household_ID['Month Year'] = pd.to_datetime(household_ID['Housing Move-In Date']).dt.strftime('%B %Y')

    unique_counts = []     # Contains the move-in date counts per unique id
    household_counts = []  # Contains the movie-in date counts per household
    for dte in a:
        unique_counts.append(list(unique_ID['Month Year']).count(dte))
        household_counts.append(list(household_ID['Month Year']).count(dte))

    # Client count plot(Unique Id)
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.2,
        specs=[[{"type": "scatter"}],
               [{"type": "table"}]] )
    fig.add_trace(
        go.Scatter(
            x=a,
            y=unique_counts,
            mode='lines',
            line_color='#d55e00'),
                   row=1, col=1)
    fig.add_trace(
        go.Table(header=dict(values=['Time', 'Client Counts']),
         cells=dict(values=[a,unique_counts])),
        row=2, col=1
    )
    fig.update_layout(
        height=700,
        showlegend=False,
        title_text="Number of Individuals with a Move-In Date",
    )
    
    # Household count plot (household Id)
    fig2 = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.2,
        specs=[[{"type": "scatter"}],
               [{"type": "table"}]] )
    fig2.add_trace(
        go.Scatter(
            x=a,
            y=household_counts,
            mode='lines',
            line_color='#d55e00'),
                   row=1, col=1)
    fig2.add_trace(
        go.Table(header=dict(values=['Time', 'Household Counts']),
         cells=dict(values=[a,household_counts])),
        row=2, col=1
    )
    fig2.update_layout(
        height=800,
        showlegend=False,
        title_text="Number of Households with a Move-In Date",
    )
    
    return(fig,fig2)



# =============================================================================
def SankeyDiagram(cols=[]):
    
    df = clean.groupby(cols).agg({'Unique ID':'count'}).reset_index()
    df = df.set_axis([*df.columns[:-1], 'Total_Numbers'], axis=1, inplace=False)
    value_col='Total_Numbers'
    
    colorPalette = px.colors.qualitative.D3
    labelList = []
    colorNumList = []
    for catCol in cols:
        labelListTemp =  list(set(df[catCol].values))
        colorNumList.append(len(labelListTemp))
        labelList = labelList + labelListTemp
        
    # Remove duplicates from labelList
    labelList = list(dict.fromkeys(labelList))
    
    # Define colors based on number of levels
    colorList = []
    for index, colorNum in enumerate(colorNumList):
        colorList = colorList + [colorPalette[index]]*colorNum
        
    # Transform df into a source-target pair
    for i in range(len(cols)-1):
        if i==0:
            sourceTargetDf = df[[cols[i],cols[i+1],value_col]]
            sourceTargetDf.columns = ['source','target','count']
        else:
            tempDf = df[[cols[i],cols[i+1],value_col]]
            tempDf.columns = ['source','target','count']
            sourceTargetDf = pd.concat([sourceTargetDf,tempDf])
            
        sourceTargetDf = sourceTargetDf.groupby(['source','target']).agg({'count':'sum'}).reset_index()
        
    # Add index for source-target pair
    sourceTargetDf['source_indices'] = [labelList.index(i) for i in sourceTargetDf.source]
    sourceTargetDf['target_indices'] = [labelList.index(j) for j in sourceTargetDf.target]
    
    fig = go.Figure(data=[go.Sankey(
        # Define nodes
        node = dict(
          pad = 15,
          thickness = 20,
          line = dict(
            color = "black",
            width = 0.5
          ),
          label = labelList,
          color = colorList
        ),

        # Add links
        link = dict(
          source = sourceTargetDf['source_indices'],
          target = sourceTargetDf['target_indices'],
          value = sourceTargetDf['count']
        
    ))])
    fig.update_layout(title_text="Sankey Diagram", annotations=[
    go.layout.Annotation(
      showarrow=False,
      text='** Counted by unique individuals',
      xanchor='right',
      x=1,
      xshift=75,
      yanchor='top',
      y=-0.1,
      font=dict(
        size=12,
        color="grey"
      )
    )])
    return(fig)


# =============================================================================
# When a file is uploaded it will display all of the uploaded excel files, download link, and various plotly graphs
uploaded_file = st.file_uploader("Upload your Excel file.", type="xlsx",accept_multiple_files=True)

if uploaded_file:
    
    # The empty lists will store the read excel files
    d_entry = []
    d_exit = []
    
    # The for loop reads the excel files by sheet name and converts it to a pd dataframe
    for file in uploaded_file:
        Entry = pd.read_excel(file,sheet_name ='Entry data')
        Exit = pd.read_excel(file,sheet_name ='Exit data')
        
        d_entry.append(Entry)
        d_exit.append(Exit)
        
    # We concatenate the list of pd dataframes to create a cumulative dataframe
    df_entry = pd.concat(d_entry).reset_index(drop=True)
    df_exit = pd.concat(d_exit).reset_index(drop=True)
    
    # Cleaned data (this df will be used to create visuals)
    clean = performance(df_entry, df_exit)[0]
    
    # Pandas df of performance report
    d = performance(df_entry, df_exit)[1]

    # Function to format streamlit display of performance report
    def highlight_gray(x):
        if x.Total == '':
            return ['background-color: lightgray']*6                     # Highlighting in gray
        if (x.Destination == 'Subtotal') or (x.Destination == 'Total'):  # Bolding Subtotals and Total Row
            return['font-weight: bold']*6
        else:
            return ['background-color: white']*6
        
    # Formating display table
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("**Performance Report Preview**")
    display = d.replace(np.nan, '', regex=True) # replacing nan with blank space
    display = display.style.apply(highlight_gray, axis=1)
    st.dataframe(display) # displaying the performance report in streamlit
    
    # Download link of performance excel report
    df = get_table_download_link(d) # Excel File
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(df, unsafe_allow_html=True)
    
    
    # ===================================================
    # Creating plots that will be placed in a downloadable pdf file(8 plots, sankey diagram not included)
    
    # Plot 1: Households per destination pie chart + table
    des = pd.DataFrame(d[d['Destination'] == 'Subtotal'].iloc[:,1])
    des['Destination Type'] = ['Permanent', 'Temporary', 'Institutional Setting', 'Other']
    
    colors = ['#ffc000', '#F0F0F0', '#838588', '#CECFD1']

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        specs=[[{"type": "pie"}],
               [{"type": "table"}]])
    fig.add_trace(
        go.Pie(labels=des['Destination Type'],
               values=des['Total']), 
               row=1, col=1)
    fig.add_trace(
        go.Table(header=dict(values=['Destination', 'Household Count']),
             cells=dict(values=[des['Destination Type'],des['Total']],align='center')), 
                 row=2, col=1)
    fig.update_traces(hoverinfo='label+percent',
                      marker=dict(colors=colors),row=1, col=1)
    fig.update_layout(
        height=800,
        width=800,
        showlegend=True,
        title_text="Household Destinations",
        plot_bgcolor='white',
        legend=dict(
                orientation="h",
                yanchor="top",
                y= .525,
                xanchor="center",
                x=.5
            )
    )
    
    
    # ===================================================
    # Plot 2: Creating household count horizontal bar chart  
    p = pd.DataFrame(d[d['Destination']=='Total'].iloc[:, 2:].transpose()).reset_index()
    p.columns = ["Household Type", "Count"]
    
    fig2 = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        specs=[[{"type": "scatter"}],
               [{"type": "table"}]] )
    fig2.add_trace(
        go.Bar(
            x = p["Count"],
            y = p["Household Type"],
            orientation = 'h',
            marker = dict(color= '#4472c4')),
                   row=1, col=1)
    fig2.add_trace(
        go.Table(header=dict(values=['Household Type', 'Household Count']),
        cells=dict(values=[p["Household Type"],p["Count"]])),
        row=2, col=1
    )
    fig2.update_layout(
        height=800,
        showlegend=False,
        title_text="Number of Households per Household Type",
        plot_bgcolor='white'
    )
    fig2.update_xaxes(showline=True, linewidth=0.5, linecolor='lightgray')
    fig2.update_yaxes(showline=True, linewidth=0.5, linecolor='lightgray')
    
    # ===================================================
    # Plot 3: Creating an age range vertical bar chart
    NumberofClients = []
    NumberofClients.append(len(clean[clean["Age"]<5]))
    NumberofClients.append(len( clean[ (clean["Age"]>=5) & (clean["Age"]<13) ]))
    NumberofClients.append(len( clean[ (clean["Age"]>=13) & (clean["Age"]<18) ]))  
    NumberofClients.append(len( clean[ (clean["Age"]>=18) & (clean["Age"]<25) ]))
    NumberofClients.append(len( clean[ (clean["Age"]>=25) & (clean["Age"]<35) ]))
    NumberofClients.append(len( clean[ (clean["Age"]>=35) & (clean["Age"]<45) ]))
    NumberofClients.append(len( clean[ (clean["Age"]>=45) & (clean["Age"]<55) ]))
    NumberofClients.append(len( clean[ (clean["Age"]>=55) & (clean["Age"]<62) ])) 
    NumberofClients.append(len(clean[clean["Age"]>=62]))
    NumberofClients.append(len(clean[clean["Age"]==None]))
    
    AgeRange = ['Under 5','5-12','13-17','18-24','25-34','35-44','45-54','55-62','62+','No Answer']
    
    fig3 = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        specs=[[{"type": "scatter"}],
               [{"type": "table"}]] )
    fig3.add_trace(
        go.Bar(
            x = AgeRange,
            y = NumberofClients,
            marker = dict(color= '#ffc000')),
                   row=1, col=1)
    fig3.add_trace(
        go.Table(header=dict(values=['Age Range', 'Client Count']),
             cells=dict(values=[AgeRange,NumberofClients])),
        row=2, col=1
    )
    fig3.update_layout(
        height=800,
        showlegend=False,
        title_text="Number of Households per Household Type",
        plot_bgcolor='white'
    )

    
    # ===================================================
    # Plot 4: Creating the gender demographic pie chart
    gender = list(clean['Gender'].unique())
    value=[list(clean['Gender']).count(i) for i in gender]
    des = pd.DataFrame ({'Gender':gender,'value':value})
    
    colors = ['#ffc000', '#4472c4', '#d55e00', '#cc79a7', '#e69f00', '#56b4e9','#009e73', '#f0e442']
 
    fig4 = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        specs=[[{"type": "pie"}],
               [{"type": "table"}]])
    fig4.add_trace(
        go.Pie(labels=gender,
               values=value), 
               row=1, col=1)
    fig4.add_trace(
        go.Table(header=dict(values=['Gender', 'Client Count']),
             cells=dict(values=[gender,value],align='center')), 
                 row=2, col=1)
    fig4.update_traces(hoverinfo='label+percent',
                      marker=dict(colors=colors),row=1, col=1)
    fig4.update_layout(
        height=800,
        width = 800,
        showlegend=True,
        title_text="Gender Demographics",
        plot_bgcolor='white',
        legend=dict(
                orientation="h",
                yanchor="top",
                y= .515,
                xanchor="center",
                x=.5
            )
    )
    
    # ===================================================
    # Plot 5: Creating the race demographic pie chart
    race = list(clean['Race'].unique())
    value=[list(clean['Race']).count(i) for i in race]
    des = pd.DataFrame ({'Race':race,'value':value})

    fig5 = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        specs=[[{"type": "pie"}],
               [{"type": "table"}]])
    fig5.add_trace(
        go.Pie(labels=race,
               values=value), 
               row=1, col=1)
    fig5.add_trace(
        go.Table(header=dict(values=['Race', 'Client Count']),
             cells=dict(values=[race,value],align='center')), 
                 row=2, col=1)
    fig5.update_traces(hoverinfo='label+percent',
                      marker=dict(colors=colors),row=1, col=1)
    fig5.update_layout(
        height=800,
        width = 800,
        showlegend=True,
        title_text="Race Demographics",
        plot_bgcolor='white',
# =============================================================================
#         legend=dict(
#                 orientation="h",
#                 yanchor="top",
#                 y= .525,
#                 xanchor="center",
#                 x=.5
#             )
# =============================================================================
    )
    
    # ===================================================
    # Plot 6: Creating a the ethnicity demographic pie chart
    ethnicity = list(clean['Ethnicity'].unique())
    value=[list(clean['Ethnicity']).count(i) for i in ethnicity]
    des = pd.DataFrame ({'Ethnicity':ethnicity,'value':value})

    fig6 = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        specs=[[{"type": "pie"}],
               [{"type": "table"}]])
    fig6.add_trace(
        go.Pie(labels=ethnicity,
               values=value), 
               row=1, col=1)
    fig6.add_trace(
        go.Table(header=dict(values=['Ethnicity', 'Client Count']),
             cells=dict(values=[ethnicity,value],align='center')), 
                 row=2, col=1)
    fig6.update_traces(hoverinfo='label+percent',
                      marker=dict(colors=colors),row=1, col=1)
    fig6.update_layout(
        height=800,
        width = 800,
        showlegend=True,
        title_text="Ethnicity Demographics",
        plot_bgcolor='white',
        legend=dict(
                orientation="h",
                yanchor="top",
                y= .525,
                xanchor="center",
                x=.5
            )
    )
    
    
   # =================================================== 
    # Plot 7: Creating a line chart of individuals with Move-In date by calling our line_plot function we created above
    fig7 = line_plots(clean)[0]
    
    # ===================================================
    # Plot 8: Creating a line chart households with Move-In date by calling our line_plot function we created above
    fig8 = line_plots(clean)[1]
    
    # ===================================================
    # Taking all the visuals and placing them into a downloadable pdf file link
    
    # Creating a list that contains all the figures (8 figures, excluding the sankey diagram)
    figs = [fig, fig2, fig3, fig4, fig5, fig6, fig7, fig8]

    # This for loop creates a new pdf page and places one chart per pdf page
    pdf = FPDF()
    for i in figs:
        pdf.add_page() # creates a new pdf page each iteration
        
        # Creation of a temporary file that will hold the charts (in memory until the download button is clicked)
        with NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                i.write_image(tmpfile.name)               # writes the chart as a png file type
                pdf.image(tmpfile.name, 10, 10, 175, 180) # Adjusts the chart size on the pdf

    # Creating a download link for the temporary file that is holding the 8 charts
    html = create_pdf_download_link(pdf.output(dest="S").encode("latin-1"))
    
    #Creating a download link of the charts report pdf that will be visible on streamlit app
    st.markdown(html, unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    

    # ===================================================
    # Streamlit Plot 1: Households per destination pie chart
    st.plotly_chart(fig)
    st.markdown("<hr>", unsafe_allow_html=True)

    # ===================================================
    # Streamlit Plot 2: Household Counts horizontal bar chart
    st.plotly_chart(fig2)
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # ===================================================
    # Streamlit Plot 3: Age range vertical bar chart
    st.plotly_chart(fig3)
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # ===================================================
    # Streamlit Plot 4: Demographics pie charts with dropdown menu
    option_pie = st.selectbox('Please select a demographic variable you would like to observe.',
    ('Gender', 'Race','Ethnicity'))
    
    # Waits for user selection for either Gender, Race, or Ethnicity selection
    if option_pie == "Gender":
        st.plotly_chart(fig4)
        st.markdown("<hr>", unsafe_allow_html=True)  
    elif option_pie == "Race":
        st.plotly_chart(fig5)
        st.markdown("<hr>", unsafe_allow_html=True)
    elif option_pie == "Ethnicity":
        st.plotly_chart(fig6)
        st.markdown("<hr>", unsafe_allow_html=True)
    
    # ===================================================
    # Streamlit Plot 5: Move-In Date Counts line plots with dropdown menu
    option = st.selectbox('Would you like to observe the number of move-in dates by individuals or by households?',
    ('Individuals', 'Households'))
    
    # Waits for user selection for either Individuals or Households selection
    if option == "Individuals":
        st.plotly_chart(fig7)
        st.markdown("<hr>", unsafe_allow_html=True)
    else:
        st.plotly_chart(fig8)
        st.markdown("<hr>", unsafe_allow_html=True)
    
    
    # ===================================================
    # Streamlit Plot 6: Sankey diagram

    # Produces a multiselection dropdown menu
    var_selected = st.multiselect("Select at least two features to produce a sankey diagram. The order of selection matters.",
                       ['Race','Destination Type', 'Destination', 'Ethnicity', 'Gender'],
                       default=['Race','Destination Type','Destination'])
    st.write("You have selected", len(var_selected), "features.")

    # Returns an error message if 1 or less attributes are selected
    # Otherwise it calls our sankey diagram function we made above and produces the sankey diagram using the user's selected attributes
    if len(var_selected) <= 1:
        st.error("Error: Please select at least TWO variables in order to produce a sankey diagram.")
    else:
        st.plotly_chart(SankeyDiagram(var_selected))
    
    st.markdown("<hr>", unsafe_allow_html=True)








