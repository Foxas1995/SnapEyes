# -*- coding: utf-8 -*-
"""The plate library as the engines read it: BAKED OFFLINE by scripts/bake_plates_registry.py from the design rounds' registries, never
edited by hand, never fitted, scanned or written at run time (a function's folder is read-only). api/_lib/styles/plates.py is the only
reader. JSON inside Python, as styles_registry.py is: ASCII, double quotes, 1 and 0, [] and {} for nothing, the literal ends the file.

  PLATES_REGISTRY_SCHEMA   1
  PLATES_VERSION           the version of the library (the same number as styles_registry.PLATES_VERSION: a build check compares them)
  DEPENDENCIES_MIB         the Linux wheels of requirements.txt in MiB (suites/baseline.md): added to the bytes of api/ by the build check of the
                           function size (scripts/check_styles.mjs, item 9). Replaced by the measured figure when V1 has one
  atlas                    {chips, drops: {file, bytes, sha256}}: the two sprite atlases in api/_assets/atlas/
  families                 {family: {store4k, release1, source}}: store4k 1 when the family's 4K files go to private storage (the collision
                           plates are used at 1K only), release1 1 when a style of the first release needs them
  plates                   {id: {family, since, until, usable, mono, kind, variables, score, void [cx, cy, r0], void_diam, strong_angle,
                           strength, k1 {file, bytes, sha256, px}, k4 {file, bytes, sha256, px}, fit, crisp, extra}}
    since / until          the plates version a plate arrived in, and 0 or the first version that ignores it: the library is append-only, a
                           plate added later never changes the pick of an older version, a retired plate keeps its record
    usable                 1 when an engine may pick it; 0 keeps the record and ships no file (the v2 flames, the soft spirals, the vetoed
                           milky ways, the collision plates that fail the accept rules)
    k1                     the 1024 px file in the bundle: api/_assets/plates/<family>/<file>
    k4                     the 4096 px file in private storage: plates/v1/<family>/<file> (empty: none, or not read at 4K)
"""
PLATES_REGISTRY_SCHEMA = 1
PLATES_VERSION = 1
DEPENDENCIES_MIB = 126
PLATES_REGISTRY = {
 "atlas": {
  "chips": {
   "bytes": 3806278,
   "file": "chips.npz",
   "sha256": "3ca24613c92d963cfb5921af19f62cfcd1acf42daa7af715f65d26a74625b395"
  },
  "drops": {
   "bytes": 3371063,
   "file": "drops.npz",
   "sha256": "83b41b880ef869843e3ce853eab0e80a3fbb000dae70ab4e72c6b5062a658767"
  }
 },
 "families": {
  "P-CX-JET": {
   "release1": 0,
   "source": "cx",
   "store4k": 0
  },
  "P-CX-RIVER": {
   "release1": 0,
   "source": "cx",
   "store4k": 0
  },
  "P-DN-SPIRAL": {
   "release1": 1,
   "source": "y2",
   "store4k": 1
  },
  "P-EL-FLAME": {
   "release1": 0,
   "source": "y2",
   "store4k": 1
  },
  "P-SN-CLOUD": {
   "release1": 1,
   "source": "y2",
   "store4k": 1
  },
  "P-SP-CROWN": {
   "release1": 1,
   "source": "y2",
   "store4k": 1
  },
  "P-UV-DUST": {
   "release1": 1,
   "source": "uv",
   "store4k": 1
  },
  "P-UV-MILKY": {
   "release1": 0,
   "source": "uv",
   "store4k": 1
  }
 },
 "plates": {
  "P-CX-JET__medium_left_b60__flash1K__t0": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.7105220328572195,
    "black": 0.6776123046875,
    "fam": "JET",
    "glare": 0.0019454560242593288,
    "half": 0.4133774533539132,
    "reach60": 0.5620861790659468,
    "reach90": 0.7090990171146133,
    "side": 1024,
    "strong_cw": 0,
    "strong_share": 0.5541849139833804,
    "sx": 0.49039946583955935,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__medium_left_b60__pro4K__t0": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.8053496361258434,
    "black": 0.6398706436157227,
    "fam": "JET",
    "glare": 0.0012205797247588634,
    "half": 0.6561248577921228,
    "reach60": 0.5935977328311426,
    "reach90": 0.7612389225403151,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.5063367287253224,
    "sx": 0.5019314090780012,
    "sy": 0.9990234375
   },
   "k1": {
    "bytes": 414795,
    "file": "P-CX-JET__medium_left_b60__pro4K__t0.png",
    "px": 1024,
    "sha256": "6f86f8f404e1ca3a06696e3461cc126de8ce78563241c8538ff3f14451dc1b9c"
   },
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-JET__medium_left_b60__pro4K__t1": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.8768831134246766,
    "black": 0.6567306518554688,
    "fam": "JET",
    "glare": 0.008129938505589962,
    "half": 0.44537252795715787,
    "reach60": 0.6388499889326733,
    "reach90": 0.7949665136757466,
    "side": 4096,
    "strong_cw": 0,
    "strong_share": 0.5860988822834239,
    "sx": 0.5936097873011253,
    "sy": 0.9990234375
   },
   "k1": {
    "bytes": 376208,
    "file": "P-CX-JET__medium_left_b60__pro4K__t1.png",
    "px": 1024,
    "sha256": "531b53e8d7bce66186289c39e561c3a7353b9673eaecb329a7b8fab878fb00e4"
   },
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-JET__medium_left_b60__pro4K__t2": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.7152344824778112,
    "black": 0.6641502380371094,
    "fam": "JET",
    "glare": 0.0016410648822784424,
    "half": 0.5726943789512018,
    "reach60": 0.6033218284823207,
    "reach90": 0.743861397094679,
    "side": 4096,
    "strong_cw": 0,
    "strong_share": 0.5443580892052293,
    "sx": 0.46544218440798163,
    "sy": 0.9990234375
   },
   "k1": {
    "bytes": 374274,
    "file": "P-CX-JET__medium_left_b60__pro4K__t2.png",
    "px": 1024,
    "sha256": "72d449e99c056df3853a0de4945719dc9e508d95b4096f6f347485216c78cb7d"
   },
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-JET__medium_left_b75__pro4K__t0": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.8984743328058016,
    "black": 0.4758434295654297,
    "fam": "JET",
    "glare": 0.6147570013999939,
    "half": 0.3446017290523429,
    "reach60": 0.6597937635376541,
    "reach90": 0.9511666903981822,
    "side": 4096,
    "strong_cw": 0,
    "strong_share": 0.5283040899734361,
    "sx": 0.49652205907859215,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__medium_left_b75__pro4K__t1": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.7196642343079973,
    "black": 0.6205997467041016,
    "fam": "JET",
    "glare": 0.6004486680030823,
    "half": 0.3789785146519762,
    "reach60": 0.6777492952381341,
    "reach90": 0.9676444288494332,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.6780198528355904,
    "sx": 0.4283252506538797,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__medium_left_b75__pro4K__t2": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.7014703674720868,
    "black": 0.6109809875488281,
    "fam": "JET",
    "glare": 0.0033124517649412155,
    "half": 0.6032078954553093,
    "reach60": 0.6001991676994742,
    "reach90": 0.750992976947239,
    "side": 4096,
    "strong_cw": 0,
    "strong_share": 0.5232597667455439,
    "sx": 0.4500420491700201,
    "sy": 0.9990234375
   },
   "k1": {
    "bytes": 414918,
    "file": "P-CX-JET__medium_left_b75__pro4K__t2.png",
    "px": 1024,
    "sha256": "1b591ac4803e08163efb20b33f8952d4d4912cc930ceaa3846c024aee834f470"
   },
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-JET__medium_right_b60__flash1K__t0": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.2811655299489475,
    "black": 0.6385564804077148,
    "fam": "JET",
    "glare": 0.0017524684080854058,
    "half": 0.6669441513942962,
    "reach60": 0.5251257059648905,
    "reach90": 0.6964750572685194,
    "side": 1024,
    "strong_cw": 1,
    "strong_share": 0.5152602598470792,
    "sx": 0.5038571019468819,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__medium_right_b60__pro4K__t0": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.3465734328235939,
    "black": 0.7260932922363281,
    "fam": "JET",
    "glare": 0.0006518358713947237,
    "half": 0.5214197234783717,
    "reach60": 0.5147865567983902,
    "reach90": 0.6621173566816813,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.5128760981740742,
    "sx": 0.49326691397825306,
    "sy": 0.9990234375
   },
   "k1": {
    "bytes": 328919,
    "file": "P-CX-JET__medium_right_b60__pro4K__t0.png",
    "px": 1024,
    "sha256": "01502abcfcc66c34b744d18d7879ee2edcc0f46e26b9cc9431259919b5ab2c1a"
   },
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-JET__medium_right_b60__pro4K__t1": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.6438505614695018,
    "black": 0.4868478775024414,
    "fam": "JET",
    "glare": 0.26959028840065,
    "half": 0.5595039424144708,
    "reach60": 0.5795874238208854,
    "reach90": 0.7452405928445082,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.52348651166676,
    "sx": 0.5000698412919454,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__medium_right_b60__pro4K__t2": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.4054766610973892,
    "black": 0.659454345703125,
    "fam": "JET",
    "glare": 0.000332870171405375,
    "half": 0.5195757529799856,
    "reach60": 0.48907605971227025,
    "reach90": 0.6391555066896445,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.5495562774896691,
    "sx": 0.4955303961912977,
    "sy": 0.9990234375
   },
   "k1": {
    "bytes": 408516,
    "file": "P-CX-JET__medium_right_b60__pro4K__t2.png",
    "px": 1024,
    "sha256": "2a5f8f5063313d81b345cb54272ae6744a4f7e543429564c7e388f0b4105288e"
   },
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-JET__medium_right_b75__pro4K__t0": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.5570905843200777,
    "black": 0.6064929962158203,
    "fam": "JET",
    "glare": 0.00024106702767312527,
    "half": 0.5626037410473139,
    "reach60": 0.5693964325793388,
    "reach90": 0.7220595768054784,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.5481309125408761,
    "sx": 0.5800598714953272,
    "sy": 0.9990234375
   },
   "k1": {
    "bytes": 351727,
    "file": "P-CX-JET__medium_right_b75__pro4K__t0.png",
    "px": 1024,
    "sha256": "0a9773fbd5e7c3aa77ffc3bf07dfebc842062e069b97cd406313777fa09966dc"
   },
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-JET__medium_right_b75__pro4K__t1": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.3628869688843999,
    "black": 0.7225580215454102,
    "fam": "JET",
    "glare": 0.0002792624873109162,
    "half": 0.7014510677058392,
    "reach60": 0.4852790402289212,
    "reach90": 0.6818248148253051,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.5011039574272801,
    "sx": 0.4933186948140152,
    "sy": 0.9990234375
   },
   "k1": {
    "bytes": 363024,
    "file": "P-CX-JET__medium_right_b75__pro4K__t1.png",
    "px": 1024,
    "sha256": "d375fdda46347cc4889a2d8bf4054af8fce289053216da7bc8dd0b1f88b122af"
   },
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-JET__medium_right_b75__pro4K__t2": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.4933299854668372,
    "black": 0.6703176498413086,
    "fam": "JET",
    "glare": 0.0037104885559529066,
    "half": 0.4723805425456278,
    "reach60": 0.5915337695921288,
    "reach90": 0.7068232808062554,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.5027691619906418,
    "sx": 0.5394382422977423,
    "sy": 0.9990234375
   },
   "k1": {
    "bytes": 367558,
    "file": "P-CX-JET__medium_right_b75__pro4K__t2.png",
    "px": 1024,
    "sha256": "c7137e16e0a122d3ed702d885932dc039a1c138d95fab2684d5886e5f7304ffd"
   },
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-JET__narrow_left_b60__flash1K__t0": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.7228413649002277,
    "black": 0.6741085052490234,
    "fam": "JET",
    "glare": 0.0019429431995376945,
    "half": 0.514757638410865,
    "reach60": 0.570917913431922,
    "reach90": 0.7176445684572755,
    "side": 1024,
    "strong_cw": 0,
    "strong_share": 0.5686916399033726,
    "sx": 0.5081989222554544,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__narrow_left_b60__pro4K__t0": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.9105912949278594,
    "black": 0.35340023040771484,
    "fam": "JET",
    "glare": 0.6122874021530151,
    "half": 0.6478663470083652,
    "reach60": 0.670786404332905,
    "reach90": 0.932455009699455,
    "side": 4096,
    "strong_cw": 0,
    "strong_share": 0.5209928643072697,
    "sx": 0.5137504130025039,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__narrow_left_b60__pro4K__t1": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.7616837099312352,
    "black": 0.35400867462158203,
    "fam": "JET",
    "glare": 0.21119831502437592,
    "half": 0.72529171598294,
    "reach60": 0.6251541695293436,
    "reach90": 0.8291567925424449,
    "side": 4096,
    "strong_cw": 0,
    "strong_share": 0.5356413381627605,
    "sx": 0.4779907692123811,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__narrow_left_b60__pro4K__t2": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.6171127559388876,
    "black": 0.5951919555664062,
    "fam": "JET",
    "glare": 0.0003087467048317194,
    "half": 0.5825569524668754,
    "reach60": 0.5903692298400055,
    "reach90": 0.7320128841841129,
    "side": 4096,
    "strong_cw": 0,
    "strong_share": 0.5291531072198727,
    "sx": 0.4346179755287418,
    "sy": 0.9990234375
   },
   "k1": {
    "bytes": 395938,
    "file": "P-CX-JET__narrow_left_b60__pro4K__t2.png",
    "px": 1024,
    "sha256": "cefdc7faf02bb188e652f2df219ea910e1d9f7d0665f68a04db6a86a9d2efaa6"
   },
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-JET__narrow_left_b75__pro4K__t0": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.7813291498098298,
    "black": 0.7219867706298828,
    "fam": "JET",
    "glare": 0.0004683970473706722,
    "half": 0.5792062113086223,
    "reach60": 0.513375154279398,
    "reach90": 0.6729664049055917,
    "side": 4096,
    "strong_cw": 0,
    "strong_share": 0.5611620180791181,
    "sx": 0.4885121410955431,
    "sy": 0.9990234375
   },
   "k1": {
    "bytes": 347667,
    "file": "P-CX-JET__narrow_left_b75__pro4K__t0.png",
    "px": 1024,
    "sha256": "14d140553544ff4a7d25e4f9e07b72fa04190083de10c569398507b5ba4e20ca"
   },
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-JET__narrow_left_b75__pro4K__t1": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.5082244109399996,
    "black": 0.6802225112915039,
    "fam": "JET",
    "glare": 0.0004509745631366968,
    "half": 0.5203311707133995,
    "reach60": 0.5496711551789376,
    "reach90": 0.6646928785086594,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.5124058969734573,
    "sx": 0.40590383738902985,
    "sy": 0.9990234375
   },
   "k1": {
    "bytes": 377437,
    "file": "P-CX-JET__narrow_left_b75__pro4K__t1.png",
    "px": 1024,
    "sha256": "472e4309e3948bbc279d9dcdfec6e6252e85e6d31de615b12c664660d06287e4"
   },
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-JET__narrow_left_b75__pro4K__t2": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.536098866628689,
    "black": 0.5176410675048828,
    "fam": "JET",
    "glare": 0.5244377851486206,
    "half": 0.6954943005758065,
    "reach60": 0.5925148612442152,
    "reach90": 0.8821549178140492,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.5437155727699493,
    "sx": 0.3148957840119949,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__narrow_right_b60__flash1K__t0": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.393384899681599,
    "black": 0.6469306945800781,
    "fam": "JET",
    "glare": 0.001736386213451624,
    "half": 0.5429650174655931,
    "reach60": 0.524479487815499,
    "reach90": 0.6930994432972561,
    "side": 1024,
    "strong_cw": 0,
    "strong_share": 0.500694661677871,
    "sx": 0.49678015545898097,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__narrow_right_b60__pro4K__t0": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.6503162487701073,
    "black": 0.4854602813720703,
    "fam": "JET",
    "glare": 0.03012767620384693,
    "half": 0.3192350459867308,
    "reach60": 0.767877223036534,
    "reach90": 0.948778950711954,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.5366093430522906,
    "sx": 0.5037382285077252,
    "sy": 0.9990234375
   },
   "k1": {
    "bytes": 432307,
    "file": "P-CX-JET__narrow_right_b60__pro4K__t0.png",
    "px": 1024,
    "sha256": "9f4f4d44b28eb06b5836a4605926b1a252659b730511d604f988991512b3daf6"
   },
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-JET__narrow_right_b60__pro4K__t1": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.8109573114443605,
    "black": 0.4301300048828125,
    "fam": "JET",
    "glare": 0.4841325879096985,
    "half": 0.6369493906008872,
    "reach60": 0.5869394602187334,
    "reach90": 0.9279822409434068,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.5895481891019072,
    "sx": 0.5003992283349051,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__narrow_right_b60__pro4K__t2": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.464068673618984,
    "black": 0.7980976104736328,
    "fam": "JET",
    "glare": 0.0003435916732996702,
    "half": 0.2639850660148504,
    "reach60": 0.552421328635001,
    "reach90": 0.7037564244050191,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.5695636369356422,
    "sx": 0.4984836638520685,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__narrow_right_b75__pro4K__t0": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.6083760884486633,
    "black": 0.49191761016845703,
    "fam": "JET",
    "glare": 0.025686116889119148,
    "half": 0.3667719368836808,
    "reach60": 0.7315517669642774,
    "reach90": 0.9356837350298475,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.5251768092552077,
    "sx": 0.4978068092207489,
    "sy": 0.9990234375
   },
   "k1": {
    "bytes": 551979,
    "file": "P-CX-JET__narrow_right_b75__pro4K__t0.png",
    "px": 1024,
    "sha256": "6ad5abf76a11ae4227a5072c57374c6adc048cec10b6f3af1245a1f7d84c5cbc"
   },
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-JET__narrow_right_b75__pro4K__t1": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.5406069113651673,
    "black": 0.4143342971801758,
    "fam": "JET",
    "glare": 0.050907351076602936,
    "half": 0.4135625085339192,
    "reach60": 0.6363621097535491,
    "reach90": 0.9041501838553351,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.636967990794845,
    "sx": 0.4968287434464093,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__narrow_right_b75__pro4K__t2": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.4325469629676115,
    "black": 0.42803955078125,
    "fam": "JET",
    "glare": 0.034819189459085464,
    "half": 0.38450444274835727,
    "reach60": 0.6280289461150994,
    "reach90": 0.8150680559259253,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.5914435736080085,
    "sx": 0.4756355370328006,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__wide_left_b60__flash1K__t0": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.8494145300154887,
    "black": 0.5821552276611328,
    "fam": "JET",
    "glare": 0.001777932164259255,
    "half": 0.5922753517559336,
    "reach60": 0.6126547810201692,
    "reach90": 0.7737219782113052,
    "side": 1024,
    "strong_cw": 0,
    "strong_share": 0.5363240864282997,
    "sx": 0.5064024139559501,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__wide_left_b60__pro4K__t0": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.6820183923887693,
    "black": 0.6045866012573242,
    "fam": "JET",
    "glare": 0.001997388433665037,
    "half": 0.41264160333338573,
    "reach60": 0.5985058445201846,
    "reach90": 0.7091733653873195,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.53050104822833,
    "sx": 0.48225076375049997,
    "sy": 0.9990234375
   },
   "k1": {
    "bytes": 421003,
    "file": "P-CX-JET__wide_left_b60__pro4K__t0.png",
    "px": 1024,
    "sha256": "038a11389ea1bd1c27bd73121e2187b95728a43425036a5339e2aedbf89f0bdb"
   },
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-JET__wide_left_b60__pro4K__t1": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.8132893759753497,
    "black": 0.6943244934082031,
    "fam": "JET",
    "glare": 0.004923362284898758,
    "half": 0.6997262444203436,
    "reach60": 0.5599649528436429,
    "reach90": 0.7488389508142685,
    "side": 4096,
    "strong_cw": 0,
    "strong_share": 0.5090137703275717,
    "sx": 0.5118730206780924,
    "sy": 0.9990234375
   },
   "k1": {
    "bytes": 387557,
    "file": "P-CX-JET__wide_left_b60__pro4K__t1.png",
    "px": 1024,
    "sha256": "54dafef9140f8c8b497844f40adbafb7c75f3a14ce59befaf20778b4e789f9d3"
   },
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-JET__wide_left_b60__pro4K__t2": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.675559644768604,
    "black": 0.5110721588134766,
    "fam": "JET",
    "glare": 0.36338967084884644,
    "half": 0.5682501395122439,
    "reach60": 0.6539460072399171,
    "reach90": 0.9229606546435428,
    "side": 4096,
    "strong_cw": 0,
    "strong_share": 0.5061035554132306,
    "sx": 0.4229226078892789,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__wide_left_b75__pro4K__t0": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.5491814443841174,
    "black": 0.7916889190673828,
    "fam": "JET",
    "glare": 0.00045918329851701856,
    "half": 0.42826547064884135,
    "reach60": 0.5445838543698784,
    "reach90": 0.64240925315164,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.5202481044095938,
    "sx": 0.41359083532896396,
    "sy": 0.9990234375
   },
   "k1": {
    "bytes": 263729,
    "file": "P-CX-JET__wide_left_b75__pro4K__t0.png",
    "px": 1024,
    "sha256": "e4ea3638fa521d156d5761b8cdb7ab7723942710fddcf8b16a2488351bb885d6"
   },
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-JET__wide_left_b75__pro4K__t1": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.582152636803578,
    "black": 0.4783143997192383,
    "fam": "JET",
    "glare": 0.3306487798690796,
    "half": 0.5332007315736478,
    "reach60": 0.750460564557017,
    "reach90": 0.9433121658481725,
    "side": 4096,
    "strong_cw": 0,
    "strong_share": 0.5429037574668603,
    "sx": 0.4232373377539503,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__wide_left_b75__pro4K__t2": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.8155205968772596,
    "black": 0.3555173873901367,
    "fam": "JET",
    "glare": 0.6215022206306458,
    "half": 0.741041106880862,
    "reach60": 0.6370630614417692,
    "reach90": 0.9271024213227418,
    "side": 4096,
    "strong_cw": 0,
    "strong_share": 0.5258138696942889,
    "sx": 0.4872231508273824,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__wide_right_b60__flash1K__t0": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.3679382983042332,
    "black": 0.6122140884399414,
    "fam": "JET",
    "glare": 0.0018280217191204429,
    "half": 0.5689768023445083,
    "reach60": 0.5690461917384378,
    "reach90": 0.7200232633378746,
    "side": 1024,
    "strong_cw": 1,
    "strong_share": 0.5078320981307727,
    "sx": 0.507003551443556,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__wide_right_b60__pro4K__t0": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.478110237980218,
    "black": 0.5728168487548828,
    "fam": "JET",
    "glare": 0.005982951261103153,
    "half": 0.5312444055655652,
    "reach60": 0.5993554678716612,
    "reach90": 0.7339658960976534,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.5818166067592851,
    "sx": 0.501087790107725,
    "sy": 0.9990234375
   },
   "k1": {
    "bytes": 424878,
    "file": "P-CX-JET__wide_right_b60__pro4K__t0.png",
    "px": 1024,
    "sha256": "5596598204ea7fbb4c553eeb2221a2d931bfd9e16fc0762d4bead97748b4a2b7"
   },
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-JET__wide_right_b60__pro4K__t1": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.4655443156487227,
    "black": 0.42436885833740234,
    "fam": "JET",
    "glare": 0.14574770629405975,
    "half": 0.48299154817788637,
    "reach60": 0.67533778189446,
    "reach90": 0.8742668098902071,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.5929888125418057,
    "sx": 0.49687042513988006,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__wide_right_b60__pro4K__t2": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.5728059721959635,
    "black": 0.35163402557373047,
    "fam": "JET",
    "glare": 0.33629110455513,
    "half": 0.48175018348164134,
    "reach60": 0.764533809300713,
    "reach90": 0.9477130251228035,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.5533747677715032,
    "sx": 0.48748432223285054,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__wide_right_b75__pro4K__t0": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.6362302322240065,
    "black": 0.35039710998535156,
    "fam": "JET",
    "glare": 0.1770574301481247,
    "half": 0.4506082714497994,
    "reach60": 0.703967127650693,
    "reach90": 0.9082503005000367,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.566778900651576,
    "sx": 0.49615537158930717,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-JET__wide_right_b75__pro4K__t1": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.4875009198901494,
    "black": 0.6918745040893555,
    "fam": "JET",
    "glare": 0.004151244647800922,
    "half": 0.5118284374669013,
    "reach60": 0.5523099634498068,
    "reach90": 0.7110313551126751,
    "side": 4096,
    "strong_cw": 0,
    "strong_share": 0.5048353870562731,
    "sx": 0.49472144432945814,
    "sy": 0.9990234375
   },
   "k1": {
    "bytes": 397902,
    "file": "P-CX-JET__wide_right_b75__pro4K__t1.png",
    "px": 1024,
    "sha256": "b770e153271f038de7d7b7867c52c4b615d56064aab5f705d54ef5824f3474f4"
   },
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-JET__wide_right_b75__pro4K__t2": {
   "family": "P-CX-JET",
   "fit": {
    "axis": -1.4309570794034359,
    "black": 0.4081392288208008,
    "fam": "JET",
    "glare": 0.052873075008392334,
    "half": 0.5924976705805145,
    "reach60": 0.5752031779070482,
    "reach90": 0.6920374974478092,
    "side": 4096,
    "strong_cw": 1,
    "strong_share": 0.5731724416878808,
    "sx": 0.4925339767166868,
    "sy": 0.9990234375
   },
   "k1": {},
   "k4": {},
   "kind": "jet",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-RIVER__ll_ur_lower_b60__flash1K__t0": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 2.342708914973504,
    "black": 0.620417594909668,
    "cx": 0.48561531630982396,
    "cy": 0.4875575952455524,
    "fam": "RIVER",
    "glare": 0.41279634833335876,
    "side": 1024,
    "strong_pos": 1,
    "strong_share": 0.5063665560216051,
    "width": 0.1816190838407688
   },
   "k1": {},
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-RIVER__ll_ur_lower_b60__pro4K__t0": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 2.36179995406592,
    "black": 0.5372953414916992,
    "cx": 0.4824875299868257,
    "cy": 0.497011172679736,
    "fam": "RIVER",
    "glare": 0.5269295573234558,
    "side": 4096,
    "strong_pos": 1,
    "strong_share": 0.5008785812592422,
    "width": 0.22730984011469985
   },
   "k1": {
    "bytes": 461398,
    "file": "P-CX-RIVER__ll_ur_lower_b60__pro4K__t0.png",
    "px": 1024,
    "sha256": "469a5e6170a41902d68b9098d912475ef94792c449572ce7401f941e0a440e10"
   },
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-RIVER__ll_ur_lower_b60__pro4K__t1": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 2.3369936631119357,
    "black": 0.5858268737792969,
    "cx": 0.4486605682299399,
    "cy": 0.5023958644354074,
    "fam": "RIVER",
    "glare": 0.5356969237327576,
    "side": 4096,
    "strong_pos": 1,
    "strong_share": 0.5111813651149301,
    "width": 0.25464074274175663
   },
   "k1": {
    "bytes": 474539,
    "file": "P-CX-RIVER__ll_ur_lower_b60__pro4K__t1.png",
    "px": 1024,
    "sha256": "8e87b0451dd1ceb56b90f68149e0603cbad3fa39d7af20726a911a6b44aeeb3a"
   },
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-RIVER__ll_ur_lower_b60__pro4K__t2": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 2.2026854587751012,
    "black": 0.6148900985717773,
    "cx": 0.43263099800606125,
    "cy": 0.5500641189166267,
    "fam": "RIVER",
    "glare": 0.6148101687431335,
    "side": 4096,
    "strong_pos": 1,
    "strong_share": 0.5364591884908018,
    "width": 0.20565097336747573
   },
   "k1": {
    "bytes": 498822,
    "file": "P-CX-RIVER__ll_ur_lower_b60__pro4K__t2.png",
    "px": 1024,
    "sha256": "cc0691cd5c6e729822f7c6cd5e3dfc6d8830bba7bbbbbdceb765f8eec3229265"
   },
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-RIVER__ll_ur_lower_b70__pro4K__t0": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 2.1989694025995807,
    "black": 0.5925140380859375,
    "cx": 0.4483204610665688,
    "cy": 0.4547209754632829,
    "fam": "RIVER",
    "glare": 0.18408875167369843,
    "side": 4096,
    "strong_pos": 0,
    "strong_share": 0.5443906733936389,
    "width": 0.2479629663149032
   },
   "k1": {
    "bytes": 388841,
    "file": "P-CX-RIVER__ll_ur_lower_b70__pro4K__t0.png",
    "px": 1024,
    "sha256": "8491a06404e57fbc8fb22d3e39ceca8a11252c7f3b63b2d98e91b493cf6fecb8"
   },
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-RIVER__ll_ur_lower_b70__pro4K__t1": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 2.3972854902942475,
    "black": 0.38039684295654297,
    "cx": 0.4541733186685896,
    "cy": 0.49855882098976373,
    "fam": "RIVER",
    "glare": 0.5446407198905945,
    "side": 4096,
    "strong_pos": 1,
    "strong_share": 0.5126240652851732,
    "width": 0.25872250397063457
   },
   "k1": {},
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-RIVER__ll_ur_lower_b70__pro4K__t2": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 2.2611173140867895,
    "black": 0.3314380645751953,
    "cx": 0.42877281658637967,
    "cy": 0.4632725735553518,
    "fam": "RIVER",
    "glare": 0.6298191547393799,
    "side": 4096,
    "strong_pos": 0,
    "strong_share": 0.5203482092288773,
    "width": 0.6779562057320768
   },
   "k1": {},
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-RIVER__ll_ur_upper_b60__flash1K__t0": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 2.2938464017391733,
    "black": 0.47785377502441406,
    "cx": 0.4857683193715299,
    "cy": 0.46791282951987273,
    "fam": "RIVER",
    "glare": 0.4869620203971863,
    "side": 1024,
    "strong_pos": 0,
    "strong_share": 0.5082182053469266,
    "width": 0.31728345686423787
   },
   "k1": {},
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-RIVER__ll_ur_upper_b60__pro4K__t0": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 2.257764263581985,
    "black": 0.30270957946777344,
    "cx": 0.4421507490206205,
    "cy": 0.4628005671298766,
    "fam": "RIVER",
    "glare": 0.5298509001731873,
    "side": 4096,
    "strong_pos": 0,
    "strong_share": 0.5156746636958299,
    "width": 0.6775785607478568
   },
   "k1": {},
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-RIVER__ll_ur_upper_b60__pro4K__t1": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 2.4805079190534745,
    "black": 0.586369514465332,
    "cx": 0.4883782031671801,
    "cy": 0.47416341046197236,
    "fam": "RIVER",
    "glare": 0.3665379583835602,
    "side": 4096,
    "strong_pos": 1,
    "strong_share": 0.520069283416023,
    "width": 0.19194467995416742
   },
   "k1": {
    "bytes": 458298,
    "file": "P-CX-RIVER__ll_ur_upper_b60__pro4K__t1.png",
    "px": 1024,
    "sha256": "adec0d25c6ee37c9955818710a3cf9aeb16bdf71ee2228f1284508fd9ac491e9"
   },
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-RIVER__ll_ur_upper_b60__pro4K__t2": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 1.8536012330763112,
    "black": 0.4824371337890625,
    "cx": 0.48369885893520204,
    "cy": 0.45159280301925336,
    "fam": "RIVER",
    "glare": 0.29518312215805054,
    "side": 4096,
    "strong_pos": 1,
    "strong_share": 0.5206233309214099,
    "width": 0.5281887339630464
   },
   "k1": {},
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-RIVER__ll_ur_upper_b70__pro4K__t0": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 2.2751282449526804,
    "black": 0.5270957946777344,
    "cx": 0.46693542694679624,
    "cy": 0.5012974068727263,
    "fam": "RIVER",
    "glare": 0.519698441028595,
    "side": 4096,
    "strong_pos": 1,
    "strong_share": 0.5062882061048495,
    "width": 0.26634176749994437
   },
   "k1": {
    "bytes": 518463,
    "file": "P-CX-RIVER__ll_ur_upper_b70__pro4K__t0.png",
    "px": 1024,
    "sha256": "96928618ca3999bdaa0457283de7ed5c6bc9e62850a947a12664b0a367ba5cfc"
   },
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-RIVER__ll_ur_upper_b70__pro4K__t1": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 2.5066249535249914,
    "black": 0.40477752685546875,
    "cx": 0.43888712355889925,
    "cy": 0.40587537169415977,
    "fam": "RIVER",
    "glare": 0.6157189607620239,
    "side": 4096,
    "strong_pos": 1,
    "strong_share": 0.5512446539938325,
    "width": 0.6281166878208084
   },
   "k1": {},
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-RIVER__ll_ur_upper_b70__pro4K__t2": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 2.3338740335390926,
    "black": 0.4911680221557617,
    "cx": 0.4386058182850566,
    "cy": 0.4937770454662048,
    "fam": "RIVER",
    "glare": 0.5357437133789062,
    "side": 4096,
    "strong_pos": 0,
    "strong_share": 0.5158361499504016,
    "width": 0.6306549399710977
   },
   "k1": {},
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-RIVER__lr_ul_lower_b60__flash1K__t0": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": -2.36806242903732,
    "black": 0.5308446884155273,
    "cx": 0.5368678004887364,
    "cy": 0.5000866254263142,
    "fam": "RIVER",
    "glare": 0.4993620216846466,
    "side": 1024,
    "strong_pos": 1,
    "strong_share": 0.5058048356474627,
    "width": 0.2544039230810101
   },
   "k1": {},
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-RIVER__lr_ul_lower_b60__pro4K__t0": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 0.8338581281498901,
    "black": 0.5193777084350586,
    "cx": 0.4725495742125832,
    "cy": 0.45263478098163507,
    "fam": "RIVER",
    "glare": 0.49835532903671265,
    "side": 4096,
    "strong_pos": 0,
    "strong_share": 0.559191958084708,
    "width": 0.29746020710026744
   },
   "k1": {
    "bytes": 449505,
    "file": "P-CX-RIVER__lr_ul_lower_b60__pro4K__t0.png",
    "px": 1024,
    "sha256": "a897a02ecdd8af45cc7f1c50c618c5ee4c488c0ace5424fecf3a1f3a47e61286"
   },
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-RIVER__lr_ul_lower_b60__pro4K__t1": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": -2.39397171849804,
    "black": 0.6304035186767578,
    "cx": 0.5057167366695899,
    "cy": 0.4166436585685819,
    "fam": "RIVER",
    "glare": 0.5650430917739868,
    "side": 4096,
    "strong_pos": 0,
    "strong_share": 0.5030242689270179,
    "width": 0.2293588518894889
   },
   "k1": {
    "bytes": 455913,
    "file": "P-CX-RIVER__lr_ul_lower_b60__pro4K__t1.png",
    "px": 1024,
    "sha256": "54bda858f300e8ef800570974f61138f6ca46fe4279f3e656e947df97b533e92"
   },
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-RIVER__lr_ul_lower_b60__pro4K__t2": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 0.8027315191782246,
    "black": 0.7365627288818359,
    "cx": 0.524533608907052,
    "cy": 0.5044954362625707,
    "fam": "RIVER",
    "glare": 0.009119837544858456,
    "side": 4096,
    "strong_pos": 1,
    "strong_share": 0.5175095805607461,
    "width": 0.18696672228386396
   },
   "k1": {
    "bytes": 343176,
    "file": "P-CX-RIVER__lr_ul_lower_b60__pro4K__t2.png",
    "px": 1024,
    "sha256": "095c57ae31773fdf0d4f5f9e53926e96da004e2b93c7e8ffb60b5f2aed415e14"
   },
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-RIVER__lr_ul_lower_b70__pro4K__t0": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 0.8904642050894497,
    "black": 0.4412374496459961,
    "cx": 0.4659828855895423,
    "cy": 0.4324065332665551,
    "fam": "RIVER",
    "glare": 0.5831702351570129,
    "side": 4096,
    "strong_pos": 0,
    "strong_share": 0.5508169464242583,
    "width": 0.22980602064537997
   },
   "k1": {
    "bytes": 487252,
    "file": "P-CX-RIVER__lr_ul_lower_b70__pro4K__t0.png",
    "px": 1024,
    "sha256": "2a6b1acabafde955ff378c78f4dc81fa7e73d5a8db0e2cb6262aee94133ffdf2"
   },
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-RIVER__lr_ul_lower_b70__pro4K__t1": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": -2.417793939627935,
    "black": 0.6387929916381836,
    "cx": 0.438412551753845,
    "cy": 0.4421995644501563,
    "fam": "RIVER",
    "glare": 0.5154886841773987,
    "side": 4096,
    "strong_pos": 1,
    "strong_share": 0.5119698466412735,
    "width": 0.17116737759713774
   },
   "k1": {
    "bytes": 417415,
    "file": "P-CX-RIVER__lr_ul_lower_b70__pro4K__t1.png",
    "px": 1024,
    "sha256": "f57e75805a58c9e53295278d42b6c589c3efbcf974131426643027de333cf3cd"
   },
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-RIVER__lr_ul_lower_b70__pro4K__t2": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": -2.3781735461852187,
    "black": 0.6391468048095703,
    "cx": 0.5396956278971676,
    "cy": 0.5139486954327199,
    "fam": "RIVER",
    "glare": 0.45369547605514526,
    "side": 4096,
    "strong_pos": 0,
    "strong_share": 0.516844734329707,
    "width": 0.1893049240073375
   },
   "k1": {
    "bytes": 465170,
    "file": "P-CX-RIVER__lr_ul_lower_b70__pro4K__t2.png",
    "px": 1024,
    "sha256": "13cdae0387d43963fb3b6db65ddc4d71f4db13798174e00824c6e0fc661568ae"
   },
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-RIVER__lr_ul_upper_b60__flash1K__t0": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": -2.367098521628498,
    "black": 0.6016616821289062,
    "cx": 0.4327769516922611,
    "cy": 0.4175051152571216,
    "fam": "RIVER",
    "glare": 0.6152508854866028,
    "side": 1024,
    "strong_pos": 1,
    "strong_share": 0.5130432788450695,
    "width": 0.15871239192183123
   },
   "k1": {},
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-RIVER__lr_ul_upper_b60__pro4K__t0": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 0.8808597609685488,
    "black": 0.45894718170166016,
    "cx": 0.4291612958104685,
    "cy": 0.4068452371786898,
    "fam": "RIVER",
    "glare": 0.7207765579223633,
    "side": 4096,
    "strong_pos": 0,
    "strong_share": 0.512799720233763,
    "width": 0.16098883225936172
   },
   "k1": {
    "bytes": 494559,
    "file": "P-CX-RIVER__lr_ul_upper_b60__pro4K__t0.png",
    "px": 1024,
    "sha256": "8535321c9b930c0dd07267e64e5679237402487776db3f72367677bda547780a"
   },
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-RIVER__lr_ul_upper_b60__pro4K__t1": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 0.9784577772060855,
    "black": 0.6458225250244141,
    "cx": 0.47586719150665546,
    "cy": 0.4562428082202401,
    "fam": "RIVER",
    "glare": 0.2763840854167938,
    "side": 4096,
    "strong_pos": 0,
    "strong_share": 0.5365786096067988,
    "width": 0.3418446487839666
   },
   "k1": {
    "bytes": 454167,
    "file": "P-CX-RIVER__lr_ul_upper_b60__pro4K__t1.png",
    "px": 1024,
    "sha256": "eb7368c9ab7c127f9142b9de57f150fd3ad9201ab015f6db0e648d481eea46a7"
   },
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-RIVER__lr_ul_upper_b60__pro4K__t2": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 0.8909659523281689,
    "black": 0.5397911071777344,
    "cx": 0.4964208940995372,
    "cy": 0.42636203705235887,
    "fam": "RIVER",
    "glare": 0.5132552981376648,
    "side": 4096,
    "strong_pos": 1,
    "strong_share": 0.5041779700926571,
    "width": 0.27818671956891305
   },
   "k1": {
    "bytes": 508057,
    "file": "P-CX-RIVER__lr_ul_upper_b60__pro4K__t2.png",
    "px": 1024,
    "sha256": "978d31c8ab363591549e72e699ce4db0ac91fa3f137ac5d525f5624614bb7a09"
   },
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-RIVER__lr_ul_upper_b70__pro4K__t0": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 1.5333530561793787,
    "black": 0.44904518127441406,
    "cx": 0.48044718895081223,
    "cy": 0.4506926286652454,
    "fam": "RIVER",
    "glare": 0.004634885583072901,
    "side": 4096,
    "strong_pos": 0,
    "strong_share": 0.5188376369741939,
    "width": 0.29506344159071884
   },
   "k1": {},
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-CX-RIVER__lr_ul_upper_b70__pro4K__t1": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 0.9732997285795895,
    "black": 0.5777120590209961,
    "cx": 0.4842911568967664,
    "cy": 0.4231290047902903,
    "fam": "RIVER",
    "glare": 0.45816749334335327,
    "side": 4096,
    "strong_pos": 0,
    "strong_share": 0.5389371733039111,
    "width": 0.2421287759035393
   },
   "k1": {
    "bytes": 473027,
    "file": "P-CX-RIVER__lr_ul_upper_b70__pro4K__t1.png",
    "px": 1024,
    "sha256": "b7bc1fff22b7fda7351fc21f48eb5a4923ceefa19bd68216d717987e9a591358"
   },
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-CX-RIVER__lr_ul_upper_b70__pro4K__t2": {
   "family": "P-CX-RIVER",
   "fit": {
    "axis": 1.1969189516881873,
    "black": 0.5694179534912109,
    "cx": 0.5338636149084753,
    "cy": 0.45181003361821753,
    "fam": "RIVER",
    "glare": 0.0168924480676651,
    "side": 4096,
    "strong_pos": 0,
    "strong_share": 0.531576687248778,
    "width": 0.2084574017070004
   },
   "k1": {},
   "k4": {},
   "kind": "river",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-DN-SPIRAL__arms-three_sense-ccw_wound-loose__v10__pro4K__t2": {
   "crisp": 1,
   "family": "P-DN-SPIRAL",
   "k1": {
    "bytes": 154574,
    "file": "P-DN-SPIRAL__arms-three_sense-ccw_wound-loose__v10__pro4K__t2.webp",
    "px": 1024,
    "sha256": "b3a0376fd21237b1c7d7348fc6e6ccd55075bf4e6a85334e70968c13ea489c79"
   },
   "k4": {
    "bytes": 8022011,
    "file": "P-DN-SPIRAL__arms-three_sense-ccw_wound-loose__v10__pro4K__t2.png",
    "px": 4096,
    "sha256": "ee4a4d36616c8bb7b0663c039fec147ae44523dbb059efed3ec0267e07c654ff"
   },
   "kind": "radial",
   "mono": 1,
   "score": 100.0,
   "since": 1,
   "strength": 0.0312,
   "strong_angle": 287.2,
   "until": 0,
   "usable": 1,
   "variables": {
    "arms": "three",
    "sense": "ccw",
    "wound": "loose"
   },
   "void": [
    0.50006,
    0.49986,
    0.2071
   ],
   "void_diam": 0.4142
  },
  "P-DN-SPIRAL__arms-three_sense-ccw_wound-loose__v12__pro4K__t0": {
   "crisp": 0,
   "family": "P-DN-SPIRAL",
   "k1": {},
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 99.5,
   "since": 1,
   "strength": 0.0104,
   "strong_angle": 232.6,
   "until": 0,
   "usable": 0,
   "variables": {
    "arms": "three",
    "sense": "ccw",
    "wound": "loose"
   },
   "void": [
    0.49997,
    0.49983,
    0.21651
   ],
   "void_diam": 0.433
  },
  "P-DN-SPIRAL__arms-three_sense-cw_wound-tight__v10__pro4K__t0": {
   "crisp": 1,
   "family": "P-DN-SPIRAL",
   "k1": {
    "bytes": 225192,
    "file": "P-DN-SPIRAL__arms-three_sense-cw_wound-tight__v10__pro4K__t0.webp",
    "px": 1024,
    "sha256": "c3d440607cf4417ef42020b3ca5a0f591525f8b17baab68d18a66563b203cdc9"
   },
   "k4": {
    "bytes": 8845238,
    "file": "P-DN-SPIRAL__arms-three_sense-cw_wound-tight__v10__pro4K__t0.png",
    "px": 4096,
    "sha256": "150ee079cf088f08154f916f601cf28d40aba0bbab7a0c3f4d0d5d503c2599bd"
   },
   "kind": "radial",
   "mono": 1,
   "score": 99.5,
   "since": 1,
   "strength": 0.0457,
   "strong_angle": 320.7,
   "until": 0,
   "usable": 1,
   "variables": {
    "arms": "three",
    "sense": "ccw",
    "wound": "tight"
   },
   "void": [
    0.50002,
    0.49993,
    0.23228
   ],
   "void_diam": 0.4646
  },
  "P-DN-SPIRAL__arms-three_sense-cw_wound-tight__v10__pro4K__t2": {
   "crisp": 0,
   "family": "P-DN-SPIRAL",
   "k1": {},
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 83.1,
   "since": 1,
   "strength": 0.053,
   "strong_angle": 354.2,
   "until": 0,
   "usable": 0,
   "variables": {
    "arms": "three",
    "sense": "ccw",
    "wound": "tight"
   },
   "void": [
    0.49972,
    0.49966,
    0.22556
   ],
   "void_diam": 0.4511
  },
  "P-DN-SPIRAL__arms-two_sense-ccw_wound-loose__v10__pro4K__t0": {
   "crisp": 1,
   "family": "P-DN-SPIRAL",
   "k1": {
    "bytes": 170306,
    "file": "P-DN-SPIRAL__arms-two_sense-ccw_wound-loose__v10__pro4K__t0.webp",
    "px": 1024,
    "sha256": "b7deb29a82940d8ea3c132198f9e7bf173d1860bcd8c30a1df8116389e3727aa"
   },
   "k4": {
    "bytes": 7915380,
    "file": "P-DN-SPIRAL__arms-two_sense-ccw_wound-loose__v10__pro4K__t0.png",
    "px": 4096,
    "sha256": "f879ccc0c421d62e2f83293cc0389402b0881e94bee75e0b038773655a26efb3"
   },
   "kind": "radial",
   "mono": 1,
   "score": 100.0,
   "since": 1,
   "strength": 0.0138,
   "strong_angle": 358.3,
   "until": 0,
   "usable": 1,
   "variables": {
    "arms": "two",
    "sense": "ccw",
    "wound": "loose"
   },
   "void": [
    0.49999,
    0.49995,
    0.20773
   ],
   "void_diam": 0.4155
  },
  "P-DN-SPIRAL__arms-two_sense-ccw_wound-tight__v10__pro4K__t1": {
   "crisp": 1,
   "family": "P-DN-SPIRAL",
   "k1": {
    "bytes": 272472,
    "file": "P-DN-SPIRAL__arms-two_sense-ccw_wound-tight__v10__pro4K__t1.webp",
    "px": 1024,
    "sha256": "d64954a6d3e38fa3cdc166a2be32c69dc0d0a2b4c22cb17039dae702543690e4"
   },
   "k4": {
    "bytes": 9592422,
    "file": "P-DN-SPIRAL__arms-two_sense-ccw_wound-tight__v10__pro4K__t1.png",
    "px": 4096,
    "sha256": "9039fb697fd9d3fefd0540dbf82cd4bd4a9f775071931bb3292dbb3d21ff8b49"
   },
   "kind": "radial",
   "mono": 1,
   "score": 98.0,
   "since": 1,
   "strength": 0.0299,
   "strong_angle": 309.5,
   "until": 0,
   "usable": 1,
   "variables": {
    "arms": "two",
    "sense": "ccw",
    "wound": "tight"
   },
   "void": [
    0.49999,
    0.49971,
    0.22933
   ],
   "void_diam": 0.4587
  },
  "P-DN-SPIRAL__arms-two_sense-ccw_wound-tight__v10__pro4K__t2": {
   "crisp": 0,
   "family": "P-DN-SPIRAL",
   "k1": {},
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 84.3,
   "since": 1,
   "strength": 0.0085,
   "strong_angle": 262.5,
   "until": 0,
   "usable": 0,
   "variables": {
    "arms": "two",
    "sense": "ccw",
    "wound": "tight"
   },
   "void": [
    0.50002,
    0.49997,
    0.19376
   ],
   "void_diam": 0.3875
  },
  "P-DN-SPIRAL__arms-two_sense-ccw_wound-tight__v12__pro4K__t1": {
   "crisp": 0,
   "family": "P-DN-SPIRAL",
   "k1": {},
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 73.1,
   "since": 1,
   "strength": 0.0045,
   "strong_angle": 153.1,
   "until": 0,
   "usable": 0,
   "variables": {
    "arms": "two",
    "sense": "ccw",
    "wound": "tight"
   },
   "void": [
    0.49933,
    0.49977,
    0.21823
   ],
   "void_diam": 0.4365
  },
  "P-DN-SPIRAL__arms-two_sense-cw_wound-loose__v10__pro4K__t0": {
   "crisp": 1,
   "family": "P-DN-SPIRAL",
   "k1": {
    "bytes": 233758,
    "file": "P-DN-SPIRAL__arms-two_sense-cw_wound-loose__v10__pro4K__t0.webp",
    "px": 1024,
    "sha256": "24d6d5d1d8b9db9d89a9050b193a2624ff966e1aa22f9fb24e530a58cdf07a8b"
   },
   "k4": {
    "bytes": 8911300,
    "file": "P-DN-SPIRAL__arms-two_sense-cw_wound-loose__v10__pro4K__t0.png",
    "px": 4096,
    "sha256": "99b1352743a20a78f22e98ad224e579a6c295c4ef90f04c8d1b692c236c20ac9"
   },
   "kind": "radial",
   "mono": 1,
   "score": 99.9,
   "since": 1,
   "strength": 0.0064,
   "strong_angle": 186.4,
   "until": 0,
   "usable": 1,
   "variables": {
    "arms": "two",
    "sense": "ccw",
    "wound": "loose"
   },
   "void": [
    0.49999,
    0.49986,
    0.20895
   ],
   "void_diam": 0.4179
  },
  "P-DN-SPIRAL__arms-two_sense-cw_wound-loose__v12__pro4K__t0": {
   "crisp": 1,
   "family": "P-DN-SPIRAL",
   "k1": {
    "bytes": 108264,
    "file": "P-DN-SPIRAL__arms-two_sense-cw_wound-loose__v12__pro4K__t0.webp",
    "px": 1024,
    "sha256": "2a91e79803b76134af6e0a3fd1e657dcc8935084f8e21431237c93f0722d8dec"
   },
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 99.9,
   "since": 1,
   "strength": 0.0083,
   "strong_angle": 196.3,
   "until": 0,
   "usable": 1,
   "variables": {
    "arms": "two",
    "sense": "ccw",
    "wound": "loose"
   },
   "void": [
    0.50003,
    0.49995,
    0.19954
   ],
   "void_diam": 0.3991
  },
  "P-DN-SPIRAL__arms-two_sense-cw_wound-loose__v8__pro4K__t0": {
   "crisp": 1,
   "family": "P-DN-SPIRAL",
   "k1": {
    "bytes": 138654,
    "file": "P-DN-SPIRAL__arms-two_sense-cw_wound-loose__v8__pro4K__t0.webp",
    "px": 1024,
    "sha256": "9309794575219e432fd8a425de58b0bc6c7cf5f73bcf108f1c99becc2acd69dc"
   },
   "k4": {
    "bytes": 7746780,
    "file": "P-DN-SPIRAL__arms-two_sense-cw_wound-loose__v8__pro4K__t0.png",
    "px": 4096,
    "sha256": "9a8a39c3fbdb5d9eb184f4f9a0886af04fae6c73d898c2dda1f6b988a9e28ff4"
   },
   "kind": "radial",
   "mono": 1,
   "score": 100.0,
   "since": 1,
   "strength": 0.0335,
   "strong_angle": 329.6,
   "until": 0,
   "usable": 1,
   "variables": {
    "arms": "two",
    "sense": "ccw",
    "wound": "loose"
   },
   "void": [
    0.50002,
    0.49981,
    0.24942
   ],
   "void_diam": 0.4988
  },
  "P-DN-SPIRAL__arms-two_sense-cw_wound-tight__v10__pro4K__t0_g50": {
   "crisp": 1,
   "family": "P-DN-SPIRAL",
   "k1": {
    "bytes": 207314,
    "file": "P-DN-SPIRAL__arms-two_sense-cw_wound-tight__v10__pro4K__t0_g50.webp",
    "px": 1024,
    "sha256": "834d546290b505de65adde8edf515e66b35909a1b35a387998af4c5311dc303e"
   },
   "k4": {
    "bytes": 8497815,
    "file": "P-DN-SPIRAL__arms-two_sense-cw_wound-tight__v10__pro4K__t0_g50.png",
    "px": 4096,
    "sha256": "ef982f97fd3c56bd5992ab1d45f86aee23d04e1e0e1d57bcf6b7935848e0d202"
   },
   "kind": "radial",
   "mono": 1,
   "score": 99.6,
   "since": 1,
   "strength": 0.0148,
   "strong_angle": 318.6,
   "until": 0,
   "usable": 1,
   "variables": {
    "arms": "two",
    "sense": "ccw",
    "wound": "tight"
   },
   "void": [
    0.50006,
    0.49988,
    0.20645
   ],
   "void_diam": 0.4129
  },
  "P-DN-SPIRAL__arms-two_sense-cw_wound-tight__v11__pro4K__t0": {
   "crisp": 1,
   "family": "P-DN-SPIRAL",
   "k1": {
    "bytes": 174240,
    "file": "P-DN-SPIRAL__arms-two_sense-cw_wound-tight__v11__pro4K__t0.webp",
    "px": 1024,
    "sha256": "70ce85d2d3d54bd0e70731bb568fb11ca99964fb1043c489251422609e86217d"
   },
   "k4": {
    "bytes": 8146298,
    "file": "P-DN-SPIRAL__arms-two_sense-cw_wound-tight__v11__pro4K__t0.png",
    "px": 4096,
    "sha256": "36a8ff62151f6978a903a6f4620b63e99d703f09a43c7cba969788888db4d533"
   },
   "kind": "radial",
   "mono": 1,
   "score": 100.0,
   "since": 1,
   "strength": 0.0429,
   "strong_angle": 308.1,
   "until": 0,
   "usable": 1,
   "variables": {
    "arms": "two",
    "sense": "ccw",
    "wound": "tight"
   },
   "void": [
    0.50005,
    0.4998,
    0.24939
   ],
   "void_diam": 0.4988
  },
  "P-DN-SPIRAL__arms-two_sense-cw_wound-tight__v12__pro4K__t0": {
   "crisp": 0,
   "family": "P-DN-SPIRAL",
   "k1": {},
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 95.9,
   "since": 1,
   "strength": 0.0085,
   "strong_angle": 254.1,
   "until": 0,
   "usable": 0,
   "variables": {
    "arms": "two",
    "sense": "cw",
    "wound": "tight"
   },
   "void": [
    0.49999,
    0.49998,
    0.21832
   ],
   "void_diam": 0.4366
  },
  "P-DN-SPIRAL__arms-two_sense-cw_wound-tight__v12__pro4K__t1": {
   "crisp": 0,
   "family": "P-DN-SPIRAL",
   "k1": {},
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 96.5,
   "since": 1,
   "strength": 0.0068,
   "strong_angle": 279.1,
   "until": 0,
   "usable": 0,
   "variables": {
    "arms": "two",
    "sense": "ccw",
    "wound": "tight"
   },
   "void": [
    0.50006,
    0.50006,
    0.20538
   ],
   "void_diam": 0.4108
  },
  "P-DN-SPIRAL__arms-two_sense-cw_wound-tight__v4__pro4K__t0_g50": {
   "crisp": 1,
   "family": "P-DN-SPIRAL",
   "k1": {
    "bytes": 201776,
    "file": "P-DN-SPIRAL__arms-two_sense-cw_wound-tight__v4__pro4K__t0_g50.webp",
    "px": 1024,
    "sha256": "58ab0c46fee26aff25a12d3ca0b4ae50cf42e63a0c19341535495daea8d32174"
   },
   "k4": {
    "bytes": 8328274,
    "file": "P-DN-SPIRAL__arms-two_sense-cw_wound-tight__v4__pro4K__t0_g50.png",
    "px": 4096,
    "sha256": "e1e750946dee87efb69a9fde09187ba3840fb81d4413a8b2cb61e1992f63f134"
   },
   "kind": "radial",
   "mono": 1,
   "score": 99.9,
   "since": 1,
   "strength": 0.0621,
   "strong_angle": 313.3,
   "until": 0,
   "usable": 1,
   "variables": {
    "arms": "two",
    "sense": "ccw",
    "wound": "tight"
   },
   "void": [
    0.50044,
    0.50033,
    0.24612
   ],
   "void_diam": 0.4922
  },
  "P-EL-FLAME__tongues-12_side-up__v2__pro4K__t0": {
   "family": "P-EL-FLAME",
   "k1": {},
   "k4": {},
   "kind": "radial",
   "mono": 0,
   "score": 90.3,
   "since": 1,
   "strength": 0.731,
   "strong_angle": 88.4,
   "until": 0,
   "usable": 0,
   "variables": {
    "side": "up",
    "tongues": "12"
   },
   "void": [
    0.50357,
    0.56038,
    0.26636
   ],
   "void_diam": 0.5327
  },
  "P-EL-FLAME__tongues-12_side-up__v2__pro4K__t2": {
   "family": "P-EL-FLAME",
   "k1": {},
   "k4": {},
   "kind": "radial",
   "mono": 0,
   "score": 66.6,
   "since": 1,
   "strength": 0.6502,
   "strong_angle": 86.6,
   "until": 0,
   "usable": 0,
   "variables": {
    "side": "up",
    "tongues": "12"
   },
   "void": [
    0.4992,
    0.57668,
    0.24713
   ],
   "void_diam": 0.4943
  },
  "P-EL-FLAME__tongues-12_side-up__v3__pro4K__t1": {
   "family": "P-EL-FLAME",
   "k1": {
    "bytes": 48052,
    "file": "P-EL-FLAME__tongues-12_side-up__v3__pro4K__t1.webp",
    "px": 1024,
    "sha256": "1d7aee5bd3806676f6c1f5b06333e18159074a0c16df249f721ca5c4cf3fb64b"
   },
   "k4": {
    "bytes": 626618,
    "file": "P-EL-FLAME__tongues-12_side-up__v3__pro4K__t1.webp",
    "px": 4096,
    "sha256": "91e37d0a8c6cb0e930b544ab97c7420f8dad3eee04207b58d7c081a82cde52c7"
   },
   "kind": "radial",
   "mono": 0,
   "score": 58.8,
   "since": 1,
   "strength": 0.7223,
   "strong_angle": 88.4,
   "until": 0,
   "usable": 1,
   "variables": {
    "side": "up",
    "tongues": "12"
   },
   "void": [
    0.50187,
    0.56566,
    0.23797
   ],
   "void_diam": 0.4759
  },
  "P-EL-FLAME__tongues-12_side-up_right__v2__pro4K__t0": {
   "family": "P-EL-FLAME",
   "k1": {},
   "k4": {},
   "kind": "radial",
   "mono": 0,
   "score": 95.9,
   "since": 1,
   "strength": 0.7126,
   "strong_angle": 62.0,
   "until": 0,
   "usable": 0,
   "variables": {
    "side": "up_right",
    "tongues": "12"
   },
   "void": [
    0.48974,
    0.57491,
    0.26556
   ],
   "void_diam": 0.5311
  },
  "P-EL-FLAME__tongues-12_side-up_right__v2__pro4K__t2": {
   "family": "P-EL-FLAME",
   "k1": {},
   "k4": {},
   "kind": "radial",
   "mono": 0,
   "score": 81.2,
   "since": 1,
   "strength": 0.8554,
   "strong_angle": 67.3,
   "until": 0,
   "usable": 0,
   "variables": {
    "side": "up_right",
    "tongues": "12"
   },
   "void": [
    0.49047,
    0.57281,
    0.28234
   ],
   "void_diam": 0.5647
  },
  "P-EL-FLAME__tongues-12_side-up_right__v3__pro4K__t0": {
   "family": "P-EL-FLAME",
   "k1": {
    "bytes": 59562,
    "file": "P-EL-FLAME__tongues-12_side-up_right__v3__pro4K__t0.webp",
    "px": 1024,
    "sha256": "bfcfa4e1c2fa7bfce0af23b90041a2fec340e9d92134b9c271bae66a5eebfe15"
   },
   "k4": {
    "bytes": 654126,
    "file": "P-EL-FLAME__tongues-12_side-up_right__v3__pro4K__t0.webp",
    "px": 4096,
    "sha256": "bc2f4746a1fbc6b05ecea7230e4b770094d9654052a923d1fdde5e6c05c62c17"
   },
   "kind": "radial",
   "mono": 0,
   "score": 75.0,
   "since": 1,
   "strength": 0.7577,
   "strong_angle": 70.7,
   "until": 0,
   "usable": 1,
   "variables": {
    "side": "up_right",
    "tongues": "12"
   },
   "void": [
    0.49732,
    0.56287,
    0.26175
   ],
   "void_diam": 0.5235
  },
  "P-EL-FLAME__tongues-12_side-up_right__v3__pro4K__t2": {
   "family": "P-EL-FLAME",
   "k1": {
    "bytes": 46568,
    "file": "P-EL-FLAME__tongues-12_side-up_right__v3__pro4K__t2.webp",
    "px": 1024,
    "sha256": "ae9d9a5bbdf6d29eb0f330e2da32b4387a46a27e827db1f70562cb614e1ec3a9"
   },
   "k4": {
    "bytes": 549920,
    "file": "P-EL-FLAME__tongues-12_side-up_right__v3__pro4K__t2.webp",
    "px": 4096,
    "sha256": "56ae2b79d57b77cfb98c58f4878f112ae0526c0ff33fbb992bf8fe971604940a"
   },
   "kind": "radial",
   "mono": 0,
   "score": 91.1,
   "since": 1,
   "strength": 0.4605,
   "strong_angle": 48.6,
   "until": 0,
   "usable": 1,
   "variables": {
    "side": "up_right",
    "tongues": "12"
   },
   "void": [
    0.50002,
    0.50148,
    0.25903
   ],
   "void_diam": 0.5181
  },
  "P-EL-FLAME__tongues-16_side-up__v2__pro4K__t1": {
   "family": "P-EL-FLAME",
   "k1": {},
   "k4": {},
   "kind": "radial",
   "mono": 0,
   "score": 85.4,
   "since": 1,
   "strength": 0.6587,
   "strong_angle": 91.7,
   "until": 0,
   "usable": 0,
   "variables": {
    "side": "up",
    "tongues": "16"
   },
   "void": [
    0.49567,
    0.5139,
    0.26429
   ],
   "void_diam": 0.5286
  },
  "P-EL-FLAME__tongues-16_side-up__v2__pro4K__t2": {
   "family": "P-EL-FLAME",
   "k1": {},
   "k4": {},
   "kind": "radial",
   "mono": 0,
   "score": 82.5,
   "since": 1,
   "strength": 0.5695,
   "strong_angle": 72.8,
   "until": 0,
   "usable": 0,
   "variables": {
    "side": "up",
    "tongues": "16"
   },
   "void": [
    0.49328,
    0.54193,
    0.25005
   ],
   "void_diam": 0.5001
  },
  "P-EL-FLAME__tongues-16_side-up__v3__pro4K__t1": {
   "family": "P-EL-FLAME",
   "k1": {
    "bytes": 41318,
    "file": "P-EL-FLAME__tongues-16_side-up__v3__pro4K__t1.webp",
    "px": 1024,
    "sha256": "1c2d339864810993d6d6d465297911c3bf01cb42b3b8fd76dd89bd32edf985dc"
   },
   "k4": {
    "bytes": 570194,
    "file": "P-EL-FLAME__tongues-16_side-up__v3__pro4K__t1.webp",
    "px": 4096,
    "sha256": "32f701a0c5ab8dab2c3881f5a09cb0859c3efc147b0da170b1738c5bcc57eb04"
   },
   "kind": "radial",
   "mono": 0,
   "score": 82.0,
   "since": 1,
   "strength": 0.7499,
   "strong_angle": 92.3,
   "until": 0,
   "usable": 1,
   "variables": {
    "side": "up",
    "tongues": "16"
   },
   "void": [
    0.50307,
    0.57005,
    0.24775
   ],
   "void_diam": 0.4955
  },
  "P-EL-FLAME__tongues-16_side-up__v3__pro4K__t2": {
   "family": "P-EL-FLAME",
   "k1": {
    "bytes": 38364,
    "file": "P-EL-FLAME__tongues-16_side-up__v3__pro4K__t2.webp",
    "px": 1024,
    "sha256": "8011872391e051c2e99b583646c5cf2573a29428a04023b0cea2d34c2e313f25"
   },
   "k4": {
    "bytes": 510234,
    "file": "P-EL-FLAME__tongues-16_side-up__v3__pro4K__t2.webp",
    "px": 4096,
    "sha256": "bb4fe7765dcdf082c8c6d54019da3c003c1e40154cb2313f65e73740f4b23e6f"
   },
   "kind": "radial",
   "mono": 0,
   "score": 76.5,
   "since": 1,
   "strength": 0.7676,
   "strong_angle": 91.6,
   "until": 0,
   "usable": 1,
   "variables": {
    "side": "up",
    "tongues": "16"
   },
   "void": [
    0.5013,
    0.58435,
    0.26715
   ],
   "void_diam": 0.5343
  },
  "P-EL-FLAME__tongues-16_side-up_right__v2__pro4K__t1": {
   "family": "P-EL-FLAME",
   "k1": {},
   "k4": {},
   "kind": "radial",
   "mono": 0,
   "score": 93.3,
   "since": 1,
   "strength": 0.6192,
   "strong_angle": 59.1,
   "until": 0,
   "usable": 0,
   "variables": {
    "side": "up_right",
    "tongues": "16"
   },
   "void": [
    0.49658,
    0.50449,
    0.25636
   ],
   "void_diam": 0.5127
  },
  "P-EL-FLAME__tongues-16_side-up_right__v2__pro4K__t2": {
   "family": "P-EL-FLAME",
   "k1": {},
   "k4": {},
   "kind": "radial",
   "mono": 0,
   "score": 78.9,
   "since": 1,
   "strength": 0.7951,
   "strong_angle": 65.7,
   "until": 0,
   "usable": 0,
   "variables": {
    "side": "up_right",
    "tongues": "16"
   },
   "void": [
    0.50178,
    0.53783,
    0.28261
   ],
   "void_diam": 0.5652
  },
  "P-EL-FLAME__tongues-16_side-up_right__v3__pro4K__t1": {
   "family": "P-EL-FLAME",
   "k1": {
    "bytes": 60226,
    "file": "P-EL-FLAME__tongues-16_side-up_right__v3__pro4K__t1.webp",
    "px": 1024,
    "sha256": "151aa4ad0a54496207e7020782edea8ddd02ee77c695a31649800966b9988a1a"
   },
   "k4": {
    "bytes": 688886,
    "file": "P-EL-FLAME__tongues-16_side-up_right__v3__pro4K__t1.webp",
    "px": 4096,
    "sha256": "777434b92ff591d0d21cc865195f4e5d20eb9c7a18d3a46dd2e15120d51fca42"
   },
   "kind": "radial",
   "mono": 0,
   "score": 83.7,
   "since": 1,
   "strength": 0.784,
   "strong_angle": 73.8,
   "until": 0,
   "usable": 1,
   "variables": {
    "side": "up_right",
    "tongues": "16"
   },
   "void": [
    0.49944,
    0.62741,
    0.28418
   ],
   "void_diam": 0.5684
  },
  "P-SN-CLOUD__strong-down_black-15__v5__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 257676,
    "file": "P-SN-CLOUD__strong-down_black-15__v5__pro4K__t1.webp",
    "px": 1024,
    "sha256": "7b887ed41800af2aae96bca73cab7967d8e40c58f4b293201098e38c37fe33f9"
   },
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 98.2,
   "since": 1,
   "strength": 0.1171,
   "strong_angle": 140.2,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "15",
    "strong": "down"
   },
   "void": [
    0.50002,
    0.49975,
    0.22153
   ],
   "void_diam": 0.4431
  },
  "P-SN-CLOUD__strong-down_black-30__v4__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 171616,
    "file": "P-SN-CLOUD__strong-down_black-30__v4__pro4K__t0.webp",
    "px": 1024,
    "sha256": "54616c672d621b632c85b1cf19fcc5a92691436285cde4ac9eb023f3925ede2b"
   },
   "k4": {
    "bytes": 6547651,
    "file": "P-SN-CLOUD__strong-down_black-30__v4__pro4K__t0.png",
    "px": 4096,
    "sha256": "ebbd4860c88e4d52d34fa63841ab3fec56a6a3ab7d7cb4d14eacc791148da5b4"
   },
   "kind": "radial",
   "mono": 1,
   "score": 98.4,
   "since": 1,
   "strength": 0.6694,
   "strong_angle": 259.7,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "30",
    "strong": "down"
   },
   "void": [
    0.50369,
    0.4741,
    0.21558
   ],
   "void_diam": 0.4312
  },
  "P-SN-CLOUD__strong-down_black-30__v4__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 177602,
    "file": "P-SN-CLOUD__strong-down_black-30__v4__pro4K__t1.webp",
    "px": 1024,
    "sha256": "e04cc155d9ce2df88ebb5c66f00f98b44e7ca7401709b398e2f688a8e6949999"
   },
   "k4": {
    "bytes": 6573247,
    "file": "P-SN-CLOUD__strong-down_black-30__v4__pro4K__t1.png",
    "px": 4096,
    "sha256": "ff26b20f847c3407eb3b1ef8e0711d9fcfeb1fe6fa00d43250f8be3a45b0775e"
   },
   "kind": "radial",
   "mono": 1,
   "score": 100.0,
   "since": 1,
   "strength": 0.6006,
   "strong_angle": 278.9,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "30",
    "strong": "down"
   },
   "void": [
    0.50015,
    0.49975,
    0.22494
   ],
   "void_diam": 0.4499
  },
  "P-SN-CLOUD__strong-down_black-45__v6__pro4K__t2": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 230626,
    "file": "P-SN-CLOUD__strong-down_black-45__v6__pro4K__t2.webp",
    "px": 1024,
    "sha256": "3fb53ff433bc5a05b3d8a926aa5f5724040e7b5fa2ceb222bbccf3d7d55b9dc0"
   },
   "k4": {
    "bytes": 7772230,
    "file": "P-SN-CLOUD__strong-down_black-45__v6__pro4K__t2.png",
    "px": 4096,
    "sha256": "9299ff7d18321a311433e01e834bf76eeca38777c97f6ffb0ff52d8191b18216"
   },
   "kind": "radial",
   "mono": 1,
   "score": 96.0,
   "since": 1,
   "strength": 0.493,
   "strong_angle": 264.6,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "45",
    "strong": "down"
   },
   "void": [
    0.49755,
    0.49775,
    0.2371
   ],
   "void_diam": 0.4742
  },
  "P-SN-CLOUD__strong-down_black-60__v4__pro4K__t2": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 163258,
    "file": "P-SN-CLOUD__strong-down_black-60__v4__pro4K__t2.webp",
    "px": 1024,
    "sha256": "292ab8de964447cbca628027b882c15678096389d7cebd8a814ea36b9aba776c"
   },
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 100.0,
   "since": 1,
   "strength": 0.5328,
   "strong_angle": 263.2,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "60",
    "strong": "down"
   },
   "void": [
    0.5,
    0.4999,
    0.19972
   ],
   "void_diam": 0.3994
  },
  "P-SN-CLOUD__strong-left_black-15__v5__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 313312,
    "file": "P-SN-CLOUD__strong-left_black-15__v5__pro4K__t0.webp",
    "px": 1024,
    "sha256": "896972fa15d20a2510c3ea304bb039b34ef2ea256ff3bf1d27cc38b3b1f6e56a"
   },
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 92.6,
   "since": 1,
   "strength": 0.155,
   "strong_angle": 120.4,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "15",
    "strong": "left"
   },
   "void": [
    0.49975,
    0.49919,
    0.19391
   ],
   "void_diam": 0.3878
  },
  "P-SN-CLOUD__strong-left_black-15__v5__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 238670,
    "file": "P-SN-CLOUD__strong-left_black-15__v5__pro4K__t1.webp",
    "px": 1024,
    "sha256": "70148cbb8bb4e693687e60f3022d7a216e722cc7b9c1c58a157c49c96286a2a2"
   },
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 98.3,
   "since": 1,
   "strength": 0.3923,
   "strong_angle": 137.8,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "15",
    "strong": "left"
   },
   "void": [
    0.50015,
    0.49933,
    0.1996
   ],
   "void_diam": 0.3992
  },
  "P-SN-CLOUD__strong-left_black-30__v4__pro4K__t2": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 240900,
    "file": "P-SN-CLOUD__strong-left_black-30__v4__pro4K__t2.webp",
    "px": 1024,
    "sha256": "09ab2544043ea762c3143414ef026f8275d2c86920d96ea0966ceb5895250718"
   },
   "k4": {
    "bytes": 8515427,
    "file": "P-SN-CLOUD__strong-left_black-30__v4__pro4K__t2.png",
    "px": 4096,
    "sha256": "bff5f7b511b5ea9405b237ff4f3296bb2ac6494671bffb062cbba1622c7133c0"
   },
   "kind": "radial",
   "mono": 1,
   "score": 89.9,
   "since": 1,
   "strength": 0.4471,
   "strong_angle": 164.1,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "30",
    "strong": "left"
   },
   "void": [
    0.50126,
    0.49968,
    0.2063
   ],
   "void_diam": 0.4126
  },
  "P-SN-CLOUD__strong-left_black-45__v4__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 207380,
    "file": "P-SN-CLOUD__strong-left_black-45__v4__pro4K__t1.webp",
    "px": 1024,
    "sha256": "d2488f45b4591ac3649d620bb625112370a11c8d46264e06efa6951dd5ad5f7d"
   },
   "k4": {
    "bytes": 7309324,
    "file": "P-SN-CLOUD__strong-left_black-45__v4__pro4K__t1.png",
    "px": 4096,
    "sha256": "9bb56c3a74cb8af52e36e8eb2f55f9da8555fbdd3c7f34801fc44cab0ca3a855"
   },
   "kind": "radial",
   "mono": 1,
   "score": 99.7,
   "since": 1,
   "strength": 0.647,
   "strong_angle": 163.6,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "45",
    "strong": "left"
   },
   "void": [
    0.50111,
    0.49765,
    0.22085
   ],
   "void_diam": 0.4417
  },
  "P-SN-CLOUD__strong-left_black-60__v4__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 195906,
    "file": "P-SN-CLOUD__strong-left_black-60__v4__pro4K__t0.webp",
    "px": 1024,
    "sha256": "dc197600892fb7e56d7e7ae274d8224d279faee9b86293ec16be99ee0f9028cc"
   },
   "k4": {
    "bytes": 6801562,
    "file": "P-SN-CLOUD__strong-left_black-60__v4__pro4K__t0.png",
    "px": 4096,
    "sha256": "311443d4fd2b2a67c271a86ff616a994b7bf958b62aa35e0b2dbfd10b63f6213"
   },
   "kind": "radial",
   "mono": 1,
   "score": 94.1,
   "since": 1,
   "strength": 0.6775,
   "strong_angle": 168.9,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "60",
    "strong": "left"
   },
   "void": [
    0.50805,
    0.49893,
    0.21972
   ],
   "void_diam": 0.4394
  },
  "P-SN-CLOUD__strong-left_black-60__v4__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 216154,
    "file": "P-SN-CLOUD__strong-left_black-60__v4__pro4K__t1.webp",
    "px": 1024,
    "sha256": "1cd38a84fa0ff9b4e93521ef008d58c98ffc66bcbf31457212bb82179e957bf2"
   },
   "k4": {
    "bytes": 8353916,
    "file": "P-SN-CLOUD__strong-left_black-60__v4__pro4K__t1.png",
    "px": 4096,
    "sha256": "518924fcc757d5732352de7ccf647710f3c71b096d80d8680a1788c06b8914c6"
   },
   "kind": "radial",
   "mono": 1,
   "score": 97.8,
   "since": 1,
   "strength": 0.6044,
   "strong_angle": 176.3,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "60",
    "strong": "left"
   },
   "void": [
    0.49963,
    0.49952,
    0.23818
   ],
   "void_diam": 0.4764
  },
  "P-SN-CLOUD__strong-lower_left_black-15__v5__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 250110,
    "file": "P-SN-CLOUD__strong-lower_left_black-15__v5__pro4K__t0.webp",
    "px": 1024,
    "sha256": "fbad82537dee074240f4918ccda7f3d8fb71df3c9df4fd7053176b7bda303baf"
   },
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 100.0,
   "since": 1,
   "strength": 0.2491,
   "strong_angle": 153.9,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "15",
    "strong": "lower_left"
   },
   "void": [
    0.50011,
    0.49972,
    0.22461
   ],
   "void_diam": 0.4492
  },
  "P-SN-CLOUD__strong-lower_left_black-30__v4__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 289250,
    "file": "P-SN-CLOUD__strong-lower_left_black-30__v4__pro4K__t0.webp",
    "px": 1024,
    "sha256": "48d9f99bf4b3d2a198cd43a334fa465fe9dcbd9b50eb318eb75d8b2f0ba2ea6f"
   },
   "k4": {
    "bytes": 9403639,
    "file": "P-SN-CLOUD__strong-lower_left_black-30__v4__pro4K__t0.png",
    "px": 4096,
    "sha256": "69b7a51a9f0c68f7dcd03d4c73aa889b75b094c8100fe545c61c98b9ccd6c083"
   },
   "kind": "radial",
   "mono": 1,
   "score": 99.6,
   "since": 1,
   "strength": 0.3187,
   "strong_angle": 175.4,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "30",
    "strong": "lower_left"
   },
   "void": [
    0.49972,
    0.49957,
    0.20783
   ],
   "void_diam": 0.4157
  },
  "P-SN-CLOUD__strong-lower_left_black-45__v4__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 213602,
    "file": "P-SN-CLOUD__strong-lower_left_black-45__v4__pro4K__t1.webp",
    "px": 1024,
    "sha256": "fbe619ef062af8b093aed442531c0b957ca3d884811a8a0360c87e3201099215"
   },
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 94.8,
   "since": 1,
   "strength": 0.6103,
   "strong_angle": 229.2,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "45",
    "strong": "lower_left"
   },
   "void": [
    0.50088,
    0.4996,
    0.19315
   ],
   "void_diam": 0.3863
  },
  "P-SN-CLOUD__strong-lower_left_black-45__v6__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 203500,
    "file": "P-SN-CLOUD__strong-lower_left_black-45__v6__pro4K__t0.webp",
    "px": 1024,
    "sha256": "9a13b7098f06b2443509165680ad8ef6f3b780c4f0522a787b26b32ed8def072"
   },
   "k4": {
    "bytes": 7661139,
    "file": "P-SN-CLOUD__strong-lower_left_black-45__v6__pro4K__t0.png",
    "px": 4096,
    "sha256": "e5b518d75027eefe6441a6048c243e4be12aef300d3f049e71790cdd4e708506"
   },
   "kind": "radial",
   "mono": 1,
   "score": 95.8,
   "since": 1,
   "strength": 0.4241,
   "strong_angle": 203.6,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "45",
    "strong": "lower_left"
   },
   "void": [
    0.50046,
    0.49992,
    0.22262
   ],
   "void_diam": 0.4452
  },
  "P-SN-CLOUD__strong-lower_left_black-60__v4__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 222736,
    "file": "P-SN-CLOUD__strong-lower_left_black-60__v4__pro4K__t0.webp",
    "px": 1024,
    "sha256": "4d00c840a0442938f5086cba02f2e77205a76773d766c1d8b3194f24577d80c2"
   },
   "k4": {
    "bytes": 8326062,
    "file": "P-SN-CLOUD__strong-lower_left_black-60__v4__pro4K__t0.png",
    "px": 4096,
    "sha256": "26f44ed3a32400d0661f13f26fe9e5e39be292c8a3c5f8c1f435deb8740c780e"
   },
   "kind": "radial",
   "mono": 1,
   "score": 100.0,
   "since": 1,
   "strength": 0.5304,
   "strong_angle": 185.9,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "60",
    "strong": "lower_left"
   },
   "void": [
    0.50015,
    0.49971,
    0.20589
   ],
   "void_diam": 0.4118
  },
  "P-SN-CLOUD__strong-lower_left_black-60__v6__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 243466,
    "file": "P-SN-CLOUD__strong-lower_left_black-60__v6__pro4K__t0.webp",
    "px": 1024,
    "sha256": "95c25e0b7b5983b75ddae8a467b8b7b056556183071a3a7b84e24ba7a3e24d38"
   },
   "k4": {
    "bytes": 7914640,
    "file": "P-SN-CLOUD__strong-lower_left_black-60__v6__pro4K__t0.png",
    "px": 4096,
    "sha256": "31d981d63376fb90c08ad8ff6f177e9d15cedaa72b0af0ba178a55c0fd7eb739"
   },
   "kind": "radial",
   "mono": 1,
   "score": 95.7,
   "since": 1,
   "strength": 0.5142,
   "strong_angle": 189.7,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "60",
    "strong": "lower_left"
   },
   "void": [
    0.49978,
    0.49851,
    0.23084
   ],
   "void_diam": 0.4617
  },
  "P-SN-CLOUD__strong-lower_left_black-60__v6__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 169782,
    "file": "P-SN-CLOUD__strong-lower_left_black-60__v6__pro4K__t1.webp",
    "px": 1024,
    "sha256": "67bb644ca57844e2e5dcb5c2f554b1f78df33eef135289a008dc73d64ed9d7b3"
   },
   "k4": {
    "bytes": 6834798,
    "file": "P-SN-CLOUD__strong-lower_left_black-60__v6__pro4K__t1.png",
    "px": 4096,
    "sha256": "46727942aa4ad2263dcf30ea686127a5cac918bbb2eb66883f0f1023a7555e78"
   },
   "kind": "radial",
   "mono": 1,
   "score": 91.7,
   "since": 1,
   "strength": 0.5467,
   "strong_angle": 217.7,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "60",
    "strong": "lower_left"
   },
   "void": [
    0.50013,
    0.49976,
    0.22133
   ],
   "void_diam": 0.4427
  },
  "P-SN-CLOUD__strong-lower_right_black-30__v4__pro4K__t3": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 261106,
    "file": "P-SN-CLOUD__strong-lower_right_black-30__v4__pro4K__t3.webp",
    "px": 1024,
    "sha256": "e14f405e20b9f2eb1fe13e0a4544582cfaba6e1f7e1141161902f6e13e2bc737"
   },
   "k4": {
    "bytes": 8840544,
    "file": "P-SN-CLOUD__strong-lower_right_black-30__v4__pro4K__t3.png",
    "px": 4096,
    "sha256": "72d55230548df960ecde973fd3c0fb06c5cb3e816b42ec5c241937e65109a473"
   },
   "kind": "radial",
   "mono": 1,
   "score": 91.5,
   "since": 1,
   "strength": 0.3778,
   "strong_angle": 354.4,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "30",
    "strong": "lower_right"
   },
   "void": [
    0.49493,
    0.49572,
    0.2174
   ],
   "void_diam": 0.4348
  },
  "P-SN-CLOUD__strong-lower_right_black-45__v4__pro4K__t5": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 284656,
    "file": "P-SN-CLOUD__strong-lower_right_black-45__v4__pro4K__t5.webp",
    "px": 1024,
    "sha256": "dffa8c95f3d5bcd4ff7c200e3938594eb0763693b5b7fc4909f015302fc14469"
   },
   "k4": {
    "bytes": 8964683,
    "file": "P-SN-CLOUD__strong-lower_right_black-45__v4__pro4K__t5.png",
    "px": 4096,
    "sha256": "6a9677ff972af6a3bf5e24b2a9e047d85e4e7c8468719d2cd17d087230344af3"
   },
   "kind": "radial",
   "mono": 1,
   "score": 95.0,
   "since": 1,
   "strength": 0.3563,
   "strong_angle": 335.7,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "45",
    "strong": "lower_right"
   },
   "void": [
    0.49878,
    0.49432,
    0.22763
   ],
   "void_diam": 0.4553
  },
  "P-SN-CLOUD__strong-lower_right_black-60__v4__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 227988,
    "file": "P-SN-CLOUD__strong-lower_right_black-60__v4__pro4K__t1.webp",
    "px": 1024,
    "sha256": "deeabbd713de2ce605afe09536261a11c3562de77c2f1bcee82bf764f8b82975"
   },
   "k4": {
    "bytes": 8316762,
    "file": "P-SN-CLOUD__strong-lower_right_black-60__v4__pro4K__t1.png",
    "px": 4096,
    "sha256": "6e620fbdb93fa0eb3dbf02820a12abbfb07d60c268bd3d8c032c63b96ace213b"
   },
   "kind": "radial",
   "mono": 1,
   "score": 98.3,
   "since": 1,
   "strength": 0.3869,
   "strong_angle": 338.8,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "60",
    "strong": "lower_right"
   },
   "void": [
    0.5,
    0.49978,
    0.22472
   ],
   "void_diam": 0.4494
  },
  "P-SN-CLOUD__strong-right_black-15__v5__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 238572,
    "file": "P-SN-CLOUD__strong-right_black-15__v5__pro4K__t1.webp",
    "px": 1024,
    "sha256": "b5bf9aece422f06a88974f14d1b0772f1f4379c1dd7851dc6e1259bbbb87b764"
   },
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 92.7,
   "since": 1,
   "strength": 0.1452,
   "strong_angle": 94.2,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "15",
    "strong": "right"
   },
   "void": [
    0.49283,
    0.49907,
    0.18996
   ],
   "void_diam": 0.3799
  },
  "P-SN-CLOUD__strong-right_black-30__v4__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 183216,
    "file": "P-SN-CLOUD__strong-right_black-30__v4__pro4K__t0.webp",
    "px": 1024,
    "sha256": "a033cf47104a31f3606e7ddc3bc82114f1fe071041d3efa1357fe102cac6ef12"
   },
   "k4": {
    "bytes": 6999465,
    "file": "P-SN-CLOUD__strong-right_black-30__v4__pro4K__t0.png",
    "px": 4096,
    "sha256": "5c0d6d16237d8aa0f4f27aa343eca23f08af291e40080fa7319d81d629b7eab5"
   },
   "kind": "radial",
   "mono": 1,
   "score": 92.6,
   "since": 1,
   "strength": 0.5889,
   "strong_angle": 3.6,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "30",
    "strong": "right"
   },
   "void": [
    0.49547,
    0.49603,
    0.24313
   ],
   "void_diam": 0.4863
  },
  "P-SN-CLOUD__strong-right_black-45__v4__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 155548,
    "file": "P-SN-CLOUD__strong-right_black-45__v4__pro4K__t0.webp",
    "px": 1024,
    "sha256": "b441b0048202562b5ec91b71ce5af84940c15840c0a5dc704b3e16472238866f"
   },
   "k4": {
    "bytes": 6536234,
    "file": "P-SN-CLOUD__strong-right_black-45__v4__pro4K__t0.png",
    "px": 4096,
    "sha256": "126304ee5baf72ebbec92603c12f6d08d45712dbdc95072f390e6247b107df99"
   },
   "kind": "radial",
   "mono": 1,
   "score": 97.9,
   "since": 1,
   "strength": 0.6486,
   "strong_angle": 1.8,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "45",
    "strong": "right"
   },
   "void": [
    0.49963,
    0.49238,
    0.22761
   ],
   "void_diam": 0.4552
  },
  "P-SN-CLOUD__strong-right_black-45__v4__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 159042,
    "file": "P-SN-CLOUD__strong-right_black-45__v4__pro4K__t1.webp",
    "px": 1024,
    "sha256": "40a280e6c39c07800c66b9b1c9c2d9e566f29214682c36f194323a4162a30d93"
   },
   "k4": {
    "bytes": 6052932,
    "file": "P-SN-CLOUD__strong-right_black-45__v4__pro4K__t1.png",
    "px": 4096,
    "sha256": "b9bbc1ce6f24ca126ace1d39a63352220f1811b233f30bfc8adbd861eac84efe"
   },
   "kind": "radial",
   "mono": 1,
   "score": 100.0,
   "since": 1,
   "strength": 0.7047,
   "strong_angle": 8.2,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "45",
    "strong": "right"
   },
   "void": [
    0.49967,
    0.49966,
    0.22456
   ],
   "void_diam": 0.4491
  },
  "P-SN-CLOUD__strong-right_black-60__v4__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 177992,
    "file": "P-SN-CLOUD__strong-right_black-60__v4__pro4K__t0.webp",
    "px": 1024,
    "sha256": "4028a66c9a44040ee23f0a7212c94ca526c74b1f29a5db5166819e2e095c64af"
   },
   "k4": {
    "bytes": 6857036,
    "file": "P-SN-CLOUD__strong-right_black-60__v4__pro4K__t0.png",
    "px": 4096,
    "sha256": "2dde8aba66a7f16a66ec4f53d60f66906f3b30453fc6524c28e1a14aea22e41e"
   },
   "kind": "radial",
   "mono": 1,
   "score": 100.0,
   "since": 1,
   "strength": 0.6379,
   "strong_angle": 6.0,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "60",
    "strong": "right"
   },
   "void": [
    0.49591,
    0.50169,
    0.21474
   ],
   "void_diam": 0.4295
  },
  "P-SN-CLOUD__strong-right_black-60__v4__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 256580,
    "file": "P-SN-CLOUD__strong-right_black-60__v4__pro4K__t1.webp",
    "px": 1024,
    "sha256": "68fb7576d322e29ec82e6ceac5ba209ead615eeb135f84bbfa008cafdc5a07ce"
   },
   "k4": {
    "bytes": 8493780,
    "file": "P-SN-CLOUD__strong-right_black-60__v4__pro4K__t1.png",
    "px": 4096,
    "sha256": "b72b3ce844a7730187e234b214753396642d5d5de8ff05f4f06721bc52ed0622"
   },
   "kind": "radial",
   "mono": 1,
   "score": 92.1,
   "since": 1,
   "strength": 0.507,
   "strong_angle": 24.9,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "60",
    "strong": "right"
   },
   "void": [
    0.49854,
    0.50188,
    0.22347
   ],
   "void_diam": 0.4469
  },
  "P-SN-CLOUD__strong-up_black-15__v5__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 237204,
    "file": "P-SN-CLOUD__strong-up_black-15__v5__pro4K__t0.webp",
    "px": 1024,
    "sha256": "a4c63b017d9d09f8e4d7d1759a514b80c89a3eeba7d3c86109656fef9ce09b58"
   },
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 97.9,
   "since": 1,
   "strength": 0.2757,
   "strong_angle": 128.5,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "15",
    "strong": "up"
   },
   "void": [
    0.50362,
    0.50315,
    0.21267
   ],
   "void_diam": 0.4253
  },
  "P-SN-CLOUD__strong-up_black-15__v5__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 233208,
    "file": "P-SN-CLOUD__strong-up_black-15__v5__pro4K__t1.webp",
    "px": 1024,
    "sha256": "8830678af98daf4d4167a9948af601dc92e1e07fb936fdeda37e1e1850172596"
   },
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 99.5,
   "since": 1,
   "strength": 0.3387,
   "strong_angle": 124.4,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "15",
    "strong": "up"
   },
   "void": [
    0.49995,
    0.49988,
    0.22696
   ],
   "void_diam": 0.4539
  },
  "P-SN-CLOUD__strong-up_black-30__v4__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 180358,
    "file": "P-SN-CLOUD__strong-up_black-30__v4__pro4K__t0.webp",
    "px": 1024,
    "sha256": "7163c16b95094a2cbe8c30740bc1d2b722f7c762a726b1a4e5c70dc8915aee45"
   },
   "k4": {
    "bytes": 7125088,
    "file": "P-SN-CLOUD__strong-up_black-30__v4__pro4K__t0.png",
    "px": 4096,
    "sha256": "deecadab9ee393cfe2d74c41c7a0ceecb0a528157a574fe6dd14157ff7eac646"
   },
   "kind": "radial",
   "mono": 1,
   "score": 97.1,
   "since": 1,
   "strength": 0.6074,
   "strong_angle": 103.0,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "30",
    "strong": "up"
   },
   "void": [
    0.50129,
    0.5007,
    0.25088
   ],
   "void_diam": 0.5018
  },
  "P-SN-CLOUD__strong-up_black-30__v4__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 202392,
    "file": "P-SN-CLOUD__strong-up_black-30__v4__pro4K__t1.webp",
    "px": 1024,
    "sha256": "bcacd827500e9c13205197f73b071e479157a93b60bbcd1ddf6cb9087f4d7c83"
   },
   "k4": {
    "bytes": 7201005,
    "file": "P-SN-CLOUD__strong-up_black-30__v4__pro4K__t1.png",
    "px": 4096,
    "sha256": "0e2a556fbf4e15be399994644a1ccbb054d8ed98ed123b36244873a287ed4daf"
   },
   "kind": "radial",
   "mono": 1,
   "score": 98.2,
   "since": 1,
   "strength": 0.6189,
   "strong_angle": 131.4,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "30",
    "strong": "up"
   },
   "void": [
    0.50008,
    0.49959,
    0.20992
   ],
   "void_diam": 0.4198
  },
  "P-SN-CLOUD__strong-up_black-45__v4__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 224706,
    "file": "P-SN-CLOUD__strong-up_black-45__v4__pro4K__t0.webp",
    "px": 1024,
    "sha256": "0b4914b1c305d9ebe9551b2f2ec4fe3a0e7f67d8f35235609e0044ad9585c822"
   },
   "k4": {
    "bytes": 8440444,
    "file": "P-SN-CLOUD__strong-up_black-45__v4__pro4K__t0.png",
    "px": 4096,
    "sha256": "f6bb36e28d4950064060d1c11de9a2470fc182d98eb6fa46b794ac5279d6b475"
   },
   "kind": "radial",
   "mono": 1,
   "score": 95.2,
   "since": 1,
   "strength": 0.5835,
   "strong_angle": 132.3,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "45",
    "strong": "up"
   },
   "void": [
    0.50016,
    0.4998,
    0.20606
   ],
   "void_diam": 0.4121
  },
  "P-SN-CLOUD__strong-up_black-45__v4__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 218918,
    "file": "P-SN-CLOUD__strong-up_black-45__v4__pro4K__t1.webp",
    "px": 1024,
    "sha256": "9faf712196bc519346a2bdcf0a9da6eb2f42fdb64dffd38d3a1e5e2b1c544eb2"
   },
   "k4": {
    "bytes": 8512056,
    "file": "P-SN-CLOUD__strong-up_black-45__v4__pro4K__t1.png",
    "px": 4096,
    "sha256": "dad6a9a785321bade3b896262849338bb4d3edcec4d2d4497af816f555882e40"
   },
   "kind": "radial",
   "mono": 1,
   "score": 100.0,
   "since": 1,
   "strength": 0.5863,
   "strong_angle": 119.6,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "45",
    "strong": "up"
   },
   "void": [
    0.49987,
    0.49976,
    0.20915
   ],
   "void_diam": 0.4183
  },
  "P-SN-CLOUD__strong-up_black-60__v4__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 217762,
    "file": "P-SN-CLOUD__strong-up_black-60__v4__pro4K__t0.webp",
    "px": 1024,
    "sha256": "20f3c770228f7c7e27e15e6c4b4859b904724c0a6d5882cc77aedee4add471c9"
   },
   "k4": {
    "bytes": 7306479,
    "file": "P-SN-CLOUD__strong-up_black-60__v4__pro4K__t0.png",
    "px": 4096,
    "sha256": "f3ae59422a15b88241bf2f15cb6a93c1de8e65af93607433c773134cfbf79cf8"
   },
   "kind": "radial",
   "mono": 1,
   "score": 100.0,
   "since": 1,
   "strength": 0.6273,
   "strong_angle": 103.6,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "60",
    "strong": "up"
   },
   "void": [
    0.50011,
    0.4998,
    0.20089
   ],
   "void_diam": 0.4018
  },
  "P-SN-CLOUD__strong-up_black-60__v4__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 203712,
    "file": "P-SN-CLOUD__strong-up_black-60__v4__pro4K__t1.webp",
    "px": 1024,
    "sha256": "b7c5fac76087a3eb454d6b2d157afd7790342b268c044b0724e13d2c19158898"
   },
   "k4": {
    "bytes": 7438298,
    "file": "P-SN-CLOUD__strong-up_black-60__v4__pro4K__t1.png",
    "px": 4096,
    "sha256": "a487b29408a2907b9ad87b297826e5cb5c88c83f8080617cbf637bf0fd583d09"
   },
   "kind": "radial",
   "mono": 1,
   "score": 98.1,
   "since": 1,
   "strength": 0.6041,
   "strong_angle": 117.4,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "60",
    "strong": "up"
   },
   "void": [
    0.50006,
    0.49899,
    0.2215
   ],
   "void_diam": 0.443
  },
  "P-SN-CLOUD__strong-upper_left_black-15__v5__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 253584,
    "file": "P-SN-CLOUD__strong-upper_left_black-15__v5__pro4K__t1.webp",
    "px": 1024,
    "sha256": "9cddbcbdc357db4c6c765aa0affdc92fc486cee54619941d916f403d2c8f6d38"
   },
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 100.0,
   "since": 1,
   "strength": 0.3923,
   "strong_angle": 138.3,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "15",
    "strong": "upper_left"
   },
   "void": [
    0.49997,
    0.49983,
    0.23602
   ],
   "void_diam": 0.472
  },
  "P-SN-CLOUD__strong-upper_left_black-30__v4__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 225942,
    "file": "P-SN-CLOUD__strong-upper_left_black-30__v4__pro4K__t0.webp",
    "px": 1024,
    "sha256": "66e5ec52806fd43fd8f5aa51cbf1600c69f43067d08127f08a6113232936cdc1"
   },
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 100.0,
   "since": 1,
   "strength": 0.6627,
   "strong_angle": 135.9,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "30",
    "strong": "upper_left"
   },
   "void": [
    0.49988,
    0.49944,
    0.19955
   ],
   "void_diam": 0.3991
  },
  "P-SN-CLOUD__strong-upper_left_black-45__v4__pro4K__t2": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 249754,
    "file": "P-SN-CLOUD__strong-upper_left_black-45__v4__pro4K__t2.webp",
    "px": 1024,
    "sha256": "ca3176cdaf53088dadbe33b92f3d4eac3ba965c75e82e8b02c471e584a6ba04f"
   },
   "k4": {
    "bytes": 8254944,
    "file": "P-SN-CLOUD__strong-upper_left_black-45__v4__pro4K__t2.png",
    "px": 4096,
    "sha256": "33e0128e05f7493892785c1560b47650a261b9e9be1e088f8f3867d04f41037e"
   },
   "kind": "radial",
   "mono": 1,
   "score": 94.4,
   "since": 1,
   "strength": 0.5878,
   "strong_angle": 132.7,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "45",
    "strong": "upper_left"
   },
   "void": [
    0.50011,
    0.49959,
    0.20651
   ],
   "void_diam": 0.413
  },
  "P-SN-CLOUD__strong-upper_left_black-60__v4__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 183736,
    "file": "P-SN-CLOUD__strong-upper_left_black-60__v4__pro4K__t0.webp",
    "px": 1024,
    "sha256": "a69212131aba85fd6d62a44e54cbf0d6ce71a37cb2026032bd763a88b74ccdd7"
   },
   "k4": {
    "bytes": 6702645,
    "file": "P-SN-CLOUD__strong-upper_left_black-60__v4__pro4K__t0.png",
    "px": 4096,
    "sha256": "743c6fe5ef5e32587ce1feabe6009cf3f59c0e5a835a898a35960ade0092c909"
   },
   "kind": "radial",
   "mono": 1,
   "score": 100.0,
   "since": 1,
   "strength": 0.695,
   "strong_angle": 142.1,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "60",
    "strong": "upper_left"
   },
   "void": [
    0.50035,
    0.50009,
    0.22121
   ],
   "void_diam": 0.4424
  },
  "P-SN-CLOUD__strong-upper_left_black-60__v4__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 201906,
    "file": "P-SN-CLOUD__strong-upper_left_black-60__v4__pro4K__t1.webp",
    "px": 1024,
    "sha256": "9f8c5948569ea7350ae94bccf07b9df1461403b10147ce647db3c02b101b48e1"
   },
   "k4": {
    "bytes": 8663480,
    "file": "P-SN-CLOUD__strong-upper_left_black-60__v4__pro4K__t1.png",
    "px": 4096,
    "sha256": "74275f0ece285d787f2023e5bd534af78c0e60f401668cffdc700e67e25588fb"
   },
   "kind": "radial",
   "mono": 1,
   "score": 100.0,
   "since": 1,
   "strength": 0.5494,
   "strong_angle": 140.8,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "60",
    "strong": "upper_left"
   },
   "void": [
    0.49993,
    0.49972,
    0.22844
   ],
   "void_diam": 0.4569
  },
  "P-SN-CLOUD__strong-upper_right_black-15__v5__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 226194,
    "file": "P-SN-CLOUD__strong-upper_right_black-15__v5__pro4K__t0.webp",
    "px": 1024,
    "sha256": "326d697e35dbdae2032f1249b25cd960b65b1c5b72a5c90a39187b486081be4a"
   },
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 97.8,
   "since": 1,
   "strength": 0.3354,
   "strong_angle": 36.6,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "15",
    "strong": "upper_right"
   },
   "void": [
    0.50012,
    0.49933,
    0.20154
   ],
   "void_diam": 0.4031
  },
  "P-SN-CLOUD__strong-upper_right_black-15__v5__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 136864,
    "file": "P-SN-CLOUD__strong-upper_right_black-15__v5__pro4K__t1.webp",
    "px": 1024,
    "sha256": "c4f662fba259f813f5ae795e40ab4519beb9d914c7e1d8b6cb8bdc71cda7e75e"
   },
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 95.2,
   "since": 1,
   "strength": 0.3597,
   "strong_angle": 51.0,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "15",
    "strong": "upper_right"
   },
   "void": [
    0.50019,
    0.49975,
    0.20875
   ],
   "void_diam": 0.4175
  },
  "P-SN-CLOUD__strong-upper_right_black-30__v4__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 178798,
    "file": "P-SN-CLOUD__strong-upper_right_black-30__v4__pro4K__t0.webp",
    "px": 1024,
    "sha256": "f012af062bfded009455504e07addaf03d47c8acb8961186e86d17b73a1ef5a6"
   },
   "k4": {
    "bytes": 6938625,
    "file": "P-SN-CLOUD__strong-upper_right_black-30__v4__pro4K__t0.png",
    "px": 4096,
    "sha256": "176f75ae0e1d58254c49e1c29b05c5872338ec04fcf712fc6af2f484ba9990ad"
   },
   "kind": "radial",
   "mono": 1,
   "score": 100.0,
   "since": 1,
   "strength": 0.7053,
   "strong_angle": 49.3,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "30",
    "strong": "upper_right"
   },
   "void": [
    0.50003,
    0.50012,
    0.22119
   ],
   "void_diam": 0.4424
  },
  "P-SN-CLOUD__strong-upper_right_black-30__v4__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 185572,
    "file": "P-SN-CLOUD__strong-upper_right_black-30__v4__pro4K__t1.webp",
    "px": 1024,
    "sha256": "6ba5f31aed6776dc3c720ce1c100e2b687a19fffc6ddcf6dc7ce57f1f2c022e8"
   },
   "k4": {
    "bytes": 7579607,
    "file": "P-SN-CLOUD__strong-upper_right_black-30__v4__pro4K__t1.png",
    "px": 4096,
    "sha256": "ca31c3e95a8b0fef1a3140c6cd273cf97514662b660e131eb792c026760ab7bd"
   },
   "kind": "radial",
   "mono": 1,
   "score": 99.0,
   "since": 1,
   "strength": 0.487,
   "strong_angle": 48.7,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "30",
    "strong": "upper_right"
   },
   "void": [
    0.50002,
    0.49978,
    0.2401
   ],
   "void_diam": 0.4802
  },
  "P-SN-CLOUD__strong-upper_right_black-45__v4__pro4K__t0": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 105910,
    "file": "P-SN-CLOUD__strong-upper_right_black-45__v4__pro4K__t0.webp",
    "px": 1024,
    "sha256": "c7ae375fe02e55b472c798756d4950aafe044d8ac14ccee989e1b483cea2c12d"
   },
   "k4": {
    "bytes": 5296082,
    "file": "P-SN-CLOUD__strong-upper_right_black-45__v4__pro4K__t0.png",
    "px": 4096,
    "sha256": "7a224221c6413e5c4bc49fff70fb63503dc652888fcf5246dd3f9e98940a0270"
   },
   "kind": "radial",
   "mono": 1,
   "score": 100.0,
   "since": 1,
   "strength": 0.7655,
   "strong_angle": 46.2,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "45",
    "strong": "upper_right"
   },
   "void": [
    0.50001,
    0.4999,
    0.22886
   ],
   "void_diam": 0.4577
  },
  "P-SN-CLOUD__strong-upper_right_black-45__v4__pro4K__t1": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 176104,
    "file": "P-SN-CLOUD__strong-upper_right_black-45__v4__pro4K__t1.webp",
    "px": 1024,
    "sha256": "9d4009fdf0fcee3bea1dbb76ca154b6f2a331220cad22b8362244439fb3b946a"
   },
   "k4": {
    "bytes": 6653771,
    "file": "P-SN-CLOUD__strong-upper_right_black-45__v4__pro4K__t1.png",
    "px": 4096,
    "sha256": "82f2f69fa21fbff3177581a3a4c18633da17ccd4790c7f3f74128921462008ef"
   },
   "kind": "radial",
   "mono": 1,
   "score": 93.9,
   "since": 1,
   "strength": 0.6114,
   "strong_angle": 45.0,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "45",
    "strong": "upper_right"
   },
   "void": [
    0.49989,
    0.50002,
    0.20169
   ],
   "void_diam": 0.4034
  },
  "P-SN-CLOUD__strong-upper_right_black-60__v4__pro4K__t2": {
   "family": "P-SN-CLOUD",
   "k1": {
    "bytes": 193948,
    "file": "P-SN-CLOUD__strong-upper_right_black-60__v4__pro4K__t2.webp",
    "px": 1024,
    "sha256": "a695c6e6a84f59ce3ddf32c34d44dbda0be48c35b1fbd1e903e0c0b5a463394e"
   },
   "k4": {},
   "kind": "radial",
   "mono": 1,
   "score": 96.0,
   "since": 1,
   "strength": 0.6188,
   "strong_angle": 57.0,
   "until": 0,
   "usable": 1,
   "variables": {
    "black": "60",
    "strong": "upper_right"
   },
   "void": [
    0.50062,
    0.50328,
    0.19428
   ],
   "void_diam": 0.3886
  },
  "P-SP-CROWN__liquid-cognac_spikes-12_rise-up__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 171866,
    "file": "P-SP-CROWN__liquid-cognac_spikes-12_rise-up__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "8744ec43b9e1737d5fb2871787d540a06b6a8376f988a30dd459b020b3f2c67f"
   },
   "k4": {
    "bytes": 1626116,
    "file": "P-SP-CROWN__liquid-cognac_spikes-12_rise-up__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "907962591e756f655dbe49ddbf2cb7abb1f93155bc8d47075f16697301783e41"
   },
   "kind": "radial",
   "mono": 0,
   "score": 92.0,
   "since": 1,
   "strength": 0.2403,
   "strong_angle": 94.1,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "cognac",
    "rise": "up",
    "spikes": "12"
   },
   "void": [
    0.50002,
    0.50003,
    0.22909
   ],
   "void_diam": 0.4582
  },
  "P-SP-CROWN__liquid-cognac_spikes-12_rise-up_left__vc__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 62254,
    "file": "P-SP-CROWN__liquid-cognac_spikes-12_rise-up_left__vc__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "c9a78a73ffdf696507e7d9fa87aa990dd50fd87faa0acd39b283fbc63a37aa3b"
   },
   "k4": {
    "bytes": 641128,
    "file": "P-SP-CROWN__liquid-cognac_spikes-12_rise-up_left__vc__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "ccaa31b90fdf510f400caf2d4d6fe8b5f73d566e451915e8acd6f8a05664d346"
   },
   "kind": "radial",
   "mono": 0,
   "score": 92.9,
   "since": 1,
   "strength": 0.4736,
   "strong_angle": 112.3,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "cognac",
    "rise": "up_left",
    "spikes": "12"
   },
   "void": [
    0.5001,
    0.49995,
    0.23095
   ],
   "void_diam": 0.4619
  },
  "P-SP-CROWN__liquid-cognac_spikes-12_rise-up_right__vc__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 57540,
    "file": "P-SP-CROWN__liquid-cognac_spikes-12_rise-up_right__vc__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "4bc24b08a22f8d6db61927c72ea77d42a80c463c4d68594cc6caf851cb6a17aa"
   },
   "k4": {
    "bytes": 617888,
    "file": "P-SP-CROWN__liquid-cognac_spikes-12_rise-up_right__vc__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "7acaf0c2367048d7ede2625fd109661a4b9ac2d3036044b827a19eefe222754a"
   },
   "kind": "radial",
   "mono": 0,
   "score": 84.3,
   "since": 1,
   "strength": 0.4867,
   "strong_angle": 50.3,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "cognac",
    "rise": "up_right",
    "spikes": "12"
   },
   "void": [
    0.49941,
    0.49731,
    0.23894
   ],
   "void_diam": 0.4779
  },
  "P-SP-CROWN__liquid-cognac_spikes-12_rise-up_right__vh__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 173740,
    "file": "P-SP-CROWN__liquid-cognac_spikes-12_rise-up_right__vh__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "7fe219cb80a22d8e634b03c957aebd186e7be7bfe4d469b86c9b9b760f6bc5ff"
   },
   "k4": {
    "bytes": 1584322,
    "file": "P-SP-CROWN__liquid-cognac_spikes-12_rise-up_right__vh__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "9ffb611a255448d92a9ccea98506d5a39dd987e44f47517fb5b9b49fcee136bd"
   },
   "kind": "radial",
   "mono": 0,
   "score": 89.1,
   "since": 1,
   "strength": 0.1857,
   "strong_angle": 54.5,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "cognac",
    "rise": "up_right",
    "spikes": "12"
   },
   "void": [
    0.49986,
    0.49959,
    0.23159
   ],
   "void_diam": 0.4632
  },
  "P-SP-CROWN__liquid-cognac_spikes-16_rise-up__v7__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 66276,
    "file": "P-SP-CROWN__liquid-cognac_spikes-16_rise-up__v7__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "920863097404287c99d80e2e11b52a9b65f88791be2f9d2ffd063bcc34779474"
   },
   "k4": {
    "bytes": 703864,
    "file": "P-SP-CROWN__liquid-cognac_spikes-16_rise-up__v7__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "70b050e40b394c05de6c3061d76c8d31103ec638e1385fc31efdbddc036a345f"
   },
   "kind": "radial",
   "mono": 0,
   "score": 90.4,
   "since": 1,
   "strength": 0.2801,
   "strong_angle": 85.5,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "cognac",
    "rise": "up",
    "spikes": "16"
   },
   "void": [
    0.50001,
    0.49986,
    0.23077
   ],
   "void_diam": 0.4615
  },
  "P-SP-CROWN__liquid-cognac_spikes-16_rise-up__vh__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 125644,
    "file": "P-SP-CROWN__liquid-cognac_spikes-16_rise-up__vh__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "2ae247e1c59eed72234185ddac35f3298b8abb638bd39231c5fb23636f95dbd4"
   },
   "k4": {
    "bytes": 1114172,
    "file": "P-SP-CROWN__liquid-cognac_spikes-16_rise-up__vh__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "27048ef25030645c413ff49b5135e1de8b472ba9afada0318a1099a539c7c8ba"
   },
   "kind": "radial",
   "mono": 0,
   "score": 94.9,
   "since": 1,
   "strength": 0.1409,
   "strong_angle": 85.6,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "cognac",
    "rise": "up",
    "spikes": "16"
   },
   "void": [
    0.49995,
    0.50002,
    0.23056
   ],
   "void_diam": 0.4611
  },
  "P-SP-CROWN__liquid-cognac_spikes-16_rise-up_left__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 150562,
    "file": "P-SP-CROWN__liquid-cognac_spikes-16_rise-up_left__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "e6bb318a8b9899afb42998ca2c571f77ccb17bce5b97b410b3fc4925b93914e2"
   },
   "k4": {
    "bytes": 1307630,
    "file": "P-SP-CROWN__liquid-cognac_spikes-16_rise-up_left__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "26c2f0e9feccede51dec19f3074b4c0b2f508be5c5f1cddab7b434efec4892b9"
   },
   "kind": "radial",
   "mono": 0,
   "score": 89.0,
   "since": 1,
   "strength": 0.266,
   "strong_angle": 134.3,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "cognac",
    "rise": "up_left",
    "spikes": "16"
   },
   "void": [
    0.50009,
    0.4998,
    0.23076
   ],
   "void_diam": 0.4615
  },
  "P-SP-CROWN__liquid-cognac_spikes-16_rise-up_right__vc__pro4K__t1_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 62036,
    "file": "P-SP-CROWN__liquid-cognac_spikes-16_rise-up_right__vc__pro4K__t1_g47.webp",
    "px": 1024,
    "sha256": "1b907c45a76b6e0a24ac0669e3274f57382f03eb63317e4713fdbe06470a32e5"
   },
   "k4": {
    "bytes": 677136,
    "file": "P-SP-CROWN__liquid-cognac_spikes-16_rise-up_right__vc__pro4K__t1_g47.webp",
    "px": 4096,
    "sha256": "c542a3d2d4684cefdb94d868aedf3d6f9cee1665589ff16e97f6c76420a09fcd"
   },
   "kind": "radial",
   "mono": 0,
   "score": 87.6,
   "since": 1,
   "strength": 0.4229,
   "strong_angle": 39.6,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "cognac",
    "rise": "up_right",
    "spikes": "16"
   },
   "void": [
    0.49897,
    0.50032,
    0.23108
   ],
   "void_diam": 0.4622
  },
  "P-SP-CROWN__liquid-cognac_spikes-16_rise-up_right__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 115990,
    "file": "P-SP-CROWN__liquid-cognac_spikes-16_rise-up_right__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "df0965567e836efc41b6d3cade42b9a7791d155ec26b4f42d911ad2595fdeaa6"
   },
   "k4": {
    "bytes": 1002744,
    "file": "P-SP-CROWN__liquid-cognac_spikes-16_rise-up_right__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "c3ba9bbb911a60c3019b862928ff8df1525311fb21c7f9293627343cfcb8527f"
   },
   "kind": "radial",
   "mono": 0,
   "score": 96.8,
   "since": 1,
   "strength": 0.4571,
   "strong_angle": 44.0,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "cognac",
    "rise": "up_right",
    "spikes": "16"
   },
   "void": [
    0.49358,
    0.52086,
    0.23888
   ],
   "void_diam": 0.4778
  },
  "P-SP-CROWN__liquid-cognac_spikes-20_rise-up__v7__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 76318,
    "file": "P-SP-CROWN__liquid-cognac_spikes-20_rise-up__v7__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "72da989afe252b94c6ec3c642b4e57d2f3a55d7885811e96a25c1252165c2eaa"
   },
   "k4": {
    "bytes": 777450,
    "file": "P-SP-CROWN__liquid-cognac_spikes-20_rise-up__v7__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "a133e7602403bceed1bf1e51897279ed32fa1323c8cd106e2bdb827220d07f9d"
   },
   "kind": "radial",
   "mono": 0,
   "score": 94.7,
   "since": 1,
   "strength": 0.2063,
   "strong_angle": 106.2,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "cognac",
    "rise": "up",
    "spikes": "20"
   },
   "void": [
    0.50001,
    0.49976,
    0.23096
   ],
   "void_diam": 0.4619
  },
  "P-SP-CROWN__liquid-cognac_spikes-20_rise-up__vc__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 75166,
    "file": "P-SP-CROWN__liquid-cognac_spikes-20_rise-up__vc__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "088c826184d0b6b0e80647c3994397b1e77350eaf09cfa7d20fdf899cd616eb2"
   },
   "k4": {
    "bytes": 768584,
    "file": "P-SP-CROWN__liquid-cognac_spikes-20_rise-up__vc__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "763129d7590d7b1ea07e4bb178a02a057c9c9c43d738510922d011107758af34"
   },
   "kind": "radial",
   "mono": 0,
   "score": 89.2,
   "since": 1,
   "strength": 0.311,
   "strong_angle": 85.5,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "cognac",
    "rise": "up",
    "spikes": "20"
   },
   "void": [
    0.50006,
    0.49989,
    0.23125
   ],
   "void_diam": 0.4625
  },
  "P-SP-CROWN__liquid-cognac_spikes-20_rise-up_right__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 130032,
    "file": "P-SP-CROWN__liquid-cognac_spikes-20_rise-up_right__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "81d4235cf5177879349e4b7fd44119f36a759a82bec5e0b3c12e7057a9d3e049"
   },
   "k4": {
    "bytes": 1102252,
    "file": "P-SP-CROWN__liquid-cognac_spikes-20_rise-up_right__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "a1a9d10b2581feaa36aba468b7997f62ee9129b9d4f81bec4a312f170ae14cec"
   },
   "kind": "radial",
   "mono": 0,
   "score": 92.9,
   "since": 1,
   "strength": 0.3159,
   "strong_angle": 51.8,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "cognac",
    "rise": "up_right",
    "spikes": "20"
   },
   "void": [
    0.5,
    0.50001,
    0.23114
   ],
   "void_diam": 0.4623
  },
  "P-SP-CROWN__liquid-tea_olive_spikes-12_rise-up__v7__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 50224,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-12_rise-up__v7__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "e64c20d2ebeabed6c46f20738e8691d2be7ddc9a6fbd75c472e420efb0b6b0ae"
   },
   "k4": {
    "bytes": 559334,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-12_rise-up__v7__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "ccc0d880a7dee67b16edf8e8f764d28e01d3949d9acdcbd639aa62e69d8357b7"
   },
   "kind": "radial",
   "mono": 0,
   "score": 99.0,
   "since": 1,
   "strength": 0.2293,
   "strong_angle": 91.2,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "tea_olive",
    "rise": "up",
    "spikes": "12"
   },
   "void": [
    0.50012,
    0.49983,
    0.23104
   ],
   "void_diam": 0.4621
  },
  "P-SP-CROWN__liquid-tea_olive_spikes-12_rise-up_left__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 104458,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-12_rise-up_left__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "f5dbadf33e7a44ae0936d5edee8096e5ae493416726dfe6889d0b708b07f279a"
   },
   "k4": {
    "bytes": 845478,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-12_rise-up_left__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "e9041138710843ab22590d88d8bcfe722de39c00bfa4ce28b920407b997877ae"
   },
   "kind": "radial",
   "mono": 0,
   "score": 94.7,
   "since": 1,
   "strength": 0.3412,
   "strong_angle": 128.6,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "tea_olive",
    "rise": "up_left",
    "spikes": "12"
   },
   "void": [
    0.49997,
    0.4999,
    0.23137
   ],
   "void_diam": 0.4627
  },
  "P-SP-CROWN__liquid-tea_olive_spikes-16_rise-up__vh__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 140022,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-16_rise-up__vh__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "628ff16977a11b38f77c6779ea405bd2b900d37a077832aa073e54e19748e79f"
   },
   "k4": {
    "bytes": 1197862,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-16_rise-up__vh__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "78d70b2c039624c849f644d31b3520ae844daffb9a2e9f1e5cc99eef21d4a593"
   },
   "kind": "radial",
   "mono": 0,
   "score": 100.0,
   "since": 1,
   "strength": 0.1892,
   "strong_angle": 104.1,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "tea_olive",
    "rise": "up",
    "spikes": "16"
   },
   "void": [
    0.49998,
    0.49977,
    0.23107
   ],
   "void_diam": 0.4621
  },
  "P-SP-CROWN__liquid-tea_olive_spikes-16_rise-up_left__vd__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 115872,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-16_rise-up_left__vd__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "33019e2bcb7eb4440fb1d61a9740631c5eb7db3b1b8dad6f78d8213ff11e86e0"
   },
   "k4": {
    "bytes": 907002,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-16_rise-up_left__vd__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "59fa727740fdd63cae537d19abe360943e7cad5b6d8d33a2a1f82e65ed2ffaaf"
   },
   "kind": "radial",
   "mono": 0,
   "score": 99.9,
   "since": 1,
   "strength": 0.297,
   "strong_angle": 112.0,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "tea_olive",
    "rise": "up_left",
    "spikes": "16"
   },
   "void": [
    0.50012,
    0.49996,
    0.23104
   ],
   "void_diam": 0.4621
  },
  "P-SP-CROWN__liquid-tea_olive_spikes-16_rise-up_right__vc__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 51956,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-16_rise-up_right__vc__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "368213dff151391255dba1fa3e8ce7d256370e9bce54c76290afa32c77134e29"
   },
   "k4": {
    "bytes": 582024,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-16_rise-up_right__vc__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "43cc63dab58abf899751ae36794fc467a66492de369e9633ca5469d1a50ae5e8"
   },
   "kind": "radial",
   "mono": 0,
   "score": 98.9,
   "since": 1,
   "strength": 0.4427,
   "strong_angle": 59.5,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "tea_olive",
    "rise": "up_right",
    "spikes": "16"
   },
   "void": [
    0.50004,
    0.49987,
    0.23108
   ],
   "void_diam": 0.4622
  },
  "P-SP-CROWN__liquid-tea_olive_spikes-16_rise-up_right__vd__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 60120,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-16_rise-up_right__vd__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "91c9d1790ce3f79f0a0a46661a095a7cf350a5e1c63e8ee53747d8e497f08f88"
   },
   "k4": {
    "bytes": 659482,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-16_rise-up_right__vd__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "4851e6ce81a6ced9e2b1cc3e3051f49cad90463e145ea0ad94787038521ac5c7"
   },
   "kind": "radial",
   "mono": 0,
   "score": 100.0,
   "since": 1,
   "strength": 0.379,
   "strong_angle": 40.1,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "tea_olive",
    "rise": "up_right",
    "spikes": "16"
   },
   "void": [
    0.49997,
    0.4998,
    0.23097
   ],
   "void_diam": 0.4619
  },
  "P-SP-CROWN__liquid-tea_olive_spikes-16_rise-up_right__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 181924,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-16_rise-up_right__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "cea216f1eeb5e7acc000be2e7871d151cdf4a5197b746ad9f828ba6ef730bb03"
   },
   "k4": {
    "bytes": 1426700,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-16_rise-up_right__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "a19eeb10939da0fad1863eb3b8338b5be8e6df1a10920e6eba965a53b45f2435"
   },
   "kind": "radial",
   "mono": 0,
   "score": 100.0,
   "since": 1,
   "strength": 0.1979,
   "strong_angle": 48.6,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "tea_olive",
    "rise": "up_right",
    "spikes": "16"
   },
   "void": [
    0.50005,
    0.5,
    0.23112
   ],
   "void_diam": 0.4622
  },
  "P-SP-CROWN__liquid-tea_olive_spikes-20_rise-up__v7__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 64460,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-20_rise-up__v7__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "5b8cc809d8fc5c4b1fe869caebf95db48767a6ac5a4b77c54c1f85b8b7a7be1e"
   },
   "k4": {
    "bytes": 716202,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-20_rise-up__v7__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "46927ec98ba77fb64bf56f78d3460e12243ab7666d2330930325e46abf02d562"
   },
   "kind": "radial",
   "mono": 0,
   "score": 98.5,
   "since": 1,
   "strength": 0.1365,
   "strong_angle": 93.7,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "tea_olive",
    "rise": "up",
    "spikes": "20"
   },
   "void": [
    0.50006,
    0.49968,
    0.23091
   ],
   "void_diam": 0.4618
  },
  "P-SP-CROWN__liquid-tea_olive_spikes-20_rise-up__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 60808,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-20_rise-up__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "644f2e28d68890242c62d8521f859be6b05891fb927ba38f7c2baf1dd23eb474"
   },
   "k4": {
    "bytes": 627902,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-20_rise-up__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "6f7e0333d8f04445566ca6ab7f1eb3e7fdfa1d67b241ca3cc10bda5d0b4c5600"
   },
   "kind": "radial",
   "mono": 0,
   "score": 98.7,
   "since": 1,
   "strength": 0.2733,
   "strong_angle": 86.9,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "tea_olive",
    "rise": "up",
    "spikes": "20"
   },
   "void": [
    0.5001,
    0.49986,
    0.23089
   ],
   "void_diam": 0.4618
  },
  "P-SP-CROWN__liquid-tea_olive_spikes-20_rise-up_left__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 77396,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-20_rise-up_left__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "66f8dca8e5f6b690675d98179420c4fd855af0bb424b661f63da0f3e86ede6c1"
   },
   "k4": {
    "bytes": 661230,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-20_rise-up_left__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "418ed25ead2a1e0eed606d65ff40b5d5bfa912eb9e7c740907a9b5b194b6a926"
   },
   "kind": "radial",
   "mono": 0,
   "score": 96.2,
   "since": 1,
   "strength": 0.2784,
   "strong_angle": 125.0,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "tea_olive",
    "rise": "up_left",
    "spikes": "20"
   },
   "void": [
    0.50007,
    0.50009,
    0.23083
   ],
   "void_diam": 0.4617
  },
  "P-SP-CROWN__liquid-tea_olive_spikes-20_rise-up_left__vh__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 108958,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-20_rise-up_left__vh__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "a547761d4531990ff1848f1ce40d06ff7826d8529af28eef604c4683cbdf4fb3"
   },
   "k4": {
    "bytes": 925796,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-20_rise-up_left__vh__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "253e30faf9f1053f7437ad74b71ed5ee674b20e5da7ed8df14d7550759d8544a"
   },
   "kind": "radial",
   "mono": 0,
   "score": 97.5,
   "since": 1,
   "strength": 0.4172,
   "strong_angle": 121.1,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "tea_olive",
    "rise": "up_left",
    "spikes": "20"
   },
   "void": [
    0.50002,
    0.49995,
    0.231
   ],
   "void_diam": 0.462
  },
  "P-SP-CROWN__liquid-tea_olive_spikes-20_rise-up_right__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 86996,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-20_rise-up_right__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "0dd7171ece397c18d1e0f1ea9f5151a5b520b860826a7e48fdc0d628c91272de"
   },
   "k4": {
    "bytes": 812686,
    "file": "P-SP-CROWN__liquid-tea_olive_spikes-20_rise-up_right__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "2492a246392b6f1b10d366c3f3442b667762b007917f07bbce64d4d098e0e733"
   },
   "kind": "radial",
   "mono": 0,
   "score": 98.6,
   "since": 1,
   "strength": 0.272,
   "strong_angle": 36.3,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "tea_olive",
    "rise": "up_right",
    "spikes": "20"
   },
   "void": [
    0.50003,
    0.49983,
    0.23109
   ],
   "void_diam": 0.4622
  },
  "P-SP-CROWN__liquid-water_clear_spikes-12_rise-up__v7__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 66492,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-12_rise-up__v7__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "5d199719251f9572bbb0305f2984389ddc6572ee4c24412b63e19c68334d239f"
   },
   "k4": {
    "bytes": 724766,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-12_rise-up__v7__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "9574251b1a7f83cd988d61691001a9563b7fdee3393ad756605c600962e5a3ae"
   },
   "kind": "radial",
   "mono": 0,
   "score": 100.0,
   "since": 1,
   "strength": 0.1234,
   "strong_angle": 96.9,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_clear",
    "rise": "up",
    "spikes": "12"
   },
   "void": [
    0.50001,
    0.4999,
    0.23091
   ],
   "void_diam": 0.4618
  },
  "P-SP-CROWN__liquid-water_clear_spikes-12_rise-up_left__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 166088,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-12_rise-up_left__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "e50f4826f4f194bc661eeef696e33c42dfeade12fb46b2a047250e21fc2347a9"
   },
   "k4": {
    "bytes": 1475450,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-12_rise-up_left__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "fc50e45031006a8bf2b773f2bbc6845da970478dd788b13e808102b574c822f9"
   },
   "kind": "radial",
   "mono": 0,
   "score": 99.1,
   "since": 1,
   "strength": 0.2803,
   "strong_angle": 131.0,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_clear",
    "rise": "up_left",
    "spikes": "12"
   },
   "void": [
    0.4986,
    0.49899,
    0.24966
   ],
   "void_diam": 0.4993
  },
  "P-SP-CROWN__liquid-water_clear_spikes-12_rise-up_right__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 100566,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-12_rise-up_right__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "b705ee5e4edb3f08178e4ee702d8c419dbd1ae3cfb956090fa25b381542a2a90"
   },
   "k4": {
    "bytes": 925568,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-12_rise-up_right__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "9c344b09a479b83d2ad4d6604562dd41594504250aeaac54847d4821e24f98e0"
   },
   "kind": "radial",
   "mono": 0,
   "score": 99.1,
   "since": 1,
   "strength": 0.3563,
   "strong_angle": 42.5,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_clear",
    "rise": "up_right",
    "spikes": "12"
   },
   "void": [
    0.50012,
    0.4999,
    0.23113
   ],
   "void_diam": 0.4623
  },
  "P-SP-CROWN__liquid-water_clear_spikes-12_rise-up_right__vh__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 140668,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-12_rise-up_right__vh__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "ad95a8ff795c952ee19b6cf888c902f68807b09c49226b31eeab51511893c126"
   },
   "k4": {
    "bytes": 1272886,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-12_rise-up_right__vh__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "6fe49ef9582f8912a3cf8fd70685d938ad885f11f08dad3df755d40e6913adbf"
   },
   "kind": "radial",
   "mono": 0,
   "score": 99.1,
   "since": 1,
   "strength": 0.2636,
   "strong_angle": 45.1,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_clear",
    "rise": "up_right",
    "spikes": "12"
   },
   "void": [
    0.50009,
    0.49988,
    0.23078
   ],
   "void_diam": 0.4616
  },
  "P-SP-CROWN__liquid-water_clear_spikes-16_rise-up__v7__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 79694,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-16_rise-up__v7__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "965c50af92b9ca9c9d3920affe8d685079970a2943b7558e2bb52c18a65e5c9e"
   },
   "k4": {
    "bytes": 884936,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-16_rise-up__v7__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "680bac0181123c2cf77a457aafd2fbf442c8b2d5fb149b40358a58f91494cf05"
   },
   "kind": "radial",
   "mono": 0,
   "score": 99.4,
   "since": 1,
   "strength": 0.0524,
   "strong_angle": 92.2,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_clear",
    "rise": "up",
    "spikes": "16"
   },
   "void": [
    0.50001,
    0.49992,
    0.23092
   ],
   "void_diam": 0.4618
  },
  "P-SP-CROWN__liquid-water_clear_spikes-16_rise-up__vh__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 89224,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-16_rise-up__vh__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "8d1adc0f0d85da9b3246c355f007ef0a253d48a4cfeb32b51e8d6345d369ade8"
   },
   "k4": {
    "bytes": 907018,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-16_rise-up__vh__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "9987c5b327a661a23adf65f4fb6299dfa93a808e8d844d68bce8910039120b83"
   },
   "kind": "radial",
   "mono": 0,
   "score": 99.3,
   "since": 1,
   "strength": 0.147,
   "strong_angle": 91.9,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_clear",
    "rise": "up",
    "spikes": "16"
   },
   "void": [
    0.49998,
    0.49992,
    0.23083
   ],
   "void_diam": 0.4617
  },
  "P-SP-CROWN__liquid-water_clear_spikes-16_rise-up_left__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 147150,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-16_rise-up_left__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "5bff69572a6a8871867142ba94d38e3682641ac75bd492a10a194fa3c2b15a07"
   },
   "k4": {
    "bytes": 1336106,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-16_rise-up_left__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "7fd6fc0a67685cfd786dd504ebab9ae98a05a7319d856341abea3097c3082330"
   },
   "kind": "radial",
   "mono": 0,
   "score": 99.8,
   "since": 1,
   "strength": 0.2429,
   "strong_angle": 117.4,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_clear",
    "rise": "up_left",
    "spikes": "16"
   },
   "void": [
    0.50005,
    0.50019,
    0.23081
   ],
   "void_diam": 0.4616
  },
  "P-SP-CROWN__liquid-water_clear_spikes-16_rise-up_right__vc__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 65174,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-16_rise-up_right__vc__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "6a1b73615e32eb6257af481eec34c9214a254683cc157f246822bb8851f17e2b"
   },
   "k4": {
    "bytes": 699462,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-16_rise-up_right__vc__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "2c2075f9fa7a29476eccf8024915c8116bf4281b3f181d0ca4241eee14d38cc6"
   },
   "kind": "radial",
   "mono": 0,
   "score": 99.1,
   "since": 1,
   "strength": 0.4767,
   "strong_angle": 50.0,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_clear",
    "rise": "up_right",
    "spikes": "16"
   },
   "void": [
    0.50004,
    0.49987,
    0.23097
   ],
   "void_diam": 0.4619
  },
  "P-SP-CROWN__liquid-water_clear_spikes-16_rise-up_right__vd__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 109088,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-16_rise-up_right__vd__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "d833f2844a5e1e08a53e7d4cf16dbdc233054512c1327c211a8fb39cce808a94"
   },
   "k4": {
    "bytes": 942026,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-16_rise-up_right__vd__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "8a541c4b7d499ced97ae8aa524b8a2b996665bd7f2ad05ae12613c3b0f17f2f7"
   },
   "kind": "radial",
   "mono": 0,
   "score": 100.0,
   "since": 1,
   "strength": 0.2082,
   "strong_angle": 40.9,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_clear",
    "rise": "up_right",
    "spikes": "16"
   },
   "void": [
    0.50008,
    0.49989,
    0.23095
   ],
   "void_diam": 0.4619
  },
  "P-SP-CROWN__liquid-water_clear_spikes-20_rise-up__v7__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 74826,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-20_rise-up__v7__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "66a195a6a8d2236c79de4c114e4aa361a9a7596069fada04f2fe356fdffeed16"
   },
   "k4": {
    "bytes": 826278,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-20_rise-up__v7__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "aaf5d266e8f9a42892a91f329e7583a2cb264d0b8fff5611f10f361daa03bf0b"
   },
   "kind": "radial",
   "mono": 0,
   "score": 99.7,
   "since": 1,
   "strength": 0.0741,
   "strong_angle": 75.6,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_clear",
    "rise": "up",
    "spikes": "20"
   },
   "void": [
    0.50004,
    0.4998,
    0.2308
   ],
   "void_diam": 0.4616
  },
  "P-SP-CROWN__liquid-water_clear_spikes-20_rise-up_left__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 158322,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-20_rise-up_left__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "b62992dad4386bb7114d959511233b86eaca561b3deecb7b3b71db8f1a49a2d9"
   },
   "k4": {
    "bytes": 1353140,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-20_rise-up_left__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "6bcb09d3cec23aafd5275d1cd6fa512a05f0fdd681c72009725bd44267b33500"
   },
   "kind": "radial",
   "mono": 0,
   "score": 100.0,
   "since": 1,
   "strength": 0.1546,
   "strong_angle": 133.5,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_clear",
    "rise": "up_left",
    "spikes": "20"
   },
   "void": [
    0.50004,
    0.49996,
    0.23095
   ],
   "void_diam": 0.4619
  },
  "P-SP-CROWN__liquid-water_clear_spikes-20_rise-up_right__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 119300,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-20_rise-up_right__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "828d17d1d71fb6c5eaf1a344997ae9676f88b8b72487e1f634f85a2c2d709768"
   },
   "k4": {
    "bytes": 1074412,
    "file": "P-SP-CROWN__liquid-water_clear_spikes-20_rise-up_right__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "169a6873c02dd4eb780747cddd5ec12adb80045680b671bb117d6f76fa21b5a4"
   },
   "kind": "radial",
   "mono": 0,
   "score": 97.5,
   "since": 1,
   "strength": 0.3213,
   "strong_angle": 41.2,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_clear",
    "rise": "up_right",
    "spikes": "20"
   },
   "void": [
    0.49997,
    0.50009,
    0.23089
   ],
   "void_diam": 0.4618
  },
  "P-SP-CROWN__liquid-water_teal_spikes-12_rise-up__v7__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 92492,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-12_rise-up__v7__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "36110e29ce340a867456fb41f3d05acf8b11f3716c1790b335ba51c45b4b01b3"
   },
   "k4": {
    "bytes": 953410,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-12_rise-up__v7__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "2be8ffa780c734a3623fcca414a3a802ca7e4d807cccbceb2af9a99103759d6b"
   },
   "kind": "radial",
   "mono": 0,
   "score": 98.3,
   "since": 1,
   "strength": 0.0559,
   "strong_angle": 113.4,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_teal",
    "rise": "up",
    "spikes": "12"
   },
   "void": [
    0.49999,
    0.49975,
    0.23086
   ],
   "void_diam": 0.4617
  },
  "P-SP-CROWN__liquid-water_teal_spikes-12_rise-up__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 164956,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-12_rise-up__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "7b8262a3af29ae28d4bd0ea5573ffe996cfabe9faece2aaef7a2e647e9038a0f"
   },
   "k4": {
    "bytes": 1459806,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-12_rise-up__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "2f343207e1ee56a38ec23111be5b2e1fef562de4acebbd0e5961dd502b3c7b96"
   },
   "kind": "radial",
   "mono": 0,
   "score": 100.0,
   "since": 1,
   "strength": 0.1808,
   "strong_angle": 76.6,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_teal",
    "rise": "up",
    "spikes": "12"
   },
   "void": [
    0.50017,
    0.50001,
    0.23079
   ],
   "void_diam": 0.4616
  },
  "P-SP-CROWN__liquid-water_teal_spikes-12_rise-up_left__vc__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 74118,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-12_rise-up_left__vc__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "1da2bcad928c5c5db5174ddd6967fa7b3272ac14ae0d032cbff369486dbf2c00"
   },
   "k4": {
    "bytes": 841926,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-12_rise-up_left__vc__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "7985078f72e73b12331047b1717476f17e4c1dd3bfc6277e6b6e180ded2ef12e"
   },
   "kind": "radial",
   "mono": 0,
   "score": 95.0,
   "since": 1,
   "strength": 0.3365,
   "strong_angle": 129.9,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_teal",
    "rise": "up_left",
    "spikes": "12"
   },
   "void": [
    0.50012,
    0.49977,
    0.23732
   ],
   "void_diam": 0.4746
  },
  "P-SP-CROWN__liquid-water_teal_spikes-12_rise-up_left__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 143702,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-12_rise-up_left__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "543fdc98fd6e3be1094824920cce04c6e2efedc4ba8a00fcb40b5f8211ca2b41"
   },
   "k4": {
    "bytes": 1261776,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-12_rise-up_left__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "f8d67719432af83f1e3162bafafaec79c7c4be8a624942d7bf4b36fbab2f70da"
   },
   "kind": "radial",
   "mono": 0,
   "score": 98.4,
   "since": 1,
   "strength": 0.3048,
   "strong_angle": 128.0,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_teal",
    "rise": "up_left",
    "spikes": "12"
   },
   "void": [
    0.50021,
    0.50004,
    0.23097
   ],
   "void_diam": 0.4619
  },
  "P-SP-CROWN__liquid-water_teal_spikes-16_rise-up__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 156940,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-16_rise-up__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "e41864fd5fd0542b9cabf2318f730481b33f268effe0ac8f2deee4cff7729be5"
   },
   "k4": {
    "bytes": 1415676,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-16_rise-up__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "a38a1039463197a466b8ebdef056271aadc74ae75146ed24c447fd62aab81c1d"
   },
   "kind": "radial",
   "mono": 0,
   "score": 98.5,
   "since": 1,
   "strength": 0.1599,
   "strong_angle": 84.1,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_teal",
    "rise": "up",
    "spikes": "16"
   },
   "void": [
    0.50001,
    0.49974,
    0.23096
   ],
   "void_diam": 0.4619
  },
  "P-SP-CROWN__liquid-water_teal_spikes-16_rise-up_left__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 132104,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-16_rise-up_left__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "cc5ee840a257ea3de5ad8fdeccae955f6240ae569692d4c3ad5ac86984c1e03b"
   },
   "k4": {
    "bytes": 1107980,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-16_rise-up_left__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "d6f933d68820af50807680ad0d0ddace83c57c23b4ab853e93bb8c977eca5801"
   },
   "kind": "radial",
   "mono": 0,
   "score": 97.2,
   "since": 1,
   "strength": 0.2605,
   "strong_angle": 123.5,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_teal",
    "rise": "up_left",
    "spikes": "16"
   },
   "void": [
    0.49998,
    0.49996,
    0.23122
   ],
   "void_diam": 0.4624
  },
  "P-SP-CROWN__liquid-water_teal_spikes-16_rise-up_right__vc__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 70482,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-16_rise-up_right__vc__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "49302e9b7734f176057195fdda584dc4484fe1323ac192d0588203aeefcd40cb"
   },
   "k4": {
    "bytes": 764214,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-16_rise-up_right__vc__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "6ed24ad9ed34dfff6b8a45b4916d38b38a18d79ae1863978692378b5c5422aba"
   },
   "kind": "radial",
   "mono": 0,
   "score": 98.8,
   "since": 1,
   "strength": 0.4524,
   "strong_angle": 45.6,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_teal",
    "rise": "up_right",
    "spikes": "16"
   },
   "void": [
    0.50009,
    0.49985,
    0.23089
   ],
   "void_diam": 0.4618
  },
  "P-SP-CROWN__liquid-water_teal_spikes-16_rise-up_right__vd__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 205130,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-16_rise-up_right__vd__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "fc35375318bd8a81250cbafa4447f2d55fca59551f1035c784c0e717c161fdce"
   },
   "k4": {
    "bytes": 1703394,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-16_rise-up_right__vd__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "92b0cbc8d0e1755374839d6de93d9e2be8fdd027b230ad263e450a8612821805"
   },
   "kind": "radial",
   "mono": 0,
   "score": 100.0,
   "since": 1,
   "strength": 0.197,
   "strong_angle": 46.4,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_teal",
    "rise": "up_right",
    "spikes": "16"
   },
   "void": [
    0.50005,
    0.4999,
    0.23091
   ],
   "void_diam": 0.4618
  },
  "P-SP-CROWN__liquid-water_teal_spikes-16_rise-up_right__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 70100,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-16_rise-up_right__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "bdbaf75a408c9b98d6df2780027857b1f3d72f734c29ad40247bb77159af280c"
   },
   "k4": {
    "bytes": 743264,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-16_rise-up_right__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "decb053412faf15cb0881ed7395fb6df5a0c7ff0a3cb32c5a3bc249dbd7cf007"
   },
   "kind": "radial",
   "mono": 0,
   "score": 97.0,
   "since": 1,
   "strength": 0.3419,
   "strong_angle": 37.2,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_teal",
    "rise": "up_right",
    "spikes": "16"
   },
   "void": [
    0.49996,
    0.49987,
    0.2323
   ],
   "void_diam": 0.4646
  },
  "P-SP-CROWN__liquid-water_teal_spikes-20_rise-up__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 165010,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-20_rise-up__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "19cbca383bd4b4bbe7b331dbe56d1b852d7ffcfeb30d6597520737952d1bd95d"
   },
   "k4": {
    "bytes": 1526858,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-20_rise-up__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "4629e1c013998741f578625c7ecebdeb5300a9a7974b816e637996d5dc7fbfdd"
   },
   "kind": "radial",
   "mono": 0,
   "score": 100.0,
   "since": 1,
   "strength": 0.1264,
   "strong_angle": 72.9,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_teal",
    "rise": "up",
    "spikes": "20"
   },
   "void": [
    0.50005,
    0.49981,
    0.23085
   ],
   "void_diam": 0.4617
  },
  "P-SP-CROWN__liquid-water_teal_spikes-20_rise-up_left__vc__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 84854,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-20_rise-up_left__vc__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "da50c66dbfbe6049bbd5accb0192301f9886e7406e130149e00e888e10f1ce81"
   },
   "k4": {
    "bytes": 918212,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-20_rise-up_left__vc__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "0afcfb47e08e34b81d9a43cb1282a2dcc30a6bb70d0e4885a99fe20d5b4b6fce"
   },
   "kind": "radial",
   "mono": 0,
   "score": 97.2,
   "since": 1,
   "strength": 0.1603,
   "strong_angle": 89.9,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_teal",
    "rise": "up_left",
    "spikes": "20"
   },
   "void": [
    0.49998,
    0.49988,
    0.23118
   ],
   "void_diam": 0.4624
  },
  "P-SP-CROWN__liquid-water_teal_spikes-20_rise-up_left__vh__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 188060,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-20_rise-up_left__vh__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "c4971afca286c2f609b8519bc7b94ab128eed73bcf8908fa7e09adcfdb023de9"
   },
   "k4": {
    "bytes": 1850220,
    "file": "P-SP-CROWN__liquid-water_teal_spikes-20_rise-up_left__vh__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "13ccb3e8365f80779a004afa696156e24e567c14a05c6b6c5dcef13857a3cd59"
   },
   "kind": "radial",
   "mono": 0,
   "score": 98.8,
   "since": 1,
   "strength": 0.0805,
   "strong_angle": 191.1,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "water_teal",
    "rise": "up_left",
    "spikes": "20"
   },
   "void": [
    0.50004,
    0.49977,
    0.23081
   ],
   "void_diam": 0.4616
  },
  "P-SP-CROWN__liquid-whisky_amber_spikes-12_rise-up__v7__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 84364,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-12_rise-up__v7__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "f1ab3d5a6cbe3a62d287aae0ac57cacad2bfac99d5c524f33a89440a4ebc211a"
   },
   "k4": {
    "bytes": 921382,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-12_rise-up__v7__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "f68d9fa18e21817e47fa5c7223839834f5dc96e8bba5b92eb63c5dd1b1fc513f"
   },
   "kind": "radial",
   "mono": 0,
   "score": 100.0,
   "since": 1,
   "strength": 0.0836,
   "strong_angle": 142.7,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "whisky_amber",
    "rise": "up",
    "spikes": "12"
   },
   "void": [
    0.50007,
    0.49981,
    0.23077
   ],
   "void_diam": 0.4615
  },
  "P-SP-CROWN__liquid-whisky_amber_spikes-12_rise-up_left__vc__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 70552,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-12_rise-up_left__vc__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "67976cad4e00f2c781d50312404d4fd76105b819da98bcf48a5694f8bd29825e"
   },
   "k4": {
    "bytes": 796502,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-12_rise-up_left__vc__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "3b90a367dc1e0e842dda4d8467ba1267bd574888079221ed442a9082b5df1067"
   },
   "kind": "radial",
   "mono": 0,
   "score": 99.7,
   "since": 1,
   "strength": 0.3893,
   "strong_angle": 131.9,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "whisky_amber",
    "rise": "up_left",
    "spikes": "12"
   },
   "void": [
    0.50001,
    0.49982,
    0.2307
   ],
   "void_diam": 0.4614
  },
  "P-SP-CROWN__liquid-whisky_amber_spikes-12_rise-up_left__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 87606,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-12_rise-up_left__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "34f8fe77bdee29e6fced04208d8ba2214dbf1613b16b7f2d154c8287fda5d518"
   },
   "k4": {
    "bytes": 904490,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-12_rise-up_left__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "c7429a9cc0206b46590918238fdd820fb23baa51f9b3fc2a2f9ae5752576d64c"
   },
   "kind": "radial",
   "mono": 0,
   "score": 100.0,
   "since": 1,
   "strength": 0.378,
   "strong_angle": 125.7,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "whisky_amber",
    "rise": "up_left",
    "spikes": "12"
   },
   "void": [
    0.50005,
    0.5,
    0.23085
   ],
   "void_diam": 0.4617
  },
  "P-SP-CROWN__liquid-whisky_amber_spikes-16_rise-up__v7__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 99120,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-16_rise-up__v7__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "a628d83ead18eef8ec7b2b2072262c58b7040c42c7a681858533be2ab034a550"
   },
   "k4": {
    "bytes": 1179074,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-16_rise-up__v7__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "d3a4caa5dfb06cb56e2985106d3fa7c87f9695a170dbc0316fdc6d03dabf74cf"
   },
   "kind": "radial",
   "mono": 0,
   "score": 100.0,
   "since": 1,
   "strength": 0.1639,
   "strong_angle": 82.1,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "whisky_amber",
    "rise": "up",
    "spikes": "16"
   },
   "void": [
    0.49998,
    0.49968,
    0.23084
   ],
   "void_diam": 0.4617
  },
  "P-SP-CROWN__liquid-whisky_amber_spikes-16_rise-up__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 146898,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-16_rise-up__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "7c5c9d0d662d00a1ee372587c855facc01602e936cff1ec6bc9d39261fb88aad"
   },
   "k4": {
    "bytes": 1344052,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-16_rise-up__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "7b49be0285e778dbdcb1518b8ae836bbd5a3b638e6068bcff6ebdfa66763f645"
   },
   "kind": "radial",
   "mono": 0,
   "score": 100.0,
   "since": 1,
   "strength": 0.2494,
   "strong_angle": 93.2,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "whisky_amber",
    "rise": "up",
    "spikes": "16"
   },
   "void": [
    0.49993,
    0.49973,
    0.23081
   ],
   "void_diam": 0.4616
  },
  "P-SP-CROWN__liquid-whisky_amber_spikes-16_rise-up_left__vd__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 174240,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-16_rise-up_left__vd__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "6774226666925a2756137cd2116ebcf2094d6bb9ac1916b7c08a93126e5b266d"
   },
   "k4": {
    "bytes": 1572546,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-16_rise-up_left__vd__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "7bd6eb9e7e48ef45fd38e574ed7befb04b33fa1f6eb59ece806ea070e5d1be43"
   },
   "kind": "radial",
   "mono": 0,
   "score": 100.0,
   "since": 1,
   "strength": 0.1296,
   "strong_angle": 126.4,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "whisky_amber",
    "rise": "up_left",
    "spikes": "16"
   },
   "void": [
    0.50003,
    0.49991,
    0.23092
   ],
   "void_diam": 0.4618
  },
  "P-SP-CROWN__liquid-whisky_amber_spikes-16_rise-up_right__vc__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 89070,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-16_rise-up_right__vc__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "b173432eeae4c09052bb2cafedfaea1a76c2bc11761f341c79b875e754d4375f"
   },
   "k4": {
    "bytes": 958386,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-16_rise-up_right__vc__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "452177d5d0a6477264711a87df4cbd9a4e44792b27b793e63698df484a34dc6e"
   },
   "kind": "radial",
   "mono": 0,
   "score": 100.0,
   "since": 1,
   "strength": 0.4478,
   "strong_angle": 42.8,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "whisky_amber",
    "rise": "up_right",
    "spikes": "16"
   },
   "void": [
    0.50003,
    0.49977,
    0.23081
   ],
   "void_diam": 0.4616
  },
  "P-SP-CROWN__liquid-whisky_amber_spikes-16_rise-up_right__vd__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 163070,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-16_rise-up_right__vd__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "4322e1931f32cd60558096a8c6098f87b96bcfaad93e7d2163d71fa3199fe80b"
   },
   "k4": {
    "bytes": 1413760,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-16_rise-up_right__vd__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "414db2a0a99d04ae1d72fc94d3d685f3a6fcb38f4f7e01c7d91266d5ad679a20"
   },
   "kind": "radial",
   "mono": 0,
   "score": 99.5,
   "since": 1,
   "strength": 0.2417,
   "strong_angle": 52.8,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "whisky_amber",
    "rise": "up_right",
    "spikes": "16"
   },
   "void": [
    0.49999,
    0.49987,
    0.23097
   ],
   "void_diam": 0.4619
  },
  "P-SP-CROWN__liquid-whisky_amber_spikes-20_rise-up__v7__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 95600,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-20_rise-up__v7__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "101b8aa33234f679fac204d5f6484bceb942891741c10ff7ca028a6e292bd4d5"
   },
   "k4": {
    "bytes": 1042970,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-20_rise-up__v7__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "92db98e701f1a02d84e9804a66cb66d3fdf72cd430273986e201c2fd4096d676"
   },
   "kind": "radial",
   "mono": 0,
   "score": 100.0,
   "since": 1,
   "strength": 0.0689,
   "strong_angle": 129.0,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "whisky_amber",
    "rise": "up",
    "spikes": "20"
   },
   "void": [
    0.50009,
    0.49983,
    0.23084
   ],
   "void_diam": 0.4617
  },
  "P-SP-CROWN__liquid-whisky_amber_spikes-20_rise-up__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 169066,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-20_rise-up__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "645337efb4cc8685a3a4647f9d60f5dacf1423738233e6b329a35bc7eff21b29"
   },
   "k4": {
    "bytes": 1446596,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-20_rise-up__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "4eca2d5ae3e0031817ff8286d7ca6ecf813dcf52a83b415de6aa53c430630d5a"
   },
   "kind": "radial",
   "mono": 0,
   "score": 99.2,
   "since": 1,
   "strength": 0.1661,
   "strong_angle": 80.8,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "whisky_amber",
    "rise": "up",
    "spikes": "20"
   },
   "void": [
    0.50004,
    0.49974,
    0.23072
   ],
   "void_diam": 0.4614
  },
  "P-SP-CROWN__liquid-whisky_amber_spikes-20_rise-up_left__vh__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 116918,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-20_rise-up_left__vh__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "a128f0e5a769e1912c90df474ec7bd1239639741e2d61473bdfba2193172aff9"
   },
   "k4": {
    "bytes": 1049702,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-20_rise-up_left__vh__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "bbd55c8b6b4db352314678c4e5003acf269531d6da3eae9d5ad8d9be20fc908e"
   },
   "kind": "radial",
   "mono": 0,
   "score": 98.1,
   "since": 1,
   "strength": 0.3759,
   "strong_angle": 133.2,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "whisky_amber",
    "rise": "up_left",
    "spikes": "20"
   },
   "void": [
    0.50004,
    0.49978,
    0.23064
   ],
   "void_diam": 0.4613
  },
  "P-SP-CROWN__liquid-whisky_amber_spikes-20_rise-up_right__ve__pro4K__t0_g47": {
   "family": "P-SP-CROWN",
   "k1": {
    "bytes": 135514,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-20_rise-up_right__ve__pro4K__t0_g47.webp",
    "px": 1024,
    "sha256": "389c6ac6d037dc651787facb7cc3e51f2ec925bbd26fdce08750bb4dea7e9128"
   },
   "k4": {
    "bytes": 1134244,
    "file": "P-SP-CROWN__liquid-whisky_amber_spikes-20_rise-up_right__ve__pro4K__t0_g47.webp",
    "px": 4096,
    "sha256": "813873a47094c52d6d92552d8230f4a01b1b8baabf692f264151aaea9c043d5c"
   },
   "kind": "radial",
   "mono": 0,
   "score": 100.0,
   "since": 1,
   "strength": 0.3314,
   "strong_angle": 41.9,
   "until": 0,
   "usable": 1,
   "variables": {
    "liquid": "whisky_amber",
    "rise": "up_right",
    "spikes": "20"
   },
   "void": [
    0.50002,
    0.49979,
    0.23084
   ],
   "void_diam": 0.4617
  },
  "P-UV-DUST__density-dense_curl-ccw__v4__pro4K__t0": {
   "extra": {
    "black_share": 0.06941211223602295,
    "tangential": 0.5039505362510681
   },
   "family": "P-UV-DUST",
   "k1": {
    "bytes": 421755,
    "file": "P-UV-DUST__density-dense_curl-ccw__v4__pro4K__t0.png",
    "px": 1024,
    "sha256": "aa613ab70f30685d8788ba99e73114508e268477003087fc3c13756a54904eb0"
   },
   "k4": {
    "bytes": 6604747,
    "file": "P-UV-DUST__density-dense_curl-ccw__v4__pro4K__t0.png",
    "px": 4096,
    "sha256": "7c1078be59beab009a4f2f3286e3ddc48751fc7b97e50ff0ec1bfbaca447af99"
   },
   "kind": "uv",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {},
   "void": [
    0.49998771308065815,
    0.49984698302336633,
    0.1165834975857246
   ],
   "void_diam": 0.2331669951714492
  },
  "P-UV-DUST__density-dense_curl-ccw__v4__pro4K__t1": {
   "extra": {
    "black_share": 0.16317635774612427,
    "tangential": 0.4998246729373932
   },
   "family": "P-UV-DUST",
   "k1": {
    "bytes": 408228,
    "file": "P-UV-DUST__density-dense_curl-ccw__v4__pro4K__t1.png",
    "px": 1024,
    "sha256": "6ea19092676ae8b7003fce223dc14fcb1ef5dc6f2b8501f062d4f76db8f67360"
   },
   "k4": {
    "bytes": 6572080,
    "file": "P-UV-DUST__density-dense_curl-ccw__v4__pro4K__t1.png",
    "px": 4096,
    "sha256": "de6eb00493792476badba26efaf39e43843e101e2ee8829f8f3571df17b0120b"
   },
   "kind": "uv",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {},
   "void": [
    0.5000178634863052,
    0.49996947679915005,
    0.15955445799105036
   ],
   "void_diam": 0.3191089159821007
  },
  "P-UV-DUST__density-dense_curl-cw__v3__pro4K__t0": {
   "extra": {
    "black_share": 0.17337864637374878,
    "tangential": 0.5080617070198059
   },
   "family": "P-UV-DUST",
   "k1": {
    "bytes": 391051,
    "file": "P-UV-DUST__density-dense_curl-cw__v3__pro4K__t0.png",
    "px": 1024,
    "sha256": "5ab47d6b0fd13897c35181dd876f6349b46a76a5d11f6d5dad54f5b0e70b8308"
   },
   "k4": {
    "bytes": 6484208,
    "file": "P-UV-DUST__density-dense_curl-cw__v3__pro4K__t0.png",
    "px": 4096,
    "sha256": "d6b055e218627c0148a75843486474f0c567876805ed7fa801507ca4f2843e99"
   },
   "kind": "uv",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {},
   "void": [
    0.5000043801670934,
    0.4999812294382575,
    0.18557687545359325
   ],
   "void_diam": 0.3711537509071865
  },
  "P-UV-DUST__density-dense_curl-cw__v4__pro4K__t0": {
   "extra": {
    "black_share": 0.15605580806732178,
    "tangential": 0.5073256492614746
   },
   "family": "P-UV-DUST",
   "k1": {
    "bytes": 421723,
    "file": "P-UV-DUST__density-dense_curl-cw__v4__pro4K__t0.png",
    "px": 1024,
    "sha256": "e8aea8d43b09a229f78e65c7335dc9bd21e88c55333d075660d4edb136321ee3"
   },
   "k4": {
    "bytes": 6845982,
    "file": "P-UV-DUST__density-dense_curl-cw__v4__pro4K__t0.png",
    "px": 4096,
    "sha256": "5552ea49d15f6fd9da1e40d610d7943981ee429284caeadbe18cda446fb5bf70"
   },
   "kind": "uv",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {},
   "void": [
    0.5000380423535781,
    0.4999314545141716,
    0.1915919442951912
   ],
   "void_diam": 0.3831838885903824
  },
  "P-UV-DUST__density-sparse_curl-ccw__v4__pro4K__t0": {
   "extra": {
    "black_share": 0.1933819055557251,
    "tangential": 0.45747679471969604
   },
   "family": "P-UV-DUST",
   "k1": {
    "bytes": 367227,
    "file": "P-UV-DUST__density-sparse_curl-ccw__v4__pro4K__t0.png",
    "px": 1024,
    "sha256": "e5881c9e29329679d1e1c00f836180eaa2be8041b62582ba1e8c56192f41a44b"
   },
   "k4": {
    "bytes": 6286119,
    "file": "P-UV-DUST__density-sparse_curl-ccw__v4__pro4K__t0.png",
    "px": 4096,
    "sha256": "a80f0991b3f62559c66c1211a283118923282ef0604b4d3e9f5320242ddaa2d1"
   },
   "kind": "uv",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {},
   "void": [
    0.500144902955797,
    0.4998079176302761,
    0.20731229370294038
   ],
   "void_diam": 0.41462458740588076
  },
  "P-UV-DUST__density-sparse_curl-ccw__v4__pro4K__t1": {
   "extra": {
    "black_share": 0.1169237494468689,
    "tangential": 0.5175352096557617
   },
   "family": "P-UV-DUST",
   "k1": {
    "bytes": 394361,
    "file": "P-UV-DUST__density-sparse_curl-ccw__v4__pro4K__t1.png",
    "px": 1024,
    "sha256": "e1e0f02ef780b1e29d403ef1aee480d3a1475ba2b328cb6adfeb2e89009d6bc3"
   },
   "k4": {
    "bytes": 6565687,
    "file": "P-UV-DUST__density-sparse_curl-ccw__v4__pro4K__t1.png",
    "px": 4096,
    "sha256": "d8a103a588e010999d559db8392a7b214247928eb2fd799d098997f248d45d17"
   },
   "kind": "uv",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {},
   "void": [
    0.500032263601072,
    0.4998274701578298,
    0.1918668255361878
   ],
   "void_diam": 0.3837336510723756
  },
  "P-UV-DUST__density-sparse_curl-cw__v4__pro4K__t0": {
   "extra": {
    "black_share": 0.09326833486557007,
    "tangential": 0.5299469828605652
   },
   "family": "P-UV-DUST",
   "k1": {
    "bytes": 330929,
    "file": "P-UV-DUST__density-sparse_curl-cw__v4__pro4K__t0.png",
    "px": 1024,
    "sha256": "8368180296627b353c3478236a9a9dedbf9af3e84c4d6f6ae72afdf583cb2c89"
   },
   "k4": {
    "bytes": 6413983,
    "file": "P-UV-DUST__density-sparse_curl-cw__v4__pro4K__t0.png",
    "px": 4096,
    "sha256": "94749b477eaf7e0452c7e692b10b14ee893bd21dc27a8662007a7119c0f1a1de"
   },
   "kind": "uv",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {},
   "void": [
    0.4999944462557279,
    0.4999211124889101,
    0.16555866012571782
   ],
   "void_diam": 0.33111732025143564
  },
  "P-UV-MILKY__band-high_stars-dense__v1__pro4K__t0": {
   "extra": {
    "axis_deg": 139.5808964047202,
    "black_point": 0.0,
    "centroid": [
     0.49783822894096375,
     0.5122942328453064
    ],
    "mean": 0.11445885896682739,
    "width_frac": 0.42380875222366515
   },
   "family": "P-UV-MILKY",
   "k1": {},
   "k4": {},
   "kind": "uv",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-UV-MILKY__band-high_stars-sparse__v1__pro4K__t0": {
   "extra": {
    "axis_deg": 141.92436318649442,
    "black_point": 0.0,
    "centroid": [
     0.5031692385673523,
     0.5118952393531799
    ],
    "mean": 0.08264419436454773,
    "width_frac": 0.3069915949714671
   },
   "family": "P-UV-MILKY",
   "k1": {},
   "k4": {},
   "kind": "uv",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-UV-MILKY__band-high_stars-sparse__v1__pro4K__t1": {
   "extra": {
    "axis_deg": 148.4936900294734,
    "black_point": 0.0,
    "centroid": [
     0.531277596950531,
     0.5406708717346191
    ],
    "mean": 0.10007543861865997,
    "width_frac": 0.35063701246970963
   },
   "family": "P-UV-MILKY",
   "k1": {},
   "k4": {},
   "kind": "uv",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 0,
   "variables": {}
  },
  "P-UV-MILKY__band-low_stars-dense__v1__pro4K__t0": {
   "extra": {
    "axis_deg": 48.111718388677,
    "black_point": 0.0,
    "centroid": [
     0.4672652781009674,
     0.476798415184021
    ],
    "mean": 0.11441493034362793,
    "width_frac": 0.3544673858457593
   },
   "family": "P-UV-MILKY",
   "k1": {
    "bytes": 654823,
    "file": "P-UV-MILKY__band-low_stars-dense__v1__pro4K__t0.png",
    "px": 1024,
    "sha256": "1dc09e2bacd70fab4721b64b12c5b0a041c4893197dcdc5029b8478e44a597c7"
   },
   "k4": {
    "bytes": 9021420,
    "file": "P-UV-MILKY__band-low_stars-dense__v1__pro4K__t0.png",
    "px": 4096,
    "sha256": "9ee1e06642536b8b935f599c6d3812e9616cb95ffac02a9c020bc9080383ade9"
   },
   "kind": "uv",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-UV-MILKY__band-low_stars-dense__v1__pro4K__t1": {
   "extra": {
    "axis_deg": 49.202326273969,
    "black_point": 0.0,
    "centroid": [
     0.476613849401474,
     0.4802008271217346
    ],
    "mean": 0.08931396901607513,
    "width_frac": 0.3549127527265798
   },
   "family": "P-UV-MILKY",
   "k1": {
    "bytes": 556961,
    "file": "P-UV-MILKY__band-low_stars-dense__v1__pro4K__t1.png",
    "px": 1024,
    "sha256": "2fbf3f0e866d2e4cf3113197288cfc1e60ac3f71be025914fd0a53d16b31d233"
   },
   "k4": {
    "bytes": 7567689,
    "file": "P-UV-MILKY__band-low_stars-dense__v1__pro4K__t1.png",
    "px": 4096,
    "sha256": "e6ab75f6aa51aec0615dfa4575fd4a259d39480ba198d60d95199cc59229f673"
   },
   "kind": "uv",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-UV-MILKY__band-low_stars-sparse__v1__pro4K__t0": {
   "extra": {
    "axis_deg": 44.00006252857875,
    "black_point": 0.0,
    "centroid": [
     0.47664082050323486,
     0.508853554725647
    ],
    "mean": 0.09718885272741318,
    "width_frac": 0.35176605053987214
   },
   "family": "P-UV-MILKY",
   "k1": {
    "bytes": 599088,
    "file": "P-UV-MILKY__band-low_stars-sparse__v1__pro4K__t0.png",
    "px": 1024,
    "sha256": "480492011d3a86a9a06c11d1e76b0bbb4671522430c76ddfa166e9a68f0421d8"
   },
   "k4": {
    "bytes": 8041399,
    "file": "P-UV-MILKY__band-low_stars-sparse__v1__pro4K__t0.png",
    "px": 4096,
    "sha256": "0e3d2e18028337757c04aa84f43e0f4d3a401d1ce4329a6e736603bcec806e3e"
   },
   "kind": "uv",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  },
  "P-UV-MILKY__band-low_stars-sparse__v1__pro4K__t1": {
   "extra": {
    "axis_deg": 53.578326501074955,
    "black_point": 0.0,
    "centroid": [
     0.4961598217487335,
     0.4972403347492218
    ],
    "mean": 0.11173774302005768,
    "width_frac": 0.3516490405909928
   },
   "family": "P-UV-MILKY",
   "k1": {
    "bytes": 652116,
    "file": "P-UV-MILKY__band-low_stars-sparse__v1__pro4K__t1.png",
    "px": 1024,
    "sha256": "f423d7d5c35ab2894a0a29a8ab43e272a4df78377752616ad5e042642eb441d0"
   },
   "k4": {
    "bytes": 8655442,
    "file": "P-UV-MILKY__band-low_stars-sparse__v1__pro4K__t1.png",
    "px": 4096,
    "sha256": "886a6f120aadadea3dd67bde242c1398dd85b0d3d0142db5414e46f17587d0be"
   },
   "kind": "uv",
   "mono": 1,
   "score": 0.0,
   "since": 1,
   "until": 0,
   "usable": 1,
   "variables": {}
  }
 }
}
