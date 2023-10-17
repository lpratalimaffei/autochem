"""Test reac
"""
from automol import geom, graph, reac, smiles


def test__reactant_graphs():
    """Test reac.reactant_graphs"""

    def _test(rct_smis, prd_smis):
        print("Testing reactant_graphs()")
        print(f"{'.'.join(rct_smis)}>>{'.'.join(prd_smis)}")
        rct_gras0 = tuple(map(smiles.graph, rct_smis))
        prd_gras0 = tuple(map(smiles.graph, prd_smis))
        rxns = reac.find(rct_gras0, prd_gras0, stereo=False)
        for rxn in rxns:
            rct_gras1 = reac.reactant_graphs(rxn, shift_keys=False)
            prd_gras1 = reac.product_graphs(rxn, shift_keys=False)
            assert rct_gras1 == rct_gras0
            assert prd_gras1 == prd_gras0

    _test(["FC=CF", "[OH]"], ["F[CH]C(O)F"])
    _test(["C1CCC1", "[CH3]"], ["C", "C1[CH]CC1"])
    _test(["CO", "C[CH2]"], ["CCC", "[OH]"])


def test__expand_stereo():
    """Test reac.expand_stereo_for_reaction"""

    def _test(rct_smis, prd_smis, nexp1, nexp2):
        print("Testing expand_stereo()")
        print(f"{'.'.join(rct_smis)}>>{'.'.join(prd_smis)}")
        rct_gras0 = tuple(map(smiles.graph, rct_smis))
        prd_gras0 = tuple(map(smiles.graph, prd_smis))
        rxn = reac.find(rct_gras0, prd_gras0, stereo=False)[0]
        srxns = reac.expand_stereo(rxn, enant=False)
        assert len(srxns) == nexp1
        srxns = reac.expand_stereo(rxn, enant=True)
        assert len(srxns) == nexp2

    _test(["FC=CF", "[OH]"], ["F[CH]C(O)F"], 2, 4)


def test__expand_stereo_for_reaction():
    """Test reac.expand_stereo_for_reaction"""

    def _test(rct_smis, prd_smis):
        print("Testing expand_stereo_for_reaction()")
        print(f"{'.'.join(rct_smis)}>>{'.'.join(prd_smis)}")
        rct_gras0 = tuple(map(smiles.graph, rct_smis))
        prd_gras0 = tuple(map(smiles.graph, prd_smis))
        rxn = reac.find(rct_gras0, prd_gras0, stereo=False)[0]
        srxns = reac.expand_stereo_for_reaction(rxn, rct_gras0, prd_gras0)
        assert len(srxns) == 1
        (srxn,) = srxns
        rct_gras1 = reac.reactant_graphs(srxn, shift_keys=False)
        prd_gras1 = reac.product_graphs(srxn, shift_keys=False)
        assert rct_gras1 == rct_gras0
        assert prd_gras1 == prd_gras0

    _test(["F/C=C/F", "[OH]"], ["F[CH][C@H](O)F"])


