import argparse,random,json,joblib
import numpy as np,pandas as pd,tensorflow as tf
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score,accuracy_score,precision_score,recall_score,f1_score,confusion_matrix
from .config import DATA_RAW,MODELS,RESULTS,DEFAULT_CAPACITY
from .data_pipeline import load_data,contextualize,historical_stats,attach_history,targets,matrix,FEATURES

def seed(): random.seed(42);np.random.seed(42);tf.random.set_seed(42)
def ann(n):
 m=tf.keras.Sequential([tf.keras.layers.Input((n,)),tf.keras.layers.Dense(64,activation='relu'),tf.keras.layers.Dense(32,activation='relu'),tf.keras.layers.Dense(16,activation='relu'),tf.keras.layers.Dense(3)])
 m.compile(optimizer=tf.keras.optimizers.Adam(1e-3),loss='mse',metrics=[tf.keras.metrics.MeanAbsoluteError(name='mae')]);return m
def metrics(name,y,p,cap):
 a=(y[:,0]>=cap).astype(int);b=(p[:,0]>=cap).astype(int)
 return {'model':name,'MAE':mean_absolute_error(y,p),'RMSE':mean_squared_error(y,p)**.5,'R2':r2_score(y,p,multioutput='uniform_average'),'Accuracy':accuracy_score(a,b),'Precision':precision_score(a,b,zero_division=0),'Recall':recall_score(a,b,zero_division=0),'F1':f1_score(a,b,zero_division=0)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--input',default=str(DATA_RAW/'ac_transit_apc.csv'));ap.add_argument('--capacity',type=int,default=DEFAULT_CAPACITY);args=ap.parse_args();seed()
 df=load_data(args.input)
 if 'service_date' not in df: df['service_date']=df.event_timestamp.dt.date.astype(str)
 df=contextualize(df);df=df.sort_values('event_timestamp').reset_index(drop=True)
 n=len(df);a=int(n*.70);b=int(n*.85);rawtr,rawv,rawt=df.iloc[:a],df.iloc[a:b],df.iloc[b:]
 stats=historical_stats(rawtr)
 tr=targets(attach_history(rawtr,stats)).dropna(subset=['target_1','target_2','target_3']);va=targets(attach_history(rawv,stats)).dropna(subset=['target_1','target_2','target_3']);te=targets(attach_history(rawt,stats)).dropna(subset=['target_1','target_2','target_3'])
 Xtr,Xv,Xt=matrix(tr),matrix(va),matrix(te);ytr=tr[['target_1','target_2','target_3']].to_numpy(float);yv=va[['target_1','target_2','target_3']].to_numpy(float);yt=te[['target_1','target_2','target_3']].to_numpy(float)
 sc=StandardScaler().fit(Xtr);Xtr,Xv,Xt=sc.transform(Xtr),sc.transform(Xv),sc.transform(Xt)
 rows=[];pers=np.repeat(te.current_load.to_numpy()[:,None],3,axis=1);rows.append(metrics('Persistence',yt,pers,args.capacity));lr=LinearRegression().fit(Xtr,ytr);rows.append(metrics('Linear Regression',yt,lr.predict(Xt),args.capacity))
 model=ann(Xtr.shape[1]);model.fit(Xtr,ytr,validation_data=(Xv,yv),epochs=150,batch_size=256,callbacks=[tf.keras.callbacks.EarlyStopping(monitor='val_loss',patience=10,restore_best_weights=True)],verbose=1);pred=model.predict(Xt,verbose=0);rows.append(metrics('ANN',yt,pred,args.capacity))
 MODELS.mkdir(exist_ok=True);RESULTS.mkdir(exist_ok=True);model.save(MODELS/'ann_model.keras');joblib.dump(sc,MODELS/'scaler.joblib');(MODELS/'historical_stats.json').write_text(json.dumps(stats,indent=2,default=str));(MODELS/'feature_config.json').write_text(json.dumps({'features':FEATURES,'horizons':[1,2,3],'capacity':args.capacity,'thresholds':{'warning':.80,'critical':1.0},'split':{'train':.70,'validation':.15,'test':.15}},indent=2))
 pd.DataFrame(rows).to_csv(RESULTS/'comparison.csv',index=False);cm=confusion_matrix((yt[:,0]>=args.capacity).astype(int),(pred[:,0]>=args.capacity).astype(int),labels=[0,1]);pd.DataFrame(cm,index=['actual_safe','actual_overload'],columns=['pred_safe','pred_overload']).to_csv(RESULTS/'confusion_matrix.csv',index=True)
 out=te[['route_id','stop_id','event_timestamp','passenger_load']].copy()
 for i,h in enumerate([1,2,3]):out[f'actual_{h}']=yt[:,i];out[f'ann_pred_{h}']=pred[:,i]
 out.to_csv(RESULTS/'predictions.csv',index=False)
 print(pd.DataFrame(rows).to_string(index=False));print('Training complete.')
if __name__=='__main__':main()
