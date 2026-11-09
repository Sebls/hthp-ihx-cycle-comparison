# %% [markdown]
# # Project : Internal heat exchanger (IHX)

# %% [markdown]
# ### imports

# %%
# --- imports ---
import numpy as np
from CoolProp.CoolProp import PropsSI

import caldis
from caldis.core.system import System
from caldis.components import FluidBoundary
from caldis.components import Compressor
from caldis.components import SizingHX
from caldis.components import Valve
from caldis.fluids import CoolPropBackend
from caldis.solvers import solve


print("Caldis version:", getattr(caldis, "__version__", "unknown"))

# %% [markdown]
# ## The baseline cycle — S0

# %% [markdown]
# <img src="attachment:cb754d4a-ccfd-42f1-9a29-b8babcbf4d17.png" width="400">

# %%
# Common specification and assumptions

p_sink = 10e5 # 10 bar, condenser
T_sink_in = 120 + 273.15
T_sink_out = 130 + 273.15

p_source = 3e5 # 3 bar, evaporator
T_source_in = 35 + 273.15
T_source_out = 30 + 273.15

Q_cond = 100e3 # condensor
cp_w = 4.25e3 # 4.25 kJ/(kg.K)

sc = 5 # supercooling at evaporator outlet
sh = 5 # superheating at condenser outlet

pinch = 5 # 5K, evaporator and condenser

eta_is = 0.70



# %%
# Refrigerant saturation temperatures
T_cond = T_sink_out + pinch  # 135 °C
T_evap = T_source_out - pinch  # 25 °C

# Refrigerant outlet temperatures
T_ref_cond_out = T_cond - sc  # 130 °C
T_ref_evap_out = T_evap + sh  # 30 °C

# %%
# Saturation temperatures and pressures for refrigerant

p_cond = PropsSI("P", "T", T_cond, "Q", 0, "R-1233zd(E)")
p_evap = PropsSI("P", "T", T_evap, "Q", 1, "R-1233zd(E)")

print("p_cond = ", p_cond/1e5, "bar")
print("p_evap = ", p_evap/1e5, "bar")

# %% [markdown]
# Dans le condenseur : $
# \dot m_{\mathrm{sink}}=
# \frac{Q_{\mathrm{cond}}}
# {c_{p,w}(T_{\mathrm{sink,out}}-T_{\mathrm{sink,in}})} = 
# \frac{Q_{\mathrm{cond}}}
# {h_{\mathrm{sink,out}}-h_{\mathrm{sink,in}}}
# $

# %%
be_r = CoolPropBackend("R-1233zd(E)") # on définit que le réfrigérant c'est du R-1233zd(E)
be_w = CoolPropBackend('Water') # on définit que la source chaude à chauffer c'est de l'eau

h_r = 3000 # Refrigerant heat transfer coefficient
h_w = 3000 # Water heat transfer coefficient

# Déclarer les composants
# compressor
compressor = Compressor("compressor", backend=be_r, eta_is=eta_is)

#condensor
condensor = SizingHX('condensor', backend_cold=be_w, backend_hot=be_r, 
                h_cold=h_w, h_hot=h_r,area_ratio_cold_to_hot=1)
source_in = FluidBoundary('source_in', backend=be_w, p=p_source, T=T_source_in)
source_out = FluidBoundary('source_out', backend=be_w, T=T_source_out)

# expansion valve
valve = Valve('valve', backend=be_r)

# evaporator
evaporator = SizingHX('evaporator', backend_cold=be_r, backend_hot=be_w, 
                h_cold=h_r, h_hot=h_w,
                area_ratio_cold_to_hot=1)
sink_in = FluidBoundary('sink_in', backend=be_w, p=p_sink, T=T_sink_in)
sink_out = FluidBoundary('sink_out', backend=be_w, T=T_sink_out)


# Déclarer le système
sys0_ = System('sys0')

# Ajouter les composants
sys0_.add(compressor, source_in, source_out, condensor, valve, sink_in, sink_out, evaporator)

