"""Train-only discrete timing posterior for a synthetic interpretation-layer check."""
import math
import numpy as np

HYPOTHESES=np.array([-1,*range(1,46)],dtype=int)
CHANNELS=('temperature','rhr','hrv')


def _group(row):
    history=np.asarray(row.get('prior_cycle_lengths',[]),dtype=float)
    calendar='none' if not history.size else 'short' if np.mean(history[-3:])<30 else 'mid' if np.mean(history[-3:])<36 else 'long'
    age='under30' if row['age']<30 else '30plus'
    return calendar,age


def fit(records, day):
    """Fit a Laplace-smoothed calendar/static prior and pre/post Gaussian channels."""
    priors={}; channel_values={channel:{False:[],True:[]} for channel in CHANNELS}
    for row in records:
        counts=priors.setdefault(_group(row),np.ones(len(HYPOTHESES),dtype=float))
        hypothesis_index=0 if row['ovulation_day']<1 else int(row['ovulation_day'])
        counts[hypothesis_index]+=1
        for index in range(day):
            post=row['ovulation_day']>0 and index>=row['ovulation_day']
            for channel in CHANNELS:
                value=float(row[channel][index])
                if np.isfinite(value): channel_values[channel][post].append(value)
    prior={str(key): (values/values.sum()).tolist() for key,values in priors.items()}
    channels={}
    floors={'temperature':.02,'rhr':.2,'hrv':.2}
    for channel,states in channel_values.items():
        channels[channel]={}
        for post,values in states.items():
            channels[channel][str(post)]={'mean':float(np.mean(values)),'std':max(float(np.std(values)),floors[channel])}
    return {'day':int(day),'hypotheses':HYPOTHESES.tolist(),'prior':prior,'channels':channels,
            'scope':'train-only synthetic timing posterior; interpretation-layer check'}


def posterior(model, record):
    hypotheses=np.asarray(model['hypotheses'],dtype=int)
    base=np.asarray(model['prior'].get(str(_group(record)),np.mean(np.asarray(list(model['prior'].values())),axis=0)),dtype=float)
    logp=np.log(base)
    for position in range(model['day']):
        for channel in CHANNELS:
            value=float(record[channel][position])
            if not np.isfinite(value): continue
            state=np.asarray([(h>0 and position>=h) for h in hypotheses])
            pre=model['channels'][channel]['False'];post=model['channels'][channel]['True']
            means=np.where(state,post['mean'],pre['mean']);stds=np.where(state,post['std'],pre['std'])
            logp+=-.5*((value-means)/stds)**2-np.log(stds)-.5*math.log(2*math.pi)
    logp-=np.max(logp);weights=np.exp(logp);weights/=weights.sum()
    event=float(weights[(hypotheses<0)|(hypotheses>21)].sum())
    present=weights[hypotheses>0];days=hypotheses[hypotheses>0]
    estimate=float((present*days).sum()/present.sum()) if present.sum() else None
    return {'event_probability':event,'posterior':weights.tolist(),'ovulation_day_posterior_mean':estimate}
