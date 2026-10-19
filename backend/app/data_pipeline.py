import pandas as pd
import numpy as np


FEATURES = [
    "current_load",
    "previous_load",
    "recent_boarding",
    "recent_alighting",
    "recent_net_flow",
    "hist_next_boarding",
    "hist_next_alighting",
    "stop_position",
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
    "hist_load_mean",
]


def load_data(path):
    df = pd.read_csv(path, parse_dates=["event_timestamp"])

    required = [
        "route_id",
        "stop_id",
        "event_timestamp",
        "boardings",
        "alightings",
        "passenger_load",
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df.dropna(subset=required).copy()

    for c in ["boardings", "alightings", "passenger_load"]:
        df[c] = (
            pd.to_numeric(df[c], errors="coerce")
            .fillna(0)
            .clip(lower=0)
        )

    df["route_id"] = df["route_id"].astype(str)
    df["stop_id"] = df["stop_id"].astype(str)

    return df.sort_values("event_timestamp").reset_index(drop=True)


def contextualize(df):
    x = df.sort_values(
        ["route_id", "event_timestamp"]
    ).copy()

    if "service_date" in x.columns:
        g = x.groupby(
            ["route_id", "service_date"],
            sort=False
        )
    else:
        g = x.groupby(
            "route_id",
            sort=False
        )

    x["previous_load"] = g.passenger_load.shift(1)
    x["recent_boarding"] = g.boardings.shift(1)
    x["recent_alighting"] = g.alightings.shift(1)

    x["recent_net_flow"] = (
        x.recent_boarding.fillna(x.boardings)
        - x.recent_alighting.fillna(x.alightings)
    )

    x["stop_position"] = (
        g.stop_id.transform(
            lambda s: pd.factorize(s)[0]
        ).astype(float)
    )

    hour = (
        x.event_timestamp.dt.hour
        + x.event_timestamp.dt.minute / 60
    )

    weekday = x.event_timestamp.dt.dayofweek

    x["hour_sin"] = np.sin(
        2 * np.pi * hour / 24
    )

    x["hour_cos"] = np.cos(
        2 * np.pi * hour / 24
    )

    x["weekday_sin"] = np.sin(
        2 * np.pi * weekday / 7
    )

    x["weekday_cos"] = np.cos(
        2 * np.pi * weekday / 7
    )

    x["current_load"] = x.passenger_load

    return x


def historical_stats(train):
    x = train.copy()

    x["hour"] = x.event_timestamp.dt.hour
    x["weekday"] = x.event_timestamp.dt.dayofweek

    if "service_date" in x.columns:
        g = x.groupby(
            ["route_id", "service_date"],
            sort=False
        )
    else:
        g = x.groupby(
            "route_id",
            sort=False
        )

    x["next_boarding"] = g.boardings.shift(-1)
    x["next_alighting"] = g.alightings.shift(-1)
    x["next_load"] = g.passenger_load.shift(-1)

    def make_stats(columns):
        result = (
            x.groupby(columns)[
                [
                    "next_boarding",
                    "next_alighting",
                    "next_load",
                ]
            ]
            .mean()
            .reset_index()
        )

        return result.to_dict("records")

    return {
        "route_stop_hour_day": make_stats(
            [
                "route_id",
                "stop_id",
                "hour",
                "weekday",
            ]
        ),
        "route_stop_hour": make_stats(
            [
                "route_id",
                "stop_id",
                "hour",
            ]
        ),
        "stop": make_stats(
            ["stop_id"]
        ),
        "global": {
            c: float(x[c].mean())
            for c in [
                "next_boarding",
                "next_alighting",
                "next_load",
            ]
        },
    }


def attach_history(x, stats):
    """
    Fast historical-stat lookup.

    Same fallback hierarchy as the original implementation:

    1. route + stop + hour + weekday
    2. route + stop + hour
    3. stop
    4. global mean

    The original implementation performed a full row-by-row
    scan through the statistics. This version converts the
    statistics into dictionaries and performs O(1) lookups.
    """

    x = x.copy()

    # ---------------------------------------------------------
    # Build dictionaries for fast lookup
    # ---------------------------------------------------------

    route_stop_hour_day = {}

    for row in stats["route_stop_hour_day"]:
        key = (
            str(row["route_id"]),
            str(row["stop_id"]),
            int(row["hour"]),
            int(row["weekday"]),
        )

        route_stop_hour_day[key] = row

    route_stop_hour = {}

    for row in stats["route_stop_hour"]:
        key = (
            str(row["route_id"]),
            str(row["stop_id"]),
            int(row["hour"]),
        )

        route_stop_hour[key] = row

    stop_stats = {}

    for row in stats["stop"]:
        key = str(row["stop_id"])
        stop_stats[key] = row

    global_stats = stats["global"]

    # ---------------------------------------------------------
    # Extract row information as arrays
    # ---------------------------------------------------------

    route_values = x["route_id"].astype(str).to_numpy()
    stop_values = x["stop_id"].astype(str).to_numpy()

    hour_values = (
        x["event_timestamp"]
        .dt.hour
        .to_numpy()
    )

    weekday_values = (
        x["event_timestamp"]
        .dt.dayofweek
        .to_numpy()
    )

    # ---------------------------------------------------------
    # Fast lookup
    # ---------------------------------------------------------

    hist_boarding = np.empty(len(x), dtype=float)
    hist_alighting = np.empty(len(x), dtype=float)
    hist_load = np.empty(len(x), dtype=float)

    for i in range(len(x)):

        route = route_values[i]
        stop = stop_values[i]
        hour = int(hour_values[i])
        weekday = int(weekday_values[i])

        # ---------------------------------------------
        # Level 1:
        # route + stop + hour + weekday
        # ---------------------------------------------

        key1 = (
            route,
            stop,
            hour,
            weekday,
        )

        row = route_stop_hour_day.get(key1)

        # ---------------------------------------------
        # Level 2:
        # route + stop + hour
        # ---------------------------------------------

        if row is None:

            key2 = (
                route,
                stop,
                hour,
            )

            row = route_stop_hour.get(key2)

        # ---------------------------------------------
        # Level 3:
        # stop
        # ---------------------------------------------

        if row is None:
            row = stop_stats.get(stop)

        # ---------------------------------------------
        # Level 4:
        # global fallback
        # ---------------------------------------------

        if row is None:
            hist_boarding[i] = global_stats["next_boarding"]
            hist_alighting[i] = global_stats["next_alighting"]
            hist_load[i] = global_stats["next_load"]

        else:
            hist_boarding[i] = (
                row["next_boarding"]
                if pd.notna(row["next_boarding"])
                else global_stats["next_boarding"]
            )

            hist_alighting[i] = (
                row["next_alighting"]
                if pd.notna(row["next_alighting"])
                else global_stats["next_alighting"]
            )

            hist_load[i] = (
                row["next_load"]
                if pd.notna(row["next_load"])
                else global_stats["next_load"]
            )

    # ---------------------------------------------------------
    # Attach historical features
    # ---------------------------------------------------------

    x["hist_next_boarding"] = hist_boarding
    x["hist_next_alighting"] = hist_alighting
    x["hist_load_mean"] = hist_load

    # Missing previous-flow values at the beginning of a trip
    # fall back to current load / current event values.
    x["previous_load"] = (
        x["previous_load"]
        .fillna(x["current_load"])
    )

    x["recent_boarding"] = (
        x["recent_boarding"]
        .fillna(x["current_load"])
    )

    x["recent_alighting"] = (
        x["recent_alighting"]
        .fillna(x["current_load"])
    )

    return x


def targets(x):
    x = x.copy()

    if "service_date" in x.columns:
        g = x.groupby(
            ["route_id", "service_date"],
            sort=False
        )
    else:
        g = x.groupby(
            "route_id",
            sort=False
        )

    for h in (1, 2, 3):
        x[f"target_{h}"] = (
            g.passenger_load.shift(-h)
        )

    return x


def matrix(x):
    return (
        x[FEATURES]
        .astype(float)
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .fillna(0)
        .to_numpy()
    )