def test__from_old_string():
    """Text reac.from_old_string (with stereo!)"""
    old_rxn_str = """
    reaction class: addition
    forward TS atoms:
        1: {symbol: F, implicit_hydrogen_valence: 0, stereo_parity: null}
        2: {symbol: C, implicit_hydrogen_valence: 0, stereo_parity: null}
        3: {symbol: C, implicit_hydrogen_valence: 0, stereo_parity: null}
        4: {symbol: F, implicit_hydrogen_valence: 0, stereo_parity: null}
        5: {symbol: H, implicit_hydrogen_valence: 0, stereo_parity: null}
        6: {symbol: H, implicit_hydrogen_valence: 0, stereo_parity: null}
        7: {symbol: O, implicit_hydrogen_valence: 0, stereo_parity: null}
        8: {symbol: H, implicit_hydrogen_valence: 0, stereo_parity: null}
    forward TS bonds:
        1-2: {order: 1, stereo_parity: null}
        2-3: {order: 1, stereo_parity: true}
        2-5: {order: 1, stereo_parity: null}
        2-7: {order: 0.1, stereo_parity: null}
        3-4: {order: 1, stereo_parity: null}
        3-6: {order: 1, stereo_parity: null}
        7-8: {order: 1, stereo_parity: null}
    reactants keys:
    - [1, 2, 3, 4, 5, 6]
    - [7, 8]
    backward TS atoms:
        1: {symbol: F, implicit_hydrogen_valence: 0, stereo_parity: null}
        2: {symbol: C, implicit_hydrogen_valence: 0, stereo_parity: null}
        3: {symbol: H, implicit_hydrogen_valence: 0, stereo_parity: null}
        4: {symbol: C, implicit_hydrogen_valence: 0, stereo_parity: false}
        5: {symbol: H, implicit_hydrogen_valence: 0, stereo_parity: null}
        6: {symbol: O, implicit_hydrogen_valence: 0, stereo_parity: null}
        7: {symbol: F, implicit_hydrogen_valence: 0, stereo_parity: null}
        8: {symbol: H, implicit_hydrogen_valence: 0, stereo_parity: null}
    backward TS bonds:
        1-2: {order: 1, stereo_parity: null}
        2-3: {order: 1, stereo_parity: null}
        2-4: {order: 1, stereo_parity: null}
        4-5: {order: 1, stereo_parity: null}
        4-6: {order: 0.9, stereo_parity: null}
        4-7: {order: 1, stereo_parity: null}
        6-8: {order: 1, stereo_parity: null}
    products keys:
    - [1, 2, 3, 4, 5, 6, 7, 8]
    """
    rxn = reac.from_old_string(old_rxn_str, stereo=True)
    assert rxn == reac.from_data(
        cla="addition",
        rcts_keys=((0, 1, 2, 3, 4, 5), (6, 7)),
        prds_keys=((3, 2, 5, 1, 4, 6, 0, 7),),
        tsg=(
            {
                0: ("F", 0, None),
                1: ("C", 0, False),
                2: ("C", 0, None),
                3: ("F", 0, None),
                4: ("H", 0, None),
                5: ("H", 0, None),
                6: ("O", 0, None),
                7: ("H", 0, None),
            },
            {
                frozenset({0, 1}): (1, None),
                frozenset({1, 2}): (1, True),
                frozenset({1, 4}): (1, None),
                frozenset({1, 6}): (0.1, None),
                frozenset({2, 3}): (1, None),
                frozenset({2, 5}): (1, None),
                frozenset({6, 7}): (1, None),
            },
        ),
    )


