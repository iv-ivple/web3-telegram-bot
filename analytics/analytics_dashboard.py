from analytics.token_analytics import TokenAnalytics
from analytics.wallet_analytics import WalletAnalytics
from utils.hybrid_fetcher import HybridDataFetcher
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

class AnalyticsDashboard:
    def __init__(self):
        self.token_analytics = TokenAnalytics()
        self.wallet_analytics = WalletAnalytics()
    
    def generate_token_report(self, token_address: str):
        """Generate comprehensive token report"""
        print(f"\n=== Token Analytics Report ===")
        print(f"Token: {token_address}")
        print(f"Generated: {datetime.now()}\n")
        
        # 24h Volume
        volume_24h = self.token_analytics.get_token_volume_24h(token_address)
        print(f"24h Volume: ${volume_24h:,.2f}")
        
        # Price history
        price_df = self.token_analytics.get_price_history(token_address, days=7)
        self._plot_price_history(price_df, token_address)
        
        # Top traders
        top_traders = self.token_analytics.get_top_traders(token_address)
        print("\nTop 10 Traders:")
        for i, trader in enumerate(top_traders, 1):
            print(f"{i}. {trader['address']}: ${trader['volume']:,.2f}")
    
    def generate_wallet_report(self, wallet_address: str):
        """Generate wallet activity report"""
        # Implementation here
        pass
    
    def _plot_price_history(self, df, token_address):
        """Create price chart"""
        plt.figure(figsize=(12, 6))
        plt.plot(df['timestamp'], df['price'])
        plt.title(f'Price History - {token_address[:10]}...')
        plt.xlabel('Date')
        plt.ylabel('Price (USD)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'reports/price_history_{token_address}.png')
        plt.close()

if __name__ == "__main__":
    dashboard = AnalyticsDashboard()
    
    # Example: Analyze USDC
    USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    dashboard.generate_token_report(USDC)