# Ajouter les connections entre les composants
sys0_.connect(compressor.out, condensor.hot_in)
sys0_.connect(condensor.hot_out, valve.inl)
sys0_.connect(sink_in.port, condensor.cold_in)
sys0_.connect(condensor.cold_out, sink_out.port)
sys0_.connect(valve.out, evaporator.cold_in)
sys0_.connect(evaporator.cold_out, compressor.inl, close_loop=True)
sys0_.connect(evaporator.hot_in, source_in.port) 
sys0_.connect(evaporator.hot_out, source_out.port)


# Contraintes

# 1. contrainte sur le débit massique de l'eau dans le condenseur
#    mdot_sink = Q_cond / (h_sink_out - h_sink_in)
sys0_.add_constraint(lambda: (sink_out.port.h - sink_in.port.h)*sink_out.port.mdot - Q_cond, 'Q_cond')

# 2. contrainte sur la température du réfrigérant en sortie du condenseur
#    T_ref_cond_out = T_cond - sc  # 130 °C
sys0_.add_constraint(lambda: condensor.hot_out.T - T_ref_cond_out, 'SC')

# 3. contrainte sur la température du réfrigérant en sortie de l'évaporateur
#    T_ref_evap_out = T_evap + sh  # 30 °C
sys0_.add_constraint(lambda: evaporator.cold_out.T - T_ref_evap_out, 'SH')

# 4 et 5. contraintes sur les deux pressions de condensation et évaporation dans le circuit
sys0_.add_constraint(lambda: valve.inl.p - p_cond, 'HP')
sys0_.add_constraint(lambda: valve.out.p - p_evap, 'LP')

# Aide à la convergence : set_start_port
# 1. côté condensor
sys0_.set_start_port(condensor.hot_in, p=p_cond, T=T_cond+10)
sys0_.set_start_port(condensor.hot_out, p=p_cond, T=T_cond-sc)
sys0_.set_start_port(condensor.cold_in, p=p_sink, T=T_sink_in)
sys0_.set_start_port(condensor.cold_out, p=p_sink, T=T_sink_out)


# 2. coté evaporator
sys0_.set_start_port(evaporator.cold_in, p=p_evap, T=T_evap-1)
sys0_.set_start_port(evaporator.cold_out, p=p_evap, T=T_evap+sh)
sys0_.set_start_port(evaporator.hot_in, p=p_source, T=T_source_in)
sys0_.set_start_port(evaporator.hot_out, p=p_source, T=T_source_out)

from caldis.solvers.autostart import autostart
autostart(sys0_)

sol = solve(sys0_, verbose=True)

# %%
sys0_.port_table()

# %%
mdot_ref_0  = float(compressor.out.mdot)
print("mdot_ref_0 :", mdot_ref_0, "kg/s")

# %% [markdown]
# ## Internal heat exchanger (IHX) - S4

# %% [markdown]
# <img src="attachment:f05b22a5-9f21-42e4-a9a9-062dc14c70a7.png" width="400">

# %%
# Specification and assumptions for S4

x_evap = 0.90 # titre vapeur en sortie de l'évaporateur : default 0.90
suc = 5 # 5K

# %%
be_r = CoolPropBackend("R-1233zd(E)") # on définit que le réfrigérant c'est du R-1233zd(E)
be_w = CoolPropBackend('Water') # on définit que la source chaude à chauffer c'est de l'eau

h_r = 3000 # Refrigerant heat transfer coefficient
h_w = 3000 # Water heat transfer coefficient

# Déclarer les composants
# compressor
compressor = Compressor("compressor", backend=be_r, eta_is=eta_is)

#condensor
condensor = SizingHX('condensor', backend_cold=be_w, backend_hot=be_r, 
                h_cold=h_w, h_hot=h_r,area_ratio_cold_to_hot=1)
source_in = FluidBoundary('source_in', backend=be_w, p=p_source, T=T_source_in)
source_out = FluidBoundary('source_out', backend=be_w, T=T_source_out)

# expansion valve
valve = Valve('valve', backend=be_r)

# evaporator
evaporator = SizingHX('evaporator', backend_cold=be_r, backend_hot=be_w, 
                h_cold=h_r, h_hot=h_w,
                area_ratio_cold_to_hot=1)
sink_in = FluidBoundary('sink_in', backend=be_w, p=p_sink, T=T_sink_in)
sink_out = FluidBoundary('sink_out', backend=be_w, T=T_sink_out)

