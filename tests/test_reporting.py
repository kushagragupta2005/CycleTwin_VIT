import unittest
import numpy as np
from sklearn.metrics import average_precision_score,roc_auc_score
from src.reporting import metrics,reliability,decision_curve,cluster_intervals


class ReportingTests(unittest.TestCase):
    def test_ties_use_standard_average_precision(self):
        y=np.array([1,0,1,0,1,0]);p=np.array([.8,.8,.6,.6,.1,.1])
        m=metrics(y,p,.5,['a','a','b','b','c','c'],reps=30)
        self.assertAlmostEqual(m['average_precision'],average_precision_score(y,p),delta=1e-12)
        self.assertAlmostEqual(m['auroc'],roc_auc_score(y,p),delta=1e-12)
        self.assertEqual(m['tp']+m['fp']+m['tn']+m['fn'],len(y))

    def test_reliability_counts_and_decision_curve_arithmetic(self):
        bins,ece=reliability([0,1],[.1,.9],10)
        self.assertEqual(sum(r['n'] for r in bins),2)
        self.assertAlmostEqual(ece,.1)
        curve=decision_curve([0,1],[.1,.9],[.5])[0]
        self.assertEqual(curve['net_benefit'],.5)

    def test_bootstrap_tie_grouping_matches_direct_sklearn_resamples(self):
        y=np.array([1,1,0,1,0,0]);p=np.array([.8,.8,.6,.6,.1,.1]);ids=np.array(['a','a','b','b','c','c'])
        got=cluster_intervals(y,p,p>=.5,ids,reps=50,seed=8)
        rng=np.random.default_rng(8);auc=[];ap=[]
        for _ in range(50):
            chosen=rng.choice(np.unique(ids),size=3,replace=True)
            index=np.concatenate([np.flatnonzero(ids==name) for name in chosen])
            if y[index].sum(): ap.append(average_precision_score(y[index],p[index]))
            if len(np.unique(y[index]))==2: auc.append(roc_auc_score(y[index],p[index]))
        self.assertTrue(np.allclose(got['average_precision']['95ci'],np.quantile(ap,[.025,.975]),rtol=0,atol=1e-12))
        self.assertTrue(np.allclose(got['auroc']['95ci'],np.quantile(auc,[.025,.975]),rtol=0,atol=1e-12))
