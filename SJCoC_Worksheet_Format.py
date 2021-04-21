import numpy as np
import xlsxwriter
import pandas as pd

def  writeToWorksheet(wr,df,name):
    def colnum_string(n):
        string = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            string = chr(65 + remainder) + string
        return string
    
    def write_manual_titles_to_wks(wkb,wks):
        # get date and time the code was run
        import datetime
        x = datetime.datetime.now()
        # remove library from ram
        del datetime 
        # fill in black cells that mimic lines above and below Anual Performance Report
        fmt_black_line = wkb.add_format({'bg_color':'black'})
        row_list = [2,10]
        for row_itr in row_list:
            for col_itr in range(1, 12):
                cell_reference = colnum_string(col_itr) + str(row_itr)
                wks.write(cell_reference,'',fmt_black_line)
        del fmt_black_line, row_itr, col_itr, row_list,cell_reference
        # write and format "HUD FUCJ Annual Performance Report (FY YYYY)" title
        fmt_merge_title = wkb.add_format({'align': 'center','font_name': 'Arial','font_size': 16,'valign': 'vcenter','text_wrap': 1,'right': 1})
        wks.merge_range('A4:C8', f"HUD FUCJ Annual Performance Report (FY {x.year})", fmt_merge_title)
        del fmt_merge_title
        # write and format the title for CA-511: Central Valley Housing
        fmt_merge_sub1 = wkb.add_format({'font_name': 'Arial','font_size': 14,'text_wrap': 1,'bold': 1,'valign': 'vcenter','align': 'right'})
        wks.merge_range('D4:K4', "CA-511: Central Valley Housing", fmt_merge_sub1)
        del fmt_merge_sub1
        # write and format the titles beneath the top header Central Valley Housing
        fmt_merge_sub = wkb.add_format({'font_name': 'Arial','font_size': 12,'text_wrap': 1,'valign': 'vcenter','align': 'right'})
        wks.merge_range('D5:K5', "", fmt_merge_sub)
        wks.merge_range('D6:K6', "Agency cat. filter: Agency CoC", fmt_merge_sub)
        wks.merge_range('D7:K7', "Client Location filter: No", fmt_merge_sub)
        wks.merge_range('D8:K8', "Funding Criteria: Not Based on Funding Source", fmt_merge_sub)
        del fmt_merge_sub
        # write and format the Q23c. Exit Destination title in blue
        fmt_merge_lower1 = wkb.add_format({'font_name': 'Arial','font_size': 11,'text_wrap': 1,'bold': 1,'valign': 'vcenter','align': 'left','top': 1,'right': 1,'left': 1,'bg_color': '#EDF3FE','border_color': '#999999'})
        wks.merge_range('A12:K12', "Q23c. Exit Destination", fmt_merge_lower1)
        del fmt_merge_lower1
        # write and format the Program Applicability: All Projects title in blue
        fmt_merge_lower2 = wkb.add_format({'font_name': 'Arial','font_size': 11,'text_wrap': 1,'valign': 'vcenter','align': 'left','left': 1,'right': 1,'bg_color': '#EDF3FE','border_color': "#999999"})
        wks.merge_range('A13:K13', "Program Applicability: All Projects", fmt_merge_lower2)
        del fmt_merge_lower2
        # write report date at the bottom of the worksheet in the example format: Wed Mar 24 09:45:11 PM 2021
        wks.write(63, 0,x.strftime("%a %b %d %I:%M:%S %p %Y"))
        
    def write_df_to_wks(wkb,wks,df,start_row):
        
        def write_df_row_to_wks(wks,df,spacer,idx_format,num_format,row_merge=False):
            write_cols = [0,1,2,5,7,9]
            if row_merge == False:
                for idx, row in df.iterrows():
                    zipped_vals = list(zip(write_cols,row))
                    row_number = idx + spacer
                    wks.write(row_number,zipped_vals[0][0],zipped_vals[0][1],idx_format)
                    for col, val in zipped_vals[1:]:
                        if col >= 2 :
                            merge_row_number = str(row_number + 1)
                            merge_starting_column = colnum_string(col+1)
                            if col == 2:
                                merge_ending_column =  colnum_string(col + 3)
                            else:
                                merge_ending_column = colnum_string(col + 2)
                            # outputs an excel range in the format A1:A5 for merging purposes 
                            string_range = merge_starting_column + merge_row_number + ":" + merge_ending_column + merge_row_number
                            # merges cells listed in string range, writes value, formats merged cells
                            wks.merge_range(string_range,val,num_format)                    
                        else:
                            # writes value directly to cell and formats
                            wks.write(row_number,col,val,num_format)
            else:
                for idx, row in df.iterrows():
                    val = row[0]
                    merge_starting_column = colnum_string(write_cols[0]+1)
                    merge_ending_column =  colnum_string(write_cols[-1]+2)
                    row_number = idx + spacer
                    merge_row_number = str(row_number + 1)
                    # outputs an excel range in the format A1:A5 for merging purposes
                    string_range = merge_starting_column + merge_row_number + ":" + merge_ending_column + merge_row_number
                    # merges cells listed in string range, writes value, formats merged cells
                    wks.merge_range(string_range,val,num_format)

        def write_df_to_wks_headers(wkb,wks,df,start_row):
            fmt_header = wkb.add_format({'font_name':'Arial','font_size':10,'align':'center','valign':'top','num_format': '@','border':1,'text_wrap': True,'bg_color':'#E9E9E8'})
            headers_list = df.columns.tolist()
            headers_list[0] = ''
            write_cols = [0,1,2,5,7,9]
            row_number = start_row-1
            for col, val in zip(write_cols,headers_list):
                if col >= 2 :
                    merge_row_number = str(row_number + 1)
                    merge_starting_column = colnum_string(col+1)
                    if col == 2:
                        merge_ending_column =  colnum_string(col + 3)
                    else:
                        merge_ending_column = colnum_string(col + 2)
                    # outputs an excel range in the format A1:A5 for merging purposes 
                    string_range = merge_starting_column + merge_row_number + ":" + merge_ending_column + merge_row_number
                    # merges cells listed in string range, writes value, formats merged cells
                    wks.merge_range(string_range,val,fmt_header)                    
                else:
                    # writes value directly to cell and formats
                    wks.write(row_number,col,val,fmt_header)

        def write_df_to_wks_section_headings(wkb,wks,df,rows,start_row):
            fmt_index_section = wkb.add_format({'font_name':'Arial','font_size':10,'align':'left','valign':'vcenter','num_format': '@','border':1,'bold':1,'text_wrap': True,'bg_color':'#E9E9E8'})
            write_df_row_to_wks(wks, df.iloc[rows], start_row, fmt_index_section, fmt_index_section,row_merge=True)

        def write_df_to_wks_sums(wkb,wks,df,rows,start_row):
            fmt_index_sums = wkb.add_format({'font_name':'Arial','font_size':10,'align':'left','valign':'vcenter','num_format': '@','border':1,'text_wrap': True})
            fmt_numbers_sums = wkb.add_format({'font_name':'Arial','font_size':10,'align':'center','valign':'vcenter','num_format': '0','border':1,'text_wrap': True})
            write_df_row_to_wks(wks, df.iloc[rows], start_row, fmt_index_sums, fmt_numbers_sums)

        def write_df_to_wks_subtotals(wkb,wks,df,rows,start_row):
            fmt_index_subtotal = wkb.add_format({'font_name':'Arial','font_size':10,'align':'left','valign':'vcenter','num_format': '@','border':1,'bold':1,'text_wrap': True})
            fmt_numbers_subtotal = wkb.add_format({'font_name':'Arial','font_size':10,'align':'center','valign':'vcenter','num_format': '0','border':1,'bold':1,'text_wrap': True})
            write_df_row_to_wks(wks, df.iloc[rows] , start_row, fmt_index_subtotal, fmt_numbers_subtotal)

        def write_df_to_wks_totals(wkb,wks,df,rows,start_row):

            def write_df_to_wks_totals_main(wkb,wks,df,rows,start_row):
                fmt_index_total_main = wkb.add_format({'font_name':'Arial','font_size':10,'align':'left','valign':'vcenter','num_format': '@','border':1,'bottom':1,'bottom_color':'#999999','text_wrap': True})
                frmt_numbers_total_main = wkb.add_format({'font_name':'Arial','font_size':10,'align':'center','valign':'vcenter','num_format': '0','border':1,'bottom':1,'bottom_color':'#999999','text_wrap': True})
                write_df_row_to_wks(wks, df.iloc[[rows]] , start_row, fmt_index_total_main, frmt_numbers_total_main)

            def write_df_to_wks_totals_addit(wkb,wks,df,rows,start_row):
                fmt_index_total_addit = wkb.add_format({'font_name':'Arial','font_size':10,'align':'left','valign':'vcenter','num_format': '@','border':1,'border_color':'#999999','text_wrap': True})
                frmt_numbers_total_addit = wkb.add_format({'font_name':'Arial','font_size':10,'align':'center','valign':'vcenter','num_format': '0','border':1,'border_color':'#999999','text_wrap': True})
                write_df_row_to_wks(wks, df.iloc[rows] , start_row, fmt_index_total_addit, frmt_numbers_total_addit)

            def write_df_to_wks_totals_percent(wkb,wks,df,rows,start_row):
                fmt_index_total_percent = wkb.add_format({'font_name':'Arial','font_size':10,'align':'left','valign':'vcenter','num_format': '@','border':1,'border_color':'#999999','text_wrap': True})
                fmt_numbers_total_percent = wkb.add_format({'font_name':'Arial','font_size':10,'align':'center','valign':'vcenter','num_format': '0.00%','border':1,'border_color':'#999999','text_wrap': True})
                write_df_row_to_wks(wks, df.iloc[[rows]] , start_row, fmt_index_total_percent, fmt_numbers_total_percent)

            write_df_to_wks_totals_main(wkb,wks,df,rows[0],start_row)
            write_df_to_wks_totals_addit(wkb,wks,df,rows[1:len(rows)-1],start_row)
            write_df_to_wks_totals_percent(wkb,wks,df,rows[-1],start_row)        
        
        #----------Write Headers to top of Worksheet------
        write_df_to_wks_headers(wkb,wks,df,start_row)
        #----------Write Section Separators to Worksheet------
        destination_sections = df[df['Total'].isna()].index.values
        write_df_to_wks_section_headings(wkb,wks,df,destination_sections,start_row)
        #----------Write Totals to Worksheet------
        destination_totals = list(range(int(df[df['Destination']=='Total'].index[0]),len(df.index)))
        write_df_to_wks_totals(wkb,wks,df,destination_totals,start_row)
        #----------Write Subtotals to Worksheet------
        destination_subtotals = df[df['Destination']=='Subtotal'].index.values
        write_df_to_wks_subtotals(wkb,wks,df,destination_subtotals,start_row)
        #----------Write Sums to Worksheet-------
        ignored_rows = np.append(destination_sections, [destination_subtotals, destination_totals])
        destination_sums = df.loc[~df.index.isin(ignored_rows)].index.values
        write_df_to_wks_sums(wkb,wks,df,destination_sums,start_row)
        
    def fmt_row_heights(wks):
        #~~~~~~~~~~Adjusting Row Heights~~~~~~~~~~
        row_heights = [4.5, 1.5, 4.5, 27, 19.5, 19.5, 19.5, 19.5, 6.75, 0.75, 19.5, 19.5, 19.5, 31.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 0, 19.5, 31.5]
        for r_no, r_height in enumerate(row_heights):
            wks.set_row(r_no, r_height)

    def fmt_col_widths(wks):
        #~~~~~~~~~~Adjusting Column Widths~~~~~~~~~~
        col_widths = [25.57, 15, 5.57, 3.43, 4.57, 12.4, 2.14, 9.71, 4.57, 11.71, 2.57]
        for col_no, c_width in enumerate(col_widths):
            wks.set_column(col_no, col_no, c_width)

    # create workbook and worksheet objects
    workbook = wr.book
    worksheet = workbook.add_worksheet(name)
    
    # write the dataframe to the worksheet starting at row 14
    write_df_to_wks(workbook, worksheet, df, start_row=14)
    
    # manually write in the values for the report title
    write_manual_titles_to_wks(workbook, worksheet)
    
    # format the heights of each row
    fmt_row_heights(worksheet)
    
    # format the widths of each column
    fmt_col_widths(worksheet)