def test__end_to_end():
    """Test reac.ts_geometry"""

    def _test(rct_smis, prd_smis):
        print("Testing ts_geometry()")
        print(f"{'.'.join(rct_smis)}>>{'.'.join(prd_smis)}")

        # 1. generate reagent geometries and graphs
        inp_rct_geos = tuple(map(smiles.geometry, rct_smis))
        inp_prd_geos = tuple(map(smiles.geometry, prd_smis))
        inp_rct_gras = tuple(map(geom.graph, inp_rct_geos))
        inp_prd_gras = tuple(map(geom.graph, inp_prd_geos))

        # 2. find reactions
        rxns = reac.find(inp_rct_gras, inp_prd_gras, stereo=True)
        rxn, *_ = rxns  # select the first one for testing

        # 3. add geometry structures
        grxn = reac.with_structures(rxn, "geom")

        # 4. add z-matrix structures
        zrxn = reac.with_structures(rxn, "zmat")

        # 5. tests
        #   (a.) check that the graphs match the input graphs
        rct_gras = reac.reactant_graphs(rxn)
        prd_gras = reac.product_graphs(rxn)
        print(f"\n{rct_gras}\n == ? \n{inp_rct_gras}\n")
        assert rct_gras == inp_rct_gras
        print(f"\n{prd_gras}\n == ? \n{inp_prd_gras}\n")
        assert prd_gras == inp_prd_gras

        #   (b.) check that the geometry structures match the reaction graphs
        tsg = reac.ts_graph(grxn)
        ts_geo = reac.ts_structure(grxn)
        rct_geos = reac.reactant_structures(grxn)
        prd_geos = reac.product_structures(grxn)

        print(f"\n{tsg}\n geometry matches ? \n{ts_geo}\n")
        assert graph.geometry_matches(tsg, ts_geo)

        assert len(rct_gras) == len(rct_geos)
        print("Checking reactant geometries....")
        for gra, geo in zip(rct_gras, rct_geos):
            print(f"\n{gra}\n geometry matches ? \n{geo}\n")
            assert graph.geometry_matches(gra, geo)

        assert len(prd_gras) == len(prd_geos)
        print("Checking reactant geometries....")
        for gra, geo in zip(prd_gras, prd_geos):
            print(f"\n{gra}\n geometry matches ? \n{geo}\n")
            assert graph.geometry_matches(gra, geo)

        #   (b.) check that the geometry structures match the reaction graphs
        ztsg = reac.ts_graph(zrxn)
        ts_zma = reac.ts_structure(zrxn)
        rct_zmas = reac.reactant_structures(zrxn)
        prd_zmas = reac.product_structures(zrxn)
        rct_zgras = reac.reactant_graphs(zrxn)
        prd_zgras = reac.product_graphs(zrxn)

        print(f"\n{ztsg}\n z-matrix matches ? \n{ts_zma}\n")
        assert graph.zmatrix_matches(ztsg, ts_zma)

        assert len(rct_zgras) == len(rct_zmas)
        print("Checking reactant z-matrices....")
        for gra, zma in zip(rct_zgras, rct_zmas):
            print(f"\n{gra}\n z-matrix matches ? \n{zma}\n")
            assert graph.zmatrix_matches(gra, zma)

        assert len(prd_zgras) == len(prd_zmas)
        print("Checking reactant z-matrices....")
        for gra, zma in zip(prd_zgras, prd_zmas):
            print(f"\n{gra}\n z-matrix matches ? \n{zma}\n")
            assert graph.zmatrix_matches(gra, zma)


    # UNIMOLECULAR
    # hydrogen migration
    _test(["CCCO[O]"], ["[CH2]CCOO"])
    # hydrogen migration (2TS)
    _test(["CCC[CH2]"], ["CC[CH]C"])
    # beta scission (stereo-specific)
    _test(["F[CH][C@H](O)F"], [r"F/C=C\F", "[OH]"])
    # ring-forming scission (FIXED)
    _test(["[CH2]CCCOO"], ["C1CCCO1", "[OH]"])
    # elimination
    _test(["CCCCO[O]"], ["CCC=C", "O[O]"])
    # elimination (HONO)
    _test(["CCCON(=O)=O"], ["CCC=O", "N(=O)O"])
    # BIMOLECULAR
    # hydrogen abstraction
    _test(["CCO", "[CH3]"], ["[CH2]CO", "C"])
    # hydrogen abstraction (sigma)
    _test(["CCO", "C#[C]"], ["CC[O]", "C#C"])
    # hydrogen abstraction (radical radical)
    _test(["CCC", "[H]"], ["CC[CH2]", "[HH]"])
    # addition
    _test(["CC[CH2]", "[O][O]"], ["CCCO[O]"])
    # addition (H + H => H2)
    _test(["[H]", "[H]"], ["[H][H]"])
    # addition (stereo-specific)
    _test([r"F/C=C\F", "[OH]"], ["F[CH][C@H](O)F"])
    # addition (stereo-specific with ring)
    _test(["C1C=C1", "[OH]"], ["C1[CH][C@H]1(O)"])
    # addition (vinyl radical)
    _test([r"F\N=[C]/F", "[C]#C"], [r"F\N=C(C#C)/F"])
    # addition (vinyl and sigma radicals)
    _test(["FC=[N]", "[C]#C"], [r"F/C=N\C#C"])
    # addition (two vinyl radicals) (FIXED)
    _test([r"F/C=[C]/[H]", r"[H]/[C]=C/F"], [r"F/C=C\C=C/F"])
    # addition (case 2)
    _test(["C=CCCCCCC", "[CH2]C"], ["CCC[CH]CCCCCC"])
    # addition (radical radical 1)
    _test(["CC[CH2]", "[H]"], ["CCC"])
    # addition (radical radical 2) (FIXED)
    _test(["[H]", "[OH]"], ["O"])
    # addition (radical radical 3)
    _test(["[CH3]", "[OH]"], ["CO"])
    # addition (isc??)
    _test(["N#N", "[O]"], ["[N-]=[N+]=O"])
    # substitution (Sn2) (FIXED)
    _test(["[C@H](O)(C)F", "[Cl]"], ["[C@@H](O)(C)Cl", "[F]"])
    # substitution (FIXED)
    _test(["CO", "[CH2]C"], ["CCC", "[OH]"])
    # insertion
    _test(["CCC=C", "O[O]"], ["CCCCO[O]"])
    # insertion (HONO)
    _test(["CCC=O", "N(=O)O"], ["CCCON(=O)=O"])


if __name__ == "__main__":
    # test__reactant_graphs()
    # test__expand_stereo()
    # test__expand_stereo_for_reaction()
    # test__from_old_string()
    test__end_to_end()
