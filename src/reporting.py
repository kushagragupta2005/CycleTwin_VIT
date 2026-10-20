"""Synthetic reporting diagnostics. Nothing fitted here feeds deployed inference."""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score


def reliability(y, p, bins=10):
    y,p=np.asarray(y),np.asarray(p)
    index=np.minimum((np.clip(p,0,1)*bins).astype(int),bins-1)
    rows=[]
    for i in range(bins):
        mask=index==i; n=int(mask.sum())
        rows.append({'lower':i/bins,'upper':(i+1)/bins,'n':n,'positive':int(y[mask].sum()),
                     'mean_probability':float(p[mask].mean()) if n else None,
                     'event_fraction':float(y[mask].mean()) if n else None})
    ece=sum(r['n']*abs(r['mean_probability']-r['event_fraction']) for r in rows if r['n'])/max(len(y),1)
    return rows,float(ece)


def calibration_diagnostic(y,p):
    if len(np.unique(y))<2:
        return {'intercept':None,'slope':None,'reason':'Only one outcome class in subset'}
    p=np.clip(p,1e-6,1-1e-6)
    logits=np.log(p/(1-p)).reshape(-1,1)
    if np.ptp(logits)<1e-12:
        return {'intercept':float(np.log(np.mean(y)/(1-np.mean(y)))), 'slope':None,
                'reason':'Constant prediction: a calibration slope is not identifiable'}
    diagnostic=LogisticRegression(penalty=None,solver='lbfgs',max_iter=1000).fit(logits,y)
    return {'intercept':float(diagnostic.intercept_[0]),'slope':float(diagnostic.coef_[0,0]),
            'converged':bool(diagnostic.n_iter_[0]<diagnostic.max_iter),
            'scope':'Held-out reporting diagnostic only. Never applied to predictions.'}


def decision_curve(y,p,thresholds):
    y,p=np.asarray(y),np.asarray(p);n=len(y);out=[]
    for threshold in thresholds:
        flagged=p>=threshold
        tp=int(np.sum(flagged&(y==1)));fp=int(np.sum(flagged&(y==0)))
        odds=threshold/(1-threshold)
        out.append({'threshold':threshold,'n':n,'tp':tp,'fp':fp,
                    'net_benefit':tp/n-fp/n*odds,'treat_all':float(y.mean()-(1-y.mean())*odds),'treat_none':0.0})
    return out


def cluster_intervals(y,p,flag,patient_ids,reps=1000,seed=808):
    """Patient multiplicities reproduce cluster resampling while grouping score ties."""
    y,p,flag=np.asarray(y,dtype=int),np.asarray(p),np.asarray(flag,dtype=bool)
    _,patient=np.unique(patient_ids,return_inverse=True);npeople=int(patient.max()+1)
    rng=np.random.default_rng(seed)
    draws=rng.integers(npeople,size=(reps,npeople))
    counts=np.zeros((reps,npeople),dtype=np.int32)
    np.add.at(counts,(np.arange(reps)[:,None],draws),1)
    weights=counts[:,patient].astype(float)
    order=np.argsort(-p,kind='stable');ordered=p[order]
    starts=np.r_[0,np.flatnonzero(np.diff(ordered)!=0)+1]
    pos=np.add.reduceat(weights[:,order]*y[order],starts,axis=1)
    neg=np.add.reduceat(weights[:,order]*(1-y[order]),starts,axis=1)
    positive=pos.sum(axis=1);negative=neg.sum(axis=1);total=positive+negative
    cumulative_pos=np.cumsum(pos,axis=1);cumulative_neg=np.cumsum(neg,axis=1)
    tp=weights@(flag*y);fp=weights@(flag*(1-y));fn=positive-tp;tn=negative-fp
    with np.errstate(divide='ignore',invalid='ignore'):
        auroc=(pos*(negative[:,None]-cumulative_neg+neg/2)).sum(axis=1)/(positive*negative)
        ap=(pos*cumulative_pos/np.maximum(cumulative_pos+cumulative_neg,1e-30)).sum(axis=1)/positive
        values={'auroc':auroc,'average_precision':ap,'brier':weights@((y-p)**2)/total,
                'recall':tp/positive,'precision':tp/(tp+fp),'specificity':tn/negative,
                'accuracy':(tp+tn)/total,'f1':2*tp/(2*tp+fp+fn)}
    result={}
    for name,value in values.items():
        finite=value[np.isfinite(value)]
        result[name]={'95ci':[float(np.quantile(finite,.025)),float(np.quantile(finite,.975))] if len(finite) else None,
                      'valid_resamples':len(finite),'requested_resamples':reps}
    return result


def metrics(y,p,threshold,patients,reps=1000,seed=808):
    y,p=np.asarray(y,dtype=int),np.asarray(p);flag=p>=threshold
    n=len(y);positive=int(y.sum());negative=n-positive
    tp=int(np.sum(flag&(y==1)));fp=int(np.sum(flag&(y==0)));tn=negative-fp;fn=positive-tp
    divide=lambda a,b:float(a/b) if b else None
    return {'n':n,'patients':len(set(patients)),'positive':positive,'negative':negative,
            'tp':tp,'fp':fp,'tn':tn,'fn':fn,'threshold':threshold,
            'auroc':float(roc_auc_score(y,p)) if positive and negative else None,
            'average_precision':float(average_precision_score(y,p)) if positive else None,
            'brier':float(np.mean((y-p)**2)),'recall':divide(tp,positive),'precision':divide(tp,tp+fp),
            'specificity':divide(tn,negative),'accuracy':divide(tp+tn,n),'f1':divide(2*tp,2*tp+fp+fn),
            'intervals':cluster_intervals(y,p,flag,patients,reps,seed)}
