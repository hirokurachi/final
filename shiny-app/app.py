from shiny import App, render, ui, reactive
from shinywidgets import render_altair, output_widget
import os
import pandas as pd
import altair as alt

# The contents of the first 'page' is a navset with two 'panels'.
page1 = ui.card(
    ui.card_header("Bonds issuance"),
    output_widget("chart_bonds"),
    height=1000
)


page2 = ui.card(
    ui.card_header("EPI"),
    output_widget("chart_index"),
    height=1000
)


# page3 = ui.navset_card_underline(
#     # ui.nav_panel("Plot", ui.output_plot("hist")),
#     # ui.nav_panel("Table", ui.output_data_frame("data")),
#     # footer=ui.input_select(
#     #     "var", "Select variable", choices=["bill_length_mm", "body_mass_g"]
#     # ),
#     # title="Penguins data",
# )


app_ui = ui.page_navbar(
    ui.nav_spacer(),  # Push the navbar items to the right
    ui.nav_panel("Bonds issuance", page1),
    ui.nav_panel("EPI", page2),
    #    ui.nav_panel("Association", page3),
    title="Dashboard for Green+Sustainability bonds & EPI",
)


def server(input, output, session):
    # Save the working directory adress
    @reactive.calc
    def path_cwd():
        """Define working directory"""
        path = r"C:\Users\hkura\Documents\Uchicago\04 2024 Autumn\Python2\final"
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

    @render_altair
    def chart_bonds():
        """Plot the bonds issuance plot"""
        chart = alt.Chart(df_base()).mark_bar().encode(
            alt.X("Year:O"),
            alt.Y("total_combined:Q"),
            alt.Color("Country Name:N")
        ).transform_calculate(
            total_combined="datum.total_green + datum.total_sustainability"
        ).properties(
            width=500,
            height=500
        )
        return chart

    @reactive.calc
    def chart_index_line():
        """Create line plot for EPI"""
        chart = alt.Chart(df_base()).mark_line().encode(
            alt.X("Year:O"),
            alt.Y("EPI gap from average:Q"),
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
        chart = alt.Chart(df_base()).transform_filter(
            "datum.Year == 2024"
        ).mark_text(
            align="left", baseline="middle", dx=7
        ).encode(
            text="Country Name:N",
            x="Year:O",
            y="EPI gap from average:Q",
            color="Country Name:N"
        )
        return chart

    @render_altair
    def chart_index():
        """Plot the line plot + text for EPI"""
        return chart_index_line() + chart_index_text()


app = App(app_ui, server)
