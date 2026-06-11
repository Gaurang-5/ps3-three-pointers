import pandas as pd
import json
import os
import matplotlib.pyplot as plt
import logging
import shutil

logger = logging.getLogger(__name__)


class DashboardExporter:
    def __init__(
        self, portfolio_manager, metrics_report, signal_history, output_dir="output"
    ):
        self.pm = portfolio_manager
        self.metrics = metrics_report
        self.signals = signal_history
        self.output_dir = output_dir
        self.frontend_dir = os.path.join("frontend", "public", "data")

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.frontend_dir, exist_ok=True)

    def export_all(self):
        logger.info(
            f"Exporting dashboard data to {self.output_dir}/ and {self.frontend_dir}/"
        )
        self._export_timeseries()
        self._export_allocations()
        self._export_metrics()
        self._export_signals()
        self._plot_all()

    def _save_to_both(self, df: pd.DataFrame, filename: str):
        df.to_csv(os.path.join(self.output_dir, filename), index=False)
        df.to_csv(os.path.join(self.frontend_dir, filename), index=False)

    def _export_timeseries(self):
        df = self.pm.get_history_df()
        if len(df) > 0:
            self._save_to_both(df, "portfolio_timeseries.csv")

    def _export_allocations(self):
        df = self.pm.get_history_df()
        if len(df) == 0:
            return

        assets = ["Equity", "Oil", "Gold", "Bond"]
        alloc_data = []

        for _, row in df.iterrows():
            total_val = row.get("Total_Value", 1)
            date = row["Date"]
            for asset in assets:
                shares_col = f"{asset}_Shares"
                price_col = f"{asset}_Price"
                if shares_col in row and price_col in row:
                    val = row.get(shares_col, 0) * row.get(price_col, 0)
                    if val > 0:
                        alloc_data.append(
                            {"date": date, "ticker": asset, "weight": val / total_val}
                        )

        if alloc_data:
            df_alloc = pd.DataFrame(alloc_data)
            self._save_to_both(df_alloc, "asset_allocations.csv")

    def _export_metrics(self):
        # Save to output/
        with open(os.path.join(self.output_dir, "metrics_summary.json"), "w") as f:
            json.dump(self.metrics, f, indent=4)
        # Save to frontend/public/data/
        with open(os.path.join(self.frontend_dir, "metrics_summary.json"), "w") as f:
            json.dump(self.metrics, f, indent=4)

    def _export_signals(self):
        if self.signals:
            df_sig = pd.DataFrame(self.signals)
            self._save_to_both(df_sig, "signal_heatmap.csv")

    def _plot_all(self):
        df = self.pm.get_history_df()
        if len(df) == 0:
            return

        try:
            # 1. Line chart: Portfolio value over time
            plt.figure(figsize=(10, 5))
            plt.plot(
                pd.to_datetime(df["Date"]),
                df["Total_Value"],
                label="Portfolio Value",
                color="#1f77b4",
            )
            plt.title("Portfolio Value Over Time")
            plt.xlabel("Date")
            plt.ylabel("Value ($)")
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, "portfolio_value.png"))
            plt.close()

            # 2. Area chart for allocations could be added here, but simplified for standard plots
            logger.info("Visualizations generated successfully.")
        except Exception as e:
            logger.error(f"Failed to generate visualizations: {e}")