# Ajout pour le S4 : internal heat exchanger 
ihx = SizingHX('ihx', backend_cold=be_r, backend_hot=be_r, 
                h_cold=h_r, h_hot=h_r,
                area_ratio_cold_to_hot=1)

# Déclarer le système
sys4_ = System('sys4')

# Ajouter les composants
sys4_.add(compressor, source_in, source_out, condensor, valve, sink_in, sink_out, evaporator, ihx)

# Ajouter les connections entre les composants
sys4_.connect(compressor.out, condensor.hot_in)
# sys4_.connect(condensor.hot_out, valve.inl)
sys4_.connect(condensor.hot_out, ihx.hot_in)
sys4_.connect(ihx.hot_out, valve.inl)
sys4_.connect(sink_in.port, condensor.cold_in)
sys4_.connect(condensor.cold_out, sink_out.port)
sys4_.connect(valve.out, evaporator.cold_in)
# sys4_.connect(evaporator.cold_out, compressor.inl, close_loop=True)
sys4_.connect(evaporator.cold_out, ihx.cold_in)
sys4_.connect(ihx.cold_out, compressor.inl, close_loop=True)
sys4_.connect(evaporator.hot_in, source_in.port) 
sys4_.connect(evaporator.hot_out, source_out.port)


# Contraintes

# 1. contrainte sur le débit massique de l'eau dans le condenseur
#    mdot_sink = Q_cond / (h_sink_out - h_sink_in)
sys4_.add_constraint(lambda: (sink_out.port.h - sink_in.port.h)*sink_out.port.mdot - Q_cond, 'Q_cond')

# 2. contrainte sur la température du réfrigérant en sortie du condenseur
#    T_ref_cond_out = T_cond - sc  # 130 °C
sys4_.add_constraint(lambda: condensor.hot_out.T - T_ref_cond_out, 'SC')

# 3. MODIFICATION : contrainte sur le titre vapeur du réfrigérant en sortie de l'évaporateur
#    x_evap = 0.90
sys4_.add_constraint(lambda: evaporator.cold_out.x - x_evap, 'x_evap')

# 3.bis MODIFICATION contrainte sur la température du réfrigérant en entrée du compresseur
#    T_ref_comp_in = T_evap + suc  # si suc = 5K, 30 °C
sys4_.add_constraint(lambda: compressor.inl.T - (T_evap + suc), 'SUC')

# 4 et 5. contraintes sur les deux pressions de condensation et évaporation dans le circuit
sys4_.add_constraint(lambda: valve.inl.p - p_cond, 'HP')
sys4_.add_constraint(lambda: valve.out.p - p_evap, 'LP')


# Aide à la convergence : set_start_port
# 1. côté condensor
sys4_.set_start_port(condensor.hot_in, p=p_cond, T=T_cond+10)
sys4_.set_start_port(condensor.hot_out, p=p_cond, T=T_cond-sc)
sys4_.set_start_port(condensor.cold_in, p=p_sink, T=T_sink_in)
sys4_.set_start_port(condensor.cold_out, p=p_sink, T=T_sink_out)


# 2. coté evaporator
sys4_.set_start_port(evaporator.cold_in, p=p_evap, T=T_evap-1)
# MODIFICATION
h_ihx_col_out = PropsSI('H', 'P', p_evap, 'Q', x_evap, "R-1233zd(E)")   # sortie évaporateur, default x = 0.90 (J/kg)
sys4_.set_start_port(evaporator.cold_out, p=p_evap, h=h_ihx_col_out)
sys4_.set_start_port(evaporator.hot_in, p=p_source, T=T_source_in)
sys4_.set_start_port(evaporator.hot_out, p=p_source, T=T_source_out)

# 3. AJOUT : coté IHX
#sys4_.set_start_port(ihx.cold_in, p=p_evap)
sys4_.set_start_port(ihx.cold_out, p=p_evap, T=T_evap+suc)
#sys4_.set_start_port(ihx.hot_in, p=p_cond, T=T_cond-sc)
sys4_.set_start_port(ihx.hot_out, p=p_cond, T=T_cond-sc-15)

from caldis.solvers.autostart import autostart
autostart(sys4_)

sol = solve(sys4_, verbose=True)

# %%


# %%


# %%



