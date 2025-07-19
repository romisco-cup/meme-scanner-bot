import snscrape.modules.twitter as sntwitter
import re

# Configuration
INFLUENCERS = ["WatcherGuru", "elonmusk", "BillyM2k"]
HASHTAGS = ["#Solana, #PEPE"]
KEYWORDS = ["gem", "moon", "pump"]
QUERY_TEMPLATE = "from:{} {} OR {}"

def get_trending_tickers():
    trending_tickers = set()

    # Construct the query
    hashtags_str = " OR ".join(HASHTAGS)
    keywords_str = " OR ".join(KEYWORDS)

    for influencer in INFLUENCERS:
        query = QUERY_TEMPLATE.format(influencer, hashtags_str, keywords_str)

        try:
            for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
                if i > 100:  # Limit to the last 100 tweets per influencer
                    break

                # Extract tickers (e.g., $SOL, $PEPE)
                tickers = re.findall(r'\$[A-Z]+', tweet.rawContent)
                for ticker in tickers:
                    trending_tickers.add(ticker.strip('$'))
        except Exception as e:
            print(f"Error scraping tweets for {influencer}: {e}")

    return list(trending_tickers)

if __name__ == '__main__':
    tickers = get_trending_tickers()
    print(f"Trending tickers: {tickers}")
