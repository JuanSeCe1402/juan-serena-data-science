import unittest
import numpy as np
from experimento import particiones, normalizacion_entrenamiento, evaluar
from modelo_temporal import simulate_HH, compute_Z, extract_features


class ExperimentoTests(unittest.TestCase):
    def test_split_reproducible_disjoint_complete(self):
        a=particiones(31,42);b=particiones(31,42)
        for k in a:np.testing.assert_array_equal(a[k],b[k])
        sets=[set(v.tolist()) for v in a.values()]
        self.assertEqual(set.union(*sets),set(range(31)))
        for i in range(3):
            for j in range(i):self.assertFalse(sets[i]&sets[j])

    def test_held_out_values_cannot_change_training_normalization(self):
        rng=np.random.default_rng(5);X=rng.normal(size=(20,600));y=rng.normal(size=(20,5))
        split=particiones(20);before=normalizacion_entrenamiento(X,y,split['train'])
        held=np.r_[split['test'],split['validation']]
        X[held]=1e20;y[held]=-1e20
        after=normalizacion_entrenamiento(X,y,split['train'])
        for k in before:np.testing.assert_array_equal(before[k],after[k])

    def test_recovered_model_feature_contract(self):
        V=simulate_HH(110,36,T=1.,dt=.02)
        Z=compute_Z(V,1.,1e-5,.1)
        f=extract_features(Z,noise_level=0)
        self.assertEqual(Z.shape,(50,100));self.assertEqual(f.shape,(600,))
        self.assertTrue(np.isfinite(f).all())

    def test_fixed_evaluation_reports_all_parameters_without_overlap(self):
        rng=np.random.default_rng(22);X=rng.normal(size=(30,600));y=rng.normal(size=(30,5))
        a=evaluar(X,y);b=evaluar(X,y)
        self.assertEqual(a,b);self.assertEqual(a['normalization_fit'],'train_only')
        self.assertEqual(len(a['metrics']),5)
        for m in a['metrics'].values():self.assertTrue(np.isfinite(list(m.values())).all())


if __name__=='__main__':unittest.main()
