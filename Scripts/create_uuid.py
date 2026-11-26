#!/usr/bin/env python3

import argparse
from pathlib import Path
import pandas as pd
from helper_functions import excel_to_df
import uuid

def main():

    event_id = str(
    uuid.uuid5(
        uuid.NAMESPACE_DNS,
        "ProjectA-T1-25112026"
        )
    )

    print(event_id)

    ocurrence_id = str(
    uuid.uuid5(
        uuid.NAMESPACE_DNS,
        "ProjectA0000001"
        )
    )

    print(ocurrence_id)


if __name__ == "__main__":
    main()

