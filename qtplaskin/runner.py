from numpy import inf, loadtxt, where

from qtplaskin.zdplaskin import Kinetics


def run(conn, model, init_file, field_file, max_dt=inf):
    if isinstance(model, str):
        model = Kinetics(model)

    # Initialize zdplaskin
    model.init()
    model.set_config(stat_accum=True, atol=1e-8, rtol=1e-8,
                     bolsig_ee_frac=0.0, silence_mode=True)
    model.set_conditions(gas_temperature=200,
                         spec_heat_ratio=1.4,
                         reduced_field=1.0,
                         reduced_frequency=0.0,
                         gas_heating=False)

    # Sets the initial densities
    model.load_densities(init_file)
    model.truncate_densities()

    # Loads the electric field profile
    t, EN = loadtxt(field_file, unpack=True)
    dt = t[1:] - t[:-1]

    # Correct the field with a minimum field
    min_EN = 1.0
    EN = where(EN > min_EN, EN, min_EN)

    # The other end of the connection wants first wants t, the list of species
    # and the list of reactions
    conn.send([t, model.SPECIES, model.REACTIONS, model.get_stech_matrix()])

    # This is the main loop:
    for i, (it, idt, iEN) \
            in enumerate(zip(t[:-1], dt, EN)):
        print("t = %g, E/N = %g Td" % (it, iEN))

        # model.set_conditions(reduced_field=iEN)
        model.set_conditions(gas_temperature=200,
                             spec_heat_ratio=1.4,
                             reduced_frequency=0.0,
                             reduced_field=iEN,
                             gas_heating=False)
        model.truncate_densities()

        density = [model.get_density(s)
                   for s in model.SPECIES]
        rates = model.get_reaction_rates()

        current_conditions = model.get_conditions()

        # Send the present status to the other end of the connection
        conn.send([i, density, rates, current_conditions])

        model.controlled_timestep(it, idt, max_dt)

    conn.send(None)
    conn.close()
