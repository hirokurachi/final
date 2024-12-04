from shiny import App, render, ui, reactive
from shinywidgets import render_altair, output_widget
import os
import pandas as pd
import altair as alt


page1 = ui.page_fluid(
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_checkbox(
                id="bond_select_all",
                label="Select all countries",
                value=True
            ),
            ui.input_checkbox_group(
                id="bond_country",
                label="Countries:",
                choices={}
            ),
            ui.input_checkbox_group(
                id="bond_issuer_type",
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
        ui.layout_columns(
            ui.card(
                ui.card_header("Bonds issuance"),
                output_widget("chart_bonds")
            ),
            ui.card(
                ui.card_header("Borrowing mix"),
                ui.panel_conditional(
                    "input.show_mix",
                    output_widget("chart_borrowing_mix"),
                    height=1000
                )
            )
        )
    )
)

page2 = ui.page_fluid(
    ui.page_sidebar(
        ui.sidebar(
            ui.input_switch("switch_to_origin",
                            "Toggle to switch to original values, from the gap from World average", value=False),
            ui.panel_conditional(
                "!input.switch_to_origin",
                ui.input_checkbox_group(
                    id="epi_country",
                    label="Select countries you want to show:",
                    choices={}
                )
            ),
            ui.panel_conditional(
                "input.switch_to_origin",
                ui.input_checkbox_group(
                    id="epi_country_and_average",
                    label="Select countries (values) you want to show:",
                    choices={}
                )
            ),
            title="Filters"
        ),
        ui.panel_conditional(
            "!input.switch_to_origin",
            output_widget("chart_index_standardized")
        ),
        ui.panel_conditional(
            "input.switch_to_origin",
            output_widget("chart_index")
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
        # path = r"C:\Users\hkura\Documents\Uchicago\04 2024 Autumn\Python2\final"
        path = r"C:\Users\LUIS\Documents\GitHub\final"
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
        ui.update_checkbox_group("bond_country", choices=choices)

    @reactive.calc
    def df_bonds_selected():
        """Create subset of base df based on input"""

        selected_country = input.bond_country()
        if selected_country:
            df = df_base()
            df = df[df["Country Name"].isin(selected_country)]

        selected_all = input.bond_select_all()
        if selected_all:
            df = df_base()

        selected_issuer_type = input.bond_issuer_type()
        if selected_issuer_type:
            df = df[df["issuer_type"].isin(selected_issuer_type)]

        selected_bond_label = input.bond_label()
        if selected_bond_label:
            df = df[df["bond_label"].isin(selected_bond_label)]

        return df

    @render_altair
    def chart_bonds():
        filtered_df = df_bonds_selected().dropna(subset="bond_label")

        """Plot the bonds issuance plot"""
        chart = alt.Chart(filtered_df).mark_bar().encode(
            alt.X("Year:O"),
            alt.Y("amount:Q"),
            alt.Color("Country Name:N")
        ).properties(
            width=500,
            height=500
        )
        return chart

    @render_altair
    def chart_borrowing_mix():
        filtered_df = df_bonds_selected().dropna(subset="bond_label")

        """Plot the bonds issuance plot"""
        chart = alt.Chart(filtered_df).mark_bar().encode(
            alt.X("Year:O"),
            alt.Y("amount:Q"),
            alt.Color("Country Name:N")
        ).properties(
            width=500,
            height=500
        )
        return chart

    # Prepare for EPI chart

    # Standardized EPI plot: plot gap from World average
    @reactive.effect
    def _():
        """Create list of countries"""
        choices = country_names()
        ui.update_select("association_country", choices=choices)

    @reactive.calc
    def df_epi_selected_without_averages():
        """Create subset of base df based on input"""
        if "All ASEAN+3 countries" in input.epi_country():
            df = df_base()
        else:
            df = df_base()[df_base()["Country Name"].isin(input.epi_country())]
        return df

    @reactive.calc
    def chart_index_standardized_line():
        """Create line plot for EPI gap from World average"""
        chart = alt.Chart(df_epi_selected_without_averages()).mark_line().encode(
            alt.X("Year:O"),
            alt.Y("EPI gap from World average:Q"),
            alt.Color("Country Name:N", legend=None)
        ).properties(
            width=500,
            height=500
        ).transform_filter(
            "(datum.Year==2016)|(datum.Year==2018)|(datum.Year==2020)|(datum.Year==2022)|(datum.Year==2024)"
        )
        return chart

    @reactive.calc
    def chart_index_standardized_text():
        """Define texts align with line plot for EPI"""
        chart = alt.Chart(df_epi_selected_without_averages()).transform_filter(
            "datum.Year == 2024"
        ).mark_text(
            align="left", baseline="middle", dx=7
        ).encode(
            text="Country Name:N",
            x="Year:O",
            y="EPI gap from World average:Q",
            color="Country Name:N"
        )
        return chart

    @render_altair
    def chart_index_standardized():
        """Plot the line plot + text for EPI"""
        return chart_index_standardized_line() + chart_index_standardized_text()

    # original EPI plot including World/ASEAN+3 average
    @reactive.calc
    def df_index():
        """Load and store dataset including World/ASEAN+3 average"""
        path_index = os.path.join(
            path_cwd(), r"data\index.csv"
        )
        df = pd.read_csv(path_index)
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
                df = df_index()[~df_index()["Country Name"].isin(
                    ["Average (World)", "Average (ASEAN+3)"])]
            else:
                checked_averages = [
                    x for x in input.epi_country_and_average() if (x == "Average (World)") | (x == "Average (ASEAN+3)")]
                checked_all = country_names() + checked_averages
                df = df_index()[df_index()["Country Name"].isin(checked_all)]
        else:
            df = df_index()[df_index()["Country Name"].isin(
                input.epi_country_and_average())]
        return df

    @reactive.calc
    def chart_index_line():
        """Create line plot for EPI"""
        chart = alt.Chart(df_epi_selected_with_averages()).mark_line().encode(
            alt.X("Year:O"),
            alt.Y("EPI:Q"),
            alt.Color("Country Name:N", legend=None)
        ).properties(
            width=500,
            height=500
        ).transform_filter(
            "(datum.Year==2016)|(datum.Year==2018)|(datum.Year==2020)|(datum.Year==2022)|(datum.Year==2024)"
        )
        return chart

    @reactive.calc
    def chart_index_text():
        """Define texts align with line plot for EPI"""
        chart = alt.Chart(df_epi_selected_with_averages()).transform_filter(
            "datum.Year == 2024"
        ).mark_text(
            align="left", baseline="middle", dx=7
        ).encode(
            text="Country Name:N",
            x="Year:O",
            y="EPI:Q",
            color="Country Name:N"
        )
        return chart

    @render_altair
    def chart_index():
        """Plot the line plot + text for EPI"""
        return chart_index_line() + chart_index_text()

    # Prepare for plot for association btw/n Bonds and EPI

    @reactive.effect
    def _():
        """Create list of countries"""
        choices = country_names()
        ui.update_select("association_country", choices=choices)
  
    @reactive.calc
    def normalize_data():
        # Drop bonds with no label
        df_base_filtered = df_base().dropna(subset="bond_label")
        
        # Normalize amount and EPI gap from world average
        df_base_filtered["amount_norm"] = (df_base_filtered["amount"] - df_base_filtered["amount"].min()) / (df_base_filtered["amount"].max() - df_base_filtered["amount"].min())

        df_base_filtered["EPI_gap_norm"] = (df_base_filtered["EPI gap from World average"] - df_base_filtered["EPI gap from World average"].min()) / (df_base_filtered["EPI gap from World average"].max() - df_base_filtered["EPI gap from World average"].min())

        return df_base_filtered

    @render_altair
    def chart_with_trend():
        df_base_filtered = normalize_data()

        """Plot the bonds issuance plot"""
        chart_bonds = alt.Chart(df_base_filtered).mark_point().transform_filter(
            alt.FieldEqualPredicate(field="Country Name", equal=input.association_country())
        ).encode(
            alt.X("Year:O"),
            alt.Y("sum(amount_norm):Q"),
            alt.Color("Country Name:N")
        ).properties(
            width=500,
            height=500
        )

        bonds_trend_line = alt.Chart(df_base_filtered).mark_line(color="red").transform_filter(
            alt.FieldEqualPredicate(field="Country Name", equal=input.association_country())
        ).transform_aggregate(
            sum_amount="sum(amount_norm)",
            groupby=["Year"]
        ).transform_regression(
            "Year", "sum_amount", method="linear"
        ).encode(
            alt.X("Year:O"),
            alt.Y("sum_amount:Q")
        )

        chart_index_standardized = alt.Chart(df_base_filtered).mark_point().transform_filter(
            alt.FieldEqualPredicate(field="Country Name", equal=input.association_country())
        ).encode(
            alt.X("Year:O"),
            alt.Y("EPI_gap_norm:Q"),
            alt.Color("Country Name:N", legend=None)
        ).properties(
            width=500,
            height=500
        ).transform_filter(
            "(datum.Year==2016)|(datum.Year==2018)|(datum.Year==2020)|(datum.Year==2022)|(datum.Year==2024)"
        )

        index_trend_line = alt.Chart(df_base_filtered).mark_line(color="blue").transform_filter(
            alt.FieldEqualPredicate(field="Country Name", equal=input.association_country())
        ).transform_regression(
            "Year", "EPI_gap_norm", method="linear"
        ).encode(
            alt.X("Year:O"),
            alt.Y("EPI_gap_norm:Q")
        )

        combined_bonds = chart_bonds + bonds_trend_line + chart_index_standardized + index_trend_line

        return combined_bonds


app = App(app_ui, server)
