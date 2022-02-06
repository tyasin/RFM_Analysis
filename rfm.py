# Customer Segmentation using RFM

import datetime as dt

import matplotlib.colors
import matplotlib.pyplot as plt
import pandas as pd
import squarify


def outlier_thresholds(dataframe, variable):
    quartile1 = dataframe[variable].quantile(0.01)
    quartile3 = dataframe[variable].quantile(0.99)
    interquantile_range = quartile3 - quartile1
    up_limit = quartile3 + 1.5 * interquantile_range
    low_limit = quartile1 - 1.5 * interquantile_range
    return low_limit, up_limit


def replace_with_thresholds(dataframe, variable):
    low_limit, up_limit = outlier_thresholds(dataframe, variable)
    dataframe.loc[(dataframe[variable] < low_limit), variable] = low_limit
    dataframe.loc[(dataframe[variable] > up_limit), variable] = up_limit


pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.float_format', lambda x: '%.5f' % x)

##################################  GÖREV 1  ##################################
# VERİYİ ANLAMA VE HAZIRLAMA
# --------------------------
# 1. Online Retail II excelindeki 2010-2011 verisini okuyunuz. Oluşturduğunuz
# dataframe’in kopyasını oluşturunuz.
# 2. Veri setinin betimsel istatistiklerini inceleyiniz.
# 3. Veri setinde eksik gözlem var mı? Varsa hangi değişkende kaç tane eksik
# gözlem vardır?
# 4. Eksik gözlemleri veri setinden çıkartınız. Çıkarma işleminde ‘inplace=True’
# parametresini kullanınız.
# 5. Eşsiz ürün sayısı kaçtır?
# 6. Hangi üründen kaçar tane vardır?
# 7. En çok sipariş edilen 5 ürünü çoktan aza doğru sıralayınız.
# 8. Faturalardaki ‘C’ iptal edilen işlemleri göstermektedir. İptal edilen
# işlemleri veri setinden çıkartınız.
# 9. Fatura başına elde edilen toplam kazancı ifade eden ‘TotalPrice’ adında
# bir değişken oluşturunuz.


# 1
df_ = pd.read_excel('online_retail_II.xlsx', sheet_name='Year 2010-2011')
df = df_.copy()

# 2
df.shape
df.head()
df.info()
df.describe().T

# 3
df.isnull().sum()

# 4
df.dropna(inplace=True)

# 5
df.Description.nunique()
df.Description.unique()

# 6
df.Description.value_counts().head()

# 7
df.groupby('Description').Quantity.sum().sort_values(ascending=False).head()

# 8
returns = df[df.Invoice.str.contains('C', na=False)].index
df.drop(returns, axis=0, inplace=True)
df.shape

df = df[(df['Quantity'] > 0)]
df = df[(df['Price'] > 0)]
replace_with_thresholds(df, 'Price')
replace_with_thresholds(df, 'Quantity')
df.shape

# 9
df['TotalPrice'] = df.Quantity * df.Price
df['Customer ID'] = df['Customer ID'].astype('int64')
df.head()

##################################  GÖREV 2  ##################################
# RFM METRİKLERİNİN HESAPLANMASI
# ------------------------------
# Recency, Frequency ve Monetary tanımlarını yapınız.
# ▪ Müşteri özelinde Recency, Frequency ve Monetary metriklerini groupby, agg ve lambda ile
# hesaplayınız.
# ▪ Hesapladığınız metrikleri rfm isimli bir değişkene atayınız.
# ▪ Oluşturduğunuz metriklerin isimlerini recency, frequency ve monetary olarak değiştiriniz.

# Not 1: recency değeri için bugünün tarihini (2011, 12, 11) olarak kabul ediniz.
# Not 2: rfm dataframe’ini oluşturduktan sonra veri setini "monetary>0" olacak şekilde filtreleyiniz.


# Recency: Müşterilerin en son ne zaman alışveriş yaptığının gün cinsinden değeri.
# Frequency: Müşterilerin kaç kez alışveriş yaptığının değeri.
# Monetary: Müşterilerin yaptıkları tüm alışverişlerinden bıraktıkları toplam miktar.

today = dt.datetime(2011, 12, 11)
rfm = df.groupby('Customer ID').agg(
    {'InvoiceDate': lambda InvoiceDate: (today - InvoiceDate.max()).days,
     'Invoice': lambda Invoice: Invoice.nunique(),
     'TotalPrice': lambda TotalPrice: TotalPrice.sum()})

rfm.columns = ['recency', 'frequency', 'monetary']
rfm = rfm[rfm.monetary > 0]
rfm.head()

##################################  GÖREV 3  ##################################
# RFM SKORLARININ OLUŞTURULMASI VE TEK BİR DEĞİŞKENE ÇEVRİLMESİ
# -------------------------------------------------------------
# ▪ Recency, Frequency ve Monetary metriklerini qcut yardımı ile 1-5 arasında skorlara çeviriniz.
# ▪ Bu skorları recency_score, frequency_score ve monetary_score olarak kaydediniz.
# ▪ Oluşan 2 farklı değişkenin değerini tek bir değişken olarak ifade ediniz ve RFM_SCORE olarak kaydediniz.

