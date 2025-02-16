import json
import ccxt.async_support as ccxt
import asyncio
import platform
from tabulate import tabulate


# Set the event loop policy for Windows
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def fetch_tickers(exchange_name):
    """Fetch all tickers from a given exchange asynchronously."""
    try:
        exchange_class = getattr(ccxt, exchange_name)
        exchange = exchange_class({'enableRateLimit': True})  # Enable rate-limiting

        await exchange.load_markets()  # Load available trading pairs
        tickers = await exchange.fetch_tickers()  # Fetch all tickers at once
        await exchange.close()  # Close connection

        return {exchange_name: tickers}
    except Exception as e:
        await exchange.close()
        return {exchange_name: f"Error: {str(e)}"}

async def fetch_all_exchanges():
    """Fetch tickers from multiple crypto exchanges asynchronously."""
    exchanges = [
        'binance','kraken','coinbase','bitfinex','huobi','okx',
        'ace','alpaca','ascendex','bequant','bigone','binanceus',
        'bit2c','bitbank','bitbns','bitflyer','bithumb','bitopro'
        ]
    tasks = [fetch_tickers(exchange) for exchange in exchanges]
    results = await asyncio.gather(*tasks)

    all_prices = {}
    for result in results:
        all_prices.update(result)
    
    return all_prices

def find_arbitrage_opportunities(price_data, min_spread=10, max_spread=50):
    """Find arbitrage opportunities based on price differences."""
    opportunities = []
    pair_prices = {}

    # Organize prices by trading pair
    for exchange, tickers in price_data.items():
        if isinstance(tickers, str):  # Skip exchanges with errors
            continue
        for pair, data in tickers.items():
            last_price = data.get("last")
            if last_price:
                if pair not in pair_prices:
                    pair_prices[pair] = []
                pair_prices[pair].append((exchange, last_price))

    # Detect arbitrage opportunities
    for pair, prices in pair_prices.items():
        if len(prices) > 1:  # Only consider pairs listed on multiple exchanges
            prices.sort(key=lambda x: x[1])  # Sort by price (low to high)
            low_exchange, low_price = prices[0]
            high_exchange, high_price = prices[-1]
            # if (float(high_price) > 0) or (float(low_price) > 0): continue
            spread = ((high_price - low_price) / low_price) * 100  # Percentage difference
            spread = float(f"{spread:.4f}")
            if (spread >= min_spread) and (spread <= max_spread):
                opportunities.append(
                    (pair, low_exchange, float(f"{low_price:.4f}"), 
                     high_exchange, float(f"{high_price:.4f}"), spread))

    return opportunities

async def magic():
    print("Fetching market data... Please wait.")
    price_data = await fetch_all_exchanges()
    print("Data fetched successfully.")

    arbitrage_opportunities = find_arbitrage_opportunities(price_data)

    if arbitrage_opportunities:
        print("\n🔍 Potential Arbitrage Opportunities Found:")
        with open('arbitrage.json','a',encoding='utf8') as f:
            cc = len(arbitrage_opportunities)
            f.write('[')
            for i,opportuniti in enumerate(arbitrage_opportunities):
                pair={
                    "pair":opportuniti[0], "buy_from":opportuniti[1], "buy_price":opportuniti[2], 
                    "sell_on":opportuniti[3], "sell_price":opportuniti[4], "spread":opportuniti[5]
                }
                f.write(json.dumps(pair))
                if i != cc-1:
                    f.write(','+'\n')
            f.write(']')
    else:
        print("\nNo significant arbitrage opportunities found.")

    auxx = None
    with open('arbitrage.json', 'r', encoding='utf8') as f:
        auxx = json.load(f)
        auxx = sorted(auxx, key=lambda x: x['spread'], reverse=True)
    with open('arbitrage.json', 'w', encoding='utf8') as f:json.dump(auxx,f)
    

def main():
    return asyncio.run(magic())

if __name__ == "__main__":
    main() 
