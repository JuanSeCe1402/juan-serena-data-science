"""Evaluación sintética: separar antes de normalizar y reservar prueba final.

No carga bases ni checkpoints históricos. Por defecto no escribe archivos.
"""
import argparse
import importlib.metadata
import json
import platform
from pathlib import Path
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from modelo_temporal import generate_sample

PARAMETROS = ['g_Na', 'g_K', 'sigma_base', 'tau', 'alpha']


def particiones(n, semilla=42):
    if type(n) is not int or n < 15:
        raise ValueError('Se necesitan al menos 15 muestras para tres conjuntos.')
    idx = np.random.default_rng(semilla).permutation(n)
    reserve = max(3, n//5)
    return {'train':idx[2*reserve:], 'validation':idx[reserve:2*reserve], 'test':idx[:reserve]}


def normalizacion_entrenamiento(X, y, indices):
    X = np.asarray(X, dtype=float); y = np.asarray(y, dtype=float)
    train = np.asarray(indices, dtype=int)
    if X.ndim != 2 or y.ndim != 2 or len(X)!=len(y) or not len(train):
        raise ValueError('Matrices y partición incompatibles.')
    if not np.isfinite(X).all() or not np.isfinite(y).all():
        raise ValueError('Los datos deben ser finitos.')
    xm, ym = X[train].mean(axis=0), y[train].mean(axis=0)
    xs, ys = X[train].std(axis=0), y[train].std(axis=0)
    xs = np.where(xs > 1e-12, xs, 1.)
    ys = np.where(ys > 1e-12, ys, 1.)
    return {'X_mean':xm, 'X_std':xs, 'y_mean':ym, 'y_std':ys}


def generar(n, semilla):
    # El modelo recuperado usa NumPy global. Aislar y restaurar su estado.
    previous = np.random.get_state()
    try:
        np.random.seed(semilla)
        rows=[]
        for _ in range(n):
            sample=generate_sample(noise_level=.01)
            if sample is None:
                raise ValueError('El simulador produjo una muestra no finita; revisar parámetros.')
            rows.append(sample)
        return np.stack([r[0] for r in rows]), np.stack([r[1] for r in rows])
    finally:
        np.random.set_state(previous)


def entrenar_bionet(X, y, split, epochs, seed):
    # Importar PyTorch solo cuando se solicita. Arquitectura recuperada de la tesis.
    import torch
    from bionet import BioNet
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    model=BioNet(input_size=X.shape[1], n_params=y.shape[1])
    optimizer=torch.optim.Adam(model.parameters(),lr=1e-3)
    loss_fn=torch.nn.MSELoss()
    tx=torch.tensor(X,dtype=torch.float32); ty=torch.tensor(y,dtype=torch.float32)
    best_loss=float('inf'); best=None
    for _ in range(epochs):
        model.train(); optimizer.zero_grad()
        loss=loss_fn(model(tx[split['train']]),ty[split['train']]);loss.backward();optimizer.step()
        model.eval()
        with torch.no_grad():
            validation=float(loss_fn(model(tx[split['validation']]),ty[split['validation']]))
        if validation < best_loss:
            best_loss=validation
            best={k:v.detach().clone() for k,v in model.state_dict().items()}
    if best is None:
        raise ValueError('Entrenamiento no finito.')
    model.load_state_dict(best);model.eval()
    with torch.no_grad():return model(tx[split['test']]).numpy()


def evaluar(X,y,semilla=42,modelo='ridge',epochs=10):
    X=np.asarray(X,dtype=float);y=np.asarray(y,dtype=float)
    if y.ndim!=2 or y.shape[1]!=5 or X.ndim!=2 or X.shape[1]!=600:
        raise ValueError('Esta versión exige 600 variables y cinco parámetros.')
    split=particiones(len(X),semilla)
    stats=normalizacion_entrenamiento(X,y,split['train'])
    xn=(X-stats['X_mean'])/stats['X_std'];yn=(y-stats['y_mean'])/stats['y_std']
    train,test=split['train'],split['test']
    if modelo=='ridge':
        # alpha fijo, no seleccionado sobre prueba.
        model=Ridge(alpha=10.)
        model.fit(xn[train],yn[train]);pred=model.predict(xn[test])
    elif modelo=='bionet':
        if type(epochs) is not int or epochs < 1:raise ValueError('epochs debe ser positivo.')
        pred=entrenar_bionet(xn,yn,split,epochs,semilla)
    else:raise ValueError('Modelo desconocido.')
    physical=pred*stats['y_std']+stats['y_mean']
    baseline=np.tile(stats['y_mean'],(len(test),1))
    return {'data_source':'synthetic_exploratory_model','model':modelo,'seed':semilla,
            'samples':len(X),'features':X.shape[1],
            'training':{'epochs':epochs if modelo=='bionet' else None,
                        'ridge_alpha':10. if modelo=='ridge' else None},
            'runtime':{'python':platform.python_version(),
                       'numpy':np.__version__,
                       'scikit-learn':importlib.metadata.version('scikit-learn'),
                       **({'torch':importlib.metadata.version('torch')} if modelo=='bionet' else {})},
            'split_ids':{k:v.tolist() for k,v in split.items()},
            'normalization_fit':'train_only',
            'metrics':{name:{'mae':float(mean_absolute_error(y[test,j],physical[:,j])),
                             'baseline_mean_mae':float(mean_absolute_error(y[test,j],baseline[:,j])),
                             'r2':float(r2_score(y[test,j],physical[:,j]))}
                       for j,name in enumerate(PARAMETROS)},
            'limitations':['Small synthetic experiment; not an accuracy claim.',
                           'Physical identifiability and experimental validity not established.',
                           'No historical checkpoints or datasets were used.']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--muestras',type=int,default=30)
    parser.add_argument('--semilla',type=int,default=42)
    parser.add_argument('--modelo',choices=['ridge','bionet'],default='ridge')
    parser.add_argument('--epochs',type=int,default=10)
    parser.add_argument('--salida',type=Path)
    args=parser.parse_args()
    if not 15<=args.muestras<=1000:parser.error('muestras debe estar entre 15 y 1000.')
    if not 0<=args.semilla<2**32:parser.error('semilla fuera de rango.')
    if args.salida and args.salida.exists():parser.error('La salida ya existe; elige otro archivo.')
    X,y=generar(args.muestras,args.semilla)
    report=evaluar(X,y,args.semilla,args.modelo,args.epochs)
    text=json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)
    if args.salida:
        args.salida.parent.mkdir(parents=True,exist_ok=True)
        with args.salida.open('x',encoding='utf-8') as stream:stream.write(text+'\n')
    print(text)


if __name__=='__main__':main()
