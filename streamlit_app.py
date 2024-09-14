import pandas as pd
import pydeck as pdk

import streamlit as st


def fetch_school(url):
    df_schools = (
        pd.read_html(url, index_col=0)[0]
        .apply(lambda x: pd.to_numeric(x.str.rstrip("人").str.replace(",", ""), errors="coerce"))
        .drop("合計")
        .rename(columns={"新1年": "1年"})
    )
    df_schools.index.name = "name"
    return df_schools


def fetch_location():
    url = "https://www.city.imabari.ehime.jp/opendata/data/school.csv"

    df_locations = pd.read_csv(url, encoding="sjis", dtype=str)

    df_locations = df_locations.rename(
        columns={"施設名": "name", "所在地": "address", "電話番号": "tel", "緯度": "lat", "経度": "lon"}
    )

    df_locations.loc[:, "name"] = df_locations["name"].str.replace("今治市立", "", regex=True)
    df_locations.loc[:, "tel"] = df_locations["tel"].str.strip()

    df_locations.loc[:, "lat"] = pd.to_numeric(df_locations["lat"], errors="coerce")
    df_locations.loc[:, "lon"] = pd.to_numeric(df_locations["lon"], errors="coerce")

    return df_locations.set_index("name")


@st.cache_data
def load_data():
    df_elementary = fetch_school("https://www.city.imabari.ehime.jp/gakukyou/shogakkou.html")
    df_middle = fetch_school("https://www.city.imabari.ehime.jp/gakukyou/chugakkou.html")

    df_schools = pd.concat([df_elementary, df_middle])

    df_locations = fetch_location()

    return df_schools, df_locations


st.title("今治市の小学校・中学校")


df_schools, df_locations = load_data()

school_type = st.selectbox(
    "学校を選んでください",
    ("小学校", "中学校"),
)

if school_type:
    st.subheader(school_type)
    df_school = df_schools.loc[df_schools.index.str.endswith(school_type), :].copy().dropna(how="all", axis=1)

    df = df_school.join(df_locations)

    st.bar_chart(df_school.drop("計", axis=1), use_container_width=True)

    st.dataframe(
        df_school,
        width=700,
    )

    col = df_school.columns.tolist()

    st.subheader("学年")

    option = st.selectbox(
        "学年を選んでください",
        col,
        index=len(col) - 1,
    )

    if option:
        st.bar_chart(df_school[option], use_container_width=True)

        d = {
            "1年": "gr1",
            "2年": "gr2",
            "3年": "gr3",
            "4年": "gr4",
            "5年": "gr5",
            "6年": "gr6",
            "計": "total",
        }

        chois = d.get(option, "total")

        df = df.rename(
            columns={
                "1年": "gr1",
                "2年": "gr2",
                "3年": "gr3",
                "4年": "gr4",
                "5年": "gr5",
                "6年": "gr6",
                "計": "total",
            }
        )

        st.pydeck_chart(
            pdk.Deck(
                map_style=None,
                initial_view_state=pdk.ViewState(
                    latitude=df["lat"].mean(),
                    longitude=df["lon"].mean(),
                    zoom=12,
                    pitch=50,
                ),
                layers=[
                    pdk.Layer(
                        "ColumnLayer",
                        data=df,
                        get_position=["lon", "lat"],
                        get_elevation=chois,
                        elevation_scale=5,
                        radius=100,
                        get_fill_color=[180, 0, 200, 140],
                        pickable=True,
                        extruded=True,
                    ),
                ],
            )
        )
