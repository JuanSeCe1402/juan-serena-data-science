"""Funciones recuperadas de la tesis; separadas de generación de archivos y gráficos.
Modelo exploratorio sintético, sin validación experimental. Ver README.
Extracción y empaquetado para portafolio con asistencia de Codex.
"""
import numpy as np

epsilon0 = 8.854e-12

f_db     = np.logspace(3, 8, 100)

omega_db = 2 * np.pi * f_db + 1e-20

def simulate_HH(g_Na, g_K, T=50.0, dt=0.02):
    t = np.arange(0, T, dt)
    N = len(t)
    V = np.full(N, -65.0)
    m = np.zeros(N)
    h = np.zeros(N)
    n = np.zeros(N)

    E_Na, E_K, E_L   = 50.0, -77.0, -54.4
    g_L, C_m, I_ext  = 0.3, 1.0, 10.0

    def safe_exp(x):
        return np.exp(np.clip(x, -500, 500))

    def am(V):
        dV = V + 40.0
        if abs(dV) < 1e-7: return 1.0
        d = 1.0 - safe_exp(-dV / 10.0)
        return np.clip(0.1 * dV / d, 0, 10) if abs(d) > 1e-10 else 1.0

    def bm(V): return np.clip(4.0 * safe_exp(-(V + 65) / 18), 0, 50)
    def ah(V): return np.clip(0.07 * safe_exp(-(V + 65) / 20), 0, 1)
    def bh(V): return 1.0 / (1.0 + safe_exp(-(V + 35) / 10))

    def an(V):
        dV = V + 55.0
        if abs(dV) < 1e-7: return 0.1
        d = 1.0 - safe_exp(-dV / 10.0)
        return np.clip(0.01 * dV / d, 0, 1) if abs(d) > 1e-10 else 0.1

    def bn(V): return np.clip(0.125 * safe_exp(-(V + 65) / 80), 0, 1)

    for i in range(N - 1):
        Vi     = V[i]
        m[i+1] = np.clip(m[i] + dt*(am(Vi)*(1-m[i]) - bm(Vi)*m[i]), 0, 1)
        h[i+1] = np.clip(h[i] + dt*(ah(Vi)*(1-h[i]) - bh(Vi)*h[i]), 0, 1)
        n[i+1] = np.clip(n[i] + dt*(an(Vi)*(1-n[i]) - bn(Vi)*n[i]), 0, 1)
        I_Na   = g_Na * (m[i+1]**3) * h[i+1] * (Vi - E_Na)
        I_K    = g_K  * (n[i+1]**4)            * (Vi - E_K)
        dV     = np.clip(dt*(I_ext - I_Na - I_K - g_L*(Vi - E_L)) / C_m, -20, 20)
        V[i+1] = np.clip(Vi + dV, -100.0, 60.0)

    if not np.all(np.isfinite(V)):
        return None
    return V

def cole_cole(eps_inf, eps_s, tau, alpha, omega):
    return eps_inf + (eps_s - eps_inf) / (1 + (1j * omega * tau)**(1 - alpha))

def compute_Z(V, sigma_base, tau, alpha):
    eps    = cole_cole(5*epsilon0, 60*epsilon0, tau, alpha, omega_db)
    Z_time = []
    for v in V:
        sigma = sigma_base * (1.0 + 0.02 * np.tanh(v / 30.0))
        Z_time.append(1.0 / (sigma + 1j * omega_db * eps))
    Z_arr = np.array(Z_time)   # shape: (n_timesteps, 100)

    if not np.all(np.isfinite(Z_arr)):
        return None
    return Z_arr

def extract_features(Z_array, noise_level=0.01):
    """
    Z_array: (n_timesteps, 100) complejo

    Features (600 dim):
      [0:100]   log|Re(Z_mean)|   promedio temporal
      [100:200] log|Im(Z_mean)|   promedio temporal
      [200:300] log|Re(Z_std)|    desv. estándar temporal  ← g_Na, g_K
      [300:400] log|Im(Z_std)|    desv. estándar temporal  ← g_Na, g_K
      [400:500] Re(Z_max-Z_min)   rango temporal norm.     ← amplitud PA
      [500:600] Im(Z_max-Z_min)   rango temporal norm.     ← amplitud PA
    """
    if noise_level > 0:
        Z_array = Z_array + noise_level * np.random.randn(*Z_array.shape)

    Re = np.real(Z_array)   # (T, 100)
    Im = np.imag(Z_array)   # (T, 100)

    # Estadísticas temporales
    re_mean = Re.mean(axis=0)
    im_mean = Im.mean(axis=0)
    re_std  = Re.std(axis=0)  + 1e-30
    im_std  = Im.std(axis=0)  + 1e-30
    re_rng  = Re.max(axis=0)  - Re.min(axis=0)
    im_rng  = Im.max(axis=0)  - Im.min(axis=0)

    # Normalizar rango por el promedio para hacerlo invariante a escala
    re_rng_norm = re_rng / (np.abs(re_mean) + 1e-30)
    im_rng_norm = im_rng / (np.abs(im_mean) + 1e-30)

    X = np.concatenate([
        np.log(np.abs(re_mean) + 1e-30),   # [0:100]
        np.log(np.abs(im_mean) + 1e-30),   # [100:200]
        np.log(re_std),                     # [200:300]
        np.log(im_std),                     # [300:400]
        re_rng_norm,                        # [400:500]
        im_rng_norm,                        # [500:600]
    ]).astype(np.float32)

    if not np.all(np.isfinite(X)):
        return None
    return X

def generate_sample(noise_level=0.01):
    g_Na       = np.random.uniform(80.0,  140.0)
    g_K        = np.random.uniform(20.0,   50.0)
    sigma_base = np.random.uniform(0.5,    2.0)
    tau        = np.random.uniform(1e-6,   1e-4)
    alpha      = np.random.uniform(0.05,   0.3)

    V = simulate_HH(g_Na, g_K)
    if V is None:
        return None

    Z = compute_Z(V, sigma_base, tau, alpha)
    if Z is None:
        return None

    X = extract_features(Z, noise_level=noise_level)
    if X is None:
        return None

    y = np.array([g_Na, g_K, sigma_base, tau, alpha], dtype=np.float32)
    return X, y
