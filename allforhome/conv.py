import pandas as pd
import openpyxl

df = pd.read_excel("C:\RPA\conv\conv.xlsx",sheet_name='conv')
for i in range(len(df.columns)):
    result = df['Unnamed: '+str(i)]
    result = result.dropna(axis=0)
    result.to_excel("C:\RPA\conv\conv_result"+str(i+1)+".xlsx",header=False,index=False)
