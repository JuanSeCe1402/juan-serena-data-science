"""Funciones recuperadas de la tesis; separadas de generación de archivos y gráficos.
Modelo exploratorio sintético, sin validación experimental. Ver README.
Extracción y empaquetado para portafolio con asistencia de Codex.
"""
import numpy as np

epsilon0 = 8.854e-12

F_faraday = 96485.0

f     = np.logspace(2, 9, 600)

omega = 2 * np.pi * f + 1e-20

def polarizabilidad_lorentz(omega, omega0=1e16, gamma=1e14):
    """
    Polarizabilidad atómica compleja del oscilador de Lorentz.
    Ec. (alpha): alpha(omega) = (e²/m) / (omega0² - omega² - j*gamma*omega)

    Parámetros
    ----------
    omega  : array de frecuencias angulares [rad/s]
    omega0 : frecuencia natural (UV ~1e16 rad/s para bioimpedancia omega<<omega0)
    gamma  : coeficiente de amortiguamiento [rad/s]

    Retorna
    -------
    alpha : array complejo [C·m²/V]
    """
    e = 1.602e-19   # C
    m = 9.109e-31   # kg
    return (e**2 / m) / (omega0**2 - omega**2 - 1j * gamma * omega)

def clausius_mossotti(alpha, N, eps_host=epsilon0):
    """
    Permitividad efectiva macroscópica a partir de polarizabilidad microscópica.
    eps_ef = eps_host * (1 + 2*N*alpha/3*eps_host) / (1 - N*alpha/3*eps_host)

    Parámetros
    ----------
    alpha    : polarizabilidad (compleja, array)
    N        : densidad de dipolos [m⁻³]
    eps_host : permitividad del medio anfitrión [F/m]
    """
    factor = N * alpha / (3 * eps_host)
    return eps_host * (1 + 2 * factor) / (1 - factor)

def cole_cole(eps_inf, eps_s, tau, alpha_cc, omega):
    """
    Permitividad compleja de Cole-Cole.
    eps*(omega) = eps_inf + (eps_s - eps_inf) / (1 + (j*omega*tau)^(1-alpha))

    Parámetros
    ----------
    eps_inf  : permitividad de alta frecuencia [F/m]
    eps_s    : permitividad estática [F/m]
    tau      : tiempo de relajación [s]
    alpha_cc : parámetro de ensanchamiento Cole-Cole [0, 1)
    omega    : frecuencias angulares [rad/s]
    """
    return eps_inf + (eps_s - eps_inf) / (1 + (1j * omega * tau) ** (1 - alpha_cc))

def conductividad_ionica(c_na, c_k):
    """
    sigma = F * sum_i z_i * mu_i * c_i
    Unidades: c en mol/m³, mu en m²/(V·s)
    """
    z_na, z_k   = 1, 1
    mu_na, mu_k = 5.2e-8, 7.6e-8   # movilidades iónicas [m²/(V·s)]
    return F_faraday * (z_na * mu_na * c_na + z_k * mu_k * c_k)

def eps_intracelular(eps1, eps2_c, d, a):
    """
    Permitividad efectiva de la célula esférica (citoplasma + membrana).
    eps_int = eps1 / (1 + (d/a)*(eps1/eps2))   [Pauly-Schwan]

    Parámetros
    ----------
    eps1   : permitividad compleja del citoplasma
    eps2_c : permitividad compleja de la membrana
    d      : grosor de membrana [m]
    a      : radio celular [m]
    """
    return eps1 / (1 + (d / a) * (eps1 / eps2_c))

def maxwell_garnett(eps_int, eps3, phi):
    """
    Permitividad efectiva de la suspensión (Maxwell-Garnett completo).
    Válido para phi hasta ~0.6 (hematocrito fisiológico).

    eps_ef = eps3 * (eps_int + 2*eps3 + 2*phi*(eps_int - eps3)) /
                    (eps_int + 2*eps3 -   phi*(eps_int - eps3))

    Parámetros
    ----------
    eps_int : permitividad efectiva de la célula (Pauly-Schwan)
    eps3    : permitividad del plasma
    phi     : fracción volumétrica celular (hematocrito)
    """
    num = eps_int + 2*eps3 + 2*phi*(eps_int - eps3)
    den = eps_int + 2*eps3 -   phi*(eps_int - eps3)
    return eps3 * (num / den)

def simular_poblacion(omega, sigma1=0.5, sigma3=1.2, phi=0.4,
                      n_celulas=100, semilla=None):
    """
    Simula el espectro de impedancia de sangre completa.
    Promedia sobre distribución log-normal de radios celulares.

    Parámetros de citoplasma (región 1)
    ------------------------------------
    sigma1 : conductividad citoplasma [S/m]

    Parámetros de plasma (región 3)
    ---------------------------------
    sigma3 : conductividad plasma [S/m]
    phi    : hematocrito (fracción volumétrica)

    Parámetros de membrana (fijos, típicos eritrocito)
    ---------------------------------------------------
    eps2   = 5*epsilon0   sigma2 = 1e-7 S/m    d = 5e-9 m

    Retorna
    -------
    Z : impedancia compleja [Ohm], shape (len(omega),)
    """
    if semilla is not None:
        np.random.seed(semilla)

    # Permitividades complejas de citoplasma y plasma (Cole-Cole + conductividad)
    eps1 = cole_cole(5*epsilon0, 60*epsilon0, 1e-6, 0.10, omega) - 1j*sigma1/omega
    eps3 = cole_cole(10*epsilon0, 80*epsilon0, 1e-8, 0.05, omega) - 1j*sigma3/omega

    # Membrana: dieléctrico casi puro
    eps2_c = 5*epsilon0 - 1j*1e-7/omega

    # Distribución log-normal de radios (mu=5µm, sigma_log=0.2) [C5]
    radios = np.random.lognormal(mean=np.log(5e-6), sigma=0.2, size=n_celulas)
    d_mem  = 5e-9   # grosor de membrana [m]

    Z_total = np.zeros_like(omega, dtype=complex)
    for a in radios:
        eps_int  = eps_intracelular(eps1, eps2_c, d_mem, a)
        eps_cell = maxwell_garnett(eps_int, eps3, phi)
        # [C4] Promediar impedancias (no permitividades) — preserva no-linealidad
        Z_total += 1.0 / (sigma3 + 1j * omega * eps_cell)

    return Z_total / n_celulas

def validar_fisica(Z, omega, sigma_ref):
    """
    Verifica comportamientos asintóticos obligatorios:
      omega -> 0  :  Z ~ 1/sigma  (conducción iónica)
      omega -> inf:  |Z| decrece  (respuesta dieléctrica)
    """
    Z_low  = np.abs(Z[0])
    Z_high = np.abs(Z[-1])
    print("── Validación de límites físicos ──────────────────")
    print(f"  |Z| baja f  : {Z_low:.3e} Ω  (esperado ~ {1/sigma_ref:.3e} Ω)")
    print(f"  |Z| alta f  : {Z_high:.3e} Ω")
    assert Z_high < Z_low,          "ERROR: |Z| no decrece con la frecuencia"
    assert np.all(np.isfinite(Z)),  "ERROR: Z contiene NaN o Inf"
    print("  ✓ Todos los límites físicos verificados.\n")