rfm['recency_score'] = pd.qcut(rfm.recency, 5, labels=[5, 4, 3, 2, 1])
rfm['frequency_score'] = pd.qcut(rfm.frequency.rank(method='first'), 5,
                                 labels=[1, 2, 3, 4, 5])
rfm['monetary_score'] = pd.qcut(rfm.monetary, 5, labels=[1, 2, 3, 4, 5])

rfm['RFM_SCORE'] = rfm.recency_score.astype(str) + rfm.frequency_score.astype(
    str)
rfm.head()

##################################  GÖREV 4  #################################
# RFM SKORLARININ SEGMENT OLARAK TANIMLANMASI
# -------------------------------------------
# ▪ Oluşturulan RFM skorların daha açıklanabilir olması için segment tanımlamaları
# yapınız.
# ▪ Aşağıdaki seg_map yardımı ile skorları segmentlere çeviriniz.

seg_map = {r'[1-2][1-2]': 'hibernating',
           r'[1-2][3-4]': 'at_Risk',
           r'[1-2]5': 'cant_loose',
           r'3[1-2]': 'about_to_sleep',
           r'33': 'need_attention',
           r'[3-4][4-5]': 'loyal_customers',
           r'41': 'promising',
           r'51': 'new',
           r'[4-5][2-3]': 'potential_loyalists',
           r'5[4-5]': 'champions'}

rfm['segment'] = rfm['RFM_SCORE'].replace(seg_map, regex=True)
rfm.reset_index(inplace=True)
rfm.head()

##################################  GÖREV 5  ##################################
# ▪ Önemli bulduğunuz 3 segmenti seçiniz. Bu üç segmenti:
#    - Hem aksiyon kararları açısından,
#    - Hem de segmentlerin yapısı açısından (ortalama RFM değerleri)
#      yorumlayınız.
# ▪ "Loyal Customers" sınıfına ait customer ID'leri seçerek excel çıktısını alınız.

get_segment = lambda segment_: rfm[rfm.segment == segment_]

champ = get_segment('champions')
loyal = get_segment('loyal_customers')
potential = get_segment('potential_loyalists')

##############################################################################

champ[['recency', 'frequency', 'monetary']].describe().T
# r = 6 , f = 12, m = 6498
# Yakın zamanda alışveriş yapmış, sık sık, alışveriş yapanlar.

# 1. Champions (55, 54)
# ---------------------
# ▪ Loyalty programları düzenle.
# ▪ Limited Edition ürünler tanıt.
# ▪ Özel indirimler yap.
# ▪ Bu kullanıcıların öneri sistemlerini özel ayarla.
# ▪ Bu segmentten gelen geri dönüşlere dikkat et.


##############################################################################

loyal[['recency', 'frequency', 'monetary']].describe().T
# r = 33 , f = 6, m = 2752
# Yakın zaman olmasa da sık sık alışveriş yapanlar.

# 2. Loyals (34, 35, 44, 45)
# --------------------------
# ▪ Loyalty programları düzenle.
# ▪ Ücretsiz kargo vb. imkanlar sağla.
# ▪ İlgilendiklerini düşündüğün alanlar dışında önerilerde bulunma.


##############################################################################

potential[['recency', 'frequency', 'monetary']].describe().T
# r = 17 , f = 2, m = 674
# Servisi/hizmeti/ürünü birden fazla kez kullanmaya başlamış, düzenli kullanma
# potansiyeli olan yeni kullanıcılar.

# 3. Potential Loyals (42, 43, 52, 53)
# -------------------
# ▪ Cross-selling ya da up-selling dene.
# ▪ Membership, Loyalty programlarına dahil etmeye çalış.


##############################################################################

# EXCEL EXPORT
loyals = rfm[rfm.segment == 'loyal_customers']
loyals.to_excel('loyals.xlsx')

################################# EKSTRA ######################################

# 2D Görselleştirme (Segmentlerin 2 boyutta dağılımını gözlemlemek için)
sq1 = rfm.groupby('segment')['Customer ID'].nunique().sort_values(
    ascending=False).reset_index()
cmap = plt.cm.coolwarm
mini = min(sq1['Customer ID'])
maxi = max(sq1['Customer ID'])
norm = matplotlib.colors.Normalize(vmin=mini, vmax=maxi)
colors = [cmap(norm(value)) for value in sq1['Customer ID']]
fig = plt.gcf()
ax = fig.add_subplot()
fig.set_size_inches(14, 10)
squarify.plot(sizes=sq1['Customer ID'],
              label=sq1.segment,
              alpha=1,
              color=colors)
plt.axis('off')
plt.show()

##############################################################################

# 3D Görselleştirme
import plotly.express as px

data = rfm[['Customer ID', 'recency', 'frequency', 'monetary', 'segment']]
fig = px.scatter_3d(data, x='recency', y='frequency', z='monetary',
                    hover_data=['Customer ID'], color='segment', opacity=0.5)
fig.update_layout(scene_zaxis_type="log")
fig.show()
