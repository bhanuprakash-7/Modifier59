from pywebio.platform.flask import webio_view
from pywebio import STATIC_PATH
from flask import Flask, send_from_directory
from pywebio.input import *
from pywebio.output import *
import pandas as pd
import numpy as np
import os
import time
import gc
import zipfile

app = Flask(__name__)

def process():
    files = os.listdir('.')
    files = list(filter(lambda x: '.zip' in x,files))
    put_text('Are these the zipiles\n',files)
    time.sleep(0.5)
    check = radio(options=['Yes','No'],required=True)
    if(check=='Yes'):
        for i in files:
            with zipfile.ZipFile(i,'r') as zip_ref:
                zip_ref.extractall('temp/')
    files = os.listdir('temp/')
    files = list(filter(lambda x: '.xlsx' in x,files))
    put_text('Extracted',files)
    data_list = []
    for i in files:
        put_text(i)
        
        df = pd.read_excel('temp/'+i)
        df = df[['CPT only copyright 2021 American Medical Association.  All rights reserved.','Unnamed: 1','Unnamed: 5']]
        df.columns = ['Column1','Column2','Modifier']
        df = df[5:]
        data_list.append(df)
        put_text('\t',len(df),'\n')
        del df
        gc.collect()
    df = pd.concat(data_list,ignore_index=True)
    df = df.drop_duplicates(['Column1','Column2'])
    
    put_text('final\t',len(df))
    
    path1= input('Enter payments file name')
    af = pd.read_csv(path1)
    put_text(path1)
    kf = af.groupby('Bill',as_index=False).agg({'CPT code':'count'})
    kf = kf[kf['CPT code']>1]
    kf.columns = ['Bill','count']
    kf = kf['Bill'].unique()
    sf = af[af['Bill'].isin(kf)].groupby(['Bill'])['CPT code'].apply(lambda x: list(np.unique(x)))
    sf = pd.DataFrame(sf).reset_index()
    temp_list = []
    def fun(x):
        a = x[1]
        k = x[0]
        b = []
        temp = pd.DataFrame()
        for i in a:
            for j in a:
                if j == i:
                    continue
                b.append(i+j)
        temp['Bill'] = [k]*len(b)
        temp['total'] = b
        temp_list.append(temp)
    for i in range(len(sf)):
        fun(sf.loc[i].values)
    lf = pd.concat(temp_list,ignore_index = True)
    df['total'] = df[['Column1','Column2']].apply(lambda x : x[0]+x[1],axis = 1)
    zf = pd.merge(lf,df,on='total')[['Bill','total','Modifier']].drop_duplicates()
    zf = zf[zf['Modifier']=='1']
    zf['CPT code'] = zf['total'].apply(lambda x : x[:5])
    zf['FeedBack'] = '59'
    zf = zf.drop_duplicates(['Bill','CPT code'])
    final = pd.merge(af,zf[['Bill','FeedBack','CPT code']],on = ['Bill','CPT code'],how = 'left')
    final.loc[(final['FeedBack']=='59')&(final['Mod1']=='59'),'FeedBack'] = ''
    final.loc[(final['FeedBack']=='59')&(final['Mod1']!='59'),'FeedBack'] = 'missed 59'
    final.loc[(final['FeedBack']!='59')&(final['Mod1']=='59'),'FeedBack'] = 'inappropriate'
    final['FeedBack'] = final['FeedBack'].fillna('')
    final.to_excel('final.xlsx',index=False)
    put_text('Done')
    
app.add_url_rule('/tool','webio_view',webio_view(process),
                 methods=['GET','POST','OPTIONS'])

app.run(debug=False,host='0.0.0.0')
