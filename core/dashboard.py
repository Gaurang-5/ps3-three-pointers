import pandas as pd
import json
import os
import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)

class DashboardExporter:
    def __init__(self, portfolio_manager, metrics_report, signal_history, output_dir='output'):
        self.pm = portfolio_manager
        self.metrics = metrics_report
        self.signals = signal_history
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def export_all(self):
        logger.info(f"Exporting dashboard data to {self.output_dir}/")
        self._export_timeseries()
        self._export_allocations()
        self._export_metrics()
        self._export_signals()
        self._plot_all()
        
    def _export_timeseries(self):
        df = self.pm.get_history_df()
        if len(df) > 0:
            df.to_csv(os.path.join(self.output_dir, 'portfolio_timeseries.csv'), index=False)
        
    def _export_allocations(self):
        df = self.pm.get_history_df()
        if len(df) == 0:
            return
            
        alloc_data = []
        for _, row in df.iterrows():
            weight = (row.get('Equity_Shares', 0) * row.get('Equity_Price', 0)) / row.get('Total_Value', 1)
            alloc_data.append({
                'date': row['Date'],
                'ticker': 'Equity',
                'weight': weight
            })
        pd.DataFrame(alloc_data).to_csv(os.path.join(self.output_dir, 'asset_allocations.csv'), index=False)
        
    def _export_metrics(self):
        with open(os.path.join(self.output_dir, 'metrics_summary.json'), 'w') as f:
            json.dump(self.metrics, f, indent=4)
            
    def _export_signals(self):
        if self.signals:
            pd.DataFrame(self.signals).to_csv(os.path.join(self.output_dir, 'signal_heatmap.csv'), index=False)
        
    def _plot_all(self):
        df = self.pm.get_history_df()
        if len(df) == 0:
            return
            
        try:
            # 1. Line chart: Portfolio value over time
            plt.figure(figsize=(10, 5))
            plt.plot(pd.to_datetime(df['Date']), df['Total_Value'], label='Portfolio Value')
            plt.title('Portfolio Value Over Time')
            plt.xlabel('Date')
            plt.ylabel('Value ($)')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'portfolio_value.png'))
            plt.close()
            
            # 2. Bar chart: Final asset allocation
            plt.figure(figsize=(6, 4))
            final_cash = df['Cash'].iloc[-1]
            final_equity = df['Equity_Shares'].iloc[-1] * df['Equity_Price'].iloc[-1]
            total = final_cash + final_equity
            if total > 0:
                plt.bar(['Cash', 'Equity'], [final_cash/total, final_equity/total], color=['#2ca02c', '#1f77b4'])
                plt.title('Final Asset Allocation')
                plt.ylabel('Weight')
                plt.ylim(0, 1)
                plt.tight_layout()
                plt.savefig(os.path.join(self.output_dir, 'final_allocation.png'))
            plt.close()
            logger.info("Visualizations generated successfully.")
        except Exception as e:
            logger.error(f"Failed to generate visualizations: {e}")
