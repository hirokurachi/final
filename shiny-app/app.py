from shiny import App, render, ui, reactive
from shinywidgets import render_altair, output_widget
import os
import pandas as pd
import altair as alt


page1 = ui.page_fluid(
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_checkbox(
                id="bonds_select_all",
                label="Select all countries",
                value=True
            ),
            ui.input_checkbox_group(
                id="bonds_country",
                label="Countries:",
                choices={}
            ),
            ui.input_checkbox_group(
                id="bonds_issuer_type",
                label="Issuer type:",
                choices=["Government", "Corporate"],
                selected=["Government", "Corporate"]
            ),
            ui.input_checkbox_group(
                id="bond_label",
                label="Bond label:",
                choices=["Green", "Sustainability"],
                selected=["Green", "Sustainability"]
            ),
            ui.input_switch(
                "show_mix",
                "Show borrowing mix",
                value=False
            ),
            title="Filters"
        ),
        ui.panel_conditional(
            "!input.show_mix",
            ui.layout_columns(
                ui.card(
                    ui.card_header("Bonds issuance"),
                    output_widget("chart_bonds_one_column"),
                    height=800
                )
            )
        ),
        ui.panel_conditional(
            "input.show_mix",
            ui.layout_columns(
                ui.card(
                    ui.card_header("Bonds issuance"),
                    output_widget("chart_bonds"),
                    height=800
                ),
                ui.card(
                    ui.card_header("Borrowing mix"),
                    ui.panel_conditional(
                        "input.show_mix",
                        output_widget("chart_borrowing_mix"),
                        height=800
                    )
                ),
                col_widths=(6, 6)
            )
        )
    )
)

page2 = ui.page_fluid(
    ui.page_sidebar(
        ui.sidebar(
            ui.input_switch("show_nominal",
                            "Toggle to switch to nominal values, from the gap from World average", value=False),
            ui.panel_conditional(
                "!input.show_nominal",
                ui.input_checkbox_group(
                    id="epi_country",
                    label="Select countries you want to show:",
                    choices={}
                )
            ),
            ui.panel_conditional(
                "input.show_nominal",
                ui.input_checkbox_group(
                    id="epi_country_and_average",
                    label="Select countries (values) you want to show:",
                    choices={}
                )
            ),
            title="Filters"
        ),
        ui.panel_conditional(
            "!input.show_nominal",
            output_widget("chart_epi_gap")
        ),
        ui.panel_conditional(
            "input.show_nominal",
            output_widget("chart_epi")
        ),
        height=1000,
        title="EPI"
    )
)


page3 = ui.page_sidebar(
    ui.sidebar(
        ui.input_select(
            id="association_country",
            label="Choose a country:",
            choices=[]
        ),
        title="Filters"
    ),
    output_widget("chart_with_trend"),
    height=1000,
    title="Bonds issuance & EPI"
)


app_ui = ui.page_navbar(
    ui.nav_spacer(),  # Push the navbar items to the right
    ui.nav_panel("Bonds issuance", page1),
    ui.nav_panel("EPI", page2),
    ui.nav_panel("Association", page3),
    title="Dashboard for Green+Sustainability bonds & EPI",
)


