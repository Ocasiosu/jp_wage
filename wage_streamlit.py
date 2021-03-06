import pandas as pd
import streamlit as st
import pydeck as pdk
import plotly.express as px

st.title('RESAS（地域経済分析システム）から入手した日本の賃金オープンデータをさまざまなグラフで可視化')

df_jp_ind = pd.read_csv('./雇用_医療福祉_一人当たり賃金_全国_全産業.csv',encoding='shift_jis')
df_jp_category = pd.read_csv('./雇用_医療福祉_一人当たり賃金_全国_大分類.csv',encoding='shift_jis')
df_pref_ind = pd.read_csv('./雇用_医療福祉_一人当たり賃金_都道府県_全産業.csv',encoding='shift_jis')

st.header('■2019年：1人あたり平均賃金のヒートマップ')
"""
2019年において、マップ上で赤く光っている場所ほど、平均賃金が高い  
東京・大阪などの大都市圏の周辺地域で賃金が高いことがわかる
"""

jp_lat_lon = pd.read_csv('./pref_lat_lon.csv')
jp_lat_lon = jp_lat_lon.rename(columns={'pref_name':'都道府県名'})

df_pref_map = df_pref_ind[(df_pref_ind['年齢']=='年齢計')&(df_pref_ind['集計年']==2019)]
df_pref_map = pd.merge(df_pref_map,jp_lat_lon,on = '都道府県名')
#最大値1、最小値0とする正規化処理
df_pref_map['一人当たり賃金（相対値）']=((df_pref_map['一人当たり賃金（万円）']-df_pref_map['一人当たり賃金（万円）'].min())/(df_pref_map['一人当たり賃金（万円）'].max()-df_pref_map['一人当たり賃金（万円）'].min()))


view = pdk.ViewState(
    #中心は東京の県庁所在地の緯度経度
    longitude=139.691648,
    latitude=35.689185,
    zoom=4,
    pitch=40.5,
)

layer = pdk.Layer(
    "HeatmapLayer",
    data=df_pref_map,
    opacity=0.4,#透明度
    get_position=["lon","lat"],
    threshold=0.3,#しきい値
    get_weight = '一人当たり賃金（相対値）'
)
layer_map = pdk.Deck(
    layers = layer,
    initial_view_state=view,
)
st.pydeck_chart(layer_map)#ヒートマップの描画

show_df =st.checkbox('Show DataFrame')
if show_df == True:
    st.write(df_pref_map)


st.header('■集計年別の一人当たり賃金（万円）の推移')

df_ts_mean = df_jp_ind[(df_jp_ind["年齢"]=="年齢計")]
df_ts_mean = df_ts_mean.rename(columns={'一人当たり賃金（万円）':'全国_一人当たり賃金（万円）'})
"""
全国_一人当たり賃金（万円）は2010年から2019年にかけて上昇傾向にある  
「年齢計」とは、全年齢で平均をとった値
"""
df_ts_show = df_ts_mean.set_index('集計年')
df_ts_show #集計年別の全国_一人当たり賃金

df_pref_mean = df_pref_ind[(df_pref_ind["年齢"]=="年齢計")]

st.header('■都道府県別の一人当たり賃金（万円）の推移ラインチャート')
pref_list = df_pref_mean['都道府県名'].unique()
option_pref = st.selectbox( #セレクトボックス
    '都道府県を選択して、全国平均賃金との差を確認できる',
    (pref_list))
df_pref_mean = df_pref_mean[df_pref_mean['都道府県名']==option_pref]

df_mean_line = pd.merge(df_ts_mean,df_pref_mean,on='集計年')
df_mean_line = df_mean_line[['集計年','全国_一人当たり賃金（万円）','一人当たり賃金（万円）']]
df_mean_line = df_mean_line.set_index('集計年')
st.line_chart(df_mean_line)#ラインチャート描画


st.header('■年齢階級別の全国一人当たり平均賃金（万円）バブルチャート')
df_mean_bubble = df_jp_ind[df_jp_ind['年齢'] != '年齢計']
#X軸に一人あたり賃金
#Y軸は年間賞与
#バブルサイズは所定内給与額

fig = px.scatter(df_mean_bubble, #バブルチャートを
                x="一人当たり賃金（万円）",
                y="年間賞与その他特別給与額（万円）",
                range_x=[150,700],#軸の範囲
                range_y=[0,150],#軸の範囲
                size="所定内給与額（万円）",
                size_max=38,#バブルサイズの最大値38万円
                color="年齢",
                animation_frame="集計年",
                animation_group="年齢"
)
"""
一人あたり賃金が高くなるにつれて、年間賞与も高くなる傾向にある  
年齢が19歳未満の世代と60歳以上の世代はグラフの左下で賃金も年間賞与も低い  
働き盛りの30,40,50代はグラフの右上で賃金も年間賞与も高い傾向にある  
バブルサイズもグラフの左下から右上に行くほど大きな円になっている  
2010から2019の9年間で多くの世代で多少、賃金が増えているが大きな変化は見られない  
バブルサイズも9年間でほとんど変化していないため、所定内給与額はほとんど変化していない  
"""
st.plotly_chart(fig)#バブルチャートをstreamlitで呼び出す



st.header('■産業別の賃金推移横棒グラフ')

year_list = df_jp_category["集計年"].unique()#集計年をリスト化
option_year = st.selectbox(
    '集計年',
    (year_list)
)

wage_list = ['一人当たり賃金（万円）','所定内給与額（万円）','年間賞与その他特別給与額（万円）']
option_wage = st.selectbox(
    '賃金の種類',
    (wage_list)
)

df_mean_categ = df_jp_category[(df_jp_category['集計年']== option_year)]

max_x = df_mean_categ[option_wage].max()+50

fig = px.bar(df_mean_categ,
            x=option_wage,
            y='産業大分類名',
            color='産業大分類名',
            animation_frame='年齢',
            range_x=[0,max_x],
            orientation='h',
            width=800,
            height=500
)
st.plotly_chart(fig)

"""
出典：RESAS（地域経済分析システム）  
本結果はRESAS（地域経済分析システム）を加工して作成しました
"""