import json
import sys

import pandas as pd


def vis_kildeoverblik(filsti):
    indhold = json.load(open(filsti, encoding="utf-8"))

    konvolut = {nøgle: værdi for nøgle, værdi in indhold.items() if nøgle != "records"}
    print("KONVOLUT:", konvolut)

    data = pd.DataFrame(indhold["records"])
    print(f"\n{len(data)} rækker, {data.shape[1]} kolonner\n")

    print("EN RIGTIG RÆKKE (den første):")
    print(data.head(1).T)
    print()

    kolonneoversigt = pd.DataFrame({
        "dtype": data.dtypes.astype(str),
        "tomme": data.isna().sum(),
        "unikke": data.nunique(),
        "min": data.min(numeric_only=False).astype(str),
        "max": data.max(numeric_only=False).astype(str),
    })
    print(kolonneoversigt.to_string())

    print("\nPriceArea:", data["PriceArea"].value_counts().to_dict())


vis_kildeoverblik(sys.argv[1])