def server(input, output, session):
    # Store the working directory adress
    @reactive.calc
    def path_cwd():
        """Define working directory"""
        path = r"C:\Users\hkura\Documents\Uchicago\04 2024 Autumn\Python2\final"
        # path = r"C:\Users\LUIS\Documents\GitHub\final"
        return path

    # Load and store base data
    @reactive.calc
    def df_base():
        """Create base df"""
        path_base = os.path.join(
            path_cwd(), r"data\base.csv"
        )
        df = pd.read_csv(path_base)
        return df

    @reactive.calc
    def country_names():
        return list(df_base()["Country Name"].unique())

    # Prepare for Bond issuance chart
    @reactive.effect
    def _():
        """Define multiple choices for countries"""
        choices = {x: x for x in country_names()}
        ui.update_checkbox_group("bonds_country", choices=choices)

    @reactive.calc
    def df_bonds_selected():
        """Create subset of base df based on input"""
        selected_all = input.bonds_select_all()
        selected_country = input.bonds_country()
        selected_issuer_type = input.bonds_issuer_type()
        selected_bond_label = input.bond_label()

        df = df_base()
        if not selected_all:
            df = df[df["Country Name"].isin(selected_country)]

        df = df[(df["issuer_type"].isin(selected_issuer_type))
                & (df["bond_label"].isin(selected_bond_label))]

        return df

    @reactive.calc
    def plot_chart_bonds():
        """Define the bonds issuance plot"""
        subset = df_bonds_selected().dropna(subset="bond_label")
        chart = alt.Chart(subset).mark_bar().encode(
            alt.X("Year:O", axis=alt.Axis(labelAngle=45)),
            alt.Y("amount:Q"),
            alt.Color("Country Name:N")
        )
        return chart

    @render_altair
    def chart_bonds_one_column():
        """Plot the bonds issuance plot"""
        return plot_chart_bonds().properties(
            width=600,
            height=600
        )

    @render_altair
    def chart_bonds():
        """Plot the bonds issuance plot"""
        return plot_chart_bonds().properties(
            width=450,
            height=450
        )

    # Prepare for borrowing mix plot
    @reactive.calc
    def df_borrowing_mix_selected():
        """Create subset of base df based on input"""
        selected_all = input.bonds_select_all()
        selected_country = input.bonds_country()
        selected_issuer_type = input.bonds_issuer_type()
        selected_bond_label = input.bond_label()

        df = df_base().loc[df_base()["Year"] != 2024]
        if not selected_all:
            df = df[df["Country Name"].isin(selected_country)]

        df = df[(df["issuer_type"].isin(selected_issuer_type))
                & (df["bond_label"].isin(selected_bond_label) | df["bond_label"].isna())]

        return df

    @render_altair
    def chart_borrowing_mix():
        """Plot the bonds issuance plot"""
        df_borrowing_mix_selected()["bond_label"] = df_borrowing_mix_selected()[
            "bond_label"].fillna("unrelated bonds")
        chart = alt.Chart(df_borrowing_mix_selected()).mark_bar().encode(
            alt.X("amount:Q", stack="normalize", axis=alt.Axis(labelAngle=45)),
            alt.Y("Year:O"),
            alt.Color("bond_label:N",
                      legend=alt.Legend(orient="bottom", titleOrient="left")),
            alt.Order("bond_label", sort="descending")
        ).properties(
            width=450,
            height=450
        )
        return chart

    # Prepare for EPI gap from World average chart

    @reactive.effect
    def _():
        """Define multiple choices for countries"""
        choices_all = {"All ASEAN+3 countries": "All ASEAN+3 countries"}
        choices_each = {x: x for x in country_names()}
        choices = choices_all | choices_each
        ui.update_checkbox_group("epi_country", choices=choices)

    @reactive.calc
    def df_epi_selected_without_averages():
        """Create subset of base df based on input"""
        if "All ASEAN+3 countries" in input.epi_country():
            df = df_base()
        else:
            df = df_base()[df_base()["Country Name"].isin(input.epi_country())]
        return df

    @render_altair
    def chart_epi_gap():
        """Create line plot for EPI gap from World average"""
        chart_line = alt.Chart(df_epi_selected_without_averages()).mark_line().encode(
            alt.X("Year:O", axis=alt.Axis(labelAngle=45)),
            alt.Y("EPI gap from World average:Q"),
            alt.Color("Country Name:N", legend=None)
        ).properties(
            width=550,
            height=550
        ).transform_filter(
            "(datum.Year==2016)|(datum.Year==2018)|(datum.Year==2020)|(datum.Year==2022)|(datum.Year==2024)"
        )

        chart_text = alt.Chart(df_epi_selected_without_averages()).transform_filter(
            "datum.Year == 2024"
        ).mark_text(
            align="left", baseline="middle", dx=7
        ).encode(
            text="Country Name:N",
            x="Year:O",
            y="EPI gap from World average:Q",
            color="Country Name:N"
        )

        chart = chart_line + chart_text

        return chart

    # Prepare for nominal EPI chart
    @reactive.calc
    def df_epi():
        """Load and store dataset including World/ASEAN+3 average"""
        path_epi = os.path.join(
            path_cwd(), r"data\epi.csv"
        )
        df = pd.read_csv(path_epi)
        return df

    @reactive.effect
    def _():
        """Define multiple choices for countries"""
        choices_all = {"All ASEAN+3 countries": "All ASEAN+3 countries"}
        choices_averages = {"Average (World)": "Average (World)",
                            "Average (ASEAN+3)": "Average (ASEAN+3)"}
        choices_each = {x: x for x in country_names()}

        choices = choices_all | choices_averages | choices_each
        ui.update_checkbox_group("epi_country_and_average", choices=choices)

    @reactive.calc
    def df_epi_selected_with_averages():
        """Create subset of base df based on input"""
        if "All ASEAN+3 countries" in input.epi_country_and_average():
            # only "All ~" is checked
            if len(input.epi_country_and_average()) == 1:
                df = df_epi()[~df_epi()["Country Name"].isin(
                    ["Average (World)", "Average (ASEAN+3)"])]
            else:
                checked_averages = [
                    x for x in input.epi_country_and_average() if (x == "Average (World)") | (x == "Average (ASEAN+3)")]
                checked_all = country_names() + checked_averages
                df = df_epi()[df_epi()["Country Name"].isin(checked_all)]
        else:
            df = df_epi()[df_epi()["Country Name"].isin(
                input.epi_country_and_average())]
        return df

    @render_altair
    def chart_epi():
        """Create line plot for EPI"""
        chart_line = alt.Chart(df_epi_selected_with_averages()).mark_line().encode(
            alt.X("Year:O", axis=alt.Axis(labelAngle=45)),
            alt.Y("EPI:Q",
                  scale=alt.Scale(zero=False)),
            alt.Color("Country Name:N", legend=None)
        ).properties(
            width=550,
            height=550
        ).transform_filter(
            "(datum.Year==2016)|(datum.Year==2018)|(datum.Year==2020)|(datum.Year==2022)|(datum.Year==2024)"
        )

        chart_text = alt.Chart(df_epi_selected_with_averages()).transform_filter(
            "datum.Year == 2024"
        ).mark_text(
            align="left", baseline="middle", dx=7
        ).encode(
            text="Country Name:N",
            x="Year:O",
            y="EPI:Q",
            color="Country Name:N"
        )

        chart = chart_line + chart_text

        return chart

    # Prepare for plot for association btw/n Bonds and EPI
    @reactive.effect
    def _():
        """Create list of countries"""
        choices = country_names()
        ui.update_select("association_country", choices=choices)

    @reactive.calc
    def df_base_normalized():
        # Drop bonds with no label
        df = df_base().dropna(subset="bond_label")

        # Normalize amount and EPI gap from world average
        df["amount_norm"] = (df["amount"] - df["amount"].min()) / (
            df["amount"].max() - df["amount"].min())

        df["EPI_gap_norm"] = (df["EPI gap from World average"] - df["EPI gap from World average"].min()) / (
            df["EPI gap from World average"].max() - df["EPI gap from World average"].min())

        return df

    @render_altair
    def chart_with_trend():
        """Plot the scatter plots for each variable"""
        df = df_base_normalized().melt(
            id_vars=["Country Name", "Year"],
            value_vars=["amount_norm", "EPI_gap_norm"],
            var_name="Variables",
            value_name="Bonds / EPI Changes (normalized)"
        ).dropna()

        df_amount = df[(df["Country Name"]
                        == input.association_country()) & (df["Variables"] == "amount_norm")]
        df_amount = df_amount.groupby(["Country Name", "Year", "Variables"]).agg(
            result=("Bonds / EPI Changes (normalized)", "sum")
        ).reset_index().rename({"result": "Bonds / EPI Changes (normalized)"}, axis=1)

        df_epi = df[(df["Country Name"]
                     == input.association_country()) & (df["Variables"] == "EPI_gap_norm")]
        df = pd.concat(
            [df_epi, df_amount])

        chart_variables = alt.Chart(df).mark_point().transform_filter(
            alt.FieldEqualPredicate(
                field="Country Name", equal=input.association_country())
        ).encode(
            alt.X("Year:O", axis=alt.Axis(labelAngle=45)),
            alt.Y("Bonds / EPI Changes (normalized):Q"),
            alt.Color("Variables:N")
        ).properties(
            width=500,
            height=500
        )

        trend_line = alt.Chart(df).mark_line().transform_filter(
            alt.FieldEqualPredicate(
                field="Country Name", equal=input.association_country())
        ).transform_regression(
            "Year",
            "Bonds / EPI Changes (normalized)",
            groupby=["Variables"],
            method="linear"
        ).encode(
            alt.X("Year:O", axis=alt.Axis(labelAngle=45)),
            alt.Y("Bonds / EPI Changes (normalized):Q"),
            alt.Color("Variables:N")
        )

        chart = chart_variables + trend_line

        return chart


app = App(app_ui, server)
